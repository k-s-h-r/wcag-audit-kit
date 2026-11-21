"""Bind the real Orca process evidence to the standard WCAG reports."""

import argparse
from functools import partial
from html import unescape
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread
from urllib.parse import urljoin, urlsplit
from zipfile import ZipFile

from capture import QuietHandler
from score import HERE, digest, load, score


CLI = HERE.parents[2] / 'skills/wcag-audit-kit/scripts/audit.py'
STATE = 'input-error'


def command(*args):
    result = subprocess.run([sys.executable, str(CLI), *map(str, args)], text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def error_ax_role(nodes, expected_text):
    by_id = {node['nodeId']: node for node in nodes}
    node = next(item for item in nodes if item['role']['value'] == 'StaticText'
                and item.get('name', {}).get('value') == expected_text)
    while parent_id := node.get('parentId'):
        node = by_id[parent_id]
        role = node['role']['value']
        if role in {'alert', 'status', 'paragraph'}:
            return role
    raise ValueError('エラー表示の公開ロールを取得できなかった。')


def build(native_run, case_name, observation, destination):
    destination.mkdir(exist_ok=False, parents=True)
    oracle = load(HERE / 'oracle.json')
    error_text = oracle['labels']['error']
    entry = load(native_run / case_name / 'request.json')['url']
    visit = urljoin(entry, 'visit.html')
    confirmation = urljoin(entry, 'confirmation.html?people=2')
    config = destination / 'config.json'
    audit_run = destination / 'audit'
    command('init', '--url', entry, '--mode', 'screen-reader', '--config', config)
    settings = load(config)
    settings['scope'].update(mode='configured', pages=[entry, visit, confirmation], known_pages=[], max_pages=3)
    settings['environments'] = [env for env in settings['environments'] if env['id'] == 'desktop']
    settings['keyboard_steps'] = 0
    settings['inspection'].update(screenshots='initial', max_images=8)
    settings['states'] = [{
        'id': STATE, 'paths': [urlsplit(visit).path],
        'actions': [{'type': 'fill', 'selector': '#people', 'value': '1'},
                    {'type': 'press', 'key': 'Tab'}, {'type': 'press', 'key': 'Space'}],
        'assert': [{'selector': '#error', 'text': error_text, 'visible': True}],
    }]
    save(config, settings)
    command('start', '--config', config, '--out', audit_run)
    plan = load(audit_run / 'work/plan.json')
    case = next(item for item in plan['cases'] if item['criterion'] == oracle['criterion']
                and item['state'] == STATE and item['page_url'] == visit)
    case_id = case['case_id']
    packet = json.loads(command('case', '--run', audit_run, '--id', case_id))
    ax_path = Path(case['evidence_dir']) / 'accessibility-tree.json'
    public_role = error_ax_role(load(audit_run / 'work' / ax_path)['nodes'], error_text)
    if observation['valid'] and public_role != (observation['error_role'] or 'paragraph'):
        raise ValueError('収集した公開ロールが固定した対照の通知ロールと一致しない。')
    native_files = native_run / case_name / 'speech'
    files = [native_run / case_name / 'request.json', native_files / 'screen-reader.json',
             native_files / 'orca-debug.log']
    for name in ('invalid_input', 'review_control', 'error', 'return_to_input', 'corrected_input', 'confirmation'):
        position = oracle['steps'][name]
        files.extend(native_files / f'step-{position}.{ext}' for ext in ('png', 'json'))
    evidence = [ax_path.as_posix(), *(command('attach', '--run', audit_run, '--case', case_id, '--file', source)
                                     for source in files if source.is_file())]
    role = '通知要素に role="alert" があり、公開ロールは alert。' if public_role == 'alert' else (
        '通知要素にライブプロパティの指定はなく、公開ロールは paragraph。'
    )
    speech = '、'.join(f'「{phrase}」' for phrase in observation.get('error_speech', [])) or '記録なし'
    observed = (
        f'1名の入力で「{error_text}」が表示された。確認ボタンにフォーカスが残った。'
        f'{role}操作後のOrca発話は{speech}。'
        '2名に修正して同じキー操作で見学予約の確認画面に進んだ。'
    ) if observation['valid'] else observation['reason']
    expected = '確認ボタンのフォーカスを維持しながら、入力エラーの内容が支援技術に提示される。'
    outcome = observation['outcome']
    complete = outcome == 'passed'
    record = dict(
        case_id=case_id, config_digest=packet['config_digest'],
        normative_sha256=packet['criterion']['normative_sha256'],
        execution='completed', outcome=outcome, coverage_complete=complete,
        conditions_reviewed=observation['valid'], exceptions_reviewed=observation['valid'],
        observed=observed, evidence=evidence,
        steps_executed=[
            '起点ページで「見学の予約を始める」にTabで移動し、Enterで開く。',
            '見学人数を1と入力し、Tabで確認ボタンに移動してSpaceを押す。',
            '確認ボタンにフォーカスが残った状態で、表示とOrca発話を照合する。',
            'Shift+Tabで見学人数へ戻り、Backspaceで1を削除して2を入力する。',
            'Tabで確認ボタンに移動し、Spaceを押して2名の確認画面に進む。',
        ],
        tests_applied=['4.1.3-01', '4.1.3-02'],
        targets=[dict(target='見学人数の入力エラー（#error）', observed=observed, expected=expected,
                      outcome=outcome, evidence=evidence)],
        remaining=[] if complete else ['この観察は専用Orca環境の入力エラー状態。ほかの支援技術と全達成基準の検査が残る。'],
    )
    if complete:
        record['method_coverage'] = [
            {'method': 'flow', 'status': 'executed', 'reason': '起点から入力エラーと修正後の確認に至る実キー操作を取得した。'},
            {'method': 'dom', 'status': 'executed', 'reason': '通知は更新前から存在し、状態キャプチャーでアラートの構造を確認した。'},
            {'method': 'screen-reader', 'status': 'executed', 'reason': '実Orcaの操作後の発話の内容を表示と時刻で照合した。'},
        ]
    record_path = destination / 'judgment.json'
    save(record_path, record)
    command('record', '--run', audit_run, '--file', record_path)
    command('report', '--run', audit_run)
    workbook = audit_run / 'reports/report.xlsx'
    command('excel', 'export', '--run', audit_run, '--mode', 'report', '--out', workbook)
    report = load(audit_run / 'data/report.json')
    scope = report['scope_conformance']
    case_result = next(item for item in report['cases'] if item['case_id'] == case_id)
    issues = audit_run / 'reports/details/issues.md'
    html = audit_run / 'reports/report.html'
    html_text = html.read_text()
    scope_text = f'{oracle["level"]} の結論　{scope["label"]}'
    with ZipFile(workbook) as payload:
        workbook_text = unescape('\n'.join(payload.read(name).decode() for name in payload.namelist()
                                           if name.startswith('xl/worksheets/') or name == 'xl/sharedStrings.xml'))
    if (case_result['outcome'] != outcome or report['audit_complete'] or not scope['remaining']
            or any(case_id not in text or scope_text not in text for text in (html_text, workbook_text))
            or not all((audit_run / 'work' / path).is_file() for path in evidence)):
        raise ValueError('検査票の状態・判定・残る確認をHTML・JSON・Excelで照合できなかった。')
    if outcome == 'failed':
        failed = next(item for item in scope['failed_cases'] if item['case_id'] == case_id)
        if (scope['status'] != 'does_not_conform' or case_id not in issues.read_text()
                or set(failed['evidence']) != set(evidence)):
            raise ValueError('不適合箇所一覧から根拠を参照できなかった。')
    elif scope['status'] != 'unverified' or case_id in issues.read_text():
        raise ValueError('限定観点の通過・保留を範囲の適合または不適合と扱っている。')
    return {'case_id': case_id, 'criterion': oracle['criterion'], 'state': STATE, 'url': visit,
            'outcome': outcome, 'scope_status': scope['status'], 'audit_complete': report['audit_complete'],
            'remaining_count': len(scope['remaining']), 'public_error_role': public_role, 'evidence': evidence,
            'files': {file.relative_to(destination.parent).as_posix(): digest(file)
                      for file in (issues, html, workbook, audit_run / 'data/report.json')}}


def run(native_run, output):
    output.mkdir(parents=True, exist_ok=False)
    scores = score(native_run)
    save(output / 'score.json', scores)
    first = next(iter(scores['cases']))
    port = urlsplit(load(native_run / first / 'request.json')['url']).port
    handler = partial(QuietHandler, directory=native_run / 'fixture')
    with ThreadingHTTPServer(('127.0.0.1', port), handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            reports = {}
            for case_name, observation in scores['cases'].items():
                reports[case_name] = build(native_run, case_name, observation, output / case_name)
                print(case_name, reports[case_name]['case_id'], reports[case_name]['scope_status'], flush=True)
        finally:
            server.shutdown()
            thread.join()
    save(output / 'reports.json', reports)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    run(args.run, args.out)
