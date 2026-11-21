"""Verify closed-to-open and return-and-close routes through page-audit."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmarks import core, runner, url_only
from keyboard_checks import matching_keydown


PROFILE = ['--quick-explore', '--max-steps', '48', '--max-states', '24', '--max-depth', '4']
CHECKPOINT = 'キー操作後の領域の表示とフォーカス'


def load_case(output):
    run = core.audit.run_layout.ledger(output / 'page')
    return run, core.load(run / 'exploration.json'), core.load(output / 'page/data/report.json')


def edge_for(graph, environment, sequence):
    return next(edge for edge in graph['edges'] if edge['environment'] == environment
                and [(step['type'], step['selector'], step.get('key')) for step in edge['route']] == sequence)


def verify_return(output, opener, tab_destination, *, closes=True):
    run, graph, report = load_case(output)
    start = [('key', opener, 'Enter')]
    tab = start + [('press', 'body', 'Tab')]
    close = tab + [('press', 'body', 'Shift+Tab'), ('key', opener, 'Enter')]
    for environment in ('desktop', 'narrow'):
        assert edge_for(graph, environment, start)['disclosure_toggle']['status'] == 'opened'
        assert edge_for(graph, environment, tab)['focus_after'] == tab_destination
        edge = edge_for(graph, environment, close)
        record = edge['disclosure_return']
        evidence = run / edge['evidence_dir']
        events = core.load(evidence / 'input-events.json')['events']
        returned = events[record['event_index']]
        final_key = events[edge['key_effect']['event_index']]
        assert returned['expectedTargetMatched'] and matching_keydown(returned, 'Shift+Tab')
        assert final_key['expectedTargetMatched'] and matching_keydown(final_key, 'Enter')
        assert record['before']['focus'] == tab_destination and record['after']['focus'] == opener
        assert edge['disclosure_toggle']['status'] == ('closed' if closes else 'cant_tell')
        transition = f"{edge['evidence_dir']}/transition.json"
        row = next(row for row in report['machine_checks']
                   if row['evidence'] == transition and row['checkpoint'] == CHECKPOINT)
        assert row['outcome'] == ('passed' if closes else 'cant_tell'), row


def verify_opening_unknown(output, *, pointer_opens):
    run, graph, report = load_case(output)
    opener = '#subject #inner-action'
    for environment in ('desktop', 'narrow'):
        click = edge_for(graph, environment, [('click', opener, None)])
        states = core.load(run / click['evidence_dir'] / 'state.json')['state']
        if pointer_opens:
            assert any(state['selector'] == '#subject #inner-panel' for state in states)
        keyboard = edge_for(graph, environment, [('key', opener, 'Enter')])
        assert keyboard['disclosure_toggle']['status'] == ('stayed_closed' if pointer_opens else 'cant_tell')
        evidence = f"{keyboard['evidence_dir']}/transition.json"
        assert any(row['checkpoint'] == CHECKPOINT and row['evidence'] == evidence
                   and row['outcome'] == 'cant_tell' for row in report['machine_checks'])


def main(output):
    public = output / 'public'
    public.mkdir(parents=True, exist_ok=False)
    cases = core.ROOT / 'benchmarks/cases/2.1.1/public'
    for filename in ('p06.html', 'p07.html'):
        shutil.copyfile(cases / filename, public / filename)
    shutil.copyfile(core.ROOT / 'tests/fixtures/page-workflow.html', public / 'page-workflow.html')
    shadow = (cases / 'p07.html').read_text()
    (public / 'transparent.html').write_text(shadow.replace(
        'id="inner-panel" hidden', 'id="inner-panel" style="opacity:0" hidden'))
    (public / 'contents.html').write_text(shadow.replace(
        'panel.hidden=!panel.hidden;', 'if(panel.hidden){panel.hidden=false;} else {panel.style.display="contents";}')
        .replace('String(!panel.hidden)', 'String(panel.style.display!=="contents")'))
    (public / 'navigation.html').write_text(shadow.replace(
        '<div id="subject"></div>', '<nav><div id="subject"></div></nav>'))
    http = runner.server(public)
    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            cases = ('page-workflow', 'p06', 'p07', 'transparent', 'contents', 'navigation')
            jobs = {name: pool.submit(url_only.collect_page, f'http://127.0.0.1:{http.server_port}/{name}.html',
                                      output / name, PROFILE) for name in cases}
            for name, job in jobs.items():
                assert job.result(), name
    finally:
        http.shutdown()
        http.server_close()
    verify_return(output / 'page-workflow', '#accordion', '#nested')
    verify_return(output / 'p07', '#subject #inner-action', '#after')
    verify_return(output / 'contents', '#subject #inner-action', '#after', closes=False)
    verify_opening_unknown(output / 'p06', pointer_opens=True)
    verify_opening_unknown(output / 'transparent', pointer_opens=False)
    _, navigation, _ = load_case(output / 'navigation')
    for environment in ('desktop', 'narrow'):
        edge = edge_for(navigation, environment, [('key', '#subject #inner-action', 'Enter')])
        assert edge['key_effect']['after']['expanded'] == 'true' and 'disclosure_toggle' not in edge
    print('Accordion and Shadow DOM routes verified in both viewports')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out.resolve())
