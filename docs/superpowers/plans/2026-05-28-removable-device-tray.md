# Removable Device Tray Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separate the four front-row device pockets from the top tray into a standalone drop-in device tray, making both parts easier to print and iterate.

**Architecture:** Add `build_device_tray()` function containing all front-row device geometry (pockets, hinge sockets, push rod slots, Mudra socket). Modify `build_top_tray()` to replace individual pocket cuts with a single rectangular cutout and 3-sided perimeter ledge. Update export script and add slicer job.

**Tech Stack:** CadQuery (Python), PrusaSlicer CLI (K8s Job), Moonraker API

**Spec:** `docs/superpowers/specs/2026-05-28-removable-device-tray-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `designs/v1-charging-stand.py` | Modify | Add `build_device_tray()`, modify `build_top_tray()`, add constants, update build/display section |
| `export_charging_stand.py` | Modify | Add device tray STL/STEP export |
| `k8s/slice-device-tray.yaml` | Create | Slicer job for device tray |
| `CLAUDE.md` | Modify | Update architecture section (6 parts), add lessons learned |

---

### Task 1: Add device tray constants

**Files:**
- Modify: `designs/v1-charging-stand.py:39-52` (constants section, after SNAP_HOOK)

- [ ] **Step 1: Add device tray constants after the snap-fit constants block**

Add these constants after line 52 (`SNAP_HOOK = 1.2`), before the base platform section:

```python
# --- Removable device tray (front-row wearable pockets) ---
# Drop-in friction-fit tray holding UH, R1, Omi pockets + Mudra socket.
# Rests on a 3-sided ledge inside a rectangular cutout in the top tray.
DTRAY_TOL = SNAP_TOL           # 0.3mm clearance per side
DTRAY_LEDGE = WALL             # 2.5mm ledge width for tray to rest on
DTRAY_FLOOR_Z = SPLIT_Z + LID_FLOOR  # 43mm — bottom of device tray
# Width and depth computed dynamically from SLOT_POSITIONS + device sizes
```

- [ ] **Step 2: Verify the file still parses**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 -c "exec(open('designs/v1-charging-stand.py').read().replace('from cq_server.ui import ui, show_object', '# stripped').split('show_object')[0])"`

Expected: No errors (constants parse correctly)

- [ ] **Step 3: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add device tray constants (DTRAY_TOL, DTRAY_LEDGE, DTRAY_FLOOR_Z)"
```

---

### Task 2: Create `build_device_tray()` function

**Files:**
- Modify: `designs/v1-charging-stand.py` — add new function after `build_top_tray()` (after line 1755)

This is the largest task. The function builds the device tray body and cuts all four device pockets, cable holes, push rod slots, hinge sockets, and the Mudra pole socket into it.

- [ ] **Step 1: Add the device tray function skeleton with computed dimensions**

Insert after the `return base` at the end of `build_top_tray()` (line 1755), before `build_ipad_cover()`:

```python


# =============================================================================
# BUILD DEVICE TRAY (removable front-row wearable pocket tray)
# =============================================================================

def build_device_tray():
    """Removable device tray: holds UH, R1, Omi pockets + Mudra pole socket.

    Drops into a rectangular cutout in the top tray body, resting on a
    3-sided perimeter ledge (left, right, rear). Front edge butts against
    the top tray's front wall. Flush with top surface at Z=STAND_H.

    Prints right-side up (flat floor on build plate, pockets open upward).
    No supports needed.
    """

    # ── Compute tray footprint from device positions ────────────────────
    # X: from UH left edge to Mudra shelf right tip, plus WALL each side
    _uh_x = SLOT_POSITIONS["uh_ring"][0]
    _mudra_x = SLOT_POSITIONS["mudra"][0]
    _dtray_x_min = _uh_x - UH_SIDE / 2 - WALL          # left edge
    _dtray_x_max = _mudra_x + MUDRA_SHELF_L + WALL      # right edge (shelf tip + wall)
    DTRAY_W = _dtray_x_max - _dtray_x_min               # total width
    _dtray_cx = (_dtray_x_min + _dtray_x_max) / 2       # center X

    # Y: from front wall inner face to rear of deepest pocket + margin
    _dtray_y_min = -STAND_D / 2 + WALL                  # inner face of front wall
    _dtray_y_max = FRONT_ROW_Y + max(UH_SIDE, R1_DIA, 25) / 2 + WALL  # rear edge
    DTRAY_D = _dtray_y_max - _dtray_y_min               # total depth
    _dtray_cy = (_dtray_y_min + _dtray_y_max) / 2       # center Y

    DTRAY_H = STAND_H - DTRAY_FLOOR_Z                   # 15mm (Z=43 to Z=58)

    # ── Shared hinge socket constants ──────────────────────────────────
    _socket_od = HINGE_BARREL_OD + HINGE_SOCKET_TOL * 2  # 3.6mm
    _socket_len = HINGE_BARREL_L + HINGE_SOCKET_TOL * 2  # 8.6mm

    # ── Tray body ───────────────────────────────────────────────────────
    tray = (
        cq.Workplane("XY")
        .workplane(offset=DTRAY_FLOOR_Z)
        .center(_dtray_cx, _dtray_cy)
        .rect(DTRAY_W, DTRAY_D)
        .extrude(DTRAY_H)
    )
