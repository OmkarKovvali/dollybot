import json, math, struct, sys, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parent
meshes=[]
for p in sorted((ROOT/'official-a2/meshes').glob('*.STL')):
 b=p.read_bytes();n=struct.unpack_from('<I',b,80)[0];lo=[float('inf')]*3;hi=[float('-inf')]*3;tri=[]
 assert len(b)==84+50*n
 for i in range(n):
  f=struct.unpack_from('<12f',b,84+50*i);v=[f[3:6],f[6:9],f[9:12]]
  for q in v:
   for k,x in enumerate(q):lo[k]=min(lo[k],x);hi[k]=max(hi[k],x)
  if p.name=='base_link.STL': tri.append((f[:3],v))
 row={'name':p.name,'triangles':n,'bounds_m':[lo,hi],'dimensions_mm':[(hi[k]-lo[k])*1000 for k in range(3)]};meshes.append(row)
 if p.name=='base_link.STL': base=tri
r=ET.parse(ROOT/'official-a2/urdf/a2.urdf').getroot()
analysis={'mesh_units':'meters as used by URDF; STL is unitless. Import at 1000x if CAD expects mm.','total_triangles':sum(x['triangles'] for x in meshes),'meshes':meshes,'urdf_link_count':len(r.findall('link')),'urdf_joint_count':len(r.findall('joint')),'actuated_joint_count':sum(x.attrib['type']=='revolute' for x in r.findall('joint')),'urdf_total_link_mass_kg':sum(float(x.attrib['value']) for x in r.findall('.//mass')),'joints':[dict(name=j.attrib['name'],type=j.attrib['type'],parent=j.find('parent').attrib['link'],child=j.find('child').attrib['link'],origin=j.find('origin').attrib) for j in r.findall('joint')]}
(ROOT/'mesh-analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
s=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="940" viewBox="0 0 1400 940">','<rect width="1400" height="940" fill="#f8fafb"/>','<g fill="#172b40" font-family="Arial,sans-serif"><text x="45" y="43" font-size="27" font-weight="bold">Official A2 base mesh — inspected geometry</text><text x="45" y="72" font-size="16">Unitree ROS cdf67e6 · STL visual surface, not a dimensioned fabrication drawing</text></g>']
for title,ybase,view in [('TOP VIEW / +Z',150,2),('SIDE VIEW / −Y',595,1)]:
 s.append(f'<text x="45" y="{ybase-30}" font-family="Arial" font-size="19" font-weight="bold" fill="#172b40">{title}</text>')
 axisv=1 if view==2 else 2
 scale=1600
 cx=650;cy=ybase+170
 ts=sorted(base,key=lambda t:sum(v[view] for v in t[1])*(1 if view==2 else -1))
 for normal,v in ts:
  n=(normal[2] if view==2 else -normal[1])
  if n<-.001:continue
  shade=int(95+145*max(0,min(1,n)))
  pts=' '.join(f'{cx+p[0]*scale:.2f},{cy-p[axisv]*scale:.2f}' for p in v)
  s.append(f'<polygon points="{pts}" fill="rgb({shade},{shade},{min(255,shade+8)})"/>')
 s.append(f'<text x="1160" y="{ybase+330}" font-family="Arial" font-size="15" fill="#236b84">+X FRONT →</text>')
s.append('<g fill="#172b40" font-family="Arial" font-size="16"><text x="45" y="903">Base envelope: 715.10 × 286.37 × 210.55 mm · 68,422 triangles · mount threads, tolerances and load rating unspecified</text></g></svg>')
(ROOT/'base-mesh-inspection.svg').write_text('\n'.join(s))
print('Saved geometry analysis and SVG inspection view')
