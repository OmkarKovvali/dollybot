"""Tessellate the unchanged official V1 STEP for a browser viewer.

Run with /private/tmp/trebor-cad-tools/bin/python. Geometry is converted only;
no holes, cutouts, design features, or physical dimensions are changed.
"""
from pathlib import Path
import hashlib
import json
import math
import struct
import gmsh

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "v1-cover-update/cover-research/unitree-a2-v1-docking-station-20260509.stp"
DEST = ROOT / "dist/assets"
DEST.mkdir(parents=True, exist_ok=True)


def bounds(points):
    return {
        "min": [min(p[i] for p in points) for i in range(3)],
        "max": [max(p[i] for p in points) for i in range(3)],
    }


gmsh.initialize()
try:
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.occ.importShapes(str(SOURCE))
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 32)
    gmsh.option.setNumber("Mesh.MeshSizeMin", 0.6)
    gmsh.option.setNumber("Mesh.MeshSizeMax", 5.0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.ElementOrder", 1)
    gmsh.option.setNumber("Mesh.SaveAll", 1)
    gmsh.model.mesh.generate(2)
    tags, coordinates, _ = gmsh.model.mesh.getNodes()
    original = {
        int(tag): tuple(float(v) for v in coordinates[i * 3 : i * 3 + 3])
        for i, tag in enumerate(tags)
    }
    types, _, connectivity = gmsh.model.mesh.getElements(2)
    triangles = []
    for element_type, node_tags in zip(types, connectivity):
        if int(element_type) != 2:
            raise ValueError(f"Expected first-order triangles, got element type {element_type}")
        triangles.extend(tuple(int(v) for v in node_tags[i : i + 3]) for i in range(0, len(node_tags), 3))
    if not 0 < len(triangles) < 200_000:
        raise ValueError(f"Unexpected triangle count: {len(triangles)}")
    used = {tag for tri in triangles for tag in tri}
    original_bounds = bounds([original[t] for t in used])
    lo, hi = original_bounds["min"], original_bounds["max"]
    offset = [-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]]
    points = {tag: tuple(point[i] + offset[i] for i in range(3)) for tag, point in original.items()}
    normalized_bounds = bounds([points[t] for t in used])
    stl = DEST / "v1-cover.stl"
    with stl.open("wb") as stream:
        stream.write(b"Official Unitree A2 V1 STEP, translated to XY center and bottom Z=0".ljust(80, b" "))
        stream.write(struct.pack("<I", len(triangles)))
        for tri in triangles:
            a, b, c = (points[t] for t in tri)
            u = [b[i] - a[i] for i in range(3)]
            v = [c[i] - a[i] for i in range(3)]
            normal = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
            length = math.sqrt(sum(x * x for x in normal))
            normal = [x / length for x in normal] if length else [0.0, 0.0, 0.0]
            stream.write(struct.pack("<12fH", *normal, *a, *b, *c, 0))
    # Identify broad horizontal planar faces analytically, so the viewer can
    # position concept modules on the real top surface rather than a mesh bbox.
    horizontal_faces = []
    for dim, tag in gmsh.model.getEntities(2):
        if gmsh.model.getType(dim, tag) != "Plane":
            continue
        box = gmsh.model.getBoundingBox(dim, tag)
        if abs(box[5] - box[2]) < 0.001:
            area = gmsh.model.occ.getMass(dim, tag)
            center = gmsh.model.occ.getCenterOfMass(dim, tag)
            horizontal_faces.append({"tag": tag, "area_mm2": area, "original_z_mm": center[2], "normalized_z_mm": center[2] + offset[2]})
    horizontal_faces.sort(key=lambda f: f["area_mm2"], reverse=True)
    broad_top = max((f for f in horizontal_faces if f["area_mm2"] > 10_000), key=lambda f: f["original_z_mm"], default=None)
    metadata = {
        "source": str(SOURCE),
        "source_url": "https://oss-global-cdn.unitree.com/static/c7a45b0ba8374780bdbc41b26e770bbe.zip",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "mesh": stl.name,
        "mesh_sha256": hashlib.sha256(stl.read_bytes()).hexdigest(),
        "units": "mm",
        "triangle_count": len(triangles),
        "vertex_count": len(used),
        "bytes": stl.stat().st_size,
        "original_mesh_bounds_mm": original_bounds,
        "normalized_mesh_bounds_mm": normalized_bounds,
        "dimensions_mm": [hi[i] - lo[i] for i in range(3)],
        "transform": {"operation": "translation only", "normalized_equals_original_plus_mm": offset, "rotation_degrees": [0, 0, 0], "scale": 1},
        "top_surface": broad_top,
        "largest_horizontal_faces": horizontal_faces[:10],
        "tessellation": {"tool": "Gmsh OpenCASCADE", "curvature_elements_per_2pi": 32, "mesh_size_min_mm": 0.6, "mesh_size_max_mm": 5, "algorithm": "Frontal-Delaunay"},
        "limitations": ["Visualization conversion of the OEM simplified single solid; not a print-ready design.", "No source features added, removed, or drilled.", "Bounds are tessellated mesh extents, not manufacturing dimensions.", "OEM drawing nominal envelope 301 x 231 mm and rail anchor pitch 204 x 213 mm remain the nominal references; STEP outer pitch is approximately 204.186 x 213.004 mm."],
    }
    (DEST / "cover-mesh.json").write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata, indent=2))
finally:
    gmsh.finalize()
