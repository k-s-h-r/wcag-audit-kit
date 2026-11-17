"""Download verified Debian packages to a private root; no system installation."""
import concurrent.futures,hashlib,json,os,platform,shutil,subprocess,sys,urllib.request
from pathlib import Path
root=Path(sys.argv[1]);record=Path(sys.argv[2]);record.mkdir(parents=True,exist_ok=False);root.mkdir(parents=True,exist_ok=False)
repo=Path(__file__).resolve().parents[3];manifest=json.loads((repo/'validation/native-orca/run-005/package-manifest.json').read_text());downloads=root/'downloads';downloads.mkdir()
(record/'before.json').write_text(json.dumps({'os':Path('/etc/os-release').read_text(),'kernel':platform.release(),'executables':{n:shutil.which(n) for n in ['orca','Xvfb','speech-dispatcher','espeak-ng','dbus-run-session']},'source_manifest_sha256':hashlib.sha256((repo/'validation/native-orca/run-005/package-manifest.json').read_bytes()).hexdigest()},indent=2))
def acquire(pair):
 name,package=pair;attempts=[]
 for mirror in ['https://deb.debian.org/debian/','https://security.debian.org/debian-security/','https://deb.debian.org/debian-security/']:
  url=mirror+package['Filename']
  try:
   with urllib.request.urlopen(url,timeout=30) as response:data=response.read()
   digest=hashlib.sha256(data).hexdigest()
   if digest!=package['SHA256']:raise ValueError('package SHA256 differs')
   target=downloads/Path(package['Filename']).name;target.write_bytes(data)
   return name,dict(package,status='verified',url=url,attempts=attempts,size=len(data))
  except Exception as error:attempts.append({'url':url,'error':str(error)})
 return name,dict(package,status='unavailable',attempts=attempts)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:results=dict(pool.map(acquire,manifest.items()))
(record/'downloads.json').write_text(json.dumps(results,indent=2))
if all(v['status']=='verified' for v in results.values()):
 for name,package in results.items():subprocess.run(['dpkg-deb','-x',str(downloads/Path(package['Filename']).name),str(root)],check=True)
 (root/'package-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'verified':sum(v['status']=='verified' for v in results.values()),'unavailable':[k for k,v in results.items() if v['status']!='verified'],'root':str(root)}))
