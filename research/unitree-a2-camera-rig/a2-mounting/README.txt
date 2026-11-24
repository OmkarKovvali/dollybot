CURRENT DESIGN UPDATE — 2026-11-23
The owner selected the V1 housing as the printed-cover reference. Official simplified STEP files, including the V1 housing and bare A2, are now in ../v1-cover-update/cover-research/. The original dimensional drawings below remain relevant; the prior no-solid-available search finding is superseded. Current concept: bottom-up metal 1/4-20 stick bolt and recommended Falcam F38B3404 camera quick-release. See ../v1-cover-update/README.md.

UNITREE A2 MOUNTING AND ELECTRICAL REFERENCE PACK
Retrieved: 23 November 2026. Scope: legged A2, not A1, Go2, B2, As2, or A2-W.

START HERE
Open official-references.html to review the unchanged OEM drawings and version comparison images. Open a2-manual-offline.html for the complete User Manual V1.7 (28 original page images). Download source, file size and SHA-256 are recorded in assets-manifest.json and manual-manifest.json. The OCR .txt companions under manual-pages are for search only; check original images for authoritative wording.

PRIMARY SOURCES
1. About A2, official SDK Development Guide:
https://support.unitree.com/home/en/A2_SDK_Development_Guide/about_a2
Page displayed Last Updated On: 2026-11-05 11:57:14 (timezone not specified).
Original document text actually loaded by that browser page is archived as about-a2-source.txt from https://doc-cdn.unitree.com/26/1071/en/26_1071_en
2. Official docking installation:
https://support.unitree.com/home/en/A2_SDK_Development_Guide/docking_installation
Original text: dock-installation-source.txt, from https://doc-cdn.unitree.com/26/1424/en/26_1424_en
3. User Manual V1.7, currently linked by Unitree's A2 download page:
https://marketing.unitree.com/article/en/A2/User_Manual.html
https://www.unitree.com/app/A2/
All 28 page-image assets use CDN paths dated 2026/9/16. This is an asset upload date, not proof of the manual's publication date. Footer copyright 2025 is not the revision date.
4. Current product specifications:
https://www.unitree.com/A2/
Archived a2-product.html.

MECHANICAL INTERFACE: VERIFIED IN OEM DRAWINGS
A. Bare-body payload guide rails (guide-rail-drawing.png).
- The dimension across the two rail centerlines is 213.00 mm.
- Guide rail sectional dimensions: slot mouth 6.2 mm; internal channel width 10.1 mm; outside width 18.1 mm.
- Vertical dimension from top to underside of lip is 2.8 mm; top to channel floor is 6.5 mm. The nominal 3.7 mm cavity clear height is calculated (6.5 - 2.8), not separately specified by Unitree.
- A chain along the illustrated rail reads 23.35, 39.31, 67.25, 54.50, 38.94, 23.35 mm. These are existing features shown in the rail drawing. They are NOT a specification that the shell has six available threaded payload holes. Do not remove rail-retaining screws or repurpose arbitrary visible screws based on the mesh.
- OEM dock-installation Step 1 explicitly inserts the supplied M6 hex nut in the slide rail and uses M6x14 screws. This supports a sliding captive-nut attachment concept; it does not approve any generic full-height M6 nut, define the nut thickness, or establish screw length for a custom thicker adapter.
- Before manufacture: confirm the actual robot's rail dimensions and entry access; retain or measure the OEM nut; verify nut engagement, slot floor clearance and fastener torque with Unitree. The source does not provide a custom payload fastener torque or rail force/moment rating.

B. Optional dock upper interface (dock-v1-dimensions.png and dock-v2-dimensions.png).
- Both drawings show 204 mm longitudinal spacing between mounting positions, 176.5 mm transverse spacing between the inner threaded positions, 213 mm transverse spacing at the outer rail-attachment positions, and dimensioned spans of 301 mm by 231 mm.
- Chinese callout M6 threaded hole, depth 12 mm applies to the dock's inner mounting positions; a separate diameter-12 feature is shown. This is a DOCK interface, not a body-shell tapped-hole spec.
- These are nominal OEM drawing dimensions. Manufacturing tolerances, safe torque, full datum scheme and detailed counterbore specification are not given. Confirm actual dock geometry before choosing engagement length.
- V1 has a flat cover and external antenna arrangement. V2 internalizes antennas, introducing a raised cover region. Official text explicitly warns that old payloads may not fit V2.
- V2 drawing: raised feature has an 82 x 82 mm dimensioned footprint. Rear view shows main deck 49 mm above underside datum, central raised feature 14.2 mm above deck and mounting bosses 17 mm above deck. Do not infer a complete keep-out volume or antenna clearance solely from these few dimensions.
- No complete solid CAD model of these interfaces was retrieved in this subtask; use the CAD agent's OEM model with these drawings as separate authoritative interface references.

BATTERIES AND ACCESS
- Manual printed page 14 (manual-pages/page-15.png) shows both battery packs entering from the same SIDE of the robot. Printed page 10 (page-11.png) shows pulling them out sideways after pressing their latches.
- Preserve side withdrawal, latch/handle access and hand clearance. A top bridge does not require a fictitious upward battery hatch; avoid brackets descending in front of the side battery faces.
- Official battery model BT3-02: 99.1 x 82.6 x 266.2 mm and 3.3 kg. These are pack dimensions, not an exact required free extraction-distance specification.
- Keep side connector covers/top cable cover serviceable; dock installation instructions use both. Preserve robot sensor, cooling, emergency-stop and limb clearance. Camera/telescope placement and sensor occlusion need checking on the actual variant.

