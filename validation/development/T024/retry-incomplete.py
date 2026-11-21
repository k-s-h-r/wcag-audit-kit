"""Retry only incomplete T020 pages into a separate run."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import subprocess
import sys


def main(source, destination, repository):
    sys.path.insert(0, str(repository))
    from benchmarks import core, runner, url_only_machine
    from benchmarks.url_only_machine_score import score

    inventory = core.load(source / 'inventory.json')
    statuses = {p['id']: core.load(source / 'pages' / p['id'] / 'collection.json')['phases']
                for p in inventory['pages']}
    retry = [p for p in inventory['pages'] if statuses[p['id']] != {'initial': 0, 'explore': 0}]
    if not retry:
        return
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repository, text=True).strip()
    if inventory['commit'] != commit:
        raise ValueError('The checkout must match the source run commit.')
    destination.mkdir(parents=True)
    shutil.copytree(source / 'public', destination / 'public')
    (destination / 'pages').mkdir()
    totals = Counter(row['expected'] for page in retry for row in page['rows'])
    core.save(destination / 'inventory.json', dict(inventory, pages=retry, totals=dict(totals), workers=2))
    http = runner.server(destination / 'public')
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(url_only_machine.collect_page,
                                f'http://127.0.0.1:{http.server_port}/{page["path"]}',
                                destination / 'pages' / page['id']) for page in retry]
            for job in jobs:
                job.result()
    finally:
        http.shutdown()
        http.server_close()
    core.save(destination / 'score.json', score(destination))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('repository', type=Path)
    args = parser.parse_args()
    main(args.source.resolve(), args.destination.resolve(), args.repository.resolve())
