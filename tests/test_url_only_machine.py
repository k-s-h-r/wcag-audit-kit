import tempfile
import unittest
from collections import Counter
from pathlib import Path

from benchmarks import core, url_only_machine, url_only_machine_score as scoring
import target_spacing


def observations(*outcomes, reached=False):
    return dict(reached=['state.json'] if reached else [],
                verdicts=[dict(outcome=outcome) for outcome in outcomes])


class URLOnlyMachineTest(unittest.TestCase):
    def test_inventory_freezes_the_machine_rows_by_page(self):
        pages = url_only_machine.inventory(core.corpus())
        self.assertEqual(len(pages), 76)
        self.assertEqual(Counter(row['expected'] for page in pages for row in page['rows']),
                         {'failed': 39, 'passed': 47, 'inapplicable': 1})

    def test_classifies_each_row_once_and_keeps_unknown_controls(self):
        desktop = observations('failed')
        narrow = observations()
        envs = dict(desktop=desktop, narrow=narrow)
        self.assertEqual(scoring.classify('failed', envs, True), 'detected')
        self.assertEqual(scoring.classify('passed', envs, True), 'false_positive')
        self.assertEqual(scoring.classify('failed', envs, False), 'collection_error')
        envs['desktop'] = observations('passed')
        self.assertEqual(scoring.classify('passed', envs, True), 'observed_no_verdict')
        envs['narrow'] = observations('passed')
        self.assertEqual(scoring.classify('passed', envs, True), 'matched')
        self.assertEqual(scoring.classify('failed', envs, True), 'wrong_pass')
        envs['desktop'] = observations('passed', 'failed')
        self.assertEqual(scoring.classify('failed', envs, True), 'observed_no_verdict')
        self.assertEqual(scoring.classify('failed', {'desktop': observations()}, True),
                         'state_or_route_unobserved')

    def test_dispatch_is_not_a_function_verdict(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            edge = dict(route=[dict(type='key', selector='#control', key='Enter')], evidence_dir='edge')
            check = dict(checkpoint='実入力 / Enter', target='#control', evidence='edge/transition.json',
                         outcome='passed', observed='キーを送出した')
            row = dict(criterion='2.1.1', checkpoint='2.1.1-02', target='#control', state='initial')
            result = scoring.score_environment(row, [check], [edge], [], work, work)
            self.assertEqual(len(result['key_dispatch']), 1)
            self.assertEqual(result['verdicts'], [])
            row['checkpoint'] = '2.1.1-01'
            result = scoring.score_environment(row, [check], [edge], [], work, work)
            self.assertEqual(result['verdicts'][0]['outcome'], 'passed')

    def test_initial_axe_result_requires_a_matching_report_and_exact_target(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            evidence = work / 'edge'
            evidence.mkdir()
            core.save(evidence / 'state.json', dict(state=[dict(selector='#subject', tag='img')]))
            core.save(evidence / 'axe.json',
                      {'violations': [{'id': 'image-alt', 'nodes': [{'target': ['#subject']}]}]})
            edges = [dict(route=[], evidence_dir='edge')]
            transitions = list(scoring.initial_transitions(work, edges))
            row = dict(criterion='1.1.1', checkpoint='1.1.1-01', target='#subject', state='initial')
            only_raw = scoring.score_environment(row, [], edges, transitions, work, work)
            self.assertEqual(only_raw['verdicts'], [])
            check = dict(checkpoint='axe / image-alt', evidence='edge/axe.json',
                         outcome='failed', target="['#subject']", observed='altなし')
            reported = scoring.score_environment(row, [check], edges, transitions, work, work)
            self.assertEqual(reported['verdicts'][0]['outcome'], 'failed')
            wrong_target = scoring.score_environment(row, [dict(check, target="['#other']")],
                                                     edges, transitions, work, work)
            self.assertEqual(wrong_target['verdicts'], [])
            row['target'] = '#other'
            other = scoring.score_environment(row, [check], edges, transitions, work, work)
            self.assertEqual(other['verdicts'], [])

    def test_target_spacing_requires_the_report_and_exact_initial_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            evidence = work / 'initial'
            evidence.mkdir()
            url = 'http://127.0.0.1:8000/'
            targets = [dict(id=selector, x=x, y=0, width=16, height=16, explicit_size=True)
                       for selector, x in (('#a', 0), ('#b', 18))]
            for target in targets:
                target['hit_points'] = target_spacing.hit_points(target)
            controls = [dict(selector=target['id'], tag='button', formAssociated=False, events=[],
                             rect={key: target[key] for key in target_spacing.COORDINATES}) for target in targets]
            state = dict(url=url, controls=controls, state=[{'selector': control['selector']} for control in controls])
            record = dict(url=url, environment='desktop', unresolved=False, items=targets)
            edge = dict(route=[], evidence_dir='initial', environment='desktop')
            capture = dict(key='capture', environment='desktop', url=url, final_url=url)
            core.save(evidence / 'state.json', state)
            core.save(evidence / 'axe.json', {})
            core.save(evidence / 'transition.json', dict(edge, error=None, blocked_requests=[], native_events=[],
                                                         settling=[{'status': 'quiet'}]))
            core.save(evidence / target_spacing.EVIDENCE_FILE, record)
            graph = dict(nodes=[dict(edge, capture=capture['key'])], proof=[
                core.audit.evidence_item(work, path.relative_to(work).as_posix()) for path in evidence.iterdir()])
            transitions = list(scoring.initial_transitions(work, [edge]))
            row = dict(criterion='2.5.8', checkpoint='2.5.8-02', target='#a', state='initial')
            checks = list(target_spacing.report_rows(record, state, capture, 'initial/' + target_spacing.EVIDENCE_FILE,
                                                     'initial/state.json'))
            self.assertEqual(len(checks), 2)

            def outcomes(report_checks):
                return [result['outcome'] for result in scoring.score_environment(
                    row, report_checks, [edge], transitions, work, work, graph)['verdicts']]

            self.assertEqual(outcomes(checks), ['failed'])
            self.assertEqual(outcomes(checks[1:]), [])
            self.assertEqual(outcomes([dict(checks[0], capture='another')]), [])
            core.save(evidence / target_spacing.EVIDENCE_FILE, dict(record, environment='narrow'))
            self.assertEqual(outcomes(checks), [])

    def test_dialog_exit_requires_registered_unchanged_evidence(self):
        from keyboard_trap import CHECKPOINT

        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            evidence = work / 'escape'
            evidence.mkdir()
            url = 'http://127.0.0.1:8000/'
            enter = {'type': 'key', 'selector': '#open', 'key': 'Enter'}
            escape = {'type': 'press', 'selector': 'body', 'key': 'Escape'}
            opening = {'route': [enter], 'evidence_dir': 'opening'}
            exit_edge = dict(route=[enter, escape], evidence_dir='escape', dialog_focus='escape', environment='desktop')
            before = {'url': url, 'document_start': 17, 'within': True, 'modals': ['#panel']}
            after = dict(before, within=False, modals=[], supported=True, root_focus=False, shown=False)
            receipt = dict(target='#panel', outcome='passed', before=before, after_escape=after,
                           opener='#open', opener_event_index=0, escape_event_index=1, steps=[])
            events = [dict(type='keydown', key=key, isTrusted=True, is_main_frame=True, expectedTargetMatched=True,
                           url=url, documentId='doc', modifiers=dict(shift=False, control=False, alt=False, meta=False))
                      for key in ('Enter', 'Escape')]
            core.save(evidence / 'dialog-focus.json', {'keyboard_trap': receipt})
            core.save(evidence / 'input-events.json', dict(truncated=False, events=events))
            core.save(evidence / 'transition.json', exit_edge)
            paths = [path.relative_to(work).as_posix() for path in evidence.iterdir()]
            proof_hashes = {path: core.file_hash(work / path) for path in paths}
            transitions = [(opening, work / 'opening', {'state': [{'selector': '#panel'}]}),
                           (exit_edge, evidence, {'state': []})]
            row = dict(criterion='2.1.2', checkpoint='2.1.2-02', target='#panel', state='opened')
            check = dict(checkpoint=CHECKPOINT, target='#panel', outcome='passed', observed='Escape',
                         evidence='escape/dialog-focus.json', environment='desktop', criterion='2.1.2')

            def verdicts(proof):
                return scoring.score_environment(row, [check], [opening, exit_edge],
                                                 transitions, work, work, proof_hashes=proof)['verdicts']

            self.assertEqual([verdict['outcome'] for verdict in verdicts(proof_hashes)], ['passed'])
            self.assertEqual(verdicts({}), [])
            for name in paths:
                with self.subTest(file=name):
                    original = (work / name).read_bytes()
                    (work / name).write_bytes(original + b' ')
                    self.assertEqual(verdicts(proof_hashes), [])
                    (work / name).write_bytes(original)
                    self.assertEqual(verdicts({path: digest for path, digest in proof_hashes.items() if path != name}), [])

            events[0]['isTrusted'] = False
            log = evidence / 'input-events.json'
            core.save(log, dict(truncated=False, events=events))
            proof_hashes[log.relative_to(work).as_posix()] = core.file_hash(log)
            self.assertEqual(verdicts(proof_hashes), [])

            graph = {'edges': [opening, exit_edge]}
            observations = scoring.trap_transition_graph(graph, [check], work, proof_hashes)
            self.assertEqual(observations['edges'], graph['edges'])
            (evidence / 'transition.json').write_text('{')
            observations = scoring.trap_transition_graph(graph, [check], work, proof_hashes)
            self.assertEqual(observations['edges'], [opening])
            self.assertEqual(scoring.trap_transition_graph(graph, [], work, proof_hashes)['edges'], graph['edges'])
