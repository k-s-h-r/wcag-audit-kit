"""Excel views and conflict-checked work exchange, backed by the JSON ledger."""
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import tempfile
import uuid
from urllib.parse import quote

from ledger_lock import run_lock
import work_queue as queue

# Labels are part of the versioned interchange format. Context is checked on import.
CASE_COLUMNS = [
    ('case_id','検査票ID'),('criterion','基準'),('title','基準名'),('page_url','ページURL'),
    ('state','ページ状態'),('environment','環境'),('task','タスクID'),('revision','記録版'),
    ('owner','担当'),('work_state','作業状態'),('note','作業メモ'),('outcome','判定'),
    ('execution','実施状況'),('observed','観察'),('conditions_reviewed','条件確認'),
    ('exceptions_reviewed','例外確認'),('coverage_complete','全対象確認'),
    ('remaining','残る確認'),('steps_executed','実行手順'),('tests_applied','採用した検査ID'),
    ('evidence','証拠'),('comparison_pages','比較ページ'),('human_handoff','人への引き継ぎJSON')]
TARGET_COLUMNS = [('case_id','検査票ID'),('index','対象番号'),('target','対象'),('expected','期待結果'),
                  ('observed','観察'),('outcome','判定'),('evidence','証拠'),('media_review','媒体の区間比較JSON')]
METHOD_COLUMNS = [('case_id','検査票ID'),('method','観察方法'),('status','実施状況'),('reason','根拠')]
FOCUS_EVIDENCE_TITLE = 'フォーカスの画像証拠'
FOCUS_EVIDENCE_COLUMNS = [
    ('criterion', '達成基準'), ('name', '操作経路'), ('target', '対象'), ('environment', '環境'),
    ('status', '取得状態'), ('reason', '理由'), ('before_image', '入力前の画像'),
    ('after_image', '入力後の画像'), ('evidence', '操作の証拠'),
]
FOCUS_EVIDENCE_FILES = {'before_image', 'after_image', 'evidence'}
FOCUS_EVIDENCE_STATUSES = {
    'not_run': '未実施', 'skipped': '取得省略', 'partial': '一部取得', 'captured': '取得済み',
    'incomparable': '比較不可', 'error': '取得エラー',
}

CONTEXT = [key for key,_ in CASE_COLUMNS[:8]]
LISTS = {'remaining','steps_executed','tests_applied','evidence','comparison_pages'}
FLAGS = {'conditions_reviewed','exceptions_reviewed','coverage_complete'}
FORMAT = 'wcag-xlsx-1'
MAX_CASES = 10000


def text(value):
    return '' if value is None else str(value)


def lines(value):
    return '\n'.join(value or [])


def decode_lines(value):
    return [line.strip() for line in text(value).splitlines() if line.strip()]


def encoded(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':')) if value is not None else ''


def boolean(value):
    if type(value) is bool: return value
    if value in {'TRUE','true'}: return True
    if value in {'FALSE','false','',None}: return False
    raise ValueError('確認フラグはTRUE又はFALSEにする')


def json_cell(value, label):
    if value in {'',None}: return None
    try:
        result=json.loads(value)
    except (TypeError,ValueError) as exc:
        raise ValueError(label+'はJSONオブジェクトにする') from exc
    if not isinstance(result,dict): raise ValueError(label+'はJSONオブジェクトにする')
    return result


def case_row(case, plan):
    a=case['assessment_data'] or {}; assigned=queue.assignment(plan,case['case_id'])
    result={k:case[k] for k in CONTEXT if k not in {'task','revision'}}
    result.update(task=(queue.task_for(plan,case['case_id']) or {}).get('id',''),revision=case['assessment'] or '',
                  owner=assigned['owner'],work_state=assigned['state'],note=assigned['note'],
                  outcome=case['outcome'],execution=a.get('execution','not_run'),observed=a.get('observed',''),
                  human_handoff=encoded(a.get('human_handoff')))
    for field in LISTS:result[field]=lines(a.get(field,[]))
    for field in FLAGS:result[field]=a.get(field,False)
    return result


