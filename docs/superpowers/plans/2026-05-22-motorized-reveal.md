# Motorized Wearable Reveal System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add 4x SG90 servo mounts, QuinLED-Dig-Uno controller, updated ESP32 slot-cradle mount, proximity sensor, servo wiring channels, push rod slots, and ghost visualization objects to the charging stand CAD model.

**Architecture:** All geometry changes happen in the single `designs/v1-charging-stand.py` file — constants section, `build_bottom_tray()`, `build_top_tray()`, and a new `build_ghost_components()` function. Old constants and geometry (driver pocket, ESP32 standoffs) are replaced inline. The export script (`export_charging_stand.py`) needs no changes since it exports the same 4 printable parts.

**Tech Stack:** CadQuery (Python), cadquery-server for live preview

---

## File Structure

| File | Responsibility | Action |
|------|---------------|--------|
| `designs/v1-charging-stand.py` | All CadQuery geometry + constants | Modify: update constants (lines 134-162), modify `build_bottom_tray()` (lines 513-708), modify cable post loop (lines 418-456), add servo mounts + wiring, modify `build_top_tray()` (add push rod slots), add `build_ghost_components()`, update display section |
| `CLAUDE.md` | Project documentation | Modify: add motorized reveal, QuinLED, sensor, ghost objects to Architecture section |

---

### Task 1: Update Constants — Remove Old, Add New

**Files:**
- Modify: `designs/v1-charging-stand.py:134-162`

This task replaces the old ESP32 standoff + driver pocket constants with new servo, QuinLED, slot-cradle ESP32, proximity sensor, and wiring channel constants. The old constants (`DRIVER_L`, `DRIVER_W`, `DRIVER_H`, `DRIVER_STANDOFF_H`, `DRIVER_STANDOFF_D`, `ESP32_STANDOFF_H`, `ESP32_STANDOFF_D`) are deleted. `ESP32_L`, `ESP32_W`, and `ESP32_H` are updated to new values for the pin-header board.

- [x] **Step 1: Replace the ESP32 constants block**

In `designs/v1-charging-stand.py`, find the block at lines 134-143:

```python
# --- ESP32 DevKitC V4 mount ---
ESP32_L = 55 + 1          # board length + tolerance (along Y)
ESP32_W = 28 + 1          # board width + tolerance (along X)
ESP32_H = 12              # board height (tallest component)
ESP32_STANDOFF_H = 2      # standoff post height
ESP32_STANDOFF_D = 3      # standoff post diameter
ESP32_CRADLE_H = 6        # cradle wall height
ESP32_CRADLE_T = 1.5      # cradle wall thickness
ESP32_USB_SLOT_W = 12     # USB port slot width through front wall
ESP32_USB_SLOT_H = 8      # USB port slot height through front wall
```

Replace with:

```python
# --- ESP32 DevKitC V4 mount (pin-header slot-cradle) ---
ESP32_L = 56              # board length + tolerance (along Y)
ESP32_W = 29              # board width + tolerance (along X)
ESP32_H = 23              # total height with pin headers
ESP32_PIN_H = 8.5         # pin header length below PCB
ESP32_RAIL_H = 10         # slot-cradle rail height
ESP32_RAIL_W = 5          # rail width
ESP32_RAIL_PITCH = 25.4   # center-to-center of rail grooves (0.1" header pitch)
ESP32_GROOVE_W = 3.5      # groove width (2.54mm header + 1mm tolerance)
ESP32_GROOVE_D = 8.5      # groove depth (full pin length)
ESP32_CRADLE_H = 6        # cradle wall height (above rail top)
ESP32_CRADLE_T = 1.5      # cradle wall thickness
ESP32_USB_SLOT_W = 12     # USB port slot width through front wall
ESP32_USB_SLOT_H = 8      # USB port slot height through front wall
```

- [x] **Step 2: Replace the driver pocket constants with QuinLED + new feature constants**

Find the block at lines 157-162:

```python
# --- LED driver / level shifter mount ---
DRIVER_L = 22             # pocket length (Y)
DRIVER_W = 16             # pocket width (X)
DRIVER_H = 8              # pocket depth (Z)
DRIVER_STANDOFF_H = 2     # standoff height
DRIVER_STANDOFF_D = 2     # standoff diameter
```

Replace with:

```python
# --- QuinLED-Dig-Uno mount (WLED controller, replaces old driver pocket) ---
QLED_W = 50               # board width (X)
QLED_D = 50               # board depth (Y)
QLED_H = 30               # board height (Z, tallest component)
QLED_STANDOFF_H = 3       # standoff post height
QLED_STANDOFF_D = 3       # standoff post diameter
QLED_MOUNT_INSET = 4      # M2 hole inset from board edge
QLED_MOUNT_PITCH = 42     # M2 hole spacing (50 - 2*4)
QLED_CRADLE_H = 8         # cradle wall height
QLED_CRADLE_T = 1.5       # cradle wall thickness

# --- SG90 micro servo mount (4x) ---
SG90_BODY_L = 23          # body length (X)
SG90_BODY_W = 12.2        # body width (Y)
SG90_BODY_H = 22.7        # body height (Z, not including shaft)
SG90_EAR_W = 32.4         # total width with mounting ears
SG90_EAR_T = 2.5          # ear thickness (Z)
SG90_SHAFT_H = 4          # shaft + horn height above body
SG90_SCREW_SPACING = 27.5 # distance between M2 screw holes on ears
SG90_SCREW_D = 2          # M2 screw hole diameter
SERVO_Y = -37             # Y position for all servo mounts
SERVO_POCKET_W = 34       # pocket width (ears + tolerance)
SERVO_POCKET_D = 14       # pocket depth in Y (body + tolerance)
SERVO_POCKET_H = 5        # pocket depth in Z (into floor)
SERVO_POST_H = 5          # screw post height
SERVO_POST_OD = 2.5       # screw post outer diameter
SERVO_PILOT_D = 1.0       # pilot hole for M2 self-tapping

# --- Push rod slots (top tray) ---
PUSH_ROD_SLOT_W = 4       # slot width (X)
PUSH_ROD_SLOT_L = 12      # slot length (Y)

# --- VL53L0X proximity sensor ---
PROX_W = 13               # sensor board width (X)
PROX_D = 18               # sensor board depth (Y)
PROX_H = 3                # sensor board height (Z)
PROX_CLIP_H = 5           # clip bracket height
PROX_CLIP_T = 1.5         # clip bracket thickness
PROX_WINDOW_W = 8         # window width through front wall
PROX_WINDOW_H = 6         # window height through front wall

# --- Servo wiring channels ---
SERVO_WIRE_W = 8          # servo wire channel width
SERVO_WIRE_D = 4          # servo wire channel depth
```

