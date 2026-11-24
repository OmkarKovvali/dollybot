SONY ZV-E1 BODY VISUAL REFERENCE — 2026-11-23

Asset: ../../dist/assets/sony-zv-e1.glb
Fallback: ../../dist/assets/sony-zv-e1.stl
Geometry provenance and exact export hashes: model-metadata.json
Validation: export-validation.json
Editable source: build_sony.py and sony-zv-e1.blend
QA: previews/front-three-quarter.png, rear-three-quarter.png, front.png, top.png

This is an original procedural visual reconstruction from official Sony references, NOT downloaded Sony CAD, a scan, or fabrication geometry. It replaces the old rectangular body proxy for visualization. Overall width/height/depth are constrained to Sony's published 121 x 71.9 x 54.3 mm envelope. Internal features, edge shapes, mounting coordinates and detailed feature dimensions are estimated from references.

COORDINATES
GLB and STL intentionally use millimeters, Z up, lens facing -X, width along Y. The actual camera grip is on +Y. This explicit viewer-native convention differs from usual glTF meters/Y-up. Do not rescale or rotate the model when loading in the current viewer. Origin is the provisional tripod XY and lowest nominal seating plane Z0. Tripod XY must be measured physically before any drill/print interface decisions.

The open E-mount face is provided without body cap or lens. Approximate lens flange origin is [-24.7245, 0, 35.8604] mm; axis is [-1,0,0]. The user subsequently identified the Sony FE PZ16–35 mm F4 G (SELP1635G); use the separate sony-selp1635g.glb lens asset at this flange. The original body GLB remains unchanged. The screen is modeled closed as a separate named component with hinge details, but is not rigged and does not establish swept clearance.

EXPORT VALIDATION
The uncompressed GLB contains embedded buffers and standard PBR materials, no required decoder extensions. Binary GLB header, accessor bounds, file hashes and STL count were verified. Geometry: 64,848 triangles, 302 named meshes, 11 materials. Front and rear renders checked against official diagrams. QA caught and corrected the original proxy's mirrored handedness; lettering and controls now match Sony reference orientation.

REFERENCES
https://sony.scene7.com/is/image/sonyglobalsolutions/01_Dimensions?fmt=png-alpha&wid=1400
Downloaded as references/official-dimensions.png: official front/side product photograph.
https://www.sony-asia.com/interchangeable-lens-cameras/products/zv-e1
Official 121 x 71.9 x 54.3 mm dimensions verified by browser; direct HTML download returned403.
https://helpguide.sony.net/ilc/2310/v1/en/print.pdf
Pages36,37,39,41,43 rendered into references/help-guide-*.png from the already downloaded official manual. Covers front, rear, top, sides, bottom and 1/4-20 tripod socket. Sony requires the screw entering the body to be strictly less than5.5 mm. This is not a verified socket-coordinate drawing.
