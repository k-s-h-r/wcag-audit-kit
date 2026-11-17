"""Install the committed folders by copying, without build tools or a Git checkout."""
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import yaml
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'skills/wcag-audit-kit/scripts'))
import audit
import skill_layout
import sync_skills
import test_ledger as fixture


class LayoutTest(unittest.TestCase):
    def test_committed_resources_are_synchronized(self):
        self.assertEqual(sync_skills.synchronize(check=True), [])
        self.assertFalse((ROOT / 'SKILL.md').exists())
        for name in skill_layout.SKILLS:
            folder = ROOT / 'skills' / name
            self.assertIn(f'name: {name}', (folder / 'SKILL.md').read_text())
            self.assertFalse(any(folder.rglob('build_*.py')))
            self.assertFalse(any(p.is_symlink() for p in folder.rglob('*')))

    def test_check_detects_missing_changed_and_unexpected_files_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            canonical = root / 'skills/wcag-audit-kit'
            (canonical / 'scripts').mkdir(parents=True)
            (canonical / 'scripts/helper.py').write_text('original')
            for name in skill_layout.SKILLS[1:]:
                folder = root / 'skills' / name
                (folder / 'scripts').mkdir(parents=True)
                (folder / 'SKILL.md').write_text(name)
                (folder / 'agents').mkdir()
                (folder / 'agents/openai.yaml').write_text('interface:\n  display_name: ' + name + '\n')
            (root / 'skills/wcag-page/scripts/helper.py').write_text('changed')
            extra = root / 'skills/wcag-report/scripts/obsolete.py'
            extra.write_text('obsolete')
            def state():
                return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with patch.multiple(sync_skills, ROOT=root, CANONICAL=canonical), patch.object(
                    sync_skills, 'resource_files', return_value=[Path('scripts/helper.py')]):
                before = state()
                differences = sync_skills.synchronize(check=True)
                self.assertEqual(len(differences), 4)
                self.assertEqual(state(), before)
                sync_skills.synchronize()
                self.assertFalse(extra.exists())
                self.assertEqual(sync_skills.synchronize(check=True), [])
                for name in skill_layout.SKILLS[1:]:
                    self.assertEqual((root / 'skills' / name / 'SKILL.md').read_text(), name)
                    self.assertEqual(audit.load(root / 'skills' / name / 'agents/openai.yaml'),
                                     {'interface': {'display_name': name}})

    def test_local_markdown_links_resolve_without_repository_resources(self):
        for name in skill_layout.SKILLS:
            folder = ROOT / 'skills' / name
            for document in [folder / 'SKILL.md', *(folder / 'references').glob('*.md')]:
                text = re.sub(r'```.*?```', '', document.read_text(), flags=re.S)
                for link in re.findall(r'\]\(([^\s)]+)\)', text):
                    url = urlsplit(link)
                    if url.scheme or url.netloc or not url.path:
                        continue
                    target = (document.parent / unquote(url.path)).resolve()
                    self.assertTrue(target.is_relative_to(ROOT / 'skills'), (document, link))
                    self.assertTrue(target.exists(), (document, link))

    def test_each_skill_runs_and_exports_after_copying_outside_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            working = base / 'unrelated-working-directory'
            working.mkdir()
            for name in skill_layout.SKILLS:
                with self.subTest(skill=name):
                    folder = base / name
                    shutil.copytree(ROOT / 'skills' / name, folder,
                                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                    policy = audit.load(folder / 'agents/openai.yaml')
                    self.assertIs(policy['policy']['allow_implicit_invocation'], False)
                    frontmatter = yaml.safe_load((folder / 'SKILL.md').read_text().split('---', 2)[1])
                    self.assertIs(frontmatter['disable-model-invocation'], True)
                    cli = folder / 'scripts/audit.py'
                    def command(*args, expected=0):
                        result = subprocess.run([sys.executable, str(cli), *map(str, args)],
                                                cwd=working, capture_output=True, text=True, timeout=30)
                        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                        return result
                    help_result = command('page-audit', '--help')
                    self.assertIn('--mode', help_result.stdout)
                    config = base / (name + '-config.json')
                    command('init', '--url', 'https://example.test/contact', '--config', config, '--mode', 'ai')
                    value = audit.load(config)
                    value['scope'].update(mode='configured', pages=['https://example.test/contact'])
                    audit.save(config, value)
                    pages = base / (name + '-pages.json')
                    command('pages', '--config', config, '--out', pages)
                    self.assertIn('https://example.test/contact', pages.read_text())
                    ledger = fixture.LedgerTest()
                    ledger.setUp()
                    try:
                        run = base / (name + '-run')
                        shutil.copytree(ledger.run, run)
                        command('report', '--run', run, '--strict', expected=2)
                        report = audit.load(run / 'report.json')
                        self.assertFalse(report['audit_complete'])
                        self.assertEqual(report['counts']['not_run'], 55)
                        workbook = base / (name + '-report.xlsx')
                        command('excel', 'export', '--run', run, '--mode', 'report', '--out', workbook)
                        from openpyxl import load_workbook
                        with workbook.open('rb') as stream:
                            book = load_workbook(stream, read_only=True)
                            self.assertEqual(book.active.title, 'チェックシート')
                            self.assertEqual(book['検査票'].max_row, 56)
                            book.close()
                    finally:
                        ledger.tearDown()
                    expected_source = skill_layout.CANONICAL / 'references/sources/wcag22.html'
                    self.assertEqual(hashlib.sha256((folder / 'references/sources/wcag22.html').read_bytes()).digest(),
                                     hashlib.sha256(expected_source.read_bytes()).digest())


if __name__ == '__main__':
    unittest.main()
