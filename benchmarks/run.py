#!/usr/bin/env python3
"""Collect, grade and compare criterion-scoped accessibility fixtures."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import threading
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmarks import core,runner,reporting


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('inventory')
    p=sub.add_parser('collect');p.add_argument('--out',required=True);p.add_argument('--mode',choices=[*core.modes.MODES,'all'])
    p.add_argument('--criterion',action='append',choices=list(core.audit.CRITERIA));p.add_argument('--port',type=int,default=0);p.add_argument('--resume',action='store_true')
    for name in ['serve','score','import','attach','task']:
        p=sub.add_parser(name);p.add_argument('--run',required=True)
        if name in {'import','attach'}:p.add_argument('--file',required=True)
        if name=='attach':p.add_argument('--job',required=True)
        if name=='task':p.add_argument('--job',required=True)
        if name=='score':p.add_argument('--strict',action='store_true')
    p=sub.add_parser('compare');p.add_argument('--baseline',required=True);p.add_argument('--current',required=True);p.add_argument('--out',required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=='inventory':
            value=core.corpus();ready={s['criterion']:len(s['cases']) for s in value['suites']}
            print(json.dumps({'corpus_digest':value['digest'],'checkpoint_coverage':core.case_contracts.coverage(value,core.modes.catalog()['checkpoints']),'criteria':[dict(id=c['id'],title=c['title'],cases=ready.get(c['id'],0),status='prepared' if c['id'] in ready else 'unprepared') for c in core.audit.CATALOG['criteria']]},ensure_ascii=False,indent=2));return 0
        if args.command=='collect':
            selected=list(core.modes.MODES) if args.mode=='all' else [args.mode] if args.mode else None
            result=runner.collect(Path(args.out),criterion=args.criterion,selected_modes=selected,port=args.port,resume=args.resume)
            files=reporting.write(Path(args.out),result)
            print(json.dumps(dict(files=files,selected_checks_status=result['selected_checks_status'],overall_status=result['overall_status'],counts=result['counts'],pending_evidence_contracts=len(result.get('pending_evidence_contracts',[]))),ensure_ascii=False,indent=2));return 0
        if args.command=='compare':
            out=Path(args.out)
            if out.exists():raise ValueError('新しい比較結果の保存先を指定する')
            value=core.compare(core.load(args.baseline),core.load(args.current));core.save(out,value);print(json.dumps(value,ensure_ascii=False,indent=2));return 1 if value['regressions'] else 0
        run=Path(args.run);meta,_=core.verify(run)
        if args.command=='task':
            job=next((j for j in core.tasks(run) if j['id']==args.job),None)
            if job is None:raise ValueError('ジョブが存在しない')
            print(json.dumps(job,ensure_ascii=False,indent=2));return 0
        if args.command=='serve':
            http=runner.server(run/'worker/public',meta['port']);print(f'Public fixtures: http://127.0.0.1:{meta["port"]}',flush=True)
            try:threading.Event().wait()
            except KeyboardInterrupt:pass
            finally:http.shutdown();http.server_close()
            return 0
        if args.command=='attach':
            if args.job not in {j['id'] for j in core.tasks(run)}:raise ValueError('ジョブが存在しない')
            src=Path(args.file)
            if not src.is_file():raise ValueError('実在するファイルを指定する')
            dest=run/'attachments'/args.job/(uuid.uuid4().hex[:12]+'-'+src.name);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
            core.freeze(run,[dest]);print(dest.relative_to(run));return 0
        if args.command=='import':
            print(json.dumps(core.record_review(run,core.load(args.file)),ensure_ascii=False,indent=2));return 0
        result=core.score(run);files=reporting.write(run,result)
        print(json.dumps(dict(files=files,selected_checks_status=result['selected_checks_status'],overall_status=result['overall_status'],counts=result['counts'],pending_evidence_contracts=len(result.get('pending_evidence_contracts',[]))),ensure_ascii=False,indent=2))
        if not args.strict:return 0
        return 1 if result['selected_checks_status']=='failed' else 2 if result['selected_checks_status']=='incomplete' else 0
    except (ValueError,KeyError,OSError,TypeError) as error:
        print('ERROR:',error,file=sys.stderr);return 1


if __name__=='__main__':
    raise SystemExit(main())
