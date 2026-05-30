"""
Wearable Charging Stand — V1
Unified charging dock for 5 wearable devices + iPad slot, USB-A powered via VanBon hub.

Devices (front row, left to right):
  1. Ultrahuman Ring Air   — SQUARE charging dock 39×39×13mm
  2. Even Realities R1     — CIRCULAR NFC magnetic charger 30mm dia × 10mm
  3. Omi DevKit 2          — SIX-SIDED DIAMOND pendant ~41×40×13mm (direct charge)
  4. Mudra Link            — wristband DRAPES over separate snap-in L-pole shelf
Rear row:
  5. Even Realities G2     — glasses charging case 170×75×30mm
  6. iPad                  — wide slot behind G2 (fits 13" Pro, diagonal if cased)

Design goals:
  - Single AC input to internal VanBon 8-port USB-A charger (under G2 shelf)
  - Hidden cable routing channels in the bottom tray cavity
  - Each charger sits in a fitted pocket with cable pass-through
  - Mudra wristband drapes over pole arm shelf; charger flush in underside
  - Clean desktop aesthetic
  - 3D printable (PETG), fits QIDI Q2 build plate (245×255mm)

Loadable by cadquery-server via show_object().
"""

import cadquery as cq
import math
from cq_server.ui import ui, show_object

# =============================================================================
# PARAMETRIC DIMENSIONS (all in mm)
# =============================================================================

# --- Overall stand ---
STAND_W = 240          # total width (fits Q2 245mm plate)
STAND_D = 175          # total depth (G2 case + iPad slot + back wall)
STAND_H = 67           # TOTAL assembled height (bottom + top)
WALL = 2.5             # wall thickness
CORNER_R = 5           # corner fillet radius
TOL = 1.0              # print tolerance per side (1mm clearance each side for snug drop-in fit)

# --- Two-part split ---
# Bottom tray: cable management, VanBon charger, rubber feet
# Top tray: device pockets, Mudra pole, iPad wall — sits on top of bottom
# Bottom tray height = 50mm (~2 inches) to house VanBon charger (33mm)
# with 12mm headroom above for USB cables to bend out of ports.
SPLIT_Z = 50           # Z where the two parts meet (bottom tray height)
TOP_H = STAND_H - SPLIT_Z   # top tray height (16mm)
LID_FLOOR = 2          # solid floor thickness on top tray bottom face (lid surface)
SNAP_TOL = 0.3         # clearance for snap-fit (per side)
SNAP_LIP = 1.5         # ledge depth for snap engagement
SNAP_CLIP_W = 12       # width of each snap clip
SNAP_CLIP_H = 8        # clip cantilever height
SNAP_HOOK = 1.2        # hook overhang that catches the lip

# --- Removable device tray (front-row wearable pockets) ---
# Drop-in friction-fit tray holding UH, R1, Omi pockets + Mudra socket.
# Rests on a 3-sided ledge inside a rectangular cutout in the top tray.
DTRAY_TOL = SNAP_TOL           # 0.3mm clearance per side
DTRAY_LEDGE = WALL             # 2.5mm ledge width for tray to rest on
DTRAY_FLOOR_Z = SPLIT_Z + LID_FLOOR  # 43mm — bottom of device tray
# Width and depth computed dynamically from SLOT_POSITIONS + device sizes

# --- Base platform (bottom tray internals) ---
BASE_H = 5             # solid floor at very bottom of bottom tray (5mm for structural integrity)
CHANNEL_H = SPLIT_Z - BASE_H - WALL  # cable channel height
CHANNEL_W = 12         # cable channel width (wider for better cable mgmt)

# --- VanBon Smart USB Charger recess (under G2 shelf) ---
# Measured: 134mm long × 68mm wide × 33mm tall.
# 8× USB-A ports on the long side, AC cable exits the short side (left),
# 45×45mm LCD screen centered on the top face.
# The charger sits flush in the bottom tray cavity, accessed by
# removing the top tray.
CHARGER_W = 146        # charger length + ledge inset clearance (134 + 4mm ledge×2 + 4mm tolerance)
CHARGER_D = 80         # charger width  + ledge inset clearance (68 + 4mm ledge×2 + 4mm tolerance)
CHARGER_H = 35         # charger height + 2mm tolerance (measured: 33mm)
CHARGER_CABLE_SLOT_W = 18  # slot for AC input cable through wall (wider for AC plug)
CHARGER_USB_PORT_COUNT = 8  # USB-A ports on the long side
CHARGER_USB_SLOT_W = 16     # USB-A cable slot width (USB-A head ~14mm + clearance)
CHARGER_USB_SLOT_H = 10     # USB-A cable slot height
CHARGER_USB_SPACING = 16    # spacing between USB port exit slots (center-to-center)
# Legacy aliases retained so any older references compile.
HUB_W, HUB_D, HUB_H = CHARGER_W, CHARGER_D, CHARGER_H
HUB_CABLE_SLOT_W = CHARGER_CABLE_SLOT_W
USBC_HEAD_W = 14       # USB-C connector head width (long axis)
USBC_HEAD_H = 9        # USB-C connector head height (short axis)

# --- Device 1: Ultrahuman Ring Air — SQUARE dock ---
UH_SIDE = 39 + TOL * 2       # square side length (measured: 39mm)
UH_H = 13                     # dock height (measured: 13mm)
UH_CRADLE_DEPTH = 10          # how deep it sits (proportional to new height)
UH_CORNER_R = 4               # rounded corners on the square

# --- Device 2: Even Realities R1 — CIRCULAR charger ---
# Real measurements: 30mm diameter × 10mm height
R1_DIA = 30 + TOL * 2        # charger diameter (measured: 30mm)
R1_H = 10                    # charger height (measured: 10mm)
R1_CRADLE_DEPTH = 10

# --- Device 3: Omi DevKit 2 — SIX-SIDED DIAMOND PENDANT ---
# Six-sided diamond with ALTERNATING edge lengths (not a regular hexagon).
# The pendant charges directly in this pocket via pogo pins.
# Real measurements: 3 long sides of 30mm, 3 short sides of 15mm
# Interior angles 120° (hexagonal), oriented as a diamond (pointy top & bottom).
# Bounding box of this shape: ~45mm wide × ~39mm tall.
OMI_LONG_EDGE = 30            # 3 alternating long edges (mm)
OMI_SHORT_EDGE = 15           # 3 alternating short edges (mm)
OMI_THICK = 13                # pendant thickness
OMI_CRADLE_DEPTH = OMI_THICK + 2   # pocket depth to fully contain pendant + margin
OMI_VERTEX_R = 3              # small fillet for six-sided diamond vertices

# --- Device 4: Mudra Link — L-shaped pole with open charger bay ---
# Vertical pole + horizontal shelf extending right.
# Wristband drapes across the shelf in Y (toward user), hanging on both sides.
#
# KEY CONSTRAINT: The magnetic charger end piece is WIDER than the 22mm band
# (~32mm W × 18mm D × 10mm thick) and the cable exits from the SIDE of the
# charger (not straight down). The pole must have a large enough internal
# cavity to house the charger and allow the cable to make a gentle bend.
#
# Design approach:
#   - Charger sits FLUSH in a top-open pocket on the shelf surface
#   - Pogo pins face UP — wristband lays directly on the charger, no ceiling
#   - Cable exits charger sideways (-X toward post), bends down through
#     the post's internal cavity, exits through the base
#   - Chamfered pocket lip for smooth band contact (no hard edges)
#
# Constraints:
#   - Vertical clearance below shelf > band half-circ + clasp (~74mm)
#   - Shelf width (Y) ≈ band width for passive self-centering
#   - Charger pocket open from top — charger drops in flush
MUDRA_POLE_W = 22             # pole Y-extent (reduced for smaller charger, still room for band)
MUDRA_POLE_D = 20             # pole X-thickness (reduced for smaller charger + cable bend)
MUDRA_POLE_H = 85             # vertical section height (69mm clearance + 16mm shelf)
MUDRA_SHELF_L = 36            # shelf length extending right (+X) — optimized for actual charger
MUDRA_SHELF_H = 14            # shelf thickness (Z) — reduced for smaller charger bay
MUDRA_CHARGER_W = 12 + TOL * 2  # charger pocket Y-extent (real: 12mm width)
MUDRA_CHARGER_D = 30 + TOL * 2  # charger pocket X-extent (real: 30mm length)
MUDRA_CHARGER_H = 8 + TOL       # charger end piece height (real: 8mm thickness)
MUDRA_CABLE_CH_W = 12         # cable cavity width (Y) — room for USB cable
MUDRA_CABLE_CH_D = 14         # cable cavity depth (X) — room for cable + bend
MUDRA_CABLE_BEND_R = 15       # minimum cable bend radius

# --- Mudra pole snap clips (beefier than tray-to-tray clips) ---
# The original SNAP_HOOK (1.2mm) arms were too thin and broke during
# insertion. These dedicated constants make the Mudra clips much stronger.
MUDRA_CLIP_T = 2.5            # arm thickness (was SNAP_HOOK=1.2, now 2x thicker)
MUDRA_CLIP_W = 14             # clip width along Y (was SNAP_CLIP_W=12)
MUDRA_CLIP_H = 8              # cantilever height (same as before)
MUDRA_HOOK = 2.0              # hook overhang that catches the lip (was 1.2)
MUDRA_HOOK_H = 2.0            # hook nub height (was SNAP_HOOK=1.2)

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

# --- RGB LED strip (WS2812B 30/m) ---
LED_CHANNEL_W = 12        # channel width (10mm strip + clearance)
LED_CHANNEL_D = 4         # channel depth into floor
LED_SLOT_H = 3            # light exit slot height on exterior walls
LED_SLOT_Z = 1            # slot bottom edge Z (above desk)

