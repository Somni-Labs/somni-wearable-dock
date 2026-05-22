# Cradle Tilt & Mudra Rise Mechanism Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add drop-in tilt plates with filament pin hinges to 3 front-row wearable cradles, plus push rods connecting servos to cradles and the Mudra pole.

**Architecture:** 3 new `build_*_tilt_plate()` functions produce standalone printable plates. 1 new `build_push_rod()` function produces 4 push rod variants. Hinge barrel sockets are cut into existing cradle pocket rear walls in `build_top_tray()`. Ghost visualization shows plates tilted and push rods extended.

**Tech Stack:** CadQuery (Python), cadquery-server for preview

---

## File Structure

| File | Responsibility | Change Type |
|------|---------------|-------------|
| `designs/v1-charging-stand.py` | Main parametric design — add tilt plate constants, 3 tilt plate build functions, 1 push rod build function, hinge barrel sockets in `build_top_tray()`, ghost overlays, display calls | Modify |
| `export_charging_stand.py` | STL/STEP export — add 7 new part exports (3 tilt plates + 4 push rods) | Modify |

---

### Task 1: Add Tilt Plate and Push Rod Constants

**Files:**
- Modify: `designs/v1-charging-stand.py:188-204` (after existing push rod constants, before proximity sensor constants)

- [ ] **Step 1: Add the new constants block**

After line 191 (`PUSH_ROD_SLOT_L = 12`), add the tilt plate and push rod part constants:

```python
# --- Tilt plate (drop-in cradle inserts) ---
TILT_PLATE_T = 2           # plate thickness (Z)
TILT_CLEARANCE = 0.5       # clearance per side from pocket walls
HINGE_BARREL_OD = 3        # hinge barrel outer diameter
HINGE_BARREL_ID = 1.75     # hinge barrel bore (filament diameter)
HINGE_BARREL_L = 8         # hinge barrel length
HINGE_SOCKET_TOL = 0.3     # tolerance per dimension on barrel sockets
HINGE_BARREL_PROTRUDE = 1.5  # how far barrel extends beyond rear edge

# --- Push rod parts ---
PUSH_ROD_W = 3.5           # rod cross-section width (square)
PUSH_ROD_THEAD_W = 6       # T-head width (wider than slot to prevent fallthrough)
PUSH_ROD_THEAD_H = 2       # T-head height
PUSH_ROD_PAD_W = 8         # Mudra push rod flat pad width
PUSH_ROD_PAD_H = 1.5       # Mudra push rod flat pad height
PUSH_ROD_HORN_HOLE = 1.5   # hole diameter for servo horn screw
PUSH_ROD_HORN_TAB_W = 6    # horn attachment tab width
PUSH_ROD_HORN_TAB_H = 4    # horn attachment tab height

# --- Per-device push rod lengths ---
# From servo horn (~Z = BASE_H + SG90_BODY_H) to tilt plate underside
# UH/R1: plate at Z = STAND_H - cradle_depth = 48, servo top ~25.7 → ~22mm
# Omi: plate at Z = STAND_H - cradle_depth = 43, servo top ~25.7 → ~17mm
# Mudra: pole base at Z = SPLIT_Z (41), servo top ~25.7 → ~15mm
PUSH_ROD_LEN_UH = 22
PUSH_ROD_LEN_R1 = 22
PUSH_ROD_LEN_OMI = 17
PUSH_ROD_LEN_MUDRA = 15
```

- [ ] **Step 2: Verify the design file still loads**

Run:
```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py
```
Expected: `✅ Design objects loaded successfully` (constants are just numbers — no geometry changes yet)

- [ ] **Step 3: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add tilt plate and push rod constants"
```

---

### Task 2: Build UH Ring Tilt Plate Function

**Files:**
- Modify: `designs/v1-charging-stand.py` — add `build_uh_tilt_plate()` function after `build_mudra_pole()` (after line 1668)

- [ ] **Step 1: Add the `build_uh_tilt_plate()` function**

Insert after the `build_mudra_pole()` function (after line 1668, before the ghost visualization section):

```python
# =============================================================================
# TILT PLATES (drop-in cradle inserts with pin hinges)
# =============================================================================

