"""Re-run the initial native button spacing cases through the ordinary page CLI."""
import argparse
from collections import Counter
from importlib.metadata import version
from pathlib import Path
import platform
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from benchmarks import core, runner, url_only_machine
from benchmarks.url_only_machine_score import score
from target_spacing import CHECKPOINT, EVIDENCE_FILE


CONTROLS = {
    'p01.html': 'failed', 'p02.html': 'passed', 'p03.html': 'failed', 'p04.html': 'passed', 'p05.html': None,
    'spacing-exact.html': 'passed', 'spacing-under.html': 'failed', 'ancestor-crop.html': None,
    'off-grid-cover.html': None, 'pseudo-hit-extension.html': None, 'ua-size.html': None,
    'extra-target.html': None, 'closed-shadow.html': None,
}


def public_pages(output):
    public = output / 'public'
    shutil.copytree(ROOT / 'benchmarks/cases/2.5.8/public', public)
    small = (public / 'p03.html').read_text()
    large = (public / 'p04.html').read_text()
    variants = {
        'spacing-exact.html': small.replace('gap:2px', 'gap:8px'),
        'spacing-under.html': small.replace('gap:2px', 'gap:7.984375px'),
        'ancestor-crop.html': large.replace('display:flex;gap:2px', 'display:flex;gap:2px;overflow:hidden;height:27.5px'),
        'off-grid-cover.html': small.replace('display:flex;gap:2px', 'display:flex;gap:2px;position:relative').replace(
            '</div></main>', '<span style="position:absolute;left:4px;top:4px;width:1px;height:1px;opacity:0"></span></div></main>'),
        'pseudo-hit-extension.html': small.replace('</style>',
            'button{position:relative}button::before{content:"";position:absolute;inset:-4px}</style>'),
        'ua-size.html': small.replace('button{padding:.4rem}', '').replace('button,input,select,textarea{font:inherit}', '')
            .replace(' style="box-sizing:border-box;padding:0;width:16px;height:16px"', ''),
        'extra-target.html': small.replace('display:flex;gap:2px', 'display:flex;gap:8px;position:relative').replace(
            '</div></main>', '<a href="target-help.html" aria-disabled="true" style="position:absolute;left:18px;top:5px;'
            'width:4px;height:7px;opacity:0">別</a></div></main>'),
        'closed-shadow.html': small.replace('</div></main>',
            '<div style="display:contents"><template shadowrootmode="closed"><a href="target-help.html" '
            'style="position:absolute;left:48px;top:115px;width:2px;height:8px">別</a></template></div></div></main>'),
    }
    for page, content in variants.items():
        (public / page).write_text(content)
    return public


def run_initial(location, url):
    location.mkdir(parents=True)
    args = [sys.executable, str(url_only_machine.CLI), 'page-audit', '--url', url,
            '--out', str(location / 'page'), *url_only_machine.INITIAL]
    core.save(location / 'command.json', args)
    with (location / 'initial.log').open('w') as log:
        subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, timeout=300, check=True)


def checks(location, outcome, output):
    run = location / 'page'
    work = run / 'work'
    graph = core.load(work / 'exploration.json')
    report = core.load(run / 'data/report.json')
    html = (run / 'reports/report.html').read_text()
    assert not report['audit_complete'] and report['scope_conformance']['status'] == 'unverified'
    rows = [row for row in report['machine_checks'] if row['checkpoint'] == CHECKPOINT]
    proof = {item['path']: item['sha256'] for item in graph['proof']}
    assert len(rows) == (4 if outcome else 0), (location, rows)
    assert {row['outcome'] for row in rows} == ({outcome} if outcome else set())
    assert {row['environment'] for row in rows} == ({'desktop', 'narrow'} if outcome else set())
    for row in rows:
        assert row['state_label'] == '初期表示' and row['evidence'].endswith(EVIDENCE_FILE)
        assert row['evidence'] in html
        for path in [row['evidence'], *row['proof']]:
            assert core.file_hash(work / path) == proof[path]
        row['evidence'] = (work / row['evidence']).relative_to(output).as_posix()
        row['proof'] = [(work / path).relative_to(output).as_posix() for path in row['proof']]
    return rows


def main(output):
    output.mkdir(parents=True)
    public = public_pages(output)
    inventory = core.corpus()
    pages = [page for page in url_only_machine.inventory(inventory) if page['criterion'] == '2.5.8']
    indices = {page['page']: page['id'] for page in pages}
    assert indices == {'p03.html': '068', 'p04.html': '069', 'p05.html': '070'}
    core.save(output / 'inventory.json', dict(
        commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        corpus_digest=inventory['digest'], pages=pages, workers=1,
        initial_args=url_only_machine.INITIAL, explore_args=url_only_machine.EXPLORE,
        totals=dict(Counter(row['expected'] for page in pages for row in page['rows'])),
        environment=dict(system=platform.platform(), python=platform.python_version(),
                         chromium=subprocess.check_output(['chromium', '--version'], text=True).split()[1],
                         playwright=version('playwright')),
    ))
    (output / 'pages').mkdir()
    server = runner.server(public)
    results = {}
    try:
        for name in [*indices, *(page for page in CONTROLS if page not in indices)]:
            url = f'http://127.0.0.1:{server.server_port}/{name}'
            if name in indices:
                location = output / 'pages' / indices[name]
                url_only_machine.collect_page(url, location)
                assert core.load(location / 'collection.json')['phases'] == {'initial': 0, 'explore': 0}
            else:
                location = output / 'controls' / name.removesuffix('.html')
                run_initial(location, url)
            results[name] = checks(location, CONTROLS[name], output)
            core.save(output / 'observations.json', results)
            print(name, len(results[name]), flush=True)
    finally:
        server.shutdown()
        server.server_close()
    scored = score(output)
    assert scored['completed_pages'] == 3 and not scored['unmatched_findings']
    assert Counter(row['status'] for row in scored['rows']) == {'detected': 2, 'matched': 2, 'observed_no_verdict': 1}
    core.save(output / 'score.json', scored)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    main(parser.parse_args().out.resolve())
