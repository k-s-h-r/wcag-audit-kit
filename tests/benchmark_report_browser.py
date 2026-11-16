"""Check the benchmark report's browser view and workbook against its JSON."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import threading
import asyncio
from collections import Counter
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from benchmarks import core


def main(report,out):
    report=Path(report).resolve();out=Path(out);out.mkdir(parents=True,exist_ok=False)
    value=core.load(report/'result.json')
    from openpyxl import load_workbook
    book=load_workbook(report/'result.xlsx',read_only=True,data_only=True)
    try:
        assert book.sheetnames==['採点結果','概要','基準とモードの実測範囲','追加の誤検出']
        assert book['採点結果'].max_row==len(value['rows'])+1
        assert book['基準とモードの実測範囲'].max_row==87
        grades=Counter(row[9] for row in list(book['採点結果'].values)[1:])
        from benchmarks.reporting import LABEL
        assert dict(grades)=={LABEL[k]:v for k,v in value['counts'].items()}
    finally:book.close()
    # A private reviewer surface, separate from the answer-free worker server.
    class ReviewFiles(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
        def list_directory(self,path):self.send_error(404);return None
        def do_GET(self):
            if not self.path.startswith(('/reports/','/audit-runs/','/attachments/')):self.send_error(404);return
            return super().do_GET()
    http=ThreadingHTTPServer(('127.0.0.1',0),partial(ReviewFiles,directory=str(report.parents[1])))
    threading.Thread(target=http.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{http.server_port}/reports/{report.name}/result.html'
    checks=[]
    async def check():
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
            try:
                for width in [1280,320]:
                    page=await browser.new_page(viewport={'width':width,'height':900})
                    await page.goto(url)
                    assert await page.title()=='基準別の検出試験'
                    assert await page.locator('table').nth(0).locator('tbody tr').count()==len(value['rows'])
                    assert await page.locator('table').nth(1).locator('tbody tr').count()==86
                    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    region=page.get_by_role('region',name='観点ごとの採点',exact=True)
                    overflow=await region.evaluate('(e)=>e.scrollWidth>e.clientWidth')
                    await region.focus()
                    for _ in range(6):await page.keyboard.press('ArrowRight')
                    await page.wait_for_timeout(250)
                    if overflow:assert await region.evaluate('(e)=>e.scrollLeft>0')
                    await page.add_script_tag(content=(ROOT/'vendor/axe.min.js').read_text())
                    violations=await page.evaluate("async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}})).violations")
                    assert not violations,[v['id'] for v in violations]
                    await region.evaluate('(e)=>e.scrollLeft=0')
                    await page.evaluate('window.scrollTo(0,0)')
                    await page.screenshot(path=str(out/f'report-{width}.png'))
                    if width==1280:
                        await region.evaluate('(e)=>{e.scrollLeft=900;e.scrollIntoView()}')
                        await page.screenshot(path=str(out/'report-judgments-1280.png'))
                    for href in await page.locator('a').evaluate_all('(all)=>all.map(a=>a.getAttribute("href"))'):
                        assert (report/href).resolve().is_file(),href
                    checks.append({'width':width,'document_overflow':False,'table_keyboard_scroll':'checked' if overflow else 'not_needed','axe_wcag_violations':0})
                    await page.close()
            finally:await browser.close()
    try:asyncio.run(check())
    finally:http.shutdown();http.server_close()
    core.save(out/'observed.json',{'scope':'report presentation and workbook readback, not conformance or Microsoft Excel UI',
        'source_report':str(report),'rows':len(value['rows']),'grade_counts':value['counts'],'checks':checks})
    print('HTML, keyboard scrolling, evidence links and workbook values checked.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--report',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args();main(args.report,args.out)
