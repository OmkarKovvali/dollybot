import {randomUUID} from 'node:crypto';
import {makePlan} from '../dist/sim-core.mjs';
import {makeMotion,normalizeMotion} from '../dist/motion-core.mjs';

export const TERMINAL = new Set(['completed','cancelled','failed']);
export class BridgeError extends Error {
  constructor(status,message){super(message);this.status=status;}
}
export function validateShot(input){
  if(!input||typeof input!=='object'||Array.isArray(input))throw new BridgeError(400,'shot must be an object');
  const allowed=new Set(['kind','radius','sweepDeg','distance','duration','faceSubject','unconstrained']);
  if(Object.keys(input).some(k=>!allowed.has(k)))throw new BridgeError(400,'Unknown shot field');
  if(input.faceSubject!==undefined&&typeof input.faceSubject!=='boolean')throw new BridgeError(400,'faceSubject must be boolean');
  let plan;try{plan=makePlan(input);}catch(e){throw new BridgeError(400,e.message);}
  const p=plan.params;
  if(!p.unconstrained&&(p.radius<1.2||p.radius>4||p.duration<4||p.duration>40||p.distance<.2||p.distance>3||Math.abs(p.sweepDeg)>180))throw new BridgeError(400,'Shot is outside the studio range: radius 1.2–4 m, duration 4–40 s, travel .2–3 m, sweep ±180°');
  if(!plan.valid)throw new BridgeError(422,plan.reason);
  return plan;
}
export class BridgeState {
  constructor({now=Date.now}={}){this.now=now;this.viewer=null;this.jobs=new Map();this.active=null;this.stopEpoch=0;this.instance=randomUUID();}
  sweep(){
    const n=this.now();
    if(this.viewer&&n-this.viewer.lastSeen>5000){this.finish('failed','Simulator disconnected before completion');this.viewer=null;}
    const j=this.active;
    if(j&&n-j.createdAt>j.duration*3000+30000){this.finish('failed','Simulator did not finish before the execution deadline');this.stopEpoch++;}
  }
  finish(status,reason){if(this.active){Object.assign(this.active,{status,status_reason:reason,finishedAt:this.now()});this.active=null;}}
  submit({request_id,shot,reason=''}){
    const plan=validateShot(shot),canonical=JSON.stringify({shot:plan.params,reason});
    return this.enqueue({request_id,reason,canonical,shot:plan.params,duration:plan.params.duration,expected_pose:plan.sample(plan.params.duration)});
  }
  submitMotion({request_id,motion,reason=''}){
    let normalized;try{normalized=normalizeMotion(motion);}catch(e){throw new BridgeError(400,e.message);}
    const canonical=JSON.stringify({motion:normalized,reason});
    const old=this.jobs.get(request_id);
    if(old){if(old.canonical!==canonical)throw new BridgeError(409,'request_id already belongs to a different motion');return old;}
    this.sweep();
    if(!this.viewer?.ready||!this.viewer.telemetry?.pose)throw new BridgeError(409,'Open http://127.0.0.1:8766 and wait for the simulator pose');
    let plan;try{plan=makeMotion(normalized,this.viewer.telemetry.pose);}catch(e){throw new BridgeError(400,e.message);}
    return this.enqueue({request_id,reason,canonical,motion:normalized,start_pose:plan.startPose,duration:plan.params.duration,expected_pose:plan.sample(plan.params.duration)});
  }
  enqueue({request_id,reason,canonical,...command}){
    this.sweep();
    if(typeof request_id!=='string'||! /^[a-zA-Z0-9_-]{8,100}$/.test(request_id))throw new BridgeError(400,'Use a stable request_id (8–100 letters, digits, _ or -)');
    if(typeof reason!=='string'||reason.length>500)throw new BridgeError(400,'reason must be a short string');
    const previous=this.jobs.get(request_id);
    if(previous){if(previous.canonical!==canonical)throw new BridgeError(409,'request_id already belongs to a different shot');return previous;}
    if(!this.viewer?.ready)throw new BridgeError(409,'Open http://127.0.0.1:8766 and wait for “Kino bridge connected” before requesting a shot');
    if(this.active)throw new BridgeError(409,'A shot is already active. Stop it or wait for its result.');
    const job={id:request_id,...command,reason,status:'queued',createdAt:this.now(),viewerId:this.viewer.id,canonical,simulation_only:true};
    this.jobs.set(job.id,job);this.active=job;
    while(this.jobs.size>100)this.jobs.delete(this.jobs.keys().next().value);
    return job;
  }
  stop(){this.sweep();this.stopEpoch++;if(this.active)this.active.status='stopping';return {stop_requested:true,job_id:this.active?.id||null,stop_epoch:this.stopEpoch,simulation_only:true};}
  viewerTick({client_id,ready,telemetry,update,release=false}){
    this.sweep();
    if(typeof client_id!=='string'||! /^[a-zA-Z0-9_-]{8,100}$/.test(client_id))throw new BridgeError(400,'Invalid client_id');
    if(release){if(this.viewer?.id===client_id){this.finish('cancelled','Viewer disconnected');this.viewer=null;}return {role:'disconnected'};}
    if(!this.viewer)this.viewer={id:client_id,lastSeen:this.now(),ready:false,telemetry:null};
    if(this.viewer.id!==client_id)return {role:'observer',instance:this.instance,stop_epoch:this.stopEpoch};
    this.viewer.lastSeen=this.now();this.viewer.ready=ready===true;
    if(telemetry&&typeof telemetry==='object'){
      const {pose,mode,elapsed_s}=telemetry;
      if(pose&&[pose.x,pose.y,pose.yaw,elapsed_s].every(Number.isFinite))this.viewer.telemetry={pose:{x:pose.x,y:pose.y,yaw:pose.yaw},mode:String(mode).slice(0,30),elapsed_s};
    }
    const j=this.active;
    if(update&&j&&update.id===j.id){
      if(update.status==='running'&&['queued','delivered','running'].includes(j.status)){j.status='running';j.startedAt??=this.now();}
      if(update.status==='completed'&&j.status==='running'){
        const actual=this.viewer.telemetry,expected=j.expected_pose;
        const yawError=actual?(j.motion||j.shot.unconstrained?actual.pose.yaw-expected.yaw:Math.atan2(Math.sin(actual.pose.yaw-expected.yaw),Math.cos(actual.pose.yaw-expected.yaw))):Infinity;
        if(actual&&actual.elapsed_s>=j.duration-.05&&Math.hypot(actual.pose.x-expected.x,actual.pose.y-expected.y)<.03&&Math.abs(yawError)<.03){j.result=actual;this.finish('completed','Browser confirmed the final simulated pose');}
        else this.finish('failed','Browser completion did not match the requested endpoint');
      }else if(['cancelled','failed'].includes(update.status))this.finish(update.status,String(update.reason||'Stopped in the simulator').slice(0,500));
    }
    if(!ready&&this.active){this.finish('cancelled','Simulator is not ready or its tab is hidden');this.stopEpoch++;}
    if(this.active?.status==='queued')this.active.status='delivered';
    return {role:'controller',instance:this.instance,stop_epoch:this.stopEpoch,job:this.active?this.publicJob(this.active):null,last_job:[...this.jobs.values()].at(-1)?this.publicJob([...this.jobs.values()].at(-1)):null};
  }
  publicJob(j){const {canonical,viewerId,...rest}=j;return rest;}
  status(id){this.sweep();if(id){const j=this.jobs.get(id);if(!j)throw new BridgeError(404,'Job not found in this bridge session');return this.publicJob(j);}
    return {simulation_only:true,instance:this.instance,viewer_connected:!!this.viewer?.ready,viewer:this.viewer?{ready:this.viewer.ready,last_seen:this.viewer.lastSeen,telemetry:this.viewer.telemetry}:null,active_job:this.active?this.publicJob(this.active):null,last_job:[...this.jobs.values()].at(-1)?this.publicJob([...this.jobs.values()].at(-1)):null};}
}
