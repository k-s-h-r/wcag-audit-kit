const mode=document.body.dataset.profile;
const root=document.querySelector('#level1'),child=document.querySelector('#level2');
const second=document.querySelector('#level2-panel'),third=document.querySelector('#level3-panel');
const close=document.querySelector('#close'),after=document.querySelector('#after');
function closeThird(){third.hidden=true;child.setAttribute('aria-expanded','false')}
function closeAll(){closeThird();second.hidden=true;root.setAttribute('aria-expanded','false');close.hidden=true}
root.addEventListener('click',()=>{if(!second.hidden){closeAll()}else{second.hidden=false;root.setAttribute('aria-expanded','true');close.hidden=false}});
child.addEventListener('click',()=>{if(!third.hidden){closeThird()}else{third.hidden=false;child.setAttribute('aria-expanded','true');if(mode==='m04')after.focus()}});
close.addEventListener('click',()=>{closeAll();root.focus()});
if(mode==='m03')close.tabIndex=-1;
document.querySelector('#navigation').addEventListener('keydown',event=>{
 if(mode==='m03'&&!third.hidden&&third.contains(document.activeElement)){
  if(event.key==='Tab'){
   event.preventDefault();const links=[...third.querySelectorAll('a')];const at=links.indexOf(document.activeElement);
   links[(at+(event.shiftKey?-1:1)+links.length)%links.length].focus();return;
  }
  if(['Escape','Enter',' '].includes(event.key)){
   event.preventDefault();event.stopPropagation();return;
  }
 }
 if(event.key==='Escape'){
  if(!third.hidden){event.preventDefault();closeThird();child.focus()}
  else if(!second.hidden){event.preventDefault();closeAll();root.focus()}
 }
});