- [x] **Step 3: Verify the design still builds**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py`

Expected: Build will FAIL because `build_bottom_tray()` still references `ESP32_STANDOFF_H`, `ESP32_STANDOFF_D`, `DRIVER_L`, `DRIVER_W`, etc. This is expected — the next tasks replace those code references.

Note the specific error (e.g. `NameError: name 'ESP32_STANDOFF_H' is not defined`) to confirm the constants removal was clean.

- [x] **Step 4: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "refactor: replace ESP32/driver constants with servo, QuinLED, sensor, slot-cradle constants

Remove DRIVER_L/W/H, DRIVER_STANDOFF_H/D, ESP32_STANDOFF_H/D.
Add SG90 servo, QuinLED-Dig-Uno, VL53L0X sensor, push rod,
servo wiring, and ESP32 pin-header slot-cradle constants.

Note: build_bottom_tray() will fail until the geometry code is
updated in subsequent commits to use the new constants."
```

---

### Task 2: Replace ESP32 Mount — Standoffs to Slot-Cradle

**Files:**
- Modify: `designs/v1-charging-stand.py:513-566` (ESP32 mount section in `build_bottom_tray()`)

The old ESP32 mount uses 4 screw standoff posts that reference the now-deleted `ESP32_STANDOFF_H` and `ESP32_STANDOFF_D` constants. Replace with a slot-cradle design: two parallel raised rails with grooves for pin headers. Also update the USB port slot Z position for the taller board.

- [x] **Step 1: Replace the ESP32 mount code**

In `designs/v1-charging-stand.py`, find the ESP32 mount section (lines 513-566). Replace the entire block from the comment `# ── ESP32 DevKitC V4 mount` through the USB port slot code (ending at `tray = tray.cut(esp_usb_slot)` on line 566) with:

```python
    # ── ESP32 DevKitC V4 mount (front-left corner, slot-cradle) ──────────
    # Board with pre-soldered pin headers rides in grooved rails.
    # Long edge along Y (56mm), short edge (29mm, USB port) faces front wall.
    # Pin headers sit in grooves; board slides in from the rear (+Y).
    _esp_x = -STAND_W / 2 + WALL + ESP32_W / 2   # center X = -105.5mm
    _esp_y = -STAND_D / 2 + WALL + ESP32_L / 2   # center Y = -57mm

    # Two parallel rails with grooves for pin headers
    for rail_sign in [-1, 1]:  # -1 = left rail, +1 = right rail
        rail_x = _esp_x + rail_sign * (ESP32_RAIL_PITCH / 2)

        # Solid rail body
        rail = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H)
            .center(rail_x, _esp_y)
            .rect(ESP32_RAIL_W, ESP32_L)
            .extrude(ESP32_RAIL_H)
        )
        tray = tray.union(rail)

        # Groove cut into the inner face of each rail
        # Groove faces inward (toward the board center)
        groove_x = rail_x - rail_sign * (ESP32_RAIL_W / 2 - ESP32_GROOVE_W / 2)
        groove = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H + (ESP32_RAIL_H - ESP32_GROOVE_D))
            .center(groove_x, _esp_y)
            .rect(ESP32_GROOVE_W, ESP32_L + 1)  # +1 so rear end is open for insertion
            .extrude(ESP32_GROOVE_D + 0.5)
        )
        tray = tray.cut(groove)

        # Retaining tab at front end of groove (prevents board sliding out)
        tab_y = _esp_y - ESP32_L / 2
        tab = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H + (ESP32_RAIL_H - ESP32_GROOVE_D))
            .center(groove_x, tab_y)
            .rect(ESP32_GROOVE_W, 2)
            .extrude(2)  # 2mm tall bump
        )
        tray = tray.union(tab)

    # Cradle wall — left side (against the left inner wall, above rail top)
    cradle_left = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H + ESP32_RAIL_H)
        .center(_esp_x - ESP32_W / 2 - ESP32_CRADLE_T / 2, _esp_y)
        .rect(ESP32_CRADLE_T, ESP32_L)
        .extrude(ESP32_CRADLE_H)
    )
    tray = tray.union(cradle_left)

    # Cradle wall — front side (against the front inner wall, above rail top)
    cradle_front = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H + ESP32_RAIL_H)
        .center(_esp_x, _esp_y - ESP32_L / 2 - ESP32_CRADLE_T / 2)
        .rect(ESP32_W, ESP32_CRADLE_T)
        .extrude(ESP32_CRADLE_H)
    )
    tray = tray.union(cradle_front)

    # USB port slot through the front wall (repositioned for taller board)
    _usb_z = BASE_H + ESP32_RAIL_H + 4   # center of USB port on raised board
    esp_usb_slot = (
        cq.Workplane("XY")
        .workplane(offset=_usb_z - ESP32_USB_SLOT_H / 2)
        .center(_esp_x, -STAND_D / 2)
        .rect(ESP32_USB_SLOT_W, WALL * 3)
        .extrude(ESP32_USB_SLOT_H)
    )
    tray = tray.cut(esp_usb_slot)
```

