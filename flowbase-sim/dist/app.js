import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {STLLoader} from './vendor/STLLoader.js';
import {Simulator,makePlan,exportPlan,wrap,MODEL_COMMIT} from './sim-core.mjs';
import {SimulatorBridge} from './bridge-client.mjs';
import {makeMotion,exportMotion} from './motion-core.mjs';

const $=id=>document.getElementById(id);
const sim=new Simulator();
let shotKind='orbit', plan, modelReady=false, cameraHeight=1.4, focalLength=35, lastTime=0, lastUI=0, view='3d', toastTimer;
let bridge;
const keys=new Set(), joints=new Map(), travelled=[];
const heading0=[Math.PI,0,0,-Math.PI], driveSign=[-1,1,-1,1];
const scene=new THREE.Scene();scene.background=new THREE.Color('#272e30');scene.fog=new THREE.Fog('#272e30',13,30);
THREE.Object3D.DEFAULT_UP.set(0,0,1);
const camera=new THREE.PerspectiveCamera(42,1,.03,70);camera.position.set(-7,-7,6.8);
const lensCamera=new THREE.PerspectiveCamera(32,16/9,.03,40);
let renderer, previewRenderer;
try {
  renderer=new THREE.WebGLRenderer({antialias:true});
  previewRenderer=new THREE.WebGLRenderer({antialias:true});
}catch(error){$('loading').textContent='WebGL is unavailable. Open this page in a browser with hardware acceleration enabled.';throw error;}
for(const r of [renderer,previewRenderer]){r.setPixelRatio(Math.min(devicePixelRatio,2));r.outputColorSpace=THREE.SRGBColorSpace;r.toneMapping=THREE.ACESFilmicToneMapping;r.toneMappingExposure=1.15;}
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
$('viewport').appendChild(renderer.domElement);$('camera-viewport').prepend(previewRenderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(-.6,0,.25);controls.enableDamping=true;controls.minDistance=1;controls.maxDistance=22;controls.maxPolarAngle=Math.PI/2-.03;
scene.add(new THREE.HemisphereLight('#dbe8ff','#374039',2.3));
const sun=new THREE.DirectionalLight('#f5f5df',3.8);sun.position.set(-3,-5,9);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-6;sun.shadow.camera.right=6;sun.shadow.camera.top=6;sun.shadow.camera.bottom=-6;sun.shadow.normalBias=.025;scene.add(sun);
const fill=new THREE.DirectionalLight('#b0d1fc',1.1);fill.position.set(3,4,5);scene.add(fill);

const floor=new THREE.Mesh(new THREE.PlaneGeometry(60,60),new THREE.MeshStandardMaterial({color:'#343d3c',roughness:1}));floor.receiveShadow=true;floor.position.z=-.004;scene.add(floor);
const grid=new THREE.GridHelper(10,10,'#69766c','#49574e');grid.rotation.x=Math.PI/2;grid.position.z=.001;scene.add(grid);
const border=new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-5,-5,.004),new THREE.Vector3(5,-5,.004),new THREE.Vector3(5,5,.004),new THREE.Vector3(-5,5,.004)]),new THREE.LineBasicMaterial({color:'#72816d'}));scene.add(border);

