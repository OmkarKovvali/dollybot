CURRENT CAD SELECTION UPDATE — 2026-11-23
Official simplified STEP files have now been found on Unitree Get SDK and downloaded:
../v1-cover-update/cover-research/unitree-a2-v1-docking-station-20260509.stp
../v1-cover-update/cover-research/unitree-a2-bare-simplified.stp
../v1-cover-update/cover-research/unitree-a2-with-v1-docking-station.stp
Use those as primary mechanical references; retain this pack for kinematics.
The original search notes below describe the earlier search stage and their no-STEP finding is superseded.
STEP uses millimeters; the meter-to-mm scaling warning below applies only to the URDF STL files.
See ../v1-cover-update/README.md for the current design.

UNITREE A2 — OFFICIAL MODEL ASSET PACK
Retrieved and checked: 2026-11-23

SELECTION
Use the OEM unitree_ros A2 visual/kinematic package for concept packaging and
clearance, together with the newer OEM back-load interface drawing collected in
../a2-mounting/README.txt. No verified public full A2
STEP/native engineering assembly was located. Do not mistake a mesh converted
to STEP for more precise geometry, or substitute A1/As2/Go2/B2 assets.

The official STL base is visibly simplified across the top deck. Its apparent
precision (many decimal places) is numerical mesh precision, not an assurance
of mounting dimensions, thread identity, surface tolerance, or load rating.
The OEM interface drawing describes guide rails, so it is the controlling
source for the mating mount;
confirm its match to the owner's actual A2 hardware revision before modeling.

DOWNLOADED ASSETS
  official-a2/urdf/a2.urdf — joint tree, inertias, visuals, simplified collisions
  official-a2/a2.xml — MuJoCo MJCF simulation model
  official-a2/meshes/*.STL — 17 binary STL mesh files
  official-a2/LICENSE — repository BSD 3-Clause license, retained verbatim
Total: 20 files, 14,777,890 bytes. Per-file sources, sizes, SHA-256 and Git blob
IDs are in download-manifest.json. This is an intact subset, preserving paths;
it is not a ROS catkin package and has no package.xml.

VERSION PROVENANCE
Repository: https://github.com/unitreerobotics/unitree_ros
Inspected master HEAD: 157ff950351e5f535e03c5d85a16b7d594b3dbcc
Latest A2-specific commit: cdf67e6eb4c98d73202f29a25e3d098e2aa3b247
Commit time: 2026-06-09T09:16:08Z; message: add a2 camera and lidar link
Latest mesh change / initial A2 package: 29cc27f7578e010165042e1fe45cc18f3a4dd2ca
Commit time: 2026-01-04T07:11:26Z; message: add a2_description
All assets are downloaded via immutable URLs at the latest A2-specific commit.
The saved GitHub history/tree JSON files provide the evidence for 'latest
public package found'; this does not claim all manufacturer-private CAD.

INSPECTION
STL is a unitless format, but these coordinates are meter-valued in the URDF.
When importing into millimeter CAD, scale coordinates by 1000. Do not interpret
715 mm of actual body length as a 0.715 mm miniature.

base_link.STL: 68,422 triangles.
Its own bounding dimensions are 715.10 x 286.37 x 210.55 mm (X/Y/Z).
This is the base alone, not the complete robot's standing envelope.
Mesh bounds in base frame (mm):
  X = -327.851 to +387.248; Y = -143.181 to +143.189;
  Z = -80.253 to +130.300.

URDF: 20 links, 19 joints, 12 actuated revolute joints, 4 fixed foot joints,
3 fixed sensor joints. Each leg is hip -> thigh -> calf -> fixed foot.
Left/right hip locations relative to base: X +/-259.44 mm, Y +/-75.113 mm.
These are kinematic datums, not payload bolt-hole locations.

URDF summed link mass is 40.071 kg. Current Unitree product page lists about
42 kg with batteries; configuration/version correspondence is not established.
Therefore do not use simulation mass/inertia as the actual loaded robot's
certified mass properties. Front and rear LiDAR frames are present in URDF;
confirm the owner's sensor configuration (current product table differs for
A2 versus A2-PRO).

base-mesh-inspection.png / .svg are TOP (+Z) and SIDE (-Y) projections, with
+X toward the front (consistent with the camera and front LiDAR joint frames).
They are inspection previews, not manufacturing drawings. mesh-analysis.json
contains per-mesh triangle counts/bounds and the parsed joint list.

SOURCE COMPARISON
1. Official Unitree ROS A2 package: selected. OEM provenance, version history,
   inspectable geometry and 12-DOF joint layout. Limits: triangle surface
   meshes, simplified collisions/deck, no parametric solids or thread metadata.
   https://github.com/unitreerobotics/unitree_ros/tree/master/robots/a2_description
2. Official Unitree support About A2 / back-load drawings: selected for mount
   definition, retrieved separately by the mounting research agent. Newer
   documentation is not proof that the older mesh matches every shipping unit.
   https://support.unitree.com/home/en/A2_SDK_Development_Guide/about_a2
3. Official unitree_model GitHub: no A2 paths in inspected tree. Repository is
   deprecated and points to Hugging Face. Inspected SHA
   b6a8942b0803b6c137e58cef12beb4b03e4a2fa7.
   https://github.com/unitreerobotics/unitree_model
4. Official Hugging Face dataset: no A2 folder at inspected main root; listed
   B2, G1, Go2, Go2W, H1-2, H1, H2. No better A2 model found there.
   https://huggingface.co/datasets/unitreerobotics/unitree_model/tree/main
5. Commercial 3DModels.org A2 Stellar Explorer listing surfaced in search and
   advertises CAD-compatible conversion formats. Search text describes it for
   visualization/interactive use. Full page fetch returned 403. No verified
   manufacturer dimensions, tolerances or mounting accuracy were established;
   not purchased/downloaded and not selected over OEM assets.
   https://3dmodels.org/3d-models/unitree-a2-stellar-explorer/

CURRENT OEM PRODUCT REFERENCE
https://www.unitree.com/A2/
Standing dimensions: 820 x 440 x 570 mm. This is a posture envelope, not a
mounting template. Variant, battery configuration and documentation version
must be recorded for the physical unit before detailed adapter CAD.

REPRODUCTION
  python3 download_assets.py     (requires network; writes this pack only)
  python3 inspect_meshes.py      (stdlib parser; regenerates SVG and JSON)
The PNG was rendered locally from the generated SVG using existing pymupdf
at /private/tmp/fab-sku-pdf-lib with /opt/homebrew/bin/python3.

NEXT INPUT FOR FABRICATION
Use the OEM interface drawing plus a physical fit check for thread sizes,
usable engagement depth, hole spacings, standoff/contact surfaces, keep-outs,
and robot variant. No adapter has been modeled in this step.
