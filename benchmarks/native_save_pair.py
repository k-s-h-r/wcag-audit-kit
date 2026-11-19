"""Grade a bounded status-message contrast after an opt-in Orca replay."""
from datetime import datetime
from pathlib import Path
import re
from unicodedata import normalize
from urllib.parse import urlsplit
import uuid

from . import core, runner, status_capture

CHECKPOINT = '4.1.3-02'
RECORD_PAGES = {'p01.html', 'p02.html'}
RECORD_ACTION = {'type': 'click', 'selector': '#record'}
ENVIRONMENT = ('system', 'kernel', 'reader', 'reader_version', 'debian_package',
               'browser', 'browser_version', 'backend', 'audio_output', 'debug_capture')


def request_for(job, page, plan, *, record_pair=False):
    preparation = [{'type': 'reader.press', 'keys': ['Tab']}]
    if record_pair:
        preparation = [
            {'type': 'browser.click', 'selector': 'h1'},
            {'type': 'reader.press', 'keys': ['Escape']},
            {'type': 'browser.press', 'key': 'Tab'},
            {'type': 'reader.press', 'keys': ['KP_Enter']},
        ]
    return {
        'case_id': job['id'], 'url': job['urls'][page], 'locale': 'ja-JP', 'settle_ms': 3000,
        'actions': [*preparation, {'type': 'reader.press', 'keys': ['space']}],
        'observe': [{'selector': plan['action']['selector']},
                    {'selector': plan['target'], 'attributes': ['role', 'aria-live', 'aria-atomic']}],
    }


def phrase_text(value):
    return re.sub(r'\s+', '', normalize('NFKC', value)).rstrip('.。').casefold()


def record_button_speech(utterances, button):
    if not utterances or utterances[0] not in {'enter', 'エンター'}:
        return False
    return any(utterances[1:] in ([button, role], [button + role]) for role in ('button', 'ボタン'))


def check_receipt(request, request_hash, receipt, log, log_hash, *, record_pair=False):
    """Re-index the adapter's private output. Application text only chooses what to look for."""
    from orca_log import speech_in_window

    try:
        environment = receipt['environment']
        cleanup = receipt['cleanup']
        if (receipt['status'] != 'collected' or receipt['case_id'] != request['case_id']
                or receipt['scenario'] != request or receipt['request_sha256'] != request_hash
                or cleanup['debug_log_sha256'] != log_hash or cleanup['pty_error'] is not None
                or environment['reader'] != 'Orca' or environment['browser'] != 'Chromium'
                or environment['simulation'] is not False or environment['installation_verified'] is not True
                or any(not isinstance(environment[key], str) or not environment[key] for key in ENVIRONMENT)):
            return None
        start, end = (datetime.fromisoformat(receipt[key]) for key in ('started_at', 'finished_at'))
        rows = receipt['observations']
        if len(rows) != (5 if record_pair else 2):
            return None
        trigger, status = request['observe']
        focused = {'tag': 'button', 'id': trigger['selector'][1:], 'documentHasFocus': True}
        body = {'tag': 'body', 'id': '', 'documentHasFocus': True}
        expected_focus = [body, body, focused, focused, focused] if record_pair else [focused, focused]
        phases = []
        for index, (row, action, focus) in enumerate(zip(rows, request['actions'], expected_focus, strict=True), 1):
            if (row['index'] != index or row['action'] != action or row['url'] != request['url']
                    or row['focus_after'] != focus
                    or (index > 1 and row['focus_before'] != expected_focus[index-2])
                    or row['focus_before']['documentHasFocus'] is not True):
                return None
            first, last = (datetime.fromisoformat(row[key]) for key in ('started_at', 'finished_at'))
            if not start <= first < last <= end or (last-first).total_seconds() < request['settle_ms'] / 1000:
                return None
            start = last
            speech = speech_in_window(log, row['started_at'], row['finished_at'])
            if speech != row['speech']:
                return None
            button_row, status_row = row['observations']
            if button_row['target'] != trigger or status_row['target'] != status:
                return None
            attributes = status_row['attributes']
            if (set(attributes) != {'role', 'aria-live', 'aria-atomic'}
                    or attributes['role'] not in (None, 'status')
                    or attributes['aria-live'] is not None or attributes['aria-atomic'] is not None):
                return None
            phases.append((phrase_text(button_row['text']), phrase_text(status_row['text']),
                           attributes['role'], [phrase_text(entry['phrase']) for entry in speech]))
        button, before, role, first_speech = phases[0]
        _, after, _, last_speech = phases[-1]
        if (not button or not after or before == after or any(
                name != button or current_role != role for name, _, current_role, _ in phases)):
            return None
        if record_pair:
            if (any(text or after in speech for _, text, _, speech in phases[:-1])
                    or not record_button_speech(phases[-2][3], button)):
                return None
        elif (not before or not any(utterance in {button + 'button', button + 'ボタン'} for utterance in first_speech)
              or after in first_speech):
            return None
        return {'environment': {key: environment[key] for key in ENVIRONMENT}, 'button': button,
                'before': before, 'after': after, 'role': role, 'activation_speech': last_speech}
    except (KeyError, TypeError, ValueError, AttributeError, SyntaxError):
        return None