function material(color,metalness=0,roughness=.7){return new THREE.MeshStandardMaterial({color,metalness,roughness});}
function mesh(geometry,mat,position,parent=scene){const m=new THREE.Mesh(geometry,mat);m.position.set(...position);m.castShadow=true;m.receiveShadow=true;parent.add(m);return m;}
function cylinder(radius,height,mat,position,parent=scene){const m=mesh(new THREE.CylinderGeometry(radius,radius,height,24),mat,position,parent);m.rotation.x=Math.PI/2;return m;}
function label(text,color='#b8c7b7',scale=1){
  const c=document.createElement('canvas');c.width=512;c.height=96;const ctx=c.getContext('2d');ctx.font='500 30px monospace';ctx.textAlign='center';ctx.fillStyle=color;ctx.fillText(text,256,58);
  const texture=new THREE.CanvasTexture(c);const m=new THREE.Mesh(new THREE.PlaneGeometry(2.7*scale,.5*scale),new THREE.MeshBasicMaterial({map:texture,transparent:true,depthWrite:false}));return m;
}
const stageLabel=label('STAGE A  /  10 × 10 m','#9aa99c');stageLabel.position.set(0,-4.7,.01);scene.add(stageLabel);
const subjectLabel=label('SUBJECT 01','#d2e6c1',.65);subjectLabel.position.set(0,-.67,.012);scene.add(subjectLabel);
const ring=mesh(new THREE.RingGeometry(.76,.78,80),new THREE.MeshBasicMaterial({color:'#93a67b',transparent:true,opacity:.5,side:THREE.DoubleSide}),[0,0,.006]);
const subject=new THREE.Group();scene.add(subject);
const bodyMat=material('#c6c9bc',.05,.8),jointMat=material('#909c8d');
cylinder(.31,.055,material('#7c8d6d'),[0,0,.028],subject);
mesh(new THREE.SphereGeometry(.115,24,16),bodyMat,[0,0,1.59],subject);
const torso=mesh(new THREE.CapsuleGeometry(.155,.34,8,20),bodyMat,[0,0,1.23],subject);torso.rotation.x=Math.PI/2;torso.scale.set(1,.95,1.2);
for(const side of [-1,1]){
  const leg=cylinder(.065,.62,bodyMat,[0,side*.10,.43],subject);
  mesh(new THREE.BoxGeometry(.22,.12,.08),jointMat,[.04,side*.10,.10],subject);
  const arm=cylinder(.045,.48,bodyMat,[0,side*.22,1.08],subject);arm.rotation.x+=side*.08;
  mesh(new THREE.SphereGeometry(.048,16,12),bodyMat,[0,side*.24,.82],subject);
}
// Minimal studio scenery, outside the navigable stage.
for(const y of [-5.8,5.8]){
  const stand=new THREE.Group();scene.add(stand);stand.position.set(2.8,y,0);
  cylinder(.025,2.4,material('#5a645d',.6),[0,0,1.2],stand);
  const light=mesh(new THREE.BoxGeometry(.12,.9,.65),material('#bdcabb',.2),[0,0,2.45],stand);light.rotation.y=-.18;
  for(let i=0;i<3;i++){const foot=mesh(new THREE.BoxGeometry(.5,.025,.035),material('#687167',.6),[0,0,.03],stand);foot.rotation.z=i*Math.PI/3;}
}

const robot=new THREE.Group();scene.add(robot);
const robotModel=new THREE.Group();robot.add(robotModel);
const rig=new THREE.Group();robot.add(rig);
const mast=cylinder(.021,1,material('#87958d',.8,.3),[0,0,.8],rig);
const cameraBody=mesh(new THREE.BoxGeometry(.19,.145,.11),material('#232c2c',.3),[.015,0,cameraHeight],rig);
const cameraLens=mesh(new THREE.CylinderGeometry(.047,.047,.11,24),material('#101d25',.6,.2),[.16,0,cameraHeight],rig);cameraLens.rotation.z=-Math.PI/2;
const cameraGlass=mesh(new THREE.CylinderGeometry(.035,.035,.003,24),material('#558eac',.7,.1),[.217,0,cameraHeight],rig);cameraGlass.rotation.z=-Math.PI/2;
const tally=mesh(new THREE.SphereGeometry(.009,12,8),new THREE.MeshBasicMaterial({color:'#d0ff76'}),[.07,-.075,cameraHeight+.025],rig);
const front=new THREE.ArrowHelper(new THREE.Vector3(1,0,0),new THREE.Vector3(.12,0,.345),.42,0xd2fc80,.10,.07);robot.add(front);
const frustumMaterial=new THREE.LineBasicMaterial({color:'#d7eea4',transparent:true,opacity:.35});
const frustum=new THREE.LineSegments(new THREE.BufferGeometry(),frustumMaterial);robot.add(frustum);
const planLine=new THREE.Line(new THREE.BufferGeometry(),new THREE.LineDashedMaterial({color:'#cff783',dashSize:.09,gapSize:.055}));scene.add(planLine);
const trailLine=new THREE.Line(new THREE.BufferGeometry(),new THREE.LineBasicMaterial({color:'#77d2e6'}));scene.add(trailLine);
const startMarker=mesh(new THREE.RingGeometry(.34,.365,64),new THREE.MeshBasicMaterial({color:'#d0fa79',side:THREE.DoubleSide,transparent:true,opacity:.65}),[-2.5,0,.01]);
const endMarker=mesh(new THREE.RingGeometry(.10,.125,32),new THREE.MeshBasicMaterial({color:'#d0fa79',side:THREE.DoubleSide}),[0,-2.5,.01]);

