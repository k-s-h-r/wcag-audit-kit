"""Measure configured/discover URL selection on an owned, finite site."""
import argparse,asyncio,hashlib,json,sys,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'skills/wcag-audit-kit/scripts'))
import audit,page_catalog
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
requests=[]
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  path=urlsplit(self.path).path;requests.append(self.path)
  if path=='/':body='''<a href="/a">A</a><a href="./a">A again</a><a href="/query?view=one">One</a><a href="/query?view=two">Two</a><a href="/app#one">State one</a><a href="/app#two">State two</a><a href="/missing">Missing</a><a href="/dynamic">Dynamic</a><a href="/excluded/path">Excluded</a><a href="http://127.0.0.1:9/foreign">Foreign origin</a>'''
  elif path=='/dynamic':body='''<button onclick="this.insertAdjacentHTML('afterend','<a href=/hidden>More</a>')">Show more</button>'''
  else:body='<p>Owned page</p>'
  status=404 if path=='/missing' else 200
  data=('<!doctype html><html lang=en><head><title>URL fixture</title></head><body>'+body+'</body></html>').encode()
  self.send_response(status);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);base=f'http://127.0.0.1:{server.server_port}';thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
# Expectations are frozen before the selector is called. They are analysis inputs,
# never sent as hints to discover.
expected=['/','/unlinked','/a','/query?view=one','/query?view=two','/app#one','/app#two','/missing','/dynamic']
plan={'base':base,'expected_discover_urls':[base+p for p in expected],'expected_not_discovered':[base+'/hidden'],'scope_excludes':['/excluded/**'],'max_pages':[2,20],
 'configured_input':['/a','./a','/query?view=one','/query?view=two','/app#one','/app#two','/missing'],'expected_configured_requests':0,'expected_http_failure':base+'/missing','expected_full_unvisited':[]}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
results=[]
async def exercise():
 for name,mode,limit in [('configured','configured',20),('discover-full','discover',20),('discover-limited','discover',2)]:
  cfg=audit.init_config(base);cfg['scope'].update(mode=mode,max_pages=limit,exclude=['/excluded/**'],known_pages=['/unlinked'])
  if mode=='configured':cfg['scope']['pages']=plan['configured_input']
  audit.validate_config(cfg);before=len(requests);start=time.monotonic();value=await page_catalog.select_pages(cfg);elapsed=time.monotonic()-start
  audit.save(out/(name+'-config.json'),cfg);audit.save(out/(name+'.json'),value)
  urls=[r['url'] for r in value['pages']]
  if mode=='configured':
   assert urls==[base+p for p in ['/a','/query?view=one','/query?view=two','/app#one','/app#two','/missing']]
   assert len(requests)==before and not value['errors'] and all(not r['visited'] for r in value['pages'])
  else:
   assert set(urls)==set(plan['expected_discover_urls']),(name,urls)
   assert not any(u in urls for u in plan['expected_not_discovered']);assert not value['inventory_complete']
   if limit==20:
    assert len(value['errors'])==1 and value['errors'][0]['url']==base+'/missing';assert not value['unvisited']
   else:
    assert sum(r['visited'] for r in value['pages'])==2;assert len(value['unvisited'])==7;assert not value['errors']
  results.append({'scenario':name,'pages':len(urls),'visited':sum(r['visited'] for r in value['pages']),'unvisited':len(value['unvisited']),'errors':len(value['errors']),'http_requests':requests[before:],'elapsed_seconds':elapsed})
try:asyncio.run(exercise())
finally:server.shutdown();server.server_close();thread.join(timeout=5)
summary={'scope':'URL candidates only; not WCAG inspection or site completeness','results':results,'full_expected_urls':len(expected),'dynamic_link_unfound_as_expected':True,'exclusion_reasons_in_production_output':False,
 'implementation_sha256':{name:hashlib.sha256((ROOT/'skills/wcag-audit-kit/scripts'/name).read_bytes()).hexdigest() for name in ['page_catalog.py','browser_capture.py']},'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
audit.save(out/'observed.json',summary);print(json.dumps(summary,ensure_ascii=False))