def build_uh_tilt_plate():
    """UH Ring tilt plate — 40x40mm square with rounded corners.

    Built at origin (centered on X/Y, Z=0 to TILT_PLATE_T).
    Two hinge barrels on the +Y edge (rear), captured slot on underside
    for push rod T-head.
    """
    plate_side = UH_SIDE - TILT_CLEARANCE * 2  # 40mm

    # ── Main plate body ──────────────────────────────────────────────────
    plate = (
        cq.Workplane("XY")
        .rect(plate_side, plate_side)
        .extrude(TILT_PLATE_T)
    )
    plate = plate.edges("|Z").fillet(UH_CORNER_R - TILT_CLEARANCE)

    # ── Two hinge barrels on rear (+Y) edge ──────────────────────────────
    # Barrels protrude beyond the rear edge, axis parallel to X.
    # Spaced symmetrically, ~10mm from each end.
    barrel_spacing = plate_side - 2 * 10  # 20mm apart
    barrel_center_y = plate_side / 2 + HINGE_BARREL_PROTRUDE - HINGE_BARREL_OD / 2

    for x_sign in [-1, 1]:
        bx = x_sign * barrel_spacing / 2
        barrel = (
            cq.Workplane("YZ")
            .workplane(offset=bx - HINGE_BARREL_L / 2)
            .center(barrel_center_y, TILT_PLATE_T / 2)
            .circle(HINGE_BARREL_OD / 2)
            .extrude(HINGE_BARREL_L)
        )
        # Bore for filament pin
        bore = (
            cq.Workplane("YZ")
            .workplane(offset=bx - HINGE_BARREL_L / 2 - 0.5)
            .center(barrel_center_y, TILT_PLATE_T / 2)
            .circle(HINGE_BARREL_ID / 2)
            .extrude(HINGE_BARREL_L + 1)
        )
        plate = plate.union(barrel).cut(bore)

    # ── Captured slot on underside for push rod T-head ───────────────────
    # The push rod comes up at (X=0, Y=SERVO_Y relative to world).
    # In plate-local coords: X=0, Y = SERVO_Y - pocket_center_Y
    # pocket_center_Y = FRONT_ROW_Y = -49.5
    # SERVO_Y = -37
    # local_y = -37 - (-49.5) = 12.5  (12.5mm from plate center toward rear)
    slot_local_y = SERVO_Y - FRONT_ROW_Y  # 12.5mm
    captured_slot = (
        cq.Workplane("XY")
        .workplane(offset=-0.1)
        .center(0, slot_local_y)
        .rect(PUSH_ROD_THEAD_W + 0.5, 3)  # 6.5mm wide x 3mm deep channel
        .extrude(TILT_PLATE_T / 2 + 0.1)  # cut into bottom half of plate
    )
    plate = plate.cut(captured_slot)

    return plate
```

- [ ] **Step 2: Add display call and build**

At the bottom of the file, before the ghost visualization section (before `ghosts = build_ghost_components()`), add:

```python
# Tilt plates — displayed at assembly position (in cradle pockets, flat)
uh_tilt_plate = build_uh_tilt_plate()
_uh_plate_assembly = uh_tilt_plate.translate((
    SLOT_POSITIONS["uh_ring"][0],
    SLOT_POSITIONS["uh_ring"][1],
    STAND_H - UH_CRADLE_DEPTH
))
show_object(_uh_plate_assembly, name="uh_tilt_plate",
            options={"color": (0.6, 0.85, 0.6, 0.9)})
pass  # keep loop body after show_object is stripped by export script
```

- [ ] **Step 3: Verify the design loads and plate renders**

Run:
```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py
```
Expected: `✅ Design objects loaded successfully`

- [ ] **Step 4: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add UH Ring tilt plate build function"
```

---

### Task 3: Build R1 Ring Tilt Plate Function

**Files:**
- Modify: `designs/v1-charging-stand.py` — add `build_r1_tilt_plate()` after `build_uh_tilt_plate()`

- [ ] **Step 1: Add the `build_r1_tilt_plate()` function**

