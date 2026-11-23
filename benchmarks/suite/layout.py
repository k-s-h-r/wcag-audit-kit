"""Keep saved benchmarks usable across the audited directory-only migration."""
import json
from pathlib import Path


PATH = Path(__file__).with_name('layout_versions.json')


def previous_digests(kind, fingerprint):
    version = json.loads(PATH.read_text(encoding='utf-8'))[kind]
    return version['before'] if version['after'] == fingerprint else ()


def scorer_digest(kind, fingerprint):
    previous = previous_digests(kind, fingerprint)
    return previous[0] if previous else fingerprint