def calibrate(observations, *, record_pair=False):
    """Both pages must form one matched pair before classifying the silent page."""
    if len(observations) != 2 or any(value is None for value in observations):
        return ['cant_tell'] * len(observations)
    if {value['role'] for value in observations} != {None, 'status'}:
        return ['cant_tell'] * 2
    a, b = observations
    if any(a[key] != b[key] for key in ('environment', 'button', 'before', 'after')):
        return ['cant_tell'] * 2
    positive, negative = sorted(observations, key=lambda value: value['role'] is None)
    key_echo = {'space', 'スペース'}
    positive_words = positive['activation_speech']
    if record_pair and (len(positive_words) != 2 or positive_words[0] not in key_echo):
        return ['cant_tell'] * 2
    if ([word for word in positive['activation_speech'] if word not in key_echo] != [positive['after']]
            or len(negative['activation_speech']) != 1 or negative['activation_speech'][0] not in key_echo):
        return ['cant_tell'] * 2
    return ['passed' if value['role'] == 'status' else 'failed' for value in observations]


def public_inputs(run, *, record_pair=False):
    proof = core.load(run/'integrity.json')['files']
    for name, expected in proof.items():
        if (name == 'run.json' or name.startswith('worker/')) and core.file_hash(core.local(run, name)) != expected:
            raise ValueError('検査担当向けのページ・タスクが変更された')
    if not {'run.json', 'worker/tasks.json'} <= proof.keys():
        raise ValueError('公開作業票の保存済み証拠がない')
    metadata = core.load(run/'run.json')
    tasks = core.load(run/'worker/tasks.json')
    if (any(metadata[key] != tasks[key] for key in ('run_id', 'corpus_digest'))
            or metadata['implementation_digest'] != runner.implementation_digest()):
        raise ValueError('現在の実装で作った新しい問題集runを指定する')
    modes = {mode for mode in metadata['modes'] if core.modes.MODES[mode]['screen_reader']}
    groups = {mode: [] for mode in modes}
    for job in tasks['jobs']:
        if job['criterion'] != '4.1.3' or job['mode'] not in modes or CHECKPOINT not in job['checkpoints']:
            continue
        if record_pair:
            if len(job['pages']) != 1 or job['pages'][0] not in RECORD_PAGES:
                continue
            page, = job['pages']
            if (job['checkpoints'] != [CHECKPOINT] or len(job['states']) != 1
                    or job['states'][0]['id'] != 'after-activate' or job['states'][0].get('actions') != [RECORD_ACTION]):
                raise ValueError('記録通知の試験は公開作業票の固定した操作を使う')
            state, plan = 'after-activate', {'action': RECORD_ACTION, 'target': '#notice'}
        else:
            if '4.1.3-01' not in job['checkpoints'] or not any('status_capture' in state for state in job['states']):
                continue
            page, = job['pages']
            (state, plan), = status_capture.plans(job['criterion'], job['checkpoints'], job['states']).items()
        source = f'worker/public/4.1.3/{page}'
        if source not in proof or not status_capture.fixture_url(job['urls'][page], page):
            raise ValueError('状態通知の試験は固定したローカルの公開ページを使う')
        groups[job['mode']].append((job, page, state, plan, source))
    if not groups or any(len(rows) != 2 or rows[0][1] == rows[1][1] or rows[0][2:4] != rows[1][2:4]
                         for rows in groups.values()):
        raise ValueError('同じ操作と観測対象を指定した2つの対照例が必要')
    ports = {urlsplit(job['urls'][page]).port for rows in groups.values() for job, page, *_ in rows}
    port, = ports
    if port != metadata['port']:
        raise ValueError('公開作業票の配信ポートが一致しない')
    return tasks, groups, port, proof


