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
