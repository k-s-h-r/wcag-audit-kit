"""Real-browser regression for availability-only changes (PR #5 review)."""
import argparse
import asyncio
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
import threading

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'skills/wcag-audit-kit/scripts'))
import audit
import page_explorer


def run(out):
    from playwright.async_api import async_playwright
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    out.mkdir(parents=True,exist_ok=False)
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT/'tests/fixtures')))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}/control-availability.html'
    async def inspect():
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
            try:
                page=await browser.new_page();await page.add_init_script(page_explorer.SCRIPT)
                await page.goto(url)
                before=await page.evaluate('()=>__wcagExplore()')
                await page.locator('#enable').click()
                after=await page.evaluate('()=>__wcagExplore()')
                audit.save(out/'before.json',before);audit.save(out/'after.json',after)
                assert '#open' not in {c['selector'] for c in before['controls']}
                assert '#open' in {c['selector'] for c in after['controls']}
                assert next(n for n in before['state'] if n['selector']=='#open')['ariaDisabled']=='true'
                assert next(n for n in after['state'] if n['selector']=='#open')['ariaDisabled'] is None
                assert page_explorer.fingerprint(before)!=page_explorer.fingerprint(after),'enabled control merged with prior state'
            finally:await browser.close()
    try:
        asyncio.run(inspect())
        config=audit.init_config(url);config.update(environments=config['environments'][:1],keyboard_steps=3)
        path=out/'config.json';audit.save(path,config);target=out/'run'
        assert audit.main(['page-audit','--url',url,'--out',str(target),'--config',str(path),
            '--max-images','30','--max-states','12','--max-steps','100','--max-depth','2'])==0
        graph=page_explorer.status(target)
        nodes=[n for n in graph['nodes'] if any(s['selector']=='#details' for s in audit.load(target/n['evidence_dir']/'state.json')['state'])]
        assert nodes,'content behind the enabled control was not explored'
        assert all((target/n['evidence_dir']/'axe.json').is_file() for n in nodes)
        audit.save(out/'summary.json',{'states':len(graph['nodes']),'paths':len(graph['edges']),
            'enabled_control_explored':True,'downstream_content_captured':True,'downstream_machine_checks':True,
            'audit_complete':audit.outcomes(target)['audit_complete']})
        print((out/'summary.json').read_text())
    finally:server.shutdown();server.server_close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);run(parser.parse_args().out)
