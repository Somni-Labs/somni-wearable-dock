"""
Wearable Charging Stand — V1
Unified charging dock for 5 wearable devices + iPad slot, USB-A powered via VanBon hub.

Devices (front row, left to right):
  1. Ultrahuman Ring Air   — SQUARE charging dock 39×39×13mm
  2. Even Realities R1     — CIRCULAR NFC magnetic charger 30mm dia × 10mm
  3. Omi DevKit 2          — SIX-SIDED DIAMOND pendant ~41×40×13mm (direct charge)
  4. Mudra Link            — wristband DRAPES over L-pole shelf, cable exits tip
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
TOL = 0.5              # print tolerance per side

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
CHARGER_W = 138        # charger length + 4mm tolerance (measured: 134mm)
CHARGER_D = 72         # charger width  + 4mm tolerance (measured: 68mm)
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
    """Top tray: device pockets, Mudra pole, iPad wall. Sits on bottom tray."""

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

    # Build L-pole at ORIGIN, then translate.
    # Vertical post: POLE_D(X) × POLE_W(Y) × POLE_H(Z)
    post = (
        cq.Workplane("XY")
        .rect(MUDRA_POLE_D, MUDRA_POLE_W)
        .extrude(MUDRA_POLE_H)
    )

    # Horizontal shelf: extends right (+X) from top of post
    # SHELF_L(X) × POLE_W(Y) × SHELF_H(Z)
    shelf = (
        cq.Workplane("XY")
        .workplane(offset=MUDRA_POLE_H - MUDRA_SHELF_H)
        .center(MUDRA_POLE_D / 2 + MUDRA_SHELF_L / 2, 0)
        .rect(MUDRA_SHELF_L, MUDRA_POLE_W)
        .extrude(MUDRA_SHELF_H)
    )

    pole = post.union(shelf)

    # ── Charger bay — FLUSH in the shelf top, open from above ──
    # The charger drops into a pocket cut from the TOP of the shelf.
    # Pogo pins face straight up. The wristband drapes directly onto the
    # charger surface — no ceiling between them.
    # The pocket depth = CHARGER_H, leaving a solid floor beneath for
    # structural support. A chamfered lip around the top edge prevents
    # hard edges under the silicone band.
    charger_bay_x = MUDRA_POLE_D / 2 + MUDRA_SHELF_L / 2
    shelf_top_z = MUDRA_POLE_H

    # Main charger pocket — cut DOWN from shelf top surface
    charger_bay = (
        cq.Workplane("XY")
        .workplane(offset=shelf_top_z - MUDRA_CHARGER_H)
        .center(charger_bay_x, 0)
        .rect(MUDRA_CHARGER_D, MUDRA_CHARGER_W)
        .extrude(MUDRA_CHARGER_H + 1)   # +1 to cleanly break the top face
    )
    pole = pole.cut(charger_bay)

    # Chamfered lip — gentle bevel around the pocket opening so the
    # band's silicone has no sharp edge to catch on
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

    # ── Cable channel — from charger bay sideways + down through post ──
    # The cable exits the SIDE of the charger (in -X direction, toward
    # the post), then bends downward through the vertical post cavity.

    # Horizontal cable slot from charger bay toward the post (-X)
    # This connects the charger bay's -X wall to the post's internal cavity.
    # Height sits at the bottom of the charger bay (where the cable exits).
    cable_slot_z = shelf_top_z - MUDRA_CHARGER_H  # bottom of charger bay
    slot_length = charger_bay_x - MUDRA_CHARGER_D / 2  # from bay left edge to post center
    cable_horiz = (
        cq.Workplane("XY")
        .workplane(offset=cable_slot_z)
        .center(slot_length / 2, 0)
        .rect(slot_length + 2, MUDRA_CABLE_CH_W)
        .extrude(MUDRA_CABLE_CH_W)
    )
    pole = pole.cut(cable_horiz)

    # Vertical cable cavity through the post — from base up to the
    # horizontal cable slot. Rectangular cross-section.
    cable_cavity_vert = (
        cq.Workplane("XY")
        .rect(MUDRA_CABLE_CH_D, MUDRA_CABLE_CH_W)
        .extrude(cable_slot_z + MUDRA_CABLE_CH_W + 1)
    )
    pole = pole.cut(cable_cavity_vert)

    # Move into position on the stand
    pole = pole.translate((mx, my, STAND_H))

    base = base.union(pole)

    # =====================================================================
    # CRADLE 5: Even G2 glasses case — rectangular shelf (rear)
    # =====================================================================
    gx, gy = SLOT_POSITIONS["g2_case"]
    g2_pocket = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - G2_CRADLE_DEPTH)
        .center(gx, gy)
        .rect(G2_W, G2_D)
        .extrude(G2_CRADLE_DEPTH + 1)
    )
    base = base.cut(g2_pocket)
    # USB-C cable slot at rear
    g2_cable = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - G2_CRADLE_DEPTH)
        .center(gx, STAND_D / 2)
        .box(G2_CABLE_W, WALL * 4, G2_CRADLE_DEPTH,
             centered=[True, True, False])
    )
    base = base.cut(g2_cable)

    # =====================================================================
    # SLOT 6: iPad — channel at the very rear with back support wall.
    # iPad (in thick case) stands upright in landscape, leaning against
    # the back wall. Front lip prevents it from sliding forward.
    # =====================================================================
    # iPad slot center Y: positioned at the rear of the stand
    ipad_y = STAND_D / 2 - IPAD_BACK_THICK - IPAD_SLOT_GAP / 2

    # Channel cut into the base for the iPad's bottom edge
    ipad_channel = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - IPAD_SLOT_DEPTH)
        .center(0, ipad_y)
        .rect(IPAD_SLOT_W, IPAD_SLOT_GAP)
        .extrude(IPAD_SLOT_DEPTH + 1)
    )
    base = base.cut(ipad_channel)

    # Back wall — the iPad leans against this
    ipad_back = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H)
        .center(0, STAND_D / 2 - IPAD_BACK_THICK / 2)
        .rect(IPAD_SLOT_W + 10, IPAD_BACK_THICK)
        .extrude(IPAD_BACK_H)
    )
    base = base.union(ipad_back)

    # Front lip — raised ridge to catch the iPad from sliding forward
    ipad_lip = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H)
        .center(0, ipad_y - IPAD_SLOT_GAP / 2 - IPAD_BACK_THICK / 2)
        .rect(IPAD_SLOT_W - 10, IPAD_BACK_THICK)
        .extrude(IPAD_LIP_H)
    )
    base = base.union(ipad_lip)

    # USB-C cable pass-through in the iPad channel floor + slot through
    # the back wall so the charging cable can reach the iPad
    ipad_cable_floor = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z)
        .center(0, ipad_y)
        .rect(14, 8)
        .extrude(TOP_H)
    )
    base = base.cut(ipad_cable_floor)
    ipad_cable_wall = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - IPAD_SLOT_DEPTH)
        .center(0, STAND_D / 2)
        .box(14, IPAD_BACK_THICK * 2, IPAD_SLOT_DEPTH + 8,
             centered=[True, True, False])
    )
    base = base.cut(ipad_cable_wall)

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
# BUILD AND DISPLAY
# =============================================================================

bottom_tray = build_bottom_tray()
top_tray = build_top_tray()

show_object(bottom_tray, name="bottom_tray",
            options={"color": (0.15, 0.15, 0.17, 0.9)})
show_object(top_tray, name="top_tray",
            options={"color": (0.2, 0.2, 0.22, 0.95)})
