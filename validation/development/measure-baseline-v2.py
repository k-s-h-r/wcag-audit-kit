"""Run an immutable T001 machine baseline twice; grading stays outside collection."""
import argparse,hashlib,importlib.util,json,os
from pathlib import Path
import subprocess,sys,time,zipfile
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--task',required=True);p.add_argument('--criterion',required=True);p.add_argument('--records',type=Path,required=True);p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args()
root=a.repo.resolve();records=(root/a.records).resolve();art=(root/a.artifacts).resolve()
# Reject both destinations before imports, collection or any directory creation.
if records.exists() or art.exists():p.error('記録先とrun出力先は両方とも未使用のディレクトリーを指定する。保存済みの記録を上書きしない。')
if not records.is_relative_to(root) or not art.is_relative_to(root) or records.is_relative_to(art) or art.is_relative_to(records):p.error('出力先はrepo内の互いに独立したディレクトリーにする。')
if (a.task,a.criterion) not in {('T002','2.4.2'),('T003','1.1.1')}:p.error('固定したタスクと基準の組を指定する。')
sys.path.insert(0,str(root))
from benchmarks import core,runner
plan=root/'validation/development/T001';ctx=core.load(plan/'context.json')
for name,h in core.load(plan/'checksums.json').items():assert core.file_hash(plan/name)==h,name
assert runner.implementation_digest()==ctx['implementation_digest'];assert core.corpus()['digest']==ctx['corpus_digest'];assert runner.environment()==ctx['environment']
records.mkdir(parents=True,exist_ok=False)
art.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('private_analysis',plan/'summarize.py');analysis=importlib.util.module_from_spec(spec);spec.loader.exec_module(analysis)
receipts=[]
for number in [1,2]:
 name=f'run-{number:03}';run=art/name;cmd=[sys.executable,'benchmarks/run.py','collect','--mode','machine','--criterion',a.criterion,'--out',str(run.relative_to(root))]
 start=time.monotonic();result=subprocess.run(cmd,cwd=root,capture_output=True,text=True);elapsed=time.monotonic()-start
 (records/(name+'.stdout.txt')).write_text(result.stdout);(records/(name+'.stderr.txt')).write_text(result.stderr)
 assert result.returncode==0,result.stderr
 info=json.loads(result.stdout);report=core.load(root/info['files']['json']);summary=analysis.summarize(report,a.criterion)
 core.save(records/(name+'-summary.json'),summary)
 strict=subprocess.run([sys.executable,'benchmarks/run.py','score','--run',str(run.relative_to(root)),'--strict'],cwd=root,capture_output=True,text=True)
 (records/(name+'-strict.stdout.txt')).write_text(strict.stdout);(records/(name+'-strict.stderr.txt')).write_text(strict.stderr)
 core.verify(run);meta=core.load(run/'run.json')
 assert meta['implementation_digest']==ctx['implementation_digest'];assert meta['corpus_digest']==ctx['corpus_digest'];assert meta['configuration']==ctx['configuration'];assert meta['environment']==ctx['environment']
 record={'command':cmd,'exit_code':result.returncode,'elapsed_seconds':elapsed,'strict_exit_code':strict.returncode,'run':str(run.relative_to(root)),
 'run_id':meta['run_id'],'git_head':meta['git_head'],'implementation_digest':meta['implementation_digest'],'corpus_digest':meta['corpus_digest'],'environment':meta['environment'],
 'plan_checksums_sha256':core.file_hash(plan/'checksums.json'),'mode':'machine','ai_inference':False,'tokens':'not applicable; no AI inference','selected_summary':{k:v for k,v in summary.items() if k not in {'rows','pending_evidence_contracts','unexpected_findings'}}}
 receipts.append(record);core.save(records/(name+'-receipt.json'),record)
 with zipfile.ZipFile(records/(name+'.zip'),'x',zipfile.ZIP_DEFLATED) as z:
  for source in sorted(run.rglob('*')):
   if source.is_file() and source.name!='.audit.lock':z.write(source,str(source.relative_to(run)))
 with zipfile.ZipFile(records/(name+'.zip')) as z:assert z.testzip() is None
core.save(records/'runs.json',receipts)
first=core.load(records/'run-001-summary.json');second=core.load(records/'run-002-summary.json')
assert [{k:r[k] for k in ['page','state','target','checkpoint','expected','actual','grade']} for r in first['rows']]==[{k:r[k] for k in ['page','state','target','checkpoint','expected','actual','grade']} for r in second['rows']]
print(json.dumps({'task':a.task,'reproducible_selected_rows':True,'runs':[r['selected_summary'] for r in receipts],'elapsed_seconds':[r['elapsed_seconds'] for r in receipts]},ensure_ascii=False))
