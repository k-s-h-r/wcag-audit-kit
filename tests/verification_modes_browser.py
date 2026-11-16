"""Real Chromium checks for mode selection, collection, packets and reports.

This checks execution policy, not AI semantic judgments or actual SR speech.
"""
import argparse
import asyncio
import contextlib
from functools import partial
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import audit
import page_explorer
import page_workflow


def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    class Handler(SimpleHTTPRequestHandler):
        requests=[]
        def log_message(self,*args):pass
        def do_GET(self):
            self.requests.append(self.path)
            if self.path.startswith('/__reports__/'):
                self.directory=str(out)
                self.path=self.path.removeprefix('/__reports__')
            return super().do_GET()
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT/'tests/fixtures')))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}/page-workflow.html'
    with (out/'init.stdout.txt').open('w') as stdout,contextlib.redirect_stdout(stdout):
        assert audit.main(['init','--url',url,'--config',str(out/'init-generated.json'),'--mode','machine'])==0
    cfg=audit.load(out/'init-generated.json')
    assert all(e['zoom']==1 for e in cfg['environments'])
    cfg.update(environments=cfg['environments'][:1],keyboard_steps=3)
    audit.save(out/'config.json',cfg);results=[]
    try:
        for name in ['machine','ai','screen-reader','full']:
            run=out/name
            command=['page-audit','--url',url,'--config',str(out/'config.json'),'--out',str(run),'--mode',name,
                     '--max-states','2','--max-steps','4','--max-depth','1']
            if name in {'ai','full'}:command+=['--max-images','2']
            with (out/(name+'.stdout.txt')).open('w') as stdout,contextlib.redirect_stdout(stdout):
                assert audit.main(command)==0
            value=page_workflow.page_result(run,url);mode=value['verification']
            assert mode['mode']==name and mode['screen_reader_status']==('not_run' if name in {'screen-reader','full'} else 'disabled')
            assert not value['audit_complete'] and set(value['counts'])=={'not_run'}
            images=list(run.rglob('*.png'))
            assert (0<len(images)<=2) if name in {'ai','full'} else not images
            assert not list(run.rglob('screen-reader.json'))
            packet=page_workflow.next_work(run,url,limit=1)
            assert all((p['ai_instruction'] is not None)==(name in {'ai','full'}) for p in packet['next_cases'][0]['verification_checkpoints'])
            assert len(mode['checkpoints'])==131
            audit.save(out/(name+'.packet.json'),packet)
            files={'html':next(run.glob('page-*-report.html')),'json':next(run.glob('page-*-report.json')),'excel':next(run.glob('page-*-report.xlsx'))}
            from openpyxl import load_workbook
            book=load_workbook(files['excel'])
            try:
                assert book['モード別の確認範囲'].max_row==132
                assert book.sheetnames[:2]==['チェックシート','不適合箇所']
            finally:book.close()
            results.append(dict(mode=name,states=len(page_explorer.status(run)['nodes']),machine_checks=len(value['machine_checks']),
                screenshots=len(images),screen_reader=mode['screen_reader_status'],wcag_counts=value['counts'],
                mode_counts=mode['counts'],audit_complete=value['audit_complete'],files={k:str(p.relative_to(out)) for k,p in files.items()}))
        run=out/'machine';meta_before=(run/'run.json').read_bytes();old_proof=page_explorer.status(run)['proof']
        with (out/'resume.stdout.txt').open('w') as stdout,contextlib.redirect_stdout(stdout):
            assert audit.main(['page-audit','--url',url,'--out',str(run),'--resume','--max-states','3','--max-steps','6'])==0
        assert (run/'run.json').read_bytes()==meta_before
        assert audit.run_meta(run)['config']['verification']['mode']=='machine'
        assert all(audit.evidence_item(run,p['path'])==p for p in old_proof)
        with (out/'mode-change.stderr.txt').open('w') as stderr,contextlib.redirect_stderr(stderr):
            assert audit.main(['page-audit','--url',url,'--out',str(run),'--resume','--mode','ai'])==1
        assert (run/'run.json').read_bytes()==meta_before
        audit.save(out/'summary.json',dict(version='0.7.0',modes=results,resume_kept_mode=True,
            old_evidence_unchanged=len(old_proof),mode_change_rejected=True,
            scope='実ブラウザーのモード別収集・作業指示・帳票。AIの内容判断と実SRの発話は今回未実施。',
            server_requests=Handler.requests))
        async def inspect_report():
            from playwright.async_api import async_playwright
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
                try:
                    page=await browser.new_page()
                    for width in [1280,320]:
                        await page.set_viewport_size({'width':width,'height':900})
                        report=next((out/'full').glob('page-*-report.html'))
                        await page.goto(f'http://127.0.0.1:{server.server_port}/__reports__/full/{report.name}')
                        await page.locator('#verification-mode').scroll_into_view_if_needed()
                        assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
                        region=page.get_by_role('region',name='モード別の確認範囲',exact=True)
                        for _ in range(40):
                            await page.keyboard.press('Tab')
                            if await region.evaluate('(e)=>e===document.activeElement'):break
                        assert await region.evaluate('(e)=>e===document.activeElement'),'table not keyboard reachable'
                        if await region.evaluate('(e)=>e.scrollWidth>e.clientWidth'):
                            await page.keyboard.press('ArrowRight')
                            await page.wait_for_timeout(200)
                            assert await region.evaluate('(e)=>e.scrollLeft>0'),'table not keyboard scrollable'
                        await page.add_script_tag(path=str(ROOT/'vendor/axe.min.js'))
                        found=await page.evaluate("async()=>{const r=await axe.run(document);return r.violations.filter(v=>v.tags.some(t=>/^wcag/.test(t)))}")
                        audit.save(out/f'report-axe-{width}.json',found)
                        assert not found,found
                        await region.evaluate('(e)=>e.scrollLeft=0')
                        await page.locator('#verification-mode').scroll_into_view_if_needed()
                        await page.screenshot(path=str(out/f'mode-report-{width}.png'))
                finally:await browser.close()
        asyncio.run(inspect_report())
        for relative in ['scripts/audit.py','scripts/verification_modes.py','scripts/page_workflow.py','scripts/page_explorer.py',
                         'scripts/page_explorer.js','scripts/inspection.py','scripts/workbook.py','scripts/checksheet.py',
                         'references/verification-checkpoints.json','package.json','tests/verification_modes_browser.py']:
            target=out/'implementation'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,target)
        audit.save(out/'checks.json',dict(reports_no_page_overflow=[1280,320],reports_axe_wcag_violations=0,
            summaries={r['mode']:r['screen_reader'] for r in results}))
        print(json.dumps(dict(out=str(out),modes=[dict(mode=r['mode'],screenshots=r['screenshots'],screen_reader=r['screen_reader']) for r in results]),ensure_ascii=False))
    finally:server.shutdown();server.server_close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args();main(args.out)
