#!/usr/bin/env python3
"""Numerical helpers. Inputs must be verified against the actual rendered target."""
import argparse
import json
import math
import re


def validate_targets(checks, option, label):
    if not isinstance(checks, list) or len(checks) > 20:
        raise ValueError(f'{option}には20対象まで指定できる')
    seen = set()
    for check in checks:
        if not isinstance(check, dict) or set(check) != {'id', 'name', 'target'}:
            raise ValueError(f'{label}にはid、name、targetを指定する')
        identifier = check['id']
        if not isinstance(identifier, str) or not re.fullmatch(r'[a-z0-9-]{1,64}', identifier) or identifier in seen:
            raise ValueError(f'{label}には重複のない英小文字・数字・ハイフンのidを指定する')
        if any(not isinstance(check[key], str) or not check[key].strip() for key in ('name', 'target')):
            raise ValueError(f'{label}には名前と対象を一つに絞るセレクターを指定する')
        seen.add(identifier)


def luminance(hex_color):
    text=hex_color.lstrip('#')
    if len(text)==3:text=''.join(c*2 for c in text)
    if len(text)!=6:raise ValueError('不透明なRGBの#rrggbb又は#rgbを指定する')
    rgb=[int(text[i:i+2],16)/255 for i in (0,2,4)]
    v=[x/12.92 if x<=0.04045 else ((x+.055)/1.055)**2.4 for x in rgb]
    return .2126*v[0]+.7152*v[1]+.0722*v[2]


def contrast(fg,bg):
    a,b=sorted([luminance(fg),luminance(bg)])
    ratio=(b+.05)/(a+.05)
    return {'ratio':ratio,'meets_3':ratio>=3,'meets_4_5':ratio>=4.5,'meets_7':ratio>=7,
            'note':'表示上の合成色・文字サイズ・太さ・例外は別途確認する。丸め前の値で比較。'}


def spacing(rectangles):
    """24 CSS pixel circles must not intersect targets or other undersized circles."""
    results=[]
    for i,r in enumerate(rectangles):
        small=r['width']<24 or r['height']<24
        center=(r['x']+r['width']/2,r['y']+r['height']/2)
        conflicts=[]
        if small:
            for j,o in enumerate(rectangles):
                if i==j:continue
                if o['width']<24 or o['height']<24:
                    oc=(o['x']+o['width']/2,o['y']+o['height']/2)
                    hit=math.dist(center,oc)<24
                else:
                    closest=(max(o['x'],min(center[0],o['x']+o['width'])),
                             max(o['y'],min(center[1],o['y']+o['height'])))
                    hit=math.dist(center,closest)<12
                if hit:conflicts.append(o['id'])
        results.append({'id':r['id'],'size_at_least_24':not small,'spacing_geometry_ok':not conflicts,'conflicts':conflicts})
    return {'targets':results,'note':'実際の当たり判定、位置、他の例外を確認してから2.5.8を判定する。'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='cmd',required=True)
    c=s.add_parser('contrast');c.add_argument('--foreground',required=True);c.add_argument('--background',required=True)
    c=s.add_parser('spacing');c.add_argument('--file',required=True)
    a=p.parse_args()
    if a.cmd=='contrast':v=contrast(a.foreground,a.background)
    else:
        from pathlib import Path
        v=spacing(json.loads(Path(a.file).read_text()))
    print(json.dumps(v,ensure_ascii=False,indent=2))
