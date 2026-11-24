"""Revision 05: solid sidewalls, unraised OEM top, two payload clearance holes.
Derived visualization/concept geometry only, not print-ready. Preserves original
sources and prior revisions. Run with /private/tmp/trebor-cad-tools/bin/python.
"""
from pathlib import Path
import hashlib,json,math,struct,time,os,subprocess
import gmsh
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'dist/assets'
SOURCE_META=json.loads((DEST/'cover-mesh.json').read_text())
SOURCE=Path(SOURCE_META['source'])
OFFSET=SOURCE_META['transform']['normalized_equals_original_plus_mm']
SOURCE_STL=DEST/SOURCE_META['mesh']
OUTPUT=DEST/'flat-cover-concept.stl'
META=DEST/'flat-cover-concept.json'
BREP=DEST/'flat-cover-concept.brep'
START=time.time()
TOP=SOURCE_META['top_surface']['normalized_z_mm']
SEAT=27.0
CAMERA_X=float(os.environ.get('A2_CAMERA_X_MM','-48.0'))
MOUNTS=[{'name':'camera','center_xy_mm':[CAMERA_X,0.0]},{'name':'stick','center_xy_mm':[78.0,0.0]}]
FILL_BANDS=[{'name':'positive_y_side','min_mm':[-74.0,61.20,4.80],'max_mm':[68.0,79.75,27.50]},
            {'name':'negative_y_side','min_mm':[-74.0,-79.75,4.80],'max_mm':[68.0,-61.20,27.50]}]

def log(message):
    print(f'[{time.time() - START:.1f}s] {message}', flush=True)


def stl_triangles(path):
    b = path.read_bytes()
    n = struct.unpack_from('<I', b, 80)[0]
    if len(b) != 84 + 50 * n:
        raise ValueError('Binary STL size mismatch')
    out = []
    for i in range(n):
        f = struct.unpack_from('<12fH', b, 84 + 50 * i)
        out.append((f[3:6], f[6:9], f[9:12]))
    return out


def vertical_sections(triangles, xy_points):
    """Actual tessellated-surface Z intersections along vertical rays.

    Probes are away from tangent circular boundaries. Duplicate triangle-edge
    crossings collapse at 1e-4 mm. This is a cross-check, not structural proof.
    """
    hits = [[] for _ in xy_points]
    for a, b, c in triangles:
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        xmin, xmax = min(a[0], b[0], c[0]), max(a[0], b[0], c[0])
        ymin, ymax = min(a[1], b[1], c[1]), max(a[1], b[1], c[1])
        for k, (x, y) in enumerate(xy_points):
            if not xmin-1e-6 <= x <= xmax+1e-6 or not ymin-1e-6 <= y <= ymax+1e-6:
                continue
            u = ((b[1]-c[1])*(x-c[0]) + (c[0]-b[0])*(y-c[1])) / den
            v = ((c[1]-a[1])*(x-c[0]) + (a[0]-c[0])*(y-c[1])) / den
            if u >= -1e-7 and v >= -1e-7 and u+v <= 1+1e-7:
                hits[k].append(u*a[2] + v*b[2] + (1-u-v)*c[2])
    result = []
    for xy, raw in zip(xy_points, hits):
        unique = []
        for z in sorted(raw):
            if not unique or abs(z-unique[-1]) > 1e-4:
                unique.append(z)
        result.append({'xy_mm': list(xy), 'surface_intersections_z_mm': unique})
    return result


def circle_points(cx, cy, radius, count=8):
    return [(cx+radius*math.cos(i*2*math.pi/count), cy+radius*math.sin(i*2*math.pi/count)) for i in range(count)]


def mass(volumes):
    return sum(gmsh.model.occ.getMass(dim, tag) for dim, tag in volumes)


def bounds(points):
    return {'min': [min(p[i] for p in points) for i in range(3)], 'max': [max(p[i] for p in points) for i in range(3)]}