Insert immediately after `build_uh_tilt_plate()`:

```python
def build_r1_tilt_plate():
    """R1 Ring tilt plate — 31mm diameter disc.

    Built at origin (centered on X/Y, Z=0 to TILT_PLATE_T).
    The rear (+Y) edge has a flat chord for hinge barrel mounting.
    Two hinge barrels on the flat, captured slot on underside.
    """
    plate_dia = R1_DIA - TILT_CLEARANCE * 2  # 31mm

    # ── Main disc ────────────────────────────────────────────────────────
    plate = (
        cq.Workplane("XY")
        .circle(plate_dia / 2)
        .extrude(TILT_PLATE_T)
    )

    # ── Flat chord on rear edge for barrel mounting ──────────────────────
    # Cut a 2mm slice off the rear to create a flat mounting surface.
    # The flat is at Y = plate_dia/2 - 2 = 13.5mm from center.
    _chord_cut_y = plate_dia / 2 - 2  # 13.5mm
    chord_cut = (
        cq.Workplane("XY")
        .workplane(offset=-0.1)
        .center(0, _chord_cut_y + 10)  # center of a 20mm-deep block beyond the chord
        .rect(plate_dia + 2, 20)
        .extrude(TILT_PLATE_T + 0.2)
    )
    plate = plate.cut(chord_cut)

    # ── Two hinge barrels on the flat chord ──────────────────────────────
    # Chord width at Y=13.5: w = 2*sqrt(r^2 - y^2) = 2*sqrt(15.5^2 - 13.5^2) ≈ 15.2mm
    # Two 8mm barrels need ~20mm — so space them 8mm apart (4mm from center each)
    barrel_spacing = 8  # closer together to fit on the chord
    barrel_center_y = _chord_cut_y + HINGE_BARREL_PROTRUDE - HINGE_BARREL_OD / 2

    for x_sign in [-1, 1]:
        bx = x_sign * barrel_spacing / 2
        barrel = (
            cq.Workplane("YZ")
            .workplane(offset=bx - HINGE_BARREL_L / 2)
            .center(barrel_center_y, TILT_PLATE_T / 2)
            .circle(HINGE_BARREL_OD / 2)
            .extrude(HINGE_BARREL_L)
        )
        bore = (
            cq.Workplane("YZ")
            .workplane(offset=bx - HINGE_BARREL_L / 2 - 0.5)
            .center(barrel_center_y, TILT_PLATE_T / 2)
            .circle(HINGE_BARREL_ID / 2)
            .extrude(HINGE_BARREL_L + 1)
        )
        plate = plate.union(barrel).cut(bore)

    # ── Captured slot on underside ───────────────────────────────────────
    slot_local_y = SERVO_Y - FRONT_ROW_Y  # 12.5mm
    captured_slot = (
        cq.Workplane("XY")
        .workplane(offset=-0.1)
        .center(0, slot_local_y)
        .rect(PUSH_ROD_THEAD_W + 0.5, 3)
        .extrude(TILT_PLATE_T / 2 + 0.1)
    )
    plate = plate.cut(captured_slot)

    return plate
```

- [ ] **Step 2: Add display call**

After the UH tilt plate display call at the bottom of the file, add:

```python
r1_tilt_plate = build_r1_tilt_plate()
_r1_plate_assembly = r1_tilt_plate.translate((
    SLOT_POSITIONS["r1_ring"][0],
    SLOT_POSITIONS["r1_ring"][1],
    STAND_H - R1_CRADLE_DEPTH
))
show_object(_r1_plate_assembly, name="r1_tilt_plate",
            options={"color": (0.6, 0.85, 0.6, 0.9)})
pass  # keep loop body after show_object is stripped by export script
```

- [ ] **Step 3: Verify the design loads**

Run:
```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py
```
Expected: `✅ Design objects loaded successfully`

