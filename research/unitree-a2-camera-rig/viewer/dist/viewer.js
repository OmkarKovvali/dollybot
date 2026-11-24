import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';
import { STLLoader } from './vendor/STLLoader.js';
import { GLTFLoader } from './vendor/loaders/GLTFLoader.js';
import { STICK, createTelescopingStick } from './telescoping-stick.js';

const viewport = document.querySelector('#viewport');
const SONY_MOUNT_X=-48;
let sonyBaseZ=34;
let mountSeatHeight=0;
const controlPanel=document.querySelector('#viewControls');
const controlToggle=document.querySelector('#controlsToggle');
function toggleControlPanel(open){controlPanel.hidden=!open;controlToggle.setAttribute('aria-expanded',String(open));}
toggleControlPanel(window.innerWidth>620);
controlToggle.addEventListener('click',()=>toggleControlPanel(controlPanel.hidden));
const scene = new THREE.Scene();
scene.background = new THREE.Color('#11191f');
const camera = new THREE.PerspectiveCamera(37, 1, 0.5, 10000);
camera.up.set(0, 0, 1);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(viewport.clientWidth, viewport.clientHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.45;
viewport.appendChild(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.075;
controls.minDistance = 100;
controls.maxDistance = 10000;
controls.autoRotateSpeed = 0.7;
scene.add(new THREE.AmbientLight(0xcbdcec, 1.3));
const key = new THREE.DirectionalLight(0xf8f5eb, 3.2); key.position.set(-400, -350, 600); scene.add(key);
const fill = new THREE.DirectionalLight(0xa1c8ec, 2.1); fill.position.set(300, 350, 250); scene.add(fill);
const under = new THREE.DirectionalLight(0xc5dcdd, 1.8); under.position.set(0, -150, -300); scene.add(under);

const mats = {
  cover: new THREE.MeshStandardMaterial({ color: 0x34775e, metalness: 0, roughness: 0.68, side: THREE.DoubleSide }),
  reference: new THREE.MeshStandardMaterial({ color: 0x899ca7, metalness: 0.1, roughness: 0.6, side: THREE.DoubleSide }),
  robot: new THREE.MeshStandardMaterial({ color: 0x829ba9, metalness: 0.1, roughness: 0.65, transparent:true, opacity:0.65, depthWrite:false, side:THREE.FrontSide }),
  printed: new THREE.MeshStandardMaterial({ color: 0x4eac96, metalness: 0, roughness: 0.65 }),
  quick: new THREE.MeshStandardMaterial({ color: 0x9275bf, metalness: 0, roughness: 0.65 }),
  dark: new THREE.MeshStandardMaterial({ color: 0x22292e, metalness: 0.2, roughness: 0.52 }),
  rubber: new THREE.MeshStandardMaterial({ color: 0x111920, metalness: 0.1, roughness: 0.75 }),
  glass: new THREE.MeshStandardMaterial({ color: 0x224c69, metalness: 0.7, roughness: 0.13 }),
  bolt: new THREE.MeshStandardMaterial({ color: 0xd4a45b, metalness: 0.65, roughness: 0.3 }),
  silver: new THREE.MeshStandardMaterial({ color: 0x98a4ae, metalness: 0.7, roughness: 0.3 })
};
const rig = new THREE.Group(); scene.add(rig);
const cameras = new THREE.Group(); cameras.visible=true; rig.add(cameras);

function box(parent, w, d, h, x, y, z, material) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, d, h), material); mesh.position.set(x,y,z); parent.add(mesh); return mesh;
}
function cylinder(parent, r, h, x, y, z, material, axis = 'z', sides = 64) {
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, sides), material);
  if(axis === 'z') mesh.rotation.x = Math.PI / 2;
  if(axis === 'x') mesh.rotation.z = Math.PI / 2;
  mesh.position.set(x,y,z); parent.add(mesh); return mesh;
}
function ring(parent, outer, inner, h, x, y, z, material) {
  const shape = new THREE.Shape(); shape.absarc(0,0,outer,0,Math.PI*2,false);
  const hole = new THREE.Path(); hole.absarc(0,0,inner,0,Math.PI*2,true); shape.holes.push(hole);
  const mesh = new THREE.Mesh(new THREE.ExtrudeGeometry(shape,{depth:h,bevelEnabled:false,curveSegments:64}),material);
  mesh.position.set(x,y,z); parent.add(mesh); return mesh;
}
function label(text, color='#c5e1e2') {
  const c = document.createElement('canvas'); c.width=512; c.height=80;
  const ctx=c.getContext('2d'); ctx.font='500 27px -apple-system, sans-serif'; ctx.fillStyle=color; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText(text,256,40);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c),transparent:true,depthTest:true})); s.scale.set(130,20.3,1); return s;
}
const grid = new THREE.GridHelper(1600, 40, 0x36505b, 0x24343d); grid.rotation.x=Math.PI/2; grid.position.z=-8; grid.material.transparent=true; grid.material.opacity=0.26; scene.add(grid);
const direction = new THREE.ArrowHelper(new THREE.Vector3(-1,0,0),new THREE.Vector3(-165,-138,-4),55,0x7699a9,9,5); scene.add(direction);
const front = label('PROPOSED FORWARD','#7f9da9'); front.position.set(-115,-153,-3); scene.add(front);