- [x] **Step 2: Verify syntax is valid**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 -c "import ast; ast.parse(open('designs/v1-charging-stand.py').read()); print('Syntax OK')"`

Expected: `Syntax OK` (syntax check only — runtime will still fail because driver pocket code references deleted constants)

- [x] **Step 3: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: replace ESP32 standoff posts with pin-header slot-cradle mount

Two parallel raised rails with grooves for 0.1-inch pin headers.
Board slides in from rear, retaining tabs at front prevent sliding out.
Cradle walls provide lateral support above PCB level.
USB port slot repositioned higher for raised board position."
```

---

### Task 3: Replace Driver Pocket with QuinLED-Dig-Uno Mount

**Files:**
- Modify: `designs/v1-charging-stand.py:568-593` (driver pocket section in `build_bottom_tray()`)
- Modify: `designs/v1-charging-stand.py:418-456` (cable post loop — skip posts that overlap QuinLED)

The old driver pocket (22x16mm behind the ESP32) is removed entirely. A new QuinLED-Dig-Uno mount (50x50mm) goes in the front-right corner (mirroring ESP32 on front-left). The cable winding post loop on the right side must skip posts where Y < -35 (they overlap the QuinLED footprint).

- [x] **Step 1: Replace the driver pocket code with QuinLED mount code**

Find the driver pocket section (lines 568-593 — from comment `# ── LED driver / level shifter pocket` through the second `tray = tray.union(drv_standoff)`). Replace with:

```python
    # ── QuinLED-Dig-Uno WLED controller mount (front-right corner) ───────
    # 50x50mm PCB mirrors the ESP32 position on the opposite side.
    # Has onboard level shifting — replaces the old separate driver pocket.
    _qled_x = STAND_W / 2 - WALL - QLED_W / 2    # center X = +92.5mm
    _qled_y = -STAND_D / 2 + WALL + QLED_D / 2   # center Y = -60mm

    # 4 standoff posts at M2 mounting hole positions
    for qx_sign, qy_sign in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        qled_standoff = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H)
            .center(
                _qled_x + qx_sign * (QLED_MOUNT_PITCH / 2),
                _qled_y + qy_sign * (QLED_MOUNT_PITCH / 2),
            )
            .circle(QLED_STANDOFF_D / 2)
            .extrude(QLED_STANDOFF_H)
        )
        tray = tray.union(qled_standoff)

    # Cradle wall — right side (against the right inner wall)
    qled_cradle_right = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .center(_qled_x + QLED_W / 2 + QLED_CRADLE_T / 2, _qled_y)
        .rect(QLED_CRADLE_T, QLED_D)
        .extrude(QLED_CRADLE_H)
    )
    tray = tray.union(qled_cradle_right)

    # Cradle wall — front side (against the front inner wall)
    qled_cradle_front = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .center(_qled_x, _qled_y - QLED_D / 2 - QLED_CRADLE_T / 2)
        .rect(QLED_W, QLED_CRADLE_T)
        .extrude(QLED_CRADLE_H)
    )
    tray = tray.union(qled_cradle_front)
```

- [x] **Step 2: Update the cable post loop to skip posts overlapping QuinLED**

Find the cable post loop at lines 418-456. The loop iterates `for side_sign in [-1, 1]` and inside creates column 1 and column 2 posts. The right side (side_sign == +1) has posts at X=99 and X=113, running from Y=-73 to Y=73.

The QuinLED sits at X=67.5 to 117.5, Y=-85 to -35. Posts on the right side (side_sign == +1) at Y < -35 overlap.

Inside the `while _y < _pocket_y_end:` loops for both column 1 and column 2, add a skip condition. Change both column post loops from:

```python
        # ── Column 1 posts (inner loom column) ──
        _y = _pocket_y_start
        _col1_ys = []
        while _y < _pocket_y_end:
            _col1_ys.append(_y)
            post = (
                cq.Workplane("XY")
                .workplane(offset=BASE_H)
                .center(col1_x, _y)
                .circle(_post_dia / 2)
                .extrude(_post_h)
            )
            tray = tray.union(post)
            _y += _post_spacing_y
```

to:

```python
        # ── Column 1 posts (inner loom column) ──
        _y = _pocket_y_start
        _col1_ys = []
        while _y < _pocket_y_end:
            # Skip posts that overlap the QuinLED footprint (right side, Y < -35)
            if side_sign == 1 and _y < -35:
                _y += _post_spacing_y
                continue
            _col1_ys.append(_y)
            post = (
                cq.Workplane("XY")
                .workplane(offset=BASE_H)
                .center(col1_x, _y)
                .circle(_post_dia / 2)
                .extrude(_post_h)
            )
            tray = tray.union(post)
            _y += _post_spacing_y
```

Apply the same skip condition to the Column 2 loop (lines 443-456):

