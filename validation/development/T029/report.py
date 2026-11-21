"""Record independent observations in the corresponding AI-mode cases and check the reports."""
import argparse
from hashlib import sha256
from html import escape
import json
from pathlib import Path
from shutil import copytree
import subprocess
import sys
from urllib.parse import urlsplit

from openpyxl import load_workbook


def invoke(cli, *args):
    process = subprocess.run([sys.executable, str(cli), *map(str, args)], check=True,
                             capture_output=True, text=True)
    return process.stdout.strip()


def load(path):
    return json.loads(path.read_text())


def snapshot(directory):
    return {str(path.relative_to(directory)):sha256(path.read_bytes()).hexdigest()
            for path in directory.rglob('*') if path.is_file()}


def initial_case(ledger, url, mode):
    plan = load(ledger/'work/plan.json')
    case, = [row for row in plan['cases'] if row['criterion']=='1.4.1' and row['page_url']==url
             and row['state']=='initial' and row['environment']=='desktop']
    assert case['assessment'] is None, case['case_id']
    config = load(ledger/'work/run.json')['config']
    assert config['verification']['mode']==mode and config['level']=='AA'
    assert config['scope']['pages']==[url]
    assert config['environments'][0]['viewport']=={'width':1280, 'height':900}
    return case


def record(cli, ledger, case, observation, evidence_dir, record_file):
    url = observation['calendar_url']
    case_info = json.loads(invoke(cli, 'case', '--run', ledger, '--id', case['case_id']))
    assert observation['initial_image'] in observation['evidence']
    initial_capture = ledger/'work'/case['evidence_dir']/'page.png'
    proof = []
    for filename in observation['evidence']:
        source = (evidence_dir/filename).resolve()
        assert source.is_relative_to(evidence_dir) and source.is_file(), filename
        if filename == observation['initial_image']:
            assert source.read_bytes() == initial_capture.read_bytes(), (url, filename)
        path = invoke(cli, 'attach', '--run', ledger, '--case', case['case_id'], '--file', source)
        assert (ledger/'work'/path).read_bytes() == source.read_bytes()
        proof.append({'path':path, 'original':filename, 'sha256':sha256(source.read_bytes()).hexdigest()})
    files = [item['path'] for item in proof]
    target_outcome = observation['outcome']
    case_outcome = 'failed' if target_outcome == 'failed' else 'cant_tell'
    target = {'target':'日付ボタン（5月10日から16日）の選択前の空き状況',
              'expected':'選択前に、色以外の視覚的な手がかりでも空きありと満席を区別できる。',
              'observed':observation['observed'], 'outcome':target_outcome, 'evidence':files}
    judgment = {'case_id':case['case_id'], 'base_assessment':None, 'config_digest':case_info['config_digest'],
                'normative_sha256':case_info['criterion']['normative_sha256'], 'outcome':case_outcome,
                'execution':'completed', 'observed':observation['observed'], 'conditions_reviewed':True,
                'exceptions_reviewed':True, 'coverage_complete':False, 'remaining':observation['remaining'],
                'tests_applied':['1.4.1 / 色と選択前の視覚的な手がかりを比較'], 'steps_executed':observation['steps'],
                'evidence':files, 'targets':[target], 'method_coverage':[
                    {'method':'visual', 'status':'executed', 'reason':observation['visual']},
                    {'method':'semantic', 'status':'executed', 'reason':observation['semantic']},
                ]}
    record_file.write_text(json.dumps(judgment, ensure_ascii=False, indent=2)+'\n')
    invoke(cli, 'record', '--run', ledger, '--file', record_file)
    invoke(cli, 'page-report', '--run', ledger, '--page-exact', url)
    return case['case_id'], case_outcome, proof


def workbook_row(book, sheet, case_id):
    rows = iter(book[sheet].values)
    headers = next(rows)
    row, = [dict(zip(headers, values)) for values in rows if values[0]==case_id]
    return row