def read_observation(request, area, *, record_pair=False):
    request_path = area/'request.json'
    receipt_path = area/'speech/screen-reader.json'
    log_path = area/'speech/orca-debug.log'
    try:
        return check_receipt(request, core.file_hash(request_path), core.load(receipt_path),
                             log_path.read_text(errors='replace'), core.file_hash(log_path), record_pair=record_pair)
    except (OSError, ValueError, UnicodeError):
        return None


def replay(run, root, capture, import_results, *, record_pair=False):
    run = Path(run).resolve()
    tasks, groups, port, frozen = public_inputs(run, record_pair=record_pair)
    pair_name = 'record' if record_pair else 'save'
    claim = run/f'native-{pair_name}-pair'
    if any((run/name).exists() for name in ('review-index.json', 'native-save-pair', 'native-record-pair')):
        raise ValueError('状態通知を試すには、取り込み前の新しいrunを使う')
    http = runner.server(run/'worker/public', port)
    try:
        claim.mkdir()
        outputs = []
        for mode in sorted(groups):
            paired = []
            for job, page, state, plan, source in groups[mode]:
                area = run/'attachments'/job['id']/f'native-{pair_name}-{uuid.uuid4().hex[:12]}'
                area.mkdir(parents=True)
                request = request_for(job, page, plan, record_pair=record_pair)
                request_path = area/'request.json'
                core.save(request_path, request)
                capture(root, area)
                observation = read_observation(request, area, record_pair=record_pair)
                paired.append((job, page, state, plan, source, area, observation))
            outcomes = calibrate([row[-1] for row in paired], record_pair=record_pair)
            evidence = []
            for job, page, state, plan, source, area, observation in paired:
                paths = [p for p in (area/'request.json', area/'speech/screen-reader.json',
                                     area/'speech/orca-debug.log') if p.is_file()]
                evidence.append(dict(job_id=job['id'], fixture=source, fixture_sha256=frozen[source],
                                     observation=observation, files={p.relative_to(run).as_posix(): core.file_hash(p) for p in paths}))
            created = []
            for (job, page, state, plan, _, area, _), outcome in zip(paired, outcomes, strict=True):
                control = area/'paired-control.json'
                core.save(control, dict(run_id=tasks['run_id'], mode=mode, state=state, pair=evidence))
                paths = [p.relative_to(run).as_posix() for p in (area/'speech/screen-reader.json',
                         area/'speech/orca-debug.log', control) if p.is_file()]
                prediction = dict(schema_version='1', run_id=tasks['run_id'], corpus_digest=tasks['corpus_digest'],
                                  job_id=job['id'], observations=[dict(page=page, state=state, target=plan['target'],
                                  checkpoint=CHECKPOINT, outcome=outcome, method='screen-reader', evidence=paths,
                                  observed={'passed':'同じ対象の更新をOrcaの操作後の発話で確認した。',
                                            'failed':'同じ環境の対照は発話し、この操作ではキーの発話だけだった。',
                                            'cant_tell':'操作後の発話と対照を同じ条件で確認できなかった。'}[outcome])])
                core.save(area/'prediction.json', prediction)
                outputs.append((area, prediction, outcome))
                created.extend(path for path in area.rglob('*') if path.is_file())
            core.freeze(run, created)
        if import_results:
            for _, prediction, _ in outputs:
                core.record_review(run, prediction)
        return [dict(job_id=value['job_id'], outcome=outcome, prediction=str(area/'prediction.json'))
                for area, value, outcome in outputs]
    finally:
        http.shutdown()
        http.server_close()