```python
        # ── Column 2 posts (outer loom column, staggered) ──
        _y = _pocket_y_start + _post_spacing_y / 2
        _col2_ys = []
        while _y < _pocket_y_end:
            # Skip posts that overlap the QuinLED footprint (right side, Y < -35)
            if side_sign == 1 and _y < -35:
                _y += _post_spacing_y
                continue
            _col2_ys.append(_y)
            post = (
                cq.Workplane("XY")
                .workplane(offset=BASE_H)
                .center(col2_x, _y)
                .circle(_post_dia / 2)
                .extrude(_post_h)
            )
            tray = tray.union(post)
            _y += _post_spacing_y
```

- [x] **Step 3: Update the wiring groove that connected ESP32 → old driver pocket**

Find the wiring grooves section (lines 671-708). The first groove (`wire_esp_to_drv`, lines 678-686) connected the ESP32 to the old driver pocket at `_drv_y`. Replace the ESP32→driver groove with an ESP32→QuinLED floor groove instead. The wire routes from ESP32 (X=-105.5, Y=-57) rightward along X to the charger bay edge, then continues to QuinLED (X=92.5, Y=-60).

Replace the three grooves (lines 678-708) with:

```python
    # Groove 1: ESP32 → charger bay (USB power cable from VanBon)
    # Runs from ESP32 position rightward (+X) to the charger bay left edge
    wire_esp_to_charger = (
        cq.Workplane("XY")
        .workplane(offset=_wire_z)
        .center((_esp_x + _charger_left) / 2, _esp_y)
        .rect(abs(_charger_left - _esp_x) + ESP32_W / 2, _wire_w)
        .extrude(_wire_d + 0.5)
    )
    tray = tray.cut(wire_esp_to_charger)

    # Groove 2: ESP32 → left wall LED channel start (data wire to LED strip)
    _led_ch_x = _inner_left + _ch_inset + LED_CHANNEL_W / 2
    wire_esp_to_led = (
        cq.Workplane("XY")
        .workplane(offset=_wire_z)
        .center((_esp_x + _led_ch_x) / 2, _esp_y)
        .rect(abs(_esp_x - _led_ch_x) + ESP32_W / 2 + LED_CHANNEL_W / 2, _wire_w)
        .extrude(_wire_d + 0.5)
    )
    tray = tray.cut(wire_esp_to_led)

    # Groove 3: QuinLED → right wall LED channel start
    _led_ch_right_x = _inner_right - _ch_inset - LED_CHANNEL_W / 2
    wire_qled_to_led = (
        cq.Workplane("XY")
        .workplane(offset=_wire_z)
        .center((_qled_x + _led_ch_right_x) / 2, _qled_y)
        .rect(abs(_led_ch_right_x - _qled_x) + QLED_W / 2 + LED_CHANNEL_W / 2, _wire_w)
        .extrude(_wire_d + 0.5)
    )
    tray = tray.cut(wire_qled_to_led)

    # Groove 4: VL53L0X sensor → ESP32 (I2C wires, short run)
    wire_sensor_to_esp = (
        cq.Workplane("XY")
        .workplane(offset=_wire_z)
        .center((_esp_x + _prox_x) / 2, _esp_y)
        .rect(abs(_prox_x - _esp_x) + ESP32_W / 2 + PROX_W / 2, _wire_w)
        .extrude(_wire_d + 0.5)
    )
    tray = tray.cut(wire_sensor_to_esp)
```

Note: `_prox_x` is defined in Task 6 (proximity sensor mount). If building tasks in order, this groove will reference an undefined variable until Task 6 is complete. To avoid this, define `_prox_x` at the same position as the ESP32 center temporarily, or implement Tasks 3 and 6 in the same commit. The simpler approach: define `_prox_x` early in `build_bottom_tray()` right after `_esp_x` and `_esp_y`:

```python
    _prox_x = _esp_x + ESP32_W / 2 + 5 + PROX_W / 2   # sensor center X = -74.5mm
    _prox_y = -STAND_D / 2 + WALL + PROX_D / 2          # sensor center Y = -76mm
```

Add these two lines right after the `_esp_y` definition.

- [x] **Step 4: Verify the design builds**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py`

Expected: Build succeeds, 4 STL files + 4 STEP files exported. The bottom tray now has the QuinLED mount in the front-right corner and updated wiring grooves.

- [x] **Step 5: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: replace driver pocket with QuinLED-Dig-Uno mount (front-right corner)

50x50mm PCB mount with 4x M2 standoffs and cradle walls, mirroring
the ESP32 on the front-left. Right-side cable posts skip the QuinLED
footprint zone (Y < -35mm). Wiring grooves updated: ESP32→charger,
ESP32→left LED channel, QuinLED→right LED channel, sensor→ESP32."
```

---

### Task 4: Add 4x SG90 Servo Mounts

**Files:**
- Modify: `designs/v1-charging-stand.py` — add servo mount section in `build_bottom_tray()`, after the wiring grooves, before the logo recess

Each servo gets a rectangular pocket in the floor (ears rest on rim) and 2x M2 screw posts. All 4 servos sit at Y=-37, at the X positions of their corresponding front-row devices.

- [x] **Step 1: Add the servo mount code**

In `build_bottom_tray()`, find the logo section (comment `# ── "Somni Labs" backlit logo`). Insert the following code BEFORE that comment:

