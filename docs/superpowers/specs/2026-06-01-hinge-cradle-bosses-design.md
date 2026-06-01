# Hinge Cradle Bosses for Device Tray

**Date:** 2026-06-01  
**Status:** Approved

## Problem

The tilt plate hinge barrel sockets in `build_device_tray()` are 3.6mm cylindrical cuts positioned at the pocket edge (Y = pocket front face). The pocket cut already removed material from that Y inward, so the sockets only create a ~1.8mm-deep half-pipe scallop in the pocket wall — invisible on a 0.3mm layer-height FDM print and non-functional as a hinge cradle.

The cable notch forward of each pocket further erodes the wall at the same Z range as the sockets, making the problem worse.

## Solution

Replace the cylindrical socket cuts with **raised U-channel cradle bosses** — solid rectangular blocks unioned onto the pocket's front interior wall, with a semicircular channel cut into the top for the hinge barrel to drop into from above.

## Dimensions

### Boss Body
- **Width (X):** `HINGE_BARREL_L + 1.0` = 9.0mm (0.5mm wall each side of 8mm barrel)
- **Depth (Y):** 2.5mm (protrudes into pocket from front wall face)
- **Height (Z):** `HINGE_BARREL_OD + 1.5` = 4.5mm (barrel diameter + 1.5mm retention wall above)

### U-Channel
- **Radius:** `(HINGE_BARREL_OD + HINGE_SOCKET_TOL * 2) / 2` = 1.8mm
- **Open top** — barrel drops in from above
- **Axis:** parallel to X (same as barrel axis)
- **Length:** full boss width (9mm)

### Positioning Per Pocket
- **Y:** pocket front interior wall face (`pocket_center_y - pocket_size/2`), boss extends +Y into the pocket by 2.5mm
- **Z:** bottom of boss at pocket floor level (`STAND_H - CRADLE_DEPTH`), channel center at `pocket_floor + HINGE_BARREL_OD/2 + 0.5`
- **X:** same barrel spacing as existing tilt plates:
  - UH: 20mm apart (±10mm from pocket center X)
  - R1: 8mm apart (±4mm from pocket center X)
  - Omi: 8mm apart (±4mm from pocket center X)

## Assembly

1. Drop tilt plate into pocket — barrels facing front (-Y)
2. Barrels settle into U-channels by gravity
3. Push rod T-head engages captured slot on tilt plate underside
4. Push rod keeps tilt plate seated; U-channel walls prevent barrel pop-out during tilt

## What Changes

- `build_device_tray()`: Remove 6 cylindrical barrel socket cuts, add 6 U-channel cradle boss unions + channel cuts
- Add new constants: `HINGE_BOSS_DEPTH`, `HINGE_BOSS_H`, `HINGE_BOSS_W`
- Re-export device tray STL
- Re-slice device tray

## What Doesn't Change

- Tilt plates (barrel geometry unchanged)
- Push rods
- Top tray
- Bottom tray
- Any other part
