"""Bound-based clearance checks for the current upright C19 camera stack."""
from pathlib import Path
import json, hashlib, struct
P=Path(__file__).resolve().parent/'dist/assets'
def read(n):return json.loads((P/n).read_text())
mount=read('innorel-c19.json');sony=read('sony-zv-e1.json');lens=read('sony-selp1635g.json');cover=read('flat-cover-concept.json');reg=read('robot-registration.json');parts=read('robot-solid-inspection.json');hit=read('flat-cover-body-intersection.json')
assert hit['cover_brep_sha256']==cover['derived_brep_sha256']
assert hit['total_positive_intersection_volume_mm3']==0
seat=mount['camera_seating_plane_z_mm'];top=34.;hole=[-48.,0.]
roof=max(p['conservative_bbox_mm'][5]+reg['assembly_to_viewer_translation_mm'][2] for p in parts if p['tag']!=reg['assembly_dock_volume_tag'])
sony_min_z=top+seat+sony['bounds_mm']['min'][2]
lens_min_z=top+seat+sony['lens_axis']['face_origin_mm'][2]+lens['bounds_mm']['min'][2]
raw=(P/'a2-robot.stl').read_bytes();n=struct.unpack_from('<I',raw,80)[0]
lo=[hole[k]+mount['bounds_mm']['min'][k] for k in range(2)];hi=[hole[k]+mount['bounds_mm']['max'][k] for k in range(2)];mount_roof=-1e9
for i in range(n):
 f=struct.unpack_from('<12fH',raw,84+50*i);v=[f[3:6],f[6:9],f[9:12]]
 if all(min(a[k] for a in v)<=hi[k] and max(a[k] for a in v)>=lo[k] for k in range(2)):
  mount_roof=max(mount_roof,max(a[2] for a in v))
assert lens_min_z>roof and sony_min_z>roof and top>mount_roof
assets={name:hashlib.sha256((P/name).read_bytes()).hexdigest() for name in ('flat-cover-concept.brep','a2-robot.stl','sony-zv-e1.glb','sony-selp1635g.glb','insta360-x6.glb','innorel-c19.glb')}
result={
 'revision':'07 — seam-free upright cover, selected C19, telescoping stick',
 'pose':'upright ball head; camera and lens horizontal; saved static robot pose',
 'camera_mount_xy_mm':hole,'pole_mount_xy_mm':[78,0],
 'cover_top_z_mm':top,'c19_seat_height_mm':seat,'c19_seat_height_status':mount['camera_seating_plane_height_status'],
 'camera_bottom_z_mm':sony_min_z,'lens_lowest_z_mm':lens_min_z,
 'whole_robot_conservative_CAD_top_z_mm':roof,
 'camera_to_robot_vertical_separation_lower_bound_mm':sony_min_z-roof,
 'lens_to_robot_vertical_separation_lower_bound_mm':lens_min_z-roof,
 'lens_to_cover_vertical_separation_lower_bound_mm':lens_min_z-cover['bounds_mm']['max'][2],
 'c19_footprint_xy_bounds_mm':[lo,hi],
 'robot_triangle_bbox_max_z_under_c19_xy_mm':mount_roof,
 'c19_to_robot_vertical_separation_lower_bound_for_delivered_mesh_mm':top-mount_roof,
 'cover_exact_CAD_overlap_mm3':hit['total_positive_intersection_volume_mm3'],
 'files_sha256':assets,
 'limits':['Computed for the authored reference models and upright pose; physical tripod placement, mounting interfaces, stud length and C19 seating height remain unmeasured.', 'No ball-head tilt sweep, robot motion, printed strength or fastener retention qualification.', 'Mount-to-cover and mount-stud-to-camera contacts are intended mating interfaces, not separate collision-free bodies.']}
(P/'current-assembly-clearance.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if 'separation' in k or 'overlap' in k},indent=2))
