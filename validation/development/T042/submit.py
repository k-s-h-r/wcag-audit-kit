"""Attach reviewed evidence to the matching case, record it, and refresh the report."""

import argparse
from pathlib import Path
from zipfile import ZipFile

from collect import HERE, PLAN, cli, digest, load, save


EVIDENCE = ('observation.json', 'source-case.json', 'input-events.json', 'browser-requests.json',
            'main-frame-documents.json', 'http-receipts.json', 'before.html', 'after.html',
            'before.png', 'after.png')


def case_rows(report, criterion):
    return {case['case_id']: case for case in report['cases'] if case['criterion'] == criterion}


def attach(run, case_id, source, output):
    cli('attach', '--run', run, '--case', case_id, '--file', source, destination=output)
    path = output.read_text().strip()
    if (not path.startswith(f'evidence/attached/{case_id}/')
            or digest(run / 'work' / path) != digest(source)):
        raise ValueError('添付が元の検査票又は原本と一致しない')
    return path


def validate_manual(area, packet, handoff, env, judgment):
    record = load(area / 'source-case.json')
    case = packet['case']
    expected = {'case_id': handoff['environments'][env]['case_id'], 'state': 'initial',
                'environment': env, 'page_url': handoff['url'], 'graph_digest': handoff['graph_digest']}
    if (any(record[key] != value for key, value in expected.items())
            or any(case[key] != record[key] for key in ('case_id', 'environment', 'page_url', 'state'))
            or (record['original_trace'] is not None) != (handoff['environments'][env]['item'] is not None)):
        raise ValueError('追試を行った状態・画面幅と検査票が一致しない')
    observed = load(area / 'observation.json')
    if observed['new_document'] != judgment['new_document'] or observed['keydown_count'] != 1:
        raise ValueError('追試の到達と記録する所見が一致しない')
    return record


def record_for(case_id, packet, plan, decision, paths):
    target = {'target': '氏名入力欄 #subject', 'observed': decision['observed'],
              'expected': 'フォーカスを受けただけで利用者の文脈が変わらない。',
              'outcome': decision['target_outcome'], 'evidence': paths}
    return {'case_id': case_id, 'config_digest': packet['config_digest'],
            'normative_sha256': packet['criterion']['normative_sha256'],
            'base_assessment': packet['case']['assessment'],
            'execution': 'completed', 'outcome': decision['outcome'],
            'observed': decision['observed'], 'coverage_complete': False,
            'conditions_reviewed': False, 'exceptions_reviewed': True,
            'remaining': decision['remaining'], 'evidence': paths, 'targets': [target],
            'tests_applied': plan['checkpoints'],
            'steps_executed': [
                '初期レポートとpage-nextで操作後の不足を確かめ、該当する初期状態と画面幅の検査票を取得する。',
                '新しいChromiumの状態で同じURLを開く。初期画面で押すキーはTabを1回。',
                '前後のURL、表示、フォーカス、主文書とHTTP受信を照合し、押下後1秒の範囲で判断する。',
            ],
            'method_coverage': [
                {'method': 'keyboard', 'status': 'executed', 'reason': '実ブラウザーに届いたTabとフォーカスの順序を照合した。'},
                {'method': 'flow', 'status': 'executed', 'reason': '初期状態の1操作について前後の文書とサーバー受信を照合した。'},
            ]}