# --- Backlit logo ---
LOGO_TEXT = "Somni Labs"
LOGO_FONT_SIZE = 12       # cap height in mm
LOGO_RECESS_DEPTH = 1.9   # cut depth (WALL - 0.6mm diffuser)
LOGO_Z = 20               # vertical center of text on front wall

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

# --- Device 5: Even Realities G2 glasses case ---
# Caliper measurements: 174mm × 66mm × 36mm (simple rectangular box).
# Cradle only needs a shallow insert to hold the case in place.
G2_W = 174 + TOL * 2         # case length (measured: 174mm)
G2_D = 66 + TOL * 2          # case depth (measured: 66mm)
G2_H = 36                    # case height (measured: 36mm)
G2_CRADLE_DEPTH = 18          # how deep case sits (shallow insert, not full enclosure)
G2_CABLE_W = 14               # USB-C cable slot

# --- Device 6: iPad slot (rear, behind G2 case) ---
# iPad Pro 13" in landscape: 267 × 213 × ~6mm (actual device)
# With a thin case: ~270 × 215mm overall (optimized for print bed fit)
# NOTE: For thick cases, iPad can be placed diagonally in the wider slot
# Slot has a back wall the iPad leans against.
IPAD_SLOT_W = 235             # slot width (X) — max width for 245mm print bed
IPAD_SLOT_GAP = 24            # slot gap (Y) — iPad + case thickness (~22mm + tolerance)
IPAD_SLOT_DEPTH = 20          # how deep iPad sits into the base slot
IPAD_BACK_H = 60              # back wall height above base (taller for 13" iPad)
IPAD_BACK_THICK = 4           # back wall thickness
IPAD_LIP_H = 5                # front groove depth (iPad bottom edge sits in recessed channel)
IPAD_WALL_TOL = 0.4        # tongue-and-groove tolerance (tighter than global TOL for snug slide fit)
IPAD_DETENT_H = 0.6        # snap detent bump height (clicks past on insertion)
IPAD_DETENT_W = 15         # snap detent bump width (X)
# Diagonal placement: 13" iPad (270mm) can fit diagonally in 235mm slot
# sin(angle) = 235/270 = 0.87, angle ≈ 60° from horizontal

# --- Layout positions (X, Y from center) ---
FRONT_ROW_Y = -STAND_D / 2 + 38
# G2 centered between front-row rear edge and iPad front edge (11mm clearance each side)
_IPAD_FRONT_EDGE = STAND_D / 2 - IPAD_BACK_THICK - IPAD_SLOT_GAP
_FRONT_REAR_EDGE = FRONT_ROW_Y + 20          # half of largest front device (UH_SIDE)
REAR_ROW_Y = (_FRONT_REAR_EDGE + _IPAD_FRONT_EDGE) / 2

FRONT_SPACING = 54
FRONT_START = -1.5 * FRONT_SPACING

