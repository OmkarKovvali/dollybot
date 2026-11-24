"""Read-only CAD interference checks for revision 05's actual flat-cover BREP.

The original assembly cache stays in its source coordinates. The robot solids
are translated in memory into the existing viewer frame, and the dock is
excluded. No robot or cover source file is modified.
"""
from pathlib import Path
import hashlib
import json
import gmsh

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "dist/assets"
COVER = ASSETS / "flat-cover-concept.brep"
ASSEMBLY = ROOT.parent / "v1-cover-update/cover-research/unitree-a2-with-v1-docking-station.stp"
CACHE = Path("/private/tmp/unitree-a2-v1-assembly-import-cache.brep")
REGISTRATION = json.loads((ASSETS / "robot-registration.json").read_text())
PREVIOUS_SOLIDS = json.loads((ASSETS / "robot-solid-inspection.json").read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def union_bounds(boxes):
    return [min(b[i] for b in boxes) for i in range(3)] + [max(b[i] for b in boxes) for i in range(3, 6)]


if not COVER.exists():
    raise SystemExit(f"Awaiting revision 05 BREP: {COVER}")
cover_hash_before = sha256(COVER)
source_hash = sha256(ASSEMBLY)
offset = REGISTRATION["assembly_to_viewer_translation_mm"]
dock = REGISTRATION["assembly_dock_volume_tag"]
gmsh.initialize()
try:
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.occ.importShapes(str(CACHE if CACHE.exists() else ASSEMBLY))
    gmsh.model.occ.synchronize()
    original_tags = [t for _, t in gmsh.model.getEntities(3)]
    if len(original_tags) != REGISTRATION["assembly_volume_count"]:
        raise ValueError("Unexpected assembly instance count")
    # Validate cached geometry against recorded source-import geometry before
    # relying on its volume tags or registration.
    cache_validation = []
    for old in PREVIOUS_SOLIDS:
        tag = old["tag"]
        mass = gmsh.model.occ.getMass(3, tag)
        bbox = gmsh.model.getBoundingBox(3, tag)
        mass_error = abs(mass - old["volume_mm3"])
        bbox_error = max(abs(a - b) for a, b in zip(bbox, old["conservative_bbox_mm"]))
        if mass_error > 0.01 or bbox_error > 0.001:
            raise ValueError(f"Unexpected cached geometry for volume {tag}: {mass_error}, {bbox_error}")
        cache_validation.append({"tag": tag, "volume_difference_mm3": mass_error, "bbox_max_difference_mm": bbox_error})
    robot = [(3, t) for t in original_tags if t != dock]
    gmsh.model.occ.translate(robot, *offset)
    gmsh.model.occ.synchronize()
    cover_parts = [x for x in gmsh.model.occ.importShapes(str(COVER)) if x[0] == 3]
    gmsh.model.occ.synchronize()
    if not cover_parts:
        raise ValueError("Revision 05 BREP has no solid")
    cover_bbox = union_bounds([gmsh.model.getBoundingBox(d, t) for d, t in cover_parts])
    broad_bbox = [x - 0.01 if i < 3 else x + 0.01 for i, x in enumerate(cover_bbox)]
    candidates, excluded = [], []
    for d, tag in robot:
        box = gmsh.model.getBoundingBox(d, tag)
        overlaps = all(box[i + 3] >= broad_bbox[i] and box[i] <= broad_bbox[i + 3] for i in range(3))
        row = {"volume_tag": tag, "conservative_bbox_mm": box}
        (candidates if overlaps else excluded).append(row)
    print(json.dumps({"stage": "broad phase", "cover_sha256": cover_hash_before, "candidates": [x["volume_tag"] for x in candidates]}), flush=True)
    intersections = []
    for candidate in candidates:
        tag = candidate["volume_tag"]
        common, _ = gmsh.model.occ.intersect(cover_parts, [(3, tag)], removeObject=False, removeTool=False)
        gmsh.model.occ.synchronize()
        solids = [(d, t) for d, t in common if d == 3]
        volume = sum(gmsh.model.occ.getMass(d, t) for d, t in solids)
        row = {
            "robot_volume_tag": tag,
            "positive_intersection_volume_mm3": volume,
            "intersection_solid_count": len(solids),
            "returned_contact_entity_dimensions": [d for d, _ in common],
            "intersection_conservative_bboxes_mm": [gmsh.model.getBoundingBox(d, t) for d, t in solids],
        }
        intersections.append(row)
        print(json.dumps({"stage": "exact common volume", **row}), flush=True)
    axis_results = []
    for name, x, y in (("camera", -48, 0), ("stick", 78, 0)):
        axis_candidates = []
        for d, tag in robot:
            b = gmsh.model.getBoundingBox(d, tag)
            if b[0] <= x <= b[3] and b[1] <= y <= b[4]:
                axis_candidates.append((d, tag))
        p1 = gmsh.model.occ.addPoint(x, y, -700)
        p2 = gmsh.model.occ.addPoint(x, y, 100)
        line = gmsh.model.occ.addLine(p1, p2)
        clipped, _ = gmsh.model.occ.intersect([(1, line)], axis_candidates, removeObject=True, removeTool=False)
        gmsh.model.occ.synchronize()
        segments = []
        for dim, tag in clipped:
            if dim == 1:
                lo, hi = gmsh.model.getParametrizationBounds(dim, tag)
                points = [list(gmsh.model.getValue(dim, tag, [float(v[0])])) for v in (lo, hi)]
                segments.append(points)
        roof = max((p[2] for segment in segments for p in segment), default=None)
        row = {
            "mount": name,
            "xy_mm": [x, y],
            "method": "OpenCASCADE vertical line / robot solid intersection",
            "robot_volume_candidates": [tag for _, tag in axis_candidates],
            "occupied_line_segments_mm": segments,
            "robot_roof_z_mm": roof,
            "provisional_screw_head_bottom_z_mm": 20.5,
            "provisional_head_axis_gap_mm": 20.5 - roof if roof is not None else None,
            "head_note": "The 20.5-mm bottom assumes the previously illustrated 6.5-mm-high head below a z27 seat; actual screw dimensions still require confirmation.",
        }
        axis_results.append(row)
        print(json.dumps({"stage": "axis clearance", **row}), flush=True)
    cover_hash_after = sha256(COVER)
    if cover_hash_before != cover_hash_after:
        raise ValueError("Cover BREP changed during collision check; rerun against final geometry")
    total_overlap = sum(r["positive_intersection_volume_mm3"] for r in intersections)
    result = {
        "revision": "05 flat cover with closed side apertures, two through holes and underside recesses",
        "cover_file": str(COVER),
        "cover_brep_sha256": cover_hash_before,
        "cover_hash_unchanged_during_check": True,
        "source_assembly": str(ASSEMBLY),
        "source_assembly_sha256": source_hash,
        "registration": REGISTRATION,
        "cache_validation": {"volumes_checked": len(cache_validation), "maximum_volume_difference_mm3": max(r["volume_difference_mm3"] for r in cache_validation), "maximum_bbox_difference_mm": max(r["bbox_max_difference_mm"] for r in cache_validation)},
        "cover_solid_count": len(cover_parts),
        "cover_conservative_bbox_mm": cover_bbox,
        "whole_assembly_broad_phase": {"robot_volumes_checked": len(robot), "excluded_dock_volume_tag": dock, "padded_cover_bbox_mm": broad_bbox, "overlapping_candidates": candidates, "excluded_robot_volume_tags": [r["volume_tag"] for r in excluded]},
        "exact_solid_intersections": intersections,
        "total_positive_intersection_volume_mm3": total_overlap,
        "status": "no_positive_static_model_overlap" if total_overlap == 0 else "positive_static_model_overlap_detected",
        "mount_axis_checks": axis_results,
        "limitations": ["Checks exact Boolean common volume of the supplied simplified CAD in its saved static pose, not the physical robot or movement envelope.", "Zero positive volume does not certify a tolerance margin, structural capacity, fastener head envelope, or assembly/tool access.", "Robot geometry below each mount axis can obstruct a straight driver from beneath while installed; mount the screw before fitting the carrier unless access is physically verified.", "Robot front direction remains unverified; source orientation is preserved."],
    }
    (ASSETS / "flat-cover-body-intersection.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"status": result["status"], "total_positive_intersection_volume_mm3": total_overlap, "cover_sha256": cover_hash_before}), flush=True)
finally:
    gmsh.finalize()
