import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collection_checkpoint import CollectionCheckpoint, save_json_atomic


class CollectionCheckpointTest(unittest.TestCase):
    def test_failed_replace_leaves_last_valid_journal_and_no_partial_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'capture-manifest.json'
            save_json_atomic(path, {'captures': ['finished']})
            before = path.read_bytes()
            with patch('collection_checkpoint.os.replace', side_effect=OSError('interrupted write')):
                with self.assertRaises(OSError):
                    save_json_atomic(path, {'captures': ['finished', 'running']})
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual([p.name for p in Path(directory).iterdir()], [path.name])

    def test_interrupted_capture_is_preserved_and_queue_is_not_exhausted(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = {'pages': [{'url': 'https://example.com/a'}], 'captures': []}
            queue = ['https://example.com/b']
            config = {'states': [{'id': 'expanded', 'paths': ['/b']}]}
            with self.assertRaises(RuntimeError):
                with CollectionCheckpoint(config, directory, manifest, queue, set(), set(queue),
                                           lambda url, config: True) as checkpoint:
                    manifest['captures'].append({'key': 'a', 'execution': 'completed'})
                    checkpoint.save()
                    manifest['captures'].append({'key': 'a-expanded', 'execution': 'blocked', 'collection_state': 'running'})
                    checkpoint.save()
                    raise RuntimeError('simulated shutdown')
            saved = json.loads((Path(directory) / 'capture-manifest.json').read_text())
            self.assertEqual(saved['collector_status'], 'interrupted')
            self.assertEqual(len(saved['captures']), 2)
            self.assertEqual(saved['unvisited'], queue)
            self.assertFalse(saved['linked_pages_exhausted'])
            self.assertEqual(saved['declared_states_without_page'], ['expanded'])
            with self.assertRaises(ValueError):
                CollectionCheckpoint(config, directory, manifest, queue, set(), set(), lambda *args: True)


if __name__ == '__main__':
    unittest.main()