def target_rows(case):
    targets=(case['assessment_data'] or {}).get('targets',[]) or [{}]
    return [dict(case_id=case['case_id'],index=i+1,target=t.get('target',''),expected=t.get('expected',''),
                 observed=t.get('observed',''),outcome=t.get('outcome',''),evidence=lines(t.get('evidence',[])),
                 media_review=encoded(t.get('media_review'))) for i,t in enumerate(targets)]


def method_rows(case):
    methods=(case['assessment_data'] or {}).get('method_coverage',[])
    methods=methods or [{'method':m} for m in case['methods']]
    return [dict(case_id=case['case_id'],method=m['method'],status=m.get('status',''),reason=m.get('reason','')) for m in methods]


def baseline(case, plan):
    import audit
    row=case_row(case,plan)
    return audit.digest({'assessment':case['assessment_data'],'assignment':queue.assignment(plan,case['case_id']),
                         'context':{k:row[k] for k in CONTEXT}})


def validate_values(values):
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
    for value in values:
        if isinstance(value,str) and (len(value)>32767 or ILLEGAL_CHARACTERS_RE.search(value)):
            raise ValueError('Excelの文字数又は制御文字の制限。タスクを分け、長い記録はJSONで扱う')


def append(ws, values):
    if ws.max_row>=1048576:raise ValueError('Excelの行数上限。タスク又はページで分割して出力する')
    validate_values(values)
    ws.append(values)
    for cell in ws[ws.max_row]:
        # Page text starting with =, +, - or @ remains literal text, never a formula.
        if isinstance(cell.value,str):cell.data_type='s'


def sheet(book, name, columns, rows, readonly=False):
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    ws=book.create_sheet(name);append(ws,[label for _,label in columns])
    for row in rows:append(ws,[row.get(key,'') for key,_ in columns])
    ws.freeze_panes='C2';ws.auto_filter.ref=ws.dimensions
    for i,(key,_) in enumerate(columns,1):
        ws.column_dimensions[get_column_letter(i)].width=24 if key not in {'observed','note','target','expected','remaining','evidence'} else 48
    for cell in ws[1]:
        cell.font=Font(color='FFFFFF',bold=True);cell.fill=PatternFill('solid',fgColor='244A64')
    for row in ws.iter_rows(min_row=2):
        for cell in row:cell.alignment=Alignment(vertical='top',wrap_text=True)
    ws.protection.sheet=readonly
    return ws


def focus_evidence_link(run, path, directory):
    """Resolve a run-local evidence file relative to the exported report."""
    parts = path.split('/')
    if parts[0] != 'evidence' or any(part in {'', '.', '..'} or '\\' in part for part in parts):
        return None
    root = run.resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root / 'evidence') or not target.is_file():
        return None
    return quote(Path(os.path.relpath(target, directory)).as_posix())


def focus_evidence_sheet(book, run, out, rows):
    from openpyxl.styles import Font

    display_rows = [dict(row, status=FOCUS_EVIDENCE_STATUSES.get(row['status'], row['status'])) for row in rows]
    ws = sheet(book, FOCUS_EVIDENCE_TITLE, FOCUS_EVIDENCE_COLUMNS, display_rows, True)
    ws.column_dimensions['F'].width = 44
    for column, (key, _) in enumerate(FOCUS_EVIDENCE_COLUMNS, 1):
        if key not in FOCUS_EVIDENCE_FILES:
            continue
        for index, row in enumerate(rows, 2):
            target = focus_evidence_link(run, row[key], out.parent)
            if target:
                cell = ws.cell(index, column)
                cell.hyperlink = target
                cell.font = Font(color='00529B', underline='single')