SLOT_POSITIONS = {
    "uh_ring":  (FRONT_START,                     FRONT_ROW_Y),
    "r1_ring":  (FRONT_START + FRONT_SPACING,     FRONT_ROW_Y),
    "omi":      (FRONT_START + FRONT_SPACING * 2, FRONT_ROW_Y),
    "mudra":    (FRONT_START + FRONT_SPACING * 3 - 8, FRONT_ROW_Y),  # shifted left 8mm so shelf fits Q2 plate
    "g2_case":  (0,                                REAR_ROW_Y),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def six_sided_diamond_points(long_edge, short_edge):
    """Return vertices of a six-sided diamond with alternating edge lengths.

    The pendant is a hexagonal diamond: 3 long edges alternate with 3 short
    edges, all interior angles 120°.  Oriented as a diamond (pointy top and
    bottom vertex).  The shape is centered at the origin.

    - long_edge:  length of the 3 longer sides  (e.g. 30 mm)
    - short_edge: length of the 3 shorter sides  (e.g. 15 mm)

    Vertex order: top point → clockwise → back to top.
    """
    import math
    # Walk the boundary clockwise starting from the top vertex.
    # Initial heading: down-right (−60° from +x in standard math coords).
    # At each vertex we turn −60° (clockwise) — exterior angle of a 120° polygon.
    heading = math.radians(-60)
    turn = math.radians(-60)
    edges = [long_edge, short_edge, long_edge, short_edge, long_edge, short_edge]

    x, y = 0.0, 0.0
    raw = [(x, y)]
    for edge_len in edges:
        x += edge_len * math.cos(heading)
        y += edge_len * math.sin(heading)
        raw.append((x, y))
        heading += turn

    # Drop the duplicate closure vertex
    pts = raw[:-1]

    # Center on origin
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cx = (max(xs) + min(xs)) / 2
    cy = (max(ys) + min(ys)) / 2
    return [(round(px - cx, 3), round(py - cy, 3)) for px, py in pts]


# =============================================================================
# BUILD BOTTOM TRAY (cable management)
# =============================================================================

def build_bottom_tray():
    """Bottom tray: cable channels, USB hub, snap-fit clips, rubber feet."""

    # ── Outer shell ──────────────────────────────────────────────────────
    tray = (
        cq.Workplane("XY")
        .box(STAND_W, STAND_D, SPLIT_Z, centered=[True, True, False])
    )
    tray = tray.edges("|Z").fillet(CORNER_R)

    # ── Hollow interior (open-top tray) ─────────────────────────────────
    # Cut all the way to the top — NO ceiling. The bottom tray is an
    # open box. The top tray acts as the lid when snapped on.
    # This lets you set the tray on the desk, drop in the charger,
    # route all cables, then snap the top tray on to close it.
    cavity = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .box(STAND_W - WALL * 2, STAND_D - WALL * 2, SPLIT_Z - BASE_H + 1,
             centered=[True, True, False])
    )
    tray = tray.cut(cavity)

    # ── ZONED INTERIOR LAYOUT ────────────────────────────────────────────
    # The bottom tray is divided into 3 zones (front→back):
    #
    #   ZONE 1 — FRONT CABLE CHANNEL (Y = front wall to charger front edge)
    #     Short ribs between the 4 front-row device positions only.
    #     Cables drop from device pockets, run along this channel to
    #     the charger's USB-A ports on its front (-Y) face.
    #
    #   ZONE 2 — CHARGER BAY (centered on REAR_ROW_Y)
    #     Completely open — no ribs. The VanBon charger drops straight
    #     in from above when the top tray is removed. AC cable exits
    #     through the left wall. USB-A ports face front (-Y).
    #
    #   ZONE 3 — REAR CABLE CHANNEL (charger rear edge to back wall)
    #     iPad cable + AC cable routing. Minimal ribs.
    #
    # This gives an intuitive layout: pop off the top tray, drop in the
    # charger, plug cables, route them forward through the channel, done.
    # ──────────────────────────────────────────────────────────────────────

    charger_x, charger_y = SLOT_POSITIONS["g2_case"]
    _charger_front = charger_y - CHARGER_D / 2   # Y = -21
    _charger_back  = charger_y + CHARGER_D / 2    # Y = 51
    _charger_left  = charger_x - CHARGER_W / 2   # X = -69
    _charger_right = charger_x + CHARGER_W / 2   # X = 69

    # ── Zone 1: Front cable channel — completely open ──────────────────
    # No ribs. The entire front channel is one open cavity from the
    # front wall to the charger bay. Cables route freely in any
    # direction. The Velcro tie-down slots and arch clips handle
    # all the cable organization.

    # ── Zone 2: VanBon charger bay (completely open) ─────────────────────
    # The charger sits on the floor and is accessed from ABOVE when the
    # top tray is removed. The bay must:
    #   1. Be open all the way to the top of the bottom tray (Z=SPLIT_Z)
    #      so the charger drops straight in.
    #   2. Have enough headroom above the charger for USB-A cables to
    #      bend out of the ports (cables enter horizontally, need room
    #      to curve upward through the top tray cable pass-throughs).
    #   3. Not have corner tabs that reduce the opening below the
    #      charger's actual footprint.
    #
    # The charger bay is a full-depth pocket from the floor (BASE_H)
    # all the way up through the tray top surface (SPLIT_Z + 1).
    charger_bay = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .center(charger_x, charger_y)
        .box(CHARGER_W, CHARGER_D, SPLIT_Z - BASE_H + 1, centered=[True, True, False])
    )
    tray = tray.cut(charger_bay)

    # Low-profile ledge around the bay perimeter to support the charger
    # at the correct height and prevent it from shifting. The ledge is
    # only 5mm tall — well below the charger top, leaving the bay open.
    _ledge_w = 4       # ledge width (inward from bay wall)
    _ledge_h = 5       # ledge height from floor
    # Front and back ledge strips
    for dy, sign in [(-1, -1), (1, 1)]:
        ledge = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H)
            .center(charger_x, charger_y + sign * (CHARGER_D / 2 - _ledge_w / 2))
            .box(CHARGER_W - 20, _ledge_w, _ledge_h, centered=[True, True, False])
        )
        tray = tray.union(ledge)
    # Left and right ledge strips
    for dx, sign in [(-1, -1), (1, 1)]:
        ledge = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H)
            .center(charger_x + sign * (CHARGER_W / 2 - _ledge_w / 2), charger_y)
            .box(_ledge_w, CHARGER_D - 20, _ledge_h, centered=[True, True, False])
        )
        tray = tray.union(ledge)

    # AC input cable slot through left wall (-X side)
    # The VanBon's AC cable exits its short side. Full height slot.
    ac_slot = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .center(-STAND_W / 2, charger_y)
        .box(WALL * 4, CHARGER_CABLE_SLOT_W, SPLIT_Z - BASE_H, centered=True)
    )
    tray = tray.cut(ac_slot)

    # ── Zone 3: Rear — completely open ─────────────────────────────────
    # No ribs behind the charger. The USB-A ports face this direction
    # so the entire rear zone stays clear for plugging in cables,
    # iPad cable routing, and AC cable access.

    # ── Spare USB-A port exit — back wall (+Y side) ──────────────────
    # The VanBon has 8 USB-A ports but only 6 are used by devices.
    # Two spare ports need cables routed OUT the back of the stand
    # so they're accessible for ad-hoc charging (phone, earbuds, etc).
    # Slot is wide enough for 2 USB-A cables side by side (~36mm)
    # and positioned directly behind the charger bay center.
    _spare_usb_slot_w = 36   # width for 2 USB-A cables (~16mm each + gap)
    _spare_usb_slot_h = 14   # height for USB-A heads + cable bend
    spare_usb_slot = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .center(charger_x, STAND_D / 2)
        .box(_spare_usb_slot_w, WALL * 4, _spare_usb_slot_h,
             centered=[True, True, False])
    )
    tray = tray.cut(spare_usb_slot)

    # ── Velcro tie-down slots (reduced set — 6 pairs total) ────────────
    # Thread a Velcro strap down through one slot, under the floor, and
    # up through the other to cinch cables flat. Only 6 pairs needed:
    # 2 per side (front + rear of charger bay) + 2 in the rear zone.
    _velcro_slot_l = 15    # slot length along Y (wide enough for strap)
    _velcro_slot_w = 3     # slot width along X
    _velcro_pair_gap = 20  # gap between paired slots along X

    _velcro_row_offset = 20  # offset from charger bay edge (inner row only)

    # Fixed positions: (side_sign, Y position)
    _velcro_positions = [
        # Left side — front and rear of charger bay
        (-1, _charger_front - 15),   # left-front
        (-1, _charger_back + 15),    # left-rear
        (-1, 0),                     # left-center
        # Right side — front and rear of charger bay
        (1, _charger_front - 15),    # right-front
        (1, _charger_back + 15),     # right-rear
        (1, 0),                      # right-center
    ]

    for side_sign, _vy in _velcro_positions:
        edge_x = _charger_left if side_sign == -1 else _charger_right
        row_x = edge_x + side_sign * _velcro_row_offset

        slot_a = (
            cq.Workplane("XY")
            .workplane(offset=-0.5)
            .center(row_x - side_sign * _velcro_pair_gap / 2, _vy)
            .rect(_velcro_slot_w, _velcro_slot_l)
            .extrude(BASE_H + 2)
        )
        tray = tray.cut(slot_a)

        slot_b = (
            cq.Workplane("XY")
            .workplane(offset=-0.5)
            .center(row_x + side_sign * _velcro_pair_gap / 2, _vy)
            .rect(_velcro_slot_w, _velcro_slot_l)
            .extrude(BASE_H + 2)
        )
        tray = tray.cut(slot_b)

    # ── Cable routing clips REMOVED ─────────────────────────────────────
    # The arch bridges (14mm span, 2.5mm walls) spaghettified during printing
    # at aggressive speeds. Cable management uses Velcro straps instead.

    # ── ESP32 DevKitC V4 mount (front-left corner, slot-cradle) ──────────
    # Board with pre-soldered pin headers rides in grooved rails.
    # Long edge along Y (56mm), short edge (29mm, USB port) faces front wall.
    # Pin headers sit in grooves; board slides in from the rear (+Y).
    _esp_x = -STAND_W / 2 + WALL + ESP32_W / 2   # center X = -105.5mm
    _esp_y = -STAND_D / 2 + WALL + ESP32_L / 2   # center Y = -57mm

    # Proximity sensor position (defined early for use in wiring grooves below)
    _prox_x = _esp_x + ESP32_W / 2 + 5 + PROX_W / 2   # sensor center X = -74.5mm
    _prox_y = -STAND_D / 2 + WALL + PROX_D / 2          # sensor center Y = -76mm

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

    # ── RGB LED channel (U-shaped: left wall → front wall → right wall) ──
    # Groove in the floor for WS2812B LED strip. Inset 1mm from the inner
    # wall so light reflects off the wall before exiting through the slots.
    _inner_left   = -STAND_W / 2 + WALL            # X = -117.5
    _inner_right  =  STAND_W / 2 - WALL            # X =  117.5
    _inner_front  = -STAND_D / 2 + WALL             # Y = -85
    _inner_back   =  STAND_D / 2 - WALL             # Y =  85
    _ch_inset = 1   # inset from inner wall face
    _led_actual_d = min(LED_CHANNEL_D, BASE_H - 1)  # never cut deeper than floor minus 1mm
    _ch_z = BASE_H - _led_actual_d  # channel bottom (always leaves 1mm floor)

    # Left wall segment (runs along Y)
    led_ch_left = (
        cq.Workplane("XY")
        .workplane(offset=_ch_z)
        .center(_inner_left + _ch_inset + LED_CHANNEL_W / 2,
                (_inner_front + _inner_back) / 2)
        .rect(LED_CHANNEL_W, _inner_back - _inner_front)
        .extrude(_led_actual_d + 0.5)
    )
    tray = tray.cut(led_ch_left)

    # Front wall segment (runs along X)
    led_ch_front = (
        cq.Workplane("XY")
        .workplane(offset=_ch_z)
        .center(0, _inner_front + _ch_inset + LED_CHANNEL_W / 2)
        .rect(_inner_right - _inner_left, LED_CHANNEL_W)
        .extrude(_led_actual_d + 0.5)
    )
    tray = tray.cut(led_ch_front)

    # Right wall segment (runs along Y)
    led_ch_right = (
        cq.Workplane("XY")
        .workplane(offset=_ch_z)
        .center(_inner_right - _ch_inset - LED_CHANNEL_W / 2,
                (_inner_front + _inner_back) / 2)
        .rect(LED_CHANNEL_W, _inner_back - _inner_front)
        .extrude(_led_actual_d + 0.5)
    )
    tray = tray.cut(led_ch_right)

    # ── Light exit slots (exterior walls, near desk level) ───────────────
    # Narrow horizontal slots cut through the bottom of each exterior wall.
    # Light from the LED channel spills downward onto the desk.

    # Front wall light slot
    led_slot_front = (
        cq.Workplane("XY")
        .workplane(offset=LED_SLOT_Z)
        .center(0, -STAND_D / 2)
        .rect(STAND_W - CORNER_R * 4, WALL * 3)
        .extrude(LED_SLOT_H)
    )
    tray = tray.cut(led_slot_front)

    # Left wall light slot
    led_slot_left = (
        cq.Workplane("XY")
        .workplane(offset=LED_SLOT_Z)
        .center(-STAND_W / 2, 0)
        .rect(WALL * 3, STAND_D - CORNER_R * 4)
        .extrude(LED_SLOT_H)
    )
    tray = tray.cut(led_slot_left)

    # Right wall light slot
    led_slot_right = (
        cq.Workplane("XY")
        .workplane(offset=LED_SLOT_Z)
        .center(STAND_W / 2, 0)
        .rect(WALL * 3, STAND_D - CORNER_R * 4)
        .extrude(LED_SLOT_H)
    )
    tray = tray.cut(led_slot_right)

    # ── Floor wiring grooves ─────────────────────────────────────────────
    # Shallow channels in the floor for routing wires between the ESP32,
    # QuinLED, LED channels, charger bay, and proximity sensor.
    _wire_w = 6    # groove width
    _wire_d = min(3, BASE_H - 1)  # groove depth (never cut through floor, leave 1mm)
    _wire_z = BASE_H - _wire_d

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

    # ── Servo wiring channels ────────────────────────────────────────────
    # Main trunk along X at the servo row, connecting all 4 positions.
    # Spurs connect to ESP32 (front-left) and QuinLED (front-right).
    _sw_actual_d = min(SERVO_WIRE_D, BASE_H - 1)  # never cut through floor
    _sw_z = BASE_H - _sw_actual_d  # channel bottom (always leaves 1mm floor)

    # Main trunk: X=-81 to X=+73 at Y=-37
    _trunk_x_start = _servo_x_positions[0]   # -81
    _trunk_x_end = _servo_x_positions[-1]     # +73
    _trunk_length = _trunk_x_end - _trunk_x_start
    servo_trunk = (
        cq.Workplane("XY")
        .workplane(offset=_sw_z)
        .center((_trunk_x_start + _trunk_x_end) / 2, SERVO_Y)
        .rect(_trunk_length + SERVO_WIRE_W, SERVO_WIRE_W)
        .extrude(_sw_actual_d + 0.5)
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
        .extrude(_sw_actual_d + 0.5)
    )
    tray = tray.cut(spur_esp_horiz)

    spur_esp_vert = (
        cq.Workplane("XY")
        .workplane(offset=_sw_z)
        .center(_esp_x, (_esp_y + SERVO_Y) / 2)
        .rect(SERVO_WIRE_W, abs(SERVO_Y - _esp_y) + SERVO_WIRE_W)
        .extrude(_sw_actual_d + 0.5)
    )
    tray = tray.cut(spur_esp_vert)

    # QuinLED spur: from trunk at X=+73 toward QuinLED at X=+92.5, Y=-60
    spur_qled_horiz = (
        cq.Workplane("XY")
        .workplane(offset=_sw_z)
        .center((_trunk_x_end + _qled_x) / 2, SERVO_Y)
        .rect(abs(_qled_x - _trunk_x_end) + SERVO_WIRE_W, SERVO_WIRE_W)
        .extrude(_sw_actual_d + 0.5)
    )
    tray = tray.cut(spur_qled_horiz)

    spur_qled_vert = (
        cq.Workplane("XY")
        .workplane(offset=_sw_z)
        .center(_qled_x, (_qled_y + SERVO_Y) / 2)
        .rect(SERVO_WIRE_W, abs(SERVO_Y - _qled_y) + SERVO_WIRE_W)
        .extrude(_sw_actual_d + 0.5)
    )
    tray = tray.cut(spur_qled_vert)

    # ── Servo wire arch clips REMOVED ──────────────────────────────────
    # Same spaghetti issue as cable routing clips — 14mm bridge spans
    # failed at aggressive print speeds. Wires stay in channels by gravity;
    # Velcro straps handle any that need securing.

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

    # ── "Somni Labs" backlit logo (front wall exterior) ──────────────────
    # Text recessed into the front wall, leaving a 0.6mm thin wall as a
    # natural light diffuser. The RGB strip behind the front wall
    # backlights the letters for a soft glow effect.
    _logo_y = -STAND_D / 2  # exterior face of front wall
    logo_text = (
        cq.Workplane("XZ")
        .workplane(offset=-_logo_y)  # position at front wall exterior face
        .center(0, LOGO_Z)
        .text(LOGO_TEXT, LOGO_FONT_SIZE, -LOGO_RECESS_DEPTH,
              font="Sans", halign="center", valign="center")
    )
    tray = tray.cut(logo_text)

    # ── Cable pass-through holes — NOT NEEDED in bottom tray ────────────
    # The bottom tray is now an open-top box (no ceiling). Cables route
    # freely up through the open top into the top tray's pass-through
    # holes. No cuts needed here.

    # ── Snap-fit clips (4 clips — one on each long side, centered) ───────
    # Cantilever clips that hook over a lip on the top tray's inner wall.
    # Clips are on the OUTSIDE top edge of the bottom tray.
    clip_positions = [
        (-STAND_W / 4, -STAND_D / 2 + WALL / 2, 0),    # front-left
        ( STAND_W / 4, -STAND_D / 2 + WALL / 2, 0),    # front-right
        (-STAND_W / 4,  STAND_D / 2 - WALL / 2, 180),  # rear-left
        ( STAND_W / 4,  STAND_D / 2 - WALL / 2, 180),  # rear-right
    ]
    for cx, cy, _rot in clip_positions:
        # Vertical cantilever arm rising from the top surface
        arm = (
            cq.Workplane("XY")
            .workplane(offset=SPLIT_Z)
            .center(cx, cy)
            .rect(SNAP_CLIP_W, WALL)
            .extrude(SNAP_CLIP_H)
        )
        tray = tray.union(arm)

        # Hook nub at the top of the arm (inward-facing)
        # Points toward center of stand
        nub_y_offset = WALL / 2 + SNAP_HOOK / 2
        if cy > 0:
            nub_y_offset = -nub_y_offset  # rear clips hook inward
        nub = (
            cq.Workplane("XY")
            .workplane(offset=SPLIT_Z + SNAP_CLIP_H - SNAP_HOOK)
            .center(cx, cy + nub_y_offset)
            .rect(SNAP_CLIP_W, SNAP_HOOK)
            .extrude(SNAP_HOOK)
        )
        tray = tray.union(nub)

    # ── Rubber feet recesses ─────────────────────────────────────────────
    FOOT_DIA = 10
    FOOT_DEPTH = 1.5
    foot_inset = 15
    for fx, fy in [
        (-STAND_W / 2 + foot_inset, -STAND_D / 2 + foot_inset),
        ( STAND_W / 2 - foot_inset, -STAND_D / 2 + foot_inset),
        (-STAND_W / 2 + foot_inset,  STAND_D / 2 - foot_inset),
        ( STAND_W / 2 - foot_inset,  STAND_D / 2 - foot_inset),
    ]:
        foot = (
            cq.Workplane("XY")
            .workplane(offset=-0.5)
            .center(fx, fy)
            .circle(FOOT_DIA / 2)
            .extrude(FOOT_DEPTH + 0.5)
        )
        tray = tray.cut(foot)

    return tray


