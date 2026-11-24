# V1 camera cover — revision 03

**Historical concept.** Revision 04 supersedes the metal backing and commercial quick-release proposals below: the owner requested a fully printed structure, a recessed screw head, and an A2 assembly view with adjustable opacity. See the [current interactive viewer notes](../viewer/README.txt) and [asset index](../README.md). Source research and OEM downloads below remain relevant.

The selected image is exactly Unitree's **V1.0 docking-station housing render**, verified by matching its SHA-256 to the original downloaded image. The robot remains the owner's bare-rail A2. The new concept uses this housing as the shape/interface reference, adds the requested underside stick bolt, and reserves a mounting pad for a commercial camera quick-release.

## The cover has an official STEP model

The [official Get SDK page](https://support.unitree.com/home/en/A2_SDK_Development_Guide/get_sdk) links the following downloads, now saved locally:

| Local asset | What it is |
| --- | --- |
| [V1 docking-station STEP](cover-research/unitree-a2-v1-docking-station-20260509.stp) | Official simplified AP214 solid, exported May 9, 2026; approximately 4.85 MB |
| [Original V1 ZIP](cover-research/unitree-a2-v1-dock.zip) | Original manufacturer archive, approximately 1.27 MB |
| [A2 with V1 dock STEP](cover-research/unitree-a2-with-v1-docking-station.stp) | Official assembly reference, exported July 8, 2026; approximately 77.4 MB |
| [Original assembly ZIP](cover-research/unitree-a2-with-v1-dock.zip) | Original manufacturer archive, approximately 21.5 MB |
| [Bare A2 STEP](cover-research/unitree-a2-bare-simplified.stp) | Official simplified solid reference for the owner's bare-rail robot |
| [V1 dimension drawing](../a2-mounting/dock-v1-dimensions.png) | 301 × 231 mm envelope; outer attachment centers 204 × 213 mm |
| [Cover research](cover-research/README.txt) | Search results, geometry inspection and sourcing limits |

This corrects the earlier asset-stage finding that no verified public A2 STEP had been located. **Use the official STEP files as the primary mechanical CAD; retain the URDF for kinematics.** These are manufacturer-labeled simplified models. The V1 file is a single solid, not a separate removable lid or a native parametric assembly. Its explicit unit is millimeters; do not apply the ×1000 conversion required by the earlier URDF STL files. Exchange precision is not a manufacturing tolerance or load rating.

The pictured object includes the outer enclosure, mounting ears and side port apertures. A separately sold bare lid/housing has not been verified. The printable adaptation will use the selected form and verified rail interface; no purchase of the complete compute dock is implied.

**Geometry check:** the V1 STEP imports successfully as one OpenCASCADE volume. Its modeled outer hole-center spans are approximately **204.186 × 213.004 mm**, versus the drawing's nominal **204 × 213 mm**. The inner ring centers agree closely with the nominal 204 × 176.5 mm drawing. Keep this small source discrepancy visible during fitting; copying the simplified solid does not eliminate the physical rail/nut check. [Geometry summary](cover-research/v1-dock-geometry-summary.json)

## Revised feature concept

[View the concept sheet](concept/a2-v1-cover-concept.png) · [Editable vector drawing](concept/a2-v1-cover-concept.svg)

**Insta360 stick:** a metal **1/4-20 bolt goes upward from the underside**, through an unthreaded clearance hole into the stick's existing female base. The sketch uses **Ø7.0 mm nominal clearance** as a proposed print-fit dimension, not a manufacturer specification. Add a broad metal washer/load spreader below a reinforced printed boss; an optional shallow seat locates the pole base. The pole's actual thread pitch, insertion depth and base diameter must be checked before choosing bolt length. The Sony's 5.5 mm limit does not apply to the stick. Preserve access for the bolt head/tool and clearance to the robot below.

**Sony camera:** recommended **Falcam F38B3404 Multi-hole Base & Plate Kit**. The base stays attached to the cover and the plate stays on the camera, so normal removal does not involve unscrewing the camera. The manufacturer lists a **53.4 × 38 × 20.8 mm** assembled envelope, **51.7 g**, push-in/button release and a secondary button lock. Use the F38 plate supplied with the kit; the base does not accept arbitrary Arca plates. Follow the manufacturer's lens-to-button orientation and keep finger access clear. [Official product](https://www.ulanzi.com/products/falcam-f38-multi-hole-quick-release-kit-f38b3404)

Attach the quick-release base with measured bottom-hole positions and a positive anti-rotation register in the printed pad. Manufacturer underside images show the interface but do not dimension its hole centers or thread engagement. The camera-side 1/4-20 screw must protrude **less than 5.5 mm** into the ZV-E1. [Sony guide](https://helpguide.sony.net/ilc/2310/v1/en/contents/221h_names_of_parts_ilc2310_bottom.html)

**Alternative:** SmallRig **2144B** is a lever-operated Arca clamp/plate kit if broader Arca compatibility is preferred. Its [official manual](quick-release/assets/smallrig-2144b-official-manual.pdf) and product references are saved alongside the F38 references. No hardware has been purchased.

**Printer fit:** the 301 × 231 mm reference footprint fits the H2S's 340 × 320 mm XY envelope with the long side along X, leaving 39 mm and 89 mm total nominal clearance respectively. Final support/brim needs and height depend on the edited solid. The previous 280 × 280 mm module target is superseded.

## What is complete and what remains

Complete: exact reference identified; official cover and assembly CAD downloaded; through-bolt attachment captured; quick-release recommendation and source images collected; revised 2D feature layout prepared.

Before adding final holes to the solid: inspect the OEM simplified solid's surfaces/underside; decide which regions need a printable structural shell; verify the pole base and quick-release screw interfaces; set bolt head/tool clearances and check the assembled lens/pole positions. Camera battery door, release-button access, same-side robot battery extraction, native sensors and limb clearances remain part of the fit check. An extended pole's bending load needs to be carried by the reinforced seat and fasteners, not just a thin cover skin.

This is the updated feature concept and source asset package. It is not yet an edited/print-ready adapter STEP or STL. The original manufacturer STEP files remain unchanged.
