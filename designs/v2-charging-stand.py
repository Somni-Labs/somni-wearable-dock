"""
Wearable Charging Stand — V2
Unified charging dock for 5 wearable devices, all USB-C powered.

Devices (left to right):
  1. Ultrahuman Ring Air   — SQUARE charging dock ~48×48×16mm
  2. Even Realities R1     — CIRCULAR NFC magnetic charger ~42mm dia × 14mm
  3. Omi DevKit 2          — ROUNDED TRIANGLE pendant 25mm × 15mm (Reuleaux shape)
  4. Mudra Link            — wristband HANGS over a bar/saddle, charger below
  5. Even Realities G2     — glasses charging case ~165×70×35mm (rear shelf)

Layout:
  ┌───────────────────────────────────────────────────────┐
  │  ┌────────────────────────────────────────────────┐   │
  │  │  G2 GLASSES CASE (rear shelf)                  │   │
  │  │  └── slim 4-port USB-C charger hidden below ──┘│   │
  │  └────────────────────────────────────────────────┘   │
  │                                                       │
  │   ▭UH     ○R1     △Omi     ∩Mudra                    │
  │   48sq    42dia   25rt     bar+drape                  │
  │                                                       │
  │           ══════ cable spine ══════                    │
  └───────────────────────────────────────────────────────┘

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
STAND_D = 140          # total depth (increased for Mudra bar height)
STAND_H = 40           # base platform height — tall enough to house flat 4-port charger
WALL = 2.5             # wall thickness
CORNER_R = 6           # corner fillet radius
TOP_FILLET = 1.2       # top edge comfort fillet
TOL = 0.5              # print tolerance per side

# --- Internal cable routing ---
BASE_H = 7             # solid floor below cable channels
CHANNEL_H = 10         # cable channel height
CHANNEL_W = 10         # cable channel width

# --- USB-C multi-port charger recess (under G2 shelf) ---
# Sized for the class of slim flat 4-port USB-C wall chargers
# (e.g. BUDI 34W 4-Port / similar 30-35W flat bricks, ~83×44×14mm).
# Recess includes ~3mm of tolerance per side and a 2mm cable-pad allowance.
CHARGER_W = 88         # charger external width  + tolerance
CHARGER_D = 55         # charger external depth  + tolerance
CHARGER_H = 17         # charger external height + tolerance
CHARGER_FLOOR = 2      # wall thickness above charger (under G2 pocket)
CHARGER_CABLE_W = 14   # input USB-C cable slot through rear wall
# Legacy aliases for any external scripts that referenced the old names.
HUB_W, HUB_D, HUB_H = CHARGER_W, CHARGER_D, CHARGER_H
HUB_CABLE_W = CHARGER_CABLE_W

# --- Device 1: Ultrahuman Ring Air — SQUARE dock ---
UH_SIDE = 48 + TOL * 2       # square side length
UH_H = 16                     # dock height
UH_CRADLE_DEPTH = 12          # how deep it sits
UH_CORNER_R = 4               # rounded corners on the square pocket
UH_CABLE_DIA = 6

# --- Device 2: Even Realities R1 — CIRCULAR charger ---
R1_DIA = 42 + TOL * 2        # charger diameter
R1_H = 14
R1_CRADLE_DEPTH = 10
R1_CABLE_DIA = 6

# --- Device 3: Omi DevKit 2 — ROUNDED TRIANGLE (Reuleaux-ish) ---
# The pendant is roughly a triangle with heavily rounded vertices,
# like a guitar pick or Reuleaux triangle. ~25mm across.
OMI_SIZE = 25 + TOL * 2      # point-to-flat distance
OMI_H = 15
OMI_CRADLE_DEPTH = 10
OMI_CABLE_DIA = 5
OMI_VERTEX_R = 5              # fillet radius on triangle vertices

# --- Device 4: Mudra Link — WRISTBAND HANGS over a bar ---
# The wristband drapes over a raised bar/saddle. The charging cable
# connects underneath. Bar dimensions:
MUDRA_BAR_W = 30              # bar width (wristband is 22mm wide)
MUDRA_BAR_H = 25              # bar height above stand surface
MUDRA_BAR_D = 8               # bar thickness (depth)
# Top fillet kept safely under half the shortest face dimension (D/2 = 4)
# so opposing fillets don't meet and trip OCCT's BRep_API.
MUDRA_BAR_R = min(3.0, MUDRA_BAR_D / 2 - 0.5)  # bar top radius (rounded for draping)
MUDRA_BAR_VERT_R = 1.5        # vertical-edge fillet (small to avoid compounding)
MUDRA_TRAY_W = 40             # tray below bar for charger cable
MUDRA_TRAY_D = 25
MUDRA_TRAY_DEPTH = 8
MUDRA_CABLE_DIA = 5

# --- Device 5: Even Realities G2 case — rectangular shelf ---
G2_W = 165 + TOL * 2
G2_D = 70 + TOL * 2
G2_H = 35
G2_CRADLE_DEPTH = 18
G2_CABLE_W = 14
G2_POCKET_R = 8

# --- Layout positions ---
FRONT_Y = -STAND_D / 2 + 40
REAR_Y = STAND_D / 2 - G2_D / 2 - 8

FRONT_SPACING = 54
FRONT_START = -1.5 * FRONT_SPACING
POSITIONS = {
    "uh_ring":  (FRONT_START,                     FRONT_Y),
    "r1_ring":  (FRONT_START + FRONT_SPACING,     FRONT_Y),
    "omi":      (FRONT_START + FRONT_SPACING * 2, FRONT_Y),
    "mudra":    (FRONT_START + FRONT_SPACING * 3, FRONT_Y),
    "g2_case":  (0,                                REAR_Y),
}


# =============================================================================
# HELPER: Rounded equilateral triangle (Reuleaux-style)
# =============================================================================

def rounded_triangle_wire(wp, size, fillet_r):
    """
    Create a rounded equilateral triangle (like a guitar pick / the Omi pendant).
    `size` is the distance from center to vertex before filleting.
    Returns a workplane with a closed wire ready for extrude/cut.
    """
    h = size * math.sqrt(3) / 2
    cy = h / 3
    pts = [
        (0, 2 * h / 3),
        (-size / 2, -h / 3),
        (size / 2, -h / 3),
    ]
    return (
        wp
        .sketch()
        .polygon(pts, mode="a")
        .vertices()
        .fillet(fillet_r)
        .finalize()
    )


# =============================================================================
# BUILD MAIN STAND
# =============================================================================

def build_stand():
    """Build the charging stand with correctly shaped cradles."""

    # ── Base slab ────────────────────────────────────────────────────────
    base = (
        cq.Workplane("XY")
        .box(STAND_W, STAND_D, STAND_H, centered=[True, True, False])
    )
    base = base.edges("|Z").fillet(CORNER_R)
    base = base.edges(">Z").fillet(TOP_FILLET)

    # ── Cable spine (horizontal channel, left-right at Y=0) ──────────────
    spine = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .box(STAND_W - WALL * 4, CHANNEL_W, CHANNEL_H,
             centered=[True, True, False])
    )
    base = base.cut(spine)

    # ── Branch channels from spine to each device ────────────────────────
    for name, (px, py) in POSITIONS.items():
        bw = CHANNEL_W + 2 if name == "g2_case" else CHANNEL_W
        mid_y = py / 2  # halfway between spine (Y=0) and device
        branch = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H)
            .center(px, mid_y)
            .box(bw, abs(py) + CHANNEL_W, CHANNEL_H,
                 centered=[True, True, False])
        )
        base = base.cut(branch)

    # ── USB-C charger recess (under G2 shelf) ────────────────────────────
    # Open from the bottom; sits below the G2 case pocket. Charger inserts
    # through the bottom access panel.
    gx_anchor, gy_anchor = POSITIONS["g2_case"]
    charger_x = gx_anchor
    charger_y = gy_anchor
    charger_top_z = STAND_H - G2_CRADLE_DEPTH - CHARGER_FLOOR
    charger_bottom_z = charger_top_z - CHARGER_H
    charger = (
        cq.Workplane("XY")
        .workplane(offset=charger_bottom_z)
        .center(charger_x, charger_y)
        .box(CHARGER_W, CHARGER_D, CHARGER_H + 0.5,
             centered=[True, True, False])
    )
    base = base.cut(charger)
    # Input cable slot through rear wall (at charger level)
    usb_slot = (
        cq.Workplane("XY")
        .workplane(offset=charger_bottom_z + 4)
        .center(charger_x, STAND_D / 2)
        .box(CHARGER_CABLE_W, WALL * 4, 8, centered=True)
    )
    base = base.cut(usb_slot)

    # =====================================================================
    # CRADLE 1: Ultrahuman Ring Air — SQUARE pocket with rounded corners
    # =====================================================================
    ux, uy = POSITIONS["uh_ring"]
    uh_pocket = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - UH_CRADLE_DEPTH)
        .center(ux, uy)
        .sketch()
        .rect(UH_SIDE, UH_SIDE)
        .vertices()
        .fillet(UH_CORNER_R)
        .finalize()
        .extrude(UH_CRADLE_DEPTH + 1)
    )
    base = base.cut(uh_pocket)
    uh_cable = (
        cq.Workplane("XY")
        .center(ux, uy)
        .circle(UH_CABLE_DIA / 2)
        .extrude(STAND_H)
    )
    base = base.cut(uh_cable)

    # =====================================================================
    # CRADLE 2: Even R1 Ring — CIRCULAR pocket
    # =====================================================================
    rx, ry = POSITIONS["r1_ring"]
    r1_cup = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - R1_CRADLE_DEPTH)
        .center(rx, ry)
        .circle(R1_DIA / 2)
        .extrude(R1_CRADLE_DEPTH + 1)
    )
    base = base.cut(r1_cup)
    r1_cable = (
        cq.Workplane("XY")
        .center(rx, ry)
        .circle(R1_CABLE_DIA / 2)
        .extrude(STAND_H)
    )
    base = base.cut(r1_cable)

    # =====================================================================
    # CRADLE 3: Omi DevKit 2 — ROUNDED TRIANGLE pocket
    # =====================================================================
    ox, oy = POSITIONS["omi"]
    omi_wp = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - OMI_CRADLE_DEPTH)
        .center(ox, oy)
    )
    omi_pocket = rounded_triangle_wire(omi_wp, OMI_SIZE, OMI_VERTEX_R)
    omi_pocket = omi_pocket.extrude(OMI_CRADLE_DEPTH + 1)
    base = base.cut(omi_pocket)
    omi_cable = (
        cq.Workplane("XY")
        .center(ox, oy)
        .circle(OMI_CABLE_DIA / 2)
        .extrude(STAND_H)
    )
    base = base.cut(omi_cable)

    # =====================================================================
    # CRADLE 4: Mudra Link — raised BAR for wristband to drape over
    # + small tray underneath for the charger cable connection
    # =====================================================================
    mx, my = POSITIONS["mudra"]

    # Tray (recessed pocket under where the wristband hangs)
    mudra_tray = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - MUDRA_TRAY_DEPTH)
        .center(mx, my)
        .sketch()
        .rect(MUDRA_TRAY_W, MUDRA_TRAY_D)
        .vertices()
        .fillet(3)
        .finalize()
        .extrude(MUDRA_TRAY_DEPTH + 1)
    )
    base = base.cut(mudra_tray)

    # Cable pass-through in tray floor
    mudra_cable = (
        cq.Workplane("XY")
        .center(mx, my)
        .circle(MUDRA_CABLE_DIA / 2)
        .extrude(STAND_H)
    )
    base = base.cut(mudra_cable)

    # Raised bar/saddle — wristband drapes over this
    # Bar sits on the stand surface, centered over the tray
    bar = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H)
        .center(mx, my)
        .box(MUDRA_BAR_W, MUDRA_BAR_D, MUDRA_BAR_H,
             centered=[True, True, False])
    )
    # Round the top edges so the wristband drapes smoothly
    bar = bar.edges(">Z").fillet(MUDRA_BAR_R)
    # Round vertical edges too
    bar = bar.edges("|Z").fillet(MUDRA_BAR_VERT_R)
    base = base.union(bar)

    # =====================================================================
    # CRADLE 5: Even G2 glasses case — rectangular shelf
    # =====================================================================
    gx, gy = POSITIONS["g2_case"]
    g2_pocket = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - G2_CRADLE_DEPTH)
        .center(gx, gy)
        .sketch()
        .rect(G2_W, G2_D)
        .vertices()
        .fillet(G2_POCKET_R)
        .finalize()
        .extrude(G2_CRADLE_DEPTH + 1)
    )
    base = base.cut(g2_pocket)
    # USB-C cable slot at rear of G2 pocket
    g2_cable = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - G2_CRADLE_DEPTH)
        .center(gx, STAND_D / 2)
        .box(G2_CABLE_W, WALL * 4, G2_CRADLE_DEPTH,
             centered=[True, True, False])
    )
    base = base.cut(g2_cable)

    # ── Bottom access panel ──────────────────────────────────────────────
    # Cuts an opening from the underside of the stand large enough to slide
    # the charger in/out. Depth = charger height + a sliver so the cover
    # plate can latch flush.
    panel_depth = CHARGER_H + 2
    panel = (
        cq.Workplane("XY")
        .workplane(offset=-0.5)
        .center(charger_x, charger_y)
        .box(CHARGER_W + 8, CHARGER_D + 6, panel_depth,
             centered=[True, True, False])
    )
    base = base.cut(panel)

    # ── Rubber feet recesses (4 corners) ─────────────────────────────────
    FOOT_DIA = 10
    FOOT_DEPTH = 1.5
    FOOT_INSET = 15
    for fx, fy in [
        (-STAND_W / 2 + FOOT_INSET, -STAND_D / 2 + FOOT_INSET),
        ( STAND_W / 2 - FOOT_INSET, -STAND_D / 2 + FOOT_INSET),
        (-STAND_W / 2 + FOOT_INSET,  STAND_D / 2 - FOOT_INSET),
        ( STAND_W / 2 - FOOT_INSET,  STAND_D / 2 - FOOT_INSET),
    ]:
        foot = (
            cq.Workplane("XY")
            .workplane(offset=-0.5)
            .center(fx, fy)
            .circle(FOOT_DIA / 2)
            .extrude(FOOT_DEPTH + 0.5)
        )
        base = base.cut(foot)

    return base


# =============================================================================
# BUILD BOTTOM COVER PLATE
# =============================================================================

def build_cover():
    """Thin plate that friction-fits onto the bottom to hide cables."""
    cover = (
        cq.Workplane("XY")
        .box(STAND_W - WALL * 2 - 1, STAND_D - WALL * 2 - 1, 1.6,
             centered=[True, True, False])
    )
    cover = cover.edges("|Z").fillet(CORNER_R - 1)
    # Charger access window (under G2 shelf)
    cgx, cgy = POSITIONS["g2_case"]
    window = (
        cq.Workplane("XY")
        .workplane(offset=-0.5)
        .center(cgx, cgy)
        .box(CHARGER_W - 4, CHARGER_D - 4, 3,
             centered=[True, True, False])
    )
    cover = cover.cut(window)
    cover = cover.translate((0, 0, -2.0))
    return cover


# =============================================================================
# RENDER
# =============================================================================

stand = build_stand()
cover = build_cover()

show_object(stand, name="charging_stand",
            options={"color": (0.18, 0.18, 0.20, 0.95)})
show_object(cover, name="bottom_cover",
            options={"color": (0.14, 0.14, 0.16, 0.8)})
