A2 CAMERA RIG — CURRENT ASSEMBLY REVISION 07

Run from the workspace root:
python3 -m http.server 8770 --bind 127.0.0.1 --directory research/unitree-a2-camera-rig/viewer/dist
Open http://127.0.0.1:8770 in the browser or Codex panel.

Drag to rotate; scroll/pinch to zoom; right drag to pan.
View controls opens the panel on narrow windows. Show equipment toggles
the cameras, lens, ball head and stick. Inspect Sony, Inspect X6 and
Inspect INNOREL C19 frame those assemblies. Show robot and Robot opacity
control the unchanged, registered official A2 model. Fit assembly frames
the whole dog. Hide equipment to inspect the flat cover's two bores.

CURRENT COVER
Closed side port openings and filled OEM top lid groove. No integrated raised camera platform, printed
quick-release, pole boss or locating collar. Two provisional 7 mm smooth
clearance bores: camera mount(-48,0), stick(78,0), in viewer millimeters.
Underside12mm head recesses retain the earlier recessed-head requirement.
Factory rail attachment geometry remains. Both temporary forward/offset
positions are superseded; the centered camera hole is restored per owner.
The carrier is 3D printed; the separate C19 is a commercial metal accessory.

CURRENT CAMERA STACK
Flat cover topZ34 → INNOREL C19 bottomZ0 at(-48,0,34) → Sony ZV-E1 bottom
on the modeled C19 rubber pad → Sony FE PZ16-35mm F4G (SELP1635G).
The C19's published47.5mm overall height includes the stud. The modeled
camera seating height42.5mm and exposed stud5mm are photo estimates,
not separately published interface dimensions. The bottom3/8-inch socket
uses the supplied1/4-inch adapter for the requested cover fastener.
Verify actual stud insertion, adapter depth and engagement on the hardware.
Sony's entering screw length must be strictly less than5.5mm.

Reference-based Sony body, SELP1635G lens, X6 and C19 GLBs, metadata,
Blender sources and official photos are stored in dist/assets and
camera-models/. Published overall camera/lens envelopes are constrained;
small features and tripod XY are visual estimates, not manufacturer CAD.
Hood and lens caps are omitted. The stick matches the newer gold-band
114cm reference selected by the owner. Seven fixed-length tubes move by
translation, with six gold joint bands, diagonal grip, knurled head and
modeled threaded ends. Nominal full extension1140mm is published;233mm
retracted is a provisional legacy-family value. Tube diameters, individual
strokes, overlap and5mm exposed stud are estimates. The slider displays
nominal bottom-to-tip length and X6 base height above the cover. The camera
sits5mm below the modeled tip. Travel is distributed evenly for viewing;
the real independently sliding sections need not extend in this order.
The slider remains available in narrow windows. Retract / Extend change
height; Fit view reframes the assembly. Extension is not a load rating.

VERIFICATION SCOPE
flat-cover-concept.stl/.brep/.json contain actual filled side geometry and
bores. flat-cover-body-intersection.json screens all47 registered robot
parts and checks the exact solid collision candidates against the final
hash-matched cover. Zero overlap refers only to the saved static CAD pose.
The C19 camera stack is displayed upright; no tilt-sweep, walking impact,
vibration, retention, structural strength or physical tolerances validated.
Install underside fasteners before fitting the carrier if the robot blocks
tool access. Owner selected upright Z+ printing with support beneath. The OEM underside
is retained to preserve robot clearance and screw bearing surfaces. Material,
walls, support settings and physical fit still need selection in the slicer.

The original OEM and earlier concept assets are preserved. Three.js and
its loaders are vendored with THREE-LICENSE.txt; no runtime CDN is used.

EXPORT
../exports/Unitree_A2_Camera_Cover_Concept_Zplus_mm.stl contains only
the closed, single-component printed cover, upright with native Z+ up.
Dimensions300.679 x231.041 x34.000mm; scale1.0 in millimeters.
A matching copy is in the owner's Downloads folder. Supports are not included.