source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
source_triangles=stl_triangles(SOURCE_STL)
for mount in MOUNTS:
    cx,cy=mount['center_xy_mm']
    mount['source_axis_section']=vertical_sections(source_triangles,[(cx,cy)])[0]
    mount['source_opening_boundary_sections']=vertical_sections(source_triangles,circle_points(cx,cy,6.0))
    z=mount['source_axis_section']['surface_intersections_z_mm']
    if len(z)!=2:raise ValueError(f'Unexpected source material at {mount["name"]}: {z}')
    mount['counterbore']={'diameter_mm':12.0,'bottom_z_mm':z[0],'depth_mm':SEAT-z[0],
        'seat_z_mm':SEAT,'head_bottom_z_mm':20.5,'head_top_z_mm':27.0,
        'provisional_head_max_diameter_mm':10.5,'provisional_head_max_height_mm':6.5,
        'access_opening_z_mm':z[0],'access_well_total_depth_mm':SEAT-z[0],
        'provisional':True,'note':'Accessible from the underside. Actual well depth extends to the local source underside; head size remains provisional.'}
    mount['through_bore']={'diameter_mm':7.0,'provisional':True}
log('Source axis sections inspected; importing unchanged OEM STEP')
gmsh.initialize()
try:
    gmsh.option.setNumber('General.Terminal',0)
    imported=gmsh.model.occ.importShapes(str(SOURCE));gmsh.model.occ.translate(imported,*OFFSET);gmsh.model.occ.synchronize()
    original=gmsh.model.getEntities(3)
    if len(original)!=1:raise ValueError('Expected single source solid')
    original_mass=mass(original)
    # Close the OEM lid groove by extruding its actual planar annular floor.
    # The floor is at top-3 mm; this adds no top height or underside material.
    groove_candidates=[]
    for dim,tag in gmsh.model.getEntities(2):
        if gmsh.model.getType(dim,tag) != 'Plane':continue
        area=gmsh.model.occ.getMass(dim,tag);center=gmsh.model.occ.getCenterOfMass(dim,tag)
        if 140 < area < 150 and abs(center[2]-(TOP-3)) < .0001:
            groove_candidates.append((tag,area,center[2]))
    if len(groove_candidates)!=1:raise ValueError(f'Ambiguous OEM groove floor: {groove_candidates}')
    groove_tag,groove_area,groove_bottom=groove_candidates[0]
    extruded=gmsh.model.occ.extrude([(2,groove_tag)],0,0,TOP-groove_bottom)
    groove_volumes=[(d,t)for d,t in extruded if d==3]
    original,_=gmsh.model.occ.fuse(original,groove_volumes,removeObject=True,removeTool=True)
    gmsh.model.occ.synchronize()
    if len(gmsh.model.getEntities(3))!=1:raise ValueError('Groove closure did not remain one solid')
    seam_closed_mass=mass(gmsh.model.getEntities(3))
    original=gmsh.model.getEntities(3)
    log(f'Closed OEM top groove at unchanged top Z{TOP:.5f}; added volume {seam_closed_mass-original_mass:.3f} mm3')
    # Fill only the connector-row regions, above the existing lower floor. The
    # outer side face is approximately Y=+/-79.75. Curved shoulders, ear mounts,
    # housing bottom and outer plan footprint are untouched by these bands.
    fills=[]
    for band in FILL_BANDS:
        lo,hi=band['min_mm'],band['max_mm']
        tag=gmsh.model.occ.addBox(*lo,*[hi[i]-lo[i]for i in range(3)])
        fills.append((3,tag))
    fused,_=gmsh.model.occ.fuse(original,fills,removeObject=True,removeTool=True);gmsh.model.occ.synchronize()
    fused_vols=gmsh.model.getEntities(3)
    if len(fused_vols)!=1:raise ValueError('Side fills did not merge into one solid')
    filled_mass=mass(fused_vols)
    gmsh.write(str(DEST/'flat-cover-filled-base.brep'))
    log(f'Closed side connector rows with solid fills; added volume {filled_mass-original_mass:.3f} mm3')
    cutters=[]
    for mount in MOUNTS:
        cx,cy=mount['center_xy_mm']
        cutters.append((3,gmsh.model.occ.addCylinder(cx,cy,-1,0,0,36,3.5)))
        cutters.append((3,gmsh.model.occ.addCylinder(cx,cy,-1,0,0,SEAT+1,6.0)))
    result,_=gmsh.model.occ.cut(fused_vols,cutters,removeObject=True,removeTool=True);gmsh.model.occ.synchronize()
    volumes=gmsh.model.getEntities(3)
    if len(volumes)!=1:raise ValueError('Expected one closed derived solid')
    final_mass=mass(volumes)
    gmsh.write(str(BREP))
    log(f'BREP READY {BREP} SHA256={hashlib.sha256(BREP.read_bytes()).hexdigest()}')
    # Specific original port/mount-hole centers, including small adjacent holes.
    side_tests=[]
    positive=[(-60.84099,14.8),(-40.34099,14.8),(-19.84099,14.8),(0.65901,14.8),(20.30901,17.25),(36.80901,17.25),(53.30901,17.25),(-71.09099,22),(-50.59099,22),(-30.09099,22),(-9.59099,22),(10.90901,22),(20.30901,24.7),(36.80901,24.7),(53.30901,24.7)]
    negative=[(-60.04099,14.8),(-33.24099,14.8),(-6.44099,14.8),(20.80901,17.25),(37.30901,17.25),(55.54049,17.8603),(-69.04099,23.8),(-51.04099,23.8),(-42.24099,23.8),(-24.24099,23.8),(-15.44099,23.8),(2.55901,23.8),(20.80901,24.7),(37.30901,24.7),(46.04049,25.1),(65.04049,25.1)]
    for side,tests in [(1,positive),(-1,negative)]:
        for x,z in tests:
            actual=bool(gmsh.model.isInside(3,volumes[0][1],[x,side*79.5,z]))
            side_tests.append({'xyz_mm':[x,side*79.5,z],'material_present':actual})
            if not actual:raise ValueError(f'Unclosed side opening at {x,side,z}')
    log('31 original connector/small-hole points confirmed solid; meshing derived surface')
    # Direct OCCT tessellation handles the valid but tiny periodic BSpline face
    # that Gmsh's 2D mesher rejects after the side-port Boolean union.
    ocp_python=Path(os.environ.get('A2_OCP_PYTHON','/private/tmp/a2-ocp-tools/bin/python'))
    ocp_code="""
import sys,json
from OCP.TopoDS import TopoDS_Shape
from OCP.BRep import BRep_Builder
from OCP.BRepTools import BRepTools
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer
from OCP.BRepCheck import BRepCheck_Analyzer
s=TopoDS_Shape()
assert BRepTools.Read_s(s,sys.argv[1],BRep_Builder())
valid=BRepCheck_Analyzer(s).IsValid()
assert valid
m=BRepMesh_IncrementalMesh(s,.08,False,.20,True)
assert m.IsDone()
flags=m.GetStatusFlags()
assert not flags & (1|2|4|16|32|256), flags
w=StlAPI_Writer();w.ASCIIMode=False
assert w.Write(s,sys.argv[2])
print(json.dumps({'brep_valid':valid,'status_flags':flags,'status_128_means':'IMeshData_Reused; not an error','linear_deflection_mm':.08,'angular_deflection_radians':.20}))
"""
    outcome=subprocess.run([str(ocp_python),'-c',ocp_code,str(BREP),str(OUTPUT)],check=True,text=True,capture_output=True)
    tessellation=json.loads(outcome.stdout.strip().splitlines()[-1])
    raw_triangles=stl_triangles(OUTPUT)
    # Weld shared face-edge vertices at 0.0001 mm and discard collapsed
    # triangles, producing a closed indexed surface for the delivered STL.
    vertex_ids={};points={};triangles=[];collapsed=0
    for triangle in raw_triangles:
        ids=[]
        for v in triangle:
            key=tuple(round(x,4)for x in v)
            if key not in vertex_ids:
                tag=len(vertex_ids)+1;vertex_ids[key]=tag;points[tag]=key
            ids.append(vertex_ids[key])
        if len(set(ids))<3:
            collapsed+=1;continue
        triangles.append(tuple(ids))
    # Replace collapsed sliver-face fans with conforming subdivisions of the
    # neighbouring nonzero-area triangles. Removing the zero faces alone would
    # leave T-junctions; this partitions the same planar triangles, not the CAD.
    def area2(tri):
        a,b,c=(points[i]for i in tri);u=[b[i]-a[i]for i in range(3)];v=[c[i]-a[i]for i in range(3)]
        n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        return sum(q*q for q in n)
    zero_triangles=[t for t in triangles if area2(t)<1e-20]
    zero_vertices={v for t in zero_triangles for v in t}
    repaired=[];split_count=0
    for tri in triangles:
        if area2(tri)<1e-20:continue
        polygon=[];added=False
        for ai,bi in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:
            a,b=points[ai],points[bi];d=[b[i]-a[i]for i in range(3)];length2=sum(v*v for v in d)
            polygon.append(ai);inserts=[]
            for pi in zero_vertices:
                if pi in (ai,bi):continue
                q=points[pi];t=sum((q[i]-a[i])*d[i]for i in range(3))/length2
                if not 1e-9<t<1-1e-9:continue
                distance2=sum((q[i]-a[i]-t*d[i])**2 for i in range(3))
                if distance2<1e-14:inserts.append((t,pi))
            if inserts:
                added=True;polygon.extend(pi for _,pi in sorted(inserts))
        if not added:repaired.append(tri);continue
        center=tuple(sum(points[i][k]for i in tri)/3 for k in range(3))
        ci=max(points)+1;points[ci]=center
        for i in range(len(polygon)):repaired.append((ci,polygon[i],polygon[(i+1)%len(polygon)]))
        split_count+=1
    triangles=repaired
    if any(area2(t)<1e-20 for t in triangles):raise ValueError('Degenerate triangle remains after conforming repair')
    used={v for tri in triangles for v in tri};bb=bounds([points[v]for v in used])
    if bb['min'][2]<-1e-4 or bb['max'][2]>34.01:raise ValueError(f'Unexpected flat cover bounds {bb}')
    with OUTPUT.open('wb')as out:
        out.write(b'REV05 CONCEPT: closed side ports, unraised top, two payload clearance bores'.ljust(80,b' '));out.write(struct.pack('<I',len(triangles)))
        for tri in triangles:
            a,b,c=(points[i]for i in tri);u=[b[i]-a[i]for i in range(3)];v=[c[i]-a[i]for i in range(3)]
            no=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];le=math.sqrt(sum(x*x for x in no));no=[x/le for x in no]if le else[0,0,0]
            out.write(struct.pack('<12fH',*no,*a,*b,*c,0))
    tessellation.update({'method':'OpenCASCADE BRepMesh via cadquery-ocp','vertex_weld_grid_mm':.0001,'raw_triangle_count':len(raw_triangles),'collapsed_triangles_removed':collapsed,'zero_area_facets_removed':len(zero_triangles),'neighbour_triangles_subdivided_to_preserve_closed_edges':split_count})
    log(f'STL READY ({len(triangles)} triangles); validating delivered holes and mesh edges')
    delivered=stl_triangles(OUTPUT)
    for mount in MOUNTS:
        cx,cy=mount['center_xy_mm']
        mount['bore_sections']=vertical_sections(delivered,[(cx,cy)]+circle_points(cx,cy,3.0))
        mount['counterbore_sections']=vertical_sections(delivered,circle_points(cx,cy,5.7))
        for r in mount['bore_sections']:
            if r['surface_intersections_z_mm']:raise ValueError(f'Blocked {mount["name"]} bore')
        for r in mount['counterbore_sections']:
            z=r['surface_intersections_z_mm']
            if len(z)!=2 or abs(z[0]-SEAT)>.01 or abs(z[1]-TOP)>.01:raise ValueError(f'Inaccessible counterbore {mount["name"]}: {r}')
    previous_camera_xy=(-112.0,0.0) if CAMERA_X == -48.0 else (-48.0,0.0)
    former_camera_section=vertical_sections(delivered,[previous_camera_xy])[0]
    former_source_section=vertical_sections(source_triangles,[previous_camera_xy])[0]
    actual=former_camera_section['surface_intersections_z_mm'];original=former_source_section['surface_intersections_z_mm']
    if len(actual)!=len(original) or any(abs(a-b)>.01 for a,b in zip(actual,original)):raise ValueError(f'Old camera hole persists at {previous_camera_xy}')
    edge_counts={}
    for tri in triangles:
        for a,b in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:
            edge=tuple(sorted((a,b)));edge_counts[edge]=edge_counts.get(edge,0)+1
    boundary=sum(n==1 for n in edge_counts.values());nonmanifold=sum(n>2 for n in edge_counts.values())
    if boundary or nonmanifold:raise ValueError(f'Mesh edges not closed: {boundary}/{nonmanifold}')
    metadata={
        'revision':'06 seam-free upright cover','status':'derived concept geometry; not print-ready or structurally validated','units':'mm',
        'source':str(SOURCE),'source_sha256':source_hash,'source_files_modified':False,
        'source_transform':SOURCE_META['transform'],'source_top_surface_z_mm':TOP,
        'mesh':OUTPUT.name,'mesh_sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        'derived_brep':BREP.name,'derived_brep_sha256':hashlib.sha256(BREP.read_bytes()).hexdigest(),
        'triangle_count':len(triangles),'vertex_count':len(used),'bytes':OUTPUT.stat().st_size,'tessellation':tessellation,
        'bounds_mm':bb,'dimensions_mm':[bb['max'][i]-bb['min'][i]for i in range(3)],'solid_count':len(volumes),
        'volume_mm3':{'source_occ':original_mass,'after_top_seam_closure_occ':seam_closed_mass,'after_side_fills_occ':filled_mass,'final_occ':final_mass,'occ_mass_delta_after_top_seam_fuse_diagnostic':seam_closed_mass-original_mass,'added_to_close_side_ports':filled_mass-seam_closed_mass,'removed_by_payload_bores':filled_mass-final_mass,'diagnostic_note':'CAD mass integration of near-coincident trimmed surfaces is sensitive; a signed incremental mass delta is not used as an added-material measurement.'},
        'top_seam_closure':{'method':'Extrude actual OEM annular groove floor upward to existing top plane and Boolean-fuse','floor_source_face':groove_tag,'floor_z_mm':groove_bottom,'top_z_mm':TOP,'nominal_groove_depth_mm':TOP-groove_bottom,'no_added_top_height':True},
        'side_port_closure':{'method':'Boolean union of solid fill bands inside original straight sidewall zones; not a visual overlay','bands':FILL_BANDS,'original_opening_probe_count':len(side_tests),'all_original_opening_points_solid':True,'point_checks':side_tests,'outer_face_note':'Straight sidewall fill faces at Y=+/-79.75 mm. Source BSpline approximation varies by a few microns in this zone; global OEM outer plan envelope and underside preserved.'},
        'mounts':MOUNTS,
        'top_features':{'raised_boss':False,'locating_collar':False,'quick_release':False,'metal_plates':False,'new_payload_hole_count':2,'nominal_payload_clearance_diameter_mm':7.0,'source_top_face_note':'The simplified OEM broad top face had a single outer boundary and no inner screw-hole loops. It now has only the two newly cut payload holes.'},
        'rail_mounting':{'preserved_original_ear_geometry':True,'preserved_four_outer_attachment_holes':True,'original_auxiliary_inner_ear_features_preserved':True,'reason':'Do not alter OEM mounting relief/counterbores without measured interface need.'},
        'geometry_checks':{'clearance_bores_open':True,'counterbores_open_from_underside':True,'mesh_boundary_edge_count':boundary,'mesh_nonmanifold_edge_count':nonmanifold,'single_closed_occ_solid':True,'zero_area_triangles':0,'no_material_added_below_existing_lower_floor':True,'all_local_checks_passed':True,'former_camera_axis_section':former_camera_section,'former_camera_bore_removed':True},
        'assembly_sequence':'Fit underside screws with the cover off the robot, then mount the cover. Installed driver access is not established.',
        'robot_collision_check':'Pending separate exact registered-robot check on this revision-specific BREP hash.',
        'limitations':['Concept only: screwhead dimensions, 7 mm clearance bores, 12 mm underside wells, print clearances, materials and loads remain provisional.','Source is a simplified filled solid, not a hollowed printable shell or an infill recommendation.','Global footprint, native underside, mounting ears and their original geometry are retained. Side apertures are filled within the straight sidewall regions.','The main top face remains at the original approximately34 mm height, without added bosses or interface parts. The original thin lid groove has been filled to this plane.','No physical rail fit, camera/stick thread fit, fatigue, creep or dynamic motion clearance has been validated.'],
    }
    collision_path=DEST/'flat-cover-body-intersection.json'
    if collision_path.exists():
        collision=json.loads(collision_path.read_text())
        if collision.get('cover_brep_sha256')==metadata['derived_brep_sha256']:
            metadata['robot_collision_check']={
                'evidence_file':collision_path.name,
                'evidence_sha256':hashlib.sha256(collision_path.read_bytes()).hexdigest(),
                'checked_brep_sha256':collision['cover_brep_sha256'],
                'robot_parts_screened':collision['whole_assembly_broad_phase']['robot_volumes_checked'],
                'positive_overlap_volume_mm3':collision['total_positive_intersection_volume_mm3'],
                'status':collision['status'],
                'mount_axis_checks':collision['mount_axis_checks'],
                'limitations':collision['limitations'],
            }
            metadata['robot_interference_check']=metadata['robot_collision_check']
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest()!=source_hash:raise ValueError('Source was changed')
    META.write_text(json.dumps(metadata,indent=2)+'\n')
    log(f'Completed {OUTPUT.name} and {META.name}; source preserved')
finally:gmsh.finalize()
