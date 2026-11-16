"""Small native-dialog and narrow-viewport acceptance, without an AI service."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import audit
from page_explorer import status
from page_workflow import machine_checks


def run(out):
    class Handler(SimpleHTTPRequestHandler):
        writes=0
        def log_message(self,*args):pass
        def do_POST(self):type(self).writes+=1;self.send_error(500)
    out.mkdir(parents=True,exist_ok=False)
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT/'tests/fixtures')))
    threading.Thread(target=server.serve_forever,daemon=True).start();results=[]
    try:
        for name,fixture,width in [('narrow','page-workflow.html',320),('native','native-dialog.html',1280)]:
            url=f'http://127.0.0.1:{server.server_port}/{fixture}'
            config=audit.init_config(url);config.update(environments=[{'id':name,'zoom':1,'viewport':{'width':width,'height':900}}],keyboard_steps=3)
            path=out/(name+'.json');audit.save(path,config);target=out/name
            assert audit.main(['page-audit','--url',url,'--config',str(path),'--out',str(target),
                '--max-states','12','--max-steps','6' if name=='narrow' else '20','--max-depth','1'])==0
            graph=status(target)
            assert graph['nodes'];assert all(n['environment']==name for n in graph['nodes'])
            if name=='native':
                assert any(e.get('native_events') for e in graph['edges'])
                assert any(e.get('blocked_requests') for e in graph['edges'])
                assert Handler.writes==0
                assert any(c['selector']=='#property-control' for n in graph['nodes'] for c in n['controls'])
                assert any(any(s['selector']=='#property-panel' for s in audit.load(target/n['evidence_dir']/'state.json')['state']) for n in graph['nodes'])
                assert any(m['outcome']=='cant_tell' for m in machine_checks(target))
            results.append({'name':name,'width':width,'states':len(graph['nodes']),'paths':len(graph['edges']),
                'native_dialog_recorded':any(e.get('native_events') for e in graph['edges']),
                'blocked_requests_recorded':any(e.get('blocked_requests') for e in graph['edges']),
                'property_handler_discovered':any(c['selector']=='#property-control' for n in graph['nodes'] for c in n['controls']),
                'writes_received':Handler.writes,'complete':graph['complete']})
        audit.save(out/'summary.json',results);print(json.dumps(results,ensure_ascii=False,indent=2))
    finally:server.shutdown();server.server_close()


if __name__=='__main__':run(Path(sys.argv[1]))
