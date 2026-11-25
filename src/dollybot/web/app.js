const $ = id => document.getElementById(id);
const ws = new WebSocket(`ws://${location.host}/control`);
let held = false, recordingAt = null;
const send = data => { if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({...data,time:Date.now()})); };
function notice(text, error=false) { $('notice').textContent=text; $('notice').classList.toggle('error',error); $('activity').textContent=`${new Date().toLocaleTimeString()} ${text}\n`+$('activity').textContent.slice(0,6000); }
function stop() { held=false; document.querySelectorAll('.held').forEach(b=>b.classList.remove('held')); send({action:'stop'}); }
function move(action,values,button) { if(held)return; held=true;button?.classList.add('held');send({action,...values}); }
ws.onopen=()=>{ $('connection').textContent='Console online';$('connection').classList.add('online'); };
ws.onclose=()=>{ $('connection').textContent='Console disconnected';$('connection').classList.remove('online');notice('Console disconnected. Motion stop attempted; reload to reconnect.',true); };
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.error)notice(m.error,true);if(m.message)notice(m.message);if(m.state){const s=m.state;for(const name of ['base','gimbal','camera']){const on=name==='camera'?s.camera_connected:s[name].connected;$(name+'-status').textContent=on?'Connected':'Disconnected';$(name+'-status').classList.toggle('online',on);}const rec=s.camera.recording===true;$('record-state').textContent=rec?'Recording on iPhone':s.camera_connected?'Ready to record':'Camera offline';$('record-dot').classList.toggle('on',rec);if(rec&&recordingAt===null)recordingAt=Date.now();if(!rec)recordingAt=null;$('record-start').disabled=!s.camera_connected||rec;$('record-stop').disabled=!s.camera_connected;}
if(m.motion_done)notice('Motion finished. Release and press again to continue.');if(m.clip){const c=m.clip;$('clip').textContent=`Saved original clip\n${c.video.width} × ${c.video.height} · ${c.video.average_fps.toFixed(2)} FPS · ${c.video.codec}
${c.video.duration_seconds.toFixed(2)} seconds\nStop → saved: ${c.stop_to_clip_ms} ms\n${c.path}`;} };
setInterval(()=>{if(!document.hidden)send({action:'heartbeat'});if(recordingAt!==null){const t=Math.floor((Date.now()-recordingAt)/1000);$('timer').textContent=`${String(Math.floor(t/60)).padStart(2,'0')}:${String(t%60).padStart(2,'0')}`;}},75);
$('stop').onclick=stop;
document.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>{notice('Connecting…');send({action:b.dataset.action});});
$('camera-connect').onclick=()=>{notice('Connecting Moblin…');send({action:'camera_connect',url:$('camera-url').value});};
$('record-start').onclick=()=>{notice('Starting recording…');send({action:'record_start'});};
$('record-stop').onclick=()=>{notice('Stopping recording and downloading original clip…');send({action:'record_stop'});};
document.querySelectorAll('[data-base],[data-gimbal]').forEach(b=>{b.onpointerdown=e=>{e.preventDefault();b.setPointerCapture(e.pointerId);if(b.dataset.base){const [forward,left,yaw]=b.dataset.base.split(',').map(Number);move('base_move',{forward,left,yaw},b);}else{const [pan,tilt]=b.dataset.gimbal.split(',').map(Number);move('gimbal_move',{pan,tilt},b);}};b.onpointerup=stop;b.onpointercancel=stop;b.onlostpointercapture=()=>{if(held)stop();};});
const keys={KeyW:[.08,0,0],KeyS:[-.08,0,0],KeyA:[0,.08,0],KeyD:[0,-.08,0],KeyQ:[0,0,.15],KeyE:[0,0,-.15]};
window.addEventListener('keydown',e=>{if(e.code==='Space'&&e.target.tagName!=='INPUT'){e.preventDefault();stop();return;}if(e.target.tagName==='INPUT'||e.repeat||!e.shiftKey||!keys[e.code])return;e.preventDefault();const [forward,left,yaw]=keys[e.code];move('base_move',{forward,left,yaw});});
window.addEventListener('keyup',e=>{if(keys[e.code]||e.key==='Shift')stop();});
window.addEventListener('blur',stop);document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});window.addEventListener('pagehide',stop);
