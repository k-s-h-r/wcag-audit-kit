"""Compare recorded target judgments without updating either audit."""
from collections import Counter, defaultdict
from dataclasses import dataclass
from html import escape
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from run_layout import href, organized


STATUSES = {'resolved': '解消', 'new': '新規', 'continuing': '継続', 'unverified': '未確認'}
TRANSITIONS = {('failed', 'passed'): 'resolved', ('passed', 'failed'): 'new',
               ('failed', 'failed'): 'continuing'}
OUTCOMES = {'passed': '通過', 'failed': '不適合', 'cant_tell': '判断保留', 'not_run': '未実施',
            'inapplicable': '対象外', 'missing': '記録なし', 'ambiguous': '複数の記録',
            'not_listed': '未訪問・未収集の一覧に記載なし'}
REASONS = {
    'missing_case': '同じURL・状態・環境・基準の検査票が片方にない',
    'missing_target': '同じ対象と期待結果の記録が片方にない',
    'missing_capture': '同じ画面を収集した記録を確認できない',
    'environment_changed': '設定上の環境、ブラウザーの版、または遷移先が一致しない',
    'state_changed': '状態を再現する設定が不明または一致しない',
    'auth_unverified': '保存された帳票から同じ認証状態か確認できない',
    'ambiguous_target': '同じ対象と期待結果の記録が重複している',
    'evidence_unverified': '対象の証拠の所在とハッシュを確認できない',
    'judgment_unverified': '両方で通過または不適合を確定した記録が必要',
    'coverage_unverified': '検査票に未実施・判断保留・対象範囲の確認が残る',
    'unvisited': '帳票に未訪問として記録されている',
}


def _read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def _case_key(case):
    return tuple(case[field] for field in ('page_url', 'state', 'environment', 'criterion'))


class Report:
    def __init__(self, path, criterion):
        from audit import run_meta

        self.path = path.resolve()
        self.data = _read(self.path)
        if not isinstance(self.data, dict) or not isinstance(self.data.get('cases'), list):
            raise ValueError(f'検査票の報告JSONを指定する: {path}')
        self.run = (self.path.parent / unquote(self.data.get('evidence_base', '.'))).resolve()
        meta = run_meta(self.run)
        self.config = meta['config']
        self.level = self.data['level']
        self.catalog = self.data['catalog_digest']
        if self.catalog != meta['catalog_digest'] or self.level != self.config['level']:
            raise ValueError(f'帳票と収集元のレベルまたは検査定義が一致しない: {path}')
        self.environments = {item['id']: item for item in self.config['environments']}
        self.states = {'initial': {}, **{item['id']: item for item in self.config.get('states', [])}}
        manifest = _read(self.run / 'capture-manifest.json')
        self.captures = {item['key']: item for item in manifest['captures']}
        self.cases = {}
        for case in self.data['cases']:
            if criterion and case['criterion'] != criterion:
                continue
            key = _case_key(case)
            if key in self.cases:
                raise ValueError(f'同じURL・状態・環境・基準の検査票が複数ある: {path}')
            assessment = case.get('assessment_data')
            if assessment and (assessment['config_digest'] != meta['config_digest']
                               or assessment['outcome'] != case['outcome']
                               or assessment['case_id'] != case['case_id']):
                raise ValueError(f'帳票の判定と元のrunの設定または検査票が一致しない: {path}')
            self.cases[key] = case
        self.case_gaps = set()
        for ident in self.data.get('missing_cases', []):
            capture_key, missing_criterion = ident.rsplit('--', 1)
            capture = self.captures.get(capture_key)
            if capture and (not criterion or missing_criterion == criterion):
                self.case_gaps.add((capture['url'], capture['state'], capture['environment'], missing_criterion))
        self.missing = {(item['url'], item['state'], item['environment'])
                        for item in self.data.get('missing_captures', [])}
        self.unvisited = {item['url'] if isinstance(item, dict) else item
                          for item in self.data.get('unvisited', [])}
        self.checked_files = {}

    def capture(self, case):
        item = self.captures.get(case['capture'], {})
        if (item.get('url'), item.get('state'), item.get('environment')) != _case_key(case)[:3]:
            return {}
        if (item.get('execution') != 'completed' or item.get('http_status', 200) >= 400
                or item.get('collection_state', 'finished') != 'finished'):
            return {}
        return item

    def evidence(self, target, assessment):
        from audit import evidence_item

        proof = {item['path']: item['sha256'] for item in assessment.get('verified_evidence', [])}
        paths = list(dict.fromkeys(target.get('evidence', [])))
        links = []
        for path in paths:
            if path not in self.checked_files:
                try:
                    self.checked_files[path] = evidence_item(self.run, path)['sha256']
                except (ValueError, OSError):
                    self.checked_files[path] = None
            if path not in proof or not proof[path] or self.checked_files[path] != proof[path]:
                continue
            links.append({'href': (self.run / path).resolve().as_uri(), 'sha256': proof[path]})
        return links, bool(paths) and len(links) == len(paths)

    def coverage(self):
        return {key: self.data[key] for key in
                ('audit_complete', 'collection_complete', 'scope_confirmed',
                 'missing_cases', 'declared_states_without_page') if key in self.data}

    def scope(self):
        return self.config['scope'], self.data.get('report_scope'), self.data['url']


