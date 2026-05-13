#!/usr/bin/env python3
"""
Export Omi pocket cross-section for verification

Extracts the exact pocket profile from v1-charging-stand.py and exports
as DXF and additional verification formats.
"""

import sys
import math

def six_sided_diamond_points(width, height):
    """Return vertices of a six-sided diamond shape centered at origin."""
    top_facet_h = 15
    bottom_h = height - top_facet_h
    top_w = width * 0.6

    return [
        (-top_w / 2, height / 2),           # top-left
        (top_w / 2, height / 2),            # top-right
        (width / 2, top_facet_h / 2),       # right-upper
        (width / 2, -top_facet_h / 2),      # right-lower
        (0, -height / 2),                   # bottom point
        (-width / 2, -top_facet_h / 2),     # left-lower
        (-width / 2, top_facet_h / 2),      # left-upper
    ]

def export_simple_dxf(filename="omi_pocket_profile.dxf"):
    """Export simple DXF with pocket outline."""

    # Design parameters
    TOL = 0.5
    OMI_W = 41 + TOL * 2
    OMI_H = 40 + TOL * 2

    points = six_sided_diamond_points(OMI_W, OMI_H)

    # Simple DXF format
    dxf_content = f"""0
SECTION
2
ENTITIES
"""

    # Add polyline
    dxf_content += """0
LWPOLYLINE
8
POCKET_OUTLINE
62
1
70
1
"""

    # Number of vertices
    dxf_content += f"90\n{len(points)}\n"

    # Add vertices
    for x, y in points:
        dxf_content += f"10\n{x:.3f}\n20\n{y:.3f}\n"

    # Add pendant outline (dashed)
    pendant_points = six_sided_diamond_points(41, 40)
    dxf_content += """0
LWPOLYLINE
8
PENDANT_OUTLINE
62
5
70
1
"""
    dxf_content += f"90\n{len(pendant_points)}\n"

    for x, y in pendant_points:
        dxf_content += f"10\n{x:.3f}\n20\n{y:.3f}\n"

    dxf_content += """0
ENDSEC
0
EOF
"""

    with open(filename, 'w') as f:
        f.write(dxf_content)

    return filename

def export_gcode_outline(filename="omi_pocket_outline.gcode"):
    """Export G-code outline for CNC verification cut."""

    TOL = 0.5
    OMI_W = 41 + TOL * 2
    OMI_H = 40 + TOL * 2

    points = six_sided_diamond_points(OMI_W, OMI_H)

    gcode_content = f"""; Omi DevKit 2 Pocket Outline
; Dimensions: {OMI_W}mm x {OMI_H}mm
; Cut depth: 1mm for template verification

G90 ; Absolute positioning
G21 ; mm units
G17 ; XY plane
F1000 ; Feed rate

; Move to start position
G0 X{points[0][0]:.3f} Y{points[0][1]:.3f}
G0 Z0.5
G1 Z-1.0 ; Plunge

"""

    # Cut the outline
    for i, (x, y) in enumerate(points[1:] + [points[0]], 1):
        gcode_content += f"G1 X{x:.3f} Y{y:.3f} ; Point {i}\n"

    gcode_content += """
G0 Z5 ; Retract
G0 X0 Y0 ; Return to origin
M30 ; Program end
"""

    with open(filename, 'w') as f:
        f.write(gcode_content)

    return filename

def export_coordinates_csv(filename="omi_pocket_coordinates.csv"):
    """Export coordinates as CSV for CAD import."""

    TOL = 0.5
    OMI_W = 41 + TOL * 2
    OMI_H = 40 + TOL * 2

    pocket_points = six_sided_diamond_points(OMI_W, OMI_H)
    pendant_points = six_sided_diamond_points(41, 40)

    content = "Type,Point,X,Y,Description\n"

    labels = ["top-left", "top-right", "right-upper", "right-lower",
              "bottom point", "left-lower", "left-upper"]

    for i, ((px, py), label) in enumerate(zip(pocket_points, labels)):
        content += f"POCKET,{i+1},{px:.3f},{py:.3f},{label}\n"

    for i, ((px, py), label) in enumerate(zip(pendant_points, labels)):
        content += f"PENDANT,{i+1},{px:.3f},{py:.3f},{label}\n"

    with open(filename, 'w') as f:
        f.write(content)

    return filename

if __name__ == "__main__":
    print("Exporting Omi pocket verification files...")

    try:
        dxf_file = export_simple_dxf()
        print(f"✅ {dxf_file} - DXF for CAD import")
    except Exception as e:
        print(f"❌ DXF export failed: {e}")

    try:
        gcode_file = export_gcode_outline()
        print(f"✅ {gcode_file} - G-code for CNC template cut")
    except Exception as e:
        print(f"❌ G-code export failed: {e}")

    try:
        csv_file = export_coordinates_csv()
        print(f"✅ {csv_file} - CSV coordinates for CAD")
    except Exception as e:
        print(f"❌ CSV export failed: {e}")

    # Also try CadQuery export if available
    try:
        import cadquery as cq

        # Design parameters
        TOL = 0.5
        OMI_W = 41 + TOL * 2
        OMI_H = 40 + TOL * 2
        OMI_VERTEX_R = 3

        # Create the pocket shape
        points = six_sided_diamond_points(OMI_W, OMI_H)
        closed_points = points + [points[0]]

        pocket_2d = (
            cq.Workplane("XY")
            .polyline(closed_points)
            .close()
        )

        # Try to fillet (might fail, so wrap in try/except)
        try:
            pocket_2d = pocket_2d.edges().fillet(OMI_VERTEX_R)
        except:
            print("⚠️  Note: Vertex filleting skipped (edge geometry)")

        # Export as STEP and DXF using CadQuery
        pocket_2d.val().exportStep("omi_pocket_profile.step")
        pocket_2d.val().exportDxf("omi_pocket_cadquery.dxf")

        print(f"✅ omi_pocket_profile.step - STEP file from CadQuery")
        print(f"✅ omi_pocket_cadquery.dxf - DXF file from CadQuery")

    except ImportError:
        print("ℹ️  CadQuery not available - basic exports only")
    except Exception as e:
        print(f"❌ CadQuery export failed: {e}")

    print(f"\n📐 Verification files ready!")
    print(f"   Use DXF files in CAD software for precise verification")
    print(f"   Use G-code for CNC template cutting")
    print(f"   Use CSV for coordinate verification")