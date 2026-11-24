// General planar motion for the browser simulation. No physical robot transport.
import {clamp, smooth, integratePose, exportPlan} from './sim-core.mjs';

const finite=(value,label)=>{if(typeof value!=='number'||!Number.isFinite(value))throw new Error(`${label} must be a finite number`);return value;};
const object=(v,label)=>{if(!v||typeof v!=='object'||Array.isArray(v))throw new Error(`${label} must be an object`);};
const fields=(v,allowed)=>{const extra=Object.keys(v).find(k=>!allowed.includes(k));if(extra)throw new Error(`Unknown motion field: ${extra}`);};
const pose=p=>{object(p,'pose');fields(p,['x','y','yaw']);return {x:finite(p.x,'x'),y:finite(p.y,'y'),yaw:finite(p.yaw,'yaw')};};
const frame=(v,fallback)=>{v??=fallback;if(!['body','world'].includes(v))throw new Error('frame must be body or world');return v;};
const duration=v=>{finite(v,'duration');if(v<=0)throw new Error('duration must be positive');return v;};
const easing=v=>{v??='smooth';if(!['smooth','linear'].includes(v))throw new Error('easing must be smooth or linear');return v;};
const interp=(a,b,t,curve)=>{const u=curve==='smooth'?smooth(t):t;return {x:a.x+(b.x-a.x)*u,y:a.y+(b.y-a.y)*u,yaw:a.yaw+(b.yaw-a.yaw)*u};};

export function normalizeMotion(input){
  object(input,'motion');
  const kind=input.kind;
  if(kind==='sequence'){
    fields(input,['kind','commands','repeat']);
    const repeat=input.repeat??1;
    if(!Number.isInteger(repeat)||repeat<1)throw new Error('repeat must be a positive integer');
    if(!Array.isArray(input.commands)||!input.commands.length||input.commands.length*repeat>1024)throw new Error('A sequence supports 1–1024 total commands per request');
    if(input.commands.some(c=>c?.kind==='sequence'))throw new Error('Use a flat command sequence');
    return {kind,commands:input.commands.map(normalizeMotion),repeat};
  }
  if(kind==='drive'){
    fields(input,['kind','vx','vy','omega','duration','frame']);
    return {kind,vx:finite(input.vx??0,'vx'),vy:finite(input.vy??0,'vy'),omega:finite(input.omega??0,'omega'),duration:duration(input.duration),frame:frame(input.frame,'body')};
  }
  if(kind==='move'){
    fields(input,['kind','x','y','yaw','duration','relative','frame','easing']);
    if(input.relative!==undefined&&typeof input.relative!=='boolean')throw new Error('relative must be boolean');
    if(!['x','y','yaw'].some(k=>input[k]!==undefined))throw new Error('Specify x, y, or yaw');
    const p={kind,duration:duration(input.duration),relative:input.relative??true,frame:frame(input.frame,'world'),easing:easing(input.easing)};
    for(const k of ['x','y','yaw'])if(input[k]!==undefined)p[k]=finite(input[k],k);
    if(!p.relative&&p.frame!=='world')throw new Error('Absolute moves use the world frame');
    return p;
  }
  if(kind==='pose'){
    fields(input,['kind','x','y','yaw']);return {kind,...pose({x:input.x,y:input.y,yaw:input.yaw})};
  }
  if(kind==='path'){
    fields(input,['kind','waypoints','easing']);
    if(!Array.isArray(input.waypoints)||!input.waypoints.length||input.waypoints.length>1024)throw new Error('Use 1–1024 waypoints per request');
    let prev=0;
    const waypoints=input.waypoints.map(w=>{
      object(w,'waypoint');fields(w,['t','x','y','yaw']);
      const t=finite(w.t,'waypoint t');if(t<=prev)throw new Error('Waypoint times must increase and start after zero');prev=t;
      return {t,...pose({x:w.x,y:w.y,yaw:w.yaw})};
    });
    return {kind,waypoints,easing:easing(input.easing)};
  }
  throw new Error('Unknown motion kind; use drive, move, pose, path, or sequence');
}

