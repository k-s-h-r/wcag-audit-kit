"""Exercise timeout callback semantics and observation bounds in a real browser."""
import argparse,asyncio,json,shutil,sys,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
script=(ROOT/'skills/wcag-audit-kit/scripts/page_explorer.js').read_text()
class OwnedPage(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path=='/delayed':
   time.sleep(.05);body=b'{"ready":true}';self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
  body=b'<!doctype html><title>Owned timer contract</title><p>Owned timer test</p>'
  self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
http=ThreadingHTTPServer(('127.0.0.1',0),OwnedPage);threading.Thread(target=http.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{http.server_port}/timer'
async def main():
 from playwright.async_api import async_playwright
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  try:
   context=await browser.new_context();await context.add_init_script(script);page=await context.new_page();await page.goto(url)
   await page.wait_for_timeout(250)
   network=await page.evaluate('''async()=>{fetch('/delayed').then(r=>r.json()).then(()=>{const p=document.createElement('p');p.id='network-result';p.textContent='Ready';document.body.append(p)});const wait=await __wcagWaitForUpdates();return {wait,rendered:!!document.querySelector('#network-result')}}''')
   (out/'network-observed.json').write_text(json.dumps(network,indent=2)+'\n')
   assert network['rendered'] and network['wait']['elapsed_ms']>=150,network
   normal=await page.evaluate('''async()=>{window.result={};setTimeout(function(a,b){result.args=[a,b];result.receiver=this===window},20,'one',2);
    const cancel=setTimeout(()=>result.cancelled=true,700);clearTimeout(cancel);
    const other=setTimeout(()=>result.wrong=true,800);clearInterval(other);
    const wait=await __wcagWaitForUpdates();return {result,wait}}''')
   assert normal['result']=={'args':['one',2],'receiver':True} and normal['wait']['status']=='quiet',normal
   cyclic=await page.evaluate('''async()=>{window.stopped=false;function again(){if(!stopped)window.lastTimer=setTimeout(again,10)}again();
     const wait=await __wcagWaitForUpdates();stopped=true;clearTimeout(lastTimer);return wait}''')
   assert cyclic['status'] in {'bounded','timeout'} and cyclic['pending_timers']>0 and cyclic['elapsed_ms']>=1400,cyclic
   await context.close();context=await browser.new_context();await context.add_init_script(script);page=await context.new_page();await page.goto(url)
   untracked=await page.evaluate('''async()=>{setTimeout('window.stringTimerRan=true',10);const wait=await __wcagWaitForUpdates();return {wait,ran:window.stringTimerRan}}''')
   assert untracked['ran'] and untracked['wait']['status']=='bounded' and untracked['wait']['untracked_callbacks']==1,untracked
   (out/'observed.json').write_text(json.dumps({'scope':'native timeout semantics and bounds, not full asynchronous readiness','normal':normal,'short_network_response':network,'recursive_timer':cyclic,'string_timer':untracked},indent=2)+'\n')
   await context.close();print('Callback arguments, receiver, cancellation and bounded observations confirmed.')
  finally:await browser.close()
try:asyncio.run(main())
finally:http.shutdown();http.server_close()
