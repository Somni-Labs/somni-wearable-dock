#!/usr/bin/env python3
"""
Export STL files from v1-charging-stand.py for 3D printing

Exports both the bottom tray and top tray as separate STL files
ready for slicing and printing.
"""

import sys
import os
from pathlib import Path

def export_stl_files():
    """Export STL files using CadQuery standalone export."""

    try:
        import cadquery as cq
        print("✅ CadQuery available - proceeding with STL export")
    except ImportError:
        print("❌ CadQuery not available. Install with: pip install cadquery")
        return False

    # Import the design functions directly from the main file
    sys.path.insert(0, str(Path(__file__).parent / "designs"))

    try:
        # Read and modify the design file to remove cq_server dependency
        with open("designs/v1-charging-stand.py", 'r') as f:
            design_code = f.read()

        # Remove the cq_server import line and show_object calls
        design_code = design_code.replace("from cq_server.ui import ui, show_object", "# cq_server not available")
        design_code = design_code.replace('show_object(bottom_tray, name="bottom_tray",\n            options={"color": (0.15, 0.15, 0.17, 0.9)})', "# show_object removed")
        design_code = design_code.replace('show_object(top_tray, name="top_tray",\n            options={"color": (0.2, 0.2, 0.22, 0.95)})', "# show_object removed")

        # Execute the modified design file code
        exec_globals = {}
        exec(design_code, exec_globals)

        # Get the built objects
        bottom_tray = exec_globals['bottom_tray']
        top_tray = exec_globals['top_tray']

        print("✅ Design objects loaded successfully")

    except Exception as e:
        print(f"❌ Failed to load design: {e}")
        return False

    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    try:
        # Export bottom tray
        bottom_stl_path = output_dir / "v1-charging-stand-bottom-tray.stl"
        cq.exporters.export(bottom_tray, str(bottom_stl_path))
        print(f"✅ {bottom_stl_path} - Bottom tray (cable management)")

        # Export top tray
        top_stl_path = output_dir / "v1-charging-stand-top-tray.stl"
        cq.exporters.export(top_tray, str(top_stl_path))
        print(f"✅ {top_stl_path} - Top tray (device pockets + Mudra pole)")

        # Also export as STEP files for CAD verification
        bottom_step_path = output_dir / "v1-charging-stand-bottom-tray.step"
        cq.exporters.export(bottom_tray, str(bottom_step_path))
        print(f"✅ {bottom_step_path} - Bottom tray STEP (CAD)")

        top_step_path = output_dir / "v1-charging-stand-top-tray.step"
        cq.exporters.export(top_tray, str(top_step_path))
        print(f"✅ {top_step_path} - Top tray STEP (CAD)")

        return True

    except Exception as e:
        print(f"❌ STL export failed: {e}")
        return False

def print_print_info():
    """Print 3D printing information."""
    print(f"\n🖨️  3D PRINTING INFO:")
    print(f"   Material: PETG recommended (good strength + heat resistance)")
    print(f"   Layer height: 0.2mm (0.15mm for finer details)")
    print(f"   Infill: 15-20% (functional print, not decorative)")
    print(f"   Supports: Likely needed for Mudra pole overhang")
    print(f"   Build plate: Fits QIDI Q2 (245×255mm) - verify in slicer")
    print(f"   Print orientation: Bottom tray down, top tray upside down")
    print(f"")
    print(f"🔧 MUDRA LINK TEST FIT:")
    print(f"   Updated charger pocket dimensions:")
    print(f"   • Width: 12mm (+1mm tolerance) = 13mm pocket")
    print(f"   • Length: 30mm (+1mm tolerance) = 31mm pocket")
    print(f"   • Height: 8mm (+0.5mm tolerance) = 8.5mm pocket")
    print(f"   ")
    print(f"   Test with actual device:")
    print(f"   • Charger should drop flush into shelf pocket")
    print(f"   • Band should drape smoothly over L-pole")
    print(f"   • Cable should route cleanly through pole cavity")
    print(f"   • 69mm clearance below shelf for hanging band")

if __name__ == "__main__":
    print("Exporting v1-charging-stand STL files for 3D printing...")

    success = export_stl_files()

    if success:
        print_print_info()
        print(f"\n🎯 Ready for 3D printing and Mudra Link device testing!")
    else:
        print(f"\n❌ Export failed. Check error messages above.")
        sys.exit(1)