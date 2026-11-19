"""Reference equivalent axe contrast observations from independently captured pages."""

from hashlib import sha256
import json
from pathlib import Path

from audit import load, run_meta
from browser_capture import page_id
from page_batch import MANIFEST, STATUSES, page_paths, run_ref
from run_layout import ledger


RULE = 'color-contrast'


def verified_json(run, path, proof):
    source = run / path
    if source.resolve() != source or not source.is_relative_to(run):
        raise ValueError('証拠ファイルがページのrun外を参照している')
    raw = source.read_bytes()
    checksum = sha256(raw).hexdigest()
    if [item['sha256'] for item in proof if item['path'] == path.as_posix()] != [checksum]:
        raise ValueError(f'証拠ファイルのハッシュを照合できない: {path.as_posix()}')
    return json.loads(raw), checksum


def initial_evidence(batch, row, environment):
    package, _ = page_paths(batch, row)
    run = ledger(package)
    if run.resolve() != run or any((run / name).resolve() != run / name for name in ('run.json', 'capture-manifest.json', 'exploration.json')):
        raise ValueError('収集記録がページのrun外を参照している')
    meta = run_meta(run)
    config = meta['config']
    if (config['verification']['mode'] != 'machine' or config['scope']['mode'] != 'configured'
            or config['scope']['pages'] != [row['url']]):
        raise ValueError('ページの実行範囲がバッチのURLと一致しない')
    settings = [env for env in config['environments'] if env['id'] == environment]
    if len(settings) != 1:
        raise ValueError('指定した環境の記録を照合できない')
    captures = load(run / 'capture-manifest.json')['captures']
    key = f"{row['id']}--initial--{environment}"
    matches = [item for item in captures if item['key'] == key]
    if len(matches) != 1:
        raise ValueError('指定した環境の初期表示の収集記録が一つに定まらない')
    capture = matches[0]
    expected = (row['url'], row['id'], 'initial', environment, 'completed', 'finished')
    if tuple(capture[field] for field in ('url', 'page_id', 'state', 'environment', 'execution', 'collection_state')) != expected:
        raise ValueError('初期表示の収集記録が対象URL・環境と一致しない')
    graph = load(run / 'exploration.json')
    if graph['config_digest'] != meta['config_digest']:
        raise ValueError('探索とページの実行設定を照合できない')
    if graph.get('running'):
        raise ValueError('ページの探索が進行中又は中断中')
    evidence = Path(capture['evidence_dir'])
    transition, _ = verified_json(run, evidence / 'transition.json', graph['proof'])
    if (transition['environment'] != environment or transition['route'] != [] or transition['error']
            or transition['blocked_requests'] or transition['native_events'] or not transition['settling']
            or any(wait['status'] != 'quiet' for wait in transition['settling'])):
        raise ValueError('制限や中断のない初期表示を照合できない')
    path = evidence / 'axe.json'
    axe, checksum = verified_json(run, path, graph['proof'])
    if axe['url'] != row['url']:
        raise ValueError('axeの測定URLがバッチのURLと一致しない')
    context = {field: axe[field] for field in ('testEngine', 'testRunner', 'testEnvironment', 'toolOptions')}
    context['capture_environment'] = settings[0]
    context['locale'] = config.get('locale', 'ja-JP')
    receipt = {'capture': key, 'evidence': (run / path).relative_to(batch).as_posix(), 'sha256': checksum}
    return axe, context, receipt


def measured_node(axe, target):
    matches = [(bucket, node) for bucket in ('passes', 'violations', 'incomplete')
               for rule in axe[bucket] if rule['id'] == RULE
               for node in rule['nodes'] if node['target'] == [target]]
    if len(matches) != 1:
        raise ValueError('指定した対象の色コントラスト測定が一つに定まらない')
    bucket, node = matches[0]
    data = [check['data'] for check in node['any'] if check['id'] == RULE]
    if bucket == 'incomplete' or len(data) != 1 or not isinstance(data[0], dict):
        raise ValueError('指定した対象の色コントラストは測定不能')
    measure = data[0]
    ratio = measure.get('contrastRatio')
    if (type(ratio) not in (int, float) or not 1 <= ratio <= 21
            or not all(measure.get(key) for key in ('fgColor', 'bgColor', 'fontSize', 'fontWeight', 'expectedContrastRatio'))
            or 'shadowColor' not in measure):
        raise ValueError('指定した対象の測定値又は測定条件が不足している')
    return {'bucket': bucket, 'node': node}


def compare(batch_dir, *, target: str, environment: str) -> dict:
    """Group equal measurements from one environment, keeping every page receipt."""
    if not target.strip() or not environment.strip():
        raise ValueError('axeの対象文字列と環境IDを指定する')
    batch = Path(batch_dir).resolve()
    path = batch / MANIFEST
    if path.resolve() != path:
        raise ValueError('バッチ台帳がバッチの保存先外を参照している')
    manifest = load(path)
    if (not isinstance(manifest, dict) or not isinstance(manifest.get('pages'), list)
            or tuple(manifest.get(field) for field in ('schema_version', 'kind', 'mode')) != ('1', 'page-batch', 'machine')):
        raise ValueError('指定URLの機械検査バッチを指定する')

    groups = {}
    unavailable = []
    for row in manifest['pages']:
        if not isinstance(row, dict) or not isinstance(row.get('url'), str) or row.get('status') not in STATUSES:
            raise ValueError('バッチのページ又は処理状況が不正')
        page = {'url': row['url'], 'status': row['status']}
        if row['status'] != 'completed':
            unavailable.append({**page, 'reason': row.get('reason', 'ページの検査が完了していない')})
            continue
        try:
            if (row['id'] != page_id(row['url']) or type(row['attempt']) is not int or row['attempt'] < 1
                    or row['run'] != run_ref(row['id'], row['attempt'])):
                raise ValueError('バッチのページ参照が不正')
            axe, context, receipt = initial_evidence(batch, row, environment)
            page.update(receipt)
            observation = measured_node(axe, target)
            value = {'context': context, 'observation': observation}
            key = json.dumps(value, sort_keys=True, allow_nan=False)
        except (AttributeError, KeyError, OSError, TypeError, ValueError) as exc:
            unavailable.append({**page, 'reason': str(exc)})
            continue
        group = groups.setdefault(key, {**value, 'pages': []})
        group['pages'].append(page)
    return {'rule': RULE, 'target': target, 'environment': environment, 'state': 'initial',
            'groups': list(groups.values()), 'unavailable': unavailable,
            'notice': '各ページで取得したaxeの測定値を参照する。WCAGの適合判定や他の状態の確認は含まない。'}