```python
    # ── SG90 servo mounts (4x, behind front-row devices) ────────────────
    # Servos sit upright in the bottom tray, shaft pointing UP (+Z).
    # Push rods extend through top tray to actuate wearable cradles.
    _servo_x_positions = [
        SLOT_POSITIONS["uh_ring"][0],   # X = -81
        SLOT_POSITIONS["r1_ring"][0],   # X = -27
        SLOT_POSITIONS["omi"][0],       # X = +27
        SLOT_POSITIONS["mudra"][0],     # X = +73
    ]

    for sx in _servo_x_positions:
        # Rectangular pocket — body drops in, ears rest on rim
        servo_pocket = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H - SERVO_POCKET_H)
            .center(sx, SERVO_Y)
            .rect(SERVO_POCKET_W, SERVO_POCKET_D)
            .extrude(SERVO_POCKET_H + 0.5)
        )
        tray = tray.cut(servo_pocket)

        # 2x M2 screw posts on the ear mounting holes
        for screw_sign in [-1, 1]:
            screw_x = sx + screw_sign * (SG90_SCREW_SPACING / 2)
            # Outer post
            screw_post = (
                cq.Workplane("XY")
                .workplane(offset=BASE_H)
                .center(screw_x, SERVO_Y)
                .circle(SERVO_POST_OD / 2)
                .extrude(SERVO_POST_H)
            )
            tray = tray.union(screw_post)

            # Pilot hole for M2 self-tapping screw
            pilot = (
                cq.Workplane("XY")
                .workplane(offset=BASE_H - 0.5)
                .center(screw_x, SERVO_Y)
                .circle(SERVO_PILOT_D / 2)
                .extrude(SERVO_POST_H + 1)
            )
            tray = tray.cut(pilot)
```

- [x] **Step 2: Verify the design builds**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py`

Expected: Build succeeds. Bottom tray now has 4 servo pockets with screw posts.

- [x] **Step 3: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add 4x SG90 servo mount pockets with M2 screw posts

Servo pockets at Y=-37, X positions matching front-row devices
(-81, -27, +27, +73). Each pocket has 34x14mm floor recess for
body + ears, with 2x M2 screw posts for mounting ears."
```

---

### Task 5: Add Servo Wiring Channels and Arch Clips

**Files:**
- Modify: `designs/v1-charging-stand.py` — add wiring channel section in `build_bottom_tray()`, after the servo mounts

The servo wire trunk runs along X at Y=-37 connecting all 4 servos. L-shaped spurs connect to the ESP32 and QuinLED. Arch clips every ~40mm hold wires in place.

- [x] **Step 1: Add the servo wiring channel code**

Insert after the servo mount code (after the last `tray = tray.cut(pilot)`), before the logo section:

```python
    # ── Servo wiring channels ────────────────────────────────────────────
    # Main trunk along X at the servo row, connecting all 4 positions.
    # Spurs connect to ESP32 (front-left) and QuinLED (front-right).
    _sw_z = BASE_H - SERVO_WIRE_D  # channel bottom

    # Main trunk: X=-81 to X=+73 at Y=-37
    _trunk_x_start = _servo_x_positions[0]   # -81
    _trunk_x_end = _servo_x_positions[-1]     # +73
    _trunk_length = _trunk_x_end - _trunk_x_start
    servo_trunk = (
        cq.Workplane("XY")
        .workplane(offset=_sw_z)
        .center((_trunk_x_start + _trunk_x_end) / 2, SERVO_Y)
        .rect(_trunk_length + SERVO_WIRE_W, SERVO_WIRE_W)
        .extrude(SERVO_WIRE_D + 0.5)
    )
    tray = tray.cut(servo_trunk)

    # ESP32 spur: from trunk at X=-81 toward ESP32 at X=-105.5, Y=-57
    # L-shaped: horizontal segment along X, then vertical segment along Y
    _spur_esp_x_mid = (_trunk_x_start + _esp_x) / 2
    spur_esp_horiz = (
        cq.Workplane("XY")
        .workplane(offset=_sw_z)
        .center(_spur_esp_x_mid, SERVO_Y)
        .rect(abs(_esp_x - _trunk_x_start) + SERVO_WIRE_W, SERVO_WIRE_W)
        .extrude(SERVO_WIRE_D + 0.5)
    )
    tray = tray.cut(spur_esp_horiz)

    spur_esp_vert = (
        cq.Workplane("XY")
        .workplane(offset=_sw_z)
        .center(_esp_x, (_esp_y + SERVO_Y) / 2)
        .rect(SERVO_WIRE_W, abs(SERVO_Y - _esp_y) + SERVO_WIRE_W)
        .extrude(SERVO_WIRE_D + 0.5)
    )
    tray = tray.cut(spur_esp_vert)

    # QuinLED spur: from trunk at X=+73 toward QuinLED at X=+92.5, Y=-60
    spur_qled_horiz = (
        cq.Workplane("XY")
        .workplane(offset=_sw_z)
        .center((_trunk_x_end + _qled_x) / 2, SERVO_Y)
        .rect(abs(_qled_x - _trunk_x_end) + SERVO_WIRE_W, SERVO_WIRE_W)
        .extrude(SERVO_WIRE_D + 0.5)
    )
    tray = tray.cut(spur_qled_horiz)

    spur_qled_vert = (
        cq.Workplane("XY")
        .workplane(offset=_sw_z)
        .center(_qled_x, (_qled_y + SERVO_Y) / 2)
        .rect(SERVO_WIRE_W, abs(SERVO_Y - _qled_y) + SERVO_WIRE_W)
        .extrude(SERVO_WIRE_D + 0.5)
    )
    tray = tray.cut(spur_qled_vert)

    # ── Servo wire arch clips along the main trunk ───────────────────────
    _sw_clip_w = 14       # arch width (same as cable clips)
    _sw_clip_h = 8        # arch height
    _sw_clip_t = 2.5      # arch wall thickness
    _sw_clip_positions_x = [-81, -54, -27, 0, 27, 50, 73]

    for clip_x in _sw_clip_positions_x:
        # Skip if too close to an existing front-row cable clip
        # (front-row clips are at _clip_y = FRONT_ROW_Y + 12 = -37.5, nearly same Y)
        # Since servo clips are at SERVO_Y = -37 and cable clips at -37.5,
        # they overlap in Y. Only add servo clip if no front-row device is
        # at this X position (front-row clips are at -81, -27, 27, 73).
        _is_device_x = any(abs(clip_x - SLOT_POSITIONS[n][0]) < 5
                           for n in ("uh_ring", "r1_ring", "omi", "mudra"))
        if _is_device_x:
            continue  # front-row cable clip already exists at this X

        arch_outer = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H)
            .center(clip_x, SERVO_Y)
            .box(_sw_clip_w + _sw_clip_t * 2, _sw_clip_t, _sw_clip_h,
                 centered=[True, True, False])
        )
        arch_inner = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H)
            .center(clip_x, SERVO_Y)
            .box(_sw_clip_w, _sw_clip_t + 2, _sw_clip_h - _sw_clip_t,
                 centered=[True, True, False])
        )
        tray = tray.union(arch_outer)
        tray = tray.cut(arch_inner)
```

