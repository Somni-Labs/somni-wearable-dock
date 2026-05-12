"""
Wearable Charging Stand — V2
Unified charging dock for 5 wearable devices, all USB-C powered.

Devices (left to right):
  1. Ultrahuman Ring Air   — circular charging puck ~48mm dia × 16mm
  2. Even Realities R1     — NFC magnetic charger ~42mm dia × 14mm
  3. Omi DevKit 2          — cylindrical pendant 25mm dia × 15mm, pogo-pin
  4. Mudra Link            — wristband sensor pod 50×35×22mm (coiled on charger)
  5. Even Realities G2     — glasses charging case ~165×70×35mm

Layout:
  ┌─────────────────────────────────────────────────────┐
  │  ┌──────────────────────────────────────────────┐   │
  │  │            G2 GLASSES CASE (rear shelf)      │   │
  │  └──────────────────────────────────────────────┘   │
  │                                                     │
  │   (UH)     (R1)     (Omi)    (Mudra)                │
  │   ○48mm    ○42mm    ○25mm    ▭50×35                 │
  │                                                     │
  │            ══════ cable spine ══════    [USB hub]    │
  └─────────────────────────────────────────────────────┘

Design goals:
  - Single USB-C input → internal USB-C hub → all 5 chargers
  - Hidden cable routing (spine + branches inside base)
  - Each charger sits in a fitted pocket with cable pass-through
  - Clean desktop aesthetic, rounded edges
  - Fits QIDI Q2 build plate (245×255mm) — may need 2-piece split

Loadable by cadquery-server via show_object().
"""

import cadquery as cq
from cq_server.ui import ui, show_object

# =============================================================================
# PARAMETRIC DIMENSIONS (all in mm)
# =============================================================================

# --- Overall stand ---
STAND_W = 240          # total width (fits Q2 245mm plate with margin)
STAND_D = 130          # total depth (front cradles + rear G2 shelf)
STAND_H = 22           # base platform height
WALL = 2.5             # wall thickness
CORNER_R = 6           # corner fillet radius
TOP_FILLET = 1.2       # top edge comfort fillet
TOL = 0.5              # print tolerance per side

# --- Internal cable routing ---
BASE_H = 7             # solid floor below cable channels
CHANNEL_H = 10         # cable channel height
CHANNEL_W = 10         # cable channel width
SPINE_Y = 0            # spine runs at Y=0 (center line)

# --- USB-C hub recess (rear-right corner) ---
HUB_W = 65             # compact 4-port USB-C hub
HUB_D = 30
HUB_H = 12
HUB_CABLE_W = 14       # USB-C input cable slot through rear wall

# --- Device 1: Ultrahuman Ring Air charging puck ---
# The UH charger is a circular puck with a concave top to seat the ring.
# Size-specific; dims estimated from product photos + 3D print community.
UH_DIA = 48 + TOL * 2       # puck outer diameter
UH_H = 16                    # puck height
UH_CRADLE_DEPTH = 12         # how deep puck sits in cradle
UH_CABLE_DIA = 6             # USB-C cable pass-through

# --- Device 2: Even Realities R1 ring NFC charger ---
# Small magnetic pedestal connected to USB-C cable.
R1_DIA = 42 + TOL * 2       # charger diameter
R1_H = 14                    # charger height
R1_CRADLE_DEPTH = 10         # how deep it sits
R1_CABLE_DIA = 6             # USB-C cable pass-through

# --- Device 3: Omi DevKit 2 pendant ---
# Cylindrical puck, 25mm diameter, charges via pogo-pin magnetic USB-C dock.
OMI_DIA = 25 + TOL * 2      # pendant diameter
OMI_H = 15                   # pendant height
OMI_CRADLE_DEPTH = 10        # how deep the cradle cup is
OMI_CABLE_DIA = 5            # pogo-pin cable diameter

# --- Device 4: Mudra Link wristband ---
# Wristband coiled on its proprietary magnetic charger.
# Sensor pod is 22mm wide × 10mm thick; when coiled for charging
# the footprint is roughly 50×35mm.
MUDRA_W = 50 + TOL * 2      # pocket width
MUDRA_D = 35 + TOL * 2      # pocket depth
MUDRA_H = 22                 # height when coiled
MUDRA_CRADLE_DEPTH = 14      # pocket depth
MUDRA_POCKET_R = 4           # pocket corner radius
MUDRA_CABLE_DIA = 5          # charging cable pass-through

