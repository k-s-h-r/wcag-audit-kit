"""Read existing baseline reports; do not invoke collection or alter verdicts."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from benchmarks import core
p=argparse.ArgumentParser();p.add_argument('--title-root',type=Path,required=True);p.add_argument('--image-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
rows=[]
for task,directory in [('T002',a.title_root),('T003',a.image_root)]:
 for i in [1,2]:
  run=(directory/f'run-{i:03}').resolve();core.verify(run)
  before={str(p.relative_to(run)):core.file_hash(p) for p in run.rglob('*') if p.is_file()}
  info=json.loads((ROOT/'validation/development'/task/f'run-{i:03}.stdout.txt').read_text());report=run/'reports'/Path(info['files']['json']).parent.name
  target=out/f'{task}-{i:03}';result=subprocess.run([sys.executable,str(ROOT/'tests/benchmark_report_browser.py'),'--report',str(report),'--out',str(target)],capture_output=True,text=True)
  (out/f'{task}-{i:03}.stdout.txt').write_text(result.stdout);(out/f'{task}-{i:03}.stderr.txt').write_text(result.stderr);assert result.returncode==0,result.stderr
  value=core.load(report/'result.json');page_reports=[]
  for path in (run/'audit-runs').rglob('page-*-report.json'):
   page=core.load(path);assert not page['audit_complete'];assert not page.get('scope_confirmed');assert page['counts']=={'not_run':55}
   page_reports.append({'path':str(path.relative_to(run)),'counts':page['counts'],'audit_complete':page['audit_complete']})
  after={str(p.relative_to(run)):core.file_hash(p) for p in run.rglob('*') if p.is_file()};assert before==after
  rows.append({'task':task,'run':i,'grade_counts':value['counts'],'pending_acquisition':len(value.get('pending_evidence_contracts',[])),
   'overall_status':value['overall_status'],'report_files':{p.name:core.file_hash(p) for p in report.iterdir() if p.is_file()},'source_files_unchanged':len(before),'page_reports':page_reports})
core.save(out/'observed.json',{'scope':'saved reports only; no target visit or collection','runs':rows,'runtime_or_verdict_changes':False,'comparison':'HTML table rows, labels, links and Excel values match JSON; native page verdicts stay not_run'})
print(json.dumps({'runs':len(rows),'page_reports':sum(len(r['page_reports']) for r in rows),'source_files_unchanged':sum(r['source_files_unchanged'] for r in rows)}))