- [x] **Step 2: Verify the design builds**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py`

Expected: Build succeeds. Bottom tray now has servo wire channels and arch clips along the trunk.

- [x] **Step 3: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add servo wiring channels with arch clips

Main trunk along X at Y=-37 connecting all 4 servo positions.
L-shaped spurs to ESP32 (front-left) and QuinLED (front-right).
Arch clips at midpoints between servos (skips positions where
front-row cable clips already exist)."
```

---

### Task 6: Add VL53L0X Proximity Sensor Mount and Front Wall Window

**Files:**
- Modify: `designs/v1-charging-stand.py` — add sensor bracket and window in `build_bottom_tray()`, after servo wiring, before logo

The sensor sits to the right of the ESP32 mount, against the front wall. A small window through the front wall allows the ToF laser to detect approaching hands.

- [x] **Step 1: Add the proximity sensor mount code**

Insert after the servo wire arch clips, before the logo section:

```python
    # ── VL53L0X proximity sensor mount (front wall, right of ESP32) ──────
    # ToF laser sensor for hands-free reveal activation.
    # _prox_x and _prox_y were defined at the top of build_bottom_tray().

    # Clip brackets — two walls on left and right sides of the sensor
    for clip_sign in [-1, 1]:
        clip_x = _prox_x + clip_sign * (PROX_W / 2 + PROX_CLIP_T / 2)
        prox_clip = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H)
            .center(clip_x, _prox_y)
            .rect(PROX_CLIP_T, PROX_D)
            .extrude(PROX_CLIP_H)
        )
        tray = tray.union(prox_clip)

    # Front wall window — rectangular opening for ToF laser
    _prox_window_z = BASE_H + PROX_CLIP_H / 2  # center of window
    prox_window = (
        cq.Workplane("XY")
        .workplane(offset=_prox_window_z - PROX_WINDOW_H / 2)
        .center(_prox_x, -STAND_D / 2)
        .rect(PROX_WINDOW_W, WALL * 3)
        .extrude(PROX_WINDOW_H)
    )
    tray = tray.cut(prox_window)
```

- [x] **Step 2: Verify that `_prox_x` and `_prox_y` are defined**

Check that the two lines from Task 3 Step 3 are present right after `_esp_y`:

```python
    _prox_x = _esp_x + ESP32_W / 2 + 5 + PROX_W / 2   # sensor center X = -74.5mm
    _prox_y = -STAND_D / 2 + WALL + PROX_D / 2          # sensor center Y = -76mm
```

If not present, add them now.

- [x] **Step 3: Verify the design builds**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py`

Expected: Build succeeds. Bottom tray now has sensor bracket clips and front wall window.

- [x] **Step 4: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add VL53L0X proximity sensor mount with front wall window

Two clip brackets hold sensor board by friction, front wall window
allows ToF laser to detect approaching hands. Positioned to the
right of ESP32 mount at X=-74.5, Y=-76."
```

---

### Task 7: Add Push Rod Slots in Top Tray

**Files:**
- Modify: `designs/v1-charging-stand.py` — add push rod slots in `build_top_tray()`, after snap-fit receiving slots, before cable pass-through holes

4 rectangular slots through the top tray floor allow push rods from the servos below to reach the device cradles above.

- [x] **Step 1: Add the push rod slot code**

In `build_top_tray()`, find the cable pass-through holes section (line 832, comment `# ── Cable pass-through holes`). Insert the following code BEFORE that comment, after the snap-fit lip pocket loop ends:

```python
    # ── Push rod slots (servo actuator pass-through) ─────────────────────
    # Rectangular slots through the top tray floor for servo push rods.
    # One slot per servo, positioned at the servo shaft X and SERVO_Y.
    _push_rod_devices = ["uh_ring", "r1_ring", "omi", "mudra"]
    for name in _push_rod_devices:
        px, py = SLOT_POSITIONS[name]
        push_slot = (
            cq.Workplane("XY")
            .workplane(offset=SPLIT_Z - 0.5)
            .center(px, SERVO_Y)
            .rect(PUSH_ROD_SLOT_W, PUSH_ROD_SLOT_L)
            .extrude(TOP_H + 1)
        )
        base = base.cut(push_slot)
```

