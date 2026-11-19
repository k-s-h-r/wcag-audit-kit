"""Run the machine audit for each configured URL with an independent page ledger."""
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path

import audit
from browser_capture import page_id
from collection_checkpoint import save_json_atomic
from ledger_lock import run_lock
from page_catalog import configured_urls, read_config
from verification_modes import select


STATUSES = ('pending', 'interrupted', 'completed', 'failed')
MANIFEST = 'page-batch.json'


def implementation_digest():
    paths = sorted(path for directory in ('scripts', 'references', 'vendor')
                   for path in (audit.ROOT/directory).rglob('*')
                   if path.is_file() and '__pycache__' not in path.parts and path.suffix not in {'.pyc', '.tmp'})
    return audit.digest({path.relative_to(audit.ROOT).as_posix(): sha256(path.read_bytes()).hexdigest()
                         for path in paths})


def batch_config(path):
    raw = path.read_bytes()
    config = read_config(path)
    if path.read_bytes() != raw:
        raise ValueError('読み込み中に設定ファイルが変更された')
    if config['scope']['mode'] != 'configured':
        raise ValueError('page-batchにはscope.mode=configuredの指定一覧が必要')
    if 'verification' not in config:
        config = select(config, 'machine')
    if config['verification']['mode'] != 'machine':
        raise ValueError('page-batchはmachineモードに対応する')
    if config['states'] or not config['environments'] or any(env.get('zoom', 1) != 1 for env in config['environments']):
        raise ValueError('page-batchには事前設定statesを含めず、自動探索用のzoom=1の環境を指定する')
    return config, sha256(raw).hexdigest()


def auth_digest(config):
    source = config.get('auth_state')
    return sha256(Path(source).read_bytes()).hexdigest() if source else None


def run_ref(identifier, attempt):
    return f'pages/{identifier}/attempt-{attempt:04d}/run'


def save_manifest(out, value):
    counts = Counter(row['status'] for row in value['pages'])
    value['counts'] = {status: counts[status] for status in STATUSES}
    value['all_pages_attempted'] = not (counts['pending'] or counts['interrupted'])
    save_json_atomic(out/MANIFEST, value)


def prepare(out, urls, inputs, resume):
    rows = [{'url': url, 'id': page_id(url), 'attempt': 1, 'run': run_ref(page_id(url), 1), 'status': 'pending'}
            for url in urls]
    if len({row['id'] for row in rows}) != len(rows):
        raise ValueError('別のURLに同じページIDが割り当たった')
    if not resume:
        if any(path.name != '.audit.lock' for path in out.iterdir()):
            raise ValueError('新しい出力先を指定する。既存のバッチは--resumeで再開する')
        value = {'schema_version': '1', 'kind': 'page-batch', 'mode': 'machine', 'inputs': inputs, 'pages': rows,
                 'notice': 'completedはページ別報告の生成を示す。達成基準やサイト全体の適合は示さない。'}
        save_manifest(out, value)
        return value

    value = audit.load(out/MANIFEST)
    if (value.get('schema_version'), value.get('kind'), value.get('mode'), value.get('inputs')) != ('1', 'page-batch', 'machine', inputs):
        raise ValueError('指定一覧・設定・認証状態又は検査の実装が変更された。新しい出力先を指定する')
    if [(row['url'], row['id']) for row in value['pages']] != [(row['url'], row['id']) for row in rows]:
        raise ValueError('保存済みのページ一覧が入力と一致しない')
    for row in value['pages']:
        if (row['status'] not in STATUSES or type(row['attempt']) is not int or row['attempt'] < 1
                or row['run'] != run_ref(row['id'], row['attempt'])):
            raise ValueError('保存済みのページ参照が不正')
    return value


def page_paths(out, row):
    run = out/row['run']
    if run.resolve() != run or not run.is_relative_to(out):
        raise ValueError('ページの実行先はバッチ内に置く')
    return run, run.parent/'config.json'


def run_page(out, value, row, config, audit_page):
    run, path = page_paths(out, row)
    if run.is_dir() and any(run.iterdir()):
        if row['status'] != 'interrupted':
            raise ValueError('未実行のページの保存先に既存ファイルがある')
        if not (run/'run.json').is_file():
            row.setdefault('previous_runs', []).append(row['run'])
            row['attempt'] += 1
            row['run'] = run_ref(row['id'], row['attempt'])
            run, path = page_paths(out, row)
            if run.exists():
                raise ValueError('ページの再試行先が既に存在する')
    page_config = deepcopy(config)
    page_config['scope'].update(pages=[row['url']], max_pages=1)
    if path.exists():
        if path.resolve() != path or audit.load(path) != page_config:
            raise ValueError('保存済みのページ設定が変更された')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        save_json_atomic(path, page_config)
    if auth_digest(config) != value['inputs']['auth_state_sha256']:
        raise ValueError('認証状態が変更された')
    command = ['page-audit', '--url', row['url'], '--config', str(path), '--out', str(run)]
    if (run/'run.json').is_file():
        command.append('--resume')
    row['status'] = 'interrupted'
    row.pop('reason', None)
    save_manifest(out, value)
    stdout, stderr = StringIO(), StringIO()
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = audit_page(command)
    except KeyboardInterrupt:
        row['reason'] = '操作を中断した。同じ設定で再開できる。'
        save_manifest(out, value)
        return 130
    if result not in (0, 2):
        row['reason'] = stderr.getvalue().strip() or 'ページ検査を終了できなかった。'
        save_manifest(out, value)
        return result

    payload = json.loads(stdout.getvalue().splitlines()[-1])
    if result == 2:
        reasons = payload.get('exploration') or [payload['error']]
        row.update(status='failed', reason=' / '.join(reasons))
    else:
        reports = {}
        for name in ('html', 'json', 'excel'):
            artifact = Path(payload[name]).resolve()
            if not artifact.is_file() or not artifact.is_relative_to(run):
                raise ValueError('保存したページ別報告の参照が不正')
            reports[name] = artifact.relative_to(out).as_posix()
        report = audit.load(out/reports['json'])
        if report['url'] != row['url'] or report['verification']['mode'] != 'machine':
            raise ValueError('ページ別報告のURL又はモードが一致しない')
        row.update(status='completed', reports=reports, pending_routes=payload['pending_routes'],
                   collection_complete=report['collection_complete'], exploration_complete=report['exploration']['complete'],
                   audit_complete=report['audit_complete'], scope_confirmed=report['scope_confirmed'],
                   wcag_counts=report['counts'])
    save_manifest(out, value)
    return 0


def run(config_path, out, *, resume, limit, audit_page):
    if limit is not None and limit < 1:
        raise ValueError('max-pages-this-runは1以上の整数を指定する')
    config, config_hash = batch_config(Path(config_path))
    inputs = {'config_sha256': config_hash, 'effective_config_digest': audit.digest(config),
              'auth_state_sha256': auth_digest(config), 'implementation_digest': implementation_digest()}
    out = Path(out).resolve()
    if not resume:
        out.mkdir(parents=True, exist_ok=True)
    with run_lock(out):
        value = prepare(out, configured_urls(config), inputs, resume)
        remaining = [row for row in value['pages'] if row['status'] in {'pending', 'interrupted'}]
        for row in remaining[:limit]:
            code = run_page(out, value, row, config, audit_page)
            if code != 0:
                break
        else:
            code = 0
    summary = {'file': str(out/MANIFEST), 'counts': value['counts'],
               'all_pages_attempted': value['all_pages_attempted']}
    return code, summary
