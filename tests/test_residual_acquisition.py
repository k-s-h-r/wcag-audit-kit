import copy
import unittest

from benchmarks import core, residual_acquisition as acquisition


URL = 'http://127.0.0.1:8000/2.4.3/p05.html'
TARGETS = ['#level1','#level2','#leaf','#after']


class BrowserRecordTest(unittest.TestCase):
    def test_focus_records_capture_observed_failure_and_normal_routes(self):
        plan = dict(kind='menu-order', watch=TARGETS, setup=['Tab','Tab','Enter','Tab','Enter'])
        required = ['Tab','Enter','Tab','Enter','Tab','Escape']
        contract = dict(checkpoint='2.4.3-01',kind='focus-sequence',page='p05.html',
                        rationale='記録の例',state='third-level',targets=TARGETS,capture_keys=required)
        self.assertTrue(acquisition.supported(contract))
        for is_problem in (False,True):
            with self.subTest(problem=is_problem):
                focus = ['', '#before', '#level1', '#level1', '#level2',
                         '#after' if is_problem else '#level2', '' if is_problem else '#leaf', '#level2']
                watched = {target:dict(visible=True,expanded=None) for target in TARGETS}
                states = [dict(page=URL,document=1,focus_url=URL,focus_document=1,focus=target,
                    region_visible=True,within=False,outer_visible=True,outer_within=False,
                    watched=copy.deepcopy(watched)) for target in focus]
                entries = [dict(action=key,before=before,after=after,input=dict(
                    type='keydown',key=key,url=URL,time=1,trusted=True,shift=False,alt=False,ctrl=False,meta=False))
                    for key,before,after in zip(['Tab',*required],states[:-1],states[1:],strict=True)]
                data = dict(routes=[dict(kind='order',setup=entries[:5],steps=entries[5:])])
                match = acquisition.match_focus(plan,data,contract,URL)
                self.assertEqual([step['key'] for step in match['sequence']],required)
                self.assertEqual(match['sequence'][3]['after'],'#after' if is_problem else '#level2')
                entries[-1]['input']['trusted'] = False
                self.assertIsNone(acquisition.match_focus(plan,data,contract,URL))
                entries[-1]['input']['trusted'] = True
                entries[-1]['after']['watched']['#leaf'] = None
                self.assertIsNone(acquisition.match_focus(plan,data,contract,URL))

    def test_url_records_require_a_real_tab_and_a_bound_document(self):
        url = 'http://127.0.0.1:8000/3.2.1/p03.html'
        plan = dict(target='#subject')
        begin = dict(trusted=True,url=url,start=1)
        data = dict(before_url=url,after_url=url,before=dict(atStart=True,start=1),after=dict(start=1),
                    events=[dict(begin,type='keydown',key='Tab'),dict(begin,type='focusin',id='subject')])
        contract = dict(targets=['#subject'],url_changes=False)
        self.assertEqual(acquisition.match_url(plan,data,contract,url)['after_url'],url)
        data['after_url'] = url.replace('p03.html','details.html')
        self.assertIsNone(acquisition.match_url(plan,data,dict(contract,url_changes=True),url))
        data['after']['start'] = 2
        self.assertEqual(acquisition.match_url(plan,data,dict(contract,url_changes=True),url)['after_url'],data['after_url'])
        data['events'][1]['trusted'] = False
        self.assertIsNone(acquisition.match_url(plan,data,dict(contract,url_changes=True),url))

    def test_inline_geometry_requires_the_text_context_and_a_small_measured_height(self):
        plan = dict(targets=['#subject'])
        contract = dict(targets=['#subject'],expected_height_below=24)
        item = dict(id='#subject',x=130,y=114.7,width=42,height=20,inline_text=True)
        evidence = dict(items=[item],unresolved=False)
        result = acquisition.match_inline_size(plan,evidence,contract)
        self.assertEqual(result['targets'][0]['rect']['height'],20)
        item['inline_text'] = False
        self.assertIsNone(acquisition.match_inline_size(plan,evidence,contract))
        item.update(inline_text=True,height=24)
        self.assertIsNone(acquisition.match_inline_size(plan,evidence,contract))
