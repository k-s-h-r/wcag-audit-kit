"""Measure a declared focus-indicator mask at the same pixels in two captures.

The mask and component must be identified from the actual page. This tool returns
measurements, not a WCAG judgement. Install requirements-analysis.txt when needed.
"""
import argparse
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import re
import sys

import numpy as np


def number(value, name, positive=False):
    if type(value) not in {int, float} or not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(name + ' must be a finite number' + (' greater than zero' if positive else ''))
    return float(value)


def rectangle(value, name):
    if not isinstance(value, dict):
        raise ValueError(name + ' must be a rectangle')
    result={key:number(value.get(key), name+'.'+key, key in {'width','height'})
            for key in ['x','y','width','height']}
    return result


def reference_area(component, shape='rectangle', radius=None):
    width=number(component.get('width'),'component.width',True)
    height=number(component.get('height'),'component.height',True)
    if not math.isfinite(4*(width+height)):
        raise ValueError('component reference area is not finite')
    if shape=='rectangle':
        return 4 * (width + height)
    if shape not in {'circle','rounded_rectangle'}:
        raise ValueError('shape must be rectangle, circle or rounded_rectangle')
    r=number(radius,'radius',True)
    if r>min(width,height)/2:
        raise ValueError('radius exceeds the component')
    if shape=='circle':
        if abs(width-2*r)>1e-6 or abs(height-2*r)>1e-6:
            raise ValueError('circle dimensions must match its radius')
        return 4 * math.pi * r
    return 4 * (width + height) - (16 - 4*math.pi)*r


def luminance(rgb):
    values=np.asarray(rgb,dtype=np.float64)/255
    values=np.where(values<=.04045, values/12.92, ((values+.055)/1.055)**2.4)
    return values @ np.array([.2126,.7152,.0722],dtype=np.float64)


def analyse_arrays(before, focused, mask, dpr, component, shape='rectangle', radius=None):
    dpr=number(dpr,'dpr',True)
    if not math.isfinite(dpr*dpr) or dpr*dpr==0:
        raise ValueError('dpr cannot be represented as an area scale')
    before=np.asarray(before);focused=np.asarray(focused);mask=np.asarray(mask)
    if before.dtype!=np.uint8 or focused.dtype!=np.uint8 or before.ndim!=3 or before.shape[-1]!=3:
        raise ValueError('captures must contain 8-bit RGB pixels')
    if focused.shape!=before.shape or mask.shape!=before.shape[:2] or mask.dtype!=np.bool_:
        raise ValueError('capture dimensions and boolean mask must match')
    reference=reference_area(component,shape,radius)
    # Compute only declared indicator pixels, not every rendered text/edge change.
    a=before[mask];b=focused[mask]
    count=len(a);qualified=0;minimum=None;maximum=None
    for start in range(0,count,100000):
        x=luminance(a[start:start+100000]);y=luminance(b[start:start+100000])
        ratios=(np.maximum(x,y)+.05)/(np.minimum(x,y)+.05)
        qualified+=int(np.count_nonzero(ratios>=3))
        low=float(np.min(ratios));high=float(np.max(ratios))
        minimum=low if minimum is None else min(minimum,low)
        maximum=high if maximum is None else max(maximum,high)
    area=qualified/(dpr*dpr)
    return {'candidate_device_pixels':count,'same_pixel_contrast_min':minimum,
      'same_pixel_contrast_max':maximum,'pixels_with_contrast_at_least_3':qualified,
      'qualifying_area_css_px2':area,'reference_area_css_px2':reference,
      'qualifying_area_to_reference_ratio':area/reference,
      'reference_formula':'4w+4h / 4πr / 4w+4h−(16−4π)r from Understanding 2.4.13',
      'wcag_judgement':None,
      'limitations':['The operator must identify the actual component and indicator pixels.',
        'This compares the same coordinates; it does not measure adjacent-color contrast.',
        'A literal 2 CSS px perimeter and exceptions must also be checked against the source.',
        'All components, states, keyboard operation and other WCAG conditions require review.']}