```

- [ ] **Step 2: Add UH Ring pocket (CRADLE 1) to the device tray**

Continue the function with the UH pocket, cable notch, floor cable hole, and hinge barrel sockets. This is moved from `build_top_tray()` lines 1128-1180:

```python
    # =====================================================================
    # CRADLE 1: Ultrahuman Ring Air — SQUARE pocket, rounded corners
    # =====================================================================
    ux, uy = SLOT_POSITIONS["uh_ring"]
    uh_pocket = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - UH_CRADLE_DEPTH)
        .center(ux, uy)
        .rect(UH_SIDE, UH_SIDE)
        .extrude(UH_CRADLE_DEPTH + 1)
    )
    tray = tray.cut(uh_pocket)

    # Front edge cable notch — USB-C exits through tray's front face
    uh_front_slot = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - UH_CRADLE_DEPTH)
        .center(ux, uy - UH_SIDE / 2 - 5)
        .rect(USBC_HEAD_W, WALL + 12)
        .extrude(USBC_HEAD_H)
    )
    tray = tray.cut(uh_front_slot)

    # Floor pass-through (cable drops to bottom tray)
    uh_cable = (
        cq.Workplane("XY")
        .workplane(offset=DTRAY_FLOOR_Z - 0.5)
        .center(ux, uy - UH_SIDE / 2)
        .rect(USBC_HEAD_W, USBC_HEAD_H)
        .extrude(DTRAY_H + 1)
    )
    tray = tray.cut(uh_cable)

    # Hinge barrel sockets in front (-Y) wall
    _uh_plate_side = UH_SIDE - TILT_CLEARANCE * 2
    _uh_barrel_spacing = _uh_plate_side - 2 * 10
    _uh_front_y = uy - UH_SIDE / 2
    _uh_socket_z = STAND_H - UH_CRADLE_DEPTH

    for x_sign in [-1, 1]:
        _bx = ux + x_sign * _uh_barrel_spacing / 2
        barrel_socket = (
            cq.Workplane("YZ")
            .workplane(offset=_bx - _socket_len / 2)
            .center(_uh_front_y, _uh_socket_z + TILT_PLATE_T / 2)
            .circle(_socket_od / 2)
            .extrude(_socket_len)
        )
        tray = tray.cut(barrel_socket)
```

- [ ] **Step 3: Add R1 Ring pocket (CRADLE 2) to the device tray**

Moved from `build_top_tray()` lines 1188-1238:

```python
    # =====================================================================
    # CRADLE 2: Even R1 Ring — CIRCULAR pocket
    # =====================================================================
    rx, ry = SLOT_POSITIONS["r1_ring"]
    r1_cup = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - R1_CRADLE_DEPTH)
        .center(rx, ry)
        .circle(R1_DIA / 2)
        .extrude(R1_CRADLE_DEPTH + 1)
    )
    tray = tray.cut(r1_cup)

    # Front edge cable notch
    r1_cable_groove = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - R1_CRADLE_DEPTH)
        .center(rx, ry - R1_DIA / 2 - 5)
        .rect(USBC_HEAD_W, WALL + 12)
        .extrude(USBC_HEAD_H)
    )
    tray = tray.cut(r1_cable_groove)

    # Floor pass-through
    r1_cable = (
        cq.Workplane("XY")
        .workplane(offset=DTRAY_FLOOR_Z - 0.5)
        .center(rx, ry - R1_DIA / 2)
        .rect(USBC_HEAD_W, USBC_HEAD_H)
        .extrude(DTRAY_H + 1)
    )
    tray = tray.cut(r1_cable)

    # Hinge barrel sockets in front (-Y) wall
    _r1_plate_dia = R1_DIA - TILT_CLEARANCE * 2
    _r1_chord_cut_y = _r1_plate_dia / 2 - 2
    _r1_front_y = ry - _r1_chord_cut_y
    _r1_socket_z = STAND_H - R1_CRADLE_DEPTH
    _r1_barrel_spacing = 8

    for x_sign in [-1, 1]:
        _bx = rx + x_sign * _r1_barrel_spacing / 2
        barrel_socket = (
            cq.Workplane("YZ")
            .workplane(offset=_bx - _socket_len / 2)
            .center(_r1_front_y, _r1_socket_z + TILT_PLATE_T / 2)
            .circle(_socket_od / 2)
            .extrude(_socket_len)
        )
        tray = tray.cut(barrel_socket)
