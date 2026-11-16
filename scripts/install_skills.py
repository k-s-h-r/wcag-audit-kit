#!/usr/bin/env python3
"""Build self-contained skill directories from one shared source tree."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[1]
ROLES={'wcag-audit-kit':Path('SKILL.md'),
       **{name:Path('skills')/name/'SKILL.md' for name in ['wcag-pages','wcag-page','wcag-report']}}


def source_ref():
    result=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True)
    return result.stdout.strip() if result.returncode==0 else 'main'


def rewrite_markdown(body, source, destination, selected, ref):
    by_path={str((ROOT/path).resolve()):name for name,path in ROLES.items()}
    def replace(match):
        raw=match.group(1);parts=urlsplit(raw)
        if parts.scheme or parts.netloc or not parts.path:return match.group(0)
        target=(source.parent/unquote(parts.path)).resolve()
        if not target.is_relative_to(ROOT):return match.group(0)
        relative=target.relative_to(ROOT)
        if str(target) in by_path:
            role=by_path[str(target)]
            rewritten=os.path.relpath(Path('..')/role/'SKILL.md',destination.parent).replace(os.sep,'/') if role in selected else f'https://github.com/k-s-h-r/wcag-audit-kit/blob/{ref}/{relative.as_posix()}'
        elif relative.parts and (relative.parts[0] in {'scripts','references','assets','vendor'} or relative.name.startswith('requirements')):
            rewritten=os.path.relpath(relative,destination.parent).replace(os.sep,'/')
        else:
            kind='tree' if target.is_dir() else 'blob'
            rewritten=f'https://github.com/k-s-h-r/wcag-audit-kit/{kind}/{ref}/{relative.as_posix()}'
        if parts.query:rewritten+='?'+parts.query
        if parts.fragment:rewritten+='#'+parts.fragment
        return ']('+rewritten+')'
    lines=[];fenced=False
    for line in body.splitlines(keepends=True):
        if re.match(r'^\s*(`{3,}|~{3,})',line):fenced=not fenced
        lines.append(line if fenced else re.sub(r'\]\(([^\s)]+)\)',replace,line))
    return ''.join(lines)


def install(destination, selected=None, ref=None):
    destination=Path(destination).resolve();selected=list(dict.fromkeys(selected or ROLES))
    if any(role not in ROLES for role in selected):raise ValueError('スキル名が不正')
    if 'wcag-audit-kit' in selected:selected=list(ROLES)
    if destination==ROOT or destination.is_relative_to(ROOT):raise ValueError('配布先は原本の外へ指定する')
    destination.mkdir(parents=True,exist_ok=True)
    if any((destination/name).exists() for name in selected):raise ValueError('既存スキルを上書きしない。新しい配布先を指定する')
    ref=ref or source_ref()
    if not re.fullmatch(r'[A-Za-z0-9._/-]+',ref):raise ValueError('参照版が不正')
    paths=[]
    for directory in ['scripts','references','assets','vendor']:
        paths.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.tmp'}
                     and p.name not in {'install_skills.py','build_coverage.py','build_mode_matrix.py'})
    paths.extend(ROOT.glob('requirements*.txt'));paths.extend([ROOT/'package.json',ROOT/'package-lock.json'])
    with tempfile.TemporaryDirectory(dir=destination,prefix='.wcag-build-') as temporary:
        staging=Path(temporary)
        for role in selected:
            root=staging/role;root.mkdir()
            for source in paths:
                relative=source.relative_to(ROOT);target=root/relative;target.parent.mkdir(parents=True,exist_ok=True)
                if relative==Path('references/method-capabilities.json'):
                    value=json.loads(source.read_text())
                    for method in value['methods']:
                        method['evidence']=[f'https://github.com/k-s-h-r/wcag-audit-kit/blob/{ref}/{p}' for p in method['evidence']]
                    target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
                elif source.suffix=='.md' and not relative.as_posix().startswith('references/sources/'):
                    target.write_text(rewrite_markdown(source.read_text(),source,relative,selected,ref))
                else:shutil.copy2(source,target)
            source=ROOT/ROLES[role]
            (root/'SKILL.md').write_text(rewrite_markdown(source.read_text(),source,Path('SKILL.md'),selected,ref))
            (root/'distribution.json').write_text(json.dumps({'role':role,'version':json.loads((ROOT/'package.json').read_text())['version'],
                 'built_from_working_tree':True,'proof_reference':ref,'validation_copied':False},indent=2)+'\n')
        for role in selected:(staging/role).rename(destination/role)
    return {'destination':str(destination),'skills':selected,'proof_reference':ref}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--destination',required=True)
    parser.add_argument('--skills',nargs='+',choices=list(ROLES));parser.add_argument('--source-ref')
    args=parser.parse_args()
    try:print(json.dumps(install(args.destination,args.skills,args.source_ref),ensure_ascii=False,indent=2));return 0
    except (ValueError,OSError) as exc:print('ERROR:',exc);return 1


if __name__=='__main__':raise SystemExit(main())