def confirm_outputs(ledger, case_id, case_outcome, observation):
    files = ('data/report.json', 'reports/report.html', 'reports/report.xlsx', 'reports/details/issues.md')
    report = load(ledger/files[0])
    case, = [row for row in report['cases'] if row['case_id']==case_id]
    assessment = case['assessment_data']
    assert case['outcome']==case_outcome and assessment['observed']==observation['observed']
    assert assessment['targets'][0]['outcome']==observation['outcome']
    assert not assessment['coverage_complete'] and assessment['remaining']==observation['remaining']
    assert report['audit_complete'] is False
    html = (ledger/files[1]).read_text()
    issues = (ledger/files[3]).read_text()
    assert escape(observation['observed']) in html
    assert all(escape(reason) in html for reason in observation['remaining'])
    case_label = '不適合' if case_outcome == 'failed' else '判断保留'
    assert f'{escape(observation["calendar_url"])}<br>initial / desktop</td><td>{case_label}</td>' in html
    target_label = '× 不適合' if observation['outcome'] == 'failed' else '○ 適合'
    target_text = escape(assessment['targets'][0]['expected'])
    assert f'{target_text}</td><td>あり</td><td>{target_label}</td>' in html
    assert all(Path(proof['path']).name in html for proof in assessment['verified_evidence'])
    assert (observation['observed'] in issues)==(case_outcome=='failed')
    book = load_workbook(ledger/files[2], read_only=True)
    try:
        row = workbook_row(book, '検査票', case_id)
        target = workbook_row(book, '対象', case_id)
        assert row['判定']==case_outcome and row['観察']==observation['observed']
        assert row['残る確認']=='\n'.join(observation['remaining'])
        assert target['判定']==observation['outcome'] and target['観察']==observation['observed']
        assert target['証拠']=='\n'.join(assessment['targets'][0]['evidence'])
    finally:
        book.close()
    return {filename:sha256((ledger/filename).read_bytes()).hexdigest() for filename in files}


def main(cli, machine, runs, observations_path, out):
    receipt = load(observations_path)
    assert receipt['viewport']==[1280,900] and len(receipt['observations'])==2
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for observation in receipt['observations']:
        site = urlsplit(observation['entry_url']).path.strip('/')
        calendar_url = observation['calendar_url']
        machine_source = machine/site/'calendar'
        machine_files = snapshot(machine_source)
        machine_case = initial_case(machine_source, calendar_url, 'machine')
        source = runs/site/'calendar'
        source_files = snapshot(source)
        case = initial_case(source, calendar_url, 'ai')
        assert machine_case['case_id']==case['case_id']
        observed_initial = (observations_path.resolve().parent/observation['initial_image']).resolve()
        assert observed_initial.is_relative_to(observations_path.resolve().parent)
        machine_initial = machine_source/'work'/machine_case['evidence_dir']/'page.png'
        ai_initial = source/'work'/case['evidence_dir']/'page.png'
        assert observed_initial.read_bytes()==machine_initial.read_bytes()==ai_initial.read_bytes(), calendar_url
        ledger = out/site/'calendar'
        copytree(source, ledger)
        case_id, case_outcome, proof = record(cli, ledger, case, observation, observations_path.resolve().parent,
                                             out/f'{site}.json')
        files = confirm_outputs(ledger, case_id, case_outcome, observation)
        assert snapshot(source)==source_files, source
        assert snapshot(machine_source)==machine_files, machine_source
        results.append({'case_id':case_id, 'url':observation['calendar_url'], 'target_outcome':observation['outcome'],
                        'case_outcome':case_outcome, 'remaining':observation['remaining'], 'files':files, 'proof':proof,
                        'initial_image_sha256':sha256(observed_initial.read_bytes()).hexdigest(),
                        'machine_file_count_unchanged':len(machine_files),
                        'source_file_count_unchanged':len(source_files),
                        'source_snapshot_sha256':sha256(json.dumps(source_files, sort_keys=True).encode()).hexdigest()})
    (out/'summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', required=True, type=Path)
    parser.add_argument('--machine', required=True, type=Path)
    parser.add_argument('--runs', required=True, type=Path)
    parser.add_argument('--observations', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    main(args.cli, args.machine, args.runs, args.observations, args.out)
