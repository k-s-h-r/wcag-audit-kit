"""Collect a changed implementation against unchanged T001 rows; keep prior runs."""
import argparse,json,importlib.util,subprocess,sys,time,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--criterion',required=True);p.add_argument('--out',required=True);p.add_argument('--record',required=True);a=p.parse_args()
root=a.repo.resolve();sys.path.insert(0,str(root));from benchmarks import core,runner
plan=root/'validation/development/T001';context=core.load(plan/'context.json')
for name,h in core.load(plan/'checksums.json').items():assert core.file_hash(plan/name)==h
revision=core.load(root/'validation/development/T018/metadata-v2.json')
assert revision['all_expected_verdicts_unchanged'] and core.corpus()['digest']==revision['corpus_digest']
assert runner.implementation_digest()==revision['implementation_digest'];assert runner.environment()==context['environment']
records=root/a.record;records.mkdir(parents=True,exist_ok=False);run=root/a.out
cmd=[sys.executable,'benchmarks/run.py','collect','--mode','machine','--criterion',a.criterion,'--out',a.out]
start=time.monotonic();result=subprocess.run(cmd,cwd=root,text=True,capture_output=True);elapsed=time.monotonic()-start
(records/'stdout.txt').write_text(result.stdout);(records/'stderr.txt').write_text(result.stderr);assert result.returncode==0,result.stderr
value=json.loads(result.stdout);report=core.load(root/value['files']['json']);spec=importlib.util.spec_from_file_location('private_analysis',plan/'summarize.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
summary=m.summarize(report,a.criterion);core.save(records/'summary.json',summary)
strict=subprocess.run([sys.executable,'benchmarks/run.py','score','--run',a.out,'--strict'],cwd=root,capture_output=True,text=True);(records/'strict.stdout.txt').write_text(strict.stdout);(records/'strict.stderr.txt').write_text(strict.stderr)
meta,progress=core.verify(run);assert meta['configuration']==context['configuration']
core.save(records/'receipt.json',{'command':cmd,'exit_code':result.returncode,'strict_exit_code':strict.returncode,'elapsed_seconds':elapsed,'run_id':meta['run_id'],'git_head':meta['git_head'],
'baseline_corpus_digest':context['corpus_digest'],'state_metadata_revision':revision['metadata_changes'],'baseline_implementation_digest':context['implementation_digest'],'implementation_digest':meta['implementation_digest'],'corpus_digest':meta['corpus_digest'],'environment':meta['environment'],'configuration':meta['configuration'],
'plan_checksums_sha256':core.file_hash(plan/'checksums.json'),'mode':'machine','ai_inference':False,'tokens':'not applicable; no AI inference'})
with zipfile.ZipFile(records/'run.zip','x',zipfile.ZIP_DEFLATED) as z:
 for src in sorted(run.rglob('*')):
  if src.is_file() and src.name!='.audit.lock':z.write(src,str(src.relative_to(run)))
with zipfile.ZipFile(records/'run.zip') as z:assert z.testzip() is None
print(json.dumps({'criterion':a.criterion,'elapsed_seconds':elapsed,**{k:v for k,v in summary.items() if k not in {'rows','pending_evidence_contracts','unexpected_findings'}}},ensure_ascii=False))