CURRENT OEM PLATFORM SPECIFICATIONS
- Standing overall: 820 x 440 x 570 mm; prone: 720 x 550 x 220 mm.
- Approx. 35 kg without battery, 42 kg with batteries. Older reseller files may say 31/37 kg; do not silently mix versions.
- 12 joint DOF. Continuous walking payload about 25 kg; standing about 100 kg. These system-level numbers are not a per-rail/camera bracket load rating and do not define allowable telescope moment.
- Standard A2: one LiDAR + one HD camera. A2-Pro: two LiDARs + one HD camera. Hero copy and sensor section speak generically of front/rear sensors; defer to variant table and physical robot.
- Nominal supply 50.4 V; battery charge limit 58.8 V. Two 9000 mAh / 453.6 Wh packs.
- There are conflicting joint-limit conventions/values within the OEM About A2 page (marketing table vs Joint Index and Joint Limits section). Do not derive adapter clearances solely from those mixed tables. Use actual motion envelope and matching robot/URDF version.

WHAT THE SCHEMATIC ASSET ACTUALLY IS
internal-hardware-block-diagram.png is an ORIGINAL UNITREE HARDWARE BLOCK DIAGRAM. It is not an invented diagram and not a component-level circuit schematic. No public PCB-level schematic, full wire harness pin-to-pin drawing or motor-power distribution circuit was found in the examined A2 pages/manual.
The OEM diagram separates motion-control and user-development computers, two Ethernet networks, USB hubs, external CAN/RS485 paths, LiDAR and multimedia modules. The source diagram is dated by CDN upload 2026/1/5; current interface text includes later details, so read the text with it.
- Motion control computer PC1: 8-core CPU, Ethernet 192.168.123.161 via Switch 1.
- User computer PC2: Intel Core i7, on both 192.168.123.162 and 192.168.124.162.
- Switch 1: 192.168.123.0/24 for DDS/control development. Switch 2: 192.168.124.0/24 for LiDAR point clouds. Official source says SDK development is on .123, not .124.
- Front LiDAR .124.20; rear LiDAR .124.21 optional (variant dependent).
- PC2 connects external CAN/RS485 through passthrough chips. PC1 connects multimedia camera/audio/lighting chain.
- Optional dock is a separate Orin NX computing accessory; it is NOT the Intel PC2 body computer. The official text says default on A2-Pro.
A simple diagram for this camera project can show both cameras self-powered/recording internally; adding robot power or control later is a separate verified integration step.

BODY ELECTRICAL PORTS (FROM CURRENT ABOUT A2 TABLE)
Port 1: front-left leg RS485/power, 58 V. Not a payload outlet.
Port 2: PC2 USB2 Type-C + DP, max 20 V 1 A.
Port 3: PC2 USB3 Type-C, current limit 1 A.
Ports 4/5: PC1 USB3 Type-C, each current limit 2 A.
Port 6: 8+2 aviation network Switch 2, .124 subnet, 1000BASE-T +12 V.
Port 7: 8+2 aviation network Switch 1, .123 subnet, 1000BASE-T +12 V.
Port 8: rear-left leg RS485/power, 58 V. Not a payload outlet.
Port 9: rear-right leg RS485/power, 58 V. Not a payload outlet.
Port 10: CAN +24 V, listed 5 A port limit.
Port 11: CAN +BAT, listed battery voltage 58 V, 10 A.
Port 12: RS485 +12 V, listed 6 A.
Port 13: RS485 +24 V, listed 6 A.
Port 14: front-right leg RS485/power, 58 V 10 A max. Not a payload outlet.
All 24 V-labeled ports share one supply with 6 A TOTAL limit. All 12 V-labeled ports share another with 6 A TOTAL limit. Honor individual limits as well. The OEM explicitly prohibits hot-swapping aviation connectors (distinct from the robot's hot-swappable battery feature).

PINOUT REFERENCE LIMITATIONS
- 2+2 power connector image plus table: pin1 Power-, black14AWG; pin2 485A, red24AWG; pin3 485B, black24AWG; pin4 Power+, white14AWG. The table labels RS485, so do not silently reuse 485A/B as CAN-H/L without the port-specific connector confirmation.
- 8+2 connector: pin1 Power-, pin10 Power+12 V; Ethernet pins2..9 described in about-a2-source.txt and original connector image. Use actual mating-face diagrams to resolve orientation. Two extra wire colors are unassigned in the source.
- E-stop source shows pins2 and4 as E-stop; source describes triggering when connected. No changes to E-stop circuits are proposed.
- V1/V2 dock ports have different limits from body ports, including 24 V 3 A individual outputs /5 A combined and 12 V 4.5 A individual network-power outputs /5 A combined. They are separately specified in the source. Do not transfer a body-port current rating to a dock port.

DESIGN HOLD POINTS BEFORE PRINTABLE CAD
1. Verify exact legged A2 revision and whether optional dock is fitted; identify V1 flat versus V2 raised-antenna top.
2. Confirm available rail length/entry, supplied nut thickness, screw engagement/clearance, and real mounting plane datum.
3. Measure or obtain allowable rail/dock loads and torque. No per-interface force or bending-moment rating is in these retrieved drawings.
4. Confirm camera/cage/quick-release/extension-stick masses and CG, then evaluate dynamic bending and tether retention.
5. Measure battery side-access envelope, sensor occlusion, cooling and limb swept volumes.
No adapter solid, STL, G-code, robot-setting change or electrical modification has been created or performed.
