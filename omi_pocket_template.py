#!/usr/bin/env python3
"""
Omi DevKit 2 Pocket Verification Template Generator

Generates a printable SVG template at 1:1 scale so you can verify the
six-sided diamond pocket shape matches your actual pendant before 3D printing.

Usage:
  python3 omi_pocket_template.py

Output:
  - omi_pocket_template.svg (printable template)
  - omi_pocket_dimensions.txt (verification dimensions)
"""

import math

def six_sided_diamond_points(width, height):
    """Return vertices of a six-sided diamond shape centered at origin.

    Shape: Short top facet tapering to longer bottom point
    - width: maximum width across the middle
    - height: total height from top to bottom
    """
    # Six-sided diamond: top facet (15mm) + main body (30mm) = 40mm total
    top_facet_h = 15  # short top section height
    bottom_h = height - top_facet_h  # longer bottom section

    top_w = width * 0.6   # top facet is narrower

    return [
        (-top_w / 2, height / 2),           # top-left
        (top_w / 2, height / 2),            # top-right
        (width / 2, top_facet_h / 2),       # right-upper
        (width / 2, -top_facet_h / 2),      # right-lower
        (0, -height / 2),                   # bottom point
        (-width / 2, -top_facet_h / 2),     # left-lower
        (-width / 2, top_facet_h / 2),      # left-upper
    ]

def generate_svg_template(filename="omi_pocket_template.svg"):
    """Generate SVG template at 1:1 scale for physical verification."""

    # Design parameters (matching v1-charging-stand.py)
    TOL = 0.5
    OMI_W = 41 + TOL * 2  # 42mm with tolerance
    OMI_H = 40 + TOL * 2  # 41mm with tolerance
    OMI_THICK = 13
    OMI_VERTEX_R = 3

    # Get diamond points
    points = six_sided_diamond_points(OMI_W, OMI_H)

    # SVG setup (1mm = 1 SVG unit for 1:1 printing)
    margin = 20  # mm
    svg_w = OMI_W + margin * 2
    svg_h = OMI_H + margin * 2
    center_x = svg_w / 2
    center_y = svg_h / 2

    # Convert points to SVG coordinates (flip Y for SVG coordinate system)
    svg_points = []
    for x, y in points:
        svg_x = center_x + x
        svg_y = center_y - y  # flip Y
        svg_points.append(f"{svg_x:.2f},{svg_y:.2f}")

    svg_path = " ".join(svg_points)

    svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{svg_w}mm" height="{svg_h}mm" viewBox="0 0 {svg_w} {svg_h}"
     xmlns="http://www.w3.org/2000/svg">
  <title>Omi DevKit 2 Pocket Verification Template</title>
  <desc>Print at 100% scale (1:1) and cut out to test fit with actual pendant</desc>

  <!-- Grid lines every 5mm for reference -->
  <defs>
    <pattern id="grid" width="5" height="5" patternUnits="userSpaceOnUse">
      <path d="M 5 0 L 0 0 0 5" fill="none" stroke="#e0e0e0" stroke-width="0.2"/>
    </pattern>
  </defs>
  <rect width="100%" height="100%" fill="url(#grid)" />

  <!-- Pocket outline (with tolerance) -->
  <polygon points="{svg_path}"
           fill="none"
           stroke="#ff0000"
           stroke-width="1.5"
           stroke-linejoin="round"/>

  <!-- Pendant outline (actual size without tolerance) -->
  <g transform="translate({center_x}, {center_y})">
    <polygon points="{' '.join(f'{x:.2f},{-y:.2f}' for x, y in six_sided_diamond_points(41, 40))}"
             fill="none"
             stroke="#0000ff"
             stroke-width="1"
             stroke-dasharray="2,2"
             stroke-linejoin="round"/>
  </g>

  <!-- Center cross for alignment -->
  <g stroke="#666" stroke-width="0.5">
    <line x1="{center_x-5}" y1="{center_y}" x2="{center_x+5}" y2="{center_y}"/>
    <line x1="{center_x}" y1="{center_y-5}" x2="{center_x}" y2="{center_y+5}"/>
  </g>

  <!-- Dimension labels -->
  <g font-family="Arial, sans-serif" font-size="3" fill="#333">
    <text x="{center_x}" y="{margin/2}" text-anchor="middle">Omi DevKit 2 Pocket Template</text>
    <text x="{margin/2}" y="{center_y}" text-anchor="middle" transform="rotate(-90, {margin/2}, {center_y})">
      Height: {OMI_H:.0f}mm (with tolerance)
    </text>
    <text x="{center_x}" y="{svg_h - margin/4}" text-anchor="middle">
      Width: {OMI_W:.0f}mm (with tolerance)
    </text>
    <text x="{svg_w - margin/2}" y="{center_y + 15}" text-anchor="middle" font-size="2.5">
      Red: Pocket outline ({OMI_W:.0f}×{OMI_H:.0f}mm)
    </text>
    <text x="{svg_w - margin/2}" y="{center_y + 20}" text-anchor="middle" font-size="2.5">
      Blue dashed: Pendant (41×40mm)
    </text>
    <text x="{svg_w - margin/2}" y="{center_y + 25}" text-anchor="middle" font-size="2.5">
      Depth: {OMI_THICK}mm pendant + margin
    </text>
  </g>
