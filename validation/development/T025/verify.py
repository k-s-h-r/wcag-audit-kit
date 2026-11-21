"""Check recorded contrast changes for a shared link in two normal CLI runs."""
import argparse
from hashlib import sha256
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests'))
from url_selection_browser import AUDIT, start_server, stop_server, write_json

CRITERION = '1.4.3'
TARGET = '#shared-help'
EXPECTED = '通常サイズのリンク文字が背景と4.5:1以上のコントラストを持つ。'
BEFORE = {'/resolved': False, '/continuing': False, '/new': True, '/pending': False,
          '/excluded': False, '/uncollected': False}
AFTER = {'/resolved': True, '/continuing': False, '/new': False, '/pending': True,
         '/uncollected': None}
NAV = '<nav aria-label="Support"><a id="shared-help" href="/help">Support</a></nav>'


def serve():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            path = urlsplit(self.path).path
            passed = self.server.variant.get(path)
            if passed is None:
                self.send_error(404)
                return
            color = '#161616' if passed else '#aaa'
            locale_style = ('''<script>if (navigator.language === 'en-US') {
                document.querySelector('#shared-help').style.color = '#161616';
            }</script>''' if path == '/resolved' else '')
            content = ('<!doctype html><html lang="en"><meta charset="utf-8"><title>Contrast fixture</title>'
                       f'<style>body{{background:white}}#shared-help{{color:{color};font:16px sans-serif}}</style>'
                       f'{NAV}{locale_style}</html>').encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)

    return start_server(Handler)


def cli(*args, expected=0):
    result = subprocess.run([sys.executable, str(AUDIT), *map(str, args)],
                            text=True, capture_output=True, timeout=120)
    assert result.returncode == expected, (result.args, result.returncode, result.stdout, result.stderr)
    return result


def collect(directory, name, origin, variant, *, missing=(), locale=None):
    output = directory / name
    config = directory / f'{name}-config.json'
    write_json(config, {
        'schema_version': '1', 'url': origin + '/', 'level': 'AA',
        'scope': {'mode': 'configured', 'pages': list(variant), 'max_pages': len(variant)},
        'environments': [{'id': 'desktop', 'viewport': {'width': 1280, 'height': 900}, 'zoom': 1}],
        'keyboard_steps': 0,
        **({'locale': locale} if locale else {}),
    })
    cli('start', '--config', config, '--out', output)
    ledger = output / 'work'
    meta = json.loads((ledger / 'run.json').read_text())
    catalog = json.loads((ledger / 'catalog.snapshot.json').read_text())
    definition = next(row for row in catalog['criteria'] if row['id'] == CRITERION)
    plan = json.loads((ledger / 'plan.json').read_text())
    observations = {}
    for case in plan['cases']:
        if case['criterion'] != CRITERION:
            continue
        path = urlsplit(case['page_url']).path
        expected = variant[path]
        if expected is None:
            continue
        capture = ledger / case['evidence_dir']
        axe = json.loads((capture / 'axe.json').read_text())
        nodes = {section: [node for rule in axe[section] if rule['id'] == 'color-contrast'
                           for node in rule['nodes'] if node['target'] == [TARGET]]
                 for section in ('violations', 'passes')}
        section = 'passes' if expected else 'violations'
        assert len(nodes[section]) == 1 and not nodes['violations' if expected else 'passes'], nodes
        measurement = next(check['data'] for check in nodes[section][0]['any']
                           if 'contrastRatio' in check.get('data', {}))
        ratio = measurement['contrastRatio']
        assert (ratio >= 4.5) == expected, measurement
        observations[path] = {'ratio': ratio, 'assessment_recorded': path not in missing}
        if path in missing:
            continue
        outcome = 'passed' if expected else 'failed'
        proof = [f'{case["evidence_dir"]}/{file}' for file in ('axe.json', 'page.png')]
        observed = f'Chromium上で共通リンクの文字と背景のコントラストは{ratio}:1だった。'
        assessment = directory / f'{name}-{path.lstrip("/")}.json'
        write_json(assessment, {
            'case_id': case['case_id'], 'config_digest': meta['config_digest'],
            'normative_sha256': definition['normative_sha256'], 'execution': 'completed',
            'outcome': outcome, 'observed': observed, 'conditions_reviewed': True,
            'exceptions_reviewed': True, 'coverage_complete': True,
            'steps_executed': ['初期画面の唯一の文字要素である共通リンクを確認した。'],
            'tests_applied': ['WCAG22:1.4.3:normative', 'axe:color-contrast'],
            'targets': [{'target': TARGET, 'expected': EXPECTED, 'observed': observed,
                         'outcome': outcome, 'evidence': proof}],
            'method_coverage': [{'method': method, 'status': 'executed',
                                 'reason': '収集した初期画面・DOMにあるリンクをaxeの計測と照合した。'}
                                for method in definition['methods']],
            'evidence': proof, 'remaining': [],
        })
        cli('record', '--run', output, '--file', assessment)
    cli('report', '--run', output)
    return output, observations


