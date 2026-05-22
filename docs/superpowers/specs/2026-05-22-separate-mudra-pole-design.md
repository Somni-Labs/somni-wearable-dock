# Separate Mudra Pole Insert

**Date**: 2026-05-22
**Status**: Approved
**Trigger**: Top tray print time jumped from 16h to 37h because support material (48% of filament) is needed for the Mudra shelf overhang when printed flipped

## Problem

The top tray includes the Mudra L-pole (85mm vertical post + 36mm horizontal shelf). When printed flipped (as required for pocket surface quality), the shelf becomes a 36mm horizontal overhang requiring heavy support material — 110 meters of filament and 20+ extra hours of print time. The shelf only supports a light silicone wristband, so the support material is disproportionate to the structural need.

## Solution

Separate the Mudra pole into its own printable part that inserts into a socket on the top tray via snap clips.

### 1. Mudra Pole (new separate part)

The L-pole becomes a standalone piece printed **upright** — no supports needed.

**Geometry (unchanged from current design):**
- Vertical post: `MUDRA_POLE_D` (20mm) x `MUDRA_POLE_W` (22mm) x `MUDRA_POLE_H` (85mm)
- Horizontal shelf: `MUDRA_SHELF_L` (36mm) x `MUDRA_POLE_W` (22mm) x `MUDRA_SHELF_H` (14mm)
- Flush charger pocket in shelf top (open from above, chamfered lip)
- Internal cable channel: vertical cavity through post + horizontal slot connecting to charger bay
- Cable exits through the open bottom face of the pole base

**New: snap clip tabs on the pole base.**
Two cantilever hooks, one on each long side (the 20mm / X-axis faces):
- Hook overhang: `SNAP_HOOK` (1.2mm) — catches underside of top tray floor
- Cantilever height: `SNAP_CLIP_H` (8mm) — enough flex to insert and lock
- Clip width: `SNAP_CLIP_W` (12mm) — centered on each face
- Tolerance: `SNAP_TOL` (0.3mm) per side

The clips extend downward from the pole base. When inserting the pole into the socket, the hooks flex inward, pass through the socket, and snap out to catch the bottom face of the top tray.

**Print orientation:** Upright at Z=0, no rotation. The shelf prints as a horizontal extension off the top of the vertical post — trivial overhang for the slicer since it builds up layer by layer.

### 2. Top Tray Socket (modification)

Replace the built-in pole with a rectangular through-socket.

**Socket dimensions:**
- Width: `MUDRA_POLE_D + SNAP_TOL * 2` (20.6mm in X)
- Depth: `MUDRA_POLE_W + SNAP_TOL * 2` (22.6mm in Y)
- Height: Full tray thickness (`TOP_H` = 17mm) — through-hole

**Snap engagement pockets:**
Small recesses on the bottom face of the top tray around the socket, one on each long side (X-axis faces). These give the snap hooks room to spring out and catch:
- Pocket width: `SNAP_CLIP_W + SNAP_TOL * 2` (12.6mm)
- Pocket depth (into tray bottom face): `SNAP_HOOK` (1.2mm)
- Pocket height: `SNAP_HOOK * 2` (2.4mm)

**Cable pass-through:** The socket is a through-hole, so the cable path is inherently continuous — pole internal cavity → socket hole → bottom tray cavity. The existing `mudra_cable` cut in the top tray base (which cuts a `MUDRA_CABLE_CH_D x MUDRA_CABLE_CH_W` hole through the full height) already provides this. The socket just needs to encompass it.

### 3. Code Changes to `build_top_tray()`

**Remove:** The entire pole-building section:
- Post construction (local coordinates)
- Shelf construction and union
- Charger bay cut
- Chamfer lip loft
- Cable channel cuts (horizontal and vertical)
- `pole.translate()` and `base.union(pole)`
- World-coordinate re-cuts for cable channel continuity

**Add:** Socket cut at the pole position (`mx, my`):
- Rectangular through-hole (`MUDRA_POLE_D + SNAP_TOL*2` x `MUDRA_POLE_W + SNAP_TOL*2` x `TOP_H + 1`)
- Snap hook engagement pockets on the bottom face

**Keep:** The existing `mudra_cable` pass-through cut (already cuts cable channel through the base).

### 4. New `build_mudra_pole()` Function

A new function that builds the pole as a standalone part at the origin:
- Vertical post at origin, extruded upward from Z=0
- Shelf unioned at top
- Charger bay, chamfer lip, cable channels cut (same geometry as current, but built standalone)
- Snap clip tabs added to the base, extending downward (into negative Z, then the export script translates to Z=0)

### 5. Export Updates (`export_charging_stand.py`)

Add a 4th export:
- `output/v1-charging-stand-mudra-pole.stl` — no rotation needed (prints upright)
- `output/v1-charging-stand-mudra-pole.step` — assembly position for CAD review
- Translate so Z_min = 0 (same as other parts)

### 6. Slicer Job Updates (`k8s/slice-all-parts.yaml`)

Add a 4th slice+validate+upload section:
- Input: `v1-charging-stand-mudra-pole.stl` via a new ConfigMap volume (`slicer-stl-input-mudra-pole`)
- Validate: no `--require-supports` (prints upright, no overhangs)
- Upload: `v1-charging-stand-mudra-pole.gcode`

### 7. cadquery-server Preview

The `show_object()` calls at the bottom of the design file need to include the new mudra pole part so it renders in the browser preview. After pushing:
1. `python3 export_charging_stand.py` — verify build succeeds
2. `git commit && git push`
3. `kubectl rollout restart deployment cadquery-server -n utilities` — trigger git-sync
4. Check preview in browser

## Files Changed

| File | Change |
|------|--------|
| `designs/v1-charging-stand.py` | Remove pole from `build_top_tray()`, add socket cut, add `build_mudra_pole()` function, add `show_object()` call |
| `export_charging_stand.py` | Add 4th export for mudra pole STL/STEP |
| `k8s/slice-all-parts.yaml` | Add 4th slice+validate+upload section, add ConfigMap volume |
| `CLAUDE.md` | Document the 4-part assembly (bottom tray, top tray, mudra pole, iPad cover) |

## Print Time Impact

| Part | Before (with supports) | After (no supports) |
|------|----------------------|-------------------|
| Top tray | 37h | ~14-16h |
| Mudra pole | (included in top tray) | ~2-3h |
| **Total top half** | **37h** | **~16-19h** |
| Bottom tray | ~15h | ~15h (unchanged) |
| iPad cover | <1h | <1h (unchanged) |