- [ ] **Step 4: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add R1 Ring tilt plate build function"
```

---

### Task 4: Build Omi Tilt Plate Function

**Files:**
- Modify: `designs/v1-charging-stand.py` — add `build_omi_tilt_plate()` after `build_r1_tilt_plate()`

- [ ] **Step 1: Add the `build_omi_tilt_plate()` function**

Insert immediately after `build_r1_tilt_plate()`:

```python
def build_omi_tilt_plate():
    """Omi DevKit 2 tilt plate — six-sided diamond with vertex fillets.

    Built at origin (centered on X/Y, Z=0 to TILT_PLATE_T).
    Uses the same six_sided_diamond_points() helper as the pocket.
    Hinge barrels at the rearmost vertex (+Y), with a small flat added.
    Captured slot on underside for push rod T-head.
    """
    # Diamond points with clearance reduction
    plate_long = OMI_LONG_EDGE + TOL * 2 - TILT_CLEARANCE * 2   # 29mm
    plate_short = OMI_SHORT_EDGE + TOL * 2 - TILT_CLEARANCE * 2  # 14.5mm (approx)
    pts = six_sided_diamond_points(plate_long, plate_short)
    pts_closed = pts + [pts[0]]

    # ── Main diamond plate ───────────────────────────────────────────────
    plate = (
        cq.Workplane("XY")
        .polyline(pts_closed)
        .close()
        .extrude(TILT_PLATE_T)
    )
    plate = plate.edges("|Z").fillet(OMI_VERTEX_R - TILT_CLEARANCE)

    # ── Find the rearmost vertex (max Y) for barrel placement ────────────
    rear_y = max(p[1] for p in pts)  # rearmost Y coordinate

    # Add a small flat at the rear vertex to mount barrels.
    # Cut 2mm off the rear to create a flat surface.
    _chord_cut_y = rear_y - 2
    chord_cut = (
        cq.Workplane("XY")
        .workplane(offset=-0.1)
        .center(0, _chord_cut_y + 10)
        .rect(50, 20)  # wide enough to span the diamond
        .extrude(TILT_PLATE_T + 0.2)
    )
    plate = plate.cut(chord_cut)

    # ── Two hinge barrels on the flat ────────────────────────────────────
    barrel_spacing = 8
    barrel_center_y = _chord_cut_y + HINGE_BARREL_PROTRUDE - HINGE_BARREL_OD / 2

    for x_sign in [-1, 1]:
        bx = x_sign * barrel_spacing / 2
        barrel = (
            cq.Workplane("YZ")
            .workplane(offset=bx - HINGE_BARREL_L / 2)
            .center(barrel_center_y, TILT_PLATE_T / 2)
            .circle(HINGE_BARREL_OD / 2)
            .extrude(HINGE_BARREL_L)
        )
        bore = (
            cq.Workplane("YZ")
            .workplane(offset=bx - HINGE_BARREL_L / 2 - 0.5)
            .center(barrel_center_y, TILT_PLATE_T / 2)
            .circle(HINGE_BARREL_ID / 2)
            .extrude(HINGE_BARREL_L + 1)
        )
        plate = plate.union(barrel).cut(bore)

    # ── Captured slot on underside ───────────────────────────────────────
    slot_local_y = SERVO_Y - FRONT_ROW_Y  # 12.5mm
    captured_slot = (
        cq.Workplane("XY")
        .workplane(offset=-0.1)
        .center(0, slot_local_y)
        .rect(PUSH_ROD_THEAD_W + 0.5, 3)
        .extrude(TILT_PLATE_T / 2 + 0.1)
    )
    plate = plate.cut(captured_slot)

    return plate
```

- [ ] **Step 2: Add display call**

After the R1 tilt plate display call at the bottom of the file, add:

```python
omi_tilt_plate = build_omi_tilt_plate()
_omi_plate_assembly = omi_tilt_plate.translate((
    SLOT_POSITIONS["omi"][0],
    SLOT_POSITIONS["omi"][1],
    STAND_H - OMI_CRADLE_DEPTH
))
show_object(_omi_plate_assembly, name="omi_tilt_plate",
            options={"color": (0.6, 0.85, 0.6, 0.9)})
pass  # keep loop body after show_object is stripped by export script
```

- [ ] **Step 3: Verify the design loads**

Run:
```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py
```
Expected: `✅ Design objects loaded successfully`

- [ ] **Step 4: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add Omi tilt plate build function"
```