```

- [ ] **Step 4: Add Omi pocket (CRADLE 3) to the device tray**

Moved from `build_top_tray()` lines 1246-1308:

```python
    # =====================================================================
    # CRADLE 3: Omi DevKit 2 — SIX-SIDED DIAMOND pocket
    # =====================================================================
    ox, oy = SLOT_POSITIONS["omi"]
    diamond_pts = six_sided_diamond_points(OMI_LONG_EDGE + TOL * 2, OMI_SHORT_EDGE + TOL * 2)
    diamond_closed = diamond_pts + [diamond_pts[0]]

    omi_pocket = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - OMI_CRADLE_DEPTH)
        .center(ox, oy)
        .polyline(diamond_closed)
        .close()
        .extrude(OMI_CRADLE_DEPTH + 1)
    )
    omi_pocket = omi_pocket.edges("|Z").fillet(OMI_VERTEX_R)
    tray = tray.cut(omi_pocket)

    # USB-C port notch — front-left of diamond
    _omi_front_y_world = oy + min(p[1] for p in diamond_pts)
    _omi_port_x = ox - 8
    omi_port_slot = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - OMI_CRADLE_DEPTH)
        .center(_omi_port_x, _omi_front_y_world - 5)
        .rect(USBC_HEAD_W, WALL + 12)
        .extrude(USBC_HEAD_H)
    )
    tray = tray.cut(omi_port_slot)

    # Floor pass-through
    omi_cable = (
        cq.Workplane("XY")
        .workplane(offset=DTRAY_FLOOR_Z - 0.5)
        .center(_omi_port_x, _omi_front_y_world)
        .rect(USBC_HEAD_W, USBC_HEAD_H)
        .extrude(DTRAY_H + 1)
    )
    tray = tray.cut(omi_cable)

    # Hinge barrel sockets in front (-Y) wall
    _omi_pts = six_sided_diamond_points(
        OMI_LONG_EDGE + TOL * 2 - TILT_CLEARANCE * 2,
        OMI_SHORT_EDGE + TOL * 2 - TILT_CLEARANCE * 2
    )
    _omi_front_y_local = min(p[1] for p in _omi_pts)
    _omi_chord_cut_y = _omi_front_y_local + 2
    _omi_front_y = oy + _omi_chord_cut_y
    _omi_socket_z = STAND_H - OMI_CRADLE_DEPTH
    _omi_barrel_spacing = 8

    for x_sign in [-1, 1]:
        _bx = ox + x_sign * _omi_barrel_spacing / 2
        barrel_socket = (
            cq.Workplane("YZ")
            .workplane(offset=_bx - _socket_len / 2)
            .center(_omi_front_y, _omi_socket_z + TILT_PLATE_T / 2)
            .circle(_socket_od / 2)
            .extrude(_socket_len)
        )
        tray = tray.cut(barrel_socket)
```

- [ ] **Step 5: Add Mudra pole socket and snap pockets to the device tray**

Moved from `build_top_tray()` lines 1320-1362. The snap engagement pockets now cut upward into the device tray's underside:

```python
    # =====================================================================
    # CRADLE 4: Mudra Link — pole socket + snap engagement
    # =====================================================================
    mx, my = SLOT_POSITIONS["mudra"]

    # Cable pass-through (full height)
    mudra_cable = (
        cq.Workplane("XY")
        .center(mx, my)
        .rect(MUDRA_CABLE_CH_D, MUDRA_CABLE_CH_W)
        .extrude(STAND_H)
    )
    tray = tray.cut(mudra_cable)

    # Pole socket — through-hole for snap-in pole
    _socket_w = MUDRA_POLE_D + SNAP_TOL * 2   # 20.6mm in X
    _socket_d = MUDRA_POLE_W + SNAP_TOL * 2   # 22.6mm in Y
    mudra_socket = (
        cq.Workplane("XY")
        .workplane(offset=DTRAY_FLOOR_Z - 0.5)
        .center(mx, my)
        .rect(_socket_w, _socket_d)
        .extrude(DTRAY_H + 1)
    )
    tray = tray.cut(mudra_socket)

    # Snap hook engagement pockets on the underside of the tray
    _pocket_w = MUDRA_CLIP_W + SNAP_TOL * 2   # 14.6mm
    _pocket_depth = MUDRA_HOOK                 # 2.0mm
    _pocket_h = MUDRA_HOOK_H + 1              # 3.0mm
    for side_sign in [-1, 1]:
        pocket_x = mx + side_sign * (_socket_w / 2 + _pocket_depth / 2)
        snap_pocket = (
            cq.Workplane("XY")
            .workplane(offset=DTRAY_FLOOR_Z - _pocket_h)
            .center(pocket_x, my)
            .rect(_pocket_depth, _pocket_w)
            .extrude(_pocket_h + 0.5)
        )
        tray = tray.cut(snap_pocket)
