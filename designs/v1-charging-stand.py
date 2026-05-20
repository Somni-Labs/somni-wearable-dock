"""
Wearable Charging Stand — V1
Unified charging dock for 5 wearable devices + iPad slot, all USB-C powered.

Devices (front row, left to right):
  1. Ultrahuman Ring Air   — SQUARE charging dock 39×39×13mm
  2. Even Realities R1     — CIRCULAR NFC magnetic charger 30mm dia × 10mm
  3. Omi DevKit 2          — SIX-SIDED DIAMOND pendant ~41×40×13mm (direct charge)
  4. Mudra Link            — wristband DRAPES over L-pole shelf, cable exits tip
Rear row:
  5. Even Realities G2     — glasses charging case 174×66×36-50mm wedge
  6. iPad                  — wide slot behind G2 (fits 13" Pro, diagonal if cased)

Design goals:
  - Single AC input to internal slim 4-port USB-C charger (under G2 shelf)
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
STAND_H = 61           # TOTAL assembled height (bottom + top)
WALL = 2.5             # wall thickness
CORNER_R = 5           # corner fillet radius
TOL = 0.5              # print tolerance per side

# --- Two-part split ---
# Bottom tray: cable management, USB-C charger, rubber feet
# Top tray: device pockets, Mudra pole, iPad wall — sits on top of bottom
# Bottom tray height raised to 40mm to house VanBon 33mm-tall charger
# (BASE_H=3 + CHARGER_H_with_tol=34 + WALL=2.5 → rounded to 40mm).
SPLIT_Z = 40           # Z where the two parts meet (bottom tray height)
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

# --- USB-C multi-port charger recess (under G2 shelf) ---
# VanBon Smart USB Charger — 8× USB-A ports + LCD display.
# Real measurements: 134mm (L) × 68mm (W) × 33mm (H)
# Orientation: long axis runs left-right (X). AC input cable exits the
# LEFT short face (−X wall); 8× USB-A ports line the long front face.
# 45×45mm LCD sits centered on the top face — visible through the top tray
# if a window is cut, or simply enclosed and not needed during normal use.
# Charger sits flush in the bottom tray cavity, accessed by removing top tray.
CHARGER_W = 134 + TOL * 2  # charger long axis (X) — measured: 134mm
CHARGER_D = 68 + TOL * 2   # charger short axis (Y) — measured: 68mm
CHARGER_H = 33 + TOL * 2   # charger height (Z)     — measured: 33mm
CHARGER_CABLE_SLOT_W = 20  # AC input slot through left wall (cable is on short face)
CHARGER_AUX_PORT_COUNT = 2  # spare ports on charger for ad-hoc cables
CHARGER_AUX_SLOT_W = 14     # aux cable slot width (USB-A head ~12mm + clearance)
CHARGER_AUX_SLOT_H = 8      # aux cable slot height
CHARGER_AUX_SPACING = 24    # spacing between the 2 aux slots (center-to-center)
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
# Real measurements (caliper): 174mm × 66mm wedge, 50mm tall end / 36mm short end.
# The case is a tapered wedge — taller at one end, angled down across its length.
# Tall end (+X) faces the front of the stand; short end (-X) faces the rear.
G2_W = 174 + TOL * 2         # case length (measured: 174mm)
G2_D = 66 + TOL * 2          # case depth (measured: 66mm)
G2_H_TALL = 50               # case height at tall end (measured: 50mm)
G2_H_SHORT = 36              # case height at short end (measured: 36mm)
G2_CRADLE_DEPTH = 18          # how deep case sits (pocket depth into stand top)
G2_CABLE_W = 14               # USB-C cable slot

# --- Device 6: iPad slot (rear, behind G2 case) ---
# iPad Pro 13" / iPad Air 13" in portrait: 213mm wide × 267mm tall × ~5.1mm bare
# Portrait orientation chosen: 213mm width fits within 240mm stand; landscape (267mm) would not.
# With a thin case: ~215mm wide overall (213mm + 2mm tolerance).
# Slot has a back wall the iPad leans against.
IPAD_SLOT_W = 215             # slot width (X) — portrait width: 213mm + 2mm tolerance
IPAD_SLOT_GAP = 24            # slot gap (Y) — iPad + case thickness (~5.1mm bare + case allowance)
IPAD_SLOT_DEPTH = 20          # how deep iPad sits into the base slot
IPAD_BACK_H = 60              # back wall height above base
IPAD_BACK_THICK = 4           # back wall thickness
IPAD_LIP_H = 5                # front lip to stop iPad sliding forward

# --- Layout positions (X, Y from center) ---
FRONT_ROW_Y = -STAND_D / 2 + 38

# Rear row: G2 case must fit BETWEEN the front-row devices and the iPad slot.
# iPad front edge = STAND_D/2 - IPAD_BACK_THICK - IPAD_SLOT_GAP (= 59.5mm).
# Front row rear edge ≈ FRONT_ROW_Y + 20mm (half of largest front device).
# Center the G2 in the available gap for even clearance on both sides.
_IPAD_FRONT_EDGE = STAND_D / 2 - IPAD_BACK_THICK - IPAD_SLOT_GAP
_FRONT_REAR_EDGE = FRONT_ROW_Y + 20          # conservative: half of UH_SIDE
REAR_ROW_Y = (_FRONT_REAR_EDGE + _IPAD_FRONT_EDGE) / 2  # centered in gap

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

    # ── Hollow interior (cable space) ────────────────────────────────────
    cavity = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .box(STAND_W - WALL * 2, STAND_D - WALL * 2, SPLIT_Z - BASE_H - WALL,
             centered=[True, True, False])
    )
    tray = tray.cut(cavity)

    # ── Internal cable ribs (organizer dividers) ─────────────────────────
    # Spine rib left-right at Y=0
    spine_rib = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .box(STAND_W - WALL * 4, 2, SPLIT_Z - BASE_H - WALL,
             centered=[True, True, False])
    )
    tray = tray.union(spine_rib)

    # Cross ribs at each device position
    for name, (px, py) in SLOT_POSITIONS.items():
        rib = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H)
            .center(px, 0)
            .box(2, STAND_D - WALL * 4, SPLIT_Z - BASE_H - WALL,
                 centered=[True, True, False])
        )
        tray = tray.union(rib)

    # ── Cable pass-through holes in the top surface ──────────────────────
    # Each hole is large enough for a USB-C connector HEAD to pass through,
    # not just the cable. Positions are device-specific:
    #   - UH ring: rear of pocket (USB-C port faces +Y)
    #   - R1 ring: left side of pocket (fixed cable exits left edge)
    #   - Omi: left-offset on pocket (USB-C port on left of long side)
    #   - Others: centered under device
    for name, (px, py) in SLOT_POSITIONS.items():
        hw = USBC_HEAD_W + 2 if name == "g2_case" else USBC_HEAD_W
        hh = USBC_HEAD_H + 2 if name == "g2_case" else USBC_HEAD_H

        # Device-specific cable hole positions
        if name == "uh_ring":
            # USB-C port on rear face — hole at rear edge of pocket
            hole_x, hole_y = px, py + UH_SIDE / 2
        elif name == "r1_ring":
            # Fixed cable exits left edge of disc — but USB-C head on
            # the other end must feed through, so hole is head-sized
            hole_x, hole_y = px - R1_DIA / 2, py
        elif name == "omi":
            # USB-C port on left long side (Edge 4), 8mm from v4 corner
            # v4 relative to center = (-22.5, -6.5), edge runs at 60°
            _v4_rel = (-22.5, -6.5)
            hole_x = px + _v4_rel[0] + 8.0 * math.cos(math.radians(60))
            hole_y = py + _v4_rel[1] + 8.0 * math.sin(math.radians(60))
        else:
            hole_x, hole_y = px, py

        hole = (
            cq.Workplane("XY")
            .workplane(offset=SPLIT_Z - WALL - 0.5)
            .center(hole_x, hole_y)
            .rect(hw, hh)
            .extrude(WALL + 1)
        )
        tray = tray.cut(hole)

    # ── USB-C charger recess (under G2 shelf) ────────────────────────────
    # Charger sits in the bottom tray cavity, centered under where the
    # G2 case pocket lives on the top tray. Cable channels and ribs in
    # this region were already cleared by the hollow cavity above.
    charger_x, charger_y = SLOT_POSITIONS["g2_case"]
    charger = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .center(charger_x, charger_y)
        .box(CHARGER_W, CHARGER_D, CHARGER_H, centered=[True, True, False])
    )
    tray = tray.cut(charger)

    # AC input cable slot — runs from the charger's left face through the left wall.
    # Bridges the gap between the recess left edge (charger_x - CHARGER_W/2) and
    # the outer left wall (−STAND_W/2), so the AC cable can exit the enclosure.
    slot_left_edge = -STAND_W / 2
    slot_right_edge = charger_x - CHARGER_W / 2
    slot_cx = (slot_left_edge + slot_right_edge) / 2
    slot_len = slot_right_edge - slot_left_edge + WALL  # +WALL to pierce the outer face
    usb_slot = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .center(slot_cx, charger_y)
        .box(slot_len, CHARGER_CABLE_SLOT_W, CHARGER_H, centered=[True, True, False])
    )
    tray = tray.cut(usb_slot)

    # ── Auxiliary cable slots (2 spare ports, exit through rear wall) ────
    # These let you plug 2 extra cables into the charger's spare ports
    # and route them out the back of the stand for ad-hoc device charging.
    for aux_i in range(CHARGER_AUX_PORT_COUNT):
        _aux_x_offset = (aux_i - 0.5) * CHARGER_AUX_SPACING  # centered around charger_x
        aux_slot = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H + 4)
            .center(charger_x + _aux_x_offset, STAND_D / 2)
            .box(CHARGER_AUX_SLOT_W, WALL * 4, CHARGER_AUX_SLOT_H, centered=True)
        )
        tray = tray.cut(aux_slot)

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
    # USB-C port faces REAR (+Y). Cable routes down and back.
    # ASSUMPTION: port faces rear (+Y side of dock) — confirm with human
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

    # Rear wall slot — USB-C cable exits dock rear face, routes down and back.
    # Slot cut through the rear wall of the pocket (at pocket floor level).
    uh_rear_slot = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - UH_CRADLE_DEPTH)
        .center(ux, uy + UH_SIDE / 2)
        .rect(USBC_HEAD_W, WALL + 2)
        .extrude(USBC_HEAD_H)
    )
    base = base.cut(uh_rear_slot)

    # Floor pass-through at rear edge (cable drops down into bottom tray)
    uh_cable = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(ux, uy + UH_SIDE / 2)
        .rect(USBC_HEAD_W, USBC_HEAD_H)
        .extrude(TOP_H + 1)
    )
    base = base.cut(uh_cable)

    # =====================================================================
    # CRADLE 2: Even R1 Ring — CIRCULAR pocket
    # Fixed cable exits from the LEFT edge (-X) of the disc.
    # Cable is thin (~4mm), not a removable USB-C head.
    # ASSUMPTION: cable exits left edge (−X) of disc — confirm exit point and cable length with human
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
    # ASSUMPTION: port is on upper-left long side, ~8mm from lower corner — confirm which long side and offset with human
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
    # CRADLE 5: Even G2 glasses case — wedge-profile pocket (rear)
    # The case is a tapered wedge: G2_H_TALL (50mm) at +X, G2_H_SHORT
    # (36mm) at -X, dropping 14mm across the length.  The pocket floor is
    # angled to match so the case sits flush on the stand.
    #
    # Implementation: draw a trapezoid in the XZ plane (side profile of the
    # wedge void) and extrude it along Y by G2_D.
    #   +X (tall) floor: STAND_H - G2_CRADLE_DEPTH
    #   -X (short) floor: tall floor + taper  (shallower by 14mm)
    #   top of void: STAND_H + 1  (clears the top face)
    # =====================================================================
    gx, gy = SLOT_POSITIONS["g2_case"]

    _g2_taper = G2_H_TALL - G2_H_SHORT                  # 14mm
    _g2_floor_tall = STAND_H - G2_CRADLE_DEPTH           # Z at +X (tall) end
    _g2_floor_short = _g2_floor_tall + _g2_taper          # Z at -X (short) end
    _g2_top = STAND_H + 1                                # clears top face

    # Trapezoid corners in the XZ plane: bottom-right (+X floor), bottom-left
    # (-X floor), top-left, top-right.  Translated to front face of pocket (Y).
    _trap_pts = [
        (gx + G2_W / 2, _g2_floor_tall),
        (gx - G2_W / 2, _g2_floor_short),
        (gx - G2_W / 2, _g2_top),
        (gx + G2_W / 2, _g2_top),
    ]

    g2_pocket = (
        cq.Workplane("XZ")
        .transformed(offset=cq.Vector(0, 0, gy - G2_D / 2))
        .polyline(_trap_pts)
        .close()
        .extrude(G2_D)
    )
    base = base.cut(g2_pocket)

    # USB-C cable slot at rear (exits through rear wall of stand)
    g2_cable = (
        cq.Workplane("XY")
        .workplane(offset=_g2_floor_short)
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

    # ── Auxiliary cable pass-throughs (2 spare charger ports → rear) ─────
    # Matching slots in the top tray rear wall so cables can exit the back.
    # Positioned to align with the bottom tray aux slots below.
    charger_x, _charger_y = SLOT_POSITIONS["g2_case"]
    for aux_i in range(CHARGER_AUX_PORT_COUNT):
        _aux_x_offset = (aux_i - 0.5) * CHARGER_AUX_SPACING
        # Slot through the top tray rear wall
        aux_top_slot = (
            cq.Workplane("XY")
            .workplane(offset=SPLIT_Z)
            .center(charger_x + _aux_x_offset, STAND_D / 2)
            .box(CHARGER_AUX_SLOT_W, WALL * 4, CHARGER_AUX_SLOT_H,
                 centered=True)
        )
        base = base.cut(aux_top_slot)

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
