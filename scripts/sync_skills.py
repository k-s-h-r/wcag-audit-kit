#!/usr/bin/env python3
"""Synchronize committed runtime resources. This is a maintainer tool, not installation."""
import argparse
import shutil
from skill_layout import ROOT, SKILLS, CANONICAL, DIRECTORIES, resource_files


def synchronize(check=False):
    expected = set(resource_files())
    differences = []
    for name in SKILLS[1:]:
        destination = ROOT / 'skills' / name
        actual = {path.relative_to(destination) for directory in DIRECTORIES
                  for path in (destination / directory).rglob('*')
                  if path.is_file() and '__pycache__' not in path.parts and path.suffix not in {'.pyc', '.tmp'}}
        for relative in sorted(expected | actual):
            source, target = CANONICAL / relative, destination / relative
            if relative not in expected:
                differences.append(f'{name}/{relative}: unexpected resource')
                if not check:
                    target.unlink()
            elif not target.is_file() or source.read_bytes() != target.read_bytes():
                differences.append(f'{name}/{relative}: missing or different')
                if not check:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='report differences without writing')
    args = parser.parse_args()
    differences = synchronize(args.check)
    for difference in differences:
        print(difference)
    if args.check and differences:
        return 1
    print('Skill resources are synchronized.' if args.check else 'Updated committed skill resources.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