// Flat cover only: mounting bores are real mesh cuts; no raised interfaces.
const sony = new THREE.Group(); sony.position.z=-28.8; cameras.add(sony);
box(sony,54.3,121,71.9,-48,0,98.75,mats.dark);
box(sony,12,30,61,-80,-44,95,mats.rubber);
box(sony,3,85,46,-19,8,99,mats.rubber);
box(sony,3.5,77,39,-16.8,8,99,mats.glass);
cylinder(sony,31,72,-107,13,102,mats.dark,'x');
cylinder(sony,32,12,-133,13,102,mats.rubber,'x');
cylinder(sony,27,1.5,-143.8,13,102,mats.glass,'x');
cylinder(sony,7,4,-54,-43,136.5,mats.silver);
box(sony,16,22,5,-42,0,137,mats.dark);
const sonyLabel=label('ZV-E1 / lens proxy'); sonyLabel.position.set(-50,-83,127); sony.add(sonyLabel);
const stick=createTelescopingStick();
const poleAssembly=stick.group;poleAssembly.position.set(78,0,34);cameras.add(poleAssembly);
let poleHeight=550;
let detailedX6;
let sonyInspectionBounds;
function updatePole() {
  const pose=stick.setLength(poleHeight);
  poleHeight=pose.nominalLength;
  if(detailedX6)detailedX6.position.set(78,0,34+pose.cameraSeat);
  document.querySelector('#height').value=poleHeight;
  document.querySelector('#heightValue').value=`${poleHeight} mm`;
  document.querySelector('#cameraHeight').value=`X6 base: ${pose.cameraSeat} mm above cover`;
  document.querySelector('#height').setAttribute('aria-valuetext',`${poleHeight} millimeter stick; camera base ${pose.cameraSeat} millimeters above cover`);
  document.body.dataset.stickLength=String(poleHeight);
  document.body.dataset.x6BaseZ=String(34+pose.cameraSeat);
}
updatePole();

async function loadDetailedCameras() {
  const cameraLoader=new GLTFLoader();
  const [sonyAsset,x6Asset,lensAsset,mountAsset,sonyMeta,mountMeta]=await Promise.all([
    cameraLoader.loadAsync('./assets/sony-zv-e1.glb'),
    cameraLoader.loadAsync('./assets/insta360-x6.glb'),
    cameraLoader.loadAsync('./assets/sony-selp1635g.glb'),
    cameraLoader.loadAsync('./assets/innorel-c19.glb'),
    fetch('./assets/sony-zv-e1.json').then(r=>{if(!r.ok)throw Error('Missing Sony model metadata');return r.json();}),
    fetch('./assets/innorel-c19.json').then(r=>{if(!r.ok)throw Error('Missing ball-head metadata');return r.json();})
  ]);
  function verifyEnvelope(model,expected,name){
    const size=new THREE.Box3().setFromObject(model).getSize(new THREE.Vector3());
    if(size.toArray().some((v,i)=>Math.abs(v-expected[i])>1))throw Error(`${name} model units/axes need checking: ${size.toArray()}`);
  }
  verifyEnvelope(sonyAsset.scene,[54.3,121,71.9],'Sony');
  verifyEnvelope(x6Asset.scene,[40,50,100],'X6');
  verifyEnvelope(lensAsset.scene,[88.1,80.5,80.5],'Sony lens');
  mountSeatHeight=mountMeta.camera_seating_plane_z_mm;
  if(!Number.isFinite(mountSeatHeight)||mountSeatHeight<20||mountSeatHeight>60)throw Error('Ball-head seating datum needs checking');
  mountAsset.scene.position.set(SONY_MOUNT_X,0,34);cameras.add(mountAsset.scene);
  sonyBaseZ=34+mountSeatHeight;
  const detailedSony=new THREE.Group();
  detailedSony.position.set(SONY_MOUNT_X,0,sonyBaseZ);detailedSony.add(sonyAsset.scene);cameras.add(detailedSony);
  const [flangeX,flangeY,flangeZ]=sonyMeta.lens_axis.face_origin_mm;
  lensAsset.scene.position.set(flangeX,flangeY,flangeZ);detailedSony.add(lensAsset.scene);
  sonyInspectionBounds=new THREE.Box3().setFromObject(detailedSony).union(new THREE.Box3().setFromObject(mountAsset.scene));
  sony.visible=false;
  detailedX6=x6Asset.scene;cameras.add(detailedX6);updatePole();
  document.body.dataset.camerasReady='true';
}