```

- [ ] **Step 6: Add push rod slots and generic cable pass-throughs, then return**

```python
    # ── Push rod slots (servo actuator pass-through) ────────────────────
    _push_rod_devices = ["uh_ring", "r1_ring", "omi", "mudra"]
    for name in _push_rod_devices:
        px, py = SLOT_POSITIONS[name]
        push_slot = (
            cq.Workplane("XY")
            .workplane(offset=DTRAY_FLOOR_Z - 0.5)
            .center(px, SERVO_Y)
            .rect(PUSH_ROD_SLOT_W, PUSH_ROD_SLOT_L)
            .extrude(DTRAY_H + 1)
        )
        tray = tray.cut(push_slot)

    # ── Mudra generic cable pass-through (from SLOT_POSITIONS loop) ─────
    # The original top tray cut cable holes for mudra via the generic loop.
    # This is now handled by the mudra_cable cut above, so no extra cut needed.

    return tray
```

- [ ] **Step 7: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add build_device_tray() with all four device cradles"
```

---

### Task 3: Modify `build_top_tray()` — remove device geometry, add cutout and ledge

**Files:**
- Modify: `designs/v1-charging-stand.py:1046-1755` (`build_top_tray()` function)

This task removes the four device cradle sections from `build_top_tray()` and replaces them with a single rectangular cutout and perimeter ledge for the device tray to drop into.

- [ ] **Step 1: Remove CRADLE 1 (UH Ring) from build_top_tray()**

Delete lines 1123-1180 (the entire CRADLE 1 section including the pocket cut, front wall slot, floor pass-through, and hinge barrel sockets). These are now in `build_device_tray()`.

- [ ] **Step 2: Remove CRADLE 2 (R1 Ring) from build_top_tray()**

Delete lines 1182-1238 (the entire CRADLE 2 section). Now in `build_device_tray()`.

- [ ] **Step 3: Remove CRADLE 3 (Omi) from build_top_tray()**

Delete lines 1240-1308 (the entire CRADLE 3 section). Now in `build_device_tray()`.

- [ ] **Step 4: Remove CRADLE 4 (Mudra) from build_top_tray()**

Delete lines 1310-1362 (Mudra cable pass-through, socket, and snap pockets). Now in `build_device_tray()`.

- [ ] **Step 5: Remove front-row push rod slots from build_top_tray()**

The push rod slots at lines 1089-1102 iterate over `["uh_ring", "r1_ring", "omi", "mudra"]`. These are now cut in `build_device_tray()`. Remove this entire block.

- [ ] **Step 6: Remove front-row cable pass-throughs from build_top_tray()**

The cable pass-through loop at lines 1104-1121 cuts holes for each SLOT_POSITIONS entry. Remove the entries that are now handled by the device tray. Keep the loop but only process `"g2_case"` (the only remaining device in the top tray). The `"uh_ring"`, `"r1_ring"`, `"omi"` entries were already skipped with `continue`, and `"mudra"` was handled by the generic branch. Replace the loop with just the G2 cable hole:

```python
    # ── Cable pass-through for G2 (only rear-row device remains) ────────
    gx_cable, gy_cable = SLOT_POSITIONS["g2_case"]
    g2_cable_hole = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(gx_cable, gy_cable)
        .rect(USBC_HEAD_W + 2, USBC_HEAD_H + 2)
        .extrude(TOP_H + 1)
    )
    base = base.cut(g2_cable_hole)
```

- [ ] **Step 7: Add device tray rectangular cutout and 3-sided ledge**

Add this section after the snap-fit receiving slots, where the device cradles used to be. This computes the same footprint as `build_device_tray()` and cuts a matching opening:

