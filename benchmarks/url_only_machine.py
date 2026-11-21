#!/usr/bin/env python3
"""Measure the ordinary single-page workflow on all machine-target rows."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import version
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmarks import core, runner


CLI = core.ROOT / 'skills/wcag-page/scripts/audit.py'
INITIAL = ('--level', 'AAA', '--mode', 'machine', '--screenshots', 'initial', '--initial-only')
EXPLORE = ('--resume', '--quick-explore')


def inventory(corpus):
    pages = defaultdict(list)
    for suite in corpus['suites']:
        criterion = suite['criterion']
        for case in suite['cases']:
            for row in case['expectations']:
                if core.verification_group(row) == 'machine_target':
                    pages[criterion, row['page']].append({
                        **row, 'criterion': criterion, 'case': case['id'],
                    })
    return [
        dict(id=f'{index:03}', criterion=criterion, page=page, rows=rows)
        for index, ((criterion, page), rows) in enumerate(pages.items(), 1)
    ]


def collect_page(url, location):
    location.mkdir()
    command = [sys.executable, str(CLI), 'page-audit', '--url', url, '--out', str(location / 'page')]
    commands = (command + list(INITIAL), command + list(EXPLORE))
    phases = {}
    for phase, args in zip(('initial', 'explore'), commands):
        with (location / f'{phase}.log').open('w') as stream:
            print(json.dumps(args, ensure_ascii=False), file=stream, flush=True)
            try:
                result = subprocess.run(args, stdout=stream, stderr=subprocess.STDOUT,
                                        check=False, timeout=240)
                phases[phase] = result.returncode
            except subprocess.TimeoutExpired:
                phases[phase] = 'timeout'
        if phases[phase] != 0:
            break
    core.save(location / 'collection.json', dict(url=url, phases=phases))
    print(f'{location.name}: {phases}', flush=True)


def collect(output, workers):
    from playwright.sync_api import sync_playwright

    output.mkdir(parents=True, exist_ok=False)
    corpus = core.corpus()
    pages = inventory(corpus)
    totals = Counter(row['expected'] for page in pages for row in page['rows'])
    with sync_playwright() as playwright:
        with playwright.chromium.launch(executable_path=shutil.which('chromium')) as browser:
            chromium = browser.version
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=core.ROOT, text=True).strip()
    public = output / 'public'
    locations = output / 'pages'
    locations.mkdir()
    directories = {}
    for page in pages:
        criterion = page['criterion']
        if criterion not in directories:
            name = f's{len(directories) + 1:02}'
            shutil.copytree(core.ROOT / 'benchmarks/cases' / criterion / 'public', public / name)
            directories[criterion] = name
        page['path'] = directories[criterion] + '/' + page['page']
    core.save(output / 'inventory.json', dict(
        commit=commit, corpus_digest=corpus['digest'], totals=dict(totals), pages=pages,
        initial_args=INITIAL, explore_args=EXPLORE, workers=workers,
        environment=dict(system=platform.platform(), python=platform.python_version(),
                         playwright=version('playwright'), chromium=chromium),
    ))
    http = runner.server(public)
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            jobs = [
                pool.submit(collect_page, f'http://127.0.0.1:{http.server_port}/{page["path"]}',
                            locations / page['id'])
                for page in pages
            ]
            for job in jobs:
                job.result()
    finally:
        http.shutdown()
        http.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--score', type=Path, metavar='RESULT_JSON',
                        help='score a collected run and save the result at a new path')
    args = parser.parse_args()
    if args.score:
        from benchmarks.url_only_machine_score import score

        result = score(args.out.resolve())
        with args.score.open('x') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            print(file=stream)
        print(json.dumps({key: result[key] for key in ('completed_pages', 'problems', 'controls')},
                         ensure_ascii=False, indent=2))
    else:
        if args.workers < 1:
            parser.error('--workers must be positive')
        collect(args.out.resolve(), args.workers)
