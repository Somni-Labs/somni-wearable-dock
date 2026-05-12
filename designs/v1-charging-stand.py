"""
Wearable Charging Stand — V1
Unified charging dock for 5 wearable devices + iPad slot, all USB-C powered.

Devices (front row, left to right):
  1. Ultrahuman Ring Air   — SQUARE charging dock ~48×48×16mm
  2. Even Realities R1     — CIRCULAR NFC magnetic charger ~42mm dia × 14mm
  3. Omi DevKit 2          — ROUNDED TRIANGLE charging dock ~73mm
  4. Mudra Link            — wristband DRAPES over L-pole shelf, cable exits tip
Rear row:
  5. Even Realities G2     — glasses charging case ~165×70×35mm
  6. iPad                  — vertical slot behind G2 (landscape, fits 11" Pro)

Design goals:
  - Single USB-C input to internal USB hub
  - Hidden cable routing channels
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
STAND_H = 30           # TOTAL assembled height (bottom + top)
WALL = 2.5             # wall thickness
CORNER_R = 5           # corner fillet radius
TOL = 0.5              # print tolerance per side

# --- Two-part split ---
# Bottom tray: cable management, USB hub, rubber feet
# Top tray: device pockets, Mudra pole, iPad wall — sits on top of bottom
SPLIT_Z = 14           # Z where the two parts meet (bottom tray height)
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

# --- USB-C hub recess (rear-right corner) ---
HUB_W = 65             # small 4-port USB-C hub
HUB_D = 30
HUB_H = 12
HUB_CABLE_SLOT_W = 14  # slot for input USB-C cable
USBC_HEAD_W = 14       # USB-C connector head width (long axis)
USBC_HEAD_H = 9        # USB-C connector head height (short axis)

# --- Device 1: Ultrahuman Ring Air — SQUARE dock ---
UH_SIDE = 48 + TOL * 2       # square side length
UH_H = 16                     # dock height
UH_CRADLE_DEPTH = 12          # how deep it sits
UH_CORNER_R = 4               # rounded corners on the square

# --- Device 2: Even Realities R1 — CIRCULAR charger ---
R1_DIA = 42 + TOL * 2        # charger diameter
R1_H = 14
R1_CRADLE_DEPTH = 10

# --- Device 3: Omi DevKit 2 — ROUNDED TRIANGLE ---
# Guitar-pick / diamond shape with rounded vertices.
# Pendant is 25mm diameter, but the pogo-pin magnetic CHARGING DOCK
# that sits in this pocket is larger (~35mm across).
OMI_SIDE = 72 + TOL * 2      # triangle side — 2× size for charging dock
OMI_H = 15
OMI_CRADLE_DEPTH = 10
OMI_VERTEX_R = 16             # larger fillet for softer diamond/guitar-pick shape

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
MUDRA_POLE_W = 30             # pole Y-extent (wide enough for charger)
MUDRA_POLE_D = 22             # pole X-thickness (houses charger + cable bend)
MUDRA_POLE_H = 90             # vertical section height (74mm clearance + 16mm shelf)
MUDRA_SHELF_L = 40            # shelf length extending right (+X) — room for rotated charger
MUDRA_SHELF_H = 16            # shelf thickness (Z) — tall enough for charger bay
MUDRA_CHARGER_W = 20          # charger pocket Y-extent (short axis, across band path)
MUDRA_CHARGER_D = 34          # charger pocket X-extent (long axis, along shelf)
MUDRA_CHARGER_H = 11          # charger end piece height (fits inside shelf)
MUDRA_CABLE_CH_W = 12         # cable cavity width (Y) — room for USB cable
MUDRA_CABLE_CH_D = 14         # cable cavity depth (X) — room for cable + bend
MUDRA_CABLE_BEND_R = 15       # minimum cable bend radius

# --- Device 5: Even Realities G2 glasses case ---
G2_W = 165 + TOL * 2         # case length
G2_D = 70 + TOL * 2          # case depth
G2_H = 35                     # case height
G2_CRADLE_DEPTH = 18          # how deep case sits
G2_CABLE_W = 14               # USB-C cable slot

# --- Device 6: iPad slot (rear, behind G2 case) ---
# iPad Pro 11" in landscape: 249.7 × 177.5 × 5.3mm
# With a thick rugged case: ~20mm thick, ~260 × 190mm overall
# Slot has a back wall the iPad leans against.
IPAD_SLOT_W = 220             # slot width (X) — fits cased 11" landscape
IPAD_SLOT_GAP = 22            # slot gap (Y) — iPad + thick case (~20mm)
IPAD_SLOT_DEPTH = 20          # how deep iPad sits into the base slot
IPAD_BACK_H = 55              # back wall height above base (support wall)
IPAD_BACK_THICK = 4           # back wall thickness
IPAD_LIP_H = 5                # front lip to stop iPad sliding forward

# --- Layout positions (X, Y from center) ---
FRONT_ROW_Y = -STAND_D / 2 + 38
REAR_ROW_Y = STAND_D / 2 - G2_D / 2 - 8

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

def equilateral_triangle_points(side_length):
    """Return vertices of an equilateral triangle centered at origin."""
    h = side_length * math.sqrt(3) / 2
    return [
        (0, 2 * h / 3),
        (-side_length / 2, -h / 3),
        (side_length / 2, -h / 3),
    ]


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
    # not just the cable. G2 case gets double-wide for its bigger cable.
    for name, (px, py) in SLOT_POSITIONS.items():
        hw = USBC_HEAD_W + 2 if name == "g2_case" else USBC_HEAD_W
        hh = USBC_HEAD_H + 2 if name == "g2_case" else USBC_HEAD_H
        hole = (
            cq.Workplane("XY")
            .workplane(offset=SPLIT_Z - WALL - 0.5)
            .center(px, py)
            .rect(hw, hh)
            .extrude(WALL + 1)
        )
        tray = tray.cut(hole)

    # ── USB-C hub recess (rear-right) ────────────────────────────────────
    hub_x = STAND_W / 2 - HUB_W / 2 - WALL * 2
    hub_y = STAND_D / 2 - HUB_D / 2 - WALL
    hub = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .center(hub_x, hub_y)
        .box(HUB_W, HUB_D, HUB_H, centered=[True, True, False])
    )
    tray = tray.cut(hub)

    # Input cable slot through rear wall
    usb_slot = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .center(hub_x, STAND_D / 2)
        .box(HUB_CABLE_SLOT_W, WALL * 4, 8, centered=True)
    )
    tray = tray.cut(usb_slot)

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

    # ── Cable pass-through holes (matching bottom tray) ──────────────────
    # Same size as bottom tray holes — USB-C head must fit through both
    for name, (px, py) in SLOT_POSITIONS.items():
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
    # Cable pass-through — USB-C head sized, through the full top tray floor
    uh_cable = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(ux, uy)
        .rect(USBC_HEAD_W, USBC_HEAD_H)
        .extrude(TOP_H + 1)
    )
    base = base.cut(uh_cable)

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
    base = base.cut(r1_cup)
    # Cable pass-through — USB-C head sized
    r1_cable = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(rx, ry)
        .rect(USBC_HEAD_W, USBC_HEAD_H)
        .extrude(TOP_H + 1)
    )
    base = base.cut(r1_cable)

    # =====================================================================
    # CRADLE 3: Omi DevKit 2 — ROUNDED TRIANGLE pocket
    # Triangle with filleted vertices (guitar-pick / diamond shape)
    # =====================================================================
    ox, oy = SLOT_POSITIONS["omi"]
    tri_pts = equilateral_triangle_points(OMI_SIDE)
    tri_closed = tri_pts + [tri_pts[0]]

    omi_pocket = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - OMI_CRADLE_DEPTH)
        .center(ox, oy)
        .polyline(tri_closed)
        .close()
        .extrude(OMI_CRADLE_DEPTH + 1)
    )
    # Round the triangle vertices so it looks like a guitar-pick / diamond
    omi_pocket = omi_pocket.edges("|Z").fillet(OMI_VERTEX_R)
    base = base.cut(omi_pocket)
    # Cable pass-through — USB-C head sized
    omi_cable = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(ox, oy)
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
