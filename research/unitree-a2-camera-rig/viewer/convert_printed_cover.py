"""Derive a printable-structure visualization concept from the OEM V1 STEP.

This is not print-ready or structurally validated. Source files remain intact.
Run: /private/tmp/trebor-cad-tools/bin/python convert_printed_cover.py
Only the derived output STL/JSON in dist/assets are written.
"""
from pathlib import Path
import hashlib
import json
import math
import struct
import time
import gmsh

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'dist/assets'
SOURCE_META = json.loads((DEST / 'cover-mesh.json').read_text())
SOURCE = Path(SOURCE_META['source'])
SOURCE_STL = DEST / SOURCE_META['mesh']
OFFSET = SOURCE_META['transform']['normalized_equals_original_plus_mm']
OUTPUT = DEST / 'printed-cover-concept.stl'
META = DEST / 'printed-cover-concept.json'
BREP = DEST / 'printed-cover-concept.brep'
CX, CY = 78.0, 0.0
BOSS_R, BOSS_BOTTOM, BOSS_TOP = 23.0, 20.0, 42.0
BORE_R, WELL_R, SEAT = 3.5, 6.0, 27.0
HEAD_R, HEAD_BOTTOM, HEAD_TOP = 5.25, 20.5, 27.0
START = time.time()


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


def circle_points(radius, count=8):
    return [(CX+radius*math.cos(i*2*math.pi/count), CY+radius*math.sin(i*2*math.pi/count)) for i in range(count)]


def mass(volumes):
    return sum(gmsh.model.occ.getMass(dim, tag) for dim, tag in volumes)


def bounds(points):
    return {'min': [min(p[i] for p in points) for i in range(3)], 'max': [max(p[i] for p in points) for i in range(3)]}


# Probe the existing unchanged source mesh before mutation. The source is a
# simplified filled volume here, not a 3 mm lid over an empty cavity.
log('Reading unchanged source cross-sections')
source_tris = stl_triangles(SOURCE_STL)
source_axis = vertical_sections(source_tris, [(CX, CY)])[0]
source_opening_ring = vertical_sections(source_tris, circle_points(WELL_R))
axis_intersections = source_axis['surface_intersections_z_mm']
if len(axis_intersections) != 2:
    raise ValueError(f'Unexpected source material section: {axis_intersections}')
LOCAL_UNDERSIDE = axis_intersections[0]
opening_z_values = [p['surface_intersections_z_mm'][0] for p in source_opening_ring]
log(f'Source axis material z={axis_intersections}; pocket must open through the lower surface')

