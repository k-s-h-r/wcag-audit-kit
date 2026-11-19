"""Check real route labels, repeated visual states, and protected operations."""
import argparse,functools,json,sys,threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'skills/wcag-audit-kit/scripts'));import audit
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
class Handler(SimpleHTTPRequestHandler):
 writes=0
 def log_message(self,*args):pass
 def do_POST(self):type(self).writes+=1;self.send_error(500)
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT/'tests/fixtures')));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 url=f'http://127.0.0.1:{server.server_port}/formless-controls.html?clear-on-scroll';cfg=audit.init_config(url);cfg['environments']=cfg['environments'][:1];cfg['keyboard_steps']=2
 cfg['exploration_labels']=[
  {'id':'loaded-via-key','actions':[{'selector':'#load','type':'key','key':'Enter'}],'assert':[{'selector':'#result img','count':1,'visible':True}]},
  {'id':'wrong-count','actions':[{'selector':'#load','type':'click'}],'assert':[{'selector':'#result img','count':2}]},
  {'id':'protected-submit','actions':[{'selector':'#external-submit','type':'click'}],'assert':[{'selector':'main','visible':True}]}]
 audit.save(out/'config.json',cfg)
 assert audit.main(['page-audit','--url',url,'--config',str(out/'config.json'),'--mode','machine','--out',str(out/'run'),'--max-states','8','--max-steps','6','--max-depth','1'])==0
 run=audit.run_layout.ledger(out/'run')
 graph=audit.load(run/'exploration.json');labelled=[n for n in graph['nodes'] if n.get('state_labels')]
 assert len(labelled)==1 and labelled[0]['state_labels']==['loaded-via-key'],labelled
 assert labelled[0]['route']==cfg['exploration_labels'][0]['actions']
 assert any(n['fingerprint']==labelled[0]['fingerprint'] and n['route']!=labelled[0]['route'] for n in graph['nodes'])
 assert all(any('未到達の指定状態：'+name==r for r in graph['remaining']) for name in ['wrong-count','protected-submit'])
 evidence=run/labelled[0]['evidence_dir']
 assert len(audit.load(evidence/'tiles.json')['positions'])>1
 assert any(rule['id']=='image-alt' and any(node['target']==['#subject'] for node in rule['nodes'])
            for rule in audit.load(evidence/'axe.json')['violations'])
 assert Handler.writes==0
 audit.save(out/'observed.json',{'labelled_nodes':labelled,'nodes':graph['nodes'],'remaining':graph['remaining'],'post_requests_received':Handler.writes,'wcag_outcomes':audit.outcomes(run)['counts']})
 print('Exact routes, observable assertions, repeated UI capture and submission protection confirmed.')
finally:server.shutdown();server.server_close()
