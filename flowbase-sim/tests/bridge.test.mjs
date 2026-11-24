import test from 'node:test';
import assert from 'node:assert/strict';
import {BridgeState,validateShot} from '../bridge/state.mjs';
import {makePlan} from '../dist/sim-core.mjs';
import {startBridge} from '../bridge/server.mjs';
const id='viewer-test-001',request_id='test-shot-0001';
const shot={kind:'dolly',radius:2.5,distance:.8,duration:8};
const viewer=(s,extra={})=>s.viewerTick({client_id:id,ready:true,...extra});
test('no job is accepted without a ready browser',()=>{
  const s=new BridgeState();assert.throws(()=>s.submit({request_id,shot}),/Open http/);
  s.viewerTick({client_id:id,ready:false});assert.throws(()=>s.submit({request_id,shot}),/Open http/);
});
test('submission is idempotent and refuses conflicting retries',()=>{
  const s=new BridgeState();viewer(s);const first=s.submit({request_id,shot});
  assert.equal(s.submit({request_id,shot}),first);assert.equal(s.jobs.size,1);
  assert.throws(()=>s.submit({request_id,shot:{...shot,duration:10}}),/different shot/);
});
test('only the owning viewer can acknowledge a job',()=>{
  const s=new BridgeState();viewer(s);s.submit({request_id,shot});
  const wrong=s.viewerTick({client_id:'another-viewer',ready:true,update:{id:request_id,status:'completed'}});
  assert.equal(wrong.role,'observer');assert.equal(s.status(request_id).status,'queued');
});
test('completion requires running state and the actual final pose',()=>{
  const s=new BridgeState();viewer(s);s.submit({request_id,shot});viewer(s);
  viewer(s,{update:{id:request_id,status:'completed'}});assert.equal(s.status(request_id).status,'delivered');
  viewer(s,{update:{id:request_id,status:'running'}});
  viewer(s,{update:{id:request_id,status:'completed'},telemetry:{pose:makePlan(shot).sample(8),mode:'complete',elapsed_s:8}});
  assert.equal(s.status(request_id).status,'completed');assert.equal(s.active,null);
});
test('wrong final pose fails rather than claiming success',()=>{
  const s=new BridgeState();viewer(s);s.submit({request_id,shot});viewer(s,{update:{id:request_id,status:'running'}});
  viewer(s,{update:{id:request_id,status:'completed'},telemetry:{pose:{x:9,y:9,yaw:0},elapsed_s:8}});
  assert.equal(s.status(request_id).status,'failed');
});
test('disconnect fails a running job and cannot replay it',()=>{
  let clock=0;const s=new BridgeState({now:()=>clock});viewer(s);s.submit({request_id,shot});viewer(s,{update:{id:request_id,status:'running'}});
  clock=6000;s.sweep();assert.equal(s.status(request_id).status,'failed');
  assert.equal(viewer(s).job,null);assert.equal(s.submit({request_id,shot}).status,'failed');
});
test('stop remains pending until the browser acknowledges cancellation',()=>{
  const s=new BridgeState();viewer(s);s.submit({request_id,shot});s.stop();
  assert.equal(s.status(request_id).status,'stopping');
  viewer(s,{update:{id:request_id,status:'running'}});assert.equal(s.status(request_id).status,'stopping');
  viewer(s,{update:{id:request_id,status:'cancelled',reason:'Stop requested'}});assert.equal(s.status(request_id).status,'cancelled');
});
test('unknown fields, invalid booleans, unsafe paths, and fast shots are rejected',()=>{
  assert.throws(()=>validateShot({...shot,host:'robot'}),/Unknown/);
  assert.throws(()=>validateShot({...shot,faceSubject:'false'}),/boolean/);
  assert.throws(()=>validateShot({...shot,radius:1.2,distance:1}),/clearance/);
  assert.throws(()=>validateShot({kind:'orbit',duration:4}),/at least/);
});
test('HTTP service authenticates commands and rejects foreign origins',async()=>{
  const b=await startBridge({port:0,runtime:false});
  try{
    let r=await fetch(b.url+'/api/state');assert.equal(r.status,401);
    r=await fetch(b.url+'/api/bridge/session',{headers:{Origin:'https://unrelated.example'}});assert.equal(r.status,403);
    r=await fetch(b.url+'/api/bridge/session');const session=await r.json();assert.equal(session.simulation_only,true);
    r=await fetch(b.url+'/api/state',{headers:{Authorization:`Bearer ${session.token}`}});assert.equal(r.status,200);assert.equal((await r.json()).viewer_connected,false);
    r=await fetch(b.url+'/../bridge/server.mjs');assert.equal(r.status,404);
    r=await fetch(b.url+'/');assert.equal(r.status,200);assert.match(await r.text(),/Direct from Kino chat/);
    const headers={Authorization:`Bearer ${session.token}`,'Content-Type':'application/json'};
    r=await fetch(b.url+'/api/capabilities',{headers});assert.equal((await r.json()).motion_limits,null);
    r=await fetch(b.url+'/api/motions',{method:'POST',headers,body:JSON.stringify({request_id:'http-motion-001',motion:{kind:'drive',vx:2,duration:1}})});assert.equal(r.status,409);
    await fetch(b.url+'/api/bridge/viewer',{method:'POST',headers,body:JSON.stringify({client_id:'http-viewer-001',ready:true,telemetry:{pose:{x:0,y:0,yaw:0},mode:'idle',elapsed_s:0}})});
    r=await fetch(b.url+'/api/motions',{method:'POST',headers,body:JSON.stringify({request_id:'http-motion-001',motion:{kind:'drive',vx:20,duration:1}})});assert.equal(r.status,202);assert.equal((await r.json()).expected_pose.x,20);
  }finally{await b.close();}
});
