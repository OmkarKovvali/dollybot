UNITREE A2 V1 DOCK / COVER RESEARCH
Verified 2026-11-23 (America/Los_Angeles)

RESULT
The selected flat-top render is Unitree's V1.0 Docking Station housing, including the sidewalls, four mounting ears and inset top panel. Unitree DOES publish a simplified STEP solid of this exact V1 docking station. It is downloaded here, together with the full A2 + V1 dock STEP. This finding supersedes any earlier tentative note saying no public STEP was found. No native Rhino .3dm / SolidWorks / feature-history file or separately editable lid was found in these archives. No verified public listing for a blank shell or lid sold separately was found in the official shop pages checked; this is not proof that service spares are unavailable.

PRIMARY SOURCE / CAD DOWNLOADS
https://support.unitree.com/home/en/A2_SDK_Development_Guide/get_sdk
Browser displayed Last Updated On: 2026-11-05 12:20:59 (timezone unspecified).
Source content saved as get-sdk-source.txt from its observed public resource:
https://doc-cdn.unitree.com/26/1098/en/26_1098_en

V1.0 Docking Station Model:
https://oss-global-cdn.unitree.com/static/c7a45b0ba8374780bdbc41b26e770bbe.zip
Local original ZIP: unitree-a2-v1-dock.zip (1,269,634 bytes)
Original filename: A2拓展坞简化模型20260509.stp
Friendly byte-identical copy: unitree-a2-v1-docking-station-20260509.stp (4,849,268 bytes)
STEP header: Rhino 8.3 / ST-DEVELOPER v19.2; AUTOMOTIVE_DESIGN (AP214).
STEP export timestamp: 2026-05-09T17:03:57+08:00.
ZIP member timestamp: 2026-07-01 20:15:16 (timezone unspecified).
One MANIFOLD_SOLID_BREP and one ADVANCED_BREP_SHAPE_REPRESENTATION.
This is a simplified geometric solid, not a native feature-history file or a separate lid assembly.

A2 with V1.0 Docking Station Model:
https://oss-global-cdn.unitree.com/static/0d83412eb0784e86baf3285348ffe7e9.zip
Local ZIP: unitree-a2-with-v1-dock.zip (21,519,855 bytes)
Original filename: A2带拓展坞简化模型（足端）.stp
Friendly byte-identical copy: unitree-a2-with-v1-docking-station.stp (77,433,742 bytes)
STEP export timestamp: 2026-07-08T16:03:58+08:00.
45 MANIFOLD_SOLID_BREP entities; 5 ADVANCED_BREP_SHAPE_REPRESENTATION entities.

Revision interpretation: filenames and STEP export dates are provenance, not a formal vendor engineering revision or a claim of newly published design. These are the current official linked V1 files checked on the research date. Public page also offers a newer V2 design, but the user specifically selected V1.

OTHER CURRENT OFFICIAL MODEL LINKS (not substituted for V1)
V2 dock: https://oss-global-cdn.unitree.com/static/d277c7c770c145f7a901b78e2dca9776.zip
A2+V2: https://oss-global-cdn.unitree.com/static/4a5ea812a015454396f3a36a2cf3986d.zip
Bare simplified A2 (ALSO DOWNLOADED): https://oss-global-cdn.unitree.com/static/240a9c898c7c44d69e1d956e2830551b.zip
Local ZIP unitree-a2-bare-simplified.zip: 19,726,867 bytes.
Friendly STEP unitree-a2-bare-simplified.stp: 72,300,255 bytes.
Original filename A2足端版简化模型-20251125.stp; Rhino 8.3 / AP214; export 2025-11-25T20:38:31+08:00. 44 MANIFOLD_SOLID_BREP entities. This is the current linked bare model, even though its export predates the A2+V1 model. See bare-a2-download-manifest.json for hashes/header.
Side cover (a different part, not the flat V1 dock lid): https://oss-global-cdn.unitree.com/static/42c4542daf034839935265b21e85af16.zip

