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
STAND_H = 58           # TOTAL assembled height (bottom + top)
WALL = 2.5             # wall thickness
CORNER_R = 5           # corner fillet radius
TOL = 1.0              # print tolerance per side (1mm clearance each side for snug drop-in fit)

# --- Two-part split ---
# Bottom tray: cable management, VanBon charger, rubber feet
# Top tray: device pockets, Mudra pole, iPad wall — sits on top of bottom
# Bottom tray height = 41mm to house VanBon charger (33mm + 3mm floor + 2.5mm ceiling + margin).
SPLIT_Z = 41           # Z where the two parts meet (bottom tray height)
TOP_H = STAND_H - SPLIT_Z   # top tray height (16mm)
SNAP_TOL = 0.3         # clearance for snap-fit (per side)
SNAP_LIP = 1.5         # ledge depth for snap engagement
SNAP_CLIP_W = 12       # width of each snap clip
SNAP_CLIP_H = 8        # clip cantilever height
SNAP_HOOK = 1.2        # hook overhang that catches the lip

# --- Base platform (bottom tray internals) ---
BASE_H = 3             # solid floor at very bottom of bottom tray
CHANNEL_H = SPLIT_Z - BASE_H - WALL  # cable channel height (~8.5mm)
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
IPAD_LIP_H = 5                # front lip to stop iPad sliding forward
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
    # direction. The cable winding posts on the side looms, Velcro
    # strap slots, and arch clips handle all the organization.

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

    # ── Side pockets: cable corridor + loom + Velcro slots ──────────────
    # Each side pocket (48mm wide × 170mm long) serves TWO purposes:
    #
    #   INNER CORRIDOR (charger side, ~20mm wide) — CLEAR PATH for
    #   cables routing from the charger's USB-A ports (rear) through
    #   to the front channel and up to each device. No posts here.
    #
    #   OUTER LOOM (wall side, ~25mm wide) — Cable winding posts
    #   where excess cable length gets wrapped up. Velcro strap slots
    #   between posts for cinching bundles.
    #
    # This way cables route naturally: plug into charger rear → run
    # forward along the inner corridor → pass through the front spine
    # gaps → up to each device. Excess cable wraps on the outer loom.
    #
    _post_dia = 5       # slim posts, cable-friendly
    _post_h = 25        # tall enough for several wraps
    _post_spacing_y = 22  # spacing between posts along Y

    # Outer loom: posts pushed toward the outer wall
    # Inner corridor: clear 20mm path next to charger bay
    _corridor_w = 20    # clear cable routing corridor (no posts)
    _col1_offset = 26   # first post column offset from charger wall
    _col2_offset = 40   # second post column offset from charger wall

    # Velcro strap slots: 15mm × 3mm through the floor
    _velcro_slot_l = 15
    _velcro_slot_w = 3

    # Posts run the full length of the pocket
    _pocket_y_start = -STAND_D / 2 + WALL + 12
    _pocket_y_end = STAND_D / 2 - WALL - 12

    for side_sign in [-1, 1]:  # -1 = left pocket, +1 = right pocket
        if side_sign == -1:
            edge_x = _charger_left
            col1_x = edge_x - _col1_offset
            col2_x = edge_x - _col2_offset
        else:
            edge_x = _charger_right
            col1_x = edge_x + _col1_offset
            col2_x = edge_x + _col2_offset

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

        # ── Velcro strap slots between the loom columns ──
        # Thread Velcro down through one slot, under floor, up next slot.
        _velcro_x = (col1_x + col2_x) / 2
        for i in range(0, len(_col1_ys) - 1, 2):
            slot_y = (_col1_ys[i] + _col1_ys[i + 1]) / 2
            velcro = (
                cq.Workplane("XY")
                .workplane(offset=-0.5)
                .center(_velcro_x, slot_y)
                .rect(_velcro_slot_l, _velcro_slot_w)
                .extrude(BASE_H + 2)
            )
            tray = tray.cut(velcro)

        # ── Velcro slot in the inner corridor too ──
        # For cinching the routed cables (not the wrapped ones).
        _corridor_velcro_x = edge_x + side_sign * (_corridor_w / 2)
        for vy in [_charger_front - 10, charger_y, _charger_back + 10]:
            if -STAND_D / 2 + WALL + 10 < vy < STAND_D / 2 - WALL - 10:
                velcro = (
                    cq.Workplane("XY")
                    .workplane(offset=-0.5)
                    .center(_corridor_velcro_x, vy)
                    .rect(_velcro_slot_l, _velcro_slot_w)
                    .extrude(BASE_H + 2)
                )
                tray = tray.cut(velcro)

    # ── Cable routing clips in the front channel ─────────────────────────
    # Small arch bridges near each device's cable pass-through.
    # Cable threads under the arch, stays organized on its way up.
    _clip_w = 14       # slightly wider than USB cable
    _clip_h = 8        # arch height (cable passes under)
    _clip_t = 2.5      # arch wall thickness
    _clip_y = FRONT_ROW_Y + 12  # just behind device row, in the channel

    for name in ("uh_ring", "r1_ring", "omi", "mudra"):
        px, py = SLOT_POSITIONS[name]
        arch_outer = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H)
            .center(px, _clip_y)
            .box(_clip_w + _clip_t * 2, _clip_t, _clip_h,
                 centered=[True, True, False])
        )
        arch_inner = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H)
            .center(px, _clip_y)
            .box(_clip_w, _clip_t + 2, _clip_h - _clip_t,
                 centered=[True, True, False])
        )
        tray = tray.union(arch_outer)
        tray = tray.cut(arch_inner)

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
    _ch_z = BASE_H - LED_CHANNEL_D  # channel bottom (may cut into floor)

    # Left wall segment (runs along Y)
    led_ch_left = (
        cq.Workplane("XY")
        .workplane(offset=_ch_z)
        .center(_inner_left + _ch_inset + LED_CHANNEL_W / 2,
                (_inner_front + _inner_back) / 2)
        .rect(LED_CHANNEL_W, _inner_back - _inner_front)
        .extrude(LED_CHANNEL_D + 0.5)
    )
    tray = tray.cut(led_ch_left)

    # Front wall segment (runs along X)
    led_ch_front = (
        cq.Workplane("XY")
        .workplane(offset=_ch_z)
        .center(0, _inner_front + _ch_inset + LED_CHANNEL_W / 2)
        .rect(_inner_right - _inner_left, LED_CHANNEL_W)
        .extrude(LED_CHANNEL_D + 0.5)
    )
    tray = tray.cut(led_ch_front)

    # Right wall segment (runs along Y)
    led_ch_right = (
        cq.Workplane("XY")
        .workplane(offset=_ch_z)
        .center(_inner_right - _ch_inset - LED_CHANNEL_W / 2,
                (_inner_front + _inner_back) / 2)
        .rect(LED_CHANNEL_W, _inner_back - _inner_front)
        .extrude(LED_CHANNEL_D + 0.5)
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
    _wire_d = 3    # groove depth
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
    """Top tray: device pockets, Mudra pole socket, iPad wall. Sits on bottom tray."""

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

    # ── Cable pass-through holes (matching bottom tray positions) ────────
    # UH, R1, and Omi have custom cable cuts in their cradle sections below.
    # Only cut generic holes for devices that don't have custom routing.
    for name, (px, py) in SLOT_POSITIONS.items():
        if name in ("uh_ring", "r1_ring", "omi"):
            continue  # handled in individual cradle sections

        hw = USBC_HEAD_W + 2 if name == "g2_case" else USBC_HEAD_W
        hh = USBC_HEAD_H + 2 if name == "g2_case" else USBC_HEAD_H

        hole = (
            cq.Workplane("XY")
            .workplane(offset=SPLIT_Z - 0.5)
            .center(px, py)
            .rect(hw, hh)
            .extrude(TOP_H + 1)
        )
        base = base.cut(hole)

    # =====================================================================
    # CRADLE 1: Ultrahuman Ring Air — SQUARE pocket, rounded corners
    # Cable exits LEFT (-X), consistent with R1, Omi, and Mudra.
    # All front-row cables route in the same direction for clean management.
    # =====================================================================
    ux, uy = SLOT_POSITIONS["uh_ring"]
    uh_pocket = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - UH_CRADLE_DEPTH)
        .center(ux, uy)
        .rect(UH_SIDE, UH_SIDE)
        .extrude(UH_CRADLE_DEPTH + 1)
    )
    base = base.cut(uh_pocket)

    # Left wall slot — USB-C cable exits left face (-X), same direction as other devices.
    uh_left_slot = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - UH_CRADLE_DEPTH)
        .center(ux - UH_SIDE / 2, uy)
        .rect(WALL + 2, USBC_HEAD_W)
        .extrude(USBC_HEAD_H)
    )
    base = base.cut(uh_left_slot)

    # Floor pass-through at left edge (cable drops down into bottom tray)
    uh_cable = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(ux - UH_SIDE / 2, uy)
        .rect(USBC_HEAD_W, USBC_HEAD_H)
        .extrude(TOP_H + 1)
    )
    base = base.cut(uh_cable)

    # =====================================================================
    # CRADLE 2: Even R1 Ring — CIRCULAR pocket
    # Fixed cable exits from the LEFT edge (-X) of the disc.
    # Cable is thin (~4mm), not a removable USB-C head.
    # =====================================================================
    rx, ry = SLOT_POSITIONS["r1_ring"]
    r1_cup = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - R1_CRADLE_DEPTH)
        .center(rx, ry)
        .circle(R1_DIA / 2)
        .extrude(R1_CRADLE_DEPTH + 1)
    )
    base = base.cut(r1_cup)

    # Side groove — notch in the left wall of the circular pocket for
    # the fixed cable to exit. Sized for USB-C head to feed through
    # during assembly (head is 14×9mm), then cable sits in the groove.
    r1_cable_groove = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - R1_CRADLE_DEPTH)
        .center(rx - R1_DIA / 2, ry)
        .rect(10, USBC_HEAD_W)  # wide enough for USB-C head to pass through
        .extrude(USBC_HEAD_H)
    )
    base = base.cut(r1_cable_groove)

    # Floor pass-through at left edge — must fit USB-C head (the other
    # end of the fixed cable needs to feed through to reach the hub).
    r1_cable = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(rx - R1_DIA / 2, ry)
        .rect(USBC_HEAD_W, USBC_HEAD_H)
        .extrude(TOP_H + 1)
    )
    base = base.cut(r1_cable)

    # =====================================================================
    # CRADLE 3: Omi DevKit 2 — SIX-SIDED DIAMOND pocket
    # USB-C port is on the LEFT long side (30mm), offset ~8mm from the
    # left corner (first quarter of the side). Port faces -X direction.
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
    # Small fillet on vertices to prevent sharp edges
    omi_pocket = omi_pocket.edges("|Z").fillet(OMI_VERTEX_R)
    base = base.cut(omi_pocket)

    # USB-C port slot — perpendicular to the left long side (Edge 4).
    # Edge 4 runs at 60° from v4(-22.5, -6.5) to v5(-7.5, 19.5).
    # The port is ~8mm from v4 (the lower-left corner of that edge).
    # The connector inserts PERPENDICULAR to the edge (inward normal = -30°).
    # Slot is rotated to match the angled wall.
    _edge4_angle = 60.0  # degrees, direction of edge 4
    _port_offset_along_edge = 8.0  # mm from v4 corner
    # Position along edge 4, offset 8mm from v4
    _v4_x, _v4_y = -22.5, -6.5  # vertex 4 (relative to diamond center)
    _port_local_x = _v4_x + _port_offset_along_edge * math.cos(math.radians(_edge4_angle))
    _port_local_y = _v4_y + _port_offset_along_edge * math.sin(math.radians(_edge4_angle))
    # Absolute position on the stand
    _omi_port_x = ox + _port_local_x
    _omi_port_y = oy + _port_local_y

    # Slot cut perpendicular to the edge (rotated to match wall angle).
    # Use a box created at origin, rotated -30°, then translated into position.
    # This ensures the slot extends outward THROUGH the angled pocket wall.
    _slot_depth = 12.0  # deep enough to cut through the angled wall
    _normal_angle = _edge4_angle - 90  # -30° = outward normal direction
    omi_port_slot = (
        cq.Workplane("XY")
        .box(USBC_HEAD_W, _slot_depth, USBC_HEAD_H)
        .rotate((0, 0, 0), (0, 0, 1), _normal_angle)
        .translate((_omi_port_x, _omi_port_y, STAND_H - OMI_CRADLE_DEPTH + USBC_HEAD_H / 2))
    )
    base = base.cut(omi_port_slot)

    # Floor pass-through below the port position (cable drops into bottom tray)
    omi_cable = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(_omi_port_x, _omi_port_y)
        .rect(USBC_HEAD_W, USBC_HEAD_H)
        .extrude(TOP_H + 1)
    )
    base = base.cut(omi_cable)

    # =====================================================================
    # CRADLE 4: Mudra Link — L-pole with flush top-open charger pocket
    # The magnetic charger is WIDER than the 22mm band and the cable exits
    # from the SIDE of the charger. The charger drops into a pocket cut
    # from the shelf top — pogo pins face UP, wristband lays directly on
    # the charger surface. Cable exits charger sideways into a horizontal
    # slot, then bends down through the post's vertical cavity to the base.
    #
    # Clearance below shelf: POLE_H - SHELF_H = 90 - 16 = 74mm ✓
    # =====================================================================
    mx, my = SLOT_POSITIONS["mudra"]

    # Cable pass-through in the base (rectangular, matching cavity)
    mudra_cable = (
        cq.Workplane("XY")
        .center(mx, my)
        .rect(MUDRA_CABLE_CH_D, MUDRA_CABLE_CH_W)
        .extrude(STAND_H)
    )
    base = base.cut(mudra_cable)

    # ── Mudra pole socket — through-hole for snap-in pole insert ─────────
    # Rectangular through-hole where the standalone pole drops in from above.
    # The socket is slightly oversized (SNAP_TOL per side) for easy insertion.
    _socket_w = MUDRA_POLE_D + SNAP_TOL * 2   # 20.6mm in X
    _socket_d = MUDRA_POLE_W + SNAP_TOL * 2   # 22.6mm in Y
    mudra_socket = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(mx, my)
        .rect(_socket_w, _socket_d)
        .extrude(TOP_H + 1)
    )
    base = base.cut(mudra_socket)

    # ── Snap hook engagement pockets on the bottom face ──────────────────
    # Small recesses on the bottom face of the top tray around the socket,
    # one on each X-axis face. These give the snap hooks room to spring
    # out and catch after passing through the socket.
    _pocket_w = SNAP_CLIP_W + SNAP_TOL * 2    # 12.6mm
    _pocket_depth = SNAP_HOOK                  # 1.2mm into tray bottom face
    _pocket_h = SNAP_HOOK * 2                  # 2.4mm
    for side_sign in [-1, 1]:
        pocket_x = mx + side_sign * (_socket_w / 2 + _pocket_depth / 2)
        snap_pocket = (
            cq.Workplane("XY")
            .workplane(offset=SPLIT_Z - _pocket_h)
            .center(pocket_x, my)
            .rect(_pocket_depth, _pocket_w)
            .extrude(_pocket_h + 0.5)
        )
        base = base.cut(snap_pocket)

    # =====================================================================
    # CRADLE 5: Even G2 glasses case — rectangular shelf (rear)
    # The pocket has a SOLID FLOOR so the case sits on a surface, but
    # with a rectangular window cut through it so the VanBon charger's
    # LCD screen (45×45mm, centered on its top face) is visible from
    # above. The charger sits directly below at the same X,Y position.
    # =====================================================================
    gx, gy = SLOT_POSITIONS["g2_case"]

    # Pocket cuts down from the top surface but stops at the floor
    # (SPLIT_Z + WALL) — leaving a solid floor of WALL thickness.
    _g2_floor_z = SPLIT_Z + WALL  # floor of G2 pocket (43.5mm)
    _g2_pocket_depth = STAND_H - _g2_floor_z  # depth from top surface to floor
    g2_pocket = (
        cq.Workplane("XY")
        .workplane(offset=_g2_floor_z)
        .center(gx, gy)
        .rect(G2_W, G2_D)
        .extrude(_g2_pocket_depth + 1)
    )
    base = base.cut(g2_pocket)

    # LCD viewing window — cut through the G2 pocket floor so the
    # VanBon charger's 45×45mm LCD screen is visible from above.
    # Slightly oversized (48×48mm) for easy viewing at an angle.
    _lcd_window = 48  # slightly larger than 45mm LCD for visibility
    g2_lcd_window = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(gx, gy)
        .rect(_lcd_window, _lcd_window)
        .extrude(WALL + 1.5)
    )
    base = base.cut(g2_lcd_window)

    # USB-C cable slot at rear
    g2_cable = (
        cq.Workplane("XY")
        .workplane(offset=_g2_floor_z)
        .center(gx, STAND_D / 2)
        .box(G2_CABLE_W, WALL * 4, _g2_pocket_depth,
             centered=[True, True, False])
    )
    base = base.cut(g2_cable)

    # =====================================================================
    # SLOT 6: iPad — channel at the very rear with back support wall.
    #
    # STRUCTURE (bottom to top):
    #   1. Hidden cable tunnel inside the tray body (Z=42–50)
    #   2. Solid floor with cable opening (Z=50, part of top tray)
    #   3. iPad channel above the floor (Z=50 to STAND_H)
    #   4. Removable cover plate slides in on rails, hides the cable
    #      opening and provides a clean surface
    #   5. Back wall + front lip hold the iPad in place
    #
    # Cable path: bottom tray → floor hole → tunnel (exits both sides)
    #             → up through floor opening → iPad connector
    # =====================================================================
    ipad_y = STAND_D / 2 - IPAD_BACK_THICK - IPAD_SLOT_GAP / 2

    # ── Tunnel dimensions ────────────────────────────────────────────
    _tunnel_w = 14      # tunnel width (Y) — USB-C cable + clearance
    _tunnel_h = 8       # tunnel height (Z) — cable body ~5mm + margin
    _tunnel_z = SPLIT_Z + 1  # tunnel bottom (Z=42)
    _floor_z = _tunnel_z + _tunnel_h  # solid floor at top of tunnel (Z=50)
    _floor_thick = 2.5  # floor thickness
    _cover_thick = 2    # removable cover thickness
    _rail_h = _cover_thick + 1  # rail groove height (cover + clearance)
    _rail_depth = 3     # how far rail extends inward from channel wall

    # ── iPad channel — cut from floor surface up (NOT all the way through)
    # The channel has a solid floor at _floor_z + _floor_thick = Z=52.5
    _channel_floor_z = _floor_z + _floor_thick
    _channel_depth = STAND_H - _channel_floor_z  # ~5.5mm
    ipad_channel = (
        cq.Workplane("XY")
        .workplane(offset=_channel_floor_z)
        .center(0, ipad_y)
        .rect(IPAD_SLOT_W, IPAD_SLOT_GAP)
        .extrude(_channel_depth + 1)
    )
    base = base.cut(ipad_channel)

    # ── Cable opening in the floor ───────────────────────────────────
    # A rectangular hole through the solid floor so the USB-C cable
    # can come up from the tunnel to reach the iPad. Centered.
    _cable_hole_w = 18   # wide enough for USB-C head
    _cable_hole_d = 14   # deep enough for cable + bend
    ipad_floor_hole = (
        cq.Workplane("XY")
        .workplane(offset=_floor_z - 0.5)
        .center(0, ipad_y)
        .rect(_cable_hole_w, _cable_hole_d)
        .extrude(_floor_thick + 1)
    )
    base = base.cut(ipad_floor_hole)

    # ── Slide-in rails for the cover plate ───────────────────────────
    # Two continuous L-shaped rails run the FULL WIDTH of the iPad
    # channel along the front and back walls. The cover plate slides
    # in from either side on these rails.
    #
    # The rail is a groove cut into the channel wall: a horizontal
    # slot _rail_depth deep and _rail_h tall, starting at the floor.
    # The cover slides into these grooves from left or right.
    for rail_sign in [-1, 1]:  # -1 = front wall, +1 = back wall
        rail_y = ipad_y + rail_sign * (IPAD_SLOT_GAP / 2 - _rail_depth / 2)
        rail_groove = (
            cq.Workplane("XY")
            .workplane(offset=_channel_floor_z)
            .center(0, rail_y)
            .rect(IPAD_SLOT_W + 2, _rail_depth)  # full width + exits both sides
            .extrude(_rail_h)
        )
        base = base.cut(rail_groove)

    # ── Back wall — the iPad leans against this ──────────────────────
    ipad_back = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H)
        .center(0, STAND_D / 2 - IPAD_BACK_THICK / 2)
        .rect(IPAD_SLOT_W + 10, IPAD_BACK_THICK)
        .extrude(IPAD_BACK_H)
    )
    base = base.union(ipad_back)

    # ── Front lip — prevents iPad sliding forward ────────────────────
    ipad_lip = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H)
        .center(0, ipad_y - IPAD_SLOT_GAP / 2 - IPAD_BACK_THICK / 2)
        .rect(IPAD_SLOT_W - 10, IPAD_BACK_THICK)
        .extrude(IPAD_LIP_H)
    )
    base = base.union(ipad_lip)

    # ── Hidden cable tunnel (full width, exits both sides) ───────────
    # Floor hole: bottom tray cavity → tunnel
    ipad_cable_up = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(0, ipad_y)
        .rect(_tunnel_w, _tunnel_w)
        .extrude(_tunnel_h + 2)
    )
    base = base.cut(ipad_cable_up)

    # Horizontal tunnel: spans full width, exits both side walls
    ipad_cable_tunnel = (
        cq.Workplane("XY")
        .workplane(offset=_tunnel_z)
        .center(0, ipad_y)
        .rect(STAND_W + 2, _tunnel_w)
        .extrude(_tunnel_h)
    )
    base = base.cut(ipad_cable_tunnel)

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

    return base


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
    # Two cantilever hooks, one on each long side (the MUDRA_POLE_D / X-axis
    # faces). They extend downward from the pole base into negative Z.
    # When inserting the pole into the socket, the hooks flex inward, pass
    # through the socket, and snap out to catch the bottom face of the top tray.
    for side_sign in [-1, 1]:
        clip_x = side_sign * (MUDRA_POLE_D / 2 + SNAP_HOOK / 2)

        # Cantilever arm extending downward from pole base
        arm = (
            cq.Workplane("XY")
            .workplane(offset=-SNAP_CLIP_H)
            .center(clip_x, 0)
            .rect(SNAP_HOOK, SNAP_CLIP_W)
            .extrude(SNAP_CLIP_H)
        )
        pole = pole.union(arm)

        # Hook nub at the bottom of the arm (outward-facing)
        # Catches the underside of the top tray floor
        nub_x = clip_x + side_sign * (SNAP_HOOK / 2)
        nub = (
            cq.Workplane("XY")
            .workplane(offset=-SNAP_CLIP_H)
            .center(nub_x, 0)
            .rect(SNAP_HOOK, SNAP_CLIP_W)
            .extrude(SNAP_HOOK)
        )
        pole = pole.union(nub)

    return pole


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

# Ghost visualization objects (translucent component overlays)
ghosts = build_ghost_components()
for comp_name, (comp_solid, comp_color) in ghosts.items():
    show_object(comp_solid, name=f"ghost_{comp_name}", options={"color": comp_color})
    pass  # keep loop body after show_object is stripped by export script
