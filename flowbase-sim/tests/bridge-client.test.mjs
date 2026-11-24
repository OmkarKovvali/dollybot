import test from 'node:test';
import assert from 'node:assert/strict';
import {SimulatorBridge} from '../dist/bridge-client.mjs';
globalThis.document={hidden:false};
const job={id:'client-test-shot',shot:{kind:'dolly',radius:2.5,distance:.8,duration:8},status:'delivered'};
function fixture(){
  let mode='idle',executions=0,client;
  const api={getState:()=>({mode,modelReady:true,elapsed_s:0,pose:{x:-2.5,y:0,yaw:0}}),stop:()=>{mode='idle';client.interrupt('Stopped');},executeShot:()=>{executions++;mode='shot';},executeMotion:()=>{executions++;mode='shot';}};
  client=new SimulatorBridge({api,onStatus:()=>{},onJob:()=>{},onDisconnect:()=>{}});
  client.running=true;client.instance='instance';
  return {client,setMode:m=>mode=m,get executions(){return executions;},get mode(){return mode;}};
}
const response=()=>({role:'controller',instance:'instance',stop_epoch:0,job,last_job:job});
test('general motion is delivered once and acknowledged through the same lifecycle',async()=>{
  const f=fixture(),motionJob={id:'client-motion-001',motion:{kind:'drive',vx:1,duration:1},start_pose:{x:-2.5,y:0,yaw:0},status:'delivered'};
  f.client.request=async()=>({...response(),job:motionJob,last_job:motionJob});await f.client.poll();
  assert.equal(f.executions,1);assert.equal(f.client.pending.status,'running');await f.client.poll();assert.equal(f.executions,1);
});
test('a late poll cannot execute after disconnect',async()=>{
  const f=fixture();let deliver;
  f.client.request=async(route,data)=>data?.release?{role:'disconnected'}:new Promise(r=>{deliver=r;});
  const poll=f.client.poll();await f.client.disconnect();deliver(response());await poll;
  assert.equal(f.executions,0);assert.equal(f.mode,'idle');assert.equal(f.client.running,false);
});
test('manual takeover while a delivery is in flight cancels the delivery',async()=>{
  const f=fixture();let deliver;f.client.request=()=>new Promise(r=>{deliver=r;});
  const poll=f.client.poll();f.setMode('manual');f.client.interrupt('Manual takeover');deliver(response());await poll;
  assert.equal(f.executions,0);assert.equal(f.mode,'manual');assert.equal(f.client.pending.status,'cancelled');
});
test('transport failure preserves cancellation for a fast reconnect',async()=>{
  const f=fixture();f.client.activeJob=job;f.client.seen.add(job.id);f.setMode('shot');
  f.client.request=async()=>{throw new Error('Transient failure');};await f.client.poll();
  assert.equal(f.client.pending.status,'cancelled');assert.equal(f.mode,'idle');
  let deliveredUpdate;
  f.client.request=async(route,data)=>{
    if(route.endsWith('/session'))return {simulation_only:true,token:'test',instance:'instance'};
    if(data?.release)return {role:'disconnected'};
    deliveredUpdate=data.update;return {...response(),job:null,last_job:{...job,status:'cancelled'}};
  };
  await f.client.connect('');assert.equal(deliveredUpdate.status,'cancelled');assert.equal(f.executions,0);assert.equal(f.client.activeJob,null);
  await f.client.disconnect();
});
