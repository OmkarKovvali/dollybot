INNOREL C19 commercial mount reference model
Prepared 2026-11-23 from the manufacturer's product images.

User-selected listing: https://www.amazon.com/dp/B0CHB63882
Manufacturer: https://innoreltech.com/products/cnc-metal-low-profile-mini-ballhead-innorel-c19

Published anchors
-----------------
The manufacturer's dimension graphic gives 47.5 mm from the bottom to the
tip of the top screw, a 30 mm base diameter, a 19 mm ball, and 59 g mass.
The detail graphic identifies the rubber camera pad, double U-notch, main
locking knob, top 1/4-inch screw, bottom 3/8-inch hole, and supplied 3/8 to
1/4-inch thread reducer. Source files and checksums are in references/.

Camera seating plane
--------------------
47.5 mm is NOT the camera seating height. The separate seating height is
not dimensioned. This model estimates 42.5 mm to the top rubber contact
pad and 5 mm exposed screw above it, matching the approximate photo
proportions. Both are provisional pending physical measurement. Adapter
engagement depth and whether its flange is exactly flush are also unknown.

Viewer integration
------------------
Load ../../dist/assets/innorel-c19.glb at scale 1, no rotation. Raw mesh
coordinates intentionally use millimeters, Z-up, bottom center at (0,0,0),
top screw on the Z axis, and side locking knob toward -Y. This is a static
upright pose. The JSON field camera_seating_plane_z_mm = 42.5 tells the
viewer where to place the camera's bottom. On a cover top at Z34, place
the head origin at Z34 and the camera bottom at Z76.5. The stud penetrates
the camera socket; its tip should not set the camera's bottom position.

The modeled footprint extends X -15..15 and Y -30.97..15.03 mm, including
the control knob and retention detail. The knob projection, cup profile,
platform diameter, slots, surface texture, and individual thread geometry
are reconstructed from photos. Only the published dimensions listed above
are constrained. This is a visual model of a purchased commercial part,
not manufacturer CAD and not a printable substitute.

Files
-----
build_c19.py: reproducible Blender procedural model/export/render script.
innorel-c19.blend: complete editable model and separate QA studio scene.
previews/: inspected three-quarter, opposite, and bottom renders.
../../dist/assets/innorel-c19.glb: viewer model, portable PBR materials.
../../dist/assets/innorel-c19.json: dimensions, coordinates, limits, hash.

Validation
----------
35,765 source vertices; 70,048 triangles; 58,778 exported GLB position
vertices after hard-edge/material splitting (below the 60,000 target).
Native exported bounds: X -15..15, Y -30.97..15.03, Z 0..47.5 mm.
Three QA images inspected. No camera, lights, floor, or unrelated model
is exported into the GLB. No purchase or contact with the seller occurred.