function origin(group,element){
  const xyz=(element?.getAttribute('xyz')||'0 0 0').split(/\s+/).map(Number),rpy=(element?.getAttribute('rpy')||'0 0 0').split(/\s+/).map(Number);
  group.position.fromArray(xyz);group.rotation.set(rpy[0],rpy[1],rpy[2],'ZYX');
}
async function loadRobot(){
  const response=await fetch('./assets/robot/flowbase.urdf');if(!response.ok)throw new Error('Robot description unavailable');
  const xml=new DOMParser().parseFromString(await response.text(),'text/xml');if(xml.querySelector('parsererror'))throw new Error('Invalid robot description');
  const links=new Map(),loads=[],loader=new STLLoader();
  for(const l of xml.querySelectorAll('robot > link')){
    const name=l.getAttribute('name'),group=new THREE.Group();group.name=name;links.set(name,group);
    for(const visual of l.querySelectorAll(':scope > visual')){
      const file=visual.querySelector('mesh')?.getAttribute('filename');if(!file)continue;
      const visualFrame=new THREE.Group();origin(visualFrame,visual.querySelector('origin'));group.add(visualFrame);
      const color=name==='base'?'#617c9e':(Number(name.replace('motor',''))%2===0?'#2e3434':'#6f7877');
      loads.push(loader.loadAsync(`./assets/robot/${file}`).then(geometry=>{
        const m=new THREE.Mesh(geometry,material(color,name==='base'?.35:.25,.58));
        const scale=(visual.querySelector('mesh').getAttribute('scale')||'1 1 1').split(/\s+/).map(Number);m.scale.fromArray(scale);m.castShadow=true;m.receiveShadow=true;visualFrame.add(m);
      }));
    }
  }
  for(const j of xml.querySelectorAll('robot > joint')){
    const parent=links.get(j.querySelector('parent').getAttribute('link')),child=links.get(j.querySelector('child').getAttribute('link'));
    if(!parent||!child)continue;
    const jointOrigin=new THREE.Group();origin(jointOrigin,j.querySelector('origin'));
    const motion=new THREE.Group();jointOrigin.add(motion);motion.add(child);parent.add(jointOrigin);
    joints.set(j.getAttribute('name'),{motion,axis:new THREE.Vector3().fromArray((j.querySelector('axis')?.getAttribute('xyz')||'0 0 1').split(/\s+/).map(Number)).normalize()});
  }
  robotModel.add(links.get('root'));await Promise.all(loads);modelReady=true;$('loading').hidden=true;refreshPlan();
}
function setJoint(name,value){const joint=joints.get(name);if(joint)joint.motion.quaternion.setFromAxisAngle(joint.axis,value);}
function updateRig(){
  mast.scale.y=(cameraHeight-.3);mast.position.z=(cameraHeight+.3)/2;
  cameraBody.position.z=cameraLens.position.z=cameraGlass.position.z=cameraHeight;tally.position.z=cameraHeight+.025;
  lensCamera.fov=THREE.MathUtils.radToDeg(2*Math.atan(20.25/(2*focalLength)));lensCamera.updateProjectionMatrix();
  const length=.9,h=Math.tan(THREE.MathUtils.degToRad(lensCamera.fov/2))*length,w=h*16/9,points=[];
  const root=new THREE.Vector3(.22,0,cameraHeight),corners=[new THREE.Vector3(length,w,cameraHeight+h),new THREE.Vector3(length,-w,cameraHeight+h),new THREE.Vector3(length,-w,cameraHeight-h),new THREE.Vector3(length,w,cameraHeight-h)];
  for(let i=0;i<4;i++){points.push(root,corners[i],corners[i],corners[(i+1)%4]);}
  frustum.geometry.dispose();frustum.geometry=new THREE.BufferGeometry().setFromPoints(points);
  $('lens-label').textContent=`${focalLength} mm`;
}
function clearTrail(){travelled.length=0;trailLine.geometry.dispose();trailLine.geometry=new THREE.BufferGeometry();}
function addTrail(){
  const p=new THREE.Vector3(sim.pose.x,sim.pose.y,.018);
  if(!travelled.length||travelled.at(-1).distanceTo(p)>.025){travelled.push(p);if(travelled.length>3500)travelled.shift();trailLine.geometry.dispose();trailLine.geometry=new THREE.BufferGeometry().setFromPoints(travelled);}
}
function paintRange(input){const pct=(Number(input.value)-Number(input.min))/(Number(input.max)-Number(input.min))*100;input.style.setProperty('--fill',`${pct}%`);}
function readParams(){return {kind:shotKind,radius:Number($('radius').value),sweepDeg:Number($('sweep').value),distance:Number($('distance').value),duration:Number($('duration').value),faceSubject:$('subject-lock').checked,unconstrained:$('free-motion').checked};}
function refreshPlan(reset=true){
  if(reset)bridge?.interrupt('Shot parameters changed in the simulator');
  $('preset-controls').hidden=false;
  plan=makePlan(readParams());
  sim.unconstrained=plan.params.unconstrained;
  $('radius-value').textContent=`${plan.params.radius.toFixed(1)} m`;$('sweep-value').textContent=`${plan.params.sweepDeg}°`;$('distance-value').textContent=`${plan.params.distance.toFixed(1)} m`;$('duration-value').textContent=`${plan.params.duration} s`;
  $('sweep-field').hidden=shotKind!=='orbit';$('distance-field').hidden=shotKind==='orbit';
  $('shot-description').textContent={orbit:'Circle the subject while keeping them in frame.',dolly:'Move closer for a gradual, deliberate reveal.',slide:'Travel sideways for a smooth parallax move.'}[shotKind];
  renderPlan();
  if(reset){releaseKeys();sim.reset(plan.sample(0));clearTrail();$('scrub').value=0;paintRange($('scrub'));}
}
function renderPlan(){
  $('path-length').textContent=`${plan.length.toFixed(2)} m`;$('peak-speed').textContent=`${plan.maxSpeed.toFixed(2)} m/s`;
  $('validation').textContent=plan.params.unconstrained?'Free simulation · Stage and motion limits off':plan.valid?'Smooth start & finish · Within preview limits':plan.reason;
  $('validation').parentElement.classList.toggle('invalid',!plan.valid);$('play').disabled=!modelReady||!plan.valid;
  $('export').disabled=!plan.valid;
  $('camera-direction').textContent=plan.motion?'Custom heading':plan.params.faceSubject?'Subject lock':'Fixed heading';
  const points=Array.from({length:161},(_,i)=>{const p=plan.sample(i/160*plan.params.duration);return new THREE.Vector3(p.x,p.y,.016);});
  planLine.geometry.dispose();planLine.geometry=new THREE.BufferGeometry().setFromPoints(points);planLine.computeLineDistances();
  planLine.material.color.set(plan.valid?'#cff783':'#ffad89');
  startMarker.position.copy(points[0]);endMarker.position.copy(points.at(-1));
  $('total-time').textContent=`${plan.params.duration.toFixed(1)} s`;
  document.querySelectorAll('input[type=range]').forEach(paintRange);
}
function toast(message){$('toast').textContent=message;$('toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('visible'),3200);}
function releaseKeys(){keys.clear();document.querySelectorAll('[data-key]').forEach(b=>b.classList.remove('pressed'));if(sim.mode==='manual')sim.stop();}
function applyKeys(){
  document.querySelectorAll('[data-key]').forEach(b=>b.classList.toggle('pressed',keys.has(b.dataset.key)));
  const vx=(Number(keys.has('w'))-Number(keys.has('s')))*.35,vy=(Number(keys.has('a'))-Number(keys.has('d')))*.35,w=(Number(keys.has('q'))-Number(keys.has('e')))*.55;
  if(keys.size){bridge?.interrupt('Manual takeover');if(sim.mode==='shot'){toast('Manual control · Shot cancelled');clearTrail();}sim.manual([vx,vy,w]);}else if(sim.mode==='manual')sim.stop();
}
function stopAll(message=true){bridge?.interrupt('Stopped in the simulator');releaseKeys();sim.stop();if(message)toast('Movement stopped');}
function playShot(){bridge?.interrupt('Shot restarted in the simulator');releaseKeys();clearTrail();sim.play(plan);$('viewport').focus({preventScroll:true});toast('Rehearsing from the shot’s start marker');}
function setView(next){
  view=next;const points=[sim.pose,...Array.from({length:161},(_,i)=>plan.sample(plan.params.duration*i/160))];
  const minX=Math.min(...points.map(p=>p.x),-1),maxX=Math.max(...points.map(p=>p.x),1),minY=Math.min(...points.map(p=>p.y),-1),maxY=Math.max(...points.map(p=>p.y),1);
  const x=(minX+maxX)/2,y=(minY+maxY)/2,span=Math.max(5,maxX-minX,maxY-minY),d=span*1.8;
  controls.target.set(x,y,.25);camera.position.set(...(next==='top'?[x,y-.001,d]:[x-d*.65,y-d*.65,d*.65]));
  controls.maxDistance=Math.max(22,d*3);camera.far=Math.max(70,d*8);camera.updateProjectionMatrix();scene.fog.far=Math.max(30,d*5);scene.fog.near=Math.max(13,d*2);
  controls.enableRotate=next!=='top';controls.update();$('view-3d').classList.toggle('active',next==='3d');$('view-top').classList.toggle('active',next==='top');$('view-3d').setAttribute('aria-pressed',next==='3d');$('view-top').setAttribute('aria-pressed',next==='top');
}

$('play').addEventListener('click',playShot);$('stop').addEventListener('click',()=>stopAll());
$('reset').addEventListener('click',()=>{if(plan.motion){stopAll(false);sim.reset(plan.sample(0));clearTrail();}else refreshPlan();toast('Reset to shot start');});
document.querySelectorAll('[data-shot]').forEach(button=>button.addEventListener('click',()=>{
  shotKind=button.dataset.shot;document.querySelectorAll('[data-shot]').forEach(b=>{b.classList.toggle('selected',b===button);b.setAttribute('aria-pressed',b===button);});refreshPlan();
}));
for(const id of ['radius','sweep','distance','duration','subject-lock'])$(id).addEventListener('input',()=>refreshPlan());
$('free-motion').addEventListener('change',()=>{
  stopAll(false);sim.unconstrained=$('free-motion').checked;
  if(!sim.unconstrained)for(const [id,min,max] of [['radius',1.2,4],['sweep',-180,180],['distance',.2,3],['duration',4,40]]){const input=$(id),value=Number(input.value);input.min=min;input.max=max;input.value=Math.max(min,Math.min(max,value));}
  if(plan.motion){shotKind='orbit';document.querySelectorAll('[data-shot]').forEach(b=>{b.classList.toggle('selected',b.dataset.shot==='orbit');b.setAttribute('aria-pressed',b.dataset.shot==='orbit');});}refreshPlan();
});
$('height').addEventListener('change',()=>{cameraHeight=Number($('height').value);updateRig();});
$('lens').addEventListener('change',()=>{focalLength=Number($('lens').value);updateRig();});
$('scrub').addEventListener('input',()=>{bridge?.interrupt('Timeline scrubbed in the simulator');releaseKeys();sim.seek(plan,Number($('scrub').value)/1000*plan.params.duration);clearTrail();paintRange($('scrub'));});
$('view-3d').addEventListener('click',()=>setView('3d'));$('view-top').addEventListener('click',()=>setView('top'));$('view-fit').addEventListener('click',()=>setView(view));
$('sources-button').addEventListener('click',()=>{stopAll(false);$('sources-dialog').showModal();});$('close-sources').addEventListener('click',()=>$('sources-dialog').close());
$('sources-dialog').addEventListener('click',e=>{if(e.target===$('sources-dialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();}});
$('export').addEventListener('click',()=>{
  const data=plan.motion?exportMotion(plan):exportPlan(plan);data.camera={height_m:cameraHeight,focal_length_mm:focalLength,sensor_width_mm:36,aspect_ratio:'16:9',mount:'illustrative rigid mast',optical_axis:'horizontal, follows base yaw'};
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`kino-${shotKind}-shot.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Shot plan exported as JSON');
});
for(const button of document.querySelectorAll('[data-key]')){
  button.addEventListener('pointerdown',e=>{e.preventDefault();if(!modelReady)return;button.setPointerCapture(e.pointerId);keys.add(button.dataset.key);applyKeys();});
  const up=()=>{keys.delete(button.dataset.key);applyKeys();};button.addEventListener('pointerup',up);button.addEventListener('pointercancel',up);button.addEventListener('lostpointercapture',up);
}
window.addEventListener('keydown',event=>{
  if(event.code==='Space'&&!$('sources-dialog').open){event.preventDefault();stopAll(!event.repeat);return;}
  if(!modelReady||$('sources-dialog').open||/INPUT|SELECT|TEXTAREA/.test(event.target.tagName)||event.metaKey||event.ctrlKey||event.altKey)return;
  const key=event.key.toLowerCase();if('wasdqe'.includes(key)&&key.length===1){event.preventDefault();keys.add(key);applyKeys();}
});
window.addEventListener('keyup',event=>{const key=event.key.toLowerCase();if(keys.has(key)){keys.delete(key);applyKeys();}});
// Kino may hold keyboard focus while the visible simulator runs its shot.
window.addEventListener('blur',()=>{releaseKeys();});
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopAll(false);});

function resize(){
  const r=$('viewport').getBoundingClientRect();camera.aspect=r.width/r.height;camera.updateProjectionMatrix();renderer.setSize(r.width,r.height,false);
  const p=$('camera-viewport').getBoundingClientRect();previewRenderer.setSize(p.width,p.height,false);
}
new ResizeObserver(resize).observe($('viewport'));new ResizeObserver(resize).observe($('camera-viewport'));
function updateUI(){
  $('pos-x').innerHTML=`${sim.pose.x.toFixed(2)} <small>m</small>`;$('pos-y').innerHTML=`${sim.pose.y.toFixed(2)} <small>m</small>`;$('heading').innerHTML=`${THREE.MathUtils.radToDeg(wrap(sim.pose.yaw)).toFixed(1)}<small>°</small>`;$('speed').innerHTML=`${Math.hypot(sim.velocity[0],sim.velocity[1]).toFixed(2)} <small>m/s</small>`;
  $('mode').textContent={idle:'Standby',manual:'Manual',shot:'Autonomous',paused:'Scrubbing',complete:'Complete'}[sim.mode];
  $('status').textContent=sim.blocked?'Clearance limit · Stopped':{idle:'Ready to rehearse',manual:'Manual control',shot:'Rehearsing shot',paused:'Previewing frame',complete:'Shot complete'}[sim.mode];
  $('elapsed').textContent=sim.elapsed.toFixed(1).padStart(4,'0');
  if(document.activeElement!==$('scrub')){$('scrub').value=plan.params.duration?Math.round(sim.elapsed/plan.params.duration*1000):1000;paintRange($('scrub'));}
  $('play').innerHTML=sim.mode==='shot'?'<span aria-hidden="true">↺</span> Restart':'<span class="play-icon" aria-hidden="true">▶</span> Run shot';
}
function animate(time){
  const dt=Math.min((time-lastTime)/1000||0,.05);lastTime=time;
  sim.tick(dt);robot.position.set(sim.pose.x,sim.pose.y,0);robot.rotation.z=sim.pose.yaw;
  for(let i=0;i<4;i++){setJoint(`dof_joint${2*i+1}`,sim.steer[i]-heading0[i]);setJoint(`dof_joint${2*i+2}`,driveSign[i]*sim.drive[i]);}
  if(sim.mode==='manual'||sim.mode==='shot')addTrail();
  controls.update();renderer.render(scene,camera);
  const {x,y,yaw}=sim.pose;lensCamera.position.set(x+.23*Math.cos(yaw),y+.23*Math.sin(yaw),cameraHeight);lensCamera.lookAt(x+5*Math.cos(yaw),y+5*Math.sin(yaw),cameraHeight);
  robot.visible=false;planLine.visible=false;trailLine.visible=false;startMarker.visible=false;endMarker.visible=false;subjectLabel.visible=false;ring.visible=false;stageLabel.visible=false;
  previewRenderer.render(scene,lensCamera);
  robot.visible=true;planLine.visible=true;trailLine.visible=true;startMarker.visible=true;endMarker.visible=true;subjectLabel.visible=true;ring.visible=true;stageLabel.visible=true;
  if(time-lastUI>80){updateUI();lastUI=time;}
  requestAnimationFrame(animate);
}
updateRig();refreshPlan();resize();requestAnimationFrame(animate);
loadRobot().catch(error=>{console.error(error);$('loading').textContent='The model could not load. Reload the page or check the local assets.';});
// Browser-local adapter; the bridge delivers only validated simulation jobs.
window.kinoSim={
  getState:()=>({pose:{...sim.pose},body_velocity:[...sim.velocity],mode:sim.mode,elapsed_s:sim.elapsed,modelReady,model_commit:MODEL_COMMIT,simulation_only:true,unconstrained:sim.unconstrained}),
  stop:()=>stopAll(false),
  executeShot:params=>{
    const request=makePlan(params);if(!modelReady)throw new Error('Model not ready');if(!request.valid)throw new Error(request.reason);
    const fields={radius:'radius',sweepDeg:'sweep',distance:'distance',duration:'duration'};
    for(const [key,id] of Object.entries(fields)){const input=$(id);if(request.params.unconstrained){input.min=Math.min(Number(input.min),request.params[key]);input.max=Math.max(Number(input.max),request.params[key]);}else if(request.params[key]<Number(input.min)||request.params[key]>Number(input.max))throw new Error(`${key} is outside the studio's supported range`);}
    shotKind=request.params.kind;
    for(const [key,id] of Object.entries(fields)){$(id).step='any';$(id).value=request.params[key];}
    $('subject-lock').checked=request.params.faceSubject;
    $('free-motion').checked=!!request.params.unconstrained;
    document.querySelectorAll('[data-shot]').forEach(b=>{b.classList.toggle('selected',b.dataset.shot===shotKind);b.setAttribute('aria-pressed',b.dataset.shot===shotKind);});
    refreshPlan();playShot();setView(view);return {accepted:true,simulation_only:true};
  },
  executeMotion:(motion,startPose)=>{
    if(!modelReady)throw new Error('Model not ready');
    const request=makeMotion(motion,startPose);
    if(Math.hypot(sim.pose.x-startPose.x,sim.pose.y-startPose.y)>.03||Math.abs(sim.pose.yaw-startPose.yaw)>.03)throw new Error('Robot moved since command submission; request a new movement from its current pose');
    bridge?.interrupt('New motion');releaseKeys();clearTrail();plan=request;shotKind='custom';sim.unconstrained=true;$('free-motion').checked=true;$('preset-controls').hidden=true;
    document.querySelectorAll('[data-shot]').forEach(b=>{b.classList.remove('selected');b.setAttribute('aria-pressed','false');});
    $('shot-description').textContent=`Kino ${motion.kind} · ${request.params.duration.toFixed(1)} seconds · From current pose`;
    renderPlan();sim.play(plan);setView(view);return {accepted:true,simulation_only:true};
  },
  exportShot:()=>plan.motion?exportMotion(plan):exportPlan(plan)
};
bridge=new SimulatorBridge({
  api:window.kinoSim,
  onStatus:(status,message)=>{
    $('bridge-status').textContent={connected:'Kino bridge connected',connecting:'Connecting Kino…',observer:'Viewer already connected',offline:'Direct from Kino chat'}[status];
    $('bridge-detail').textContent=message;
    document.querySelector('.bridge-bar').dataset.status=status;
    $('connect-kino').textContent=status==='connected'||status==='observer'?'Disconnect':'Connect Kino';
    $('connect-kino').disabled=status==='connecting';
  },
  onJob:job=>{$('kino-shot').hidden=false;$('kino-shot-reason').textContent=job.reason||`${(job.motion||job.shot).kind} · ${job.duration} seconds`;$('kino-shot-status').textContent={queued:'Queued',delivered:'Delivered',running:'Rehearsing',stopping:'Stopping',completed:'Completed',cancelled:'Cancelled',failed:'Failed'}[job.status]||job.status;if(job.status==='failed')$('bridge-detail').textContent=job.status_reason||job.reason;},
  onDisconnect:()=>releaseKeys()
});
const localBridge=location.hostname==='127.0.0.1'&&location.port==='8766'||location.hostname==='localhost'&&location.port==='8766';
$('local-simulator').hidden=localBridge;
$('connect-kino').addEventListener('click',()=>bridge.running?bridge.disconnect():bridge.connect(localBridge?'':'http://127.0.0.1:8766'));
if(localBridge)bridge.connect('');
