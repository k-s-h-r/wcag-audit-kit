"""Compare native process observations with the fixed grading conditions."""

import argparse
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from unicodedata import normalize
from urllib.parse import urljoin


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'skills/wcag-audit-kit/scripts'))
from orca_log import speech_in_window


class ErrorMarkup(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.attributes = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if dict(attrs).get('id') == 'error':
            self.attributes = dict(attrs)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def words(value):
    return ''.join(normalize('NFKC', value).split()).rstrip('.。').casefold()


def text(row, selector):
    return next(item['text'] for item in row['observations'] if item['target']['selector'] == selector)


def focused(row, control):
    return all(row[when]['id'] == control and row[when]['documentHasFocus'] is True
               for when in ('focus_before', 'focus_after'))


def checked_observation(run, case, scenario, oracle):
    area = run / case
    receipt = area / 'speech/screen-reader.json'
    raw_log = area / 'speech/orca-debug.log'
    request_path = area / 'request.json'
    request = load(request_path)
    value = load(receipt)
    environment = value['environment']
    observations = value['observations']
    result = {'valid': False, 'outcome': 'cant_tell', 'environment': environment,
              'adapter_status': value['status'], 'receipt': receipt.relative_to(run).as_posix(),
              'error': value.get('error'), 'speech_log': raw_log.relative_to(run).as_posix()}
    if (value['status'] != 'collected' or environment.get('simulation') is not False
            or environment.get('installation_verified') is not True or environment.get('reader') != 'Orca'
            or environment.get('browser') != 'Chromium'
            or value['request_sha256'] != digest(request_path) or value['scenario'] != request
            or request != {**scenario, 'case_id': case, 'url': request['url']}
            or value['cleanup']['debug_log_sha256'] != digest(raw_log) or value['cleanup']['pty_error'] is not None):
        result['reason'] = '実Orcaの正常起動、固定シナリオ、原始ログを照合できなかった。'
        return result

    log_text = raw_log.read_text(errors='replace')
    last = datetime.fromisoformat(value['started_at'])
    for index, (row, action) in enumerate(zip(observations, scenario['actions'], strict=True), 1):
        start, finish = (datetime.fromisoformat(row[k]) for k in ('started_at', 'finished_at'))
        if (row['index'] != index or row['action'] != action or not last <= start < finish
                or (finish - start).total_seconds() < scenario['settle_ms'] / 1000
                or row['speech'] != speech_in_window(log_text, row['started_at'], row['finished_at'])):
            result['reason'] = '操作・観察窓・元のOrcaログを照合できなかった。'
            return result
        last = finish

    steps = {name: observations[index - 1] for name, index in oracle['steps'].items()}
    entry = request['url']
    visit = urljoin(entry, 'visit.html')
    confirmation = urljoin(entry, 'confirmation.html?people=2')
    labels = oracle['labels']
    error = steps['error']
    speech = [line['phrase'] for line in error['speech']]
    review = [line['phrase'] for row in observations[6:8] for line in row['speech']]
    correction = [line['phrase'] for line in steps['return_to_input']['speech']]
    normalized_speech = [words(line) for line in speech]
    attributes = ErrorMarkup((run / 'fixture' / case / 'visit.html').read_text()).attributes
    error_role = attributes.get('role')
    displayed = text(error, 'main')
    result.update(entry=entry, visit=visit, confirmation=steps['confirmation']['url'],
                  review_speech=review, error_speech=speech, correction_speech=correction,
                  error_visible=labels['error'] in displayed,
                  error_role=error_role, error_focused=focused(error, 'review'),
                  error_window=[error['started_at'], error['finished_at']],
                  error_screen_sha256=digest(area / f"speech/step-{oracle['steps']['error']}.png"),
                  silence=(not any(any(hint in line for hint in ('見学人数', '2名以上', '入力してください'))
                                   for line in normalized_speech)),
                  announcement=words(labels['error']) in normalized_speech,
                  speech_log_sha256=digest(raw_log))
    route = [entry] * 2 + [visit] * (len(observations) - 3) + [confirmation]
    result['valid'] = (
        [row['url'] for row in observations] == route and
        steps['entry_link']['focus_after']['id'] == 'start' and
        focused(steps['invalid_input'], 'people') and focused(steps['review_control'], 'review') and
        steps['return_to_input']['focus_after']['id'] == 'people' and focused(steps['corrected_input'], 'people') and
        result['error_visible'] and result['error_focused'] and
        labels['error'] not in text(steps['review_control'], 'main') and
        labels['confirmation'] in text(steps['confirmation'], 'main') and
        words(labels['review_button']) in words(' '.join(review)) and
        error_role == oracle['cases'][case]['error_role'] and 'aria-live' not in attributes
    )
    if not result['valid']:
        result['reason'] = '経路、確認ボタンの発話、エラー表示、フォーカスまたは修正後の到達を照合できなかった。'
    return result


def score(run):
    oracle = load(HERE / 'oracle.json')
    scenario = load(HERE / 'scenario.json')
    inputs = load(run / 'input-sha256.json')
    if any(digest(run / path) != checksum or digest(HERE / path) != checksum for path, checksum in inputs.items()):
        raise ValueError('測定に使用した対照ページ・操作のハッシュが一致しない。')

    cases = {name: checked_observation(run, name, scenario, oracle) for name in oracle['cases']}
    normal, comparison = (cases[case] for case in oracle['cases'])
    matched = all(case['valid'] for case in cases.values()) and normal['environment'] == comparison['environment']
    if matched and normal['announcement']:
        normal['outcome'] = 'passed'
        if comparison['silence'] and comparison['error_role'] is None:
            comparison['outcome'] = 'failed'
    correct = sum(case['outcome'] == oracle['cases'][name]['expected_outcome'] for name, case in cases.items())
    return {'criterion': oracle['criterion'], 'oracle_sha256': digest(HERE / 'oracle.json'),
            'input_sha256': inputs, 'correct': correct, 'total': len(cases), 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    value = score(args.run)
    with args.out.open('x', encoding='utf-8') as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write('\n')
    sys.exit(0 if value['correct'] == value['total'] else 2)
