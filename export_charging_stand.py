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
        import re
        design_code = re.sub(r'show_object\(.*?\)', '# show_object removed', design_code, flags=re.DOTALL)

        # Execute the modified design file code
        exec_globals = {}
        exec(design_code, exec_globals)

        # Get the built objects
        bottom_tray = exec_globals['bottom_tray']
        top_tray = exec_globals['top_tray']
        ipad_cover = exec_globals.get('ipad_cover')
        mudra_pole = exec_globals.get('mudra_pole')
        uh_tilt_plate = exec_globals.get('uh_tilt_plate')
        r1_tilt_plate = exec_globals.get('r1_tilt_plate')
        omi_tilt_plate = exec_globals.get('omi_tilt_plate')
        push_rods = exec_globals.get('push_rods', {})

        print("✅ Design objects loaded successfully")

    except Exception as e:
        print(f"❌ Failed to load design: {e}")
        return False

    # ── Translate parts to build plate (Z=0) for slicer-ready STLs ──────
    # The bottom tray already starts at Z=0, but translate for safety.
    # The top tray starts at Z=SPLIT_Z (40mm) in the assembly — move it
    # down so its lowest face sits on the build plate.
    # For STL export the top tray is also flipped upside-down (rotated 180°
    # around X) so the flat pocket surface faces down on the build plate,
    # giving the best print quality on the device-facing surfaces.
    SPLIT_Z = exec_globals['SPLIT_Z']

    bottom_bb = bottom_tray.val().BoundingBox()
    bottom_print = bottom_tray.translate((0, 0, -bottom_bb.zmin))

    top_bb = top_tray.val().BoundingBox()
    # Flip upside-down: rotate 180° around X, then shift so Z_min = 0
    top_flipped = top_tray.rotate((0, 0, 0), (1, 0, 0), 180)
    top_flipped_bb = top_flipped.val().BoundingBox()
    top_print = top_flipped.translate((0, 0, -top_flipped_bb.zmin))

    # iPad cover plate — translate to Z=0 for printing
    if ipad_cover:
        cover_bb = ipad_cover.val().BoundingBox()
        cover_print = ipad_cover.translate((0, 0, -cover_bb.zmin))

    # Mudra pole — rotate 90° to print on its side (back face down).
    # Printing upright puts thin snap clips on the build plate where brim
    # removal tears them off. On its side, the wide back face (22mm x 85mm)
    # sits on the plate and clips print horizontally (strongest orientation).
    if mudra_pole:
        pole_rotated = mudra_pole.rotate((0, 0, 0), (1, 0, 0), -90)
        pole_rot_bb = pole_rotated.val().BoundingBox()
        pole_print = pole_rotated.translate((0, 0, -pole_rot_bb.zmin))

    # Tilt plates — already at origin, just ensure Z_min = 0
    tilt_plates_print = {}
    for name, plate_var in [("uh", uh_tilt_plate), ("r1", r1_tilt_plate), ("omi", omi_tilt_plate)]:
        if plate_var:
            plate_bb = plate_var.val().BoundingBox()
            tilt_plates_print[name] = plate_var.translate((0, 0, -plate_bb.zmin))
            print(f"   Tilt plate ({name}): translated Z by {-plate_bb.zmin:+.1f}mm")

    # Push rods — already at origin, ensure Z_min = 0
    push_rods_print = {}
    for name, rod in push_rods.items():
        if rod:
            rod_bb = rod.val().BoundingBox()
            push_rods_print[name] = rod.translate((0, 0, -rod_bb.zmin))
            print(f"   Push rod ({name}): translated Z by {-rod_bb.zmin:+.1f}mm")

    print(f"   Bottom tray: translated Z by {-bottom_bb.zmin:+.1f}mm (was Z={bottom_bb.zmin:.1f})")
    print(f"   Top tray: flipped upside-down + translated Z by {-top_flipped_bb.zmin:+.1f}mm (was Z={top_bb.zmin:.1f}–{top_bb.zmax:.1f})")
    if ipad_cover:
        print(f"   iPad cover: translated Z by {-cover_bb.zmin:+.1f}mm (was Z={cover_bb.zmin:.1f})")
    if mudra_pole:
        print(f"   Mudra pole: rotated 90° (on side) + translated Z by {-pole_rot_bb.zmin:+.1f}mm")

    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    try:
        # Export bottom tray (slicer-ready: Z starts at 0)
        bottom_stl_path = output_dir / "v1-charging-stand-bottom-tray.stl"
        cq.exporters.export(bottom_print, str(bottom_stl_path))
        print(f"✅ {bottom_stl_path} - Bottom tray (cable management)")

        # Export top tray (slicer-ready: flipped + Z starts at 0)
        top_stl_path = output_dir / "v1-charging-stand-top-tray.stl"
        cq.exporters.export(top_print, str(top_stl_path))
        print(f"✅ {top_stl_path} - Top tray (flipped for printing)")

        # STEP files keep original assembly positions (for CAD review)
        bottom_step_path = output_dir / "v1-charging-stand-bottom-tray.step"
        cq.exporters.export(bottom_tray, str(bottom_step_path))
        print(f"✅ {bottom_step_path} - Bottom tray STEP (assembly position)")

        top_step_path = output_dir / "v1-charging-stand-top-tray.step"
        cq.exporters.export(top_tray, str(top_step_path))
        print(f"✅ {top_step_path} - Top tray STEP (assembly position)")

        # iPad cover plate
        if ipad_cover:
            cover_stl_path = output_dir / "v1-charging-stand-ipad-cover.stl"
            cq.exporters.export(cover_print, str(cover_stl_path))
            print(f"✅ {cover_stl_path} - iPad cover plate")

            cover_step_path = output_dir / "v1-charging-stand-ipad-cover.step"
            cq.exporters.export(ipad_cover, str(cover_step_path))
            print(f"✅ {cover_step_path} - iPad cover STEP (assembly position)")

        # Mudra pole — snap-in part (no rotation, prints upright)
        if mudra_pole:
            pole_stl_path = output_dir / "v1-charging-stand-mudra-pole.stl"
            cq.exporters.export(pole_print, str(pole_stl_path))
            print(f"✅ {pole_stl_path} - Mudra pole (snap-in, prints upright)")

            pole_step_path = output_dir / "v1-charging-stand-mudra-pole.step"
            cq.exporters.export(mudra_pole, str(pole_step_path))
            print(f"✅ {pole_step_path} - Mudra pole STEP (origin position)")

        # Tilt plates
        for name, plate_print in tilt_plates_print.items():
            plate_stl = output_dir / f"v1-charging-stand-tilt-plate-{name}.stl"
            cq.exporters.export(plate_print, str(plate_stl))
            print(f"✅ {plate_stl} - Tilt plate ({name})")

            plate_step = output_dir / f"v1-charging-stand-tilt-plate-{name}.step"
            plate_orig = {"uh": uh_tilt_plate, "r1": r1_tilt_plate, "omi": omi_tilt_plate}[name]
            cq.exporters.export(plate_orig, str(plate_step))
            print(f"✅ {plate_step} - Tilt plate ({name}) STEP")

        # Push rods
        for name, rod_print in push_rods_print.items():
            rod_stl = output_dir / f"v1-charging-stand-push-rod-{name}.stl"
            cq.exporters.export(rod_print, str(rod_stl))
            print(f"✅ {rod_stl} - Push rod ({name})")

            rod_step = output_dir / f"v1-charging-stand-push-rod-{name}.step"
            cq.exporters.export(push_rods[name], str(rod_step))
            print(f"✅ {rod_step} - Push rod ({name}) STEP")

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
    print(f"   Supports: Top tray and mudra pole need NO supports (pole prints upright)")
    print(f"   Build plate: Fits QIDI Q2 (245×255mm) - verify in slicer")
    print(f"   Print orientation: Bottom tray down, top tray upside down, mudra pole on side")
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