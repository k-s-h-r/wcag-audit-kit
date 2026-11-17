"""Exercise existing live-region controls, without a WCAG verdict or oracle."""
import hashlib,json,shutil,sys,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));from benchmarks import core
from benchmarks.native_status import capture
root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=False)
public=out/'public';public.mkdir();source=ROOT/'tests/fixtures/live-region-variants.html';shutil.copyfile(source,public/'controls.html')
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(public)));threading.Thread(target=server.serve_forever,daemon=True).start()
# Whole route fixed before capture: first implicit status, then explicit live.
actions=[]
for number,word in [(1,'one'),(2,'two'),(3,'three'),(4,'four'),(5,'five')]:
 actions.extend([{'type':'reader.press','keys':['Tab'],'expect_contains':'Save record '+word},{'type':'reader.press','keys':['space']}])
request={'case_id':'T012-existing-live-controls','url':f'http://127.0.0.1:{server.server_port}/controls.html','locale':'en-US','settle_ms':3000,'observe':[{'selector':f'#message{n}'} for n in range(1,6)],'actions':actions}
core.save(out/'request.json',request);core.save(out/'plan.json',{'source_sha256':core.file_hash(source),'purpose':'diagnose real speech with implicit/explicit live and silent controls; no WCAG judgement','input':'native XTest through reader.press, focus and visible state required'})
try:capture(root,out)
finally:server.shutdown();server.server_close()
v=core.load(out/'speech/screen-reader.json');observed=[{'index':r['index'],'action':r['action'],'focus_after':r.get('focus_after'),'speech':[s['phrase'] for s in r.get('speech',[])],'observations':r.get('observations',[])} for r in v.get('observations',[])]
core.save(out/'observed.json',{'status':v['status'],'error':v.get('error'),'environment':v.get('environment'),'steps':observed,'wcag_judgement':None});print(json.dumps(observed,ensure_ascii=False))