# =============================================================================
# BUILD TOP TRAY (device pockets + pole)
# =============================================================================

def build_top_tray():
    """Top tray: G2 shelf, iPad groove, device tray cutout. Sits on bottom tray.

    Front-row device pockets (UH, R1, Omi, Mudra) have moved to the
    removable device tray (build_device_tray()).  This function now cuts
    a rectangular opening with a 3-sided ledge for the drop-in tray.
    """

    # ── Top slab — starts at SPLIT_Z ─────────────────────────────────────
    base = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z)
        .box(STAND_W, STAND_D, TOP_H, centered=[True, True, False])
    )
    base = base.edges("|Z").fillet(CORNER_R)
    base = base.edges(">Z").fillet(1.2)

    # ── Snap-fit receiving slots ─────────────────────────────────────────
    # The top tray has a perimeter ledge (inner lip) that the bottom
    # tray's clips hook onto. Cut slots in the walls for the clips.
    clip_positions = [
        (-STAND_W / 4, -STAND_D / 2, 0),    # front-left
        ( STAND_W / 4, -STAND_D / 2, 0),    # front-right
        (-STAND_W / 4,  STAND_D / 2, 180),  # rear-left
        ( STAND_W / 4,  STAND_D / 2, 180),  # rear-right
    ]
    for cx, cy, _rot in clip_positions:
        # Slot in the wall for the clip arm to pass through
        slot = (
            cq.Workplane("XY")
            .workplane(offset=SPLIT_Z - 0.5)
            .center(cx, cy)
            .rect(SNAP_CLIP_W + SNAP_TOL * 2, WALL + 2)
            .extrude(SNAP_CLIP_H + SNAP_HOOK + 1)
        )
        base = base.cut(slot)

        # Inner lip pocket — small recess for the hook to catch behind
        lip_y = cy + (WALL + SNAP_LIP / 2) * (-1 if cy > 0 else 1)
        lip_pocket = (
            cq.Workplane("XY")
            .workplane(offset=SPLIT_Z + SNAP_CLIP_H - SNAP_HOOK - 0.5)
            .center(cx, lip_y)
            .rect(SNAP_CLIP_W + SNAP_TOL * 2, SNAP_LIP + SNAP_TOL)
            .extrude(SNAP_HOOK * 2 + 1)
        )
        base = base.cut(lip_pocket)

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

    # Extend cutout forward to inner face of front wall (no front ledge)
    _front_extension = (
        cq.Workplane("XY")
        .workplane(offset=DTRAY_FLOOR_Z)
        .center(_dtray_cx, (_dtray_y_min - DTRAY_TOL + (-STAND_D / 2 + WALL)) / 2)
        .rect(_cutout_w, abs(_dtray_y_min - DTRAY_TOL - (-STAND_D / 2 + WALL)) + 1)
        .extrude(STAND_H - DTRAY_FLOOR_Z + 1)
    )
    base = base.cut(_front_extension)

    # ── Retention lip tabs — prevent device tray from lifting out ────
    # Tiny inward-protruding nubs near the top of the cutout walls.
    # Only 0.5mm protrusion — within the 0.3mm tolerance gap, so only
    # 0.2mm of actual interference. The tray presses past with light
    # force and lifts out just as easily with one hand.
    # 4 tabs: left wall, right wall, rear wall ×2.
    _ret_protrude = 0.5   # how far the tab sticks inward (mm)
    _ret_h = 1.5          # tab height (Z)
    _ret_w = 8.0          # tab width along the wall
    _ret_z = STAND_H - _ret_h - 0.5  # sits just below top surface

    # Left wall tab
    _ret_left_tab = (
        cq.Workplane("XY")
        .workplane(offset=_ret_z)
        .center(_dtray_cx - _cutout_w / 2 + _ret_protrude / 2, _dtray_cy)
        .rect(_ret_protrude, _ret_w)
        .extrude(_ret_h)
    )
    base = base.union(_ret_left_tab)

    # Right wall tab
    _ret_right_tab = (
        cq.Workplane("XY")
        .workplane(offset=_ret_z)
        .center(_dtray_cx + _cutout_w / 2 - _ret_protrude / 2, _dtray_cy)
        .rect(_ret_protrude, _ret_w)
        .extrude(_ret_h)
    )
    base = base.union(_ret_right_tab)

    # Rear wall tabs (two, spaced apart)
    for _ret_sign in [-1, 1]:
        _ret_rear_tab = (
            cq.Workplane("XY")
            .workplane(offset=_ret_z)
            .center(_dtray_cx + _ret_sign * (_cutout_w / 4),
                    _dtray_cy + _cutout_d / 2 - _ret_protrude / 2)
            .rect(_ret_w, _ret_protrude)
            .extrude(_ret_h)
        )
        base = base.union(_ret_rear_tab)

    # Clearance notches for Mudra snap hook engagement pockets
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

    # ── Front wall cable slots (matching device tray front-edge notches) ──
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
    _omi_wall_x = SLOT_POSITIONS["omi"][0] - 8
    omi_wall_slot = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - OMI_CRADLE_DEPTH)
        .center(_omi_wall_x, -STAND_D / 2)
        .rect(USBC_HEAD_W, WALL * 2 + 2)
        .extrude(USBC_HEAD_H)
    )
    base = base.cut(omi_wall_slot)

    # =====================================================================
    # CRADLE 5: Even G2 glasses case — open-bottom raised platform (rear)
    # Shallow walls keep the case in place. No floor — completely open
    # bottom so the VanBon charger's LCD screen is visible from above.
    # =====================================================================
    gx, gy = SLOT_POSITIONS["g2_case"]

    # Open-bottom pocket — shallow walls from top surface, no floor
    _g2_wall_h = 10    # raised wall height (shallow retainer)
    g2_pocket = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - _g2_wall_h)
        .center(gx, gy)
        .rect(G2_W, G2_D)
        .extrude(_g2_wall_h + 1)
    )
    base = base.cut(g2_pocket)

    # USB-C cable slot at rear
    g2_cable = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - _g2_wall_h)
        .center(gx, STAND_D / 2)
        .box(G2_CABLE_W, WALL * 4, _g2_wall_h,
             centered=[True, True, False])
    )
    base = base.cut(g2_cable)

    # =====================================================================
    # SLOT 6: iPad — channel at the very rear with back support wall.
    #
    # STRUCTURE (bottom to top):
    #   1. Vertical cable hole through LID_FLOOR (cable from bottom tray)
    #   2. iPad channel cut into top surface (Z=SPLIT_Z+LID_FLOOR to STAND_H)
    #   3. Front groove — iPad bottom edge sits in a recessed channel
    #      (two-point retention: front groove + back wall)
    #   4. Back wall blade slot for slide-in wall
    #
    # Cable path: bottom tray (open top) → vertical hole through
    #             LID_FLOOR → iPad channel → iPad connector
    # No horizontal tunnel — cable routes straight up.
    # =====================================================================
    ipad_y = STAND_D / 2 - IPAD_BACK_THICK - IPAD_SLOT_GAP / 2

    # ── iPad channel — shallow cut from top surface only ────────────
    # Instead of cutting all the way down to LID_FLOOR (Z=43), the
    # channel only needs to be deep enough to hold the iPad bottom
    # edge (~20mm). A shallower channel means the ceiling when printed
    # flipped is closer to the bed (less bridging height) and has
    # thick solid material underneath supporting it.
    #
    # Channel floor at Z=48 (10mm deep from top, 10mm above bed when
    # flipped). The solid material from Z=43–48 acts as a structural
    # bridge support, well within PLA+ bridging range at just 10mm
    # from the bed plate.
    _channel_floor_z = STAND_H - IPAD_SLOT_DEPTH  # Z=58-20=38, but clamped above LID_FLOOR
    _channel_floor_z = max(_channel_floor_z, SPLIT_Z + LID_FLOOR + 5)  # Z=48 minimum
    _channel_depth = STAND_H - _channel_floor_z  # 10mm
    ipad_channel = (
        cq.Workplane("XY")
        .workplane(offset=_channel_floor_z)
        .center(0, ipad_y)
        .rect(IPAD_SLOT_W, IPAD_SLOT_GAP)
        .extrude(_channel_depth + 1)
    )
    base = base.cut(ipad_channel)

    # ── Vertical cable hole — straight up through channel floor ──────
    # Small hole for USB-C cable to come up from the bottom tray
    # through the LID_FLOOR and channel floor to reach the iPad.
    _cable_hole_w = 18   # wide enough for USB-C head
    _cable_hole_d = 14   # deep enough for cable + bend
    ipad_cable_hole = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(0, ipad_y)
        .rect(_cable_hole_w, _cable_hole_d)
        .extrude(_channel_floor_z - SPLIT_Z + 1)  # through LID_FLOOR + solid body to channel
    )
    base = base.cut(ipad_cable_hole)

    # ── iPad back wall through-floor blade slot ──────────────────────
    # The wall blade slides in from the side and embeds into the tray
    # body below the channel floor. Cut from Z=42 up to channel floor.
    _blade_slot_w = IPAD_SLOT_W + 10 + 2  # wall width + exits both sides for slide-in
    _blade_slot_yd = IPAD_BACK_THICK + IPAD_WALL_TOL  # 4.4mm — tight fit around blade
    _blade_slot_y = STAND_D / 2 - IPAD_BACK_THICK / 2  # centered on wall Y
    _blade_slot_bottom = SPLIT_Z + 1       # Z=42 (1mm above split for integrity)
    _blade_slot_top = _channel_floor_z + 0.5  # through channel floor
    _blade_slot_h = _blade_slot_top - _blade_slot_bottom  # engagement depth
    blade_floor_slot = (
        cq.Workplane("XY")
        .workplane(offset=_blade_slot_bottom)
        .center(0, _blade_slot_y)
        .rect(_blade_slot_w, _blade_slot_yd)
        .extrude(_blade_slot_h)
    )
    base = base.cut(blade_floor_slot)

    # ── Snap detent bumps — resist lateral slide-out ────────────────
    # Two small bumps inside the slot near each end. The blade clicks
    # past them when the wall is fully seated, preventing slide-out.
    for detent_sign in [-1, +1]:
        _detent_x = detent_sign * (IPAD_SLOT_W / 2 + 5 - 30)
        detent = (
            cq.Workplane("XY")
            .workplane(offset=_blade_slot_bottom)
            .center(_detent_x, _blade_slot_y)
            .rect(IPAD_DETENT_W, IPAD_DETENT_H)
            .extrude(IPAD_DETENT_H)
        )
        base = base.union(detent)

    # ── Front groove — iPad bottom edge sits in a recessed channel ───
    # Instead of a raised lip (which creates a 225mm cantilever overhang
    # when printed flipped), the iPad's front leverage point is a groove
    # cut INTO the tray surface. The iPad bottom edge drops into this
    # channel, and gravity + the back wall hold it in place.
    # Same two-point physics: back wall pushes iPad forward, groove
    # catches the bottom edge so it can't slide forward off the stand.
    _groove_depth = IPAD_LIP_H     # 5mm deep (same retention as old lip height)
    _groove_w = IPAD_SLOT_W - 10   # 225mm — same span as old lip
    _groove_yd = IPAD_BACK_THICK   # 4mm wide — matches iPad/case thickness
    _groove_y = ipad_y - IPAD_SLOT_GAP / 2 - _groove_yd / 2  # front edge of channel
    ipad_groove = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - _groove_depth)
        .center(0, _groove_y)
        .rect(_groove_w, _groove_yd)
        .extrude(_groove_depth + 1)  # cut through top surface
    )
    base = base.cut(ipad_groove)

    # ── AC cable pass-through (left wall, matching bottom tray) ──────────
    # The VanBon's AC cable exits the short side (-X). Route it through
    # the top tray left wall so it can reach the outlet.
    charger_x, _charger_y = SLOT_POSITIONS["g2_case"]
    ac_top_slot = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z)
        .center(-STAND_W / 2, _charger_y)
        .box(WALL * 4, CHARGER_CABLE_SLOT_W, 12, centered=True)
    )
    base = base.cut(ac_top_slot)

    # ── Spare USB-A exit (back wall, matching bottom tray) ──────────────
    # 2 spare USB-A cables exit through the back wall so they're
    # accessible from behind the stand for ad-hoc charging.
    _spare_usb_slot_w = 36
    _spare_usb_slot_h = 14
    spare_usb_top = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z)
        .center(charger_x, STAND_D / 2)
        .box(_spare_usb_slot_w, WALL * 4, _spare_usb_slot_h,
             centered=[True, True, False])
    )
    base = base.cut(spare_usb_top)


    # =====================================================================
    # CONTINUOUS LID FLOOR — connects all sections for printability
    # =====================================================================
    # When the top tray is printed flipped (Z=58 on build plate), the
    # bottom face (Z=41) becomes the topmost printed surface. Without a
    # continuous floor, through-cuts fragment this surface into
    # disconnected islands that print as flimsy, unconnected pieces.
    #
    # Strategy: union a solid floor slab across the ENTIRE interior, then
    # re-cut ONLY minimal through-holes. The device tray area keeps its
    # floor intact (the tray sits ON TOP of it). Only the G2 viewing
    # window, iPad cable hole, and blade slot tongue need re-cuts.
    #
    # This eliminates all large unsupported spans when printed flipped:
    #   - No 242mm cable tunnel (removed — cable routes vertically)
    #   - No 170×95mm device tray cutout through floor (tray rests on floor)
    #   - No 225mm cantilever lip (replaced with recessed groove)
    #   - Blade slot re-cut is narrow (4.4mm Y) — trivial bridge
    # =====================================================================
    _floor_inset = WALL  # inset from outer walls (2.5mm) to avoid interfering with wall features
    _lid_floor_w = STAND_W - _floor_inset * 2   # 235mm
    _lid_floor_d = STAND_D - _floor_inset * 2   # 170mm

    lid_floor = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z)
        .box(_lid_floor_w, _lid_floor_d, LID_FLOOR,
             centered=[True, True, False])
    )
    base = base.union(lid_floor)

    # ── Re-cut essential through-holes in the new floor ──────────────────
    # Minimal cuts only — keep the floor as continuous as possible.

    # Device tray cable pass-throughs — 3 small holes for UH, R1, Omi
    # USB-C cables to route from bottom tray up through the floor into
    # the device tray area. Each hole is just USBC_HEAD_W × USBC_HEAD_H.
    for _cable_name, _cable_x_pos in [
        ("uh", SLOT_POSITIONS["uh_ring"][0]),
        ("r1", SLOT_POSITIONS["r1_ring"][0]),
        ("omi", SLOT_POSITIONS["omi"][0] - 8),  # offset to match front wall slot
    ]:
        _floor_cable = (
            cq.Workplane("XY")
            .workplane(offset=SPLIT_Z - 0.5)
            .center(_cable_x_pos, -STAND_D / 2 + WALL + 4)  # just inside front wall
            .rect(USBC_HEAD_W + 2, USBC_HEAD_H + 2)
            .extrude(LID_FLOOR + 1)
        )
        base = base.cut(_floor_cable)

    # Mudra cable hole — through floor under mudra pole position
    _mudra_floor_x, _mudra_floor_y = SLOT_POSITIONS["mudra"]
    _floor_mudra_cable = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(_mudra_floor_x, _mudra_floor_y)
        .rect(MUDRA_CABLE_CH_W, MUDRA_CABLE_CH_D)
        .extrude(LID_FLOOR + 1)
    )
    base = base.cut(_floor_mudra_cable)

    # Mudra snap clip clearance notches — re-cut through LID_FLOOR
    # These pockets were cut before LID_FLOOR union and need to be
    # re-opened so the snap hooks on the device tray can engage.
    _ms_socket_w_f = MUDRA_POLE_D + SNAP_TOL * 2
    _ms_pocket_depth_f = MUDRA_HOOK
    _ms_pocket_w_f = MUDRA_CLIP_W + SNAP_TOL * 2
    _ms_pocket_h_f = MUDRA_HOOK_H + 1
    for _ms_sign_f in [-1, 1]:
        _ms_x_f = _mudra_floor_x + _ms_sign_f * (_ms_socket_w_f / 2 + _ms_pocket_depth_f / 2)
        _ms_floor_clearance = (
            cq.Workplane("XY")
            .workplane(offset=DTRAY_FLOOR_Z - _ms_pocket_h_f - 0.5)
            .center(_ms_x_f, _mudra_floor_y)
            .rect(_ms_pocket_depth_f + DTRAY_TOL * 2, _ms_pocket_w_f + DTRAY_TOL * 2)
            .extrude(_ms_pocket_h_f + 1)
        )
        base = base.cut(_ms_floor_clearance)

    # G2 open-bottom cutout — cut through LID_FLOOR as a grid of
    # rectangular openings with ribs in BOTH directions. This keeps
    # bridge spans under 35mm in X AND Y when printed flipped.
    #
    # Grid: 3 ribs in X (dividing 176mm into 4 cols of ~42mm)
    #        1 rib in Y (dividing 68mm into 2 rows of ~33mm)
    # The charger LCD (~45×45mm) is visible through the center cells.
    _g2_cx, _g2_cy = SLOT_POSITIONS["g2_case"]
    _g2_rib = 2          # rib width in both directions

    # X direction: 3 ribs → 4 columns
    _g2_x_ribs = 3
    _g2_x_cells = _g2_x_ribs + 1
    _g2_x_open = G2_W - _g2_rib * _g2_x_ribs   # 170mm open
    _g2_cell_w = _g2_x_open / _g2_x_cells       # ~42.5mm per cell

    # Y direction: 1 rib → 2 rows
    _g2_y_ribs = 1
    _g2_y_cells = _g2_y_ribs + 1
    _g2_y_open = G2_D - _g2_rib * _g2_y_ribs    # 66mm open
    _g2_cell_d = _g2_y_open / _g2_y_cells        # 33mm per cell

    # Cut each grid cell
    for _col_i in range(_g2_x_cells):
        for _row_i in range(_g2_y_cells):
            _cell_cx = (_g2_cx - G2_W / 2 + _g2_cell_w / 2
                        + _col_i * (_g2_cell_w + _g2_rib))
            _cell_cy = (_g2_cy - G2_D / 2 + _g2_cell_d / 2
                        + _row_i * (_g2_cell_d + _g2_rib))
            _floor_g2_cell = (
                cq.Workplane("XY")
                .workplane(offset=SPLIT_Z - 0.5)
                .center(_cell_cx, _cell_cy)
                .rect(_g2_cell_w, _g2_cell_d)
                .extrude(LID_FLOOR + 1)
            )
            base = base.cut(_floor_g2_cell)

    # iPad cable vertical hole — cable from bottom tray up to iPad channel
    _ipad_y_floor = STAND_D / 2 - IPAD_BACK_THICK - IPAD_SLOT_GAP / 2
    _floor_ipad_cable = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(0, _ipad_y_floor)
        .rect(18, 14)  # matches cable hole in channel floor above
        .extrude(LID_FLOOR + 1)
    )
    base = base.cut(_floor_ipad_cable)

    # iPad blade slot — narrow re-cut (4.4mm Y) for wall tongue only
    _floor_blade_w = IPAD_SLOT_W + 10 + 2  # full width for slide-in
    _floor_blade_yd = IPAD_BACK_THICK + IPAD_WALL_TOL  # 4.4mm — narrow
    _floor_blade_y = STAND_D / 2 - IPAD_BACK_THICK / 2
    _floor_blade_slot = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z)
        .center(0, _floor_blade_y)
        .rect(_floor_blade_w, _floor_blade_yd)
        .extrude(LID_FLOOR + 0.5)
    )
    base = base.cut(_floor_blade_slot)

    return base


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

    # =====================================================================
    # CRADLE 3: Omi DevKit 2 — SIX-SIDED DIAMOND pocket
    # =====================================================================
    ox, oy = SLOT_POSITIONS["omi"]
    diamond_pts = six_sided_diamond_points(OMI_LONG_EDGE + TOL * 2, OMI_SHORT_EDGE + TOL * 2)
    diamond_closed = diamond_pts + [diamond_pts[0]]

    # Limit pocket depth so it doesn't punch through the tray floor.
    # The pendant is 13mm thick; the pocket must stop at DTRAY_FLOOR_Z + 1mm
    # to leave a solid floor. Cable passes through a small hole instead.
    _omi_max_depth = STAND_H - DTRAY_FLOOR_Z - 1  # leave 1mm floor
    _omi_actual_depth = min(OMI_CRADLE_DEPTH, _omi_max_depth)

    omi_pocket = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - _omi_actual_depth)
        .center(ox, oy)
        .polyline(diamond_closed)
        .close()
        .extrude(_omi_actual_depth + 1)
    )
    omi_pocket = omi_pocket.edges("|Z").fillet(OMI_VERTEX_R)
    tray = tray.cut(omi_pocket)

    # USB-C port notch — front-left of diamond
    _omi_front_y_world = oy + min(p[1] for p in diamond_pts)
    _omi_port_x = ox - 8
    omi_port_slot = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - _omi_actual_depth)
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
    _omi_socket_z = STAND_H - _omi_actual_depth
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

    return tray


