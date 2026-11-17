"""Owned configured-URL exercise: one page per run, interrupt and resume."""
import argparse,hashlib,json,signal,subprocess,sys,threading,time,zipfile
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));from benchmarks import core,runner
sys.path.insert(0,str(core.RUNTIME/'scripts'));import audit
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
requests=[];gate=threading.Event();release=threading.Event();delay=True
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  global delay
  requests.append(self.path);path=urlsplit(self.path).path
  if path=='/a-extra' and delay:
   delay=False;gate.set();release.wait(15)
  title='' if self.path=='/query?view=two' else '<title>Configured page '+self.path+'</title>'
  img='<img src="/pixel.svg">' if path=='/a-extra' else '<img src="/pixel.svg" alt="Example mark">'
  data=(f'<!doctype html><html lang=en><head>{title}</head><body><main><h1>Owned page</h1>{img}</main></body></html>').encode()
  status=404 if path=='/missing' else 200
  if path=='/pixel.svg':data=b'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><rect width="16" height="16"/></svg>'
  self.send_response(status);self.send_header('Content-Type','image/svg+xml' if path=='/pixel.svg' else 'text/html');self.send_header('Content-Length',str(len(data)));self.end_headers()
  try:self.wfile.write(data)
  except (BrokenPipeError,ConnectionResetError):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);base=f'http://127.0.0.1:{server.server_port}';thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
paths=['/a','/a-extra','/query?view=one','/query?view=two','/app#one','/app#two','/missing'];urls=[base+p for p in paths]
plan={'urls':urls,'mode':'machine','environments':['desktop'],'max_states':1,'max_steps':1,'max_depth':1,'interruption':'SIGINT during second URL navigation; resume its run with identical config; completed first URL never rerun','expected_rules':{'/a-extra':{'image-alt':'failed'},'/query?view=two':{'document-title':'failed'}},'expected_navigation_failure':'/missing','implementation_digest':runner.implementation_digest(),'environment':runner.environment(),'scope':'configured URLs; rule-level observations, not criterion conformance'}
core.save(out/'plan.json',plan)
def hashes(run):return {p.relative_to(run).as_posix():core.file_hash(p) for p in sorted((run/'evidence').rglob('*')) if p.is_file()}
def command(url,cfg,run,resume=False):return [sys.executable,str(core.RUNTIME/'scripts/audit.py'),'page-audit','--url',url,'--config',str(cfg),'--out',str(run),'--max-states','1','--max-steps','1','--max-depth','1']+(['--resume'] if resume else [])
def execute(cmd,name):
 start=time.monotonic();result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=90);(out/(name+'.stdout.txt')).write_text(result.stdout);(out/(name+'.stderr.txt')).write_text(result.stderr)
 return {'command':cmd,'exit_code':result.returncode,'elapsed_seconds':time.monotonic()-start}
results=[];first_hash=None;interrupted_hash={};runs=[]
try:
 for index,url in enumerate(urls):
  assert runner.implementation_digest()==plan['implementation_digest'] and runner.environment()==plan['environment']
  run=out/f'page-{index+1:02d}';runs.append(run);cfg=out/f'config-{index+1:02d}.json';c=audit.init_config(url);c.update(environments=c['environments'][:1],keyboard_steps=2);c['scope'].update(mode='configured',pages=[url]);core.save(cfg,c)
  cmd=command(url,cfg,run)
  if index==1:
   stdout=(out/'interrupted.stdout.txt').open('w');stderr=(out/'interrupted.stderr.txt').open('w');process=subprocess.Popen(cmd,cwd=ROOT,text=True,stdout=stdout,stderr=stderr)
   try:
    assert gate.wait(30),'second page did not begin';process.send_signal(signal.SIGINT);release.set();code=process.wait(timeout=30)
   finally:
    release.set()
    if process.poll() is None:process.kill();process.wait()
    stdout.close();stderr.close()
   assert code!=0
   interrupted_hash=hashes(run);core.save(out/'interrupted-exploration.json',core.load(run/'exploration.json'));core.save(out/'interruption.json',{'command':cmd,'exit_code':code,'first_page_evidence_hashes':first_hash,'interrupted_page_evidence_hashes':interrupted_hash,'requests_at_stop':list(requests)})
   result=execute(command(url,cfg,run,True),'resumed')
   assert hashes(runs[0])==first_hash
   assert all(core.file_hash(run/p)==h for p,h in interrupted_hash.items())
  else:result=execute(cmd,f'page-{index+1:02d}')
  graph=core.load(run/'exploration.json');nodes=graph['nodes'];report=next(run.glob('page-*-report.json'),None)
  if index==0:first_hash=hashes(run)
  checks=[]
  if report:
   report_value=core.load(report);checks=report_value.get('machine_checks',[])
   assert all(row['page_url']==url for row in report_value['cases'])
   assert all(row['outcome']=='not_run' for row in report_value['cases'])
  # Read the raw rule evidence independently of human report formatting.
  rule_results={}
  for node in nodes:
   axe=core.load(run/node['evidence_dir']/'axe.json')
   for group,status in [('violations','failed'),('passes','passed'),('incomplete','cant_tell'),('inapplicable','inapplicable')]:
    for rule in axe.get(group,[]):
     if rule['id'] in {'image-alt','document-title'}:rule_results[rule['id']]=status
  expected=plan['expected_rules'].get(paths[index],{'image-alt':'passed','document-title':'passed'})
  if paths[index]=='/missing':assert result['exit_code']==2 and not nodes
  else:
   assert result['exit_code']==0 and nodes,(url,result,graph)
   assert all(rule_results.get(k)==v for k,v in expected.items()),(url,rule_results)
   assert report and report_value.get('audit_complete') is False
   assert (run/(report.stem+'.html')).is_file() and list(run.glob('page-*-report*.xlsx'))
  results.append(dict(url=url,run=run.name,status='navigation_failed' if not nodes else 'collected',rule_results=rule_results,page_report=report.name if report else None,remaining=graph.get('remaining',[]),**result))
 assert len({audit.page_id(u) for u in urls})==7
 assert sum(r['status']=='collected' for r in results)==6
 assert all(urlsplit(base+r).path in {urlsplit(u).path for u in urls}|{'/pixel.svg'} for r in requests)
 assert requests.count('/a')==1,'completed first page was revisited'
 core.save(out/'observed.json',{'results':results,'counts':{'collected':6,'navigation_failed':1,'unattempted':0},'interrupted_then_resumed':urls[1],'first_page_evidence_preserved':True,'interrupted_evidence_files_preserved':len(interrupted_hash),'separate_page_reports':6,'unintended_crawl':False,'requests':requests,'overall_audit_complete':False,'g2_host_condition_met':False})
finally:release.set();server.shutdown();server.server_close();thread.join(timeout=5)
with zipfile.ZipFile(out/'runs.zip','x',zipfile.ZIP_DEFLATED) as archive:
 for run in runs:
  for src in sorted(run.rglob('*')):
   if src.is_file() and src.name!='.audit.lock':archive.write(src,src.relative_to(out))
print(json.dumps({'pages':len(results),'collected':6,'navigation_failed':1,'resumed':True},ensure_ascii=False))