def load_frame(path):
    from PIL import Image
    data=path.read_bytes()
    with Image.open(BytesIO(data)) as im:
        if im.format!='PNG' or im.mode not in {'RGB','RGBA'}:
            raise ValueError('Use lossless RGB/RGBA PNG captures')
        if data[24]!=8:
            raise ValueError('This method requires 8-bit PNG samples')
        if im.info.get('icc_profile'):
            raise ValueError('Profiled captures need a verified color-managed method')
        if im.mode=='RGBA' and im.getchannel('A').getextrema()!=(255,255):
            raise ValueError('Transparent captures need a verified composited background')
        pixels=np.asarray(im.convert('RGB')).copy()
    return pixels,data


def run_request(request, source_dir):
    if not isinstance(request,dict) or not isinstance(request.get('case_id'),str) or not request['case_id'].strip():
        raise ValueError('case_id is required')
    if not isinstance(request.get('mask_description'),str) or len(request['mask_description'].strip())<10:
        raise ValueError('Describe why the selected regions and colors are the focus indicator')
    if request.get('color_space')!='srgb':
        raise ValueError('Declare the verified sRGB capture basis as color_space=srgb')
    dpr=number(request.get('dpr'),'dpr',True)
    first=rectangle(request.get('component_before'),'component_before')
    second=rectangle(request.get('component_focused'),'component_focused')
    if any(abs(first[key]-second[key])>1e-6 for key in first):
        raise ValueError('This method requires an unchanged component rectangle; use another method if it moves')
    before,raw_before=load_frame((source_dir/request['before']).resolve())
    focused,raw_focused=load_frame((source_dir/request['focused']).resolve())
    if before.shape!=focused.shape:
        raise ValueError('Capture dimensions differ')
    height,width=before.shape[:2]
    colors=request.get('indicator_colors')
    if not isinstance(colors,list) or not colors or any(not isinstance(c,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',c) for c in colors):
        raise ValueError('indicator_colors must contain #rrggbb values')
    regions=request.get('regions')
    if not isinstance(regions,list) or not regions:
        raise ValueError('regions must delimit the actual indicator')
    mask=np.zeros((height,width),dtype=np.bool_)
    xx=(np.arange(width)+.5)/dpr;yy=(np.arange(height)+.5)/dpr
    for index,value in enumerate(regions):
        r=rectangle(value,f'regions[{index}]')
        if r['x']<0 or r['y']<0 or r['x']+r['width']>width/dpr+1e-6 or r['y']+r['height']>height/dpr+1e-6:
            raise ValueError('A selected region is outside the capture')
        mask |= ((yy>=r['y']) & (yy<r['y']+r['height']))[:,None] & ((xx>=r['x']) & (xx<r['x']+r['width']))[None,:]
    color_mask=np.zeros((height,width),dtype=np.bool_)
    for color in colors:
        rgb=np.array([int(color[i:i+2],16) for i in (1,3,5)],dtype=np.uint8)
        color_mask |= np.all(focused==rgb,axis=2)
    result=analyse_arrays(before,focused,mask & color_mask,dpr,first,
                          request.get('shape','rectangle'),request.get('radius'))
    result.update(case_id=request['case_id'],mask_description=request['mask_description'],
                  dpr=dpr,component_before=first,component_focused=second,
                  indicator_colors=colors,regions=regions,
                  before_sha256=hashlib.sha256(raw_before).hexdigest(),
                  focused_sha256=hashlib.sha256(raw_focused).hexdigest())
    return result,raw_before,raw_focused


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    try:
        raw=args.request.read_bytes();request=json.loads(raw)
        result,before,focused=run_request(request,args.request.resolve().parent)
        args.out.mkdir(parents=True,exist_ok=False)
        (args.out/'request.json').write_bytes(raw)
        (args.out/'before.png').write_bytes(before)
        (args.out/'focused.png').write_bytes(focused)
        result.update(status='collected',request_sha256=hashlib.sha256(raw).hexdigest())
        (args.out/'focus-measure.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'status':'collected','area_css_px2':result['qualifying_area_css_px2'],
                         'reference_css_px2':result['reference_area_css_px2'],'wcag_judgement':None}))
        return 0
    except (ValueError,KeyError,OSError) as error:
        print('ERROR: '+str(error),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
