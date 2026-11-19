"""Owned browser calibration. Does not claim a full WCAG audit or image understanding."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/wcag-audit-kit/scripts'))
import audit


def exercise(out,skill_root=None):
    skill_root=Path(skill_root or ROOT/'skills/wcag-audit-kit').resolve()
    if out.exists():raise ValueError('新しい検証出力先を指定する')
    out.mkdir(parents=True);requests=[];commands=[]
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path);super().do_GET()
        def log_message(self,*args):pass
    handler=functools.partial(Handler,directory=str(ROOT/'tests/fixtures'))
    server=ThreadingHTTPServer(('127.0.0.1',0),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base='http://127.0.0.1:'+str(server.server_port)
    url=base+'/visual-controls.html'
    def command(name,args):
        result=subprocess.run([sys.executable,str(skill_root/'scripts/audit.py'),*args],cwd=skill_root,capture_output=True,text=True)
        (out/(name+'.stdout.txt')).write_text(result.stdout);(out/(name+'.stderr.txt')).write_text(result.stderr)
        commands.append({'name':name,'args':args,'returncode':result.returncode})
        if result.returncode:raise RuntimeError(result.stderr)
    config=audit.init_config(base)
    config['environments']=config['environments'][:1];config['keyboard_steps']=4
    config['states']=[
        {'id':'preferences','paths':['/visual-controls.html'],'actions':[
            {'type':'click','selector':'#preferences-trigger'},
            {'type':'press','key':'Escape','assert':[{'selector':'#preferences','visible':False}]},
            {'type':'click','selector':'#preferences-trigger'}],
         'assert':[{'selector':'#preferences','visible':True}]},
        {'id':'help','paths':['/visual-controls.html'],'actions':[
            {'type':'click','selector':'#help-trigger'},
            {'type':'press','key':'Escape','assert':[{'selector':'#help','visible':False}]},
            {'type':'press','key':'Enter'}],
         'assert':[{'selector':'#help','visible':True}]},
        {'id':'nested','paths':['/visual-controls.html'],'actions':[
            {'type':'click','selector':'#help-trigger'}, {'type':'click','selector':'#more'},
            {'type':'press','key':'Escape','assert':[{'selector':'#nested','visible':False}]},
            {'type':'press','key':'Space'}],
         'assert':[{'selector':'#nested','visible':True}]}]
    path=out/'config.json';audit.save(path,config)
    try:
        command('standard',['page','--url',url,'--config',str(path),'--out',str(out/'standard'),
                            '--profile','standard','--max-images','3','--screen-reader','off'])
        standard_requests=list(requests);requests.clear()
        standard=audit.run_layout.ledger(out/'standard')
        manifest=audit.load(standard/'capture-manifest.json')
        assert len(manifest['captures'])==4 and all(c['execution']=='completed' for c in manifest['captures'])
        assert len(list((out/'standard').rglob('*.png')))==3
        assert not any('visual-linked.html' in p for p in standard_requests)
        assert any(i.get('reason')=='image_limit' for i in manifest['inspection']['screenshots'])
        initial=next(c for c in manifest['captures'] if c['state']=='initial')
        inventory=audit.load(standard/initial['evidence_dir']/'inventory.json')
        div=next(n for n in inventory['nodes'] if n['id']=='preferences-trigger')
        assert div['tag']=='div' and div['role'] is None and div['tabIndex']==-1
        keyboard=audit.load(standard/initial['evidence_dir']/'keyboard.json')
        assert all(e['focus']['id']!='preferences-trigger' for e in keyboard)
        help_capture=next(c for c in manifest['captures'] if c['state']=='help')
        actions=audit.load(standard/help_capture['evidence_dir']/'actions.json')
        assert actions[1]['focus']['id']=='help-trigger' and actions[1]['action_asserted']
        assert actions[2]['focus']['id']=='more'
        config['states']=[];audit.save(path,config)
        for profile,limit,expected in [('quick','0',0),('thorough','2',2)]:
            command(profile,['page','--url',url,'--config',str(path),'--out',str(out/profile),
                             '--profile',profile,'--max-images',limit])
            assert len(list((out/profile).rglob('*.png')))==expected
            assert not audit.outcomes(audit.run_layout.ledger(out/profile))['audit_complete']
        requests.clear();config['scope']['seeds']=['/visual-controls.html'];config['scope']['max_pages']=3;audit.save(path,config)
        command('discover',['pages','--config',str(path),'--out',str(out/'pages.json')])
        selection=audit.load(out/'pages.json')
        assert len(selection['pages'])==2 and any('visual-linked.html' in p for p in requests)
        result={'single_page_captures':4,'configured_did_not_follow_links':True,'standard_images':3,'quick_images':0,
                'thorough_images':2,'discovered_urls':2,'div_is_not_keyboard_reachable_in_trace':True,
                'help_escape_returns_to_trigger':True,'help_reopens_with_enter':True,
                'nested_image_skipped_by_budget':True,'real_screen_reader_executed':False,
                'image_meaning_review':'The operator must inspect the captured images; this script only checks observable facts.',
                'commands':commands,'skill_root':str(skill_root)}
        audit.save(out/'result.json',result);shutil.copyfile(__file__,out/'executed-source.py.txt')
        return result
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True)
    parser.add_argument('--skill-root',help='test a copied standalone skill instead of the repository runtime')
    args=parser.parse_args();print(json.dumps(exercise(Path(args.out).resolve(),args.skill_root),ensure_ascii=False,indent=2))
