# Unitree A2 camera rig — assets and concept

Collected November 23, 2026. This pack supports a concept review before adapter CAD. It includes the best verified public OEM A2 geometry found, dimensioned mounting drawings, original hardware diagrams, camera/printer references, and a preliminary 2D arrangement. No custom adapter solid, printable STL, or G-code has been created.

## Confirmed equipment

| Item | Confirmed configuration | Reference inputs |
| --- | --- | --- |
| Robot | Unitree A2, **bare factory back rails**, no expansion dock | Rail centerlines **213.00 mm** apart; OEM sliding M6 nut attachment |
| Printer | **Bambu Lab H2S**, clarified by owner | **340 × 320 × 340 mm** nominal build volume |
| Main camera | Sony ZV-E1, owner reports an **18–50 mm lens** | Body 121 × 71.9 × 54.3 mm; 483 g with battery/card, before lens |
| 360 camera | Insta360 **X6**, Essentials Bundle, black | 50 × 100 × 40 mm including lenses; 196 g |
| Stick | Bundle reference includes a **114 cm Invisible Selfie Stick** | Manufacturer says two styles may ship; actual grip diameter and intended working extension remain unknown |

The lens brand/model, cage or quick-release hardware, and actual pole dimensions remain open. A local slicer preset is not evidence of the owned printer; the owner's H2S confirmation governs this project.

## Open these first

| Asset | What it provides |
| --- | --- |
| [2D concept sheet](concept/a2-camera-rig-concept.png) / [editable SVG](concept/a2-camera-rig-concept.svg) | Side/top arrangement and proposed mechanical load path; illustrative, not fabrication geometry |
| [Official reference gallery](a2-mounting/official-references.html) | Unchanged Unitree rail/dock drawings, V1/V2 appearance, connectors and internal hardware diagram |
| [Official rail drawing](a2-mounting/guide-rail-drawing.png) | Primary mating-interface reference for this owner's bare-rail robot |
| [Official hardware block diagram](a2-mounting/internal-hardware-block-diagram.png) | Actual OEM functional architecture; not a PCB circuit schematic |
| [A2 CAD preview](a2-cad/base-mesh-inspection.png) | Inspected top/side geometry of the OEM base mesh |
| [Pinned OEM URDF](a2-cad/official-a2/urdf/a2.urdf) / [MJCF](a2-cad/official-a2/a2.xml) / [meshes](a2-cad/official-a2/meshes) | Robot geometry and kinematics, with source license preserved |
| [Download model ZIP](a2-cad/official-a2-cdf67e6.zip) | All 20 OEM files plus provenance notes/manifest; approximately 6.3 MB compressed |
| [Offline A2 manual V1.7](a2-mounting/a2-manual-offline.html) | All 28 original page images, including battery access and operating references |
| [H2S specification PDF](printer-cameras/assets/bambu-h2s-official-spec-sheet.pdf) | Manufacturer print-volume and printer specifications |
| [Sony full manual](printer-cameras/assets/sony-zv-e1-help-guide.pdf) / [bottom view](printer-cameras/assets/sony-zv-e1-bottom-illustration.png) | Tripod socket and battery-door reference |

## Which CAD is most precise?

Use **the official Unitree ROS A2 meshes for overall packaging, together with the newer official rail drawing for mounting**. Neither asset is sufficient by itself for a print-ready adapter.

