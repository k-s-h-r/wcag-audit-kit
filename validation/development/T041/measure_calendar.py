"""Measure the frozen local calendar comparison using the native Orca adapter."""

import argparse
from contextlib import contextmanager
from datetime import datetime
from functools import partial
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sys
from threading import Thread
import unicodedata
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / 'skills/wcag-audit-kit/scripts'))

from benchmarks.native_status import capture
from orca_log import speech_in_window


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n',
                    encoding='utf-8')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def frozen_inputs(inputs):
    frozen = load(inputs / 'freeze.json')
    fixtures = {p.relative_to(HERE / 'fixture').as_posix(): digest(p)
                for p in (HERE / 'fixture').rglob('*') if p.is_file()}
    if (fixtures != frozen['fixture_sha256']
            or digest(inputs / 'scenario.json') != frozen['scenario_sha256']
            or digest(inputs / 'oracle.json') != frozen['oracle_sha256']):
        raise ValueError('事前固定した対照ページ、操作または到達条件と一致しない')
    return frozen, load(inputs / 'scenario.json'), load(inputs / 'oracle.json')


class PublicPages(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path not in {'/m8d/', '/c4p/', '/calendar.js', '/calendar.css', '/robots.txt'}:
            self.send_error(404)
            return
        super().do_GET()


@contextmanager
def serve():
    handler = partial(PublicPages, directory=HERE / 'fixture')
    with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f'http://127.0.0.1:{server.server_port}'
        finally:
            server.shutdown()
            thread.join()


def observe(row, selector):
    return next(item['text'] for item in row['observations']
                if item['target']['selector'] == selector)


def calendar_messages(phrases):
    speech = re.sub(r'\s+', '', unicodedata.normalize('NFKC', ' '.join(phrases)))
    return [f'{day}、空き{status}。' for day, status in
            re.findall(r'(12月\d{1,2}日)[、,:。]?空き(なし|あり)', speech)]


def verify(area, request, oracle, case):
    native = area / 'speech'
    receipt, log = native / 'screen-reader.json', native / 'orca-debug.log'
    original = load(receipt)
    env, rows = original['environment'], original['observations']
    result = {'adapter_status': original['status'], 'adapter_error': original.get('error'),
              'environment': env, 'valid': False}
    if (original['status'] != 'collected' or env.get('simulation') is not False
            or env.get('installation_verified') is not True or env.get('reader') != 'Orca'
            or env.get('browser') != 'Chromium' or original['scenario'] != request
            or original['request_sha256'] != digest(area / 'request.json')
            or original['cleanup']['pty_error'] is not None
            or not log.is_file() or original['cleanup']['debug_log_sha256'] != digest(log)
            or len(rows) != len(request['actions'])):
        return result

    previous_end = datetime.fromisoformat(original['started_at'])
    log_text = log.read_text(encoding='utf-8', errors='replace')
    for index, (row, action) in enumerate(zip(rows, request['actions'], strict=True), 1):
        start, end = (datetime.fromisoformat(row[key]) for key in ('started_at', 'finished_at'))
        if (row['index'] != index or row['action'] != action or row['url'] != request['url']
                or not previous_end <= start < end
                or (end - start).total_seconds() < request['settle_ms'] / 1000
                or row != load(native / f'step-{index}.json')
                or row['speech'] != speech_in_window(log_text, row['started_at'], row['finished_at'])):
            raise ValueError(f'{case}: 操作と元発話の時刻、ステップ記録、URLが一致しない')
        previous_end = end
    action_rows = rows[1:]
    shown = [observe(row, '#availability') for row in action_rows]
    focuses = [row['focus_after']['id'] for row in action_rows]
    phrases = [[item['phrase'] for item in row['speech']] for row in rows]
    messages = [calendar_messages(items) for items in phrases[1:]]
    displayed = oracle['cases'][case]
    setup_observed = (any(oracle['heading'] in text for text in phrases[0])
                      and observe(rows[0], '#availability') == oracle['start'])
    valid = (setup_observed and shown == displayed['displayed'] and shown[-1] == oracle['end']
             and oracle['end'] not in shown[:-1] and focuses == displayed['focuses']
             and all(row['focus_after']['documentHasFocus'] for row in action_rows)
             and [message for row in messages for message in row] == displayed['date_status_utterances']
             and messages[-1] == [oracle['end']])
    return dict(result, valid=valid, initial_display=observe(rows[0], '#availability'),
                setup_observed=setup_observed, setup_phrases=phrases[0],
                keypresses=len(action_rows), keypresses_including_setup=len(rows),
                date_status_utterances=sum(len(row) for row in messages),
                full_date_utterances=sum(message.endswith('空きなし。') for row in messages for message in row),
                steps=[{'index': row['index'], 'key': row['action']['keys'][0],
                        'focus': focus, 'display': display, 'phrases': utterances,
                        'date_status_utterances': observed}
                       for row, focus, display, utterances, observed in
                       zip(action_rows, focuses, shown, phrases[1:], messages, strict=True)],
                raw_log_sha256=digest(log), request_sha256=digest(area / 'request.json'))


def run(runtime, inputs, output):
    frozen, scenario, oracle = frozen_inputs(inputs)
    output.mkdir(parents=True, exist_ok=False)
    save(output / 'freeze.json', frozen)
    settings = {key: value for key, value in scenario.items() if key not in {'reader_setup', 'cases'}}
    results = {}
    with serve() as origin:
        for case, keys in scenario['cases'].items():
            request = dict(settings, case_id=case, url=f'{origin}/{case}/',
                           actions=[scenario['reader_setup'],
                                    *({'type': 'reader.press', 'keys': [key]} for key in keys)])
            area = output / case
            area.mkdir()
            save(area / 'request.json', request)
            capture(runtime, area)
            result = verify(area, request, oracle, case)
            if result.get('adapter_error') == '起動したOrcaのログから版を確認できない':
                retry = output / f'{case}-startup-retry'
                retry.mkdir()
                save(retry / 'request.json', request)
                capture(runtime, retry)
                result = verify(retry, request, oracle, case)
                result['previous_startup_failure'] = area.name
                area = retry
            result['artifact_directory'] = area.name
            result['url'] = request['url']
            results[case] = result
            save(output / 'observations.json', results)
            print(case, 'valid=' + str(result['valid']), flush=True)
    if not all(item['valid'] for item in results.values()):
        raise ValueError('到達、操作または発話を事前に固定した条件と照合できなかった')
    if results['c4p']['environment'] != results['m8d']['environment']:
        raise ValueError('実Orcaとブラウザーの実行環境が一致しない')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path, help='Orca package root')
    parser.add_argument('--inputs', default=HERE, type=Path, help='Frozen scenario and oracle')
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    run(args.root.resolve(), args.inputs.resolve(), args.out.resolve())