function compile(p,start){
  if(p.kind==='drive'){
    const sample=t=>p.frame==='body'?integratePose(start,[p.vx,p.vy,p.omega],t):{x:start.x+p.vx*t,y:start.y+p.vy*t,yaw:start.yaw+p.omega*t};
    const velocityAt=t=>{const yaw=sample(t).yaw;return p.frame==='body'?[p.vx,p.vy,p.omega]:[Math.cos(yaw)*p.vx+Math.sin(yaw)*p.vy,-Math.sin(yaw)*p.vx+Math.cos(yaw)*p.vy,p.omega];};
    return {duration:p.duration,sample,velocityAt};
  }
  if(p.kind==='pose'){const end=pose({x:p.x,y:p.y,yaw:p.yaw});return {duration:0,sample:()=>({...end}),velocityAt:()=>[0,0,0]};}
  if(p.kind==='move'){
    let end;
    if(p.relative){
      const dx=p.x??0,dy=p.y??0,c=p.frame==='body'?Math.cos(start.yaw):1,s=p.frame==='body'?Math.sin(start.yaw):0;
      end={x:start.x+c*dx-s*dy,y:start.y+s*dx+c*dy,yaw:start.yaw+(p.yaw??0)};
    }else end={x:p.x??start.x,y:p.y??start.y,yaw:p.yaw??start.yaw};
    return {duration:p.duration,sample:t=>interp(start,end,clamp(t/p.duration,0,1),p.easing)};
  }
  if(p.kind==='path'){
    const nodes=[{t:0,...start},...p.waypoints];
    return {duration:nodes.at(-1).t,sample:t=>{
      const i=Math.max(1,nodes.findIndex(n=>n.t>=t));
      const a=nodes[i-1],b=nodes[i];return interp(a,b,clamp((t-a.t)/(b.t-a.t),0,1),p.easing);
    }};
  }
  const segments=[];let elapsed=0,current={...start};
  for(let repeat=0;repeat<p.repeat;repeat++)for(const command of p.commands){
    const part=compile(command,current);segments.push({at:elapsed,...part});elapsed+=part.duration;current=part.sample(part.duration);
  }
  return {duration:elapsed,sample:t=>{
    if(t>=elapsed)return {...current};
    const part=segments.find(s=>s.duration>0&&t<s.at+s.duration);
    return part?part.sample(Math.max(0,t-part.at)):{...current};
  }};
}

export function makeMotion(input,startPose){
  const motion=normalizeMotion(input),start=pose(startPose),compiled=compile(motion,start);
  if(!Number.isFinite(compiled.duration))throw new Error('Motion duration exceeds numeric precision');
  const sample=t=>compiled.sample(clamp(t,0,compiled.duration));
  const velocityAt=compiled.velocityAt|| (t=>{
    if(!compiled.duration)return [0,0,0];
    const h=Math.min(.001,compiled.duration/1000),a=Math.max(0,t-h),b=Math.min(compiled.duration,t+h);
    const pa=sample(a),pb=sample(b),pc=sample(t),wx=(pb.x-pa.x)/(b-a),wy=(pb.y-pa.y)/(b-a);
    return [Math.cos(pc.yaw)*wx+Math.sin(pc.yaw)*wy,-Math.sin(pc.yaw)*wx+Math.cos(pc.yaw)*wy,(pb.yaw-pa.yaw)/(b-a)];
  });
  let length=0,maxSpeed=0,previous=sample(0);
  for(let i=0;i<=600;i++){
    const t=compiled.duration*i/600,point=sample(t),v=velocityAt(t);
    if(![point.x,point.y,point.yaw,...v].every(Number.isFinite))throw new Error('Motion exceeds numeric precision');
    length+=Math.hypot(point.x-previous.x,point.y-previous.y);maxSpeed=Math.max(maxSpeed,Math.hypot(v[0],v[1]));previous=point;
  }
  if(!Number.isFinite(length)||!Number.isFinite(maxSpeed))throw new Error('Motion exceeds numeric precision');
  return {params:{kind:motion.kind,duration:compiled.duration,unconstrained:true},motion,startPose:start,sample,velocityAt,length,maxSpeed,valid:true,reason:'',minDuration:0};
}

export function exportMotion(plan){const data=exportPlan(plan);data.kind='kino.motion_preview';data.motion=plan.motion;data.start_pose=plan.startPose;return data;}