# =============================================================================
# BUILD IPAD COVER PLATE (removable)
# =============================================================================

def build_ipad_cover():
    """Removable cover plate that slides into rails inside the iPad channel.

    Sits on top of the solid floor, covering the cable opening and
    providing a clean surface. Slides in from either side on continuous
    L-shaped rail grooves cut into the front and back channel walls.

    The cover has a centered cable notch so the USB-C connector can
    poke up through to reach the iPad even with the cover in place.

    Printed as a separate piece — slide in from left or right.
    """
    ipad_y = STAND_D / 2 - IPAD_BACK_THICK - IPAD_SLOT_GAP / 2
    _tunnel_h = 8
    _tunnel_z = SPLIT_Z + 1
    _floor_z = _tunnel_z + _tunnel_h       # Z=50
    _floor_thick = 2.5
    _channel_floor_z = _floor_z + _floor_thick  # Z=52.5
    _cover_thick = 2
    _rail_depth = 3
    _rail_h = _cover_thick + 1

    # Cover plate slides into the rail grooves. Its depth (Y) matches
    # the rail groove span: full channel width including the rail slots.
    # Width (X) is the full iPad slot width minus a tiny clearance.
    _cover_w = IPAD_SLOT_W - TOL * 2          # nearly full slot width
    _cover_d = IPAD_SLOT_GAP - TOL * 2        # spans channel including rails

    cover = (
        cq.Workplane("XY")
        .workplane(offset=_channel_floor_z)
        .center(0, ipad_y)
        .rect(_cover_w, _cover_d)
        .extrude(_cover_thick)
    )

    # Cable notch — centered slot so USB-C connector can reach the iPad.
    _notch_w = 20   # wider than USB-C head for easy cable routing
    _notch_d = _cover_d + 2  # cuts all the way through front-to-back
    cable_notch = (
        cq.Workplane("XY")
        .workplane(offset=_channel_floor_z - 0.5)
        .center(0, ipad_y)
        .rect(_notch_w, _notch_d)
        .extrude(_cover_thick + 1)
    )
    cover = cover.cut(cable_notch)

    return cover