def human_sheets(book, model):
    from math import ceil
    from unicodedata import east_asian_width
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.hyperlink import Hyperlink
    import checksheet
    failure_rows={f['id']:i for i,f in enumerate(model['failures'],7)}
    for name,columns,rows in [('チェックシート',checksheet.COLUMNS,model['rows']),
                              ('不適合箇所',checksheet.FAILURE_COLUMNS,model['failures'])]:
        ws=sheet(book,name,columns,rows,True);ws.insert_rows(1,5)
        prelude=[f'WCAG 2.2 {name}', '集計範囲：'+model['scope'], model['legend'],model['guidance'],
                 ' '.join(model['notices']) or '集計時点の保存済み判定を表示しています。']
        if name=='不適合箇所' and not rows:prelude[4]+=' 記録された不適合箇所はありません。未確認の有無はチェックシートを参照。'
        for index,value in enumerate(prelude,1):
            validate_values([value])
            ws.cell(index,1,value);ws.cell(index,1).data_type='s'
            ws.merge_cells(start_row=index,start_column=1,end_row=index,end_column=len(columns))
            ws.cell(index,1).alignment=Alignment(vertical='top',wrap_text=True)
            ws.row_dimensions[index].height=30 if index==1 else 44
        ws['A1'].font=Font(size=18,bold=True,color='244A64')
        widths={'criterion':14,'title':26,'level':9,'checkpoint':42,'applicability':14,'judgment':18,
                'locations':50,'notes':52,'remaining':45,'evidence':45,'id':14,'page_url':44,
                'state':18,'environment':18,'target':32,'observed':42,'expected':42,'steps':42}
        for i,(key,_) in enumerate(columns,1):ws.column_dimensions[get_column_letter(i)].width=widths[key]
        ws.row_dimensions[6].height=32
        palette={'passed':'E2F0D9','failed':'FCE4D6','unverified':'FFF2CC','inapplicable':'E7E6E6','out_of_target_level':'E7E6E6'}
        for index,row in enumerate(rows,7):
            height=3
            for i,(key,_) in enumerate(columns,1):
                cell=ws.cell(index,i)
                # Estimate wrapped CJK lines so the printed sheet remains legible.
                height=max(height,sum(max(1,ceil(sum(2 if east_asian_width(c) in {'W','F'} else 1 for c in line)/widths[key]))
                                      for line in str(cell.value or '').split('\n')))
                if row.get('kind')=='criterion':cell.font=Font(bold=True)
                if key=='judgment':cell.fill=PatternFill('solid',fgColor=palette[row['status']])
                if key=='locations':
                    location = None
                    if row.get('failure_ids'):
                        target = failure_rows[row['failure_ids'][0]]
                        location = f"'不適合箇所'!A{target}"
                    elif row.get('machine_issues_link'):
                        location = "'自動検出した問題'!A1"
                    if location:
                        cell.hyperlink = Hyperlink(ref=cell.coordinate, location=location, display=cell.value)
                        cell.font = Font(color='00529B', underline='single')
            ws.row_dimensions[index].height=min(409,height*15)
        ws.freeze_panes='D7';ws.auto_filter.ref=f'A6:{get_column_letter(len(columns))}{max(6,ws.max_row)}'
        ws.protection.autoFilter=False
        ws.print_title_rows='1:6';ws.print_options.horizontalCentered=True
        ws.page_setup.orientation='landscape';ws.page_setup.paperSize=ws.PAPERSIZE_A3
        ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0
        ws.sheet_properties.pageSetUpPr.fitToPage=True
        ws.print_area=ws.dimensions
        ws.oddFooter.center.text='&P / &N'
    book.active=0