let cover, referenceCover, robot;
let currentView='iso';
let isConcept=true;
let focusMount=true;
let robotBounds;
const conceptNote='Flat printed cover with closed sides and two Ø7 mm clearance holes for 1/4-20 screws. Underside head recesses retained. Hole sizes and fit remain provisional.';
const loader=new STLLoader();
async function loadAssembly() {
  try {
    const [coverGeometry, referenceGeometry, robotGeometry, conceptMeta] = await Promise.all([
      loader.loadAsync('./assets/flat-cover-concept.stl'),loader.loadAsync('./assets/v1-cover.stl'),loader.loadAsync('./assets/a2-robot.stl'),
      fetch('./assets/flat-cover-concept.json').then(r=>{if(!r.ok)throw Error('Missing concept metadata');return r.json();})
    ]);
    cover=new THREE.Mesh(coverGeometry,mats.cover);scene.add(cover);
    referenceCover=new THREE.Mesh(referenceGeometry,mats.reference);referenceCover.visible=false;scene.add(referenceCover);
    robot=new THREE.Mesh(robotGeometry,mats.robot);scene.add(robot);
    robotGeometry.computeBoundingBox();robotBounds=robotGeometry.boundingBox.clone();
    grid.position.z=robotBounds.min.z-5;
    direction.position.set(robotBounds.min.x-45,robotBounds.min.y-30,grid.position.z+2);
    front.position.copy(direction.position).add(new THREE.Vector3(45,-20,0));
    await loadDetailedCameras();
    document.querySelector('#loading').remove();document.body.dataset.ready='true';
    setView('iso');
  }catch(error){document.querySelector('#loading').textContent='Assembly could not load. Refresh when conversion completes.';console.error(error);}
}
function setView(view,preserveDirection=false) {
  currentView=view;
  const tall=isConcept && cameras.visible;
  const bounds=new THREE.Box3(new THREE.Vector3(tall?-180:-165,-125,0),new THREE.Vector3(155,125,tall?poleHeight+156:35));
  if(robot?.visible && robotBounds && !focusMount)bounds.union(robotBounds);
  const center=bounds.getCenter(new THREE.Vector3());
  const radius=bounds.getSize(new THREE.Vector3()).length()/2;
  const effectiveFov=Math.min(camera.fov*Math.PI/180,2*Math.atan(Math.tan(camera.fov*Math.PI/360)*camera.aspect));
  const distance=radius/Math.sin(effectiveFov/2)*0.94;
  const dirs={iso:new THREE.Vector3(-1,-1.35,0.85),top:new THREE.Vector3(0,0.001,1),side:new THREE.Vector3(0,-1,0.001),under:new THREE.Vector3(-0.3,-0.45,-1)};
  const direction=preserveDirection?camera.position.clone().sub(controls.target).normalize():dirs[view].normalize();
  camera.position.copy(center).add(direction.multiplyScalar(distance));
  controls.target.copy(center); controls.update();
  document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===view));
}
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
document.querySelector('#ghost').addEventListener('change',e=>{for(const mat of [mats.cover,mats.reference]){mat.transparent=e.target.checked;mat.opacity=e.target.checked?0.18:1;mat.depthWrite=!e.target.checked;mat.needsUpdate=true;}});
document.querySelector('#robot').addEventListener('change',e=>{if(robot)robot.visible=e.target.checked;document.querySelector('#opacity').disabled=!e.target.checked;setView(currentView);});
document.querySelector('#opacity').addEventListener('input',e=>{const value=Number(e.target.value);mats.robot.opacity=value/100;mats.robot.transparent=value<100;mats.robot.depthWrite=value===100;mats.robot.needsUpdate=true;document.querySelector('#opacityValue').value=`${value}%`;});
document.querySelector('#cameras').addEventListener('change',e=>{cameras.visible=e.target.checked;setView(currentView);});
document.querySelector('#spin').addEventListener('change',e=>controls.autoRotate=e.target.checked);
function changeStickHeight(value){
  if(!isConcept)mode(true);
  cameras.visible=true;document.querySelector('#cameras').checked=true;
  poleHeight=Number(value);updatePole();
  // Retain the viewing angle, but keep the X6 in frame throughout its travel.
  setView(currentView,true);
}
document.querySelector('#height').addEventListener('input',e=>changeStickHeight(e.target.value));
document.querySelectorAll('[data-stick-length]').forEach(b=>b.addEventListener('click',()=>changeStickHeight(b.dataset.stickLength)));
document.querySelector('#stickFit').addEventListener('click',()=>{
  if(!isConcept)mode(true);cameras.visible=true;document.querySelector('#cameras').checked=true;
  focusMount=false;setView('iso');if(window.innerWidth<=620)toggleControlPanel(false);
});
function mode(concept) {
  isConcept=concept;rig.visible=concept;
  if(cover)cover.visible=concept;if(referenceCover)referenceCover.visible=!concept;
  ['concept','original'].forEach(id=>{const on=(id==='concept')===concept;document.querySelector('#'+id).classList.toggle('active',on);document.querySelector('#'+id).setAttribute('aria-pressed',on);});
  document.querySelector('#height').disabled=!concept;
  document.querySelector('#cameras').disabled=!concept;
  document.querySelector('#note').textContent=concept?conceptNote:'Unchanged OEM housing reference, including its original side ports. Switch back to Flat cover to see the closed sides and simple mounting holes.';
  setView('iso');
}
document.querySelector('#concept').addEventListener('click',()=>mode(true));
document.querySelector('#original').addEventListener('click',()=>mode(false));
document.querySelector('#focus').addEventListener('click',()=>{focusMount=true;setView(currentView);});
document.querySelector('#reset').addEventListener('click',()=>{focusMount=false;setView('iso');});
function cameraDetail(kind) {
  if(!isConcept)mode(true);
  cameras.visible=true;document.querySelector('#cameras').checked=true;
  controls.autoRotate=false;document.querySelector('#spin').checked=false;
  const bounds=kind==='sony'?sonyInspectionBounds:new THREE.Box3().setFromObject(detailedX6);
  const target=bounds.getCenter(new THREE.Vector3());
  const direction=kind==='sony'?new THREE.Vector3(-1,-1.25,0.6):new THREE.Vector3(-1,-0.85,0.4);
  const effectiveFov=Math.min(camera.fov*Math.PI/180,2*Math.atan(Math.tan(camera.fov*Math.PI/360)*camera.aspect));
  const distance=bounds.getSize(new THREE.Vector3()).length()/2/Math.sin(effectiveFov/2)*1.08;
  camera.position.copy(target).add(direction.normalize().multiplyScalar(distance));
  controls.target.copy(target);controls.update();
  if(window.innerWidth<=620)toggleControlPanel(false);
  document.querySelectorAll('[data-view]').forEach(b=>b.classList.remove('active'));
}
document.querySelector('#sonyDetail').addEventListener('click',()=>cameraDetail('sony'));
document.querySelector('#x6Detail').addEventListener('click',()=>cameraDetail('x6'));
document.querySelector('#mountDetail').addEventListener('click',()=>{
  if(!isConcept)mode(true);
  cameras.visible=true;document.querySelector('#cameras').checked=true;
  controls.autoRotate=false;document.querySelector('#spin').checked=false;
  const target=new THREE.Vector3(SONY_MOUNT_X,0,34+mountSeatHeight/2);
  camera.position.copy(target).add(new THREE.Vector3(-100,-220,60));
  controls.target.copy(target);controls.update();
  if(window.innerWidth<=620)toggleControlPanel(false);
});
document.querySelector('#recess').addEventListener('click',()=>{
  if(!isConcept)mode(true);
  controls.autoRotate=false;document.querySelector('#spin').checked=false;
  const target=new THREE.Vector3(78,0,20);
  camera.position.copy(target).add(new THREE.Vector3(12,-8,-180));
  controls.target.copy(target);controls.update();
  document.querySelectorAll('[data-view]').forEach(b=>b.classList.remove('active'));
});
const resize=()=>{camera.aspect=viewport.clientWidth/viewport.clientHeight;camera.updateProjectionMatrix();renderer.setSize(viewport.clientWidth,viewport.clientHeight);};
new ResizeObserver(resize).observe(viewport);resize();setView('iso');
loadAssembly();
renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