def hashes(directory):
    return {path.relative_to(directory): sha256(path.read_bytes()).hexdigest()
            for path in directory.rglob('*') if path.is_file()}


class HtmlLinks(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.files = set()
        self.directory = path.parent
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.files.add((self.directory / unquote(dict(attrs)['href'])).resolve())


def compare_target(before, after):
    result = json.loads(cli('compare-reports', '--before', before, '--after', after,
                            '--criterion', CRITERION).stdout)
    page = next(page for page in result['pages'] if urlsplit(page['url']).path == '/resolved')
    return next(row for row in page['results'] if row.get('target') == TARGET)


def verify_assessment_sources(out, before, after, report):
    copied = out / 'after-record-copy'
    shutil.copytree(after, copied)
    historical = copied / 'data/earlier.json'
    shutil.copyfile(copied / report, historical)
    original = json.loads(historical.read_text())
    cases = {urlsplit(case['page_url']).path: case for case in original['cases'] if case['criterion'] == CRITERION}
    same_page, other_page = cases['/resolved'], cases['/continuing']
    assessment = json.loads((out / 'after-resolved.json').read_text())
    record_file = out / 'after-record-copy-input.json'

    # The record command accepts this: case-level evidence is local, target evidence is foreign.
    assessment['targets'][0]['evidence'] = [f'{other_page["evidence_dir"]}/axe.json']
    write_json(record_file, assessment)
    cli('record', '--run', copied, '--file', record_file)
    cli('report', '--run', copied)
    row = compare_target(before / report, copied / report)
    assert row['status'] == 'unverified' and row['reason'] == 'evidence_unverified', row
    assert compare_target(before / report, historical)['status'] == 'resolved'

    # A target can use evidence explicitly attached to the same case, including relative aliases.
    attached = cli('attach', '--run', copied, '--case', same_page['case_id'], '--file',
                   after / 'work' / same_page['evidence_dir'] / 'axe.json').stdout.strip()
    assessment['targets'][0]['evidence'] = ['./' + attached]
    write_json(record_file, assessment)
    cli('record', '--run', copied, '--file', record_file)
    cli('report', '--run', copied)
    row = compare_target(before / report, copied / report)
    assert row['status'] == 'resolved', row
    assert [item['href'] for item in row['after']['evidence']] == [(copied / 'work' / attached).as_uri()]

    altered = copied / 'data/altered-assessment.json'
    altered_case = next(case for case in original['cases'] if case['case_id'] == same_page['case_id'])
    altered_case['assessment_data']['targets'][0]['outcome'] = 'failed'
    write_json(altered, original)
    check = cli('compare-reports', '--before', before / report, '--after', altered, expected=1)
    assert '帳票の判定と元のrunの判定' in check.stderr
    altered_case['assessment_data']['targets'][0]['outcome'] = 'passed'
    altered_case['assessment'] = str(copied / 'work' / altered_case['assessment'])
    write_json(altered, original)
    check = cli('compare-reports', '--before', before / report, '--after', altered, expected=1)
    assert '保存したrun内の判定ファイル' in check.stderr

    catalog_path = copied / 'work/catalog.snapshot.json'
    catalog = json.loads(catalog_path.read_text())
    catalog['criteria'][0]['title'] = 'Changed in the copy'
    write_json(catalog_path, catalog)
    check = cli('compare-reports', '--before', before / report, '--after', historical, expected=1)
    assert '検査定義のスナップショットが変更された' in check.stderr


def verify(out):
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    server, worker = serve()
    origin = f'http://127.0.0.1:{server.server_port}'
    try:
        server.variant = BEFORE
        before, old = collect(out, 'before', origin, BEFORE)
        other_locale, locale_observation = collect(out, 'other-locale', origin, {'/resolved': True}, locale='en-US')
        server.variant = AFTER
        after, new = collect(out, 'after', origin, AFTER, missing=('/pending',), locale='ja-JP')
    finally:
        stop_server(server, worker)

    report = Path('data/report.json')
    original_before, original_after = hashes(before), hashes(after)
    comparison = out / 'preview # 1.html'
    options = ['--before', before / report, '--after', after / report, '--criterion', CRITERION]
    result = json.loads(cli('compare-reports', *options, '--out', comparison).stdout)
    pages = {urlsplit(page['url']).path: page['results'] for page in result['pages']}
    expected = {'/resolved': 'resolved', '/continuing': 'continuing', '/new': 'new',
                '/pending': 'unverified', '/excluded': 'unverified', '/uncollected': 'unverified'}
    assert pages.keys() == expected.keys()
    assert result['scope_changed']
    assert not result['before']['audit_complete'] and not result['after']['audit_complete']
    for path, status in expected.items():
        targets = [row for row in pages[path] if row.get('target') == TARGET]
        assert [row['status'] for row in targets] == [status], (path, pages[path])
    assert any(row.get('reason') == 'missing_capture' for row in pages['/uncollected'])
    assert any(row.get('reason') == 'missing_case' for row in pages['/excluded'])
    assert any(row.get('reason') == 'coverage_unverified' and row['after']['outcome'] == 'not_run'
               for row in pages['/pending'])

    proof = {}
    for rows in pages.values():
        for row in rows:
            for side in ('before', 'after'):
                for item in row[side].get('evidence', []):
                    path = Path(unquote(urlsplit(item['href']).path))
                    proof[path] = item['sha256']
    assert len(proof) == 18, proof
    assert all(sha256(path.read_bytes()).hexdigest() == digest for path, digest in proof.items())
    assert HtmlLinks(comparison).files == {(before / report).resolve(), (after / report).resolve(), *proof}

    original_html = comparison.read_bytes()
    cli('compare-reports', *options, '--out', comparison, expected=1)
    assert comparison.read_bytes() == original_html
    cli('compare-reports', *options, '--out', after / 'forbidden.html', expected=1)
    assert not (after / 'forbidden.html').exists()

    altered = out / 'after-altered'
    shutil.copytree(after, altered)
    resolved = next(row for row in pages['/resolved'] if row.get('target') == TARGET)
    altered_proof = Path(unquote(urlsplit(resolved['after']['evidence'][0]['href']).path))
    (altered / altered_proof.relative_to(after)).write_text('changed only in the copy')
    altered_options = ['--before', before / report, '--after', altered / report, '--criterion', CRITERION]
    altered_result = json.loads(cli('compare-reports', *altered_options).stdout)
    assert any(row.get('reason') == 'evidence_unverified' for page in altered_result['pages']
               if urlsplit(page['url']).path == '/resolved' for row in page['results'])
    locale_row = compare_target(before / report, other_locale / report)
    assert locale_row['status'] == 'unverified' and locale_row['reason'] == 'environment_changed', locale_row
    verify_assessment_sources(out, before, after, report)
    assert (original_before, original_after) == (hashes(before), hashes(after))

    write_json(out / 'comparison.json', result)
    browser = next(capture['browser_version']
                   for capture in json.loads((before / 'work/capture-manifest.json').read_text())['captures'])
    write_json(out / 'summary.json', {
        'browser': browser, 'viewport': [1280, 900], 'criterion': CRITERION, 'target': TARGET,
        'pages': {path: {'before': old.get(path), 'after': new.get(path), 'comparison': status}
                  for path, status in expected.items()},
        'evidence_links_verified': len(proof), 'immutable_files': [len(original_before), len(original_after)],
        'reject_existing_output': True, 'reject_output_inside_input_run': True,
        'altered_evidence_is_unverified': True,
        'locale': {'implicit_ja_JP_matches_explicit': True, 'en_US': locale_observation['/resolved'],
                   'comparison': locale_row['status'], 'reason': locale_row['reason']},
        'foreign_target_evidence_is_unverified': True,
        'matching_case_attachment_is_accepted': True,
        'historical_assessment_revision_is_accepted': True,
        'altered_assessment_and_external_path_are_rejected': True,
        'altered_catalog_is_rejected': True,
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    verify(parser.parse_args().out)
