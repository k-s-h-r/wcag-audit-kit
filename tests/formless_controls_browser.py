"""Check an immediate, formless action and retain genuine submission deferrals."""
import argparse,functools,json,sys,threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'skills/wcag-audit-kit/scripts'))
import audit
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
class Handler(SimpleHTTPRequestHandler):
 writes=0
 def log_message(self,*args):pass
 def do_POST(self):type(self).writes+=1;self.send_error(500)
http=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT/'tests/fixtures')));threading.Thread(target=http.serve_forever,daemon=True).start()
try:
 url=f'http://127.0.0.1:{http.server_port}/formless-controls.html';cfg=audit.init_config(url);cfg['environments']=cfg['environments'][:1];cfg['keyboard_steps']=4;audit.save(out/'config.json',cfg)
 assert audit.main(['page-audit','--url',url,'--config',str(out/'config.json'),'--mode','machine','--out',str(out/'run'),'--max-states','8','--max-steps','16','--max-depth','2'])==0
 graph=audit.load(out/'run/exploration.json');initial=next(n for n in graph['nodes'] if not n['route']);deferred={x['selector'] for x in initial.get('deferred',[])}
 found=[]
 for n in graph['nodes']:
  raw=audit.load(out/'run'/n['evidence_dir']/'axe.json')
  if any(r['id']=='image-alt' and any(x['target']==['#subject'] for x in r['nodes']) for r in raw['violations']):found.append(n['route'])
 value={'initial_controls':initial['controls'],'initial_deferred':sorted(deferred),'image_failure_routes':found,'post_requests_received':Handler.writes,'wcag_outcomes':audit.outcomes(out/'run')['counts']}
 audit.save(out/'observed.json',value)
 assert '#load' not in deferred and found,value
 assert {'#inside-submit','#external-submit','#save'}<=deferred,value
 assert Handler.writes==0 and set(value['wcag_outcomes'])=={'not_run'},value
 print(json.dumps({'states':len(graph['nodes']),'image_failure_routes':len(found),'protected_controls':len(deferred),'post_requests':Handler.writes}))
finally:http.shutdown();http.server_close()
