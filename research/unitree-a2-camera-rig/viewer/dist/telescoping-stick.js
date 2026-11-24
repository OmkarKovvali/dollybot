import * as THREE from './vendor/three.module.js';

// Reference-based reconstruction of the current 114cm stick (store variant 6989).
// Seven tubes are visible in the official product image. Individual dimensions,
// internal overlap, travel distribution and thread engagement are estimates.
export const STICK = Object.freeze({
  name: 'Insta360 114cm Invisible Selfie Stick — gold-band version',
  minLength: 233, maxLength: 1140, studHeight: 5,
  diameters: [22, 19.6, 17.2, 14.8, 12.4, 10, 7.6],
  baseTubeLength: 205.2, innerTubeLength: 198,
  collapsedStep: 0.8, headHeight: 18, gripHeight: 112,
  source: 'https://store.insta360.com/product/selfie_stick?c=6989'
});

export function stickPose(length) {
  const nominalLength = Math.min(STICK.maxLength, Math.max(STICK.minLength, Number(length)));
  const travel = (nominalLength-STICK.minLength)/6;
  const tops = STICK.diameters.map((_,i)=>STICK.baseTubeLength+i*(STICK.collapsedStep+travel));
  return { nominalLength, travel, tops, cameraSeat: nominalLength-STICK.studHeight,
    segments: tops.map((top,i)=>({ top, bottom: i?top-STICK.innerTubeLength:0,
      overlap: i?STICK.innerTubeLength-STICK.collapsedStep-travel:null })) };
}

function annulus(outer, inner, height) {
  const shape=new THREE.Shape();shape.absarc(0,0,outer,0,Math.PI*2,false);
  const hole=new THREE.Path();hole.absarc(0,0,inner,0,Math.PI*2,true);shape.holes.push(hole);
  return new THREE.ExtrudeGeometry(shape,{depth:height,bevelEnabled:false,curveSegments:48});
}
function tube(parent,name,outer,inner,height,material,z=0) {
  const mesh=new THREE.Mesh(annulus(outer,inner,height),material);
  mesh.name=name;mesh.position.z=z;parent.add(mesh);return mesh;
}
function solidCylinder(parent,name,radius,height,material,z=0) {
  const geometry=new THREE.CylinderGeometry(radius,radius,height,64);
  geometry.rotateX(Math.PI/2);geometry.translate(0,0,height/2);
  const mesh=new THREE.Mesh(geometry,material);mesh.name=name;mesh.position.z=z;parent.add(mesh);return mesh;
}
function helix(parent,name,radius,z0,height,turns,thickness,material,phase=0) {
  const points=[];const steps=Math.ceil(Math.abs(turns)*48);
  for(let i=0;i<=steps;i++){const f=i/steps;const a=phase+f*turns*Math.PI*2;points.push(new THREE.Vector3(radius*Math.cos(a),radius*Math.sin(a),z0+f*height));}
  const mesh=new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points),steps,thickness,5,false),material);
  mesh.name=name;parent.add(mesh);return mesh;
}

export function createTelescopingStick() {
  const group=new THREE.Group();group.name='Insta360_114cm_telescoping_stick_6989';
  const mat={
    aluminum:new THREE.MeshStandardMaterial({color:0x202326,metalness:0.65,roughness:0.42}),
    rubber:new THREE.MeshStandardMaterial({color:0x141719,metalness:0,roughness:0.86}),
    rib:new THREE.MeshStandardMaterial({color:0x26292b,metalness:0,roughness:0.74}),
    gold:new THREE.MeshStandardMaterial({color:0xa99a41,metalness:0.6,roughness:0.46}),
    thread:new THREE.MeshStandardMaterial({color:0xa7adb1,metalness:0.85,roughness:0.27})
  };
  // A true annular bottom cap leaves the 1/4-inch socket visible from beneath.
  tube(group,'bottom_cap_with_female_socket',11.6,3.175,4,mat.rubber);
  tube(group,'female_thread_insert',4.2,2.8,8,mat.thread,0.4);
  helix(group,'female_thread_visual',3.0,0.5,7,7/1.27,0.15,mat.thread);
  const base=tube(group,'fixed_outer_tube',11,10.1,STICK.baseTubeLength-4,mat.aluminum,4);
  tube(group,'rubber_grip',11.8,11,STICK.gripHeight,mat.rubber,2);
  for(let i=0;i<5;i++)helix(group,'diagonal_grip_rib_'+i,11.83,9,96,2.15,0.32,mat.rib,i*Math.PI*2/5);
  tube(group,'grip_top_lip',11.9,10.7,1.6,mat.rubber,STICK.gripHeight+1.8);
  tube(group,'grip_bottom_lip',11.9,3.175,1.4,mat.rubber,0);
  const sections=[base];
  for(let i=1;i<7;i++){
    const part=new THREE.Group();part.name='sliding_section_'+i;
    const r=STICK.diameters[i]/2;
    tube(part,'hollow_tube_'+i,r,r-0.65,STICK.innerTubeLength,mat.aluminum);
    group.add(part);sections.push(part);
  }
  const bands=[];
  for(let i=0;i<6;i++){
    const band=tube(group,'gold_joint_band_'+i,STICK.diameters[i]/2+0.08,STICK.diameters[i+1]/2+0.15,4.3,mat.gold);
    bands.push(band);
  }
  const head=new THREE.Group();head.name='knurled_camera_mount';group.add(head);
  solidCylinder(head,'knurled_head_body',7.8,17,mat.aluminum);
  for(let i=0;i<20;i++){
    helix(head,'head_knurl_forward_'+i,7.85,1.5,14,0.36,0.19,mat.rib,i*Math.PI/10);
    helix(head,'head_knurl_reverse_'+i,7.85,1.5,14,-0.36,0.19,mat.rib,i*Math.PI/10);
  }
  solidCylinder(head,'camera_contact_rubber',7.8,1,mat.rubber,17);
  solidCylinder(head,'quarter_twenty_stud_core',2.65,STICK.studHeight,mat.thread,18);
  helix(head,'quarter_twenty_stud_thread',2.92,18.2,4.5,4.5/1.27,0.25,mat.thread);
  // Branding follows the fixed tube; never stretches with the pole.
  if(typeof document!=='undefined'){
    const canvas=document.createElement('canvas');canvas.width=512;canvas.height=128;
    const ctx=canvas.getContext('2d');ctx.fillStyle='#dfe2e3';ctx.font='600 72px Arial';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('Insta360',256,64);
    const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;
    const logo=new THREE.Mesh(new THREE.PlaneGeometry(41,10.25),new THREE.MeshBasicMaterial({map:texture,transparent:true,depthWrite:false,side:THREE.DoubleSide}));
    logo.name='Insta360_wordmark';logo.rotation.set(Math.PI/2,0,Math.PI/2);logo.position.set(0,-11.04,155);group.add(logo);
  }
  function setLength(value){
    const pose=stickPose(value);
    for(let i=1;i<7;i++)sections[i].position.z=pose.segments[i].bottom;
    for(let i=0;i<6;i++)bands[i].position.z=pose.tops[i]-4.3;
    head.position.z=pose.cameraSeat-STICK.headHeight;
    group.userData={...pose,model:'6989',dimensionStatus:'reference-based estimates'};
    return pose;
  }
  setLength(STICK.minLength);
  return {group,setLength};
}
