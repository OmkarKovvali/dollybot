SONY FE PZ 16–35 MM F4 G — SELP1635G

Specific lens identified by the user; supersedes the earlier 18–50 mm description. Only product model information is retained.

OUTPUTS
../../dist/assets/sony-selp1635g.glb — colored reference model
../../dist/assets/sony-selp1635g.stl — same geometry, material-free fallback
../../dist/assets/sony-selp1635g.json — dimensions, fit metric, sources, hashes
build_lens.py and sony-selp1635g.blend — editable source
previews/ — three studio views
export-validation.json — export and independent STL clipping checks

OFFICIAL SPECS
Maximum diameter80.5 mm; nominal length88.1 mm; mass353 g; 72 mm filter; Sony E mount; 16–35 mm; constant maximum f/4. Sony states lens length stays constant while focusing and zooming.
https://www.sony.com/electronics/support/lenses-e-mount-lenses/selp1635g/specifications
https://www.sony-asia.com/lenses/products/selp1635g/feature1
Official photographs saved under references; exact URLs are in the model metadata.

MODEL CONVENTION
Millimeters, Z-up, optical axis -X. Rear flange placement datum is(0,0,0). Length runs toX=-88.1; radial envelope reaches40.25. The GLB deliberately uses the existing viewer's mm/Z-up convention, so load at identity scale and rotation. Attach to the camera body's estimated flange origin[-24.7245252,0,35.8604118] mm before applying the camera pose. No hood or lens caps are installed. Rear bayonet protrusions and mechanical engagement details are omitted.

The official 88.1 mm dimension establishes the nominal flange-to-front envelope used here. Exterior axial profile stations, ring widths, controls, optics appearance and labels are visually reconstructed from official photographs. This is not manufacturer CAD, a scan, a real lens optical prescription, or tolerance-controlled fit geometry. The Sony body's tripod XY is still unverified.

CLEARANCE RESULT
The lens reaches4.3896 mm below the body's nominal bottom plane at its widest ring. Triangle clipping (including edge intersections) at lens-localZ=-35.8604118 yields maximumX=-20.7766571 mm among all parts below the cover top. At proposed camera holeX=-112, the body flangeX=-24.7245252 gives maximumworldX=-157.5011823. The cover's minimumX=-150.3394 therefore leaves conservative7.1618 mm forward clearance for this reference geometry. This mathematical separation is not a physical fit guarantee; measure actual mounting datum and lens before printing.

QA
Checked front and control-side renders against Sony images; rings, rocker, focus button, aperture controls and rear taper are recognizable. Verified GLB header, embedded buffers/no decoder requirement, published envelope, file hashes, and independent clipping from exported STL. Original Sony ZV-E1 body GLB hash remains unchanged. Body+identified lens nominal mass is836 g before hood/filter/cage/mount.
