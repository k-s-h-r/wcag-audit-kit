"""Regression checks for keyboard evidence in the page reports."""
from pathlib import Path
from types import SimpleNamespace
import unittest

from openpyxl import load_workbook

import test_ledger as fixture
import audit
import page_workflow
from page_explorer import TAB_UNREACHABLE, is_telemetry


def action(kind, selector, **details):
    return {'type': kind, 'selector': selector, **details}


class KeyboardReportScopeTest(unittest.TestCase):
    def setUp(self):
        fixture.LedgerTest.setUp(self)
        self.addCleanup(fixture.LedgerTest.tearDown, self)
        self.proof = []

    def save_evidence(self, path, content):
        audit.save(self.run / path, content)
        self.proof.append(audit.evidence_item(self.run, path))

    def edge(self, name, route, **details):
        directory = f'evidence/{name}'
        edge = {'environment': 'desktop', 'evidence_dir': directory, 'route': route, **details}
        self.save_evidence(f'{directory}/transition.json', edge)
        return edge

    def save_graph(self, edges):
        # This is the existing saved graph format, with no new metadata required.
        graph_path = self.run / 'exploration.json'
        audit.save(graph_path, {
            'schema_version': '1', 'nodes': [], 'edges': edges, 'queue': [],
            'remaining': [], 'running': False, 'proof': self.proof,
        })
        return graph_path

    def test_pointer_and_mixed_routes_are_not_reported_as_keyboard_results(self):
        key = action('key', '#keyboard-only', key='Enter')
        click = action('click', '#pointer-only')
        edges = [self.edge('pointer', [click]), self.edge('mixed-click', [click, key])]
        for prefix in ('hover', 'fill', 'scroll'):
            edges.append(self.edge(f'mixed-{prefix}', [action(prefix, '#setup'), key], error='mixed route failure'))
        edges.append(self.edge('keyboard', [action('key', '#opener', key='Space'), key], error='key-only route failure'))
        graph_path = self.save_graph(edges)
        original = graph_path.read_bytes()

        files = audit.write_page_reports(self.run, self.config['url'])
        checks = audit.load(files['json'])['machine_checks']
        self.assertEqual([(row['target'], row['outcome']) for row in checks], [('#keyboard-only', 'cant_tell')])
        self.assertEqual(checks[0]['evidence'], 'evidence/keyboard/transition.json')
        self.assertEqual(graph_path.read_bytes(), original)

        html = Path(files['html']).read_text()
        self.assertIn('key-only route failure', html)
        self.assertNotIn('mixed route failure', html)
        self.assertNotIn('#pointer-only', html)
        workbook = load_workbook(files['excel'], read_only=True)
        try:
            rows = list(workbook['機械検査'].iter_rows(min_row=2, values_only=True))
            self.assertEqual(len(rows), 1)
            self.assertIn('#keyboard-only', rows[0])
        finally:
            workbook.close()

    def test_key_dispatch_current_focus_and_explicit_checks_keep_separate_evidence(self):
        key = action('key', '#opener', key='Enter')
        press = action('press', 'body', key='Escape')
        explicit = self.edge('explicit', [], keyboard_check='close-menu')
        self.save_evidence('evidence/explicit/keyboard-check.json', {
            'id': 'close-menu', 'name': 'Close menu', 'criterion': '2.1.2', 'outcome': 'passed',
            'steps': [{'key': 'Escape'}],
        })
        self.save_graph([
            self.edge('key', [key]), self.edge('press', [key, press]),
            self.edge('blocked', [key], blocked_requests=[{'method': 'GET', 'url': 'https://example.com'}]),
            explicit,
        ])

        checks = page_workflow.machine_checks(self.run)
        self.assertEqual([(row['criterion'], row['checkpoint'], row['outcome']) for row in checks], [
            ('2.1.1', '実入力 / Enter', 'passed'),
            ('2.1.1', '実入力 / Escape', 'passed'),
            ('2.1.1', '実入力 / Enter', 'cant_tell'),
            ('2.1.2', 'キーボード経路 / close-menu', 'passed'),
        ])
        self.assertEqual(checks[0]['target'], '#opener')
        self.assertEqual(checks[1]['target'], '現在のフォーカス')
        self.assertEqual(checks[3]['evidence'], 'evidence/explicit/keyboard-check.json')

    def test_telemetry_requires_a_known_endpoint_and_non_navigation_post(self):
        page = 'https://www.example.com/contact'
        cases = [
            ('https://www.google-analytics.com/g/collect?v=2', 'POST', 'ping', False, True),
            ('https://www.google.com/g/collect', 'POST', 'fetch', False, True),
            ('https://www.example.com/cdn-cgi/rum', 'POST', 'xhr', False, True),
            ('https://www.example.com/cdn-cgi/rum', 'POST', 'document', True, False),
            ('https://other.example.com/cdn-cgi/rum', 'POST', 'ping', False, False),
            ('https://www.google-analytics.com.evil.test/g/collect', 'POST', 'ping', False, False),
            ('https://www.google.com/g/collect', 'GET', 'fetch', False, False),
            ('https://www.example.com/submit', 'POST', 'fetch', False, False),
        ]
        for url, method, resource, navigation, expected in cases:
            with self.subTest(url=url, method=method, resource=resource):
                request = SimpleNamespace(url=url, method=method, resource_type=resource,
                                          is_navigation_request=lambda: navigation)
                self.assertEqual(is_telemetry(request, page), expected)

    def test_recorded_effect_requires_the_trusted_key_on_the_target(self):
        key = action('key', '#opener', key='Enter')
        routes = []
        for name, trusted, matched in [('trusted', True, True), ('synthetic', False, True),
                                       ('wrong-target', True, False)]:
            routes.append(self.edge(name, [key], blocked_requests=[{'method': 'POST', 'telemetry': True}],
                                    key_effect={'before': {'open': False}, 'after': {'open': True}, 'event_index': 0}))
            entry = {'type': 'keydown', 'isTrusted': trusted, 'is_main_frame': True, 'key': 'Enter',
                     'expectedTargetMatched': matched,
                     'modifiers': {'shift': False, 'control': False, 'alt': False, 'meta': False}}
            self.save_evidence(f'evidence/{name}/input-events.json', {'events': [entry], 'truncated': False})
        self.save_graph(routes)
        self.assertEqual([row['outcome'] for row in page_workflow.machine_checks(self.run)],
                         ['passed', 'cant_tell', 'cant_tell'])

    def test_unreachable_is_attributed_to_the_attempted_step(self):
        first = action('key', '#opener', key='Enter')
        last = action('key', '#nested', key='Space')
        route = [first, last]
        quiet = [{'status': 'quiet'}]
        graph = self.save_graph([
            self.edge('last', route, error=TAB_UNREACHABLE, keyboard_unreachable_step=2),
            self.edge('prefix', route, error=TAB_UNREACHABLE, keyboard_unreachable_step=1),
            self.edge('legacy-last', route, error=TAB_UNREACHABLE, settling=quiet * 2),
            self.edge('legacy-prefix', route, error=TAB_UNREACHABLE, settling=quiet),
            self.edge('legacy-unverified', route, error=TAB_UNREACHABLE),
            self.edge('blocked-last', route, error=TAB_UNREACHABLE, keyboard_unreachable_step=2,
                      native_events=[{'type': 'dialog'}]),
        ])
        original = graph.read_bytes()
        checks = page_workflow.machine_checks(self.run)
        self.assertEqual([row['outcome'] for row in checks],
                         ['failed', 'cant_tell', 'failed', 'cant_tell', 'cant_tell', 'cant_tell'])
        self.assertIn('1手順目', checks[1]['observed'])
        self.assertIn('1手順目', checks[3]['observed'])
        self.assertEqual(graph.read_bytes(), original)