```python
    # =====================================================================
    # DEVICE TRAY CUTOUT — rectangular opening for drop-in device tray
    # =====================================================================
    # Compute the same footprint as build_device_tray() for a matching cutout.
    _uh_x = SLOT_POSITIONS["uh_ring"][0]
    _mudra_x = SLOT_POSITIONS["mudra"][0]
    _dtray_x_min = _uh_x - UH_SIDE / 2 - WALL
    _dtray_x_max = _mudra_x + MUDRA_SHELF_L + WALL
    _dtray_w = _dtray_x_max - _dtray_x_min
    _dtray_cx = (_dtray_x_min + _dtray_x_max) / 2

    _dtray_y_min = -STAND_D / 2 + WALL
    _dtray_y_max = FRONT_ROW_Y + max(UH_SIDE, R1_DIA, 25) / 2 + WALL
    _dtray_d = _dtray_y_max - _dtray_y_min
    _dtray_cy = (_dtray_y_min + _dtray_y_max) / 2

    # Cut the opening — full height from DTRAY_FLOOR_Z to top, with clearance
    _cutout_w = _dtray_w + DTRAY_TOL * 2   # tray width + clearance
    _cutout_d = _dtray_d + DTRAY_TOL * 2   # tray depth + clearance
    dtray_cutout = (
        cq.Workplane("XY")
        .workplane(offset=DTRAY_FLOOR_Z)
        .center(_dtray_cx, _dtray_cy)
        .rect(_cutout_w, _cutout_d)
        .extrude(STAND_H - DTRAY_FLOOR_Z + 1)
    )
    base = base.cut(dtray_cutout)

    # 3-sided perimeter ledge (left, right, rear) for tray to rest on.
    # The front side has no ledge — the top tray's front wall is containment.
    # The ledge is DTRAY_LEDGE (2.5mm) wide and LID_FLOOR (2mm) tall,
    # sitting at DTRAY_FLOOR_Z - LID_FLOOR (Z=41, same as SPLIT_Z).
    # Actually, the ledge is part of the existing tray body — we just need
    # to make the cutout NOT extend below DTRAY_FLOOR_Z. The LID_FLOOR
    # slab and the tray body below the cutout naturally form the ledge.
    # But we need to extend the cutout on the front side (no ledge there)
    # all the way to the front wall so the tray can butt against it.

    # Extend cutout forward to inner face of front wall (no front ledge)
    _front_extension = (
        cq.Workplane("XY")
        .workplane(offset=DTRAY_FLOOR_Z)
        .center(_dtray_cx, (_dtray_y_min - DTRAY_TOL + (-STAND_D / 2 + WALL)) / 2)
        .rect(_cutout_w, abs(_dtray_y_min - DTRAY_TOL - (-STAND_D / 2 + WALL)) + 1)
        .extrude(STAND_H - DTRAY_FLOOR_Z + 1)
    )
    base = base.cut(_front_extension)

    # Clearance notches for Mudra snap hook engagement pockets.
    # The snap pockets on the device tray underside extend below DTRAY_FLOOR_Z.
    # Cut matching clearance in the ledge area so the tray drops in flush.
    _ms_socket_w = MUDRA_POLE_D + SNAP_TOL * 2
    _ms_pocket_w = MUDRA_CLIP_W + SNAP_TOL * 2
    _ms_pocket_depth = MUDRA_HOOK
    _ms_pocket_h = MUDRA_HOOK_H + 1
    mx_cutout, my_cutout = SLOT_POSITIONS["mudra"]
    for _ms_sign in [-1, 1]:
        _ms_x = mx_cutout + _ms_sign * (_ms_socket_w / 2 + _ms_pocket_depth / 2)
        _ms_clearance = (
            cq.Workplane("XY")
            .workplane(offset=DTRAY_FLOOR_Z - _ms_pocket_h - 0.5)
            .center(_ms_x, my_cutout)
            .rect(_ms_pocket_depth + DTRAY_TOL * 2, _ms_pocket_w + DTRAY_TOL * 2)
            .extrude(_ms_pocket_h + 1)
        )
        base = base.cut(_ms_clearance)
```

- [ ] **Step 8: Update LID_FLOOR re-cuts — remove front-row device holes**

In the "CONTINUOUS LID FLOOR" section (around line 1588+), after the floor is unioned, the following re-cuts are for front-row devices and must be removed since the device tray cutout replaces them:

Remove these re-cuts:
- Push rod slots for `["uh_ring", "r1_ring", "omi", "mudra"]` (lines ~1621-1630)
- Mudra pole socket re-cut (lines ~1632-1642)
- Mudra cable hole re-cut (lines ~1644-1652)
- Mudra snap hook engagement pockets re-cut (lines ~1654-1667)
- UH cable hole re-cut (lines ~1673-1682)
- R1 cable hole re-cut (lines ~1684-1693)
- Omi cable hole re-cut (lines ~1695-1707)

Keep these re-cuts (rear-row devices, still in top tray):
- G2 cable hole (lines ~1709-1718)
- G2 LCD viewing window (lines ~1720-1729)
- iPad cable vertical hole (lines ~1731-1740)
- iPad blade slot (lines ~1742-1753)

The device tray cutout itself will replace all the individual front-row floor holes. Add a single re-cut for the device tray opening through the LID_FLOOR:

```python
    # Device tray cutout — re-cut through LID_FLOOR
    _floor_dtray_cutout = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z)
        .center(_dtray_cx, _dtray_cy)
        .rect(_cutout_w, _cutout_d)
        .extrude(LID_FLOOR + 0.5)
    )
    base = base.cut(_floor_dtray_cutout)
```

