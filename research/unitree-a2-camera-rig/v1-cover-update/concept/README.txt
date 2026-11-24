A2 V1 COVER CAMERA PLATFORM — 2D CONCEPT REVISION 03

Files:
  a2-v1-cover-concept.svg — editable original vector drawing
  a2-v1-cover-concept.png — visually checked 1800 x 1570 preview
  create_v1_concept.py — source generation script (Python standard library)

This sheet is a 2D feature-layout study, not adapter CAD or a manufacturing
release. No 3D adapter geometry was created. The OEM product image was inspected
for context but was not modified. The plan outline was drawn separately from
the existing dimensioned V1 reference, with schematic curves and ears.

Reference assets:
  ../../a2-mounting/dock-v1-dimensions.png
  ../../a2-mounting/dock-v1-render.png
  ../cover-research/unitree-a2-v1-docking-station-20260509.stp

The newly found OEM STEP asset supersedes the earlier research's absence of a
verified STEP source. The concept remains drawing-based; verify shape, ear
geometry and thickness against that STEP and the physical robot before CAD.
Official source page:
  https://support.unitree.com/home/en/A2_SDK_Development_Guide/get_sdk

OEM drawing dimensions used: 301 x 231 mm overall and 204 x 213 mm outer
attachment pitch. Curved outlines, longitudinal edge offsets, ear clearances,
and the concept's cover thickness were not dimensioned or inferred as exact.

Proposed hardware: Falcam F38B3404 commercial Base & Plate Kit. Parent research
supplied the published whole-kit envelope 53.4 x 38 x 20.8 mm and mass 51.7 g.
No mounting hole pattern was invented. Base stays on cover; plate stays on Sony.
Button/lens arrow faces the lens, with access space. Optional adapter/register
geometry remains provisional.

Pole attachment: metal 1/4-20 bolt inserted upward from the cover underside,
broad metal washer/load spreader, reinforced printed boss/ribs, and an optional
shallow locating seat. The nominal diameter-7 mm smooth hole is a provisional
design dimension. Verify the actual stick's female thread and engagement depth
before choosing bolt length. Pole base diameter and working height remain TBD.

The 301 x 231 mm envelope fits the H2S 340 x 320 mm XY build area; account for
brim and orientation. Both batteries withdraw from the same side; preserve
extraction and chassis bolt/tool access. Camera and stick positions are
provisional and drawn for discussion, not for collision or load certification.

Regenerate SVG:
  python3 create_v1_concept.py
PNG was rendered directly from SVG using pymupdf with the locally available
/opt/homebrew/bin/python3 and PYTHONPATH=/private/tmp/fab-sku-pdf-lib.

GEOMETRY CROSS-CHECK
The mounting researcher inspected the STEP with gmsh (see
../cover-research/v1-dock-geometry-summary.json). Its outer diameter-6.2 mm
hole centers measure about 204.186 x 213.004 mm, slightly different from the
OEM drawing's nominal 204 x 213 mm. This sheet keeps the OEM nominal dimensions;
do not blindly copy the simplified STEP holes into a fit-critical print. Verify
the physical rail fit and allow a measurement-driven attachment strategy.
