"""Read saved page artifacts without regenerating or editing source runs."""
import asyncio,json,shutil,sys,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from openpyxl import load_workbook
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'skills/wcag-audit-kit/scripts'));import audit,checksheet,page_workflow
source=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=False)
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(source)));threading.Thread(target=server.serve_forever,daemon=True).start()
checks=[]
async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  try:
   for run in sorted(source.glob('page-*')):
    if not run.is_dir():continue
    reports=list(run.glob('page-*-report.json'))
    if not reports:continue
    report=reports[0];value=audit.load(report);_,catalog=audit.run_catalog(run)
    model=checksheet.build(value,catalog,manifest=audit.load(run/'capture-manifest.json'))
    excel=next(run.glob('page-*-report*.xlsx'));book=load_workbook(excel,read_only=True,data_only=True)
    try:
     for i,row in enumerate(model['rows'],7):assert [c.value or '' for c in book['チェックシート'][i]]==[row.get(k,'') for k,_ in checksheet.COLUMNS]
     assert book['機械検査'].max_row==len(value['machine_checks'])+1
     assert book['自動検出した問題'].max_row==len(page_workflow.grouped_machine_issues(value['machine_checks']))+1
    finally:book.close()
    for width in [1280,320]:
     page=await browser.new_page(viewport={'width':width,'height':900});await page.goto(f'http://127.0.0.1:{server.server_port}/{run.name}/{report.stem}.html')
     assert await page.get_by_role('region',name='ページ検証の概要').is_visible()
     assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
     await page.screenshot(path=str(out/f'{run.name}-{width}.png'));await page.close()
    checks.append({'page':value['url'],'run':run.name,'checksheet_rows':len(model['rows']),'machine_rows':len(value['machine_checks']),'excel_cells_match':True,'widths':[1280,320],'all_criterion_outcomes':'not_run','audit_complete':value['audit_complete']})
  finally:await browser.close()
try:asyncio.run(main())
finally:server.shutdown();server.server_close()
assert len(checks)==6;audit.save(out/'observed.json',{'pages':checks,'scope':'read-only HTML/JSON/workbook comparison; no criterion conformance claim'});print('Six page reports and workbooks match saved JSON.')