def _context_issue(before, after, key, old_case, new_case):
    if not old_case or not new_case:
        return 'missing_case'
    if before.config.get('auth_state') or after.config.get('auth_state'):
        return 'auth_unverified'
    _, state, environment, _ = key
    if state not in before.states or before.states[state] != after.states.get(state):
        return 'state_changed'
    old_capture, new_capture = before.capture(old_case), after.capture(new_case)
    if not old_capture or not new_capture:
        return 'missing_capture'
    if (environment not in before.environments or before.environments[environment] != after.environments.get(environment)
            or not old_capture.get('browser_version') or old_capture['browser_version'] != new_capture.get('browser_version')
            or not old_capture.get('final_url') or old_capture['final_url'] != new_capture.get('final_url')):
        return 'environment_changed'
    return None


def _targets(assessment):
    values = defaultdict(list)
    for target in assessment.get('targets', []):
        values[target['target'], target['expected']].append(target)
    return values


def _side(report, candidates, assessment):
    if len(candidates) != 1:
        return {'outcome': 'ambiguous' if candidates else 'missing', 'evidence': []}, False
    target = candidates[0]
    links, complete = report.evidence(target, assessment)
    return {'outcome': target['outcome'], 'observed': target['observed'], 'evidence': links}, complete


def _case_side(case, assessment):
    return {'outcome': case['outcome'] if case else 'missing', 'remaining': assessment.get('remaining', [])}


def _pending(case, assessment):
    return (not case or case['outcome'] in {'not_run', 'cant_tell'}
            or assessment.get('execution') != 'completed'
            or assessment.get('coverage_complete') is not True or bool(assessment.get('remaining')))


def _case_changes(before, after, key):
    _, state, environment, criterion = key
    context = {'state': state, 'environment': environment, 'criterion': criterion}
    old_case, new_case = before.cases.get(key), after.cases.get(key)
    old = (old_case or {}).get('assessment_data') or {}
    new = (new_case or {}).get('assessment_data') or {}
    issue = _context_issue(before, after, key, old_case, new_case)
    norm_matches = old.get('normative_sha256') and old['normative_sha256'] == new.get('normative_sha256')
    execution_complete = old.get('execution') == new.get('execution') == 'completed'
    final_outcomes = {'passed', 'failed'}
    judgments_recorded = {old.get('outcome'), new.get('outcome')}.issubset(final_outcomes)
    old_targets, new_targets = _targets(old), _targets(new)
    for target, expected in sorted(old_targets.keys() | new_targets.keys()):
        left, left_evidence = _side(before, old_targets.get((target, expected), []), old)
        right, right_evidence = _side(after, new_targets.get((target, expected), []), new)
        outcomes = left['outcome'], right['outcome']
        reason = issue
        if not reason:
            if 'ambiguous' in outcomes:
                reason = 'ambiguous_target'
            elif 'missing' in outcomes:
                reason = 'missing_target'
            elif not (norm_matches and execution_complete and judgments_recorded and set(outcomes) <= final_outcomes):
                reason = 'judgment_unverified'
            elif not (left_evidence and right_evidence):
                reason = 'evidence_unverified'
        if outcomes == ('passed', 'passed') and not reason:
            continue
        yield dict(context, target=target, expected=expected, before=left, after=right,
                   status='unverified' if reason else TRANSITIONS[outcomes],
                   **({'reason': reason} if reason else {}))
    # Preserve coverage gaps even when some explicitly checked targets can be compared.
    if issue or _pending(old_case, old) or _pending(new_case, new):
        yield dict(context, status='unverified', reason=issue or 'coverage_unverified',
                   before=_case_side(old_case, old), after=_case_side(new_case, new))


