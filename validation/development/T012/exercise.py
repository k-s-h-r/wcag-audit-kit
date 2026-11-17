"""Run the existing answer-free native status worker in a fresh SR-only run."""
import argparse,json,subprocess,sys,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));from benchmarks import core,runner
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--record',type=Path,required=True);a=p.parse_args();a.record.mkdir(parents=True,exist_ok=False)
core.save(a.record/'plan.json',{'criterion':'4.1.3','checkpoint':'4.1.3-02','mode':'screen-reader','worker':'benchmarks/native_status.py','pages':['p01.html','p02.html'],'method':'existing public-task worker, real Orca; contrast calibration required before interpreting silent negative','implementation_digest':runner.implementation_digest(),'environment':runner.environment(),'private_root':str(a.root),'no_ai_inference':True})
meta,http=runner.prepare(a.out,['4.1.3'],['screen-reader']);http.shutdown();http.server_close()
start=time.monotonic();cmd=[sys.executable,'benchmarks/native_status.py','--run',str(a.out),'--root',str(a.root),'--import-results'];result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=180)
(a.record/'stdout.txt').write_text(result.stdout);(a.record/'stderr.txt').write_text(result.stderr)
strict=subprocess.run([sys.executable,'benchmarks/run.py','score','--run',str(a.out),'--strict'],cwd=ROOT,text=True,capture_output=True)
(a.record/'strict.stdout.txt').write_text(strict.stdout);(a.record/'strict.stderr.txt').write_text(strict.stderr)
core.save(a.record/'receipt.json',{'command':cmd,'exit_code':result.returncode,'strict_exit_code':strict.returncode,'elapsed_seconds':time.monotonic()-start,'implementation_digest':meta['implementation_digest'],'corpus_digest':meta['corpus_digest'],'ai_inference':False})
with zipfile.ZipFile(a.record/'run.zip','x',zipfile.ZIP_DEFLATED) as archive:
 for src in sorted(a.out.rglob('*')):
  if src.is_file() and src.name!='.audit.lock':archive.write(src,src.relative_to(a.out))
print(json.dumps({'worker_exit_code':result.returncode,'strict_exit_code':strict.returncode,'stdout':result.stdout},ensure_ascii=False))
