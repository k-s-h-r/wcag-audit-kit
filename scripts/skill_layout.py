"""Repository paths for development tools; installed skills do not import this."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ('wcag-audit-kit', 'wcag-pages', 'wcag-page', 'wcag-report')
CANONICAL = ROOT / 'skills' / 'wcag-audit-kit'
DIRECTORIES = ('scripts', 'references', 'assets', 'vendor')
FILES = ('requirements.txt', 'requirements-analysis.txt', 'package.json', 'package-lock.json')


def resource_files():
    for directory in DIRECTORIES:
        for path in sorted((CANONICAL / directory).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix not in {'.pyc', '.tmp'}:
                yield path.relative_to(CANONICAL)
    yield from map(Path, FILES)