def _collection_gap(before, after, key, reason, **details):
    return dict(details, status='unverified', reason=reason,
                before={'outcome': 'missing' if key in before else 'not_listed'},
                after={'outcome': 'missing' if key in after else 'not_listed'})


def compare(before_path, after_path, *, criterion=None, destination=None):
    before, after = Report(before_path, criterion), Report(after_path, criterion)
    if before.level != after.level or before.catalog != after.catalog:
        raise ValueError('比較するにはWCAGの版・検査定義と適合レベルをそろえる')
    if before.run == after.run:
        raise ValueError('修正前後の検査票は別のrunを指定する')

    pages = defaultdict(list)
    keys = before.cases.keys() | after.cases.keys() | before.case_gaps | after.case_gaps
    for key in sorted(keys):
        pages[key[0]].extend(_case_changes(before, after, key))
    for key in sorted(before.missing | after.missing):
        url, state, environment = key
        pages[url].append(_collection_gap(before.missing, after.missing, key, 'missing_capture',
                                          state=state, environment=environment))
    for url in sorted(before.unvisited | after.unvisited):
        pages[url].append(_collection_gap(before.unvisited, after.unvisited, url, 'unvisited'))
    result = {'level': before.level, 'catalog_digest': before.catalog,
              'scope_changed': before.scope() != after.scope(),
              'before': {'report': before.path.as_uri(), **before.coverage()},
              'after': {'report': after.path.as_uri(), **after.coverage()},
              'pages': [{'url': url, 'counts': dict(Counter(row['status'] for row in rows)), 'results': rows}
                        for url, rows in sorted(pages.items())]}
    if destination:
        _write_html(result, destination, before, after)
    return result


def _write_html(result, destination, before, after):
    destination = destination.resolve()
    for report in (before, after):
        root = report.run.parent if organized(report.run) else report.run
        if destination.is_relative_to(root):
            raise ValueError('比較の保存先は元のrunの外を指定する')

    def link(path, label):
        return f'<a href="{escape(href(destination, path), quote=True)}">{escape(label)}</a>'

    def cell(side):
        outcome = OUTCOMES[side['outcome']]
        texts = [outcome, side.get('observed', ''), *side.get('remaining', [])]
        lines = [escape(value) for value in texts if value]
        for i, evidence in enumerate(side.get('evidence', []), 1):
            path = Path(unquote(urlsplit(evidence['href']).path))
            lines.append(link(path, f'証拠 {i}'))
        return '<br>'.join(lines)

    sections = []
    for page in result['pages']:
        rows = []
        for row in page['results']:
            condition = ' / '.join(row[field] for field in ('state', 'environment', 'criterion') if field in row)
            detail = '<br>'.join(escape(value) for value in (condition, row.get('target'), row.get('expected')) if value)
            status = STATUSES[row['status']]
            if row.get('reason'):
                status += '。' + REASONS[row['reason']]
            rows.append(f'<tr><th scope="row">{detail or "未訪問"}</th><td>{escape(status)}</td>'
                        f'<td>{cell(row["before"])}</td><td>{cell(row["after"])}</td></tr>')
        table = ('<table><thead><tr><th scope="col">状態・環境・基準・対象</th><th scope="col">比較</th>'
                 '<th scope="col">変更前</th><th scope="col">変更後</th></tr></thead><tbody>'
                 + ''.join(rows) + '</tbody></table>') if rows else '<p>比較に該当する変更・未確認の記録はありません。</p>'
        sections.append(f'<section><h2>{escape(page["url"])}</h2>{table}</section>')
    scope_note = '<p>対象範囲の設定に差があります。</p>' if result['scope_changed'] else ''
    references = f'{link(before.path, "変更前の検査票JSON")} · {link(after.path, "変更後の検査票JSON")}'
    completion = ' · '.join(f'{label}は検証{"完了" if report.data.get("audit_complete") else "未完了"}'
                            for label, report in (('変更前', before), ('変更後', after)))
    html = ('<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            '<title>WCAG検査票の前後比較</title><style>body{font:1rem/1.6 sans-serif;margin:1rem}'
            'table{width:100%;table-layout:fixed;border-collapse:collapse}th,td{border:1px solid #777;'
            'padding:.4rem;text-align:left;vertical-align:top;overflow-wrap:anywhere}</style>'
            '<main><h1>WCAG検査票の前後比較</h1>'
            f'<p>WCAG 2.2 {escape(result["level"])}。記録された観測対象ごとの比較です。</p>'
            f'{scope_note}<p>{completion}</p><p>{references}</p>{"".join(sections)}</main></html>')
    with destination.open('x', encoding='utf-8') as file:
        file.write(html)
