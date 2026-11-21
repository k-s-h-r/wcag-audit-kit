"""Collect the nested Escape scheduling controls with the ordinary page CLI."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from benchmarks import core, runner, url_only_machine


FIXTURES = {
    '045': ('2.1.2', 'p07.html'), '046': ('2.1.2', 'p08.html'),
    '062': ('2.4.3', 'p07.html'), '063': ('2.4.3', 'p08.html'),
    '039': ('2.1.2', 'p01.html'), '040': ('2.1.2', 'p02.html'),
    '064': ('2.4.3', 'p09.html'), '065': ('2.4.3', 'p10.html'),
}


def collect_page(location, url, *, pause_after_parent=False):
    location.mkdir()
    command = [sys.executable, str(url_only_machine.CLI), 'page-audit', '--url', url, '--out', str(location / 'page')]
    plan = [('initial', url_only_machine.INITIAL)]
    if pause_after_parent:
        plan.append(('pause', (*url_only_machine.EXPLORE, '--max-steps', '6')))
    plan.append(('explore', url_only_machine.EXPLORE))
    phases = {}
    for phase, flags in plan:
        with (location / (phase + '.log')).open('w') as log:
            print(json.dumps(command + list(flags)), file=log, flush=True)
            result = subprocess.run(command + list(flags), stdout=log, stderr=subprocess.STDOUT, timeout=600)
        phases[phase] = result.returncode
        result.check_returncode()
        if phase == 'pause':
            shutil.copyfile(location / 'page/work/exploration.json', location / 'exploration-at-6.json')
    core.save(location / 'collection.json', {'url': url, 'phases': phases})
    print(location.name, phases, flush=True)


def collect(output, supplemental_only):
    output.mkdir(parents=True)
    public = output / 'public'
    for criterion in sorted({criterion for criterion, _ in FIXTURES.values()}):
        shutil.copytree(ROOT / 'benchmarks/cases' / criterion / 'public', public / criterion)
    pointer_listener = public / '2.1.2/p07-pointer-listener.html'
    source = (public / '2.1.2/p07.html').read_text()
    pointer_listener.write_text(source.replace('</script>',
        ';document.addEventListener("click", () => { window.fixtureClicks = (window.fixtureClicks || 0) + 1 });</script>'))
    corpus = core.corpus()
    pages = [page for page in url_only_machine.inventory(corpus) if page['id'] in FIXTURES]
    core.save(output / 'inventory.json', dict(
        commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        corpus_digest=corpus['digest'], pages=pages, workers=1, environment=runner.environment(),
        totals=dict(Counter(row['expected'] for page in pages for row in page['rows'])),
        initial_args=url_only_machine.INITIAL, explore_args=url_only_machine.EXPLORE,
    ))
    inputs = {case: {'path': f'{criterion}/{page}', 'sha256': core.file_hash(public / criterion / page)}
              for case, (criterion, page) in FIXTURES.items()}
    inputs['pointer-listener'] = {'path': '2.1.2/' + pointer_listener.name, 'sha256': core.file_hash(pointer_listener)}
    core.save(output / 'fixtures.json', inputs)
    (output / 'pages').mkdir()
    server = runner.server(public)
    prefix = f'http://127.0.0.1:{server.server_port}/'
    try:
        if not supplemental_only:
            for case in FIXTURES:
                collect_page(output / 'pages' / case, prefix + inputs[case]['path'])
        collect_page(output / 'pages/resumed', prefix + inputs['045']['path'], pause_after_parent=True)
        collect_page(output / 'pages/pointer-listener', prefix + inputs['pointer-listener']['path'])
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--supplemental-only', action='store_true')
    args = parser.parse_args()
    collect(args.out.resolve(), args.supplemental_only)
