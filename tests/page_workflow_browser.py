"""Reproducible real-browser acceptance; only serves the owned fixture."""
import argparse
from collections import Counter
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import audit
import page_workflow
from page_explorer import status


def run(out):
    class Handler(SimpleHTTPRequestHandler):
        writes=0;foreign=0
        def log_message(self,*args):pass
        def do_POST(self):type(self).writes+=1;self.send_error(500)
        def do_GET(self):
            if self.path.endswith('unvisited.html'):type(self).foreign+=1
            return super().do_GET()
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT/'tests/fixtures')))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}/page-workflow.html'
    config=audit.init_config(url);config.update(environments=config['environments'][:1],keyboard_steps=8)
    path=out/'config.json';out.mkdir(parents=True,exist_ok=False);audit.save(path,config);target=out/'run'
    try:
        common=['page-audit','--url',url,'--out',str(target),'--config',str(path),'--max-images','400','--max-states','150','--max-depth','5']
        assert audit.main(common+['--max-steps','100','--max-depth','1'])==0
        before=status(target);old_proof=before['proof'].copy();first_steps=before['steps']
        assert before['queue']
        assert audit.main(common+['--resume','--max-steps','1000'])==0
        graph=status(target)
        assert graph['steps']>first_steps
        for proof in old_proof:assert audit.evidence_item(target,proof['path'])==proof
        assert Handler.writes==Handler.foreign==0
        inventories=[audit.load(target/n['evidence_dir']/'state.json') for n in graph['nodes']]
        assert any(any(s['selector']=='#nested-panel' for s in i['state']) for i in inventories),'nested state not reached'
        assert any(i['modal']=='#dialog' for i in inventories),'dialog not reached'
        assert any(any(s['selector']=='#options' for s in i['state']) for i in inventories),'combobox not opened'
        assert any('#pointer-only' in str(e['route']) and e['error'] for e in graph['edges'])
        machine=page_workflow.machine_checks(target)
        assert any(m['checkpoint']=='axe / image-alt' and m['outcome']=='failed' for m in machine)
        result=audit.outcomes(target)
        assert not result['audit_complete']
        assert set(result['counts'])=={'not_run'},'machine checks must not fabricate WCAG judgments'
        packet=page_workflow.next_work(target,url,1)
        audit.save(out/'next-work.json',packet)
        summary={'states':len(graph['nodes']),'input_paths':len(graph['edges']),'pending_routes':len(graph['queue']),
            'first_steps':first_steps,'resumed_steps':graph['steps'],'prior_proof_unchanged':len(old_proof),
            'machine_results':dict(Counter(m['outcome'] for m in machine)),
            'cases':len(result['cases']),'wcag_outcomes':result['counts'],'audit_complete':result['audit_complete'],
            'write_requests_received':Handler.writes,'other_page_requests':Handler.foreign,
            'remaining':graph['remaining']}
        audit.save(out/'acceptance.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
    finally:server.shutdown();server.server_close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    run(parser.parse_args().out)