---

### Task 5: Build Push Rod Function (4 variants)

**Files:**
- Modify: `designs/v1-charging-stand.py` — add `build_push_rod()` after the tilt plate functions

- [ ] **Step 1: Add the `build_push_rod()` function**

Insert after `build_omi_tilt_plate()`:

```python
def build_push_rod(length, top_type="thead"):
    """Push rod connecting servo horn to tilt plate or Mudra pole.

    Built at origin: rod extends from Z=0 upward to Z=length.
    Top end has either a T-head (for tilt plates) or a flat pad (for Mudra).
    Bottom end has a flat tab with a hole for the servo horn screw.

    Args:
        length: rod length in mm (Z extent, excluding top/bottom attachments)
        top_type: "thead" for tilt plate captured slot, "pad" for Mudra flat pad
    """
    # ── Main rod body ────────────────────────────────────────────────────
    rod = (
        cq.Workplane("XY")
        .rect(PUSH_ROD_W, PUSH_ROD_W)
        .extrude(length)
    )

    # ── Top attachment ───────────────────────────────────────────────────
    if top_type == "thead":
        # T-head: wider cross-piece that sits in the captured slot
        thead = (
            cq.Workplane("XY")
            .workplane(offset=length)
            .rect(PUSH_ROD_THEAD_W, PUSH_ROD_W)
            .extrude(PUSH_ROD_THEAD_H)
        )
        rod = rod.union(thead)
    elif top_type == "pad":
        # Flat pad for Mudra pole — presses against pole base
        pad = (
            cq.Workplane("XY")
            .workplane(offset=length)
            .rect(PUSH_ROD_PAD_W, PUSH_ROD_PAD_W)
            .extrude(PUSH_ROD_PAD_H)
        )
        rod = rod.union(pad)

    # ── Bottom attachment — horn tab ─────────────────────────────────────
    # Flat tab extending downward with a hole for the servo horn screw
    horn_tab = (
        cq.Workplane("XY")
        .workplane(offset=-PUSH_ROD_HORN_TAB_H)
        .rect(PUSH_ROD_HORN_TAB_W, PUSH_ROD_W)
        .extrude(PUSH_ROD_HORN_TAB_H)
    )
    # Screw hole through the tab
    horn_hole = (
        cq.Workplane("XY")
        .workplane(offset=-PUSH_ROD_HORN_TAB_H / 2)
        .center(0, 0)
        .circle(PUSH_ROD_HORN_HOLE / 2)
        .extrude(PUSH_ROD_W + 1)
    )
    # Rotate the hole to go through the tab face (Y axis)
    horn_hole = (
        cq.Workplane("XZ")
        .workplane(offset=-PUSH_ROD_W / 2 - 0.5)
        .center(0, -PUSH_ROD_HORN_TAB_H / 2)
        .circle(PUSH_ROD_HORN_HOLE / 2)
        .extrude(PUSH_ROD_W + 1)
    )
    rod = rod.union(horn_tab).cut(horn_hole)

    return rod
```

- [ ] **Step 2: Add build calls and display at the bottom of the file**

After the Omi tilt plate display call, add:

```python
# Push rods — displayed at assembly position (in push rod slots, extended)
_push_rod_configs = [
    ("uh_ring", PUSH_ROD_LEN_UH, "thead", UH_CRADLE_DEPTH),
    ("r1_ring", PUSH_ROD_LEN_R1, "thead", R1_CRADLE_DEPTH),
    ("omi", PUSH_ROD_LEN_OMI, "thead", OMI_CRADLE_DEPTH),
    ("mudra", PUSH_ROD_LEN_MUDRA, "pad", TOP_H),
]
push_rods = {}
for name, rod_len, top_type, _cradle_d in _push_rod_configs:
    rod = build_push_rod(rod_len, top_type)
    push_rods[name] = rod
    # Position: rod base at servo horn top, centered at push rod slot
    _rod_x = SLOT_POSITIONS[name][0]
    _rod_z = BASE_H + SG90_BODY_H  # top of servo body
    _rod_assembly = rod.translate((_rod_x, SERVO_Y, _rod_z))
    show_object(_rod_assembly, name=f"push_rod_{name}",
                options={"color": (0.9, 0.6, 0.2, 0.85)})
    pass  # keep loop body after show_object is stripped by export script
```

