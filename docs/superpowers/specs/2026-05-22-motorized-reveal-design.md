# Motorized Wearable Reveal System

**Date**: 2026-05-22
**Status**: Approved

## Overview

Add a motorized "reveal" mechanism to the charging stand: 4x SG90 micro servos in the bottom tray push wearable cradles upward through the top tray at a 30-degree tilt angle when triggered. Replace the small LED driver pocket with a full QuinLED-Dig-Uno WLED controller mount. Update the ESP32 mount for pin-header boards (slot-cradle instead of screw standoffs). Add a VL53L0X proximity sensor for hands-free activation. Add ghost visualization objects for all internal components in the cadquery-server preview.

## 1. SG90 Servo Mounts (4x)

**Servo:** SG90 micro servo (23mm x 12.2mm x 22.7mm body, 32.4mm with mounting ears, 4mm shaft height, ~250mA under load at 5V).

**Orientation:** Upright, shaft pointing UP (+Z). The servo horn connects to a push rod that extends through the top tray floor to tilt the wearable cradle.

**Y position (all 4 servos):** Y = -37mm (fixed row). This places them 12.5mm behind the front-row device centers (Y = -49.5mm) and 5.9mm clear of the charger bay front edge (Y = -25mm).

**X positions (matching device columns):**

| Servo | Device | X (mm) |
|-------|--------|--------|
| 1 | Ultrahuman Ring | -81 |
| 2 | Even R1 | -27 |
| 3 | Omi DevKit | +27 |
| 4 | Mudra Pole | +73 |

**Inter-servo spacing:** 54mm between servos 1-2 and 2-3 (21.6mm gap between ears), 46mm between servos 3-4 (13.6mm gap between ears). All clear.

**Vertical placement:**
- Servo base sits on floor: Z = BASE_H (3mm)
- Servo body top: Z = 3 + 22.7 = 25.7mm
- Servo shaft/horn top: Z = 3 + 26.7 = 29.7mm
- Split plane: Z = 41mm (11.3mm clearance above servo)
- Push rod extends from horn through the 11.3mm gap, through the top tray floor (17mm), to the device cradle

**Mount geometry (per servo):**
- Rectangular pocket in the floor: 34mm x 14mm x 5mm deep (body drops in, ears rest on pocket rim)
- The pocket is 34mm wide to accommodate the 32.4mm ear span + tolerance
- 2x M2 screw posts: 5mm tall, centered on ear screw holes (holes are 27.5mm apart, centered on body)
- Posts are 2.5mm outer diameter with 1mm pilot holes for M2 self-tapping screws
- Open top — servo drops in from above, screws secure the ears

**Clearances:**
- Servo body (12.2mm deep in Y) centered at Y=-37: front edge at Y=-43.1, rear edge at Y=-30.9
- Front-row device pockets start at ~Y=-49.5; smallest gap is Mudra socket rear edge at Y=-38.2 — 4.9mm clear of servo front edge
- Charger bay front at Y=-25 — 5.9mm clear of servo rear edge

## 2. Push Rod Slots (Top Tray)

Each servo needs a slot through the top tray floor for the push rod to pass through and actuate the wearable cradle.

**Slot dimensions:** 4mm wide x 12mm long (oriented along Y), centered at the servo shaft X position, offset from device center by the tilt geometry.

**Push rod geometry:**
- Rigid rod (printed or metal wire), ~2mm diameter
- Connects servo horn to underside of cradle tilt plate
- Rod length: ~28mm (from servo horn at Z=29.7 to cradle floor at Z=STAND_H - cradle_depth)

**Slot positions (in top tray floor, at Z = SPLIT_Z):**

| Slot | X (mm) | Y (mm) | Notes |
|------|--------|--------|-------|
| UH Ring | -81 | -37 | Behind ring pocket |
| R1 Ring | -27 | -37 | Behind disc pocket |
| Omi | +27 | -37 | Behind diamond pocket |
| Mudra | +73 | -37 | Behind pole socket |

## 3. Tilt Mechanism (Front-Row Cradles)

**Concept:** Each front-row cradle (UH Ring, R1, Omi) gets a hinge along its rear edge. The push rod pushes the front edge up, tilting the cradle 30 degrees toward the user. When the servo retracts, the cradle drops back flush.