# =============================================================================
# BUILD IPAD WALL (separate slide-in part)
# =============================================================================

def build_ipad_wall():
    """iPad back wall — drops into the tray through the iPad channel floor.

    The wall has a downward blade that passes through a slot in the
    iPad channel floor, embedding 10.5mm into the solid tray body below.
    The blade is the same thickness as the wall (4mm) so it's a simple
    flat piece — no L-shape needed.

    Assembly: slide the wall in from either side along the channel.
    The blade rides in the floor slot, snap detents click when seated.

    The blade sits in solid PETG on all four sides:
      Front: 24mm+ of tray body ahead
      Back:  tray body + 2.5mm rear stand wall behind
      Ends:  closed by slot walls when seated

    Prints flat on its back. Built at origin, centered on X.
    Z=0 is at the blade bottom. Wall body starts at Z=blade_h.
    """
    _wall_w = IPAD_SLOT_W + 10     # 245mm
    _wall_h = IPAD_BACK_H          # 60mm
    _wall_t = IPAD_BACK_THICK      # 4mm

    # Blade: same thickness as wall, extends downward
    # Depth matches the slot in the tray body (channel floor to SPLIT_Z+1)
    _channel_floor_z = SPLIT_Z + 1 + 8 + 2.5   # 52.5
    _blade_bottom_z = SPLIT_Z + 1               # 42
    _blade_h = _channel_floor_z - _blade_bottom_z  # 10.5mm
    _blade_t = _wall_t - IPAD_WALL_TOL          # 3.6mm (snug in 4.4mm slot)
    _blade_w = _wall_w - IPAD_WALL_TOL * 2      # slightly narrower for slide

    # ── Blade (Z=0 to Z=_blade_h) ────────────────────────────────────
    blade = (
        cq.Workplane("XY")
        .rect(_blade_w, _blade_t)
        .extrude(_blade_h)
    )

    # ── Wall body (Z=_blade_h upward) ────────────────────────────────
    # The wall body is wider than the blade (full 4mm vs 3.6mm blade).
    # It sits in the iPad channel above the floor. The channel is 24mm
    # deep in Y — plenty of room. The wall is only 4mm thick.
    wall_body = (
        cq.Workplane("XY")
        .workplane(offset=_blade_h)
        .rect(_wall_w, _wall_t)
        .extrude(_wall_h)
    )
    wall = blade.union(wall_body)

    return wall


