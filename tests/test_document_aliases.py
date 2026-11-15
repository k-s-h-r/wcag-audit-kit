from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit
from browser_capture import normalize


class DocumentAliasesTest(unittest.TestCase):
    def test_default_keeps_hash_router_and_query_states(self):
        for url in ['https://example.test/app#/checkout','https://example.test/app?view=one#main']:
            self.assertEqual(normalize(url),url)

    def test_only_reviewed_literal_fragments_are_aliases(self):
        config={'scope':{'same_document_fragments':['main']}}
        self.assertEqual(normalize('https://example.test/app?view=one#main',config),'https://example.test/app?view=one')
        self.assertEqual(normalize('https://example.test/app#/checkout',config),'https://example.test/app#/checkout')

    def test_aliases_need_a_recorded_basis(self):
        config=audit.init_config('https://example.test')
        config['scope']['same_document_fragments']=['main']
        with self.assertRaisesRegex(ValueError,'調査根拠'):audit.validate_config(config)
        config['scope']['same_document_fragment_reason']='実際のソースとリンクを確認し、mainは静的な主領域へのアンカーだけである。'
        audit.validate_config(config)


if __name__=='__main__':unittest.main()