# --- Device 5: Even Realities G2 glasses charging case ---
# Clamshell case with built-in battery, USB-C charging port on one end.
# Pogo-pin magnetic alignment charges the glasses inside.
G2_W = 165 + TOL * 2        # case length
G2_D = 70 + TOL * 2         # case width/depth
G2_H = 35                    # case height
G2_CRADLE_DEPTH = 18         # how deep the case sits
G2_CABLE_W = 14              # USB-C cable slot width

# --- Layout (X, Y positions relative to stand center) ---
# Front row: 4 small devices spread across the width
# Rear row: G2 case centered
FRONT_Y = -STAND_D / 2 + 38          # front row center Y
REAR_Y = STAND_D / 2 - G2_D / 2 - 8  # rear row center Y

# Front row X positions (left to right, roughly evenly spaced)
FRONT_SPACING = 52
FRONT_START = -1.5 * FRONT_SPACING    # start offset for 4 items
POSITIONS = {
    "uh_ring":  (FRONT_START,                    FRONT_Y),
    "r1_ring":  (FRONT_START + FRONT_SPACING,    FRONT_Y),
    "omi":      (FRONT_START + FRONT_SPACING * 2, FRONT_Y),
    "mudra":    (FRONT_START + FRONT_SPACING * 3, FRONT_Y),
    "g2_case":  (0,                               REAR_Y),
}


# =============================================================================
# BUILD MAIN STAND
# =============================================================================

