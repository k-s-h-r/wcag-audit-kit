'use strict';
const $=selector=>document.querySelector(selector);
async function api(path,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});return {status:r.status,data:await r.json()};}
if($('#sign-out'))$('#sign-out').addEventListener('click',async()=>{await api('/api/logout',{});location.reload();});
if($('#count-button')){
 let count=0;$('#count-button').addEventListener('click',()=>$('#count').textContent=String(++count));
 $('#about').addEventListener('click',()=>$('#about-dialog').showModal());
 $('#close-about').addEventListener('click',()=>$('#about-dialog').close());
}
if($('#profile-form')){
 const saved=JSON.parse(localStorage.getItem('demo-profile')||'{"name":"Demo User","email":"demo@example.test"}');
 $('#name').value=saved.name;$('#email').value=saved.email;
 function panel(id){for(const target of ['editor','review-panel','completion'])$('#'+target).hidden=target!==id;}
 $('#profile-form').addEventListener('submit',e=>{
  e.preventDefault();const errors=[];
  for(const [id,invalid,message] of [['name',!$('#name').value.trim(),'Enter a name.'],['email',!$('#email').validity.valid,'Enter an email such as name@example.test.']]){
   $('#'+id).setAttribute('aria-invalid',String(invalid));$('#'+id+'-error').hidden=!invalid;$('#'+id+'-error').textContent=invalid?message:'';
   if(invalid)errors.push({id,message});
  }
  $('#error-list').replaceChildren(...errors.map(error=>{const li=document.createElement('li'),a=document.createElement('a');a.href='#'+error.id;a.textContent=error.message;li.append(a);return li;}));
  $('#errors').hidden=errors.length===0;
  if(errors.length){$('#errors').focus();return;}
  $('#review-name').textContent=$('#name').value;$('#review-email').textContent=$('#email').value;
  panel('review-panel');$('#review-title').focus();
 });
 $('#back').addEventListener('click',()=>{panel('editor');$('#name').focus();});
 $('#confirm').addEventListener('click',async()=>{
  const values={name:$('#name').value,email:$('#email').value};const r=await api('/api/profile',values);
  if(r.status!==200)throw new Error('Expected an authenticated profile save');
  localStorage.setItem('demo-profile',JSON.stringify(r.data.saved));$('#saved-name').textContent=r.data.saved.name;$('#saved-email').textContent=r.data.saved.email;
  panel('completion');$('#saved-title').focus();
 });
}
if($('#login-form')){
 $('#show-password').addEventListener('click',()=>{const show=$('#password').type==='password';$('#password').type=show?'text':'password';$('#show-password').setAttribute('aria-pressed',String(show));});
 $('#login-form').addEventListener('submit',async e=>{
  e.preventDefault();const r=await api('/api/login',{email:$('#login-email').value,password:$('#password').value});
  $('#login-error').textContent=r.status===200?'':r.data.error;$('#login-status').textContent=r.status===200?'Signed in. Continue to profile.':'';
 });
}
if($('#clip')){
 const video=$('#clip');
 $('#play').addEventListener('click',async()=>{if(video.paused)await video.play();else video.pause();});
 video.addEventListener('play',()=>{$('#play').textContent='Pause video';$('#playback-state').textContent='Playing';});
 video.addEventListener('pause',()=>{$('#play').textContent='Play video';$('#playback-state').textContent=video.ended?'Ended':'Paused';});
 video.addEventListener('ended',()=>{$('#play').textContent='Play video';$('#playback-state').textContent='Ended';});
 $('#captions-toggle').addEventListener('click',()=>{const track=video.textTracks[0];track.mode=track.mode==='showing'?'hidden':'showing';$('#captions-toggle').setAttribute('aria-pressed',String(track.mode==='showing'));});
}