- [x] **Step 2: Verify the design builds**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py`

Expected: Build succeeds. Top tray now has 4 push rod slots at the servo positions.

- [x] **Step 3: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add 4x push rod slots in top tray floor

Rectangular pass-through slots (4x12mm) at each servo position
allow push rods to actuate wearable cradles from servos below."
```

---

### Task 8: Add Ghost Visualization Objects

**Files:**
- Modify: `designs/v1-charging-stand.py` — add `build_ghost_components()` function before BUILD AND DISPLAY, update display section

The ghost function creates translucent colored boxes at each component's world-coordinate position. These overlay objects are displayed in cadquery-server for visual verification of component fit — they are NOT boolean-operated with the tray geometry.

- [x] **Step 1: Add the `build_ghost_components()` function**

Insert the following function BEFORE the `# BUILD AND DISPLAY` section (before line `bottom_tray = build_bottom_tray()`):

```python
# =============================================================================
# GHOST VISUALIZATION OBJECTS (component placement preview)
# =============================================================================

def build_ghost_components():
    """Create translucent colored boxes representing internal components.

    Returns a dict of {name: (solid, (r, g, b, alpha))} tuples.
    These overlay objects are displayed in cadquery-server for visual
    verification of component fit. They are NOT boolean-operated with
    the tray geometry.
    """
    parts = {}

    # ── ESP32 board (front-left corner) ──────────────────────────────────
    _esp_x = -STAND_W / 2 + WALL + ESP32_W / 2
    _esp_y = -STAND_D / 2 + WALL + ESP32_L / 2
    _esp_z = BASE_H + ESP32_RAIL_H  # PCB sits on top of rails
    esp32 = (
        cq.Workplane("XY")
        .workplane(offset=_esp_z)
        .center(_esp_x, _esp_y)
        .rect(28, 55)  # actual PCB size (no tolerance)
        .extrude(12)    # component height above PCB
    )
    parts["esp32"] = (esp32, (0.1, 0.35, 0.7, 0.85))

    # ── QuinLED-Dig-Uno (front-right corner) ─────────────────────────────
    _qled_x = STAND_W / 2 - WALL - QLED_W / 2
    _qled_y = -STAND_D / 2 + WALL + QLED_D / 2
    _qled_z = BASE_H + QLED_STANDOFF_H
    quinled = (
        cq.Workplane("XY")
        .workplane(offset=_qled_z)
        .center(_qled_x, _qled_y)
        .rect(50, 50)  # actual PCB size
        .extrude(QLED_H)
    )
    parts["quinled"] = (quinled, (0.15, 0.55, 0.15, 0.85))

    # ── SG90 servos (4x behind front-row devices) ───────────────────────
    _servo_names = ["uh_ring", "r1_ring", "omi", "mudra"]
    for i, name in enumerate(_servo_names):
        sx = SLOT_POSITIONS[name][0]
        # Servo body
        servo_body = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H)
            .center(sx, SERVO_Y)
            .rect(SG90_BODY_L, SG90_BODY_W)
            .extrude(SG90_BODY_H)
        )
        # Mounting ears (thin plate wider than body)
        servo_ears = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H + SG90_BODY_H - SG90_EAR_T - 5)
            .center(sx, SERVO_Y)
            .rect(SG90_EAR_W, SG90_BODY_W)
            .extrude(SG90_EAR_T)
        )
        servo = servo_body.union(servo_ears)
        parts[f"servo_{name}"] = (servo, (0.85, 0.45, 0.1, 0.8))

    # ── VL53L0X proximity sensor ─────────────────────────────────────────
    _prox_x = _esp_x + ESP32_W / 2 + 5 + PROX_W / 2
    _prox_y = -STAND_D / 2 + WALL + PROX_D / 2
    sensor = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .center(_prox_x, _prox_y)
        .rect(PROX_W, PROX_D)
        .extrude(PROX_H)
    )
    parts["vl53l0x"] = (sensor, (0.3, 0.3, 0.8, 0.85))

    # ── VanBon charger (in charger bay) ──────────────────────────────────
    gx, gy = SLOT_POSITIONS["g2_case"]
    charger = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .center(gx, gy)
        .rect(134, 68)  # actual charger size (no tolerance)
        .extrude(33)     # actual charger height
    )
    parts["vanbon_charger"] = (charger, (0.3, 0.3, 0.3, 0.5))

    # ── LED strip (U-shaped path along 3 walls) ─────────────────────────
    _inner_left = -STAND_W / 2 + WALL
    _inner_right = STAND_W / 2 - WALL
    _inner_front = -STAND_D / 2 + WALL
    _inner_back = STAND_D / 2 - WALL
    _ch_inset = 1
    _strip_w = 10   # actual LED strip width
    _strip_h = 2    # LED strip thickness
    _strip_z = BASE_H - LED_CHANNEL_D + 0.5  # sitting in channel

    # Left wall segment
    led_left = (
        cq.Workplane("XY")
        .workplane(offset=_strip_z)
        .center(_inner_left + _ch_inset + _strip_w / 2,
                (_inner_front + _inner_back) / 2)
        .rect(_strip_w, _inner_back - _inner_front)
        .extrude(_strip_h)
    )
    # Front wall segment
    led_front = (
        cq.Workplane("XY")
        .workplane(offset=_strip_z)
        .center(0, _inner_front + _ch_inset + _strip_w / 2)
        .rect(_inner_right - _inner_left, _strip_w)
        .extrude(_strip_h)
    )
    # Right wall segment
    led_right = (
        cq.Workplane("XY")
        .workplane(offset=_strip_z)
        .center(_inner_right - _ch_inset - _strip_w / 2,
                (_inner_front + _inner_back) / 2)
        .rect(_strip_w, _inner_back - _inner_front)
        .extrude(_strip_h)
    )
    led_strip = led_left.union(led_front).union(led_right)
    parts["led_strip"] = (led_strip, (0.2, 1.0, 0.3, 0.7))

    return parts
```

