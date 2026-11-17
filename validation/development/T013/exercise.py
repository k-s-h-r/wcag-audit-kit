"""Build a selection ledger from actual candidate discovery and a dynamic route."""
import argparse,asyncio,hashlib,json,shutil,sys,threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'skills/wcag-audit-kit/scripts'));import audit,page_catalog
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);requests=[]
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  path=urlsplit(self.path).path;requests.append(self.path)
  if path=='/':body='<a href="/a">A</a><a href="./a">A again</a><a href="/query?view=one">One</a><a href="/query?view=two">Two</a><a href="/app#one">State one</a><a href="/app#two">State two</a><a href="/missing">Missing</a><a href="/dynamic">Dynamic</a><a href="/excluded/path">Excluded</a><a href="http://127.0.0.1:9/foreign">Foreign origin</a>'
  elif path=='/dynamic':body='<button id="show" onclick="this.insertAdjacentHTML(\'afterend\',\'<a href=/hidden>More</a>\')">Show more</button>'
  elif path=='/hidden':body='<p id="completion">Dynamic route complete</p>'
  else:body='<p>Owned page</p>'
  data=('<!doctype html><html lang=en><head><meta charset=utf-8><title>Selection fixture</title></head><body><header>Owned fixture</header><main><h1>Selection fixture</h1>'+body+'</main></body></html>').encode()
  self.send_response(404 if path=='/missing' else 200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);base=f'http://127.0.0.1:{server.server_port}';threading.Thread(target=server.serve_forever,daemon=True).start()
# Fixture-specific denominator is private analysis, never discovery hints.
expected=['/','/unlinked','/a-extra','/a','/query?view=one','/query?view=two','/app#one','/app#two','/missing','/dynamic'];excluded=['/excluded/path','http://127.0.0.1:9/foreign'];states=[]
audit.save(out/'scope.json',{'url':base,'wcag':'2.2','level':'AA','authentication':'anonymous; no authenticated routes in this owned fixture','environment':{'browser':'Chromium','viewport':{'width':1280,'height':900}},'policy':'all known in-scope URLs, no sample','expected_candidate_paths':expected,'excluded':excluded,'dynamic_procedure':'/dynamic initial -> reveal link -> /hidden completion -> browser back; select both endpoints and revealed state','conformance_claim':False})
config=audit.init_config(base);config['scope'].update(mode='discover',max_pages=20,known_pages=['/unlinked','/a-extra'],exclude=[{'path':'/excluded/**','reason':'Outside agreed fixture scope'}]);config['environments']=config['environments'][:1];audit.save(out/'discovery-config.json',config)
async def exercise():
 candidates=await page_catalog.select_pages(config);audit.save(out/'candidates.json',candidates);assert {r['url'] for r in candidates['pages']}=={base+p for p in expected};assert base+'/hidden' not in {r['url'] for r in candidates['pages']}
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1280,'height':900})
  try:
   await page.goto(base+'/dynamic');assert await page.get_by_role('link',name='More').count()==0
   for name,action in [('initial',None),('revealed','show'),('completed','follow'),('returned','back')]:
    if action=='show':await page.get_by_role('button',name='Show more').click()
    if action=='follow':await page.get_by_role('link',name='More',exact=True).click();await page.wait_for_url(base+'/hidden');assert await page.locator('#completion').is_visible()
    if action=='back':await page.go_back();await page.wait_for_url(base+'/dynamic')
    links=await page.get_by_role('link').evaluate_all('(all)=>all.map(a=>({url:a.href,text:a.textContent}))');(out/(name+'.html')).write_text(await page.content());await page.screenshot(path=str(out/(name+'.png')))
    states.append({'id':name,'url':page.url,'links':links,'action':action,'proof':[name+'.html',name+'.png']})
   revealed=[link['url'] for s in states if s['id']=='revealed' for link in s['links']];assert revealed==[base+'/hidden']
  finally:await browser.close()
 ledger=[]
 for row in candidates['pages']:
  ledger.append({'url':row['url'],'selected':True,'origin':'candidate inventory','reason':'finite fixture census; retain query and fragment identities','candidate_visited':row['visited'],'access':'failed HTTP 404' if row['url']==base+'/missing' else 'visited by candidate selector','audit':'not_run','states':['initial'],'type':'dynamic route start' if row['url']==base+'/dynamic' else 'query variant' if '?' in row['url'] else 'fragment variant' if '#' in row['url'] else 'document'})
 ledger.append({'url':base+'/hidden','selected':True,'origin':'observed revealed link at /dynamic','reason':'procedure completion page; initially undiscovered','candidate_visited':False,'access':'reached via actual click','audit':'not_run','states':['initial'],'type':'procedure end'})
 for value in excluded:
  ledger.append({'url':base+value if value.startswith('/') else value,'selected':False,'origin':'root link','reason':'agreed path exclusion' if value.startswith('/') else 'different origin','candidate_visited':False,'access':'not visited','audit':'out_of_scope','states':[],'type':'excluded'})
 for row in ledger:
  if row['url']==base+'/dynamic':row['states']=['initial','revealed','returned']
 audit.save(out/'ledger.json',{'pages':ledger,'common_parts':{'header':'same authored markup; no audit-result reuse is asserted'},'unvisited_distinct_from_undiscovered':True,'hidden_initially_undiscovered_then_reached':True})
 selected=[r['url'] for r in ledger if r['selected']];handoff=audit.init_config(base);handoff['scope'].update(mode='configured',pages=selected);handoff['environments']=handoff['environments'][:1];audit.validate_config(handoff)
 assert len(selected)==11 and len(set(selected))==11
 urls=page_catalog.configured_urls(handoff);assert set(urls)==set(selected)
 assert base+'/dynamic' in selected and base+'/hidden' in selected
 audit.save(out/'handoff-config.json',handoff);audit.save(out/'procedure.json',{'start':base+'/dynamic','end':base+'/hidden','states':states,'actions':[{'type':'click','selector':'#show'},{'type':'click','selector':'a[href="/hidden"]'}],'completion':'#completion visible at /hidden','reset':'browser back; revealed link may need reopening; verify actual state','requires_separate_procedure_from_configured_initial_pages':True})
 audit.save(out/'observed.json',{'candidates':10,'selected_urls':11,'excluded_urls':2,'candidate_http_failures':len(candidates['errors']),'procedure_steps_observed':len(states),'configured_input_valid':True,'site_conformance':None,'requests':requests,'limitation':'owned finite fixture; unknown real-site routes and rights require investigation; no common-part proof reuse'})
try:asyncio.run(exercise())
finally:server.shutdown();server.server_close()
print('Selected 11 URLs, retained 404, excluded two; observed dynamic route and return.')
