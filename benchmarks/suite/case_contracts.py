"""Private expected evidence for fixture acquisition checks, never WCAG verdicts."""

KINDS={'inventory','focus-sequence','viewport','state-capture','timeline','language','accessible-name','geometry'}


def validate(case):
    seen=set()
    for item in case.get('evidence_expectations',[]):
        key=(item.get('page'),item.get('state'),item.get('checkpoint'))
        if key in seen:raise ValueError('取得期待が重複')
        seen.add(key)
        if item.get('page') not in case['pages'] or item.get('state') not in {s['id'] for s in case['states']} or item.get('checkpoint') not in case['checkpoints']:
            raise ValueError('取得期待がページ・状態・確認観点と不一致')
        if item.get('kind') not in KINDS or not isinstance(item.get('targets'),list) or any(not isinstance(t,str) or not t.strip() for t in item['targets']):
            raise ValueError('取得期待の種類又は対象が不正')
        if not item['targets'] and item.get('empty_is_expected') is not True:raise ValueError('対象なしの取得期待は意図を明示する')
        if not isinstance(item.get('rationale'),str) or not item['rationale'].strip():raise ValueError('取得期待の根拠が必要')
        if 'expected' in item or 'outcome' in item:raise ValueError('取得期待を適合・不適合の判定へ混ぜない')


def coverage(data,checkpoints):
    verdict={e['checkpoint'] for s in data['suites'] for c in s['cases'] for e in c['expectations']}
    acquisition={e['checkpoint'] for s in data['suites'] for c in s['cases'] for e in c.get('evidence_expectations',[])}
    all_ids={p['id'] for p in checkpoints}
    return dict(verdict=sorted(verdict),acquisition=sorted(acquisition),missing=sorted(all_ids-verdict-acquisition),
                registered=sorted(verdict|acquisition))