Note: `_dtray_cx`, `_dtray_cy`, `_cutout_w`, `_cutout_d` are already computed earlier in the function from Step 7. Make sure these variables are in scope (they are, since they're defined in the same function body).

- [ ] **Step 9: Keep front wall cable slots**

The USB-C cable exit slots in the top tray's front wall for UH, R1, and Omi must remain. These are NOT part of the device cradle cuts — they're wall pass-throughs that the device tray's front-edge notches align with. However, looking at the original code, the front wall slots were cut as part of each cradle section (e.g., `uh_front_slot` cuts deep enough to "visibly breach front wall").

Since the device tray's front edge now butts against the front wall's inner face, the cable must pass through BOTH the device tray's front notch AND the top tray's front wall. The device tray already has front notches (from Step 2-4). The top tray needs matching wall slots.

Add these front wall cable slots to `build_top_tray()`, after the device tray cutout:

```python
    # ── Front wall cable slots (matching device tray front-edge notches) ──
    # These pass through the top tray's front wall so cables from device
    # pockets can exit to the exterior. The device tray has matching open
    # notches on its front edge that align with these.

    # UH cable slot
    _uh_wall_x = SLOT_POSITIONS["uh_ring"][0]
    uh_wall_slot = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - UH_CRADLE_DEPTH)
        .center(_uh_wall_x, -STAND_D / 2)
        .rect(USBC_HEAD_W, WALL * 2 + 2)
        .extrude(USBC_HEAD_H)
    )
    base = base.cut(uh_wall_slot)

    # R1 cable slot
    _r1_wall_x = SLOT_POSITIONS["r1_ring"][0]
    r1_wall_slot = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - R1_CRADLE_DEPTH)
        .center(_r1_wall_x, -STAND_D / 2)
        .rect(USBC_HEAD_W, WALL * 2 + 2)
        .extrude(USBC_HEAD_H)
    )
    base = base.cut(r1_wall_slot)

    # Omi cable slot
    _omi_wall_x = SLOT_POSITIONS["omi"][0] - 8  # offset left, matching pocket
    omi_wall_slot = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - OMI_CRADLE_DEPTH)
        .center(_omi_wall_x, -STAND_D / 2)
        .rect(USBC_HEAD_W, WALL * 2 + 2)
        .extrude(USBC_HEAD_H)
    )
    base = base.cut(omi_wall_slot)
```

- [ ] **Step 10: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "refactor: replace device pockets in top tray with rectangular cutout and ledge"
```

---

### Task 4: Update build/display section and export script

**Files:**
- Modify: `designs/v1-charging-stand.py:2493-2581` (build and display section)
- Modify: `export_charging_stand.py`

- [ ] **Step 1: Add device tray build + show_object call**

In the BUILD AND DISPLAY section (line ~2497), after `top_tray = build_top_tray()`, add:

```python
device_tray = build_device_tray()
```

After the `show_object(top_tray, ...)` call (line ~2506), add:

```python
show_object(device_tray, name="device_tray",
            options={"color": (0.25, 0.25, 0.27, 0.95)})
```

- [ ] **Step 2: Update export script — add device_tray export**

In `export_charging_stand.py`, after the line `mudra_pole = exec_globals.get('mudra_pole')` (line 45), add:

```python
        device_tray = exec_globals.get('device_tray')
```

After the mudra pole translation block (around line 94), add:

```python
    # Device tray — translate to Z=0 for printing (no flip needed)
    if device_tray:
        dtray_bb = device_tray.val().BoundingBox()
        dtray_print = device_tray.translate((0, 0, -dtray_bb.zmin))
        print(f"   Device tray: translated Z by {-dtray_bb.zmin:+.1f}mm (was Z={dtray_bb.zmin:.1f})")
```

After the mudra pole STL/STEP export block (around line 171), add:

```python
        # Device tray — drop-in wearable pocket tray
        if device_tray:
            dtray_stl_path = output_dir / "v1-charging-stand-device-tray.stl"
            cq.exporters.export(dtray_print, str(dtray_stl_path))
            print(f"✅ {dtray_stl_path} - Device tray (drop-in, prints right-side up)")

            dtray_step_path = output_dir / "v1-charging-stand-device-tray.step"
            cq.exporters.export(device_tray, str(dtray_step_path))
            print(f"✅ {dtray_step_path} - Device tray STEP (assembly position)")
```

- [ ] **Step 3: Commit**

```bash
git add designs/v1-charging-stand.py export_charging_stand.py
git commit -m "feat: add device tray to build/display section and export script"
```

---

### Task 5: Create K8s slicer job for device tray

**Files:**
- Create: `k8s/slice-device-tray.yaml`

- [ ] **Step 1: Create the slicer job**

Create `k8s/slice-device-tray.yaml` based on `k8s/slice-bottom-tray.yaml` (no supports, no brim):

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: slice-device-tray
  namespace: utilities
spec:
  ttlSecondsAfterFinished: 3600
  backoffLimit: 1
  template:
    spec:
      restartPolicy: Never
      nodeSelector:
        kubernetes.io/arch: amd64
      initContainers:
      - name: fetch-stl
        image: alpine/git:latest
        command: ["/bin/sh", "-c"]
        args:
        - |
          git clone --depth 1 https://github.com/somni-labs/somni-wearable-dock.git /tmp/repo
          cp /tmp/repo/output/v1-charging-stand-device-tray.stl /shared/device-tray.stl
          ls -la /shared/
        volumeMounts:
        - name: shared
          mountPath: /shared
      containers:
      - name: slicer
        image: cznewt/prusa-slicer:latest
        command: ["/bin/bash", "-c"]
        args:
        - |
          set -e
          echo "=== PrusaSlicer — Device Tray ==="

          SLICER=/prusa-slicer/prusa-slicer
          INI=/tmp/pla_plus.ini
          MOONRAKER="http://192.168.1.15:7125"

          cat > "$INI" << 'PROFILE'
          layer_height = 0.3
          first_layer_height = 0.35
          perimeters = 3
          top_solid_layers = 5
          bottom_solid_layers = 4
          fill_density = 20%
          fill_pattern = gyroid
          external_perimeter_speed = 40
          infill_speed = 60
          travel_speed = 150
          bridge_speed = 25
          support_material = 0
          support_material_auto = 0
          skirts = 2
          skirt_distance = 5
          brim_width = 0
          temperature = 215
          first_layer_temperature = 220
          bed_temperature = 70
          first_layer_bed_temperature = 70
          fan_always_on = 0
          min_fan_speed = 0
          max_fan_speed = 80
          bridge_fan_speed = 80
          overhangs_fan_speed = 80
          disable_fan_first_layers = 3
          gcode_flavor = klipper
          bed_shape = 0x0,275x0,275x295,0x295
          max_print_height = 265
          nozzle_diameter = 0.4
          retract_length = 0.8
          retract_speed = 40
          retract_lift = 0.2
          start_gcode = G28\nG1 Z5 F5000
          end_gcode = END_PRINT
          PROFILE

          sed -i 's/^[[:space:]]*//' "$INI"

          echo "--- Checking STL ---"
          ls -la /shared/device-tray.stl

          echo "--- Slicing device tray (NO supports, NO brim, prints right-side up) ---"
          $SLICER --load "$INI" --center 137,147 \
            --output /tmp/device-tray.gcode --export-gcode /shared/device-tray.stl

          echo "--- Capping fan speed to 80% (S204) ---"
          sed -i 's/M106 S255/M106 S204/g' /tmp/device-tray.gcode
          FULL_FAN=$(grep -c 'M106 S255' /tmp/device-tray.gcode || true)
          echo "  M106 S255 remaining after cap: $FULL_FAN (should be 0)"

          echo "--- Validating gcode ---"
          BED_TEMP=$(grep -E '^M1[49]0 S[0-9]+' /tmp/device-tray.gcode | sed 's/.*S\([0-9]*\).*/\1/' | head -1)
          EXT_TEMP=$(grep -E '^M10[49] S[0-9]+' /tmp/device-tray.gcode | sed 's/.*S\([0-9]*\).*/\1/' | sort -n | tail -1)
          LAYER_COUNT=$(grep -c ';LAYER_CHANGE' /tmp/device-tray.gcode || true)
          echo "  Bed temp: ${BED_TEMP}C, Extruder temp: ${EXT_TEMP}C, Layers: ${LAYER_COUNT}"

          ERRORS=0
          if [ -z "$BED_TEMP" ] || [ "$BED_TEMP" -lt 65 ]; then
            echo "  FAIL: Bed temp too low (got: ${BED_TEMP:-none}, need >= 65)"
            ERRORS=$((ERRORS + 1))
          else
            echo "  OK: Bed temperature = ${BED_TEMP}C"
          fi
          if [ -z "$EXT_TEMP" ] || [ "$EXT_TEMP" -lt 210 ]; then
            echo "  FAIL: Extruder temp too low (got: ${EXT_TEMP:-none}, need >= 210)"
            ERRORS=$((ERRORS + 1))
          else
            echo "  OK: Extruder temperature = ${EXT_TEMP}C"
          fi
          if [ "$LAYER_COUNT" -lt 3 ]; then
            echo "  FAIL: Only $LAYER_COUNT layers — file may be corrupt"
            ERRORS=$((ERRORS + 1))
          else
            echo "  OK: $LAYER_COUNT layers"
          fi

          X_MAX=$(awk -F'X' '/^G1 .*X[0-9]/ { split($2, a, " "); if (a[1]+0 > max) max=a[1]+0 } END { printf "%.1f", max }' /tmp/device-tray.gcode)
          Y_MAX=$(awk -F'Y' '/^G1 .*Y[0-9]/ { split($2, a, " "); if (a[1]+0 > max) max=a[1]+0 } END { printf "%.1f", max }' /tmp/device-tray.gcode)
          echo "  Coordinate bounds: X max = ${X_MAX}, Y max = ${Y_MAX}"

          if [ "$ERRORS" -gt 0 ]; then
            echo "  ABORT: $ERRORS validation error(s)"
            exit 1
          fi
          echo "  PASS: All gcode checks passed"

          echo "--- Uploading to Moonraker ---"
          curl -s -X DELETE "$MOONRAKER/server/files/gcodes/v1-charging-stand-device-tray.gcode" || true
          sleep 2
          UPLOAD_RESULT=$(curl -s -X POST "$MOONRAKER/server/files/upload" \
            -F "file=@/tmp/device-tray.gcode;filename=v1-charging-stand-device-tray.gcode" \
            -F "root=gcodes")
          echo "  Upload result: $UPLOAD_RESULT"

          echo ""
          echo "=== Device tray sliced and uploaded ==="
          echo "  File size: $(wc -c < /tmp/device-tray.gcode) bytes"
          echo "  Layers: $LAYER_COUNT"
          echo "  Ready to print: v1-charging-stand-device-tray.gcode"
        volumeMounts:
        - name: shared
          mountPath: /shared
      volumes:
      - name: shared
        emptyDir: {}
```

- [ ] **Step 2: Commit**

```bash
git add k8s/slice-device-tray.yaml
git commit -m "feat: add K8s slicer job for device tray"
```

---

### Task 6: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update architecture section**

Change the architecture description to reflect 6 parts:

Find:
```
- **`k8s/slice-all-parts.yaml`** — K8s Job template for PrusaSlicer slicing + Moonraker upload
```

Replace with:
```
- **`k8s/slice-*.yaml`** — K8s Job templates for PrusaSlicer slicing + Moonraker upload (per-part)
```

Find the line in the architecture section:
```
- **Motorized reveal** — 4x SG90 servo mounts in bottom tray (Y=-37), push rod slots in top tray, servo wiring channels with arch clips
```

Add after it:
```
- **Removable device tray** — Drop-in friction-fit tray (front row) holding UH, R1, Omi pockets + Mudra pole socket. Prints right-side up, no supports. Top tray has rectangular cutout with 3-sided perimeter ledge.
```

- [ ] **Step 2: Add lessons learned entry**

Add to the Lessons Learned section:

```markdown
### Front-row device pockets should be a removable tray

The top tray's four front-row device pockets (UH, R1, Omi, Mudra) created deep overhangs when printed flipped, requiring heavy supports and causing spaghetti failures. Separating them into a removable drop-in tray solves multiple problems:
1. Device tray prints right-side up — zero supports needed
2. Top tray flipped print becomes dramatically simpler
3. Device tray can be reprinted independently when devices change
4. Assembly: 6 parts (bottom tray, top tray, device tray, mudra pole, iPad cover plate, iPad back wall)

**Rule of thumb:** When a group of features creates significant overhang complexity in a flipped print, consider making them a separate drop-in tray that prints in its natural orientation.
```

- [ ] **Step 3: Update the "Separate parts eliminate support material waste" lesson**

Find:
```
Assembly: 5 parts (bottom tray, top tray, mudra pole, iPad cover plate, iPad back wall).
```

Replace with:
```
Assembly: 6 parts (bottom tray, top tray, device tray, mudra pole, iPad cover plate, iPad back wall).
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for 6-part assembly with removable device tray"
```

---

### Task 7: Build verification and export

**Files:** None new — verification only

- [ ] **Step 1: Verify CadQuery build succeeds**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py`

Expected: All STL/STEP files exported successfully, including the new `v1-charging-stand-device-tray.stl` and `v1-charging-stand-device-tray.step`.

- [ ] **Step 2: Verify device tray dimensions are reasonable**

Check the exported STL bounding box. The device tray should be approximately:
- Width: ~220mm (fits Q2 plate)
- Depth: ~55mm
- Height: ~15mm
- No dimension exceeds Q2 build volume (275×295×265)

- [ ] **Step 3: Verify cadquery-server preview**

Push to GitHub, restart cadquery-server, check browser preview:
```bash
git push
kubectl rollout restart deployment cadquery-server -n utilities
```

Verify in cadquery-server that:
- Device tray appears as a separate object
- It sits flush in the top tray cutout
- Mudra pole socket is visible in the device tray
- Device pockets are visible from above

- [ ] **Step 4: Commit any fixes**

If the build or preview reveals issues, fix them and commit:
```bash
git add -A
git commit -m "fix: device tray geometry adjustments from build verification"
```

---

### Task 8: Slice and upload device tray + re-slice top tray

**Files:** None — operational steps

- [ ] **Step 1: Run the device tray slicer job**

```bash
kubectl delete job slice-device-tray -n utilities --ignore-not-found=true
kubectl apply -f k8s/slice-device-tray.yaml
kubectl wait --for=condition=complete job/slice-device-tray -n utilities --timeout=300s
kubectl logs job/slice-device-tray -n utilities -c slicer
```

Verify: All gcode checks pass, file uploaded to Moonraker.

- [ ] **Step 2: Re-slice the top tray (now simpler)**

The top tray has changed significantly — re-slice it:

```bash
kubectl delete job slice-top-tray -n utilities --ignore-not-found=true
kubectl apply -f k8s/slice-top-tray.yaml
kubectl wait --for=condition=complete job/slice-top-tray -n utilities --timeout=300s
kubectl logs job/slice-top-tray -n utilities -c slicer
```

Verify: Gcode passes validation. Note the reduced layer count and filament usage compared to the previous top tray (should be significantly less due to removed device pocket overhangs).

- [ ] **Step 3: Verify both files on Moonraker**

```bash
curl -s "http://192.168.1.15:7125/server/files/metadata?filename=v1-charging-stand-device-tray.gcode" | python3 -m json.tool | grep -E "filament_total|estimated_time|layer_count"
curl -s "http://192.168.1.15:7125/server/files/metadata?filename=v1-charging-stand-top-tray.gcode" | python3 -m json.tool | grep -E "filament_total|estimated_time|layer_count"
```

Do NOT start any prints — just verify the files are ready.
