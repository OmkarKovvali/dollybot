INSTA360 X6 VISUAL REFERENCE MODEL

Files for the interactive viewer:
../../dist/assets/insta360-x6.glb — materials and named component meshes, mm/Z-up.
../../dist/assets/insta360-x6.stl — same-coordinate fallback, no materials.
../../dist/assets/insta360-x6.json — provenance, dimensions, coordinate convention and checksums.

Coordinates: published overall envelope X=-20..20, Y=-25..25, Z=0..100 mm. Opposing lenses point along X. Front touchscreen faces -X. Load without scale or axis rotation. Nominal bottom center is the origin; the exact tripod socket XY and entering screw depth are NOT verified.

Only overall published dimensions are constrained. The 26.4-mm lens-free depth was used for the main housing, with lens domes extending to the 40-mm total depth. Radii, individual feature coordinates, mic patterns, door seams, lens element shapes and bottom interfaces are reconstructed estimates from the official photographs and five exterior diagrams. This is not manufacturer CAD, a 3D scan, a drilling template or a guaranteed collision model for close fits.

Features retained: rounded graphite housing, opposing convex lens domes, layered replaceable lens rings, front OLED with illustrative virtual controls, microphone grilles, ambient sensors, rear vertical branding and quick button, side power and shutter buttons, USB door, opposite battery door and speaker holes, status LEDs, bottom mounting socket/contact/release cues.

Build: run build_x6.py using the installed Blender. See the Blender skill for this Mac's sandbox startup restriction. GLB export intentionally uses export_yup=False and raw millimeter coordinates for this viewer. No floor, lighting or QA camera is exported. Source .blend and three QA views are also saved.

Reference sources:
https://www.insta360.com/specs/x6
https://onlinemanual.insta360.com/x6/en-us/specs/hardware
https://onlinemanual.insta360.com/x6/en-us/camera/product-introduction/insta360-x6
https://www.insta360.com/product/insta360-x6

Unchanged official reference images and SHA-256/URL manifest are in references/.
