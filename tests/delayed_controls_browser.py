"""Verify bounded observation of function timers with a previously unused delay."""
import argparse,functools,json,sys,threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'skills/wcag-audit-kit/scripts'));import audit
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--delay',type=int,default=650);p.add_argument('--expect-bounded',action='store_true');a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
http=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT/'tests/fixtures')));threading.Thread(target=http.serve_forever,daemon=True).start()
try:
 url=f'http://127.0.0.1:{http.server_port}/delayed-controls.html?delay={a.delay}';cfg=audit.init_config(url);cfg['environments']=cfg['environments'][:1];cfg['keyboard_steps']=2;audit.save(out/'config.json',cfg)
 assert audit.main(['page-audit','--url',url,'--config',str(out/'config.json'),'--mode','machine','--out',str(out/'run'),'--max-states','8','--max-steps','6','--max-depth','1'])==0
 run=audit.run_layout.ledger(out/'run')
 graph=audit.load(run/'exploration.json');found=[];waits=[]
 for node in graph['nodes']:
  raw=audit.load(run/node['evidence_dir']/'axe.json');state=audit.load(run/node['evidence_dir']/'state.json')
  if any(n.get('selector')=='#subject' for n in state['state']) and any(r['id']=='image-alt' for r in raw['violations']):found.append(node['route'])
 for edge in graph['edges']:
  transition=audit.load(run/edge['evidence_dir']/'transition.json');waits.extend(transition.get('settling',[]))
 value={'delay_ms':a.delay,'routes_with_image_and_axe':found,'waits':waits,'remaining':graph['remaining'],'states':len(graph['nodes']),'wcag_outcomes':audit.outcomes(run)['counts']};audit.save(out/'observed.json',value)
 if a.expect_bounded:assert any(w and w['status']!='quiet' for w in waits) and graph['remaining'],value
 else:assert found,value
 assert set(value['wcag_outcomes'])=={'not_run'}
 print(json.dumps({'delay_ms':a.delay,'image_routes':len(found),'states':len(graph['nodes']),'bounded_expected':a.expect_bounded}))
finally:http.shutdown();http.server_close()