- [x] **Step 2: Update the BUILD AND DISPLAY section to show ghost objects**

Find the current display section (starting at `bottom_tray = build_bottom_tray()`). Add the ghost display loop after the mudra pole display:

```python
# Ghost visualization objects (translucent component overlays)
ghosts = build_ghost_components()
for comp_name, (comp_solid, comp_color) in ghosts.items():
    show_object(comp_solid, name=f"ghost_{comp_name}",
                options={"color": comp_color})
```

The complete BUILD AND DISPLAY section should now read:

```python
# =============================================================================
# BUILD AND DISPLAY
# =============================================================================

bottom_tray = build_bottom_tray()
top_tray = build_top_tray()
ipad_cover = build_ipad_cover()
mudra_pole = build_mudra_pole()

show_object(bottom_tray, name="bottom_tray",
            options={"color": (0.15, 0.15, 0.17, 0.9)})
show_object(top_tray, name="top_tray",
            options={"color": (0.2, 0.2, 0.22, 0.95)})
show_object(ipad_cover, name="ipad_cover",
            options={"color": (0.3, 0.3, 0.32, 0.9)})

# Mudra pole displayed at its assembly position (inserted into the top tray socket)
mx, my = SLOT_POSITIONS["mudra"]
mudra_pole_assembly = mudra_pole.translate((mx, my, STAND_H))
show_object(mudra_pole_assembly,
            name="mudra_pole",
            options={"color": (0.25, 0.25, 0.27, 0.95)})

# Ghost visualization objects (translucent component overlays)
ghosts = build_ghost_components()
for comp_name, (comp_solid, comp_color) in ghosts.items():
    show_object(comp_solid, name=f"ghost_{comp_name}",
                options={"color": comp_color})
```

- [x] **Step 3: Verify the design builds and ghosts appear**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py`

Expected: Build succeeds. The export script strips `show_object` calls, so ghost objects don't affect STL export. The ghost objects will be visible in cadquery-server preview after pushing.

- [x] **Step 4: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add ghost visualization objects for all internal components

build_ghost_components() creates translucent colored overlays:
ESP32 (blue), QuinLED (green), 4x SG90 servos (orange),
VL53L0X sensor (light blue), VanBon charger (dark gray),
U-shaped LED strip (bright green). Displayed in cadquery-server
for visual verification of component fit."
```

---

### Task 9: Update CLAUDE.md Documentation

**Files:**
- Modify: `CLAUDE.md`

Update the Architecture section to document the motorized reveal system, QuinLED controller, updated ESP32 mount, proximity sensor, and ghost visualization.

- [x] **Step 1: Update the Architecture section**

In `CLAUDE.md`, find the Architecture section. Replace the existing lines about ESP32 mount, LED driver pocket:

```markdown
- **ESP32 mount** — DevKitC V4 cradle in bottom tray front-left corner, USB port through front wall
```

with:

```markdown
- **ESP32 mount** — DevKitC V4 pin-header slot-cradle in bottom tray front-left corner, USB port through front wall
```

Replace:

```markdown
- **LED driver pocket** — Level shifter mount behind ESP32 for 3.3V→5V logic conversion
```

with:

```markdown
- **QuinLED-Dig-Uno mount** — WLED controller (50x50mm) in bottom tray front-right corner, onboard level shifting, drives WS2812B LED strip
- **Motorized reveal** — 4x SG90 servo mounts in bottom tray (Y=-37), push rod slots in top tray, servo wiring channels with arch clips
- **Proximity sensor** — VL53L0X ToF laser mount (front wall, right of ESP32) with front wall window for hands-free reveal activation
- **Ghost visualization** — Translucent colored component overlays in cadquery-server preview (ESP32, QuinLED, servos, sensor, charger, LED strip)
```

- [x] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with motorized reveal, QuinLED, sensor, ghost objects"
```

---

## Task Summary

| Task | Description | Key Changes |
|------|------------|-------------|
| 1 | Update constants | Remove old ESP32/driver constants, add servo/QuinLED/sensor/wiring constants |
| 2 | ESP32 slot-cradle | Replace standoff posts with pin-header rail mount |
| 3 | QuinLED mount | Replace driver pocket with 50x50mm mount, update cable posts + wiring grooves |
| 4 | Servo mounts | 4x SG90 pockets with M2 screw posts |
| 5 | Servo wiring | Main trunk channel + ESP32/QuinLED spurs + arch clips |
| 6 | Proximity sensor | VL53L0X clip bracket + front wall window |
| 7 | Push rod slots | 4x slots through top tray floor |
| 8 | Ghost objects | `build_ghost_components()` + display loop |
| 9 | Documentation | Update CLAUDE.md Architecture section |

**Build order note:** Tasks 1-6 modify `build_bottom_tray()` and must be applied in order (each builds on the previous). Task 7 modifies `build_top_tray()` independently but depends on Task 1 (constants). Task 8 adds a new function and is independent. Task 9 is pure documentation.
