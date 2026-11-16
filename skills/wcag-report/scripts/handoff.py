"""Concrete human review tasks. A handoff never supplies a conformance verdict."""
from html import escape

REASONS={'environment_constraint','no_reliable_method','specialist_judgement','impractical_verification'}


def text(value, name, minimum=1):
    if not isinstance(value,str) or len(value.strip())<minimum:
        raise ValueError('人への引き継ぎに具体的な'+name+'が必要')


def strings(value, name):
    if not isinstance(value,list) or not value:
        raise ValueError('人への引き継ぎに'+name+'の一覧が必要')
    for item in value:text(item,name)


def validate_handoff(value):
    if not isinstance(value,dict) or value.get('reason_kind') not in REASONS:
        raise ValueError('人への引き継ぎの理由区分が不正')
    for name in ['reason','reviewer','required_environment','resume']:
        text(value.get(name),name,10 if name in {'reason','resume'} else 1)
    attempts=value.get('attempts')
    if not isinstance(attempts,list) or not attempts:
        raise ValueError('人への引き継ぎ前に調べた方法・結果・証拠が必要')
    paths=[]
    for attempt in attempts:
        if not isinstance(attempt,dict):raise ValueError('人への引き継ぎの試行が不正')
        text(attempt.get('method'),'試した方法')
        text(attempt.get('observed'),'試行の具体的な結果',10)
        strings(attempt.get('evidence'),'試行の証拠')
        paths.extend(attempt['evidence'])
    checks=value.get('checks')
    if not isinstance(checks,list) or not checks:
        raise ValueError('人への引き継ぎに対象ごとの残る検査が必要')
    for check in checks:
        if not isinstance(check,dict):raise ValueError('人への引き継ぎの検査が不正')
        text(check.get('target'),'実際の対象')
        strings(check.get('steps'),'対象ページで行う操作')
        text(check.get('expected'),'判定する条件',10)
        strings(check.get('evidence'),'対象の証拠')
        paths.extend(check['evidence'])
    return paths


def details(value):
    checks=[]
    for check in value['checks']:
        steps=''.join('<li>'+escape(step)+'</li>' for step in check['steps'])
        checks.append('<li>'+escape(check['target'])+'<ol>'+steps+'</ol><p>判定条件：'+escape(check['expected'])+'</p></li>')
    return ('<details><summary>人による確認が必要</summary><p>'+escape(value['reason'])+'</p>'
        '<p>担当に必要な知識：'+escape(value['reviewer'])+'。環境：'+escape(value['required_environment'])+'</p>'
        '<ul>'+''.join(checks)+'</ul><p>結果の戻し方：'+escape(value['resume'])+'</p></details>')


def markdown(cases):
    lines=['# 人による確認の引き継ぎ','',
        'ここにある項目は未確認です。引き継ぎを記録しても検証完了・適合にはなりません。',
        'このファイルは依頼内容の出力であり、外部への送信や担当者への連絡は行っていません。','']
    if not cases:lines.append('人への引き継ぎが記録されたcaseはありません。未実施・その他の判断保留はreport.jsonで別に確認してください。')
    for case in cases:
        value=case['assessment_data']['human_handoff']
        lines += ['## '+case['criterion']+' '+case['title'],'',
            'case_id: '+case['case_id'],
            '対象: '+case['page_url']+' / '+case['state']+' / '+case['environment'],
            '現在の判定: '+case['outcome'],'',
            '引き継ぐ理由: '+value['reason'],
            '担当に必要な知識: '+value['reviewer'],
            '必要な環境: '+value['required_environment'],'','調べた方法と結果:','']
        for attempt in value['attempts']:
            lines += ['- '+attempt['method']+': '+attempt['observed'],
                '  証拠: '+', '.join(attempt['evidence'])]
        for check in value['checks']:
            lines += ['','対象: '+check['target'],'','実行する操作:','']
            lines += [str(i)+'. '+step for i,step in enumerate(check['steps'],1)]
            lines += ['','判定条件: '+check['expected'],'証拠: '+', '.join(check['evidence'])]
        lines += ['','結果の戻し方: '+value['resume'],
            '元の判定: ['+case['assessment']+']('+case['assessment']+')','']
    return '\n'.join(lines)+'\n'
