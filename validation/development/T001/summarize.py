"""Private analysis of existing score rows; never passed to the collector."""
import argparse
from collections import Counter
import csv,json
from pathlib import Path


def summarize(report,criterion):
    selected=[r for r in csv.DictReader((Path(__file__).parent/'selected-rows.csv').open()) if r['criterion']==criterion]
    keys=['case','page','state','target','checkpoint'];index={tuple(r[k] for k in keys):r for r in report['rows'] if r['mode']=='machine'}
    results=[]
    for expected in selected:
        actual=index.get(tuple(expected[k] for k in keys))
        if actual and actual['expected']!=expected['expected']:raise ValueError('Frozen expected result differs')
        results.append(dict(expected,actual=(actual or {}).get('actual','not_run'),grade=(actual or {}).get('grade','not_evaluated'),evidence=(actual or {}).get('evidence',[]),source=(actual or {}).get('source','')))
    point={r['checkpoint'] for r in selected}
    extras=[r for r in report['unexpected_findings'] if r['checkpoint'] in point]
    return dict(selected_rows=len(results),grade_counts=dict(Counter(r['grade'] for r in results)),
        known_failures=sum(r['expected']=='failed' for r in results),detected_failures=sum(r['expected']=='failed' and r['actual']=='failed' for r in results),
        false_passes=sum(r['expected']=='failed' and r['actual']=='passed' for r in results),
        false_positives=sum(r['expected']!='failed' and r['actual']=='failed' for r in results)+len(extras),
        unverified=sum(r['actual'] in {'not_run','cant_tell'} for r in results),
        selected_checks_status=report['selected_checks_status'],overall_status=report['overall_status'],
        full_counts=report['counts'],pending_evidence_contracts=report.get('pending_evidence_contracts',[]),
        rows=results,unexpected_findings=extras)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('report');p.add_argument('criterion');a=p.parse_args()
    print(json.dumps(summarize(json.loads(Path(a.report).read_text()),a.criterion),ensure_ascii=False,indent=2))