- [ ] **Step 3: Verify the design loads**

Run:
```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py
```
Expected: `✅ Design objects loaded successfully`

- [ ] **Step 4: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add push rod build function with T-head and pad variants"
```

---

### Task 6: Add Hinge Barrel Sockets to Top Tray Cradle Pockets

**Files:**
- Modify: `designs/v1-charging-stand.py` — add barrel socket cuts in `build_top_tray()` after each of the 3 cradle pocket sections (UH Ring, R1, Omi)

This task modifies the existing `build_top_tray()` function to cut semicircular hinge barrel sockets into the rear wall of each front-row cradle pocket (UH Ring at ~line 1140, R1 at ~line 1175, Omi at ~line 1219). The sockets allow the tilt plate barrels to sit in the pocket wall.

- [ ] **Step 1: Add UH Ring barrel sockets**

After the UH Ring floor pass-through cut (after `base = base.cut(uh_cable)` at ~line 1160), add:

```python
    # ── Hinge barrel sockets in rear (+Y) wall ───────────────────────────
    # Two semicircular channels in the pocket's rear wall for tilt plate
    # hinge barrels. Filament pin threads through barrels + sockets.
    _uh_plate_side = UH_SIDE - TILT_CLEARANCE * 2  # 40mm
    _uh_barrel_spacing = _uh_plate_side - 2 * 10  # 20mm
    _uh_rear_y = uy + UH_SIDE / 2  # rear wall Y position (-29.0)
    _uh_socket_z = STAND_H - UH_CRADLE_DEPTH  # pocket floor Z (48.0)
    _socket_od = HINGE_BARREL_OD + HINGE_SOCKET_TOL * 2  # 3.6mm
    _socket_len = HINGE_BARREL_L + HINGE_SOCKET_TOL * 2  # 8.6mm

    for x_sign in [-1, 1]:
        _bx = ux + x_sign * _uh_barrel_spacing / 2
        barrel_socket = (
            cq.Workplane("YZ")
            .workplane(offset=_bx - _socket_len / 2)
            .center(_uh_rear_y, _uh_socket_z + TILT_PLATE_T / 2)
            .circle(_socket_od / 2)
            .extrude(_socket_len)
        )
        base = base.cut(barrel_socket)
```

- [ ] **Step 2: Add R1 Ring barrel sockets**

After the R1 floor pass-through cut (after `base = base.cut(r1_cable)` at ~line 1198), add:

```python
    # ── Hinge barrel sockets in rear (+Y) wall ───────────────────────────
    _r1_plate_dia = R1_DIA - TILT_CLEARANCE * 2  # 31mm
    _r1_chord_cut_y = _r1_plate_dia / 2 - 2  # 13.5mm from plate center
    _r1_rear_y = ry + _r1_chord_cut_y  # world Y of barrel center
    _r1_socket_z = STAND_H - R1_CRADLE_DEPTH  # pocket floor Z (48.0)
    _r1_barrel_spacing = 8  # matches plate barrel spacing

    for x_sign in [-1, 1]:
        _bx = rx + x_sign * _r1_barrel_spacing / 2
        barrel_socket = (
            cq.Workplane("YZ")
            .workplane(offset=_bx - _socket_len / 2)
            .center(_r1_rear_y, _r1_socket_z + TILT_PLATE_T / 2)
            .circle(_socket_od / 2)
            .extrude(_socket_len)
        )
        base = base.cut(barrel_socket)
