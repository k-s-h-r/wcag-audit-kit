"""Synthetic candidate acquisition contracts, never WCAG pass/fail evidence."""
import copy,json
from pathlib import Path
import sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));from benchmarks import core,acquisition
import test_benchmarks as fixture

CONTRACT=dict(checkpoint='1.1.1-02',kind='inventory',state='initial',page='p01.html',targets=['#graphic'],formats=['inline-svg'],rationale='Synthetic visible candidate list.')
VALUE=dict(candidate_collection={'method':acquisition.METHOD,'complete':True},visual_candidates=[{'selector':'#graphic','formats':['inline-svg']}])

class AcquisitionTest(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.run=Path(t.name);self.root=self.run/'audit-run';self.job={'id':'unit'}
  self.progress={'jobs':{'unit':{'p01.html':{'status':'completed','directory':'audit-run'}}}}
  core.save(self.root/'exploration.json',{'nodes':[{'route':[],'evidence_dir':'evidence/initial'}]});self.write(VALUE)
 def write(self,value):core.save(self.root/'evidence/initial/state.json',value)
 def assess(self,contract=None):return acquisition.assess(self.run,self.job,self.progress,contract or CONTRACT)
 def test_candidates_match_without_producing_wcag_verdicts(self):
  result=self.assess();self.assertEqual(result['status'],'matched');self.assertNotIn('outcome',result);self.assertEqual(len(result['evidence']),1)
 def test_missing_extra_or_wrong_formats_are_mismatches(self):
  for candidates in [[],[{'selector':'#other','formats':['inline-svg']}],[{'selector':'#graphic','formats':['canvas']}]]:
   self.write(dict(VALUE,visual_candidates=candidates));self.assertEqual(self.assess()['status'],'mismatch')
 def test_missing_partial_malformed_and_duplicate_evidence_remains_unknown(self):
  for value in [{},dict(VALUE,candidate_collection={'method':acquisition.METHOD,'complete':False}),dict(VALUE,visual_candidates=[{'selector':'#graphic','formats':[[]]}]),dict(VALUE,visual_candidates=VALUE['visual_candidates']*2)]:
   self.write(value);self.assertEqual(self.assess()['status'],'not_evaluated')
 def test_unimplemented_conditions_cannot_be_silently_ignored(self):
  self.assertEqual(self.assess(dict(CONTRACT,decorative=True))['status'],'not_evaluated')
 def test_other_kinds_and_states_are_not_connected(self):
  self.assertIsNone(self.assess(dict(CONTRACT,kind='geometry')))
  self.assertIsNone(self.assess(dict(CONTRACT,state='opened')))

class IntegrationTest(unittest.TestCase):
 def setUp(self):
  self.fixture=fixture.ScoringTest();self.fixture.setUp();self.addCleanup(self.fixture.tearDown)
  self.run,_,self.job,self.progress=self.fixture.make_run(mode='machine',contract=CONTRACT)
  receipt=self.progress['jobs'][self.job['id']]['p01.html'];receipt['status']='completed';self.root=self.run/receipt['directory']
  core.save(self.root/'exploration.json',{'nodes':[{'route':[],'evidence_dir':'evidence/candidates'}],'edges':[]})
  core.save(self.root/'evidence/candidates/state.json',VALUE);core.save(self.root/'evidence/candidates/axe.json',{'violations':[],'passes':[],'incomplete':[]})
  core.save(self.run/'progress.json',self.progress);core.freeze(self.run,[p for p in self.root.rglob('*') if p.is_file()])
 def test_match_does_not_complete_native_verdicts_and_is_reported_separately(self):
  from benchmarks import reporting
  result=core.score(self.run);self.assertEqual(result['acquisition_counts'],{'matched':1});self.assertFalse(result['pending_evidence_contracts'])
  self.assertTrue(all(r['actual']=='not_run' for r in result['rows']));self.assertEqual(result['overall_status'],'incomplete')
  files=reporting.write(self.run,result)
  from openpyxl import load_workbook
  book=load_workbook(files['excel'],read_only=True);self.assertIn('取得期待の照合',book.sheetnames);book.close()
 def test_modified_acquisition_evidence_is_rejected(self):
  core.save(self.root/'evidence/candidates/state.json',{})
  with self.assertRaisesRegex(ValueError,'変更された'):core.score(self.run)
 def test_lost_acquisition_matches_are_regressions(self):
  baseline=core.score(self.run);current=copy.deepcopy(baseline);current['acquisition_results'][0]['status']='not_evaluated'
  self.assertEqual(core.compare(baseline,current)['status'],'regressions')

if __name__=='__main__':unittest.main()
