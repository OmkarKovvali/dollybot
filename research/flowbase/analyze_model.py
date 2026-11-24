import hashlib,json,math,pathlib,struct,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).parent
MODEL=ROOT/'i2rt/robot_models/linearbot'
xml=ET.parse(MODEL/'linearbot.urdf').getroot()
def vec(s): return [float(x) for x in s.split()]
def origin(node):
 o=node.find('origin');return (vec(o.get('xyz','0 0 0')),vec(o.get('rpy','0 0 0'))) if o is not None else ([0,0,0],[0,0,0])
def mm(a,b): return [[sum(a[i][k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]
def rot(v):
 r,p,y=v;cr,sr,cp,sp,cy,sy=math.cos(r),math.sin(r),math.cos(p),math.sin(p),math.cos(y),math.sin(y)
 return [[cy*cp,cy*sp*sr-sy*cr,cy*sp*cr+sy*sr],[sy*cp,sy*sp*sr+cy*cr,sy*sp*cr-cy*sr],[-sp,cp*sr,cp*cr]]
def rv(r,v):return [sum(a*b for a,b in zip(row,v)) for row in r]
def plus(a,b):return [x+y for x,y in zip(a,b)]
def minus(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(v):return math.sqrt(dot(v,v))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def sign(x):return 1 if x>=0 else -1
links={x.get('name'):x for x in xml.findall('link')}; joints={}
for j in xml.findall('joint'):
 p,r=origin(j);axis=j.find('axis');joints[j.get('name')]={'name':j.get('name'),'type':j.get('type'),'parent':j.find('parent').get('link'),'child':j.find('child').get('link'),'xyz':p,'rpy':r,'axis':vec(axis.get('xyz')) if axis is not None else [0,0,1]}
world={'root':([0,0,0],rot([0,0,0]))}
while len(world)<len(links):
 for j in joints.values():
  if j['parent'] in world and j['child'] not in world:
   p,r=world[j['parent']]; world[j['child']]=(plus(p,rv(r,j['xyz'])),mm(r,rot(j['rpy'])))
geometry=[]
for name,link in links.items():
 visual=link.find('visual')
 if visual is None:continue
 mesh=visual.find('geometry/mesh');vp,vr=origin(visual);lp,lr=world[name];p=plus(lp,rv(lr,vp));r=mm(lr,rot(vr));path=MODEL/mesh.get('filename');buf=path.read_bytes();n=struct.unpack_from('<I',buf,80)[0]
 lo=[float('inf')]*3;hi=[float('-inf')]*3
 for k in range(n):
  for off in (12,24,36):
   v=vec(' '.join(str(x) for x in struct.unpack_from('<fff',buf,84+50*k+off)))
   w=plus(p,rv(r,v))
   lo=[min(a,b) for a,b in zip(lo,w)];hi=[max(a,b) for a,b in zip(hi,w)]
 geometry.append({'link':name,'mesh':mesh.get('filename'),'units':'meters','visual_xyz':vp,'visual_rpy':vr,'root_zero_xyz':p,'root_zero_rotation_matrix':r,'root_zero_aabb':{'min':lo,'max':hi,'size':minus(hi,lo)},'triangles':n})
casters=[]
for name,steer,drive,hx,hy in [('rear-left',1,2,-.2,.2),('front-left',3,4,.2,.2),('front-right',5,6,.2,-.2),('rear-right',7,8,-.2,-.2)]:
 s=joints[f'dof_joint{steer}'];d=joints[f'dof_joint{drive}'];sp,sr=world[s['child']];dp,dr=world[d['child']];axis=rv(dr,d['axis']);trail=minus(dp,sp);heading=[-(t-a*dot(trail,axis)) for t,a in zip(trail,axis)];heading=[x/norm(heading) for x in heading]
 casters.append({'name':name,'controller_hip_xy':[hx,hy],'model_steer_anchor':sp,'steer_joint':s['name'],'steer_link':s['child'],'drive_joint':d['name'],'drive_link':d['child'],'steer_sign':sign(rv(sr,s['axis'])[2]),'heading_at_joint_zero':math.atan2(heading[1],heading[0]),'drive_sign':sign(dot(axis,cross([0,0,1],heading)))})
base=[g for g in geometry if g['link']=='base' or g['link'].startswith('motor')]
lo=[min(g['root_zero_aabb']['min'][i] for g in base) for i in range(3)];hi=[max(g['root_zero_aabb']['max'][i] for g in base) for i in range(3)]
out={'source_commit':'8c1b3ab6b6f31ae11e8b5f1e46c037d154199938','units':'meters','frame':'+x forward, +y left, +z up; root at floor and caster center','base_assembled_zero_pose_aabb':{'min':lo,'max':hi,'size':minus(hi,lo)},'joints':list(joints.values()),'geometry':geometry,'casters_controller_order':casters,'joint_pose_formula':{'steer':'q = steer_sign * (controller_steer - heading_at_joint_zero)','drive':'q = drive_sign * controller_drive'}}
(ROOT/'model-mapping.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'base_bounds':out['base_assembled_zero_pose_aabb'],'casters':casters},indent=2))