# =============================================================================
# BUILD MUDRA POLE (separate snap-in part)
# =============================================================================

def build_mudra_pole():
    """Mudra Link L-pole with flush charger pocket and snap-clip base.

    Standalone part that inserts into a socket on the top tray.
    Printed upright — no supports needed.

    Geometry (unchanged from original inline design):
      - Vertical post: MUDRA_POLE_D x MUDRA_POLE_W x MUDRA_POLE_H
      - Horizontal shelf at top: MUDRA_SHELF_L x MUDRA_POLE_W x MUDRA_SHELF_H
      - Flush charger pocket in shelf top (open from above, chamfered lip)
      - Internal cable channel: vertical cavity + horizontal slot to charger bay
      - Cable exits through the open bottom face of the pole base

    New: snap clip tabs on the base that catch the underside of the top tray.
    """

    # ── Vertical post at origin ──────────────────────────────────────────
    post = (
        cq.Workplane("XY")
        .rect(MUDRA_POLE_D, MUDRA_POLE_W)
        .extrude(MUDRA_POLE_H)
    )

    # ── Horizontal shelf extending right (+X) from top of post ───────────
    shelf = (
        cq.Workplane("XY")
        .workplane(offset=MUDRA_POLE_H - MUDRA_SHELF_H)
        .center(MUDRA_POLE_D / 2 + MUDRA_SHELF_L / 2, 0)
        .rect(MUDRA_SHELF_L, MUDRA_POLE_W)
        .extrude(MUDRA_SHELF_H)
    )

    pole = post.union(shelf)

    # ── Charger bay — flush pocket cut from shelf top ────────────────────
    charger_bay_x = MUDRA_POLE_D / 2 + MUDRA_SHELF_L / 2
    shelf_top_z = MUDRA_POLE_H

    charger_bay = (
        cq.Workplane("XY")
        .workplane(offset=shelf_top_z - MUDRA_CHARGER_H)
        .center(charger_bay_x, 0)
        .rect(MUDRA_CHARGER_D, MUDRA_CHARGER_W)
        .extrude(MUDRA_CHARGER_H + 1)
    )
    pole = pole.cut(charger_bay)

    # ── Chamfered lip around charger pocket opening ──────────────────────
    chamfer_lip = (
        cq.Workplane("XY")
        .workplane(offset=shelf_top_z + 0.1)
        .center(charger_bay_x, 0)
        .rect(MUDRA_CHARGER_D + 4, MUDRA_CHARGER_W + 4)
        .workplane(offset=-2.0)
        .center(charger_bay_x, 0)
        .rect(MUDRA_CHARGER_D, MUDRA_CHARGER_W)
        .loft()
    )
    pole = pole.cut(chamfer_lip)

    # ── Cable channel — horizontal slot from charger bay to post ─────────
    cable_slot_z = shelf_top_z - MUDRA_CHARGER_H
    slot_length = charger_bay_x - MUDRA_CHARGER_D / 2
    cable_horiz = (
        cq.Workplane("XY")
        .workplane(offset=cable_slot_z)
        .center(slot_length / 2, 0)
        .rect(slot_length + 2, MUDRA_CABLE_CH_W)
        .extrude(MUDRA_CABLE_CH_W)
    )
    pole = pole.cut(cable_horiz)

    # ── Vertical cable cavity through the post ───────────────────────────
    cable_cavity_vert = (
        cq.Workplane("XY")
        .rect(MUDRA_CABLE_CH_D, MUDRA_CABLE_CH_W)
        .extrude(cable_slot_z + MUDRA_CABLE_CH_W + 1)
    )
    pole = pole.cut(cable_cavity_vert)

    # ── Snap clip tabs on the base ───────────────────────────────────────
    # Two cantilever hooks, one on each X-axis face of the pole base.
    # They extend downward from the pole base into negative Z.
    # When inserting the pole into the socket, the hooks flex inward, pass
    # through the socket, and snap out to catch the bottom face of the top tray.
    #
    # Uses MUDRA_CLIP_* constants (beefier than the tray-to-tray SNAP_* clips).
    #
    # STRUCTURAL DESIGN: The clip arms are built as thick buttresses that
    # overlap HALF the pole width (5mm) and extend 6mm up into the pole body.
    # Triangular gussets on both sides of each arm create a smooth load path
    # from the clip into the pole wall. This prevents the crack-at-the-seam
    # failure seen in earlier prints where thin arms broke off the bed plate.
    _clip_overlap = 5.0   # mm of arm overlapping into the pole body (half of 10mm radius)
    _arm_root_h = 6       # mm the arm extends UP into the pole body
    _gusset_h = 5         # mm tall triangular gusset at the arm-to-pole junction
    _gusset_depth = 4     # mm the gusset extends along the pole wall (Y direction)

    for side_sign in [-1, 1]:
        # Arm center shifted well into the pole body for a solid union
        clip_x = side_sign * (MUDRA_POLE_D / 2 + MUDRA_CLIP_T / 2 - _clip_overlap)

        # Cantilever arm: extends from -CLIP_H (below base) to +_arm_root_h (into pole)
        arm = (
            cq.Workplane("XY")
            .workplane(offset=-MUDRA_CLIP_H)
            .center(clip_x, 0)
            .rect(MUDRA_CLIP_T, MUDRA_CLIP_W)
            .extrude(MUDRA_CLIP_H + _arm_root_h)
        )
        pole = pole.union(arm)

        # Triangular gussets on both Y-sides of the arm where it meets the pole.
        # These spread the load from the clip into the pole wall, preventing
        # the clean fracture line that killed previous prints.
        for y_sign in [-1, 1]:
            # Gusset is a wedge: full thickness at Z=0 (pole base), tapering
            # to zero at Z=_gusset_h. Runs along the pole face in Y.
            gusset_y = y_sign * (MUDRA_CLIP_W / 2 + _gusset_depth / 2)
            # Build as a lofted solid from a rectangle at base to a thin line at top
            gusset = (
                cq.Workplane("XY")
                .center(clip_x, gusset_y)
                .rect(MUDRA_CLIP_T, _gusset_depth)
                .workplane(offset=_gusset_h)
                .center(clip_x, gusset_y)
                .rect(MUDRA_CLIP_T, 0.1)  # taper to near-zero
                .loft()
            )
            pole = pole.union(gusset)

        # Hook nub at the bottom of the arm (outward-facing)
        # Catches the underside of the top tray floor.
        # Position the nub so its outer edge protrudes past the pole face
        # by MUDRA_HOOK mm — this is what catches the socket lip.
        # The nub is anchored to the arm's outer edge and extends outward.
        _pole_face_x = side_sign * MUDRA_POLE_D / 2  # pole outer face
        nub_x = _pole_face_x + side_sign * MUDRA_HOOK / 2  # centered on the overhang
        nub = (
            cq.Workplane("XY")
            .workplane(offset=-MUDRA_CLIP_H)
            .center(nub_x, 0)
            .rect(MUDRA_HOOK, MUDRA_CLIP_W)
            .extrude(MUDRA_HOOK_H)
        )
        pole = pole.union(nub)

    return pole


# =============================================================================
# TILT PLATES (drop-in cradle inserts with pin hinges)
# =============================================================================

def build_uh_tilt_plate():
    """UH Ring tilt plate — 40x40mm square with rounded corners.

    Built at origin (centered on X/Y, Z=0 to TILT_PLATE_T).
    Two hinge barrels on the -Y edge (FRONT), so the rear edge tilts UP
    toward the user when the push rod pushes from below.
    Captured slot on underside for push rod T-head.
    """
    plate_side = UH_SIDE - TILT_CLEARANCE * 2  # 40mm

    # ── Main plate body ──────────────────────────────────────────────────
    plate = (
        cq.Workplane("XY")
        .rect(plate_side, plate_side)
        .extrude(TILT_PLATE_T)
    )
    plate = plate.edges("|Z").fillet(UH_CORNER_R - TILT_CLEARANCE)

    # ── Two hinge barrels on FRONT (-Y) edge ─────────────────────────────
    # Barrels protrude beyond the front edge, axis parallel to X.
    # Spaced symmetrically, ~10mm from each end.
    # Negative Y = front edge (toward user).
    barrel_spacing = plate_side - 2 * 10  # 20mm apart
    barrel_center_y = -(plate_side / 2 + HINGE_BARREL_PROTRUDE - HINGE_BARREL_OD / 2)

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


def build_r1_tilt_plate():
    """R1 Ring tilt plate — 31mm diameter disc.

    Built at origin (centered on X/Y, Z=0 to TILT_PLATE_T).
    The front (-Y) edge has a flat chord for hinge barrel mounting,
    so the rear edge tilts UP toward the user when pushed from below.
    Two hinge barrels on the flat, captured slot on underside.
    """
    plate_dia = R1_DIA - TILT_CLEARANCE * 2  # 31mm

    # ── Main disc ────────────────────────────────────────────────────────
    plate = (
        cq.Workplane("XY")
        .circle(plate_dia / 2)
        .extrude(TILT_PLATE_T)
    )

    # ── Flat chord on FRONT (-Y) edge for barrel mounting ────────────────
    # Cut a 2mm slice off the front to create a flat mounting surface.
    # The flat is at Y = -(plate_dia/2 - 2) = -13.5mm from center.
    _chord_cut_y = plate_dia / 2 - 2  # 13.5mm (absolute distance)
    chord_cut = (
        cq.Workplane("XY")
        .workplane(offset=-0.1)
        .center(0, -(_chord_cut_y + 10))  # center of block beyond the FRONT chord
        .rect(plate_dia + 2, 20)
        .extrude(TILT_PLATE_T + 0.2)
    )
    plate = plate.cut(chord_cut)

    # ── Two hinge barrels on the FRONT flat chord ────────────────────────
    # Chord width at Y=-13.5: w = 2*sqrt(r^2 - y^2) ≈ 15.2mm
    # Two 8mm barrels need ~20mm — so space them 8mm apart (4mm from center each)
    barrel_spacing = 8  # closer together to fit on the chord
    barrel_center_y = -(_chord_cut_y + HINGE_BARREL_PROTRUDE - HINGE_BARREL_OD / 2)

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


