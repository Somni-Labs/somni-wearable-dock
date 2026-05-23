# Separate iPad Back Wall Insert

**Date:** 2026-05-23
**Status:** Approved
**Trigger:** Top tray print cancelled after 10 hours — the 60mm iPad back wall makes the flipped top tray ~77mm tall, consuming massive print time for a simple vertical wall

## Problem

The iPad back wall (`IPAD_BACK_H = 60mm`) is unioned directly onto the top tray. When the top tray is flipped for printing (pocket surface face-down), the wall becomes the tallest feature — 60mm of vertical wall printed first, before the actual tray body even begins. This makes the top tray ~77mm tall on the build plate, adding hours of print time for geometry that is structurally just a flat slab.

## Solution

Extract the iPad back wall into a separate slide-in piece, using tongue-and-groove rails — the same pattern already used for the iPad cover plate. The wall prints flat on its back (4mm tall, ~15 minutes) and slides into the top tray from the side.

### 1. Top Tray Modifications (`build_top_tray()`)

**Remove:** The `ipad_back` union block — the 60mm tall back wall currently built at `Z = STAND_H`, centered at `Y = STAND_D/2 - IPAD_BACK_THICK/2`, width `IPAD_SLOT_W + 10`, thickness `IPAD_BACK_THICK` (4mm).

**Keep:** The front lip (`ipad_lip`) remains on the top tray — 5mm tall, provides iPad retention even without the wall installed.

**Add:** A tongue-and-groove rail along the rear edge of the top tray top surface where the wall base sits.

**Rail groove dimensions:**
- Position: top surface of tray at the rear edge, centered on `Y = STAND_D/2 - IPAD_BACK_THICK/2` (same Y as the old wall)
- Groove width (X): `IPAD_SLOT_W + 10 + 2` (full wall width + exits both sides for slide-in)
- Groove depth (Y): 3mm (into the tray surface)
- Groove height (Z): 3mm (cut down from the top surface)
- Open on both left and right sides — wall slides in from either end
- The groove cut must happen AFTER the `base.edges(">Z").fillet(1.2)` call in `build_top_tray()`, or the fillet will round the groove edges. Alternatively, cut the groove before filleting and ensure the fillet selector excludes groove edges. Simplest: cut the groove after all fillets.

### 2. New `build_ipad_wall()` Function

A standalone flat slab with a tongue tab on its bottom edge.

**Wall body:**
- Width (X): `IPAD_SLOT_W + 10` (same as current — 245mm)
- Height (Z): `IPAD_BACK_H` (60mm)
- Thickness (Y): `IPAD_BACK_THICK` (4mm)
- Built at origin, centered on X, Z=0 at the bottom edge

**Tongue tab:**
- Runs the full width of the wall along the bottom edge
- Tongue depth (Y): 3mm - IPAD_WALL_TOL (= 2.6mm, extends beyond the wall's back face, into the groove)
- Tongue height (Z): 3mm - IPAD_WALL_TOL (= 2.6mm, matches groove height minus clearance)
- Centered on the wall thickness

**Print orientation:** Flat on its back — the 245mm x 60mm face sits on the build plate, making the print only 4mm tall. No rotation needed in the export script.

### 3. Rail Tolerances

Same as the iPad cover plate rails:
- Groove: nominal 3mm deep x 3mm tall
- Tongue: 3mm - IPAD_WALL_TOL deep x 3mm - IPAD_WALL_TOL tall (IPAD_WALL_TOL = 0.4mm, so 2.6mm x 2.6mm)
- This provides 0.2mm clearance per side for a snug slide fit

The global `TOL = 1.0mm` is tuned for device pocket drop-in fit and is too generous for a structural slide joint — it would leave 1mm of slop and wobble. Use a dedicated `IPAD_WALL_TOL = 0.4` constant for the tongue-and-groove fit, giving 0.4mm clearance per side (snug slide, minimal wobble).

### 4. Export Script Updates (`export_charging_stand.py`)

Add iPad wall export:
- `output/v1-charging-stand-ipad-wall.stl` — no rotation needed (prints flat as-built)
- `output/v1-charging-stand-ipad-wall.step` — assembly position for CAD review
- Translate so Z_min = 0 (same as other parts)

Update `exec_globals` to extract the new `ipad_wall` variable.

### 5. cadquery-server Preview

Add `show_object()` call for the iPad wall at its assembly position:
- Translate to `(0, STAND_D/2 - IPAD_BACK_THICK/2, STAND_H)` — same position the old union wall occupied
- Color matching top tray or slightly lighter for visibility

### 6. Ghost Visualization

No ghost needed — the wall is a visible structural part, not an internal component.

### 7. CLAUDE.md Updates

Add to the architecture section:
- iPad wall is now a 5th printable part (bottom tray, top tray, mudra pole, iPad cover plate, iPad wall)

Add to lessons learned:
- Tall vertical walls should be separate parts printed flat, not unioned onto trays that get flipped

## Parts Summary

| Part | Print Orientation | Height on Plate | Estimated Time |
|------|-------------------|-----------------|----------------|
| iPad back wall (NEW) | Flat (wide face down) | 4mm | ~15 min |
| Top tray (MODIFIED) | Flipped (pockets down) | ~17mm (was ~77mm) | ~4-6h (was 10h+) |

## Files Changed

| File | Change |
|------|--------|
| `designs/v1-charging-stand.py` | Remove wall union from `build_top_tray()`, add groove rail, add `build_ipad_wall()`, add `show_object()` call, add `IPAD_WALL_TOL` constant |
| `export_charging_stand.py` | Add iPad wall STL/STEP export |
| `CLAUDE.md` | Update architecture (5 parts), add lesson learned |

## Assembly

1. Print top tray (flipped, ~17mm tall)
2. Print iPad wall (flat, ~4mm tall)
3. Slide iPad wall into rear groove from left or right side
4. iPad leans against wall, front lip prevents forward slide
