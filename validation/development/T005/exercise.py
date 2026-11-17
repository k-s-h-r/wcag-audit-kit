"""Execute an owned login/edit/logout route; this is not a WCAG verdict."""
import argparse,asyncio,hashlib,importlib.util,json,shutil,socket,sys,threading
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('owned_site',ROOT/'tests/fixtures/audit_site_server.py');site=importlib.util.module_from_spec(spec);spec.loader.exec_module(site)
requests=[]
class Handler(site.Handler):
 def log_message(self,*args):pass
 def send(self,status,body,*args,**kw):
  requests.append({'method':self.command,'path':self.path,'status':status});return super().send(status,body,*args,**kw)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);port=server.server_port;base=f'http://127.0.0.1:{port}';thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
assert urlopen(base+'/login',timeout=3).status==200
observed=[]
async def exercise():
 from playwright.async_api import async_playwright
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  context=await browser.new_context(viewport={'width':1280,'height':900});page=await context.new_page()
  async def record(step,selector):
   observed.append({'step':step,'url':page.url,'text':await page.locator(selector).inner_text(),'focus':await page.evaluate('document.activeElement.id')})
  try:
   await page.goto(base+'/profile');assert await page.locator('#signed-out').is_visible();await record('signed-out','#main')
   await page.goto(base+'/login');await page.locator('#login-email').fill('demo@example.test');await page.locator('#password').fill('Test-password-42!');await page.locator('#sign-in').click()
   await page.get_by_text('Signed in. Continue to profile.',exact=True).wait_for();await record('signed-in','#login-status')
   await page.goto(base+'/profile');await page.locator('#name').fill('T005 Example');await page.locator('#email').fill('t005@example.test');await page.locator('#review').click()
   assert await page.locator('#review-name').inner_text()=='T005 Example';await record('review','#review-panel')
   await page.locator('#back').click();assert await page.locator('#name').input_value()=='T005 Example';await record('back-to-edit','#editor')
   await page.locator('#review').click();await page.locator('#confirm').click();await page.locator('#completion').wait_for(state='visible')
   assert await page.locator('#saved-name').inner_text()=='T005 Example';assert await page.locator('#saved-email').inner_text()=='t005@example.test';await record('saved','#completion')
   await page.screenshot(path=str(out/'saved.png'))
   await page.locator('#sign-out').click();await page.locator('#signed-out').wait_for();await record('signed-out-again','#main')
   assert await page.locator('#profile-form').count()==0;await page.screenshot(path=str(out/'signed-out.png'))
  finally:await context.close();await browser.close()
try:asyncio.run(exercise())
finally:
 server.shutdown();server.server_close();thread.join(timeout=5);site.SESSIONS.clear()
with socket.socket() as sock:closed=sock.connect_ex(('127.0.0.1',port))!=0
assert closed and (out/'saved.png').is_file() and (out/'signed-out.png').is_file()
value={'scope':'owned functional route, not WCAG conformance or speech','base_url':base,'requests':requests,'observations':observed,'server_closed':closed,'session_count_after_cleanup':len(site.SESSIONS),'evidence_readable_after_cleanup':True,
 'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'tests/fixtures/audit_site_server.py',*sorted((ROOT/'tests/fixtures/audit-site').iterdir())] if p.is_file()}}
(out/'observed.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'steps':len(observed),'requests':len(requests),'server_closed':closed}))
