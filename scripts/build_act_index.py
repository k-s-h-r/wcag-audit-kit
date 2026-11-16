#!/usr/bin/env python3
"""Index pinned W3C ACT rules without turning atomic outcomes into WCAG verdicts."""
from collections import Counter
from hashlib import sha256
from html import unescape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1] / 'skills' / 'wcag-audit-kit'
SOURCE=ROOT/'references/sources/act'


def examples_from_source(text,rule_id,metadata):
    """Use examples in this exact rule version, not every draft with the same ID."""
    examples=[]
    for match in re.finditer(r'<a\b[^>]*\bclass="example-link"[^>]*>',text):
        tag=match.group();href=re.search(r'href="([^"]+)"',tag);title=re.search(r'title="([^"]+)"',tag)
        if not href or not title:raise ValueError('ACT example link is incomplete')
        url=unescape(href[1]);ident=re.search(r'/testcases/([a-z0-9]{6})/([0-9a-f]{40})\.(html|svg|xml)$',url)
        if not ident or ident[1]!=rule_id:raise ValueError('ACT example belongs to another rule')
        expected=title[1].split()[0].lower()
        if expected not in {'passed','failed','inapplicable'}:raise ValueError('Unknown ACT expected outcome')
        source=metadata.get((rule_id,ident[2],ident[3]))
        if source and source['expected']!=expected:raise ValueError('Conflicting expected outcome in selected ACT version')
        examples.append({'id':ident[2],'extension':ident[3],'title':unescape(title[1]),'expected':expected,'url':url,
            'metadata_approved_flag':source.get('approved') if source else None})
    if len({(x['id'],x['extension']) for x in examples})!=len(examples):raise ValueError('Duplicate ACT example')
    return examples


def build():
    mapping=json.loads((SOURCE/'wcag-mapping.json').read_text())['act-rules']
    repository=json.loads((SOURCE/'repository.json').read_text())
    source_files={x['local']:x for x in repository['files']}
    tests=json.loads((SOURCE/'testcases.json').read_text())
    example_metadata={(x['ruleId'],x['testcaseId'],urlsplit(x['url']).path.rsplit('.',1)[-1]):x for x in tests['testcases']}
    criteria=json.loads((ROOT/'references/catalog.json').read_text())['criteria']
    known={c['id']:c for c in criteria}
    rules=[]
    for item in mapping:
        ident=item['frontmatter']['id']
        status='deprecated' if item['deprecated'] else 'proposed' if item['proposed'] else 'approved'
        requirements=item['frontmatter'].get('accessibility_requirements') or {}
        linked=[]
        for key,value in requirements.items():
            match=re.fullmatch(r'wcag(?:20|21|22):(\d\.\d\.\d)',key)
            if match:linked.append({'criterion':match[1],'requirement_key':key,
                'in_wcag22':match[1] in known,'mapping':value})
        rule={'id':ident,'title':item['title'],'status':status,
            'type':item['frontmatter']['rule_type'],'published_url':'https://www.w3.org/WAI'+item['permalink'],
            'requirements':requirements,'criteria':linked,'input_aspects':item['frontmatter'].get('input_aspects',[]),
            'input_rules':item['frontmatter'].get('input_rules',[]),'source':None,'examples':[]}
        if status!='deprecated':
            path=f'rules/{ident}.md';text=(SOURCE/path).read_text()
            digest=sha256((SOURCE/path).read_bytes()).hexdigest()
            if digest!=source_files[path]['sha256']:raise ValueError('ACT source changed: '+path)
            frontmatter=yaml.safe_load(text.split('---',2)[1])
            if frontmatter['rule_meta']['id']!=ident:raise ValueError('ACT source ID differs')
            if bool(frontmatter['proposed'])!=(status=='proposed'):raise ValueError('ACT source status differs')
            rule['source']={'path':'references/sources/act/'+path,'sha256':digest,
                'repository_path':source_files[path]['remote'],'commit':repository['commit'],
                'last_modified':str(frontmatter['rule_meta'].get('last_modified',''))}
            rule['examples']=examples_from_source(text,ident,example_metadata)
            if not rule['examples']:raise ValueError('No examples found for '+ident)
        rules.append(rule)
    if len({r['id'] for r in rules})!=len(rules):raise ValueError('ACT IDs must be unique')
    by_id={r['id']:r for r in rules}
    for rule in rules:
        for child in rule['input_rules']:
            if child not in by_id:raise ValueError('Missing composite input rule '+child)
    out={'source_repository':repository['repository'],'source_commit':repository['commit'],
         'note':'Atomic/composite rule outcomes are distinct from whole-success-criterion judgments.',
         'rules':rules}
    (ROOT/'references/act-rules.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    dest=ROOT/'references/act';dest.mkdir(exist_ok=True)
    labels={'approved':'承認済み','proposed':'提案中','deprecated':'廃止'}
    for criterion in criteria:
        entries=[(r,next(x for x in r['criteria'] if x['criterion']==criterion['id']))
                 for r in rules if any(x['criterion']==criterion['id'] for x in r['criteria']) and r['status']!='deprecated']
        entries.sort(key=lambda item:(item[0]['status']!='approved',item[0]['id']))
        lines=[f"# {criterion['id']}に関係するACT Rules",'',
            '適用条件・期待結果・前提・支援状況・用語を、使用するルール本文で読む。ページの対象へ具体化して実行する。',
            '承認済みを優先する。提案中のものを使う場合はその状態と版を記録する。廃止されたルールは検査の根拠にしない。',
            'ルールがこの基準より厳しい場合や、合格後も追加検査を要する場合がある。下記の対応と原典を照合し、合否を機械的に基準全体へ変換しない。','']
        if not entries:lines+=['この基準に対応する現行ルールは、このスナップショットにない。基準の本文とTechniquesに沿った検査を省略しない。','']
        for rule,link in entries:
            lines += [f"## {rule['id']} — {rule['title']}",'',f"状態：{labels[rule['status']]}。種別：{rule['type']}。",
                f"[本文・具体例](../sources/act/rules/{rule['id']}.md) / [公開ページ]({rule['published_url']})",'',
                'この基準との対応（原文）：','', '```json',json.dumps(link['mapping'],ensure_ascii=False,indent=2),'```','',
                f"この版の具体例：{len(rule['examples'])}件。ID・期待値・URLは `python3 scripts/audit.py rule --id {rule['id']}` で参照できる。",'']
        (dest/(criterion['id']+'.md')).write_text('\n'.join(lines)+'\n')
    print(json.dumps({'rules':len(rules),'statuses':dict(Counter(r['status'] for r in rules)),
        'examples_in_selected_versions':sum(len(r['examples']) for r in rules),'criterion_guides':len(criteria)},ensure_ascii=False))


if __name__=='__main__':build()
