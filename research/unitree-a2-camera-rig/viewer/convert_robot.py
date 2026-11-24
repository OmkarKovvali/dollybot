"""Extract the OEM A2 body from its V1-dock assembly, registered by geometry."""
from pathlib import Path
from collections import defaultdict
import hashlib, json, math, struct
import gmsh

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "dist/assets"
RESEARCH = ROOT.parent / "v1-cover-update/cover-research"
ASSEMBLY = RESEARCH / "unitree-a2-with-v1-docking-station.stp"
COVER = RESEARCH / "unitree-a2-v1-docking-station-20260509.stp"
COVER_META = json.loads((ASSETS / "cover-mesh.json").read_text())

def boundary(dimtags, recursive=False):
    return sorted(set(gmsh.model.getBoundary(dimtags, combined=False, oriented=False, recursive=recursive)))

def xy_circle(tag):
    lo, hi = gmsh.model.getParametrizationBounds(1, tag)
    ts = [float(lo[0]), (float(lo[0])+float(hi[0]))/2, float(hi[0])]
    p = [list(gmsh.model.getValue(1, tag, [t])) for t in ts]
    if max(v[2] for v in p)-min(v[2] for v in p) > 1e-6: return None
    (x1,y1,z1),(x2,y2,z2),(x3,y3,z3)=p
    den=2*(x1*(y2-y3)+x2*(y3-y1)+x3*(y1-y2))
    if abs(den)<1e-7: return None
    cx=((x1*x1+y1*y1)*(y2-y3)+(x2*x2+y2*y2)*(y3-y1)+(x3*x3+y3*y3)*(y1-y2))/den
    cy=((x1*x1+y1*y1)*(x3-x2)+(x2*x2+y2*y2)*(x1-x3)+(x3*x3+y3*y3)*(x2-x1))/den
    return (cx,cy,z1,math.hypot(cx-x1,cy-y1))

def ear_centers(volume):
    faces=boundary([(3,volume)])
    circles=[]
    for _,t in boundary(faces):
        if gmsh.model.getType(1,t)!="Circle": continue
        c=xy_circle(t)
        if c and abs(c[3]-3.1)<1e-5: circles.append(c)
    zmin=min(c[2] for c in circles)
    unique={tuple(round(v,7) for v in c[:3]) for c in circles if abs(c[2]-zmin)<1e-5}
    if len(unique)!=4: raise ValueError(f"Expected 4 outer ear centers, got {len(unique)}")
    return sorted(unique)

def top_face(volume):
    candidates=[]
    for d,t in boundary([(3,volume)]):
        if gmsh.model.getType(d,t)!="Plane": continue
        box=gmsh.model.getBoundingBox(d,t)
        area=gmsh.model.occ.getMass(d,t)
        if abs(box[5]-box[2])<0.001 and area>10000:
            candidates.append((gmsh.model.occ.getCenterOfMass(d,t)[2],area,t))
    return max(candidates)

def bounds(points):
    return {"min":[min(p[i] for p in points) for i in range(3)],"max":[max(p[i] for p in points) for i in range(3)]}

