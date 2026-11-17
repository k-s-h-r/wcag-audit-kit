"""Read saved report cells and compare identities, verdicts and evidence paths."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

class Tables(HTMLParser):
 def __init__(self,text):
  super().__init__(convert_charrefs=True);self.tables=[];self.table=None;self.row=None;self.cell=None;self.feed(text)
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag=='table':self.table={'attrs':attrs,'rows':[]};self.tables.append(self.table)
  elif tag=='tr' and self.table is not None:self.row=[]
  elif tag in {'td','th'} and self.row is not None:self.cell={'text':'','links':[]}
  elif tag=='br' and self.cell is not None:self.cell['text']+='\n'
  elif tag=='a' and self.cell is not None:self.cell['links'].append(attrs.get('href',''))
 def handle_data(self,data):
  if self.cell is not None:self.cell['text']+=data
 def handle_endtag(self,tag):
  if tag in {'td','th'} and self.cell is not None:self.row.append(self.cell);self.cell=None
  elif tag=='tr' and self.row is not None:
   self.table['rows'].append(self.row);self.row=None
  elif tag=='table':self.table=None

def translated(value):
 from benchmarks.reporting import COLS,LABEL
 from benchmarks import core
 methods={'program':'機械','ai':'AI','screen-reader':'実SR'}
 rows=[]
 for r in value['rows']:
  cells=[]
  for k,_ in COLS:
   v=r[k]
   if k in {'expected','actual','grade'}:v=LABEL.get(v,v)
   elif k=='mode':v=core.modes.MODES[v]['label']
   elif k=='method':v=methods.get(v,'未実施')
   elif k=='evidence':v='\n'.join(v)
   cells.append(v)
  rows.append(cells)
 return rows

def workbook_rows(book,sheet,expected,start=2):
 rows=list(book[sheet].values)[start-1:];actual=[['' if c is None else c for c in r] for r in rows]
 assert actual==expected,('workbook cells differ',sheet)

def benchmark_book(book,value):
 workbook_rows(book,'採点結果',translated(value))
 for name,rows in extra_rows(value,book).items():workbook_rows(book,name,rows)
 return len(value['rows'])*14

def benchmark_html(path,value,text=None):
 text=Path(path).read_text() if text is None else text
 rows=Tables(text).tables[0]['rows'][1:];expected=translated(value);assert len(rows)==len(expected)
 for index,(actual,wanted,original) in enumerate(zip(rows,expected,value['rows'])):
  assert len(actual)==len(wanted)
  for col,(cell,v) in enumerate(zip(actual,wanted)):
   if col==13:
    assert [(Path(path).parent/unquote(href)).resolve() for href in cell['links']]==[(Path(path).parents[2]/p).resolve() for p in original['evidence']],('HTML evidence association',index)
   else:assert cell['text']==str(v),('HTML cell differs',index,col,cell['text'],v)
 for title,expected_rows in extra_rows(value).items():
  table=next(t for t in Tables(text).tables if t['rows'] and t['rows'][0][0]['text']=='基準' and any(c['text']==('候補一覧の照合' if title=='取得期待の照合' else '取得期待の種類') for c in t['rows'][0]))
  cells=table['rows'][1:]
  if len(table['rows'][0])==7:expected_rows=[row[:7] for row in expected_rows]
  assert len(cells)==len(expected_rows)
  for actual,wanted in zip(cells,expected_rows):
   assert len(actual)==len(wanted)
   for n,(cell,v) in enumerate(zip(actual,wanted)):
    if title=='取得期待の照合' and n==9:
     assert [(Path(path).parent/unquote(href)).resolve() for href in cell['links']]==[(Path(path).parents[2]/p).resolve() for p in str(v).splitlines()]
    else:assert cell['text']==str(v),('acquisition HTML cell',title,n)
 return len(rows)*14

def extra_rows(value,book=None):
 from benchmarks import core
 from benchmarks.reporting import LABEL
 kinds={'inventory':'対象の列挙','focus-sequence':'フォーカス経路','viewport':'表示幅と拡大','state-capture':'操作前後の状態','timeline':'時系列の区間','language':'指定言語','accessible-name':'名前と表示ラベル','geometry':'サイズと位置'}
 result={}
 pending=value.get('pending_evidence_contracts',[])
 if pending:
  rows=[[r['criterion'],core.modes.MODES[r['mode']]['label'],r['page'],r['state'],r['checkpoint'],kinds.get(r['kind'],r['kind']),LABEL.get(r['status'],r['status']),r.get('observed','対応する取得照合又は証拠がありません。')] for r in pending]
  if book and book['取得期待の未確認'].max_column==7:rows=[r[:7] for r in rows]
  result['取得期待の未確認']=rows
 acquired=[r for r in value.get('acquisition_results',[]) if r['status'] in {'matched','mismatch'}]
 if acquired:
  result['取得期待の照合']=[[r['criterion'],core.modes.MODES[r['mode']]['label'],r['page'],r['state'],r['checkpoint'],{'matched':'候補一覧一致','mismatch':'候補一覧不一致'}[r['status']],'\n'.join(r['expected_targets']),'\n'.join(r['actual_targets']),r['observed'],'\n'.join(r['evidence'])] for r in acquired]
 return result

def page_formats(report,book,value,catalog,manifest):
 import checksheet,page_workflow
 from html import unescape
 model=checksheet.build(value,catalog,manifest=manifest)
 workbook_rows(book,'チェックシート',[[r.get(k,'') for k,_ in checksheet.COLUMNS] for r in model['rows']],7)
 machine_columns=['criterion','checkpoint','expected','outcome','environment','capture','target','observed','evidence','note']
 workbook_rows(book,'機械検査',[[r.get(k,'') for k in machine_columns] for r in value['machine_checks']])
 tables=Tables(Path(report).read_text()).tables
 table=next(t for t in tables if 'checksheet-table' in t['attrs'].get('class',''))
 rows=table['rows'][1:];assert len(rows)==len(model['rows'])
 for i,(cells,row) in enumerate(zip(rows,model['rows'])):
  assert len(cells)==len(checksheet.COLUMNS)
  for cell,(key,_) in zip(cells,checksheet.COLUMNS):
   if key=='evidence':
    assert [(Path(report).parent/unquote(p)).resolve() for p in cell['links']]==[(Path(report).parent/p).resolve() for p in row.get('evidence_paths',[])],('page evidence association',i)
   else:
    expected=str(row.get(key,''))
    if key=='locations' and row.get('failure_ids'):expected+='\n不適合箇所の詳細'
    assert cell['text']==expected,('page HTML cell differs',i,key)
 return {'checksheet_cells':len(rows)*len(checksheet.COLUMNS),'machine_cells':len(value['machine_checks'])*len(machine_columns)}
