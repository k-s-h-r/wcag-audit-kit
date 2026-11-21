from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/wcag-audit-kit/scripts'))
from input_observation import InputObserver, blocked_tab_focus


class InputObservationTest(unittest.IsolatedAsyncioTestCase):
    def source(self):
        frame=object();return {'frame':frame,'page':SimpleNamespace(main_frame=frame)}

    async def test_synthetic_or_wrong_target_is_not_accepted_as_pointer_input(self):
        for trusted,matched in [(False,True),(True,False)]:
            observer=InputObserver();observer.accept(self.source(),{'type':'pointerdown','isTrusted':trusted,'expectedTargetMatched':matched})
            with self.assertRaises(ValueError):await observer.pointer_down_after(0)

    async def test_trusted_input_is_retained_and_truncation_explicit(self):
        observer=InputObserver(limit=1);event={'type':'pointerdown','isTrusted':True,'expectedTargetMatched':True}
        observer.accept(self.source(),event);self.assertTrue((await observer.pointer_down_after(0))['isTrusted'])
        observer.accept(self.source(),event)
        self.assertTrue(observer.export()['truncated']);self.assertEqual(observer.export()['dropped'],1)

    def test_tab_focus_navigation_requires_unambiguous_guard_and_input_evidence(self):
        url = 'http://127.0.0.1/start'
        destination = 'http://127.0.0.1/details'
        target = {'tag': 'input', 'id': 'subject'}
        request = {'url': destination, 'method': 'GET', 'is_main_frame': True,
                   'resource_type': 'document', 'reason': 'navigation_out_of_scope'}
        key = {'type': 'keydown', 'key': 'Tab', 'modifiers': {'shift': False}}
        focus = {'type': 'focus', 'target': target}
        navigate = {'type': 'navigate', 'target': target, 'focusType': 'focus', 'focusDispatchPhase': 2, 'navigationId': 1,
                    'destination': destination, 'sameDocument': False, 'hashChange': False}
        keyup = {'type': 'keyup', 'key': 'Tab',
                 'navigationAtKeyup': {'id': 1, 'dispatchEnded': True, 'canceled': False, 'aborted': False}}
        observer = InputObserver()
        source = self.source()
        for event in (key, focus, navigate, keyup):
            observer.accept(source, dict(event, url=url, documentId='source', isTrusted=True))
        receipt = blocked_tab_focus(observer, 0, [request], url)
        self.assertEqual([receipt[key] for key in ('keydown_event_index', 'focus_event_index',
                                                  'navigation_event_index', 'keyup_event_index')], [0, 1, 2, 3])
        self.assertIsNone(blocked_tab_focus(observer, 0, [request, request], url))
        self.assertIsNone(blocked_tab_focus(observer, 0, [dict(request, is_main_frame=None)], url))
        self.assertIsNone(blocked_tab_focus(observer, 0, [dict(request, url=url)], url))
        self.assertIsNone(blocked_tab_focus(observer, 1, [request], url))
        observer.accept(source, dict(navigate, url=url, documentId='source', isTrusted=True,
                                     target=None, focusDispatchPhase=0))
        self.assertIsNone(blocked_tab_focus(observer, 0, [request], url))
        observer.events.pop()
        for field, value in [('focusDispatchPhase', 0), ('isTrusted', False), ('sameDocument', True),
                             ('documentId', 'other'), ('hashChange', True)]:
            with self.subTest(field=field):
                original = observer.events[2]
                observer.events[2] = dict(original, **{field: value})
                self.assertIsNone(blocked_tab_focus(observer, 0, [request], url))
                observer.events[2] = original
        for field, value in [('id', 2), ('dispatchEnded', False), ('canceled', True), ('aborted', True)]:
            with self.subTest(field=field):
                observer.events[3]['navigationAtKeyup'] = dict(keyup['navigationAtKeyup'], **{field: value})
                self.assertIsNone(blocked_tab_focus(observer, 0, [request], url))
        observer.events[3]['navigationAtKeyup'] = keyup['navigationAtKeyup']
        observer.dropped = 1
        self.assertIsNone(blocked_tab_focus(observer, 0, [request], url))