```

- [ ] **Step 3: Add Omi barrel sockets**

After the Omi floor pass-through cut (after `base = base.cut(omi_cable)` at ~line 1257), add:

```python
    # ── Hinge barrel sockets in rear (+Y) wall ───────────────────────────
    _omi_pts = six_sided_diamond_points(
        OMI_LONG_EDGE + TOL * 2 - TILT_CLEARANCE * 2,
        OMI_SHORT_EDGE + TOL * 2 - TILT_CLEARANCE * 2
    )
    _omi_rear_y_local = max(p[1] for p in _omi_pts)
    _omi_chord_cut_y = _omi_rear_y_local - 2
    _omi_rear_y = oy + _omi_chord_cut_y  # world Y of barrel center
    _omi_socket_z = STAND_H - OMI_CRADLE_DEPTH  # pocket floor Z (43.0)
    _omi_barrel_spacing = 8  # matches plate barrel spacing

    for x_sign in [-1, 1]:
        _bx = ox + x_sign * _omi_barrel_spacing / 2
        barrel_socket = (
            cq.Workplane("YZ")
            .workplane(offset=_bx - _socket_len / 2)
            .center(_omi_rear_y, _omi_socket_z + TILT_PLATE_T / 2)
            .circle(_socket_od / 2)
            .extrude(_socket_len)
        )
        base = base.cut(barrel_socket)
```

- [ ] **Step 4: Verify the design loads**

Run:
```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py
```
Expected: `✅ Design objects loaded successfully`

- [ ] **Step 5: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add hinge barrel sockets to UH, R1, and Omi cradle pockets"
```

---

### Task 7: Add Ghost Visualization for Tilt Plates and Push Rods

**Files:**
- Modify: `designs/v1-charging-stand.py` — add ghost overlays in `build_ghost_components()` function (after ~line 1793, before `return parts`)

- [ ] **Step 1: Add tilt plate and push rod ghosts to `build_ghost_components()`**

Before `return parts` in `build_ghost_components()`, add:

```python
    # ── Tilt plates (shown tilted ~15° for visual preview) ───────────────
    # Show plates partially tilted so you can see the mechanism concept.
    _tilt_preview_angle = 15  # degrees, partial tilt for preview

    # UH Ring tilt plate ghost
    _uh_plate = build_uh_tilt_plate()
    _uh_hinge_y = SLOT_POSITIONS["uh_ring"][1] + (UH_SIDE - TILT_CLEARANCE * 2) / 2
    _uh_hinge_z = STAND_H - UH_CRADLE_DEPTH + TILT_PLATE_T / 2
    _uh_plate_pos = _uh_plate.translate((
        SLOT_POSITIONS["uh_ring"][0],
        SLOT_POSITIONS["uh_ring"][1],
        STAND_H - UH_CRADLE_DEPTH
    ))
    _uh_plate_tilted = _uh_plate_pos.rotate(
        (SLOT_POSITIONS["uh_ring"][0], _uh_hinge_y, _uh_hinge_z),
        (SLOT_POSITIONS["uh_ring"][0] + 1, _uh_hinge_y, _uh_hinge_z),
        -_tilt_preview_angle
    )
    parts["tilt_plate_uh"] = (_uh_plate_tilted, (0.4, 0.8, 0.4, 0.6))

    # R1 Ring tilt plate ghost
    _r1_plate = build_r1_tilt_plate()
    _r1_chord_y = (R1_DIA - TILT_CLEARANCE * 2) / 2 - 2
    _r1_hinge_y = SLOT_POSITIONS["r1_ring"][1] + _r1_chord_y
    _r1_hinge_z = STAND_H - R1_CRADLE_DEPTH + TILT_PLATE_T / 2
    _r1_plate_pos = _r1_plate.translate((
        SLOT_POSITIONS["r1_ring"][0],
        SLOT_POSITIONS["r1_ring"][1],
        STAND_H - R1_CRADLE_DEPTH
    ))
    _r1_plate_tilted = _r1_plate_pos.rotate(
        (SLOT_POSITIONS["r1_ring"][0], _r1_hinge_y, _r1_hinge_z),
        (SLOT_POSITIONS["r1_ring"][0] + 1, _r1_hinge_y, _r1_hinge_z),
        -_tilt_preview_angle
    )
    parts["tilt_plate_r1"] = (_r1_plate_tilted, (0.4, 0.8, 0.4, 0.6))

    # Omi tilt plate ghost
    _omi_plate = build_omi_tilt_plate()
    _omi_pts_ghost = six_sided_diamond_points(
        OMI_LONG_EDGE + TOL * 2 - TILT_CLEARANCE * 2,
        OMI_SHORT_EDGE + TOL * 2 - TILT_CLEARANCE * 2
    )
    _omi_rear_local = max(p[1] for p in _omi_pts_ghost) - 2
    _omi_hinge_y = SLOT_POSITIONS["omi"][1] + _omi_rear_local
    _omi_hinge_z = STAND_H - OMI_CRADLE_DEPTH + TILT_PLATE_T / 2
    _omi_plate_pos = _omi_plate.translate((
        SLOT_POSITIONS["omi"][0],
        SLOT_POSITIONS["omi"][1],
        STAND_H - OMI_CRADLE_DEPTH
    ))
    _omi_plate_tilted = _omi_plate_pos.rotate(
        (SLOT_POSITIONS["omi"][0], _omi_hinge_y, _omi_hinge_z),
        (SLOT_POSITIONS["omi"][0] + 1, _omi_hinge_y, _omi_hinge_z),
        -_tilt_preview_angle
    )
    parts["tilt_plate_omi"] = (_omi_plate_tilted, (0.4, 0.8, 0.4, 0.6))

    # ── Push rods (shown in extended/up position) ────────────────────────
    _rod_configs = [
        ("uh_ring", PUSH_ROD_LEN_UH, "thead"),
        ("r1_ring", PUSH_ROD_LEN_R1, "thead"),
        ("omi", PUSH_ROD_LEN_OMI, "thead"),
        ("mudra", PUSH_ROD_LEN_MUDRA, "pad"),
    ]
    for name, rod_len, top_type in _rod_configs:
        _rod = build_push_rod(rod_len, top_type)
        _rod_x = SLOT_POSITIONS[name][0]
        _rod_z = BASE_H + SG90_BODY_H
        _rod_pos = _rod.translate((_rod_x, SERVO_Y, _rod_z))
        parts[f"push_rod_{name}"] = (_rod_pos, (0.9, 0.6, 0.2, 0.5))
```

