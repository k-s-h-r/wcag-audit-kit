"""Run the production collector against a frozen, answer-separated fixture corpus."""
import asyncio
import contextlib
from functools import partial
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
import threading
import uuid
import platform
import sys
from importlib.metadata import version
from . import core, inactive_control_probe, residual_evidence, status_capture, text_paint_evidence
from scripts.skill_layout import resource_files,SKILLS


class PublicFiles(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def list_directory(self,path):self.send_error(404);return None
    def do_GET(self):
        if self.path.split('?',1)[0].endswith('.json'):self.send_error(404);return
        return super().do_GET()


def server(public,port=0):
    value=ThreadingHTTPServer(('127.0.0.1',port),partial(PublicFiles,directory=str(public)))
    threading.Thread(target=value.serve_forever,daemon=True).start()
    return value


def source_files():
    # Freeze the canonical runtime, including templates and dependency locks.
    # The other three skills share these bytes but keep their entry points and policies.
    paths=[*[core.RUNTIME/p for p in resource_files()],
           *sorted((core.ROOT/'scripts').glob('*.py')),
           *sorted((core.ROOT/'benchmarks').glob('*.py')),
           core.ROOT/'package.json',core.ROOT/'package-lock.json',core.ROOT/'benchmarks/WORKER.md',
           *sorted((core.ROOT/'skills').rglob('SKILL.md')),
           *[core.ROOT/'skills'/name/'agents/openai.yaml' for name in SKILLS]]
    return sorted(set(paths))


def implementation_digest():
    return core.digest({p.relative_to(core.ROOT).as_posix():core.file_hash(p) for p in source_files()})


def environment():
    return {'system':platform.system(),'kernel':platform.release(),'python':platform.python_version(),
            'playwright':version('playwright'),'chromium':subprocess.run([shutil.which('chromium') or 'chromium','--version'],capture_output=True,text=True,check=True).stdout.strip()}


def prepare(run,criterion=None,selected_modes=None,port=0,config=None,*,text_paint=False,machine_targets=False,residual_only=False):
    run=Path(run);data=core.corpus();selected_modes=selected_modes or ['machine']
    chosen=[s for s in data['suites'] if not criterion or s['criterion'] in criterion]
    if criterion and set(criterion)!={s['criterion'] for s in chosen}:raise ValueError('指定基準はまだ問題集に登録されていません')
    if any(m not in core.modes.MODES for m in selected_modes):raise ValueError('モードが不正')
    selected_criteria = [suite['criterion'] for suite in chosen]
    if machine_targets:
        if selected_modes != ['machine']:
            raise ValueError('--machine-targetsはmachineモード専用')
        chosen = [dict(suite, cases=[
            case for case in suite['cases']
            if any(core.verification_group(row) == 'machine_target' for row in case['expectations'])
        ]) for suite in chosen]
        chosen = [suite for suite in chosen if suite['cases']]
        if not chosen:
            raise ValueError('選んだ基準に機械検出対象の期待結果がありません')
    if residual_only:
        if selected_modes != ['machine'] or text_paint:
            raise ValueError('--residual-onlyはmachineモード専用で、--text-paintとは併用しない')
        chosen = [dict(suite, cases=[case for case in suite['cases']
            if any(residual_evidence.selected(dict(case,criterion=suite['criterion']), row)
                   and core.verification_group(row) == 'machine_target' for row in case['expectations'])])
            for suite in chosen]
        chosen = [suite for suite in chosen if suite['cases']]
        if not chosen:
            raise ValueError('選んだ基準にブラウザー計測の対象がありません')
    configuration = dict(config or {'max_states':8,'max_steps':32,'max_depth':3,'max_images':6})
    if 'text_paint_images' in configuration:
        raise ValueError('文字の画素測定は--text-paintで指定する')
    if text_paint:
        if not set(selected_modes) <= text_paint_evidence.MODES or '1.4.3' not in {s['criterion'] for s in chosen}:
            raise ValueError('--text-paintにはmachine、ai又はfullモードと1.4.3を含む対象が必要')
        configuration['text_paint_images'] = text_paint_evidence.IMAGE_BUDGET
    if run.exists() and any(run.iterdir()):raise ValueError('新しい出力先を指定する。再開は--resume')
    run.mkdir(parents=True,exist_ok=True);public=run/'worker/public'
    for suite in (chosen if residual_only else data['suites']):
        shutil.copytree(core.ROOT/'benchmarks/cases'/suite['criterion']/'public',public/suite['criterion'])
    # The server never has access to the oracle: its document root is worker/public.
    http=server(public,port);base=f'http://127.0.0.1:{http.server_port}'
    try:
        ids={r['id']:r for r in core.modes.catalog()['checkpoints']};jobs=[]
        for mode in selected_modes:
            for suite in chosen:
                for case in suite['cases']:
                    ident=f'{mode}--{suite["criterion"]}--{case["id"]}'
                    jobs.append(dict(id=ident,mode=mode,criterion=suite['criterion'],case=case['id'],pages=case['pages'],
                        urls={p:f'{base}/{suite["criterion"]}/{p}' for p in case['pages']},states=case['states'],
                        checkpoints=case['checkpoints'],acquisition_checkpoints=sorted({e['checkpoint'] for e in case.get('evidence_expectations',[])}-{e['checkpoint'] for e in case['expectations']}),checks={p:ids[p]['check'] for p in case['checkpoints']},
                        target_aliases=case.get('target_aliases',{}),
                        evidence_requirements={e['checkpoint']:{'image':e['evidence_kind']=='visual-semantic',
                            'speech':e['evidence_kind']=='screen-reader','comparison':e['evidence_kind']=='cross-page'} for e in case['expectations']},
                        comparison_record_page=case['pages'][-1] if len(case['pages'])>1 else None,
                        required_environment=case.get('requires_environment',[]),evidence_root=f'audit-runs/{ident}',method_root='implementation',
                        instruction='正解ファイルは参照せず、実ページ・操作・証拠から観点別に判定する。未実施はnot_run、確定できない場合はcant_tell。'))
        oracle={'schema_version':'1','suites':data['suites']};core.save(run/'oracle.snapshot.json',oracle)
        git=subprocess.run(['git','rev-parse','HEAD'],cwd=core.ROOT,text=True,capture_output=True)
        metadata=dict(schema_version='1',run_id=uuid.uuid4().hex,created_at=core.timestamp(),corpus_digest=data['digest'],
            oracle_digest=core.digest(oracle),modes=selected_modes,selection=selected_criteria,port=http.server_port,
            configuration=configuration,machine_targets_only=machine_targets,residual_probes_only=residual_only,
            implementation_digest=implementation_digest(),git_head=git.stdout.strip(),working_tree=True,
            environment=environment(),
            standard=core.audit.CATALOG['standard'],normative_hashes={s['criterion']:core.audit.CRITERIA[s['criterion']]['normative_sha256'] for s in chosen},
            mode_catalog=core.modes.catalog(),criteria_catalog=[{k:c[k] for k in ['id','title','level']} for c in core.audit.CATALOG['criteria']])
        core.save(run/'run.json',metadata)
        core.save(run/'worker/tasks.json',dict(schema_version='1',run_id=metadata['run_id'],corpus_digest=data['digest'],jobs=jobs,
            serve_command=f'python3 benchmarks/run.py serve --run {run.resolve()}',
            note='このファイルとpublic/だけを検査担当へ渡す。正解・採点結果は渡さない。'))
        core.save(run/'progress.json',{'jobs':{},'collection':'running'})
        for source in source_files():
            target=run/'implementation'/source.relative_to(core.ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        core.freeze(run,[run/'run.json',run/'oracle.snapshot.json',run/'worker/tasks.json',
                         *[p for p in public.rglob('*') if p.is_file()],*[p for p in (run/'implementation').rglob('*') if p.is_file()]])
        return metadata,http
    except BaseException:
        http.shutdown();http.server_close();raise


def collect_standard_page(run, meta, job, page, url, location):
    cfg=core.audit.init_config(url);cfg.update(environments=cfg['environments'][:1],keyboard_steps=6)
    labels=core.state_labels.public_specs(job['states'])
    if labels:cfg['exploration_labels']=labels
    core.audit.save(location/'config.json',cfg)
    args=['page-audit','--url',url,'--out',str(location/'run'),'--config',str(location/'config.json'),'--mode',job['mode'],
          '--max-states',str(meta['configuration']['max_states']),'--max-steps',str(meta['configuration']['max_steps']),
          '--max-depth',str(meta['configuration']['max_depth'])]
    if core.modes.MODES[job['mode']]['ai']:args+=['--max-images',str(meta['configuration']['max_images'])]
    with (location/'stdout.txt').open('w') as out,(location/'stderr.txt').open('w') as err,contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
        code=core.audit.main(args)
    if code == 0:
        plans = status_capture.plans(job['criterion'], job['checkpoints'], job['states'])
        for identifier, plan in plans.items():
            fixture = core.local(run/'worker/public', f"{job['criterion']}/{page}")
            body = fixture.read_bytes()
            verified = core.load(run/'integrity.json')['files']
            source_digest = sha256(body).hexdigest()
            if verified.get(fixture.relative_to(run.resolve()).as_posix()) != source_digest:
                raise ValueError('状態変化を取得する公開ページが変更された')
            binding = dict(job_id=job['id'], page=page, mode=job['mode'], state=identifier,
                           fixture_sha256=source_digest)
            observed = asyncio.run(status_capture.collect(url, body, binding, plan))
            core.save(location/f'status-capture-{identifier}.json', observed)
        text_paint_evidence.collect(run, meta, job, page, location)
        inactive_control_probe.collect(run, meta, job, page, location)
    return code


def collect(run,*,criterion=None,selected_modes=None,port=0,resume=False,config=None,text_paint=False,machine_targets=False,residual_only=False):
    from ledger_lock import run_lock
    run=Path(run)
    if resume:
        meta,progress=core.verify(run)
        if meta['implementation_digest']!=implementation_digest():raise ValueError('検証方法・収集器・採点器の実装が変わった。別runで比較する')
        if meta['environment']!=environment():raise ValueError('実行環境が変わった。別runへ記録する')
        if residual_only != meta.get('residual_probes_only',False):
            raise ValueError('再開時に--residual-onlyの指定を変えない')
        if machine_targets != meta.get('machine_targets_only', False):
            raise ValueError('再開時に--machine-targetsの指定を変えない')
        if criterion and set(criterion)!=set(meta['selection']):raise ValueError('再開時に対象基準を変えない')
        if selected_modes and selected_modes!=meta['modes']:raise ValueError('再開時にモードを変えない')
        saved_configuration = dict(meta['configuration'])
        if text_paint != (saved_configuration.pop('text_paint_images', None) is not None):
            raise ValueError('再開時に--text-paintの指定を変えない')
        if config and config!=saved_configuration:raise ValueError('再開時に実行上限を変えない')
        http=server(run/'worker/public',meta['port'])
    else:meta,http=prepare(run,criterion,selected_modes,port,config,text_paint=text_paint,machine_targets=machine_targets,residual_only=residual_only)
    try:
        with run_lock(run):
            try:
                _,progress=core.verify(run);progress['collection']='running';core.save(run/'progress.json',progress)
                for job in core.tasks(run):
                    pages=progress['jobs'].setdefault(job['id'],{})
                    for page,url in job['urls'].items():
                        if pages.get(page,{}).get('status')=='completed':continue
                        location=run/'audit-runs'/job['id']/Path(page).stem/('attempt-'+uuid.uuid4().hex[:12]);location.mkdir(parents=True)
                        state='interrupted';code=None
                        try:
                            code=0 if residual_only else collect_standard_page(run,meta,job,page,url,location)
                            if code == 0:
                                residual_evidence.collect(run,job,page,location)
                            state='completed' if code==0 else 'error'
                        finally:
                            pages[page]={'status':state,'exit_code':code,'directory':(location/'run').relative_to(run).as_posix()}
                            core.save(location/'receipt.json',dict(job_id=job['id'],page=page,mode=job['mode'],url=url,status=state,exit_code=code))
                            core.freeze(run,[p for p in location.rglob('*') if p.is_file() and p.name!='.audit.lock'])
                            core.save(run/'progress.json',progress)
                progress['collection']='completed' if all(r['status']=='completed' for p in progress['jobs'].values() for r in p.values()) else 'partial'
                core.save(run/'progress.json',progress)
                return core.score(run)
            except BaseException:
                progress=core.load(run/'progress.json');progress['collection']='interrupted';core.save(run/'progress.json',progress)
                raise
    finally:http.shutdown();http.server_close()
