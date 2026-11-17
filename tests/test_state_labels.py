"""Synthetic state-contract tests; no browser or conformance claim."""
import copy
from pathlib import Path
import sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'skills/wcag-audit-kit/scripts'))
import state_labels
from benchmarks import core

SPEC={'id':'loaded','actions':[{'type':'click','selector':'#load'}],'assert':[{'selector':'#slot img','count':1,'visible':True}]}
OBS={'id':'loaded','actions':SPEC['actions'],'assertions':[{'selector':'#slot img','count':1,'visible':True}],'matched':True}

class ContractTest(unittest.TestCase):
 def test_legacy_action_only_hints_are_not_state_labels(self):
  self.assertEqual(state_labels.public_specs([{'id':'opened','actions':[{'type':'click','selector':'#open'}]}]),[])
 def test_validation_rejects_ambiguous_or_unsupported_contracts(self):
  for value in [[dict(SPEC,id='initial')],[SPEC,SPEC],[dict(SPEC,actions=[])],[dict(SPEC,**{'assert':[{'selector':'#x','text':'private answer'}]})]]:
   with self.assertRaises(ValueError):state_labels.validate(value)
 def test_missing_or_wrong_observations_cannot_label_a_state(self):
  self.assertEqual(state_labels.verified([SPEC],SPEC['actions'],[OBS]),['loaded'])
  for altered in [dict(OBS,matched=False),dict(OBS,actions=[{'type':'hover','selector':'#load'}]),dict(OBS,assertions=[]),dict(OBS,assertions=[{'selector':'#slot img','count':0,'visible':False}])]:
   self.assertEqual(state_labels.verified([SPEC],SPEC['actions'],[altered]),[])
  self.assertEqual(state_labels.verified([SPEC],[{'type':'click','selector':'#other'}],[OBS]),[])

 def test_ambiguous_plural_visibility_is_not_hidden(self):
  self.assertFalse(state_labels.conditions_match([{'selector':'img','visible':False}],[{'selector':'img','count':2,'visible':None}]))
  self.assertTrue(state_labels.conditions_match([{'selector':'img','count':2}],[{'selector':'img','count':2,'visible':None}]))

class PredictionTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.run=Path(self.tmp.name)
  self.job={'id':'machine--1.1.1--unit','checkpoints':['1.1.1-01'],'states':[SPEC]};self.root=self.run/'audit-run'
  self.progress={'jobs':{self.job['id']:{'p01.html':{'status':'completed','directory':'audit-run'}}}}
  self.node={'route':SPEC['actions'],'evidence_dir':'evidence/one'}
  self.write_node(self.node,'failed');self.save_graph([self.node])
 def write_node(self,node,outcome):
  p=self.root/node['evidence_dir'];core.save(p/'state.json',{'state_labels':[OBS]});core.save(p/'transition.json',{'route':node['route'],'error':None,'blocked_requests':[],'native_events':[]})
  core.save(p/'axe.json',{'violations':[{'id':'image-alt','nodes':[{'target':['#subject'],'html':'<img id="subject">'}]}] if outcome=='failed' else [],'passes':[{'id':'image-alt','nodes':[{'target':['#subject'],'html':'<img id="subject" alt="Chart">'}]}] if outcome=='passed' else [],'incomplete':[]})
 def save_graph(self,nodes):core.save(self.root/'exploration.json',{'nodes':nodes,'edges':[]})
 def predict(self):return core.program_predictions(self.run,self.job,self.progress)
 def test_only_observed_named_state_receives_the_raw_rule(self):
  result=self.predict();row=result[('p01.html','loaded','#subject','1.1.1-01')]
  self.assertEqual(row['outcome'],'failed');self.assertEqual(len(row['evidence']),3)
 def test_old_unlabelled_noninitial_proofs_remain_unverified(self):
  core.save(self.root/'evidence/one/state.json',{'state':[]});self.assertEqual(self.predict(),{})
 def test_wrong_or_blocked_transition_cannot_claim_the_label(self):
  for transition in [{'route':[]},{'route':SPEC['actions'],'blocked_requests':[{'url':'/save'}]}]:
   core.save(self.root/'evidence/one/transition.json',transition);self.assertEqual(self.predict(),{})
 def test_conflicting_raw_observations_are_not_last_writer_wins(self):
  other=dict(self.node,evidence_dir='evidence/two');self.write_node(other,'passed');self.save_graph([self.node,other])
  row=next(iter(self.predict().values()));self.assertEqual(row['outcome'],'cant_tell');self.assertTrue(row['conflicting']);self.assertEqual(len(row['evidence']),6)

if __name__=='__main__':unittest.main()