- [ ] **Step 2: Verify the design loads**

Run:
```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py
```
Expected: `✅ Design objects loaded successfully`

- [ ] **Step 3: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add ghost visualization for tilt plates (tilted) and push rods"
```

---

### Task 8: Update Export Script for New Parts

**Files:**
- Modify: `export_charging_stand.py` — add exports for 3 tilt plates + 4 push rods

- [ ] **Step 1: Add new part extraction from exec_globals**

In `export_stl_files()`, after the line `mudra_pole = exec_globals.get('mudra_pole')` (~line 44), add:

```python
        uh_tilt_plate = exec_globals.get('uh_tilt_plate')
        r1_tilt_plate = exec_globals.get('r1_tilt_plate')
        omi_tilt_plate = exec_globals.get('omi_tilt_plate')
        push_rods = exec_globals.get('push_rods', {})
```

- [ ] **Step 2: Add Z=0 translation for tilt plates and push rods**

After the Mudra pole translation section (~line 82), add:

```python
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
```

- [ ] **Step 3: Add STL/STEP export calls**

Inside the `try` block, after the Mudra pole export section (~line 133), add:

```python
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
```

- [ ] **Step 4: Verify the full export pipeline**

Run:
```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py
```
Expected: All existing exports succeed plus 7 new tilt plate STLs + 7 STEP files + 4 push rod STLs + 4 STEP files.

- [ ] **Step 5: Commit**

```bash
git add export_charging_stand.py
git commit -m "feat: add tilt plate and push rod exports to export script"
```

---

### Task 9: Push to GitHub and Restart cadquery-server

**Files:**
- No file changes — deployment only

- [ ] **Step 1: Push all commits**

```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && git push
```

- [ ] **Step 2: Restart cadquery-server to pick up changes**

```bash
kubectl rollout restart deployment cadquery-server -n utilities
```

- [ ] **Step 3: Verify rollout completes**

```bash
kubectl rollout status deployment cadquery-server -n utilities --timeout=120s
```
Expected: `deployment "cadquery-server" successfully rolled out`