def verify_final(run, initial, outcome, handoff, attachments, old_graph, criterion):
    report = load(run / 'data/report.json')
    before = load(initial / 'data/report.json')
    old_rows, new_rows = case_rows(before, criterion), case_rows(report, criterion)
    if (old_rows.keys() != new_rows.keys() or new_rows.keys() != attachments.keys()
            or any(before[key] != report[key] for key in ('machine_checks', 'report_scope', 'url'))
            or digest(run / 'work/exploration.json') != old_graph):
        raise ValueError('同じ検査票・機械検査・原始探索を保持していない')
    old_others = [case for case in before['cases'] if case['criterion'] != criterion]
    if old_others != [case for case in report['cases'] if case['criterion'] != criterion]:
        raise ValueError('対象外の基準の検査票が変更された')
    for case_id, row in new_rows.items():
        assessment = row['assessment_data']
        if (old_rows[case_id]['outcome'] != 'not_run' or row['outcome'] != outcome
                or row['environment'] != old_rows[case_id]['environment']
                or row['state'] != old_rows[case_id]['state'] or assessment['coverage_complete']
                or not assessment['remaining'] or attachments[case_id] != assessment['evidence']
                or any(digest(run / 'work' / proof['path']) != proof['sha256']
                       for proof in assessment['verified_evidence'])):
            raise ValueError('保存した対象、未確認、添付原本を帳票から確認できない')
    expected_scope = 'does_not_conform' if outcome == 'failed' else 'unverified'
    original_scope = before['scope_conformance']['status']
    result = report['scope_conformance']
    if (original_scope != 'unverified' or result['status'] != expected_scope
            or report['audit_complete'] or not result['remaining']):
        raise ValueError('範囲の結論又は未確認の表示が異なる')
    prior = load(initial / 'next.json')['exploration']
    removed = {item['item'] for item in handoff['environments'].values() if item['item']}
    remaining = report['exploration']['remaining']
    if remaining != [note for note in prior['remaining'] if note not in removed]:
        raise ValueError('対象の不足以外の探索残件が変化した')
    html = (run / 'reports/report.html').read_text()
    issues = (run / 'reports/details/issues.md').read_text()
    with ZipFile(run / 'reports/report.xlsx') as payload:
        excel = b'\n'.join(payload.read(name) for name in payload.namelist()
                           if name.startswith('xl/worksheets/') or name == 'xl/sharedStrings.xml').decode()
        links = b'\n'.join(payload.read(name) for name in payload.namelist()
                           if name.startswith('xl/worksheets/_rels/')).decode()
    for case_id, paths in attachments.items():
        if (case_id not in html or case_id not in excel
                or paths[0] not in html or paths[0] not in excel
                or outcome == 'failed' and paths[0] not in links
                or (case_id in issues) != (outcome == 'failed')):
            raise ValueError('HTML・Excel・不適合一覧で同じ検査票や証拠を照合できない')
    return {'checksheet_case_ids': list(new_rows), 'outcome': outcome,
            'scope_before': original_scope, 'scope_after': result['status'],
            'resolved_items': len(removed), 'remaining_items': len(remaining),
            'unexplored_routes': prior['pending_routes'], 'evidence': attachments}


def submit(output):
    if digest(output / 'plan.json') != digest(PLAN):
        raise ValueError('通常収集と帳票への記録で事前条件が一致しない')
    plan = load(output / 'plan.json')
    handoff = load(output / 'handoff.json')
    judgments = load(HERE / 'observed-judgments.json')
    processed = {}
    for case, selected in handoff.items():
        area = output / case
        run = area / 'page'
        before = area / 'before'
        after = area / 'after'
        after.mkdir(exist_ok=False)
        previous_graph = digest(run / 'work/exploration.json')
        decision = judgments[case]
        attachments, resolution_count = {}, 0
        for env, item in selected['environments'].items():
            ledger_id = item['case_id']
            packet = load(before / f'case-{env}.json')
            manual = output / 'manual' / case / env
            reviewed = validate_manual(manual, packet, selected, env, decision)
            path = after / env
            path.mkdir()
            paths = [attach(run, ledger_id, manual / name, path / f'attach-{name}.log') for name in EVIDENCE]
            if reviewed['original_trace']:
                stop = reviewed['original_trace']
                if digest(run / 'work' / stop['path']) != stop['sha256']:
                    raise ValueError('標準探索の停止記録が変更された')
                paths.append(stop['path'])
            attachments[ledger_id] = paths
            request = path / 'judgment.json'
            save(request, record_for(ledger_id, packet, plan, decision, paths))
            cli('record', '--run', run, '--file', request, destination=path / 'record.log')
            if item['item']:
                resolution = path / 'resolution.json'
                save(resolution, {'graph_digest': selected['graph_digest'],
                                  'resolutions': [{'item': item['item'], 'observed': decision['observed'],
                                                   'evidence': paths}]})
                answer = path / 'resolve.log'
                cli('resolve-exploration', '--run', run, '--file', resolution, destination=answer)
                resolution_count += 1
                if load(answer)['total_resolved'] != resolution_count:
                    raise ValueError('同じ探索版の解消記録が累積されない')
        cli('page-report', '--run', run, '--page-exact', selected['url'], destination=after / 'report.log')
        next_file = after / 'next.json'
        cli('page-next', '--run', run, '--page-exact', selected['url'], destination=next_file)
        if load(next_file)['exploration']['graph_digest'] != selected['graph_digest']:
            raise ValueError('追加確認で原始探索の版が変化した')
        processed[case] = verify_final(run, before, decision['outcome'], selected, attachments,
                                       previous_graph, plan['criterion'])
        print(case, 'verified', flush=True)
    save(output / 'checks.json', processed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    submit(parser.parse_args().run.resolve())
