#!/usr/bin/env python3
"""Optional Orca worker for this corpus's 4.1.3 status-message contrast cases.

Reads only public tasks to decide observations. It never reads expected outcomes.
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmarks import core,runner


def phrases(row):return ''.join(s.get('phrase','') for s in row.get('speech',[]) if isinstance(s,dict)).replace(' ','').replace('\n','')


def interpret(result):
    rows=result.get('observations',[]);env=result.get('environment',{})
    if len(rows)<2 or result.get('status')=='blocked' or env.get('simulation') is not False or not env.get('installation_verified'):
        return {'valid':False,'announced':False,'reason':'実SRの起動・操作を完了できなかった。'}
    last=rows[-1];focus=last.get('focus_after',{})
    shown=any(o.get('target',{}).get('selector')=='#notice' and o.get('text')=='記録しました。' for o in last.get('observations',[]))
    control='記録する' in phrases(rows[0])
    valid=shown and control and focus.get('id')=='record' and focus.get('documentHasFocus') is True
    return {'valid':valid,'announced':valid and '記録しました' in phrases(last),
            'reason':f'実SRの対照発話={control}、画面の記録完了={shown}、操作後のフォーカス={focus.get("id")}。',
            'environment':{k:env.get(k) for k in ['reader','reader_version','browser_version','kernel']}}


def make_request(job):
    from screen_reader_native import validate
    request={'case_id':job['id'],'url':job['urls'][job['pages'][0]],'locale':'ja-JP','settle_ms':3000,
        'actions':[{'type':'browser.press','key':'Tab','expect_contains':'記録する'},
                   {'type':'browser.press','key':'Space','expect_contains':'記録しました'}],
        'observe':[{'selector':'#notice'}]}
    validate(request)
    return request


def capture(root,area):
    # AF_UNIX socket names have a short OS limit. Keep the live backend in a
    # short private directory, then preserve its regular files byte-for-byte.
    with tempfile.TemporaryDirectory(prefix='wcag-sr-',dir='/tmp') as temporary:
        runtime=Path(temporary)/'speech'
        with (area/'stdout.txt').open('w') as stdout,(area/'stderr.txt').open('w') as stderr:
            subprocess.run([sys.executable,str(core.ROOT/'scripts/screen_reader_native.py'),'--root',str(root),
                '--request',str(area/'request.json'),'--out',str(runtime)],stdout=stdout,stderr=stderr,check=False)
        for source in runtime.rglob('*'):
            if source.is_file() and source.resolve().is_relative_to(runtime.resolve()):
                target=area/'speech'/source.relative_to(runtime);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)


def work(run,root,import_results=False):
    run=Path(run);task_file=core.load(run/'worker/tasks.json')
    proof=core.load(run/'integrity.json')['files']
    for name,expected in proof.items():
        if name.startswith('worker/') and core.file_hash(core.local(run,name))!=expected:raise ValueError('検査担当向けのページ・タスクが変更された')
    jobs=[j for j in task_file['jobs'] if j['criterion']=='4.1.3' and core.modes.MODES[j['mode']]['screen_reader'] and j['pages'] in [['p01.html'],['p02.html']]]
    if not jobs:raise ValueError('このworkerが扱う初版の4.1.3対照例がありません。追加パターンは別の実SR手順で確認する')
    from urllib.parse import urlsplit
    port=urlsplit(next(iter(jobs[0]['urls'].values()))).port
    http=runner.server(run/'worker/public',port);received=[]
    producer=core.file_hash(Path(__file__));source=run/'producers'/producer/'native_status.py'
    source.parent.mkdir(parents=True,exist_ok=True)
    if not source.exists():shutil.copyfile(__file__,source)
    try:
        for job in jobs:
            area=run/'attachments'/job['id']/('native-'+uuid.uuid4().hex[:12]);area.mkdir(parents=True)
            request=make_request(job)
            core.save(area/'request.json',request)
            capture(root,area)
            receipt=area/'speech/screen-reader.json'
            result=core.load(receipt) if receipt.exists() else {}
            received.append((job,area,receipt,interpret(result)))
        # A silent negative is classified only when the same mode/environment
        # also produced the requested live message in the contrast set.
        calibrated={(j['mode'],core.digest(r.get('environment'))) for j,_,_,r in received if r['valid'] and r['announced']}
        outputs=[]
        for job,area,receipt,result in received:
            key=(job['mode'],core.digest(result.get('environment')))
            outcome='passed' if result['valid'] and result['announced'] else 'failed' if result['valid'] and key in calibrated else 'cant_tell'
            proof=[receipt.relative_to(run).as_posix()] if receipt.exists() else []
            value={'schema_version':'1','run_id':task_file['run_id'],'corpus_digest':task_file['corpus_digest'],'job_id':job['id'],
                'producer_digest':producer,'observations':[dict(page=job['pages'][0],state='after-activate',target='#notice',checkpoint='4.1.3-02',
                outcome=outcome,method='screen-reader',observed=result['reason']+f' 操作中の通知発話={result["announced"]}。同じ環境の対照確認={key in calibrated}。',evidence=proof)]}
            core.save(area/'prediction.json',value)
            core.freeze(run,[source,*[p for p in area.rglob('*') if p.is_file()]])
            if import_results:core.record_review(run,value)
            outputs.append({'job_id':job['id'],'outcome':outcome,'prediction':str(area/'prediction.json')})
        return outputs
    finally:http.shutdown();http.server_close()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',required=True);parser.add_argument('--root',required=True)
    parser.add_argument('--import-results',action='store_true');args=parser.parse_args()
    try:
        import json
        print(json.dumps(work(args.run,args.root,args.import_results),ensure_ascii=False,indent=2));return 0
    except (ValueError,OSError) as error:print('ERROR:',error,file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