The latest A2-specific public revision found in [Unitree's repository](https://github.com/unitreerobotics/unitree_ros/tree/master/robots/a2_description) is `cdf67e6eb4c98d73202f29a25e3d098e2aa3b247`, dated **June 9, 2026**. That update adds camera/LiDAR frames. The actual mesh geometry last changed **January 4, 2026**, at `29cc27f7578e010165042e1fe45cc18f3a4dd2ca`. The downloaded files are pinned to the June revision, so later upstream changes cannot silently alter this pack.

The pack contains 17 STL meshes, URDF, MJCF and the BSD-3 license: 20 files, 14,777,890 bytes. SHA-256 and Git blob hashes were checked, and mesh paths in both robot descriptions resolve. This is a reference subset, not a complete installable ROS package.

No verified public full native/STEP A2 engineering assembly was located. The official alternative model repositories did not contain an A2 model. A high-polygon visualization or an STL-to-STEP conversion would not add trustworthy thread dimensions or tolerances. [CAD selection and provenance](a2-cad/README.txt) documents the comparison.

**Import units:** STL is unitless; these particular coordinates are meter-valued. Scale by **1000** when importing into millimeter CAD. The base mesh alone measures approximately 715.10 × 286.37 × 210.55 mm; this is not the full standing robot envelope. The top deck is simplified and does not encode the rail interface adequately.

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

The first concept is a short removable bridge across the two factory rails, with a low Sony camera mount and a separate braced pole holder near the robot centerline. These are proposed design choices, not OEM-approved load ratings.

- **Robot interface:** printed feet/cross-members with metal M6 fasteners and the correct captive rail nuts. Keep fore/aft placement adjustable during fitting.
- **Sony interface:** a metal quick-release or camera plate attached to an anti-rotation saddle. Keep the lens mass low, with access for the battery door, screen, zoom travel and ports. The official [Sony bottom-view guide](https://helpguide.sony.net/ilc/2310/v1/en/contents/221h_names_of_parts_ilc2310_bottom.html) specifies **1/4-20 UNC** and screw protrusion into the camera **strictly less than 5.5 mm**. This is a maximum limit, not a target.
- **Pole interface:** two separated clamps on the same rigid lower tube, joined by a brace to the bridge. Confirm enough straight fixed-tube length for both clamps. Use the factory camera-to-stick fitting; do not substitute a printed camera thread. Clamp diameter, liner thickness and fastener engagement remain unset.
- **Print layout:** provisional target of no more than **280 × 280 mm footprint per printed module**, comfortably inside H2S nominal XY limits. This is a planning envelope, not a measured final plate size. Thickness, ribs, material, layer orientation, hardware and support/brim margins belong to the next engineering step.
- **Power:** initially use each camera's own battery and internal recording. Robot power is unnecessary for the mechanical concept; any later power/control integration must use the correct verified port and converter.

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
2. Exact Sony lens make/model, any hood/filter/cage, selected quick-release interface and assembled mass.
3. Actual stick grip diameter at two stations, straight rigid clamp length, stick model/mass, and desired extension while walking.
4. Camera and pole clearance in chosen positions; side battery removal, sensor visibility and leg movement.
5. Suitable fastener lengths, material, print orientation, and a load/retention check before equipment is installed.

The downloaded references are complete for this concept stage; those physical fit inputs remain explicitly unresolved. Begin detailed adapter CAD only after reviewing the concept and resolving the relevant dimensions.

## Provenance and files

- [CAD download manifest](a2-cad/download-manifest.json)
- [Mounting reference manifest](a2-mounting/assets-manifest.json) and [manual manifest](a2-mounting/manual-manifest.json)
- [Camera/printer manifest](printer-cameras/download-manifest.json) and [research notes](printer-cameras/research-notes.txt)
- [Consolidated inputs](design-inputs.json)

Validation checked 101 downloaded source records against recorded sizes and SHA-256 values, including upstream Git blob hashes for the CAD subset. Two direct Insta360 URL downloads returned HTTP 403 and are recorded as failed attempts, not local assets; X6 facts are also available in the downloaded official comparison page and bundle data. Local dossier links and the model ZIP were checked.

Primary references also include the [H2S datasheet](https://store.bblcdn.com/s7/default/3f91ec86de1a4ce28fe8fb660b95cd3e/h2s.pdf), [Sony specifications](https://helpguide.sony.net/ilc/2310/v1/en/contents/221h_specifications_ilc2310.html), [X6 specifications](https://www.insta360.com/specs/x6), and [X6 Essentials Bundle](https://store.insta360.com/product/x6?c=6922). Manufacturer originals are retained for this research with attribution; public accessibility is not a blanket redistribution license. H2D/H2C references in the camera folder document an earlier model-identification branch and do not apply to the confirmed H2S.
