import test from 'node:test';
import assert from 'node:assert/strict';
import {makeMotion,normalizeMotion,exportMotion} from '../dist/motion-core.mjs';
import {Simulator,makePlan} from '../dist/sim-core.mjs';
import {BridgeState,validateShot} from '../bridge/state.mjs';
const origin={x:0,y:0,yaw:0};
const near=(actual,expected)=>assert.ok(Math.abs(actual-expected)<1e-8,`${actual} != ${expected}`);

test('body drive combines holonomic translation and exact rotation',()=>{
 const p=makeMotion({kind:'drive',vx:1,vy:0,omega:Math.PI/2,duration:1},origin);
 const end=p.sample(1);near(end.x,2/Math.PI);near(end.y,2/Math.PI);near(end.yaw,Math.PI/2);
});
test('world drive keeps translation independent of heading',()=>{
 const p=makeMotion({kind:'drive',vx:2,vy:-3,omega:Math.PI,duration:2,frame:'world'},origin);
 assert.deepEqual(p.sample(2),{x:4,y:-6,yaw:Math.PI*2});
});
test('relative body displacement captures initial heading and preserves multi-turn yaw',()=>{
 const p=makeMotion({kind:'move',x:2,y:1,yaw:Math.PI*4,duration:2,frame:'body'},{x:3,y:4,yaw:Math.PI/2});
 near(p.sample(2).x,2);near(p.sample(2).y,6);near(p.sample(2).yaw,Math.PI*4.5);
 const absolute=makeMotion({kind:'move',relative:false,x:8,duration:2},{x:3,y:4,yaw:2});
 assert.deepEqual(absolute.sample(2),{x:8,y:4,yaw:2});
});
test('paths cross the subject and extend outside the original stage',()=>{
 const p=makeMotion({kind:'path',easing:'linear',waypoints:[{t:1,x:0,y:0,yaw:0},{t:2,x:10,y:10,yaw:Math.PI*4}]},{x:-2,y:0,yaw:0});
 assert.equal(p.valid,true);assert.deepEqual(p.sample(1),origin);assert.deepEqual(p.sample(2),{x:10,y:10,yaw:Math.PI*4});
});
test('repeated mixed commands start from the prior endpoint',()=>{
 const p=makeMotion({kind:'sequence',repeat:4,commands:[{kind:'move',x:2,frame:'body',duration:1},{kind:'move',yaw:Math.PI/2,duration:1}]},origin);
 near(p.sample(8).x,0);near(p.sample(8).y,0);near(p.sample(8).yaw,Math.PI*2);
 near(p.sample(1).x,2);near(p.sample(2).yaw,Math.PI/2);
});
test('teleport completes with zero duration and supports following moves',()=>{
 const p=makeMotion({kind:'pose',x:50,y:-20,yaw:6},origin),sim=new Simulator();sim.play(p);sim.tick(.01);
 assert.deepEqual(sim.pose,{x:50,y:-20,yaw:6});assert.equal(sim.mode,'complete');assert.equal(sim.elapsed,0);
 const seq=makeMotion({kind:'sequence',commands:[p.motion,{kind:'move',x:2,duration:1}]},origin);
 assert.deepEqual(seq.sample(1),{x:52,y:-20,yaw:6});
});
test('free presets and manual input bypass motion limits; constrained mode still validates',()=>{
 assert.equal(validateShot({kind:'orbit',radius:10,sweepDeg:1080,duration:2,unconstrained:true}).valid,true);
 assert.equal(makePlan({kind:'dolly',distance:-20,duration:.5,unconstrained:true}).valid,true);
 assert.throws(()=>validateShot({kind:'orbit',radius:10,duration:2}));
 const sim=new Simulator();sim.unconstrained=true;sim.reset({x:-.1,y:0,yaw:0});sim.manual([100,0,2]);sim.tick(.1);
 near(sim.velocity[0],100);assert.ok(sim.pose.x>4.5);assert.equal(sim.blocked,false);
});
test('invalid math and oversized/nested payloads are rejected without restricting ordinary motion',()=>{
 for(const input of [{kind:'drive',vx:Infinity,duration:1},{kind:'move',x:1,duration:0},{kind:'move',x:1,duration:1,relative:'yes'},{kind:'path',waypoints:[{t:1,x:0,y:0,yaw:0},{t:1,x:1,y:1,yaw:1}]},{kind:'sequence',repeat:1025,commands:[{kind:'pose',...origin}]},{kind:'sequence',commands:[{kind:'sequence',commands:[]}]}])assert.throws(()=>normalizeMotion(input));
});
test('long motions export a bounded number of samples',()=>{
 const p=makeMotion({kind:'drive',vx:1,duration:1e6},origin),out=exportMotion(p);
 assert.ok(out.samples.length<=5001);assert.equal(out.samples.at(-1).x,1e6);assert.equal(out.validation.constraints_enforced,false);assert.equal(out.simulation_only,true);
});
function ready(s,p=origin){return s.viewerTick({client_id:'motion-viewer',ready:true,telemetry:{pose:p,elapsed_s:0,mode:'idle'}});}
test('relative command retries keep their original start and completed commands never replay',()=>{
 const s=new BridgeState();ready(s);const input={request_id:'relative-test-1',motion:{kind:'move',x:3,duration:1}};
 const job=s.submitMotion(input);ready(s,{x:2,y:0,yaw:0});assert.equal(s.submitMotion(input),job);assert.equal(job.expected_pose.x,3);
 s.viewerTick({client_id:'motion-viewer',ready:true,update:{id:job.id,status:'running'}});
 s.viewerTick({client_id:'motion-viewer',ready:true,telemetry:{pose:job.expected_pose,elapsed_s:1,mode:'complete'},update:{id:job.id,status:'completed'}});
 assert.equal(s.submitMotion(input).status,'completed');assert.equal(s.active,null);
});
test('full turns must be confirmed, not merely equivalent wrapped yaw',()=>{
 const s=new BridgeState();ready(s);const job=s.submitMotion({request_id:'turns-test-001',motion:{kind:'move',yaw:Math.PI*4,duration:1}});
 s.viewerTick({client_id:'motion-viewer',ready:true,update:{id:job.id,status:'running'}});
 s.viewerTick({client_id:'motion-viewer',ready:true,telemetry:{pose:origin,elapsed_s:1,mode:'complete'},update:{id:job.id,status:'completed'}});
 assert.equal(s.status(job.id).status,'failed');
});
