#!/usr/bin/env python3
"""Measure the ordinary single-page workflow on all machine-target rows."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
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
                    record = {**row, 'criterion': criterion, 'case': case['id']}
                    if row['checkpoint'] == '2.1.1-02' and row['state'] == 'initial':
                        state = next(state for state in case['states'] if state['id'] == row['state'])
                        record['function_probe'] = state.get('residual_probe')
                    pages[criterion, row['page']].append(record)
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--score', type=Path, metavar='RESULT_JSON',
                        help='score a collected run and save the result at a new path')
    parser.add_argument('--report', action='store_true', help='write the score and an HTML report')
    parser.add_argument('--baseline', type=Path, metavar='SCORE_JSON', help='compare with an earlier score in the report')
    args = parser.parse_args(argv)
    if args.baseline and not args.report:
        parser.error('--baseline requires --report')
    if not args.score and args.workers < 1:
        parser.error('--workers must be positive')

    output = args.out.resolve()
    score_path = (args.score or output / 'score.json').resolve()
    html_path = score_path.with_suffix('.html')
    try:
        baseline = core.load(args.baseline) if args.baseline else None
        if args.baseline and not isinstance(baseline, dict):
            raise ValueError('基準にURL起点の採点JSONを指定してください')
        if args.report and (score_path == html_path or score_path.exists() or html_path.exists()):
            raise ValueError('採点JSONとHTMLの新しい出力先を指定してください')
        if not args.score:
            collect(output, args.workers)
        if not (args.score or args.report):
            return 0

        from benchmarks.url_only_machine_score import score

        result = score(output)
        console = {key: result[key] for key in ('completed_pages', 'problems', 'controls')}
        report = None
        if args.report:
            from benchmarks import url_only_machine_report as reporting

            result['scorer_digest'] = reporting.scorer_digest()
            result['summary'] = reporting.summary(result)
            console['summary'] = result['summary']
            if baseline is not None:
                result['comparison'] = reporting.compare(baseline, result)
                console['comparison'] = {key: len(result['comparison'][key]) for key in
                                         ('regressions', 'improvements', 'other_changes')}
            report = reporting.render(result, output, html_path, score_path.name)
            console['files'] = dict(json=str(score_path), html=str(html_path))
        with ExitStack() as rollback:
            with score_path.open('x', encoding='utf-8') as stream:
                rollback.callback(score_path.unlink, missing_ok=True)
                json.dump(result, stream, ensure_ascii=False, indent=2)
                print(file=stream)
            if report is not None:
                with html_path.open('x', encoding='utf-8') as stream:
                    rollback.callback(html_path.unlink, missing_ok=True)
                    stream.write(report)
            rollback.pop_all()
        print(json.dumps(console, ensure_ascii=False, indent=2))
        return int(bool(result.get('comparison', {}).get('regressions')))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    raise SystemExit(main())