gmsh.initialize()
try:
    gmsh.option.setNumber("General.Terminal",0)
    cache=Path('/private/tmp/unitree-a2-v1-assembly-import-cache.brep')
    gmsh.model.occ.importShapes(str(cache if cache.exists() else ASSEMBLY));gmsh.model.occ.synchronize()
    if not cache.exists(): gmsh.write(str(cache))
    original_volumes=[t for _,t in gmsh.model.getEntities(3)]
    # Unique thin rectangular housing; then validate it using mounting circles
    # and the complete broad top-face vertices against the standalone cover.
    dock_candidates=[]
    for t in original_volumes:
        box=gmsh.model.getBoundingBox(3,t);dims=[box[i+3]-box[i] for i in range(3)]
        if all(abs(a-b)<2 for a,b in zip(dims,(301.13,232.62,35.12))): dock_candidates.append(t)
    if len(dock_candidates)!=1: raise ValueError(f"Ambiguous dock: {dock_candidates}")
    dock=dock_candidates[0]
    standalone=gmsh.model.occ.importShapes(str(COVER));gmsh.model.occ.synchronize()
    standalone_volume=next(t for d,t in standalone if d==3)
    assembly_centers=ear_centers(dock);standalone_centers=ear_centers(standalone_volume)
    translations=[[b[i]-a[i] for i in range(3)] for a,b in zip(assembly_centers,standalone_centers)]
    to_standalone=[sum(t[i] for t in translations)/4 for i in range(3)]
    residual=max(math.dist(t,to_standalone) for t in translations)
    if residual>0.01: raise ValueError(f"Mounting geometry registration residual {residual}")
    assembly_top=top_face(dock);standalone_top=top_face(standalone_volume)
    av=[list(gmsh.model.getValue(0,t,[])) for _,t in boundary([(2,assembly_top[2])],True)]
    sv=[list(gmsh.model.getValue(0,t,[])) for _,t in boundary([(2,standalone_top[2])],True)]
    moved=[[p[i]+to_standalone[i] for i in range(3)] for p in av]
    hausdorff=max(max(min(math.dist(a,b) for b in sv) for a in moved),max(min(math.dist(b,a) for a in moved) for b in sv))
    # The two revisions use different edge segmentation (2 versus23 top-face
    # vertices), so vertex Hausdorff distance does not test surface alignment.
    # Use the asymmetric housing's XY extrema and actual top-plane height as
    # independent checks of the mounting-circle registration and orientation.
    abox=gmsh.model.getBoundingBox(3,dock);sbox=gmsh.model.getBoundingBox(3,standalone_volume)
    xy_residual=max(abs(abox[k]+to_standalone[k%3]-sbox[k]) for k in (0,1,3,4))
    top_residual=abs(assembly_top[0]+to_standalone[2]-standalone_top[0])
    if xy_residual>0.01 or top_residual>0.01: raise ValueError(f"Housing registration failed XY={xy_residual}, top={top_residual}")
    offset=[to_standalone[i]+COVER_META['transform']['normalized_equals_original_plus_mm'][i] for i in range(3)]
    registration={"assembly_dock_volume_tag":dock,"assembly_volume_count":len(original_volumes),"robot_volume_count":len(original_volumes)-1,"assembly_to_standalone_translation_mm":to_standalone,"assembly_to_viewer_translation_mm":offset,"rotation_degrees":[0,0,0],"scale":1,"four_ear_center_registration_max_residual_mm":residual,"asymmetric_housing_xy_bbox_residual_mm":xy_residual,"top_plane_z_residual_mm":top_residual,"top_face_vertex_counts":[len(av),len(sv)],"assembly_top_z_mm":assembly_top[0],"standalone_top_z_mm":standalone_top[0],"assembly_dock_volume_mm3":gmsh.model.occ.getMass(3,dock),"standalone_dock_volume_mm3":gmsh.model.occ.getMass(3,standalone_volume),"note":"Registration uses four actual ear-hole circles, checked against asymmetric XY housing extents and top-plane height. Dock revisions have different volume and edge segmentation; internal geometry is not claimed identical."}
    (ASSETS/'robot-registration.json').write_text(json.dumps(registration,indent=2));print(json.dumps(registration),flush=True)
    gmsh.model.occ.remove([(3,dock),(3,standalone_volume)],recursive=True);gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature",16)
    gmsh.option.setNumber("Mesh.MeshSizeMin",2.0)
    gmsh.option.setNumber("Mesh.MeshSizeMax",14.0)
    gmsh.option.setNumber("Mesh.Algorithm",6)
    gmsh.option.setNumber("Mesh.ElementOrder",1)
    gmsh.option.setNumber("General.NumThreads",8)
    gmsh.option.setNumber("Mesh.MaxNumThreads2D",8)
    gmsh.model.mesh.generate(2)
    gmsh.option.setNumber("Mesh.Binary",1)
    gmsh.write('/private/tmp/a2-robot-registered-mesh.msh')
    tags,coords,_=gmsh.model.mesh.getNodes()
    points={int(t):tuple(float(coords[3*j+i])+offset[i] for i in range(3)) for j,t in enumerate(tags)}
    types,_,connectivity=gmsh.model.mesh.getElements(2)
    triangles=[]
    for typ,conn in zip(types,connectivity):
        if int(typ)!=2: raise ValueError(f"Unexpected non-triangle type {typ}")
        triangles.extend(tuple(int(x) for x in conn[i:i+3]) for i in range(0,len(conn),3))
    if not triangles: raise ValueError("No triangles generated")
    mesh=ASSETS/'a2-robot.stl'
    with mesh.open('wb') as f:
        f.write(b'Official A2 assembly minus V1 dock; registered to actual V1 mesh'.ljust(80,b' '));f.write(struct.pack('<I',len(triangles)))
        for tri in triangles:
            a,b,c=(points[t] for t in tri);u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
            n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];length=math.sqrt(sum(x*x for x in n));n=[x/length for x in n] if length else [0,0,0]
            f.write(struct.pack('<12fH',*n,*a,*b,*c,0))
    # Dense vertical samples over the full proposed 46-mm mount footprint.
    # This is a mesh clearance estimate, not a physical measurement.
    footprint_triangles=[]
    for tri in triangles:
        vertices=[points[t] for t in tri]
        if max(p[0] for p in vertices)<55 or min(p[0] for p in vertices)>101 or max(p[1] for p in vertices)<-23 or min(p[1] for p in vertices)>23: continue
        footprint_triangles.append(vertices)
    def highest_at(x,y):
        zs=[]
        for a,b,c in footprint_triangles:
            det=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(det)<1e-12:continue
            u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/det
            v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/det
            w=1-u-v
            if min(u,v,w)>=-1e-8:zs.append(u*a[2]+v*b[2]+w*c[2])
        return max(zs) if zs else None
    samples=[]
    for dx in range(-23,24):
        for dy in range(-23,24):
            if dx*dx+dy*dy<=23*23:
                z=highest_at(78+dx,dy)
                if z is not None:samples.append((78+dx,dy,z))
    for n in range(360):
        angle=math.radians(n);x=78+23*math.cos(angle);y=23*math.sin(angle);z=highest_at(x,y)
        if z is not None:samples.append((x,y,z))
    peak=max(samples,key=lambda p:p[2]);center=highest_at(78,0)
    clearance={"method":"Vertical ray intersection against the converted OEM robot mesh; 1-mm disk grid plus360 perimeter rays","pole_center_xy_mm":[78,0],"footprint_radius_mm":23,"robot_top_at_center_z_mm":center,"highest_sampled_robot_surface_xyz_mm":peak,"sample_count":len(samples),"clearance_from_cover_bottom_z0_mm":-peak[2],"clearance_from_concept_boss_bottom_z20_mm":20-peak[2],"clearance_from_cover_top_z34_mm":34-peak[2],"limitations":["Sampled tessellation estimate; local small omitted geometry or unsampled peaks can differ.","Does not certify a collision-free insertion path, tool access, fastener head clearance, tolerance, flex or dynamic motion.","OEM simplified geometry and assembly revision must be physically checked; no robot disassembly performed."]}
    used={t for tri in triangles for t in tri};mesh_bounds=bounds([points[t] for t in used])
    metadata={"source":str(ASSEMBLY),"source_sha256":hashlib.sha256(ASSEMBLY.read_bytes()).hexdigest(),"mesh":mesh.name,"mesh_sha256":hashlib.sha256(mesh.read_bytes()).hexdigest(),"units":"mm","triangle_count":len(triangles),"vertex_count":len(used),"bytes":mesh.stat().st_size,"normalized_mesh_bounds_mm":mesh_bounds,"registration":registration,"pole_footprint_clearance":clearance,"notes":["Actual official A2 assembly with its dock volume excluded, not an invented robot shape.","Geometry preserved except rigid translation; no robot parts resized, rotated, or reshaped.","47 placed volume instances retained. Source contains45 BREP definitions; reused instances increase imported count.","Snapshot pose only; limb-motion clearance is not tested."]}
    collision_path=ASSETS/'cover-body-intersection.json'
    if collision_path.exists():
        collision=json.loads(collision_path.read_text())
        metadata['exact_cad_collision_check']=collision_path.name
        metadata['exact_robot_roof_at_pole_axis_z_mm']=collision['robot_top_at_exact_pole_axis_z_mm']
        metadata['provisional_head_axis_clearance_mm']=collision.get('provisional_screw_head_axis_clearance_mm')
        metadata['notes'].append('Use the separate exact CAD Boolean/line collision check for interference conclusions; coarse mesh samples are visualization estimates.')
    metadata['front_direction_status']='unverified; source orientation preserved'
    (ASSETS/'robot-mesh.json').write_text(json.dumps(metadata,indent=2));print(json.dumps(metadata,indent=2),flush=True)
finally:
    gmsh.finalize()
