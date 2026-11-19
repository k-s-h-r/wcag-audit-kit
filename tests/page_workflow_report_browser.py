"""Compare page HTML/Excel and render at 1280/320px; run from repository root."""
import asyncio,json,shutil,threading,sys
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from openpyxl import load_workbook
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'skills/wcag-audit-kit/scripts'))
import audit,checksheet,page_workflow
root=Path(sys.argv[1]).resolve();run=audit.run_layout.ledger(root/'run')
url=audit.run_meta(run)['config']['scope']['pages'][0]
files=audit.write_page_reports(run,url)
result=page_workflow.page_result(run,url)
_,catalog=audit.run_catalog(run)
model=checksheet.build(result,catalog,manifest=audit.load(run/'capture-manifest.json'))
book=load_workbook(files['excel'])
assert book.active.title=='チェックシート'
for i,row in enumerate(model['rows'],7):
 assert [c.value or '' for c in book['チェックシート'][i]]==[row.get(k,'') for k,_ in checksheet.COLUMNS]
assert book['機械検査'].max_row==len(result['machine_checks'])+1
assert book['自動検出した問題'].max_row==len(page_workflow.grouped_machine_issues(result['machine_checks']))+1
book.close()
async def main():
 class Handler(SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(root/'run')))
 threading.Thread(target=server.serve_forever,daemon=True).start();checks=[]
 try:
  async with async_playwright() as p:
   browser=await p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
   for width in [1280,320]:
    page=await browser.new_page(viewport={'width':width,'height':900})
    await page.goto(f'http://127.0.0.1:{server.server_port}/{Path(files["html"]).relative_to(root/'run').as_posix()}')
    assert await page.get_by_role('region',name='ページ検証の概要').is_visible()
    assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
    await page.screenshot(path=str(root/f'report-{width}.png'))
    disclosure=page.locator('details').filter(has=page.locator('summary').filter(has_text='自動検出した問題')).first
    if await disclosure.count() and await disclosure.get_attribute('open') is None:await disclosure.locator('summary').first.click()
    await page.locator('#checksheet > summary').click()
    await page.locator('#checksheet').evaluate('(e)=>e.scrollIntoView({block:"start"})')
    await page.screenshot(path=str(root/f'checksheet-{width}.png'))
    await page.add_script_tag(path=str(ROOT/'skills/wcag-audit-kit/vendor/axe.min.js'))
    violations=await page.evaluate('async()=>{const r=await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21a","wcag21aa","wcag22aa"]}});return r.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.length}))}')
    assert not violations,violations
    checks.append({'width':width,'document_horizontal_overflow':False,'axe_violations':violations})
    await page.close()
   await browser.close()
 finally:server.shutdown();server.server_close()
 data={'browser':checks,'excel_cells_match':True,'checksheet_rows':len(model['rows']),
       'machine_check_rows':len(result['machine_checks']),'machine_issue_groups':len(page_workflow.grouped_machine_issues(result['machine_checks'])),
       'files':files}
 audit.save(root/'report-checks.json',data);print(json.dumps(data,ensure_ascii=False,indent=2))
asyncio.run(main())