source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
gmsh.initialize()
try:
    gmsh.option.setNumber('General.Terminal', 1)
    imported = gmsh.model.occ.importShapes(str(SOURCE))
    gmsh.model.occ.translate(imported, *OFFSET)
    gmsh.model.occ.synchronize()
    original_volumes = gmsh.model.getEntities(3)
    if len(original_volumes) != 1:
        raise ValueError(f'Expected one OEM source volume, got {original_volumes}')
    original_mass = mass(original_volumes)
    log(f'Imported source solid, volume={original_mass:.3f} mm3')

    boss = gmsh.model.occ.addCylinder(CX, CY, BOSS_BOTTOM, 0, 0, BOSS_TOP-BOSS_BOTTOM, BOSS_R)
    fused, _ = gmsh.model.occ.fuse(original_volumes, [(3, boss)], removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    fused_volumes = gmsh.model.getEntities(3)
    if len(fused_volumes) != 1:
        raise ValueError(f'Boss must be fused to the housing: {fused_volumes}')
    fused_mass = mass(fused_volumes)
    log(f'Boss fused; added volume={fused_mass-original_mass:.3f} mm3')

    # The counterbore seat is z=27. A tool extending below z=0 opens the well
    # through the sloping source underside (z approx 2..5.04 over this footprint).
    # It adds no geometry below the source and avoids a trapped z20..27 pocket.
    bore = gmsh.model.occ.addCylinder(CX, CY, -1, 0, 0, 44, BORE_R)
    well = gmsh.model.occ.addCylinder(CX, CY, -1, 0, 0, SEAT+1, WELL_R)
    result, _ = gmsh.model.occ.cut(fused_volumes, [(3, bore), (3, well)], removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    final_volumes = gmsh.model.getEntities(3)
    if len(final_volumes) != 1:
        raise ValueError(f'Expected a connected housing after cuts: {final_volumes}')
    final_mass = mass(final_volumes)
    assert original_mass > 0 and fused_mass > original_mass and 0 < final_mass < fused_mass
    log(f'Bore and accessible underside well cut; volume removed={fused_mass-final_mass:.3f} mm3')
    gmsh.write(str(BREP))
    log('Normalized derived BREP saved for robot intersection inspection')

    # Exact OCC point membership supplements tessellated ray sections. All
    # points stay away from boundary/tolerance ambiguities.
    checks = []
    test_specs = [
        ('axis_lower_access_empty', CX, CY, 10, False),
        ('axis_head_space_empty', CX, CY, 23, False),
        ('axis_through_bore_empty', CX, CY, 38, False),
        ('head_outer_radius_empty', CX+HEAD_R-0.05, CY, 24, False),
        ('counterbore_outer_region_empty', CX+5.8, CY, 26.8, False),
        ('annular_seat_material_above', CX+4.8, CY, 27.2, True),
        ('boss_wall_connected_material', CX+12, CY, 38, True),
        ('no_new_material_below_zero', CX+12, CY, -0.01, False),
    ]
    gmsh.option.setNumber('General.Terminal', 0)
    for name, x, y, z, expected in test_specs:
        actual = bool(gmsh.model.isInside(3, final_volumes[0][1], [x, y, z]))
        checks.append({'name': name, 'point_mm': [x,y,z], 'expected_material': expected, 'actual_material': actual, 'pass': actual == expected})
        if actual != expected:
            raise ValueError(f'OCC point membership failed: {checks[-1]}')
    log('Analytic point checks passed; tessellating only the derived surface')
    gmsh.option.setNumber('General.Terminal', 1)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature', 32)
    gmsh.option.setNumber('Mesh.MeshSizeMin', 0.6)
    gmsh.option.setNumber('Mesh.MeshSizeMax', 5.0)
    gmsh.option.setNumber('Mesh.Algorithm', 6)
    gmsh.option.setNumber('Mesh.ElementOrder', 1)
    gmsh.option.setNumber('Mesh.SaveAll', 1)
    gmsh.model.mesh.generate(2)
    node_tags, coords, _ = gmsh.model.mesh.getNodes()
    points = {int(tag): tuple(float(v) for v in coords[3*i:3*i+3]) for i,tag in enumerate(node_tags)}
    types, _, connectivity = gmsh.model.mesh.getElements(2)
    triangles = []
    for typ, nodes in zip(types, connectivity):
        if int(typ) != 2:
            raise ValueError(f'Unexpected non-linear/non-triangular element {typ}')
        triangles.extend(tuple(int(v) for v in nodes[i:i+3]) for i in range(0,len(nodes),3))
    if not 0 < len(triangles) < 250000:
        raise ValueError(f'Unexpected surface mesh count {len(triangles)}')
    used = {v for tri in triangles for v in tri}
    mesh_bounds = bounds([points[v] for v in used])
    if mesh_bounds['min'][2] < -1e-4 or abs(mesh_bounds['max'][2]-BOSS_TOP) > 0.01:
        raise ValueError(f'Unexpected derived Z extent: {mesh_bounds}')
    with OUTPUT.open('wb') as out:
        out.write(b'DERIVED PRINTED CONCEPT: OEM V1 + pole boss and accessible recessed bolt well'.ljust(80,b' '))
        out.write(struct.pack('<I',len(triangles)))
        for tri in triangles:
            a,b,c = (points[i] for i in tri)
            u = [b[i]-a[i] for i in range(3)];v = [c[i]-a[i] for i in range(3)]
            normal = [u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            length = math.sqrt(sum(n*n for n in normal))
            normal = [n/length for n in normal] if length else [0,0,0]
            out.write(struct.pack('<12fH',*normal,*a,*b,*c,0))
    log(f'Derived STL written ({len(triangles)} triangles); validating sections')

    # Work with the exact written binary STL so the checks validate the delivered
    # mesh. Rays through the entire hole footprint are clear from underneath to
    # the head seat; inside radius 3.5 they are clear all the way through.
    final_tris = stl_triangles(OUTPUT)
    bore_sections = vertical_sections(final_tris, [(CX,CY)] + circle_points(3.0))
    pocket_sections = vertical_sections(final_tris, circle_points(5.7))
    outer_sections = vertical_sections(final_tris, circle_points(6.5))
    for row in bore_sections:
        if row['surface_intersections_z_mm']:
            raise ValueError(f'Clearance bore ray blocked: {row}')
    for row in pocket_sections:
        z = row['surface_intersections_z_mm']
        if len(z) != 2 or abs(z[0]-SEAT) > .01 or abs(z[1]-BOSS_TOP) > .01:
            raise ValueError(f'Underside counterbore access blocked: {row}')

    # Surface edge counts and mesh volume are diagnostics, with explicit scope:
    # shared-tag edge consistency tests the delivered tessellation, not FDM fit.
    edge_counts = {}
    signed_volume = 0.0
    for tri in triangles:
        for a,b in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:
            edge = tuple(sorted((a,b)));edge_counts[edge] = edge_counts.get(edge,0)+1
        a,b,c = (points[i] for i in tri)
        signed_volume += (a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    boundary_edges = sum(n == 1 for n in edge_counts.values())
    nonmanifold_edges = sum(n > 2 for n in edge_counts.values())
    top_surface = max((f for f in SOURCE_META['largest_horizontal_faces'] if f['area_mm2'] > 10000), key=lambda f:f['normalized_z_mm'])
    metadata = {
        'status': 'derived geometry for interactive visualization; not print-ready or structurally validated',
        'units': 'mm',
        'source': str(SOURCE), 'source_sha256': source_hash,
        'source_files_modified': False,
        'source_transform': SOURCE_META['transform'],
        'source_top_surface_z_mm': top_surface['normalized_z_mm'],
        'mesh': OUTPUT.name, 'mesh_sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        'derived_brep': BREP.name, 'derived_brep_sha256':hashlib.sha256(BREP.read_bytes()).hexdigest(),
        'triangle_count': len(triangles), 'vertex_count': len(used), 'bytes': OUTPUT.stat().st_size,
        'bounds_mm': mesh_bounds,
        'dimensions_mm': [mesh_bounds['max'][i]-mesh_bounds['min'][i] for i in range(3)],
        'solid_count': len(final_volumes),
        'volume_mm3': {'source_occ': original_mass, 'after_boss_union_occ': fused_mass, 'final_occ': final_mass, 'added_by_union': fused_mass-original_mass, 'removed_by_bores': fused_mass-final_mass, 'net_change': final_mass-original_mass, 'mesh_signed': signed_volume},
        'boss': {'center_xy_mm': [CX,CY], 'outer_radius_mm': BOSS_R, 'bottom_z_mm': BOSS_BOTTOM, 'top_z_mm': BOSS_TOP, 'operation': 'OCC fused cylinder; intersects source material and rises to z42'},
        'through_bore': {'diameter_mm': 2*BORE_R, 'center_xy_mm':[CX,CY], 'cut_tool_start_z_mm':-1, 'cut_tool_end_z_mm':43, 'provisional':True},
        'counterbore': {
            'diameter_mm': 2*WELL_R,
            'center_xy_mm':[CX,CY],
            'bottom_z_mm':LOCAL_UNDERSIDE,
            'bottom_reference':'local source underside at hole axis; opening is sloped, not one constant Z plane',
            'depth_mm':SEAT-LOCAL_UNDERSIDE,
            'seat_z_mm':SEAT,
            'access_opening_z_mm':LOCAL_UNDERSIDE,
            'access_opening_boundary_z_range_mm':[min(opening_z_values),max(opening_z_values)],
            'access_well_total_depth_mm':SEAT-LOCAL_UNDERSIDE,
            'access_well_boundary_depth_range_mm':[SEAT-max(opening_z_values),SEAT-min(opening_z_values)],
            'cut_tool_start_z_mm':-1,
            'cut_tool_end_z_mm':SEAT,
            'head_bottom_z_mm':HEAD_BOTTOM,
            'head_top_z_mm':HEAD_TOP,
            'provisional_head_max_diameter_mm':2*HEAD_R,
            'provisional_head_max_height_mm':HEAD_TOP-HEAD_BOTTOM,
            'radial_head_clearance_mm':WELL_R-HEAD_R,
            'provisional':True,
            'access_statement':'Full diameter-12 access well opens through the original sloping underside. It is about 23.55 mm deep at the axis, not a 7 mm deep underside pocket. Head is entirely inside the housing, at z20.5..27.',
        },
        'metal_parts_in_structure':False,
        'separate_hardware_note':'Only the metal screw is represented separately by the viewer; no washer or metal plate is part of this derived mesh.',
        'geometry_checks': {
            'source_axis_section':source_axis,
            'source_12mm_opening_boundary_sections':source_opening_ring,
            'occ_point_membership':checks,
            'through_bore_axis_and_ring_sections':bore_sections,
            'counterbore_near_wall_sections':pocket_sections,
            'outside_counterbore_sections':outer_sections,
            'through_bore_rays_clear':True,
            'counterbore_rays_open_to_seat':True,
            'mesh_tag_boundary_edge_count':boundary_edges,
            'mesh_tag_nonmanifold_edge_count':nonmanifold_edges,
            'no_added_material_below_z0':True,
            'all_recorded_checks_passed':True,
        },
        'limitations':[
            'The OEM source is a simplified filled single solid at this location, not an engineered hollow printable shell; the retained source volume is not an infill recommendation.',
            'The accessible pocket is approximately 23.55 mm deep at its axis. A proposed isolated z20..27 pocket would have been inaccessible and was not used.',
            'Screw head and diameter-7/diameter-12 bores are provisional until actual screw and stick thread/engagement are measured.',
            'Printed material, orientation, tolerances, local stress, creep, fatigue and dynamic pole loads remain unvalidated. See separate main-body snapshot intersection evidence; installed driver access and full robot motion are not verified.',
            'The separately displayed locating collar is a viewer concept and not included in this fused STL.',
            'The source mounting pitch discrepancy versus OEM nominal drawing remains; physical rail fit must be checked.',
        ],
    }
    if boundary_edges or nonmanifold_edges:
        metadata['geometry_checks']['all_recorded_checks_passed'] = False
        metadata['limitations'].append('Mesh edge consistency found unmatched or multiply shared edges; inspect before any fabrication use.')
    collision_file = DEST / 'cover-body-intersection.json'
    if collision_file.exists():
        collision = json.loads(collision_file.read_text())
        derived_result = next((r for r in collision.get('comparisons', []) if r.get('model') == 'derived_printed_cover_concept'), None)
        if derived_result is not None:
            metadata['robot_snapshot_intersection'] = {
                'evidence_file': collision_file.name,
                'evidence_sha256': hashlib.sha256(collision_file.read_bytes()).hexdigest(),
                'derived_cover_vs_main_body_common_volume_mm3': derived_result['positive_intersection_volume_mm3'],
                'scope': collision['scope'],
                'robot_top_at_exact_pole_axis_z_mm': collision['robot_top_at_exact_pole_axis_z_mm'],
                'opening_to_robot_axis_gap_mm': LOCAL_UNDERSIDE-collision['robot_top_at_exact_pole_axis_z_mm'],
                'head_to_robot_axis_gap_mm': HEAD_BOTTOM-collision['robot_top_at_exact_pole_axis_z_mm'],
            }
            metadata['assembly_sequence'] = 'Install the stick and recessed screw while the cover is off the robot, then mount the cover. Installed downward driver access is not established.'
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != source_hash:
        raise ValueError('Source STEP changed unexpectedly')
    META.write_text(json.dumps(metadata,indent=2)+'\n')
    log(f'Validated output saved: {OUTPUT.name}, {META.name}; edge counts boundary={boundary_edges}, nonmanifold={nonmanifold_edges}')
    print(json.dumps({'output':str(OUTPUT),'triangle_count':len(triangles),'volume_mm3':final_mass,'counterbore':metadata['counterbore'],'geometry_checks_passed':metadata['geometry_checks']['all_recorded_checks_passed']},indent=2),flush=True)
finally:
    gmsh.finalize()