def build_stand():
    """Build the charging stand platform with cradles and cable routing."""

    # ── Base slab ────────────────────────────────────────────────────────
    base = (
        cq.Workplane("XY")
        .box(STAND_W, STAND_D, STAND_H, centered=[True, True, False])
    )
    base = base.edges("|Z").fillet(CORNER_R)
    base = base.edges(">Z").fillet(TOP_FILLET)

    # ── Cable spine (horizontal channel running left-right at Y=0) ───────
    spine = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .box(
            STAND_W - WALL * 4,
            CHANNEL_W,
            CHANNEL_H,
            centered=[True, True, False],
        )
    )
    base = base.cut(spine)

    # ── Branch channels (spine → each device) ────────────────────────────
    for name, (px, py) in POSITIONS.items():
        if name == "g2_case":
            # G2 gets a wider channel from spine toward rear
            branch = (
                cq.Workplane("XY")
                .workplane(offset=BASE_H)
                .center(px, (SPINE_Y + py) / 2)
                .box(CHANNEL_W + 2, abs(py - SPINE_Y) + CHANNEL_W, CHANNEL_H,
                     centered=[True, True, False])
            )
        else:
            # Front-row devices: branch from spine toward front
            branch = (
                cq.Workplane("XY")
                .workplane(offset=BASE_H)
                .center(px, (SPINE_Y + py) / 2)
                .box(CHANNEL_W, abs(py - SPINE_Y) + CHANNEL_W, CHANNEL_H,
                     centered=[True, True, False])
            )
        base = base.cut(branch)

    # ── USB-C hub recess (rear-right, accessible from back) ──────────────
    hub_x = STAND_W / 2 - HUB_W / 2 - WALL * 2
    hub_y = STAND_D / 2 - HUB_D / 2 - WALL
    hub = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H - 2)
        .center(hub_x, hub_y)
        .box(HUB_W, HUB_D, HUB_H, centered=[True, True, False])
    )
    base = base.cut(hub)

    # USB-C input slot through rear wall
    usb_slot = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .center(hub_x, STAND_D / 2)
        .box(HUB_CABLE_W, WALL * 4, 8, centered=True)
    )
    base = base.cut(usb_slot)

    # ── CRADLE 1: Ultrahuman Ring Air (circular cup) ─────────────────────
    ux, uy = POSITIONS["uh_ring"]
    uh_cup = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - UH_CRADLE_DEPTH)
        .center(ux, uy)
        .circle(UH_DIA / 2)
        .extrude(UH_CRADLE_DEPTH + 1)
    )
    base = base.cut(uh_cup)
    # Cable pass-through
    uh_cable = (
        cq.Workplane("XY")
        .center(ux, uy)
        .circle(UH_CABLE_DIA / 2)
        .extrude(STAND_H)
    )
    base = base.cut(uh_cable)

    # ── CRADLE 2: Even R1 Ring (circular cup) ────────────────────────────
    rx, ry = POSITIONS["r1_ring"]
    r1_cup = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - R1_CRADLE_DEPTH)
        .center(rx, ry)
        .circle(R1_DIA / 2)
        .extrude(R1_CRADLE_DEPTH + 1)
    )
    base = base.cut(r1_cup)
    # Cable pass-through
    r1_cable = (
        cq.Workplane("XY")
        .center(rx, ry)
        .circle(R1_CABLE_DIA / 2)
        .extrude(STAND_H)
    )
    base = base.cut(r1_cable)

    # ── CRADLE 3: Omi DevKit 2 (circular cup, smaller) ───────────────────
    ox, oy = POSITIONS["omi"]
    omi_cup = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - OMI_CRADLE_DEPTH)
        .center(ox, oy)
        .circle(OMI_DIA / 2)
        .extrude(OMI_CRADLE_DEPTH + 1)
    )
    base = base.cut(omi_cup)
    # Cable pass-through
    omi_cable = (
        cq.Workplane("XY")
        .center(ox, oy)
        .circle(OMI_CABLE_DIA / 2)
        .extrude(STAND_H)
    )
    base = base.cut(omi_cable)

    # ── CRADLE 4: Mudra Link (rounded rectangular pocket) ────────────────
    mx, my = POSITIONS["mudra"]
    # Use a sketch for rounded rectangle
    mudra_pocket = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - MUDRA_CRADLE_DEPTH)
        .center(mx, my)
        .sketch()
        .rect(MUDRA_W, MUDRA_D)
        .vertices()
        .fillet(MUDRA_POCKET_R)
        .finalize()
        .extrude(MUDRA_CRADLE_DEPTH + 1)
    )
    base = base.cut(mudra_pocket)
    # Cable pass-through
    mudra_cable = (
        cq.Workplane("XY")
        .center(mx, my)
        .circle(MUDRA_CABLE_DIA / 2)
        .extrude(STAND_H)
    )
    base = base.cut(mudra_cable)

    # ── CRADLE 5: Even G2 case (large rounded rectangular shelf) ─────────
    gx, gy = POSITIONS["g2_case"]
    g2_pocket = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - G2_CRADLE_DEPTH)
        .center(gx, gy)
        .sketch()
        .rect(G2_W, G2_D)
        .vertices()
        .fillet(8)
        .finalize()
        .extrude(G2_CRADLE_DEPTH + 1)
    )
    base = base.cut(g2_pocket)
    # USB-C cable slot at rear of G2 pocket
    g2_cable = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - G2_CRADLE_DEPTH)
        .center(gx, STAND_D / 2)
        .box(G2_CABLE_W, WALL * 4, G2_CRADLE_DEPTH, centered=[True, True, False])
    )
    base = base.cut(g2_cable)

    # ── Identification dots (small raised bumps next to each cradle) ─────
    DOT_R = 2.5
    DOT_H = 0.6
    for name, (px, py) in POSITIONS.items():
        if name == "g2_case":
            dy = py - G2_D / 2 - 6
        else:
            dy = py - 20
        dot = (
            cq.Workplane("XY")
            .workplane(offset=STAND_H)
            .center(px, dy)
            .circle(DOT_R)
            .extrude(DOT_H)
        )
        base = base.union(dot)

    # ── Bottom access panel (rectangular cutout to reach hub + cables) ────
    panel = (
        cq.Workplane("XY")
        .workplane(offset=-0.5)
        .center(hub_x, hub_y)
        .box(HUB_W + 10, HUB_D + 6, BASE_H - 1, centered=[True, True, False])
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

    # Window over hub area so you can still reach it
    window = (
        cq.Workplane("XY")
        .workplane(offset=-0.5)
        .center(STAND_W / 2 - HUB_W / 2 - WALL * 2,
                STAND_D / 2 - HUB_D / 2 - WALL)
        .box(HUB_W - 4, HUB_D - 4, 3, centered=[True, True, False])
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