def export(run, out, *, mode='report', task=None, owner=None, page=None, page_exact=None, criterion=None, pending=False, page_view=False):
    import audit
    from openpyxl import Workbook
    from openpyxl.worksheet.datavalidation import DataValidation
    if mode not in {'report','work'}:raise ValueError('Excel出力のモードが不正')
    if out.suffix.lower()!='.xlsx' or out.exists():raise ValueError('新しい.xlsxの出力先を指定する')
    out.parent.mkdir(parents=True,exist_ok=True)
    with run_lock(run):
        result=audit.outcomes(run);plan=audit.run_plan(run);meta,catalog=audit.run_catalog(run)
        if page_view:
            if not page_exact or mode!='report':raise ValueError('ページ帳票にはreportとpage_exactが必要')
            from page_workflow import page_result
            result=page_result(run,page_exact,result)
        cases=queue.select(result['cases'],plan,task=task,owner=owner,page=page,page_exact=page_exact,criterion=criterion,pending=pending)
        if not cases:raise ValueError('条件に合う検査票がない')
        if len(cases)>MAX_CASES:raise ValueError('1万票を超える。--task、--page、--criterion等で分割して出力する')
        selected_criteria=({r['criterion'] for r in cases} if criterion or task or owner is not None or pending else
                           {c['id'] for c in result['criteria']})
        environments = {r['environment'] for r in cases}
        result['machine_checks']=[c for c in result['machine_checks'] if c['criterion'] in selected_criteria and c['environment'] in environments]
        focus_evidence = [row for row in result.get('focus_evidence', [])
                          if row['criterion'] in selected_criteria and row['environment'] in environments]
        export_id=uuid.uuid4().hex
        if mode=='work':
            audit.run_catalog(run,for_write=True);queue.work(plan,create=True)
            audit.save(run/'plan.json',plan)
        identity={'format':FORMAT,'mode':mode,'export_id':export_id,
                  'run_id':queue.work(plan).get('run_id',''),
                  'config_digest':meta['config_digest'],'catalog_digest':meta['catalog_digest']}
        case_table=[case_row(c,plan) for c in cases]
        targets=[t for c in cases for t in target_rows(c)]
        methods=[m for c in cases for m in method_rows(c)]
        snapshot={'identity':identity,'cases':case_table,'targets':targets,'methods':methods,
                  'baselines':{c['case_id']:baseline(c,plan) for c in cases}}
        book=Workbook();book.remove(book.active)
        import checksheet
        model=checksheet.build(result,catalog,cases=cases,
            filters=dict(task=task,owner=owner,page=page,page_exact=page_exact,criterion=criterion,pending=pending),
            manifest=audit.load(run/'capture-manifest.json'))
        human_sheets(book,model)
        if result.get('verification'):
            from verification_modes import COVERAGE_COLUMNS, table_rows
            sheet(book,'モード別の確認範囲',COVERAGE_COLUMNS,
                  [r for r in table_rows(result['verification']) if r['criterion'] in selected_criteria],True)
        from page_workflow import grouped_machine_issues
        sheet(book,'自動検出した問題',[(k,v) for k,v in [('criterion','達成基準'),('expected','機械で確認した条件'),('target','対象要素・位置'),
              ('outcome','機械の結果'),('observed','観察'),('count','状態・経路の記録数'),('states','確認した状態・環境'),('evidence','全記録の証拠'),('note','判定範囲')]],
              grouped_machine_issues(result['machine_checks']),True)
        sheet(book,'機械検査',[(k,v) for k,v in [('criterion','達成基準'),('checkpoint','検査'),('expected','期待結果'),
              ('outcome','機械ルールの判定'),('environment','環境'),('capture','状態・経路'),('target','対象'),('observed','観察'),('evidence','証拠'),('note','判定範囲')]],
              result['machine_checks'],True)
        if focus_evidence:
            focus_evidence_sheet(book, run, out, focus_evidence)
        summary=[['出力モード',mode],['サイト',result['url']],['全検査票',len(result['cases'])],['このファイルの票数',len(cases)],
                 ['検証完了',result['audit_complete']],['範囲確認',result['scope_confirmed']],
                 ['人の確認待ち',len(result['human_review_cases'])],['未訪問URL',len(result['unvisited'])]]
        summary += [[key,value] for key,value in result['counts'].items()]
        summary += [['画像の設定',result['inspection_policy']['screenshots']],['実スクリーンリーダーの設定',result['inspection_policy']['screen_reader']],
                    ['操作・状態の調査',result['interaction_review']['status']],['操作調査の完了',result['interaction_review']['complete']]]
        if result.get('verification'):
            from verification_modes import report_summary_rows
            summary += [['検証モード',result['verification']['label']],['モード対応表の記号',result['verification']['legend']],
                        ['モード対応表の注意',result['verification']['notice']]]
            summary += [list(item) for item in report_summary_rows(result['verification'])]
        else:
            reader_statuses = {p['screen_reader']['status'] for p in result['interaction_review'].get('pages',{}).values()}
            summary += [['実SRの実施記録', ', '.join(sorted(reader_statuses)) or 'not_recorded']]
        summary += [['使い方','チェックシート・不適合箇所は出力条件内の閲覧用。編集しても取り込まれない。workでは検査票・対象・観察方法を編集しexcel import --checkで確認する。'],
                    ['共同作業','同じrunから配布し、調整担当が取り込む。同一runのJSONを複数端末で同時同期しない。'],
                    ['判定の注意','作業状態のdoneとWCAG適合・検証完了は別。未確認は通過に数えない。'],
                    ['行の編集','検査票の灰色の識別情報は変更しない。行の並べ替え可。対象の追加は検査票IDと対象番号を指定。'],
                    ['複雑な記録','人への引き継ぎと媒体の区間比較はJSON欄。既存のrecordコマンドも利用できる。']]
        sheet(book,'概要',[('label','項目'),('value','内容')],[dict(label=a,value=b) for a,b in summary],True)
        ws=sheet(book,'検査票',CASE_COLUMNS,case_table,mode=='report')
        from openpyxl.styles import PatternFill
        for row in ws.iter_rows(min_row=2,max_col=len(CONTEXT)):
            for cell in row:cell.fill=PatternFill('solid',fgColor='E8E8E8')
        for key,options in [('work_state','todo,in_progress,blocked,done'),('outcome','not_run,passed,failed,inapplicable,cant_tell'),('execution','not_run,completed,blocked')]:
            index=next(i for i,(k,_) in enumerate(CASE_COLUMNS,1) if k==key)
            from openpyxl.utils import get_column_letter
            rule=DataValidation(type='list',formula1='"'+options+'"',allow_blank=False);rule.errorTitle='一覧の値を選ぶ';rule.showErrorMessage=True
            ws.add_data_validation(rule);rule.add(f'{get_column_letter(index)}2:{get_column_letter(index)}{len(cases)+1}')
        sheet(book,'対象',TARGET_COLUMNS,targets,mode=='report')
        sheet(book,'観察方法',METHOD_COLUMNS,methods,mode=='report')
        from inspection import report_rows
        selected_ids={c['page_id'] for c in cases}
        sheet(book,'操作調査',[('url','ページURL'),('capture','状態・環境'),('label','見える操作対象'),('location','位置'),
              ('visual','画像確認'),('status','操作確認'),('observed','観察'),('steps','実施した操作'),
              ('remaining','残る確認'),('screen_reader','実SRの実施結果'),('source_review','元の調査票')],
              [r for r in report_rows(result) if r['page_id'] in selected_ids],True)
        sheet(book,'達成基準',[('id','基準'),('level','レベル'),('title','名称'),('status','状況'),('counts','件数'),('normative_url','原典')],
              [dict(c,counts=encoded(c['counts'])) for c in result['criteria']],True)
        handoffs=[]
        for case in cases:
            handoff=(case['assessment_data'] or {}).get('human_handoff')
            if not handoff:continue
            for check in handoff['checks']:
                handoffs.append(dict(case_id=case['case_id'],criterion=case['criterion'],url=case['page_url'],
                    target=check['target'],reason=handoff['reason'],reviewer=handoff['reviewer'],
                    environment=handoff['required_environment'],steps=lines(check['steps']),expected=check['expected'],
                    attempts='\n'.join(a['method']+': '+a['observed'] for a in handoff['attempts']),resume=handoff['resume']))
        sheet(book,'人への確認',[(k,v) for k,v in [('case_id','検査票ID'),('criterion','基準'),('url','ページURL'),('target','対象'),
              ('reason','残る理由'),('reviewer','必要な担当'),('environment','必要な環境'),('steps','確認手順'),('expected','判定条件'),
              ('attempts','試した方法'),('resume','結果の戻し方')]],handoffs,True)
        tasks=queue.work(plan)['tasks']
        by_id={c['case_id']:c for c in result['cases']}
        sheet(book,'タスク',[('id','タスクID'),('title','対象範囲'),('size','票数'),('owners','担当'),('remaining','未完了'),('human','人の確認待ち')],
              [dict(t,size=len(t['case_ids']),owners=', '.join(sorted({queue.assignment(plan,i)['owner'] for i in t['case_ids']})),
                    remaining=sum(queue.unfinished(by_id[i]) for i in t['case_ids']),
                    human=sum(bool((by_id[i]['assessment_data'] or {}).get('human_handoff')) for i in t['case_ids'])) for t in tasks],True)
        ws=book.create_sheet('_meta')
        for key,value in identity.items():append(ws,[key,value])
        ws.sheet_state='veryHidden'
        if mode=='work':audit.save(run/'exchanges'/(export_id+'.json'),snapshot)
        temporary=None
        try:
            with tempfile.NamedTemporaryFile(dir=out.parent,suffix='.xlsx',delete=False) as handle:temporary=Path(handle.name)
            book.save(temporary);os.link(temporary,out)
        finally:
            book.close()
            if temporary is not None:temporary.unlink(missing_ok=True)
        return {'file':str(out),'mode':mode,'export_id':export_id,'cases':len(cases),'total_cases':len(result['cases'])}