def build_omi_tilt_plate():
    """Omi DevKit 2 tilt plate — six-sided diamond with vertex fillets.

    Built at origin (centered on X/Y, Z=0 to TILT_PLATE_T).
    Uses the same six_sided_diamond_points() helper as the pocket.
    Hinge barrels at the frontmost vertex (-Y), with a small flat added,
    so the rear edge tilts UP toward the user when pushed from below.
    Captured slot on underside for push rod T-head.
    """
    # Diamond points with clearance reduction
    plate_long = OMI_LONG_EDGE + TOL * 2 - TILT_CLEARANCE * 2   # 31mm
    plate_short = OMI_SHORT_EDGE + TOL * 2 - TILT_CLEARANCE * 2  # 16mm
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

    # ── Find the frontmost vertex (min Y) for barrel placement ───────────
    front_y = min(p[1] for p in pts)  # frontmost Y coordinate (negative)

    # Add a small flat at the front vertex to mount barrels.
    # Cut 2mm off the front to create a flat surface.
    _chord_cut_y = front_y + 2  # e.g. -rear_y + 2 (negative, closer to center)
    chord_cut = (
        cq.Workplane("XY")
        .workplane(offset=-0.1)
        .center(0, _chord_cut_y - 10)  # center of block beyond the FRONT chord
        .rect(50, 20)  # wide enough to span the diamond
        .extrude(TILT_PLATE_T + 0.2)
    )
    plate = plate.cut(chord_cut)

    # ── Two hinge barrels on the FRONT flat ──────────────────────────────
    barrel_spacing = 8
    barrel_center_y = _chord_cut_y - HINGE_BARREL_PROTRUDE + HINGE_BARREL_OD / 2

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
    # Screw hole through the tab face (Y axis)
    horn_hole = (
        cq.Workplane("XZ")
        .workplane(offset=-PUSH_ROD_W / 2 - 0.5)
        .center(0, -PUSH_ROD_HORN_TAB_H / 2)
        .circle(PUSH_ROD_HORN_HOLE / 2)
        .extrude(PUSH_ROD_W + 1)
    )
    rod = rod.union(horn_tab).cut(horn_hole)

    return rod


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

    # ── Tilt plates (shown tilted ~15° for visual preview) ───────────────
    # Show plates partially tilted so you can see the mechanism concept.
    _tilt_preview_angle = 15  # degrees, partial tilt for preview

    # UH Ring tilt plate ghost — hinge on FRONT (-Y) edge
    _uh_plate = build_uh_tilt_plate()
    _uh_hinge_y = SLOT_POSITIONS["uh_ring"][1] - (UH_SIDE - TILT_CLEARANCE * 2) / 2
    _uh_hinge_z = STAND_H - UH_CRADLE_DEPTH + TILT_PLATE_T / 2
    _uh_plate_pos = _uh_plate.translate((
        SLOT_POSITIONS["uh_ring"][0],
        SLOT_POSITIONS["uh_ring"][1],
        STAND_H - UH_CRADLE_DEPTH
    ))
    _uh_plate_tilted = _uh_plate_pos.rotate(
        (SLOT_POSITIONS["uh_ring"][0], _uh_hinge_y, _uh_hinge_z),
        (SLOT_POSITIONS["uh_ring"][0] + 1, _uh_hinge_y, _uh_hinge_z),
        _tilt_preview_angle  # positive = rear edge rises toward user
    )
    parts["tilt_plate_uh"] = (_uh_plate_tilted, (0.4, 0.8, 0.4, 0.6))

    # R1 Ring tilt plate ghost — hinge on FRONT (-Y) edge
    _r1_plate = build_r1_tilt_plate()
    _r1_chord_y = (R1_DIA - TILT_CLEARANCE * 2) / 2 - 2
    _r1_hinge_y = SLOT_POSITIONS["r1_ring"][1] - _r1_chord_y  # front (-Y)
    _r1_hinge_z = STAND_H - R1_CRADLE_DEPTH + TILT_PLATE_T / 2
    _r1_plate_pos = _r1_plate.translate((
        SLOT_POSITIONS["r1_ring"][0],
        SLOT_POSITIONS["r1_ring"][1],
        STAND_H - R1_CRADLE_DEPTH
    ))
    _r1_plate_tilted = _r1_plate_pos.rotate(
        (SLOT_POSITIONS["r1_ring"][0], _r1_hinge_y, _r1_hinge_z),
        (SLOT_POSITIONS["r1_ring"][0] + 1, _r1_hinge_y, _r1_hinge_z),
        _tilt_preview_angle  # positive = rear edge rises toward user
    )
    parts["tilt_plate_r1"] = (_r1_plate_tilted, (0.4, 0.8, 0.4, 0.6))

    # Omi tilt plate ghost — hinge on FRONT (-Y) edge
    _omi_plate = build_omi_tilt_plate()
    _omi_pts_ghost = six_sided_diamond_points(
        OMI_LONG_EDGE + TOL * 2 - TILT_CLEARANCE * 2,
        OMI_SHORT_EDGE + TOL * 2 - TILT_CLEARANCE * 2
    )
    _omi_front_local = min(p[1] for p in _omi_pts_ghost) + 2  # front chord
    _omi_hinge_y = SLOT_POSITIONS["omi"][1] + _omi_front_local  # front (-Y)
    _omi_hinge_z = STAND_H - OMI_CRADLE_DEPTH + TILT_PLATE_T / 2
    _omi_plate_pos = _omi_plate.translate((
        SLOT_POSITIONS["omi"][0],
        SLOT_POSITIONS["omi"][1],
        STAND_H - OMI_CRADLE_DEPTH
    ))
    _omi_plate_tilted = _omi_plate_pos.rotate(
        (SLOT_POSITIONS["omi"][0], _omi_hinge_y, _omi_hinge_z),
        (SLOT_POSITIONS["omi"][0] + 1, _omi_hinge_y, _omi_hinge_z),
        _tilt_preview_angle  # positive = rear edge rises toward user
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

    return parts


# =============================================================================
# BUILD AND DISPLAY
# =============================================================================

bottom_tray = build_bottom_tray()
top_tray = build_top_tray()
device_tray = build_device_tray()
ipad_cover = build_ipad_cover()
ipad_wall = build_ipad_wall()
mudra_pole = build_mudra_pole()

show_object(bottom_tray, name="bottom_tray",
            options={"color": (0.15, 0.15, 0.17, 0.9)})
show_object(top_tray, name="top_tray",
            options={"color": (0.2, 0.2, 0.22, 0.95)})
show_object(device_tray, name="device_tray",
            options={"color": (0.25, 0.25, 0.27, 0.95)})
show_object(ipad_cover, name="ipad_cover",
            options={"color": (0.3, 0.3, 0.32, 0.9)})

# iPad wall displayed at assembly position (inserted into rear groove)
# Wall blade bottom at Z = SPLIT_Z + 1 (42mm), drops through channel floor.
# Wall Y: centered on the rear edge where the old back wall was.
_ipad_wall_y = STAND_D / 2 - IPAD_BACK_THICK / 2
_ipad_wall_z = SPLIT_Z + 1   # blade bottom sits just above the split plane
ipad_wall_assembly = ipad_wall.translate((0, _ipad_wall_y, _ipad_wall_z))
show_object(ipad_wall_assembly,
            name="ipad_wall",
            options={"color": (0.28, 0.28, 0.30, 0.95)})

# Mudra pole displayed at its assembly position (inserted into the top tray socket)
mx, my = SLOT_POSITIONS["mudra"]
mudra_pole_assembly = mudra_pole.translate((mx, my, STAND_H))
show_object(mudra_pole_assembly,
            name="mudra_pole",
            options={"color": (0.25, 0.25, 0.27, 0.95)})

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

r1_tilt_plate = build_r1_tilt_plate()
_r1_plate_assembly = r1_tilt_plate.translate((
    SLOT_POSITIONS["r1_ring"][0],
    SLOT_POSITIONS["r1_ring"][1],
    STAND_H - R1_CRADLE_DEPTH
))
show_object(_r1_plate_assembly, name="r1_tilt_plate",
            options={"color": (0.6, 0.85, 0.6, 0.9)})
pass  # keep loop body after show_object is stripped by export script

omi_tilt_plate = build_omi_tilt_plate()
_omi_plate_assembly = omi_tilt_plate.translate((
    SLOT_POSITIONS["omi"][0],
    SLOT_POSITIONS["omi"][1],
    STAND_H - OMI_CRADLE_DEPTH
))
show_object(_omi_plate_assembly, name="omi_tilt_plate",
            options={"color": (0.6, 0.85, 0.6, 0.9)})
pass  # keep loop body after show_object is stripped by export script

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

# Ghost visualization objects (translucent component overlays)
ghosts = build_ghost_components()
for comp_name, (comp_solid, comp_color) in ghosts.items():
    show_object(comp_solid, name=f"ghost_{comp_name}", options={"color": comp_color})
    pass  # keep loop body after show_object is stripped by export script
