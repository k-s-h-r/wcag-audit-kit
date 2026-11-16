"""Atomic progress journal for interrupted browser collection."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit


def save_json_atomic(path, value):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.' + path.name + '-', suffix='.tmp', delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class CollectionCheckpoint:
    def __init__(self, config, run, manifest, queue, seen, known, in_scope):
        self.config = config
        self.path = Path(run) / 'capture-manifest.json'
        if self.path.exists():
            raise ValueError('収集済みのmanifestを上書きしない。新しいrun又はprobeを使う')
        self.manifest = manifest
        self.queue = queue
        self.seen = seen
        self.known = known
        self.in_scope = in_scope

    def save(self):
        value = self.manifest
        value['checkpoint_at'] = datetime.now(timezone.utc).isoformat()
        value['discovered'] = sorted(self.known)
        value['unvisited'] = [url for url in self.queue if url not in self.seen and self.in_scope(url, self.config)]
        value['declared_states_without_page'] = [state['id'] for state in self.config.get('states', [])
            if not any(urlsplit(page['url']).path in state['paths'] for page in value['pages'])]
        value['linked_pages_exhausted'] = value['collector_status'] == 'completed' and not value['unvisited']
        value['site_inventory_confirmed'] = False
        value['scope_note'] = 'リンクをたどった範囲のみ。未リンクURL・権限別画面・未知の状態の調査は別に必要'
        save_json_atomic(self.path, value)

    def __enter__(self):
        self.manifest['collector_status'] = 'running'
        self.save()
        return self

    def __exit__(self, kind, error, traceback):
        self.manifest['collector_status'] = 'interrupted' if kind is not None else 'completed'
        if error is not None:
            self.manifest['collector_error'] = str(error)
        self.save()
