# Removable Device Tray

Separate the four front-row wearable device pockets (UH Ring, R1 Ring, Omi pendant, Mudra pole socket) from the top tray body into a standalone drop-in tray. The tray prints right-side up with no supports and drops into a rectangular cutout in the top tray.

## Motivation

The top tray currently contains all four front-row device pockets molded directly into its body. When printed flipped (required because the top tray sits on the bottom tray), these pockets create deep overhangs that require heavy support material, long print times, and risk spaghetti failures. Separating the device zone into its own tray eliminates these problems:

- Device tray prints right-side up -- zero supports
- Top tray flipped print becomes much simpler (single rectangular cutout instead of four complex pockets)
- Device tray can be reprinted independently if devices change
- Faster iteration on pocket geometry without reprinting the entire top tray

## Assembly

6 parts total (was 5):

1. Bottom tray
2. Top tray (with rectangular device tray cutout)
3. **Device tray (new)** -- drops into top tray cutout
4. Mudra pole -- snaps into device tray (was top tray)
5. iPad cover plate
6. iPad back wall

## Device Tray Geometry

### Footprint

The tray spans all four front-row devices:

- **X span**: UH left edge (X = -102) to Mudra shelf right tip (X = +109), plus WALL (2.5mm) on each side = **~220mm wide**
- **Y span**: Front wall inner face (Y = -85) to rear edge of deepest pocket plus margin = **~55mm deep**
- **Z height**: 15mm (from Z = 43 to Z = 58, i.e., SPLIT_Z + LID_FLOOR to STAND_H)

Exact dimensions will be computed from the existing SLOT_POSITIONS, device pocket sizes, and Mudra shelf extent during implementation. The values above are estimates for planning.

### Contents (moved from top tray)

Everything device-specific moves to the device tray:

- **UH Ring pocket** -- square cutout (41x41mm), rounded corners, USB-C front wall notch, floor cable hole, hinge barrel sockets
- **R1 Ring pocket** -- circular cutout (32mm dia), USB-C front wall notch, floor cable hole, hinge barrel sockets
- **Omi pocket** -- six-sided diamond cutout, USB-C front-left notch, floor cable hole, hinge barrel sockets
- **Mudra pole socket** -- rectangular through-hole (20.6x22.6mm) with snap engagement pockets on underside, cable pass-through
- **Push rod slots** -- 4x rectangular through-holes at SERVO_Y for servo actuators
- **Cable pass-through holes** -- USB-C sized holes through tray floor for each device

### Front wall interface

The device tray's front edge butts against the inner face of the top tray's front wall. Cable exit notches in the tray's front edge align with matching slots in the top tray wall, creating a continuous cable path:

```
device pocket --> tray front notch --> top tray front wall slot --> exterior
```

The front wall cable slots for UH, R1, and Omi remain in the top tray's front wall. The device tray has matching open notches on its front edge.

## Top Tray Modifications

### Rectangular cutout

A single rectangular opening replaces all four device pockets. Sized to match the device tray outer dimensions plus 0.3mm clearance per side (SNAP_TOL).

### Perimeter ledge (3-sided)

A 2.5mm wide ledge (WALL thickness) around the cutout at Z = SPLIT_Z + LID_FLOOR (Z = 43). The ledge runs on three sides:

- **Left**: cutout wall
- **Right**: cutout wall  
- **Rear**: cutout wall

The **front side has no ledge** -- the top tray's front wall acts as containment. The tray's front edge sits flush against the wall's inner face.

### Removed geometry

All device pocket cuts, hinge barrel sockets, push rod slots (in the device zone), Mudra socket, and Mudra snap pockets are removed from `build_top_tray()`. The LID_FLOOR remains but gets the device tray cutout instead of individual through-holes for the front-row devices.

### Retained geometry

- Outer shell and walls (including front wall with backlit logo)
- Snap-fit clips for bottom-to-top tray connection
- G2 glasses case pocket (rear row)
- iPad channel, tunnel, blade slot, cover plate rails, front lip
- AC cable pass-through (left wall)
- Spare USB exit (back wall)
- Front wall cable slots (UH, R1, Omi USB-C exits)
- LID_FLOOR (with device tray cutout)
- G2 cable hole, G2 LCD window, iPad cable hole, iPad blade slot re-cuts

## Retention Mechanism

**Drop-in friction fit** -- no clips, no fasteners.

- 0.3mm clearance per side (SNAP_TOL) between tray walls and cutout walls
- Gravity holds the tray down on the ledge
- Front wall contains the tray in -Y
- Cutout walls contain in +/-X and +Y
- Top surface flush at Z = STAND_H (58mm)

If the fit is too loose in practice, small detent bumps (like the iPad wall's IPAD_DETENT_H = 0.6mm) can be added later.

### Mudra pole snap engagement

The Mudra pole's snap hooks currently engage pockets cut into the underside of the top tray at Z = SPLIT_Z - 3mm. With the device tray, the pole snaps into the tray instead. The snap engagement pockets move to the device tray's underside. Since the tray floor is at Z = 43 (DTRAY_FLOOR_Z), the pockets cut upward into the tray body from below. The tray has 15mm of material -- more than enough for the 3mm pocket depth. The cutout ledge in the top tray must have a matching clearance notch so the snap hooks don't collide with the ledge when the tray drops in.

## Printing

### Device tray

- Prints **right-side up** (flat floor on build plate, pockets facing up)
- **No supports needed** -- all pockets are open-top
- **No brim needed** -- solid rectangular base, good adhesion
- Estimated height: 15mm
- Fast print, simple geometry

### Top tray (modified)

- Still prints **flipped** (Z=58 on build plate)
- Dramatically simpler -- one rectangular cutout replaces four complex pocket overhangs
- Support material drops significantly (only G2 pocket + iPad channel overhangs remain)
- Shorter print time

## Export and Slicing

### New function

`build_device_tray()` in `designs/v1-charging-stand.py` -- builds the tray at its assembly position (Z = 43 to Z = 58), exported translated down to Z = 0 for printing.

### Export script

`export_charging_stand.py` gets a new entry:
- `v1-charging-stand-device-tray.stl` / `.step`
- Translated to Z = 0, no flip needed

### Slicer job

New `k8s/slice-device-tray.yaml`:
- No supports, no brim
- 70C bed, 215/220C extruder
- Fan off first 3 layers, 80% max
- sed guard for M106 S255 -> S204
- No support validation check (supports not needed)

### Ghost visualization

The device tray should be included in `build_ghost_components()` or shown as a distinct object in cadquery-server preview for assembly visualization.

## Constants

New constants to add:

```python
# --- Removable device tray ---
DTRAY_TOL = SNAP_TOL          # 0.3mm clearance per side
DTRAY_LEDGE = WALL            # 2.5mm ledge width
DTRAY_FLOOR_Z = SPLIT_Z + LID_FLOOR  # 43mm -- bottom of device tray
```

Width and depth computed dynamically from SLOT_POSITIONS and device dimensions.