def read_rows(book, name, columns):
    if name not in book:raise ValueError('Excelのシートが不足: '+name)
    rows=list(book[name].iter_rows(values_only=True))
    if not rows or list(rows[0])!=[label for _,label in columns]:raise ValueError('Excelの列を変更しない: '+name)
    return [{key:('' if value is None else value) for (key,_),value in zip(columns,row)} for row in rows[1:] if any(v is not None for v in row)]


def import_book(run, path, *, check=False):
    import audit
    from openpyxl import load_workbook
    try:book=load_workbook(path,data_only=False)
    except Exception as exc:raise ValueError('Excelファイルを読み取れない: '+str(exc)) from exc
    try:
        for ws in book:
            for row in ws:
                if any(c.data_type=='f' for c in row):raise ValueError('数式は取り込まない。文字列又は値を記入する')
        if '_meta' not in book:raise ValueError('このスキルから出力した作業用Excelを指定する')
        identity={r[0]:r[1] for r in book['_meta'].iter_rows(values_only=True)}
        if identity.get('format')!=FORMAT or identity.get('mode')!='work':raise ValueError('作業用（work）のExcelだけを取り込める')
        if not re.fullmatch(r'[0-9a-f]{32}',text(identity.get('export_id'))):raise ValueError('出力IDが不正')
        table=read_rows(book,'検査票',CASE_COLUMNS)
        targets=read_rows(book,'対象',TARGET_COLUMNS);methods=read_rows(book,'観察方法',METHOD_COLUMNS)
    finally:book.close()
    with run_lock(run):
        meta,catalog=audit.run_catalog(run,for_write=True);plan=audit.run_plan(run)
        snapshot_path=run/'exchanges'/(identity['export_id']+'.json')
        if not snapshot_path.is_file():raise ValueError('このrunに作業用Excelの配布記録がない')
        snapshot=audit.load(snapshot_path)
        if (snapshot['identity']!=identity or identity['run_id']!=queue.work(plan).get('run_id') or
            identity['config_digest']!=meta['config_digest'] or identity['catalog_digest']!=meta['catalog_digest']):
            raise ValueError('Excelとrun・設定・検査定義が一致しない')
        original={r['case_id']:r for r in snapshot['cases']}
        ids=[r['case_id'] for r in table]
        if len(ids)!=len(set(ids)) or set(ids)!=set(original):raise ValueError('検査票IDの重複・追加・削除がある')
        grouped_targets={i:[] for i in ids};grouped_methods={i:[] for i in ids}
        for row in targets:
            if row['case_id'] not in original:raise ValueError('対象に配布範囲外の検査票IDがある')
            if type(row['index']) is not int or row['index']<1:raise ValueError('対象番号は1以上の整数')
            grouped_targets[row['case_id']].append(row)
        for row in methods:
            if row['case_id'] not in original:raise ValueError('観察方法に配布範囲外の検査票IDがある')
            grouped_methods[row['case_id']].append(row)
        current={c['case_id']:c for c in audit.outcomes(run)['cases']}
        definitions={c['id']:c for c in catalog['criteria']}
        original_targets={i:[] for i in ids};original_methods={i:[] for i in ids}
        for item in snapshot['targets']:original_targets[item['case_id']].append(item)
        for item in snapshot['methods']:original_methods[item['case_id']].append(item)
        prepared=[];updates={};conflicts=[];receipts={}
        applied=queue.work(plan).get('imports',{}).get(identity['export_id'],{})
        for row in table:
            ident=row['case_id'];before=original[ident]
            if any(row[k]!=before[k] for k in CONTEXT):raise ValueError('識別情報を変更しない: '+ident)
            ts=sorted(grouped_targets[ident],key=lambda t:t['index']);ms=sorted(grouped_methods[ident],key=lambda m:text(m['method']))
            if len({t['index'] for t in ts})!=len(ts):raise ValueError('対象番号が重複している: '+ident)
            if len({m['method'] for m in ms})!=len(ms):raise ValueError('観察方法が重複している: '+ident)
            old_ts=sorted(original_targets[ident],key=lambda t:t['index'])
            old_ms=sorted(original_methods[ident],key=lambda m:text(m['method']))
            if row==before and ts==old_ts and ms==old_ms:continue
            request_digest=audit.digest({'row':row,'targets':ts,'methods':ms})
            if applied.get(ident)==request_digest:continue
            case=current.get(ident)
            if case is None or baseline(case,plan)!=snapshot['baselines'][ident]:
                conflicts.append(ident);continue
            assigned={'owner':text(row['owner']),'state':text(row['work_state']),'note':text(row['note'])}
            if assigned['state'] not in queue.STATES:raise ValueError('作業状態が不正: '+ident)
            assessment_changed=(any(row[k]!=before[k] for k,_ in CASE_COLUMNS[11:]) or ts!=old_ts or ms!=old_ms)
            next_case=case
            if assessment_changed:
                value=deepcopy(case['assessment_data'] or {})
                for key in ['recorded_at','verified_evidence']:value.pop(key,None)
                value.update(case_id=ident,config_digest=meta['config_digest'],base_assessment=case['assessment'],
                             normative_sha256=definitions[case['criterion']]['normative_sha256'])
                for key in ['outcome','execution','observed']:value[key]=text(row[key])
                for key in FLAGS:value[key]=boolean(row[key])
                for key in LISTS:value[key]=decode_lines(row[key])
                value['targets']=[]
                for t in ts:
                    if not any(t[k] for k in ['target','expected','observed','outcome','evidence','media_review']):continue
                    target={k:text(t[k]) for k in ['target','expected','observed','outcome']};target['evidence']=decode_lines(t['evidence'])
                    review=json_cell(t['media_review'],'媒体の区間比較')
                    if review is not None:target['media_review']=review
                    value['targets'].append(target)
                value['method_coverage']=[{k:text(m[k]) for k in ['method','status','reason']} for m in ms if m['status'] or m['reason']]
                handoff=json_cell(row['human_handoff'],'人への引き継ぎ')
                value.pop('human_handoff',None)
                if handoff is not None:value['human_handoff']=handoff
                checked=audit.prepare_record(run,value,plan);prepared.append(checked)
                next_case=dict(case,outcome=checked['outcome'],assessment_data=checked)
                if row['work_state']==before['work_state']:
                    assigned['state']='done' if queue.can_finish(next_case) else 'blocked'
            if assigned['state']=='done' and not queue.can_finish(next_case):
                raise ValueError('未記録・引き継ぎ未整理の検査票をdoneにできない: '+ident)
            updates[ident]=assigned
            receipts[ident]=request_digest
        if conflicts:raise ValueError('更新競合。最新のExcelを再出力して差分を確認する: '+', '.join(conflicts))
        if not check and updates:
            plan['work'].setdefault('imports',{}).setdefault(identity['export_id'],{}).update(receipts)
            audit.commit_records(run,plan,prepared,updates)
        return {'check_only':check,'changed_cases':len(updates),'new_assessments':len(prepared),'unchanged_cases':len(table)-len(updates)}
