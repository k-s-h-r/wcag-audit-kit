"""Verify preserved evidence and active document links without mutating sources."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));from benchmarks import core,runner
record=Path(sys.argv[1]);record.mkdir(parents=True,exist_ok=False)
base=subprocess.check_output(['git','ls-tree','-r','origin/main','validation'],cwd=ROOT,text=True).splitlines()
for line in base:
 mode,kind,ident,path=line.split(maxsplit=3);data=(ROOT/path).read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==ident,path
count=0;manifests=[]
for m in sorted((ROOT/'validation/development').rglob('*checksums.json')):
 if m.parent==record.resolve():continue
 for name,h in core.load(m).items():assert core.file_hash(m.parent/name)==h,(str(m),name);count+=1
 manifests.append(m.relative_to(ROOT).as_posix())
assert runner.implementation_digest()==core.load(ROOT/'validation/development/T007/inventory-001/context.json')['implementation_digest']
assert core.corpus()['digest']=='c27eb953840655e3bdac2bfd751a6d25c289ed1f5039eb7e08ff86c9dee4686a'
missing=[];historical=[];checked=0
for file in [ROOT/'README.md',*(ROOT/'docs').rglob('*.md'),ROOT/'validation/development/README.md']:
 for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',file.read_text()):
  if '://' in link or link.startswith(('#','mailto:')):continue
  dest=link.split('#',1)[0].strip('<>')
  if not dest:continue
  checked+=1
  if not (file.parent/dest).exists():
   if file.relative_to(ROOT).as_posix()=='docs/adr/0004-human-checksheet.md' and link=='../../references/checksheet.md':
    assert file.read_bytes()==subprocess.check_output(['git','show','origin/main:docs/adr/0004-human-checksheet.md'],cwd=ROOT)
    historical.append({'file':str(file.relative_to(ROOT)),'link':link,'reason':'Existing ADR retains historical layout; unchanged from main','current_target':'skills/wcag-audit-kit/references/checksheet.md'})
   else:missing.append([str(file.relative_to(ROOT)),link])
assert not missing,missing
core.save(record/'integrity.json',{'main_commit':subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip(),'main_validation_files_unchanged':len(base),'local_checksum_entries_unchanged':count,'manifests':manifests,'local_markdown_links_checked':checked,'active_missing_links':missing,'preexisting_historical_links':historical,'implementation_digest':runner.implementation_digest(),'corpus_digest':core.corpus()['digest'],'ai_evaluation_performed':False,'integrated_site_acceptance_performed':False,'main_merges_performed':False})
print(json.dumps({'main_validation_files_unchanged':len(base),'local_checksum_entries_unchanged':count,'links_checked':checked,'active_missing_links':len(missing),'historical_links':len(historical)}))
