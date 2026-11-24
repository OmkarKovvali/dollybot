import test from 'node:test';
import assert from 'node:assert/strict';
import {Simulator,integratePose,makePlan,advanceCasters,exportPlan,LIMITS} from '../dist/sim-core.mjs';
const near=(a,b,e=1e-6)=>assert.ok(Math.abs(a-b)<e,`${a} != ${b}`);
test('body frame translation follows yaw; exact curved integration',()=>{
  const p=integratePose({x:0,y:0,yaw:Math.PI/2},[1,0,0],1); near(p.x,0);near(p.y,1);
  const q=integratePose({x:0,y:0,yaw:0},[1,0,1],Math.PI/2);near(q.x,1);near(q.y,1);
});
test('shot ends at expected angle, holds subject, eases to rest',()=>{
  const p=makePlan({kind:'orbit',radius:2,duration:20,sweepDeg:90});assert.ok(p.valid);
  near(p.sample(20).x,0);near(p.sample(20).y,-2);near(p.sample(20).yaw,Math.PI/2);
  assert.ok(Math.hypot(...p.velocityAt(20))<1e-6);
});
test('rejects fast moves and paths entering subject',()=>{
  assert.equal(makePlan({duration:2}).valid,false);
  assert.equal(makePlan({kind:'dolly',radius:1.2,distance:1,duration:20}).valid,false);
  assert.throws(()=>makePlan({duration:NaN}));
});
test('manual takeover cancels shot and stop cannot resume it',()=>{
  const s=new Simulator();s.play(makePlan({}));s.tick(.1);s.manual([.2,0,0]);
  assert.equal(s.plan,null);s.stop();const p={...s.pose};s.tick(.1);assert.deepEqual(s.pose,p);
});
test('manual diagonal speed and acceleration are bounded',()=>{
  const s=new Simulator();s.manual([1,1,10]);s.tick(.1);
  near(Math.hypot(s.velocity[0],s.velocity[1]),LIMITS.acceleration*.1);
  assert.ok(Math.hypot(s.target[0],s.target[1])<=LIMITS.linear+1e-8);
});
test('clearance zone stops a manual move before reaching subject',()=>{
  const s=new Simulator();s.reset({x:-.81,y:0,yaw:0});s.manual([.5,0,0]);
  for(let i=0;i<100;i++)s.tick(.01);assert.ok(s.pose.x<=-.8);assert.ok(s.blocked);near(s.velocity[0],0);
});
test('caster equations are stable and forward travel spins wheels',()=>{
  const a=[0,0,0,0],d=[0,0,0,0];advanceCasters(a,d,[.5,0,0],1);
  a.forEach(v=>near(v,0));d.forEach(v=>near(v,10));
  advanceCasters(a,d,[0,.5,.3],1);assert.ok([...a,...d].every(Number.isFinite));
});
test('export is complete, finite, and explicitly simulation-only',()=>{
  const e=exportPlan(makePlan({}));assert.equal(e.simulation_only,true);
  assert.equal(e.samples.at(-1).t_s,16);assert.deepEqual(e.samples.at(-1).body_velocity,[0,0,0]);
  assert.ok(!JSON.stringify(e).includes('null'));
});