**Hinge slot:** A narrow gap (0.8mm) cut across the rear edge of each cradle pocket at the floor level. This acts as a living hinge — thin enough to flex but thick enough to survive repeated cycles.

**Tilt angle:** 30 degrees. At 30 degrees with a cradle depth of ~20mm, the front edge rises sin(30) x 20 = 10mm — a subtle but noticeable reveal.

**Mudra pole (servo 4):** The mudra servo pushes the pole straight UP (vertical rise, no tilt). The pole already sits in a through-socket; the push rod lifts it 15mm to present the wristband at a more accessible height. A small collar on the push rod prevents the pole from lifting out completely.

**Implementation note:** The tilt mechanism is a future enhancement that requires careful living-hinge design and push-rod linkage tuning. For the initial build, the servo mounts, push rod slots, and wiring are all installed, but the cradles remain fixed. The servos can be tested independently (horn rotation visible through the slots) before adding the tilt plates in a later iteration.

## 4. QuinLED-Dig-Uno Mount (Replaces Driver Pocket)

**Board:** QuinLED-Dig-Uno v3 (50mm x 50mm PCB, ~30mm tall with components). WLED-compatible ESP8266-based LED controller with onboard level shifting, 2x LED outputs, fused 5V input.

**Location:** Front-right corner of the bottom tray interior (mirrors ESP32 on the front-left). Symmetric layout.

**Position (board center):**
- X = +STAND_W/2 - WALL - 50/2 = +117.5 - 25 = +92.5mm
- Y = -STAND_D/2 + WALL + 50/2 = -85 + 25 = -60mm

**Mount geometry:**
- 4x M2 standoff posts: 3mm diameter, 3mm tall, at QuinLED mounting hole positions (4mm inset from each corner, on a 42mm x 42mm square pattern)
- Two cradle walls: right side (against outer wall) and front side (against front wall), 1.5mm thick, 8mm tall
- Open on left and rear sides for cable access
- The existing cable winding posts in the right-side pocket at Y < -35mm are removed (they overlap the QuinLED footprint). Posts at Y > -35mm remain.

**Power input:** 5V DC from VanBon USB-A port via USB cable. The QuinLED has a screw terminal for 5V input (or can be powered via its own USB port).

**LED strip connection:** QuinLED LED output → WS2812B strip DIN. Wire routes through a floor groove from QuinLED to the right-wall LED channel start.

**Clearances:**
- Board top: 3 + 3 + 30 = 36mm; SPLIT_Z = 41mm — 5mm clearance
- Board left edge at X = 92.5 - 25 = 67.5mm; charger bay right edge at X = 73mm — 5.5mm overlap in X but separated by 35mm in Y (charger at Y=15, QuinLED at Y=-60)
- Mudra servo at X=73, Y=-37: 19.5mm away in X from QuinLED center, no physical overlap

**Replaces:** The old LED driver pocket (22mm x 16mm x 8mm at X=-103, Y=-13) is REMOVED. The QuinLED-Dig-Uno has onboard level shifting, eliminating the need for a separate driver board.

## 5. Updated ESP32 Mount (Pin-Header Slot-Cradle)

**Board:** ESP32-DevKitC V4 with pre-soldered pin headers. Same 55x28mm PCB, but total height ~23mm with headers (~8.5mm pin length below PCB + ~12mm components above).

**Location:** Same front-left corner position (center X=-103, Y=-57).

**Mount change:** Replace the 4 screw standoff posts with a slot-cradle design. The DevKitC V4 doesn't have standard mounting holes; with pin headers, the board rides on the header pins which sit in grooves.