WHAT THE DRAWING ACTUALLY DIMENSIONS
https://support.unitree.com/home/en/A2_SDK_Development_Guide/about_a2
V1 figure: dock-v1-dimensions.png (original OEM raster).
Housing outline including mounting ears: 301 mm fore/aft by 231 mm across the robot. Direction is established by comparison with the installed illustration and the bare-rail transverse spacing of 213 mm.
Outer rail-fastener center rectangle: 204 mm fore/aft by 213 mm transverse.
Inner threaded-feature center rectangle: 204 mm fore/aft by 176.5 mm transverse.
OEM callout points to an inner feature: M6 tapped hole, depth 12 mm; separate Ø12 callout identifies the ring feature. Do not assume a complete counterbore specification or copy these inner positions onto the bare rails.
The 301×231 envelope is NOT the separate flat lid size.
The supplied public top plan does not dimension lid thickness, every small perimeter screw, corner radii, wall thickness, underside contact geometry or datum tolerances. STEP geometry must be inspected for what it retains and physical interface checked before fabrication.

INSTALLATION / BARE RAILS
https://support.unitree.com/home/en/A2_SDK_Development_Guide/docking_installation
OEM figure dock-install-m6-nut-rail-interface.png shows four nuts in the factory rails, dock placed above and M6×14 screws. That screw length applies to the OEM assembly; select new hardware length from actual custom stack thickness and engagement. Bare rails use 213 mm cross-rail centers. The inner 176.5-mm pattern belongs to the dock, not the bare A2 rails.

PHYSICAL PART AVAILABILITY CHECK
Official shop https://shop.unitree.com/collections/all and ?page=2 (34 products) plus https://shop.unitree.com/products/unitree-a2: no verified separate V1 shell or lid listing found. Official A2 technical docs identify a computing expansion dock, not a lid spare part.
Seller category https://crkphotoimaging.com.au/robotics/batteries-and-accessories/_brands/unitree lists SKU UTA2DOCK as 'Unitree A2 High Computing Power Docking Station Kit (Backpack Processor)'. It supports availability of a full compute kit, not a blank shell or an assurance of V1 version.
Observed exact seller detail URL: https://crkphotoimaging.com.au/products/uta2dock/unitree-a2-high-computing-power-docking-station-kit---backpack-processor--
Detail fetch timed out; category title is the only evidence used. No purchase or contact made.

DESIGN CONSEQUENCE
Use the official V1 STEP as the starting geometry/reference for the chosen flat-top visual form, then make a new rail-mounted camera carrier with the requested features. Do not describe this as modifying a separately obtained OEM lid unless such a physical part is actually sourced. A cosmetic one-solid dock model is not by itself a qualified structural printed camera bracket. No new 3D model created in this phase.

PROVENANCE
cad-download-manifest.json contains URLs, download lengths, original archive members, server headers and SHA-256 hashes. step-inspection.json records original UTF-8 filenames, STEP headers, geometry entity counts and hashes. reference-images-manifest.json records unchanged OEM illustration provenance. Named STEP files are byte-identical exports, renamed for convenient use. Original archive extraction directories preserve ZIP-decoded member names, including metadata.

READ-ONLY CAD VALIDATION
Imported the V1 standalone STEP successfully with gmsh's OpenCASCADE importer. One volume, positive volume 1,300,719.829 mm³. This checks basic readable solid geometry, not strength, watertight-print behavior, surface validity or manufacturing fitness.

The STEP uses millimetres. Its 0.001 exchange uncertainty is not a manufacturing accuracy claim.

IMPORTANT DRAWING / SIMPLIFIED MODEL DIFFERENCE
Outer four ear-hole circles in this STEP have modeled diameter 6.2 mm and center spans 204.1861305 mm longitudinal ×213.0040000 mm transverse. This differs slightly from the OEM drawing's nominal204×213 mm. Circle centers were reconstructed from three evaluated points on each analytic semicircle, not estimated from raster or arc center-of-mass. The inner Ø12 rings span204.0000000×176.5000951 mm, effectively matching drawing nominal204×176.5.
Use OEM nominal drawings as nominal interface dimensions and measure the robot before fabrication. Do not copy a simplified STEP's small discrepancies as manufacturing requirements. The tapped-thread depth/counterbore details have not been independently verified in the geometry.

Default OCC conservative overall bbox spans301.130×232.620×35.124 mm. Because spline bounds can include a control polygon, these are NOT exact outside dimensions. Enabling Geometry.OCCBoundsUseStl gave an approximate tighter envelope300.681×231.044×34.001 mm; it is still an approximate check, not a replacement for the drawing. The concept remains301×231 nominal. The CAD remains one merged/simple solid: no separate lid component was supplied.

v1-dock-geometry-summary.json is the concise checked result, including exact curve IDs and circle centers in the STEP's original coordinates. v1-dock-gmsh-inspection.json retains the detailed importer observations. No new model or mechanical geometry was authored.