</svg>"""

    with open(filename, 'w') as f:
        f.write(svg_content)

    return filename, OMI_W, OMI_H, OMI_THICK

def generate_dimensions_file(filename="omi_pocket_dimensions.txt"):
    """Generate text file with verification dimensions."""

    TOL = 0.5
    OMI_W = 41 + TOL * 2
    OMI_H = 40 + TOL * 2
    OMI_THICK = 13
    OMI_CRADLE_DEPTH = OMI_THICK + 2

    points = six_sided_diamond_points(OMI_W, OMI_H)

    content = f"""Omi DevKit 2 Pendant Pocket - Verification Dimensions
====================================================

MEASURED PENDANT (actual device):
  Width:  41.0mm (across widest point)
  Height: 40.0mm (top to bottom)
  Thickness: 13.0mm

POCKET DIMENSIONS (with {TOL*2:.1f}mm print tolerance):
  Width:  {OMI_W:.1f}mm
  Height: {OMI_H:.1f}mm
  Depth:  {OMI_CRADLE_DEPTH:.1f}mm ({OMI_THICK}mm pendant + 2mm margin)

SIX-SIDED DIAMOND VERTICES (mm, from center):
"""

    for i, (x, y) in enumerate(points):
        labels = ["top-left", "top-right", "right-upper", "right-lower",
                  "bottom point", "left-lower", "left-upper"]
        content += f"  {i+1}. ({x:6.1f}, {y:6.1f})  # {labels[i]}\n"

    # Calculate key measurements for verification
    max_width = max(abs(p[0]) for p in points) * 2
    max_height = max(abs(p[1]) for p in points) * 2
    top_width = abs(points[0][0] - points[1][0])  # top facet width

    content += f"""
VERIFICATION MEASUREMENTS:
  Maximum width:    {max_width:.1f}mm (should match {OMI_W:.1f}mm)
  Maximum height:   {max_height:.1f}mm (should match {OMI_H:.1f}mm)
  Top facet width:  {top_width:.1f}mm (narrow top section)
  Top facet height: 15.0mm (from measurement notes)
  Bottom height:    25.0mm (40mm total - 15mm top)

PRINT VERIFICATION:
1. Print omi_pocket_template.svg at 100% scale (NO SCALING)
2. Cut out the RED outline carefully
3. Test fit your Omi pendant through the cutout
4. Pendant should pass through with slight clearance
5. If too tight/loose, adjust TOL parameter in v1-charging-stand.py

SHAPE VERIFICATION:
- Six-sided diamond (NOT triangle or circle)
- Short top facet tapering to longer bottom point
- Blue dashed line shows pendant outline (41×40mm)
- Red solid line shows pocket outline (with tolerance)
"""

    with open(filename, 'w') as f:
        f.write(content)

    return filename

if __name__ == "__main__":
    print("Generating Omi DevKit 2 pocket verification templates...")

    svg_file, width, height, thickness = generate_svg_template()
    txt_file = generate_dimensions_file()

    print(f"\n✅ Generated verification templates:")
    print(f"   📄 {svg_file} - Print at 100% scale and cut out")
    print(f"   📄 {txt_file} - Dimensions and verification steps")
    print(f"\n🔍 Pocket dimensions: {width:.0f}×{height:.0f}×{thickness+2:.0f}mm")
    print(f"   (pendant: 41×40×{thickness}mm + tolerance)")

    print(f"\n📋 To verify fit:")
    print(f"   1. Print {svg_file} at 100% scale (1:1)")
    print(f"   2. Cut out the RED outline carefully")
    print(f"   3. Test if your Omi pendant fits through with slight clearance")
    print(f"   4. Check that the shape matches the pendant's silhouette")