**Slot-cradle geometry:**
- 2 parallel raised rails running along Y (board length direction)
- Rail dimensions: 56mm long (board + 1mm tolerance) x 5mm wide x 10mm tall
- Rail spacing: 25.4mm center-to-center (matching standard 0.1" header pitch for 28mm-wide board)
- Rail X positions: X = -103 +/- 12.7mm = X=-115.7 and X=-90.3
- Each rail has a 3.5mm wide x 8.5mm deep groove on its inner face (the pin headers ride in these grooves)
- Board slides in from the rear (+Y direction) — front end is closed (retaining wall), rear end is open for insertion
- Retaining tab: 2mm tall bump at the front end of each groove to prevent the board from sliding out

**Cradle walls:** Keep the existing left-side and front-side cradle walls (1.5mm thick, 6mm tall) for lateral support above the PCB level.

**USB port access:** Same 12mm x 8mm slot through the front wall, repositioned for the higher board position: Z center = BASE_H + 10 (rail height) + 4mm (USB port center on PCB) = 17mm.

**Clearances:**
- Board top: 3 + 10 + 12 = 25mm; SPLIT_Z = 41mm — 16mm clearance
- Left rail at X=-115.7: inner wall at X=-117.5 — 1.8mm clear (tight but printable)
- Right rail at X=-90.3: charger bay left at X=-73 — 17.2mm clear

## 6. VL53L0X Proximity Sensor Mount

**Sensor:** VL53L0X Time-of-Flight laser ranging module (13mm x 18mm breakout board, I2C, 3.3V, range 30-1200mm). Detects hand approach to trigger the reveal animation.

**Location:** Front wall interior, to the right of the ESP32 mount.

**Position (sensor center):**
- X = _esp_x + ESP32_W/2 + 5 + 9 = -103 + 14.5 + 5 + 9 = -74.5mm
- Y = -STAND_D/2 + WALL + 9 = -85 + 9 = -76mm (against front wall)
- Z = BASE_H + 5 = 8mm (low, pointing forward through front wall)

**Mount geometry:**
- Small clip bracket: two 1.5mm thick x 5mm tall walls on left and right sides of the sensor, spaced 14mm apart (13mm board + 1mm tolerance)
- Sensor drops in from above, held by friction

**Front wall window:**
- Rectangular opening through the front wall: 8mm wide x 6mm tall
- Centered on the sensor's laser emitter/detector position
- Allows the ToF laser to "see" through the wall to detect approaching hands

**Wiring:** I2C (SDA, SCL) + 3.3V + GND from ESP32. 4 wires route through a floor groove from sensor position to ESP32.

## 7. Servo Wiring Channels

**Channel dimensions:** 8mm wide x 4mm deep grooves in the bottom tray floor. Wider than the existing 6mm data wire grooves because servo cables are thicker (3-wire bundles).

**Channel layout:**
- **Main trunk:** Runs along X at Y=-37 (the servo row), connecting all 4 servo positions. Length: from X=-81 to X=+73 = 154mm.
- **ESP32 spur:** From the main trunk at X=-81, turns toward the ESP32 at X=-103, Y=-57. L-shaped: 22mm along X then 20mm along Y.
- **QuinLED spur:** From the main trunk at X=+73, turns toward the QuinLED at X=+92.5, Y=-60. L-shaped: 19.5mm along X then 23mm along Y.

**Wire management clips:** Arch bridges every ~40mm along the main trunk. Same design as the existing cable clips (14mm wide, 8mm tall, 2.5mm thick arch walls) but spaced along the servo wire trunk.

Clip positions on main trunk (Y=-37):
- X = -81 (servo 1)
- X = -54 (midpoint 1-2)
- X = -27 (servo 2)
- X = 0 (midpoint 2-3)
- X = +27 (servo 3)
- X = +50 (midpoint 3-4)
- X = +73 (servo 4)

Note: Some of these may overlap existing front-row cable clips (at Y=-37.5). The implementation should check for overlap and skip duplicates.

## 8. Ghost Visualization Objects

**Pattern:** Follow the somni-humidifier `build_components()` pattern. Create a `build_ghost_components()` function that returns a dict of `{name: (solid, (r, g, b, alpha))}` tuples. Display them with `show_object()` in the build section using translucent colors.

**Components to visualize:**

| Component | Color | RGBA | Shape |
|-----------|-------|------|-------|
| ESP32 board | Blue PCB | (0.1, 0.35, 0.7, 0.85) | 55x28x12mm box at mount position |
| QuinLED-Dig-Uno | Green PCB | (0.15, 0.55, 0.15, 0.85) | 50x50x30mm box at mount position |
| SG90 servo x4 | Orange | (0.85, 0.45, 0.1, 0.8) | 23x12.2x22.7mm box + 32.4mm ear plate at each servo position |
| LED strip | Bright green | (0.2, 1.0, 0.3, 0.7) | 10mm x 2mm cross-section, U-shaped path following LED channel |
| VL53L0X sensor | Light blue | (0.3, 0.3, 0.8, 0.85) | 13x18x3mm box at sensor position |
| VanBon charger | Dark gray | (0.3, 0.3, 0.3, 0.5) | 134x68x33mm box in charger bay |
| Servo wires | Yellow | (0.9, 0.85, 0.1, 0.6) | 3mm diameter path following wire channels |

**Display loop (in BUILD AND DISPLAY section):**
```python
ghosts = build_ghost_components()
for comp_name, (comp_solid, comp_color) in ghosts.items():
    show_object(comp_solid, name=f"ghost_{comp_name}",
                options={"color": comp_color})
```

**Implementation:** Each ghost is a simple CadQuery box or extruded shape placed at the component's world-coordinate position. No boolean operations with the tray geometry — these are independent overlay objects for visualization only.

## 9. Constants

New and updated parametric constants:

```python
# --- SG90 micro servo mount ---
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

# --- QuinLED-Dig-Uno mount (replaces DRIVER_* constants) ---
QLED_W = 50               # board width (X)
QLED_D = 50               # board depth (Y)
QLED_H = 30               # board height (Z, tallest component)
QLED_STANDOFF_H = 3       # standoff post height
QLED_STANDOFF_D = 3       # standoff post diameter
QLED_MOUNT_INSET = 4      # M2 hole inset from board edge
QLED_MOUNT_PITCH = 42     # M2 hole spacing (50 - 2*4)
QLED_CRADLE_H = 8         # cradle wall height
QLED_CRADLE_T = 1.5       # cradle wall thickness

# --- ESP32 mount (updated for pin headers) ---
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
SERVO_CLIP_SPACING = 40   # arch clip spacing along trunk (approximate)
```

## 10. Removed Constants

The following constants are REMOVED (replaced by QuinLED mount):
```python
# REMOVED — replaced by QLED_* constants
# DRIVER_L = 22
# DRIVER_W = 16
# DRIVER_H = 8
# DRIVER_STANDOFF_H = 2
# DRIVER_STANDOFF_D = 2
```

The following ESP32 constants are REMOVED (replaced by slot-cradle design):
```python
# REMOVED — replaced by ESP32_RAIL_*, ESP32_GROOVE_* constants
# ESP32_STANDOFF_H = 2
# ESP32_STANDOFF_D = 3
```

## 11. Print Impact

**Bottom tray changes:**
- Servo pockets: 4x subtractive cuts — slight reduction in print time
- Servo screw posts: 8x small cylinders — negligible material
- QuinLED mount: replaces small driver pocket with larger cradle — slight increase
- ESP32 slot-cradle: replaces standoff posts with rails — roughly equivalent material
- Servo wire channels: subtractive — slight reduction
- Wire arch clips: 7x small arches — negligible
- Proximity sensor bracket: 2 small walls — negligible
- Front wall window: subtractive — negligible
- **Net impact: approximately zero additional print time**

**Top tray changes:**
- 4x push rod slots: subtractive cuts through floor — negligible
- **Net impact: trivially less print time**

## 12. Files Changed

| File | Change |
|------|--------|
| `designs/v1-charging-stand.py` | Add servo/QuinLED/sensor constants; replace ESP32 standoffs with slot-cradle and driver pocket with QuinLED mount in `build_bottom_tray()`; add servo mounts, servo wire channels, proximity sensor bracket, push rod slots; add `build_ghost_components()` function; update display section |
| `CLAUDE.md` | Document motorized reveal, QuinLED, updated ESP32 mount, proximity sensor, ghost objects |

## 13. Trigger Mechanism (Software — Future)

The ESP32 handles all trigger logic (not part of the CadQuery geometry, but informs the hardware layout):

- **Proximity:** VL53L0X detects hand within 300mm → triggers reveal animation
- **Button:** Capacitive touch pad on top tray surface (future addition)
- **App:** MQTT/HTTP command from phone via WiFi
- **Schedule:** Time-based (morning routine reveal)

The ESP32 drives all 4 servos via GPIO pins (GPIO 13, 14, 25, 26). PWM signal, no additional driver board needed for SG90 servos.
