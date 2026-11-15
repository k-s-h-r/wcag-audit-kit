const video=document.querySelector('#clip');
document.querySelector('#play').addEventListener('click',()=>{if(video.paused)video.play();else video.pause()});
video.addEventListener('play',()=>document.querySelector('#play').textContent='Pause video');
video.addEventListener('pause',()=>document.querySelector('#play').textContent='Play video');
document.querySelector('#captions').addEventListener('click',()=>{
 const showing=video.textTracks[0].mode!=='showing';
 video.textTracks[0].mode=showing?'showing':'hidden';
 document.querySelector('#captions').setAttribute('aria-pressed',String(showing));
 document.querySelector('#caption-state').textContent=showing?'On':'Off';
});
