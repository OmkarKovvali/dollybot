# Unitree A2 camera rig — assets and concept

Collected November 23, 2026. Current assembly revision 07 uses the owner's selected **V1 outline with closed side openings and a flat top**. Integrated raised camera and stick interfaces are removed; the user-selected INNOREL C19 ball head is modeled as a separate commercial accessory on the flat cover. Two provisional Ø7 mm clearance bores take bottom-up 1/4-20 screws; underside head recesses and required rail attachment holes remain. The interactive viewer includes the official A2 assembly with adjustable opacity. Derived geometry is for concept review, not a validated printable adapter or G-code.

See [the interactive viewer notes](viewer/README.txt) for the current assembly and geometry limitations. Start the local viewer at [127.0.0.1:8770](http://127.0.0.1:8770/). The [earlier V1 cover design update](v1-cover-update/README.md) retains source research; its commercial quick-release and metal backing proposals are superseded. Revision 04's printed quick-release and raised pole seat are also superseded by revision 05. The earlier two-clamp bridge is archived under `v1-cover-update/previous-concept-02/`.

## Confirmed equipment

| Item | Confirmed configuration | Reference inputs |
| --- | --- | --- |
| Robot | Unitree A2, **bare factory back rails**, no expansion dock | Rail centerlines **213.00 mm** apart; OEM sliding M6 nut attachment |
| Printer | **Bambu Lab H2S**, clarified by owner | **340 × 320 × 340 mm** nominal build volume |
| Main camera | Sony ZV-E1, **Sony FE PZ 16–35mm F4 G (SELP1635G)**, confirmed by receipt | Body 121 × 71.9 × 54.3 mm; 483 g with battery/card, before lens |
| 360 camera | Insta360 **X6**, Essentials Bundle, black | 50 × 100 × 40 mm including lenses; 196 g |
| Stick | Bundle reference includes a **114 cm Invisible Selfie Stick** | Owner photo selects newer gold-band version: seven tubes; 1140 mm maximum, provisional 233 mm collapsed; diameters and working extension unmeasured |

The lens is now identified as SELP1635G. The actual tripod socket location, any cage, and detailed pole dimensions remain open. A local slicer preset is not evidence of the owned printer; the owner's H2S confirmation governs this project.

## Open these first

| Asset | What it provides |
| --- | --- |
| [Interactive flat-cover concept](http://127.0.0.1:8770/) / [viewer notes](viewer/README.txt) | Current revision 07: seam-free top, telescoping stick with height slider, actual robot with adjustable opacity |
| [Earlier V1 cover sketch](v1-cover-update/concept/a2-v1-cover-concept.png) / [editable SVG](v1-cover-update/concept/a2-v1-cover-concept.svg) | Revision 03 research sketch; metal backing and commercial quick-release proposals superseded |
| [Official reference gallery](a2-mounting/official-references.html) | Unchanged Unitree rail/dock drawings, V1/V2 appearance, connectors and internal hardware diagram |
| [Official rail drawing](a2-mounting/guide-rail-drawing.png) | Primary mating-interface reference for this owner's bare-rail robot |
| [Official V1 STEP](v1-cover-update/cover-research/unitree-a2-v1-docking-station-20260509.stp) / [bare A2 STEP](v1-cover-update/cover-research/unitree-a2-bare-simplified.stp) | Current primary solid-CAD references for the selected cover and robot |
| [Official hardware block diagram](a2-mounting/internal-hardware-block-diagram.png) | Actual OEM functional architecture; not a PCB circuit schematic |
| [A2 CAD preview](a2-cad/base-mesh-inspection.png) | Inspected top/side geometry of the OEM base mesh |
| [Pinned OEM URDF](a2-cad/official-a2/urdf/a2.urdf) / [MJCF](a2-cad/official-a2/a2.xml) / [meshes](a2-cad/official-a2/meshes) | Robot geometry and kinematics, with source license preserved |
| [Download model ZIP](a2-cad/official-a2-cdf67e6.zip) | All 20 OEM files plus provenance notes/manifest; approximately 6.3 MB compressed |
| [Offline A2 manual V1.7](a2-mounting/a2-manual-offline.html) | All 28 original page images, including battery access and operating references |
| [H2S specification PDF](printer-cameras/assets/bambu-h2s-official-spec-sheet.pdf) | Manufacturer print-volume and printer specifications |
| [Sony full manual](printer-cameras/assets/sony-zv-e1-help-guide.pdf) / [bottom view](printer-cameras/assets/sony-zv-e1-bottom-illustration.png) | Tripod socket and battery-door reference |

## Which CAD is most precise?

**The official simplified STEP files are now the primary mechanical references.** The [Unitree Get SDK page](https://support.unitree.com/home/en/A2_SDK_Development_Guide/get_sdk) provides a V1 docking-station STEP and an A2-with-V1-dock STEP. Both have been downloaded. This supersedes the earlier search conclusion that only URDF/STL assets were available.

- [V1 dock STEP](v1-cover-update/cover-research/unitree-a2-v1-docking-station-20260509.stp): exported May 9, 2026; one simplified solid. It is not a separately modeled lid or native parametric source.
- [Bare A2 STEP](v1-cover-update/cover-research/unitree-a2-bare-simplified.stp): official simplified robot solid reference for the owner's bare-rail configuration.
- [A2 + V1 dock STEP](v1-cover-update/cover-research/unitree-a2-with-v1-docking-station.stp): exported July 8, 2026; full robot/dock reference.
- [Current selection and limitations](v1-cover-update/README.md): use these solids with the OEM interface drawings and physical fit checks.

The STEP files explicitly use **millimeters**. They are OEM-labeled simplified models, with no implied manufacturing tolerance or load certification. The V1 image and outer mounting drawing define the selected concept; inspect the actual solid before editing its top surface.

The V1 solid imported successfully. Its outer hole-center span is approximately 204.186 × 213.004 mm, slightly different from the nominal 204 × 213 mm drawing. [Geometry check](v1-cover-update/cover-research/v1-dock-geometry-summary.json) records the discrepancy; retain the physical fit check.

Retain the [official URDF/MJCF pack](a2-cad/README.txt) for robot joint structure, simulation and kinematics. Its latest A2-specific revision is June 9, 2026 (`cdf67e6`); its meshes date to January 4, 2026. Those STL coordinates are meter-valued and require **×1000** when imported into millimeter CAD. Do not apply that scaling to the new STEP files. The model ZIP linked above contains the earlier URDF/STL pack; the STEP downloads are separate.

## Mounting definition

Unitree's [About A2 guide](https://support.unitree.com/home/en/A2_SDK_Development_Guide/about_a2), displayed as updated November 5, 2026, provides the following nominal rail dimensions:

| Dimension | Value |
| --- | --- |
| Rail centerline separation | 213.00 mm |
| Slot mouth | 6.2 mm |
| Internal channel width | 10.1 mm |
| Rail outside width | 18.1 mm |
| Top to underside of lip | 2.8 mm |
| Top to channel floor | 6.5 mm |

The [OEM dock installation](https://support.unitree.com/home/en/A2_SDK_Development_Guide/docking_installation) specifies inserting **supplied M6 hex nuts** in the rails, then using M6×14 screws for that OEM assembly. It does not establish the correct screw length for a printed bridge. The inferred channel height under the lip is only 3.7 mm; an ordinary full-height M6 nut may not fit. Retain or measure the appropriate OEM nuts and calculate custom bolt engagement and floor clearance from the real stack.

The drawing's longitudinal screw locations describe existing rail hardware. They are not a set of free body-shell mounting holes. The concept uses sliding nuts and leaves the rail-retaining screws in place. No custom payload torque or rail moment rating was found.

Both robot batteries withdraw sideways from the same side; the original manual shows this clearly. The adapter must preserve the side latches, handles, extraction path, cooling, connectors, native perception and leg motion. Do not add a belt or side skirt across the battery faces.

## Proposed arrangement

The current concept follows the flat V1 housing's **301 × 231 mm** plan envelope and four mounting ears. The owner's image exactly matches the archived OEM V1 render. That render shows a housing assembly with a lid and connector apertures; it is not itself a solid CAD file or a verified separately sold lid.

- **Robot interface:** four attachment positions span **204 × 213 mm** in the OEM drawing. Use metal fasteners and the proper captive rail nuts. The separate inner M6 dock threads are not the bare-rail attachment pattern.
- **Sony interface:** the camera uses a **plain Ø7 mm clearance hole at (−48, 0) mm** for the selected INNOREL C19 ball head, with an underside screw-head recess. The cover has no integrated raised platform; the separate C19 sits on the flat top and supports the Sony. The earlier [Falcam research](v1-cover-update/quick-release/quick-release-recommendation.txt) is retained as history. The official [Sony guide](https://helpguide.sony.net/ilc/2310/v1/en/contents/221h_names_of_parts_ilc2310_bottom.html) requires camera screw protrusion **strictly less than 5.5 mm**.
- **Pole interface:** a **metal 1/4-20 screw inserted upward from below** passes through a provisional **7.0 mm clearance bore** into the stick's female base. Revision 05 removes the raised pole seat, leaving a flat top and a real underside counterbore/access well to recess the screw head. **No metal washer or backing plate.** Verify actual stick thread/depth and selected screw head before setting fabrication dimensions.
- **Print layout:** **301 × 231 mm fits the H2S's 340 × 320 mm XY area** when the 301 mm direction runs along X. The old 280 mm module target no longer applies. Final height, thickness, underside support, brim and print orientation are still open.
- **Access:** preserve same-side battery withdrawal. Install the recessed stick screw from the underside before fitting the printed housing to the rails if access is blocked by the robot. Keep native perception and limbs clear.
- **Power:** use each camera's own battery for the initial mechanical concept.

Pole height and motion matter more than camera weight alone suggests. As an illustration, the 0.196 kg X6 at a 1.14 m lever arm produces about **2.19 N·m** under **1 g transverse acceleration** (`m × a × h`), before stick mass and dynamic amplification. This is not vertical static loading, a measured walking load, or an allowable rail moment. The actual camera lever arm differs from nominal stick length; intended working height is still needed.

## What V1 and V2 look like

The expansion dock is a separate **Jetson Orin NX compute and interface module**; it is distinct from the Intel development computer already in the robot. It is unnecessary for this bare-rail camera attachment concept.

| V1 | V2 |
| --- | --- |
| [Housing render](a2-mounting/dock-v1-render.png) | [Housing render](a2-mounting/dock-v2-render.png) |
| [Installed on A2](a2-mounting/a2-with-dock-v1.png) | [Installed on A2](a2-mounting/a2-with-dock-v2.png) |
| Flat top, separately installed antennas | Internal antennas under a raised top-cover enclosure |
| [Dimension drawing](a2-mounting/dock-v1-dimensions.png) | [Dimension drawing](a2-mounting/dock-v2-dimensions.png) |

Unitree says the internal compute and interfaces are identical between dock versions. V2 changes the cover geometry and can interfere with older payloads. Its drawing includes an 82 × 82 mm raised feature. These renders depict the dock housing; they are not photos of fully populated electronics. See the [official comparison](https://support.unitree.com/home/en/A2_SDK_Development_Guide/about_a2).

## Schematics collected

The original [OEM hardware block diagram](a2-mounting/internal-hardware-block-diagram.png) describes the motion-control computer, Intel user-development computer, networks, sensors, hubs and external interfaces. Connector drawings and accompanying pin tables are saved in the reference gallery and [archived official text](a2-mounting/about-a2-source.txt).

No component-level PCB schematic or full pin-to-pin wiring harness drawing was found in the examined public sources. The editable [project block diagram](project-block-diagram.mmd) is our functional summary of the camera concept, separate from the OEM document. Robot joint geometry comes from the URDF; the overall body is a 12-actuated-joint quadruped.

## Inputs needed for the next modeling step

1. Actual rail slot measurements, usable nut-entry access, nut thickness and fit. Confirm physical hardware matches the drawing.
2. Any Sony hood/filter/cage and assembled mass; SELP1635G lens and C19 mount are already selected.
3. Actual gold-band stick collapsed length, base diameter, female thread pitch/engagement, mass, and desired extension while walking.
4. Camera and pole clearance in chosen positions; side battery removal, sensor visibility and leg movement.
5. C19 adapter engagement, suitable fastener lengths, material, support settings and a load/retention check before equipment is installed. Upright Z+ printing is already selected.

The downloaded references are complete for this concept stage; those physical fit inputs remain explicitly unresolved. The derived cover STL is suitable for slicer inspection and fit prototyping; these inputs remain necessary for a validated loaded rig.

## Provenance and files

- [CAD download manifest](a2-cad/download-manifest.json)
- [Mounting reference manifest](a2-mounting/assets-manifest.json) and [manual manifest](a2-mounting/manual-manifest.json)
- [Camera/printer manifest](printer-cameras/download-manifest.json) and [research notes](printer-cameras/research-notes.txt)
- [Consolidated inputs](design-inputs.json)

Validation checks downloaded source records against recorded sizes and SHA-256 values, including upstream Git blob hashes for the URDF subset. Failed direct-download attempts are recorded as unavailable URLs, not local assets. Product facts are also captured through browsed official pages and downloaded manufacturer images. See [validation results](asset-validation.json) for the current counts and local-link check.

Primary references also include the [H2S datasheet](https://store.bblcdn.com/s7/default/3f91ec86de1a4ce28fe8fb660b95cd3e/h2s.pdf), [Sony specifications](https://helpguide.sony.net/ilc/2310/v1/en/contents/221h_specifications_ilc2310.html), [X6 specifications](https://www.insta360.com/specs/x6), and [X6 Essentials Bundle](https://store.insta360.com/product/x6?c=6922). Manufacturer originals are retained for this research with attribution; public accessibility is not a blanket redistribution license. H2D/H2C references in the camera folder document an earlier model-identification branch and do not apply to the confirmed H2S.

## Detailed camera assets

The interactive rig now uses reference-based models of the [Sony ZV-E1](viewer/dist/assets/sony-zv-e1.glb), [Sony FE PZ 16–35mm F4 G](viewer/dist/assets/sony-selp1635g.glb), and [Insta360 X6](viewer/dist/assets/insta360-x6.glb). Each has metadata and build sources under `viewer/camera-models/`. Published overall envelopes are constrained; small feature and tripod positions are estimates, not OEM CAD.

The identified lens replaces the earlier 18–50 mm assumption. The user subsequently selected the [INNOREL C19](https://innoreltech.com/products/cnc-metal-low-profile-mini-ballhead-innorel-c19), which raises the Sony above the cover. The camera hole is restored to (−48, 0) mm. The manufacturer dimension graphic gives 47.5 mm through the stud tip; the model uses a provisional 42.5 mm rubber-pad seating height. The supplied base adapter permits a 1/4-inch fastener through the printed clearance hole. Physical stud protrusion, seating height and engagement still need measurement.

## Telescoping stick and upright cover export

The stick model matches the newer gold-band style in the owner’s reference image. Its seven rigid tubes slide on six joints; the camera moves with the upper mount. The always-visible slider adjusts nominal stick length, reports X6 base height above the cover, and preserves the viewing angle while reframing. The nominal 1140 mm maximum is published; 233 mm retracted, individual tube sizes, strokes and exposed thread length remain provisional. See [reference evidence](viewer/camera-models/stick/research-findings.txt) and [model dimensions](viewer/dist/assets/insta360-114cm-stick.json).

The narrow OEM lid groove is filled to make the top continuous. The cover exports alone with Z+ up; its underside, rail interfaces and screw bearing seats are preserved. No low-risk underside change was found that would materially reduce supports while retaining known robot clearance. See [upright support review](viewer/print-review/upright-support-review.json).

Standalone export: [printed cover, Z+ up, millimeters](exports/Unitree_A2_Camera_Cover_Concept_Zplus_mm.stl). A verified identical copy was saved to `/Users/vinnie/Downloads/Unitree_A2_Camera_Cover_Concept_Zplus_mm.stl`.
