"""Optional native Orca replay of two unchanged local 4.1.3 save fixtures."""

import argparse
from functools import partial
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
from threading import Thread


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmarks.native_status import capture


PAGES = ('p04.html', 'p03.html')
ENVIRONMENT_FIELDS = ('system', 'kernel', 'reader', 'reader_version', 'browser_version', 'audio_output')
SAVE_LABEL = '保存する'
SAVED_TEXT = '保存しました'


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def observe(area, root, url, source):
    area.mkdir()
    request = {
        'case_id': source.name,
        'url': url,
        'locale': 'ja-JP',
        'settle_ms': 3000,
        'actions': [{'type': 'reader.press', 'keys': [key]} for key in ('Tab', 'space')],
        'observe': [{'selector': '#subject'}],
    }
    request_path = area / 'request.json'
    request_path.write_text(json.dumps(request, ensure_ascii=False), encoding='utf-8')
    capture(root, area)
    receipt = area / 'speech/screen-reader.json'
    result = {
        'fixture_sha256': sha256(source.read_bytes()).hexdigest(),
        'valid': False,
        'announcement_observed': None,
    }
    if not receipt.is_file():
        return dict(result, reason='The native adapter did not write a receipt.')
    observed = json.loads(receipt.read_text(encoding='utf-8'))
    environment = observed['environment']
    rows = observed['observations']
    result.update(receipt=receipt.relative_to(area.parent).as_posix(),
                  adapter_status=observed['status'], environment={k: environment.get(k) for k in ENVIRONMENT_FIELDS})
    if (observed['status'] != 'collected' or environment.get('reader') != 'Orca'
            or environment.get('simulation') is not False or environment.get('installation_verified') is not True
            or observed.get('request_sha256') != sha256(request_path.read_bytes()).hexdigest()
            or [step['action'] for step in rows] != request['actions'] or any(step['url'] != url for step in rows)):
        return dict(result, reason=observed.get('error') or 'The native speech observation did not complete.')
    speech = [[utterance['phrase'] for utterance in step['speech']] for step in rows]
    texts = [
        [item['text'] for item in step['observations'] if item.get('target', {}).get('selector') == '#subject']
        for step in rows
    ]
    focused = all(
        step['focus_after'].get('id') == 'save' and step['focus_after'].get('documentHasFocus') is True
        for step in rows
    )
    valid = focused and texts == [['待機中'], [SAVED_TEXT]] and SAVE_LABEL in ''.join(speech[0])
    return dict(result, valid=valid, visible_text=texts, speech=speech, focus_on_save=focused,
                announcement_observed=(SAVED_TEXT in ''.join(speech[1])) if valid else None)


def run(root, out):
    out.mkdir(parents=True, exist_ok=False)
    public = out / 'public'
    public.mkdir()
    for name in PAGES:
        shutil.copyfile(ROOT / 'benchmarks/cases/4.1.3/public' / name, public / name)
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=public)) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            observations = {
                name: observe(out / name.removesuffix('.html'), root,
                              f'http://127.0.0.1:{server.server_port}/{name}', public / name)
                for name in PAGES
            }
        finally:
            server.shutdown()
            thread.join()
    positive, negative = (observations[name] for name in PAGES)
    reproduced = (positive['valid'] and negative['valid'] and positive['environment'] == negative['environment']
                  and positive['announcement_observed'] is True and negative['announcement_observed'] is False)
    result = {
        'status': 'reproduced' if reproduced else 'inconclusive',
        'observations': observations,
        'scope': 'Native Orca speech-dispatch log during the observation windows',
        'wcag_judgement': None,
    }
    path = out / 'observed.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'evidence': str(path)}))
    return 0 if reproduced else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path, help='prepared private Debian Orca and Xvfb package root')
    parser.add_argument('--out', required=True, type=Path, help='new evidence directory')
    arguments = parser.parse_args()
    sys.exit(run(arguments.root, arguments.out))
