"""Collect the existing keyboard-trap suite through ordinary page-audit."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import version
from pathlib import Path
import platform
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from benchmarks import core, runner, url_only_machine
from benchmarks.url_only_machine_score import score
from playwright.sync_api import sync_playwright


def measure(out, checkout, workers):
    out.mkdir(parents=True)
    corpus = core.corpus()
    pages = [page for page in url_only_machine.inventory(corpus) if page['criterion'] == '2.1.2']
    totals = Counter(row['expected'] for page in pages for row in page['rows'])
    public = out / 'public'
    shutil.copytree(core.ROOT / 'benchmarks/cases/2.1.2/public', public)
    (out / 'pages').mkdir()
    with sync_playwright() as playwright:
        with playwright.chromium.launch(executable_path=shutil.which('chromium')) as browser:
            chromium = browser.version
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip()
    core.save(out / 'inventory.json', dict(
        commit=commit, corpus_digest=corpus['digest'], pages=pages, totals=dict(totals), workers=workers,
        initial_args=url_only_machine.INITIAL, explore_args=url_only_machine.EXPLORE,
        environment=dict(system=platform.platform(), python=platform.python_version(),
                         playwright=version('playwright'), chromium=chromium),
    ))
    url_only_machine.CLI = checkout / 'skills/wcag-page/scripts/audit.py'
    server = runner.server(public)
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            jobs = [pool.submit(url_only_machine.collect_page,
                                f'http://127.0.0.1:{server.server_port}/{page["page"]}',
                                out / 'pages' / page['id']) for page in pages]
            for job in jobs:
                job.result()
    finally:
        server.shutdown()
        server.server_close()
    core.save(out / 'score.json', score(out))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--checkout', type=Path, default=core.ROOT)
    parser.add_argument('--workers', type=int, default=4)
    options = parser.parse_args()
    if options.workers < 1:
        parser.error('--workers must be positive')
    measure(options.out.resolve(), options.checkout.resolve(), options.workers)
