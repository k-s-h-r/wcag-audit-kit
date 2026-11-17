"""Verify a metadata-only corpus revision against the frozen baseline bytes."""
import copy,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));from benchmarks import core,runner
baseline=ROOT/'validation/development/T003/run-001.zip'
with zipfile.ZipFile(baseline) as z:
 original=core.load(ROOT/'validation/development/T001/context.json');old=json.loads(z.read('oracle.snapshot.json'));current=core.corpus();normalized=copy.deepcopy(current['suites'])
 changes=[]
 for suite,prior in zip(normalized,old['suites']):
  assert suite['criterion']==prior['criterion']
  if suite['criterion']=='1.1.1':
   changes.append({'criterion':'1.1.1','version_before':prior['version'],'version_after':suite['version'],'states':['c09/after-load','c10/after-load']});suite['version']=prior['version']
   for c in suite['cases']:
    if c['id'] in ['c09','c10']:
     assert c['states'][0]['actions']==[{'selector':'#load','type':'click'}]
     assert c['states'][0]['assert']==[{'selector':'#slot img','count':1,'visible':True}]
     c['states'][0].pop('actions');c['states'][0].pop('assert')
 assert normalized==old['suites'],'A change beyond declared state metadata was found'
 count=0
 for name in z.namelist():
  if name.startswith('worker/public/') and not name.endswith('/'):
   relative=name[len('worker/public/'):];assert core.file_hash(ROOT/'benchmarks/cases'/relative.split('/')[0]/'public'/'/'.join(relative.split('/')[1:]))==__import__('hashlib').sha256(z.read(name)).hexdigest(),name;count+=1
 report={'baseline_corpus_digest':original['corpus_digest'],'corpus_digest':current['digest'],'implementation_digest':runner.implementation_digest(),
 'all_expected_verdicts_unchanged':True,'public_files_unchanged':count,'metadata_changes':changes,'plan_checksums_sha256':core.file_hash(ROOT/'validation/development/T001/checksums.json'),
 'scope':'Public operations and observable state assertions added; HTML/media and every expected verdict stay byte-identical or structurally identical.'}
 print(json.dumps(report,ensure_ascii=False,indent=2))
