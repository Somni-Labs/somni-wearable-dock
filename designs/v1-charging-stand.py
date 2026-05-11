"""
Wearable Charging Stand -- V1
Unified charging dock for 6 non-Apple wearable devices.

Devices:
  1. Omi pendant (DevKit 2) — 25mm dia × 15mm, pogo pin charger
  2. Ultrahuman Ring Air — charging puck ~50mm dia × 20mm
  3. Even Realities R1 ring — NFC magnetic charger ~45mm dia × 15mm
  4. Even Realities G1 glasses case — ~170×70×40mm clamshell, USB-C
  5. Omi Developer Edition — triangle ~35mm side × 12mm thick
  6. Mudra Link wristband — 22mm wide × 10mm thick, cable charger

Design goals:
  - Single USB-C input to internal USB hub
  - Hidden cable routing channels
  - Cradle for each device's existing charger
  - Clean desktop aesthetic
  - 3D printable (PETG)

Loadable by cadquery-server via show_object().
"""

import cadquery as cq
import math
from cq_server.ui import ui, show_object

# =============================================================================
# PARAMETRIC DIMENSIONS (all in mm)
# =============================================================================

# --- Overall stand ---
STAND_W = 280          # total width
STAND_D = 120          # total depth
STAND_H = 25           # base platform height
WALL = 2.5             # wall thickness
CORNER_R = 5           # corner fillet radius
TOL = 0.5              # print tolerance per side

# --- Base platform ---
BASE_H = 8             # solid base below cable channels
CHANNEL_H = 12         # cable channel height inside base
CHANNEL_W = 10         # cable channel width

# --- USB-C hub recess (rear center of base) ---
HUB_W = 65             # small 4-port USB-C hub
HUB_D = 30
HUB_H = 12
HUB_CABLE_SLOT_W = 12  # slot for input USB-C cable

# --- Device 1: Omi Pendant (DevKit 2) ---
OMI_DIA = 25 + TOL * 2           # pendant diameter + tolerance
OMI_H = 15                        # pendant height
OMI_CRADLE_DEPTH = 10             # how deep the cradle cup is
OMI_CHARGER_CABLE_DIA = 5         # pogo-pin cable diameter

# --- Device 2: Ultrahuman Ring Air charger ---
UH_CHARGER_DIA = 50 + TOL * 2    # charging puck diameter
UH_CHARGER_H = 20                 # charging puck height
UH_CRADLE_DEPTH = 15              # how deep it sits

# --- Device 3: Even R1 Ring charger ---
R1_CHARGER_DIA = 45 + TOL * 2    # NFC charger diameter
R1_CHARGER_H = 15                 # charger height
R1_CRADLE_DEPTH = 10              # how deep it sits

# --- Device 4: Even G1 Glasses case ---
G1_CASE_W = 170 + TOL * 2        # case width (glasses folded)
G1_CASE_D = 70 + TOL * 2         # case depth
G1_CASE_H = 40                    # case height
G1_CRADLE_DEPTH = 20              # how deep it sits in the cradle
G1_CRADLE_ANGLE = 10              # slight tilt angle (degrees)

# --- Device 5: Omi Developer Edition (triangle) ---
OMI_DEV_SIDE = 35 + TOL * 2      # triangle side length
OMI_DEV_H = 12                    # thickness
OMI_DEV_CRADLE_DEPTH = 8          # how deep the cradle is

# --- Device 6: Mudra Link wristband ---
MUDRA_W = 50 + TOL * 2           # wristband laid flat width (wider than sensor)
MUDRA_D = 35 + TOL * 2           # wristband depth when coiled
MUDRA_H = 22                      # height when coiled on charger
MUDRA_CRADLE_DEPTH = 12           # how deep the cradle is

# --- Layout positions (X offset from center, left to right) ---
# Order: G1 case (large, rear shelf), then front row L-R:
#   Omi pendant, UH ring, R1 ring, Omi Dev, Mudra Link
FRONT_ROW_Y = -STAND_D / 2 + 35   # front row center Y
REAR_ROW_Y = STAND_D / 2 - 40     # rear row center Y (glasses case)

SLOT_POSITIONS = {
    "omi_pendant":  (-100, FRONT_ROW_Y),
    "uh_ring":      (-45, FRONT_ROW_Y),
    "r1_ring":      (10, FRONT_ROW_Y),
    "omi_dev":      (60, FRONT_ROW_Y),
    "mudra":        (110, FRONT_ROW_Y),
    "g1_case":      (0, REAR_ROW_Y),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def rounded_rect(wp, w, d, r):
    """Create a rounded rectangle on a workplane."""
    return (
        wp
        .rect(w, d)
        .extrude(0)  # placeholder - use sketch instead
    )


def equilateral_triangle_points(side_length):
    """Return vertices of an equilateral triangle centered at origin."""
    h = side_length * math.sqrt(3) / 2
    # Center the triangle
    cy = h / 3  # centroid Y offset
    return [
        (0, 2 * h / 3),                              # top vertex
        (-side_length / 2, -h / 3),                   # bottom-left
        (side_length / 2, -h / 3),                    # bottom-right
    ]


# =============================================================================
# BUILD STAND
# =============================================================================

def build_stand():
    """Build the main charging stand platform."""

    # -------------------------------------------------------------------------
    # BASE PLATFORM — rounded rectangle slab
    # -------------------------------------------------------------------------
    base = (
        cq.Workplane("XY")
        .box(STAND_W, STAND_D, STAND_H, centered=[True, True, False])
    )
    base = base.edges("|Z").fillet(CORNER_R)

    # Top surface fillet for comfort
    base = base.edges(">Z").fillet(1.5)

    # -------------------------------------------------------------------------
    # HOLLOW OUT cable channel space inside base
    # -------------------------------------------------------------------------
    cavity = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H)
        .box(
            STAND_W - WALL * 2,
            STAND_D - WALL * 2,
            CHANNEL_H,
            centered=[True, True, False],
        )
    )
    # Don't cut the cavity from the top — the cradles will open into it
    # Instead we'll route individual channels

    # -------------------------------------------------------------------------
    # CABLE CHANNELS — longitudinal spine + branches to each device
    # -------------------------------------------------------------------------

    # Main spine channel (runs left-right through center)
    spine = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H - CHANNEL_H + 2)
        .center(0, 0)
        .box(STAND_W - WALL * 4, CHANNEL_W, CHANNEL_H - 2, centered=[True, True, False])
    )
    base = base.cut(spine)

    # Branch channels from spine to each front-row device
    for name, (px, py) in SLOT_POSITIONS.items():
        if name == "g1_case":
            continue  # rear row gets its own channel
        branch = (
            cq.Workplane("XY")
            .workplane(offset=BASE_H - CHANNEL_H + 2)
            .center(px, py / 2)  # from spine toward device
            .box(CHANNEL_W, abs(py) + 10, CHANNEL_H - 2, centered=[True, True, False])
        )
        base = base.cut(branch)

    # G1 case rear channel
    g1x, g1y = SLOT_POSITIONS["g1_case"]
    g1_channel = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H - CHANNEL_H + 2)
        .center(g1x, g1y / 2)
        .box(CHANNEL_W, abs(g1y) + 10, CHANNEL_H - 2, centered=[True, True, False])
    )
    base = base.cut(g1_channel)

    # -------------------------------------------------------------------------
    # USB-C HUB RECESS (rear center, accessible from back)
    # -------------------------------------------------------------------------
    hx, hy = 0, STAND_D / 2 - HUB_D / 2 - WALL
    hub_recess = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H - 2)
        .center(hx, hy)
        .box(HUB_W, HUB_D, HUB_H, centered=[True, True, False])
    )
    base = base.cut(hub_recess)

    # USB-C input slot (rear wall)
    usb_input = (
        cq.Workplane("XY")
        .center(hx, STAND_D / 2)
        .workplane(offset=BASE_H)
        .box(HUB_CABLE_SLOT_W, WALL * 3, 8, centered=True)
    )
    base = base.cut(usb_input)

    # -------------------------------------------------------------------------
    # DEVICE CRADLES
    # -------------------------------------------------------------------------

    # --- 1. Omi Pendant cradle (circular cup) ---
    ox, oy = SLOT_POSITIONS["omi_pendant"]
    omi_cup = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - OMI_CRADLE_DEPTH)
        .center(ox, oy)
        .circle(OMI_DIA / 2 + WALL)
        .circle(OMI_DIA / 2)
        .extrude(OMI_CRADLE_DEPTH + 1)
    )
    omi_hole = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - OMI_CRADLE_DEPTH)
        .center(ox, oy)
        .circle(OMI_DIA / 2)
        .extrude(OMI_CRADLE_DEPTH + 1)
    )
    base = base.cut(omi_hole)

    # Cable pass-through hole at bottom of Omi cradle
    omi_cable = (
        cq.Workplane("XY")
        .workplane(offset=0)
        .center(ox, oy)
        .circle(OMI_CHARGER_CABLE_DIA)
        .extrude(STAND_H)
    )
    base = base.cut(omi_cable)

    # --- 2. Ultrahuman Ring charger cradle (circular cup) ---
    ux, uy = SLOT_POSITIONS["uh_ring"]
    uh_hole = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - UH_CRADLE_DEPTH)
        .center(ux, uy)
        .circle(UH_CHARGER_DIA / 2)
        .extrude(UH_CRADLE_DEPTH + 1)
    )
    base = base.cut(uh_hole)

    # Cable hole for UH charger USB-C
    uh_cable = (
        cq.Workplane("XY")
        .workplane(offset=0)
        .center(ux, uy)
        .circle(5)
        .extrude(STAND_H)
    )
    base = base.cut(uh_cable)

    # --- 3. Even R1 Ring charger cradle (circular cup) ---
    rx, ry = SLOT_POSITIONS["r1_ring"]
    r1_hole = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - R1_CRADLE_DEPTH)
        .center(rx, ry)
        .circle(R1_CHARGER_DIA / 2)
        .extrude(R1_CRADLE_DEPTH + 1)
    )
    base = base.cut(r1_hole)

    # Cable hole for R1 charger USB-C
    r1_cable = (
        cq.Workplane("XY")
        .workplane(offset=0)
        .center(rx, ry)
        .circle(5)
        .extrude(STAND_H)
    )
    base = base.cut(r1_cable)

    # --- 4. Omi Developer Edition cradle (triangular pocket) ---
    dx, dy = SLOT_POSITIONS["omi_dev"]
    tri_pts = equilateral_triangle_points(OMI_DEV_SIDE)
    # Close the polygon
    tri_pts_closed = tri_pts + [tri_pts[0]]

    dev_pocket = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - OMI_DEV_CRADLE_DEPTH)
        .center(dx, dy)
        .polyline(tri_pts_closed)
        .close()
        .extrude(OMI_DEV_CRADLE_DEPTH + 1)
    )
    base = base.cut(dev_pocket)

    # Cable hole for Omi Dev charger
    dev_cable = (
        cq.Workplane("XY")
        .workplane(offset=0)
        .center(dx, dy)
        .circle(4)
        .extrude(STAND_H)
    )
    base = base.cut(dev_cable)

    # --- 5. Mudra Link cradle (rectangular pocket) ---
    mx, my = SLOT_POSITIONS["mudra"]
    mudra_pocket = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - MUDRA_CRADLE_DEPTH)
        .center(mx, my)
        .rect(MUDRA_W, MUDRA_D)
        .extrude(MUDRA_CRADLE_DEPTH + 1)
    )
    base = base.cut(mudra_pocket)

    # Round the pocket edges
    # Cable hole for Mudra charger
    mudra_cable = (
        cq.Workplane("XY")
        .workplane(offset=0)
        .center(mx, my)
        .circle(5)
        .extrude(STAND_H)
    )
    base = base.cut(mudra_cable)

    # --- 6. G1 Glasses case cradle (large rectangular shelf, rear) ---
    gx, gy = SLOT_POSITIONS["g1_case"]
    g1_pocket = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - G1_CRADLE_DEPTH)
        .center(gx, gy)
        .rect(G1_CASE_W, G1_CASE_D)
        .extrude(G1_CRADLE_DEPTH + 1)
    )
    base = base.cut(g1_pocket)

    # Cable slot at rear of G1 pocket (for USB-C to case)
    g1_cable = (
        cq.Workplane("XY")
        .center(gx, STAND_D / 2)
        .workplane(offset=STAND_H - G1_CRADLE_DEPTH)
        .box(12, WALL * 3, G1_CRADLE_DEPTH, centered=[True, True, False])
    )
    base = base.cut(g1_cable)

    # -------------------------------------------------------------------------
    # LABEL ENGRAVINGS (shallow text on front edge)
    # -------------------------------------------------------------------------
    # CadQuery text engraving — optional, adds visual identification
    # We'll add raised label pads next to each cradle instead

    # Small raised label pads (bumps) to identify each slot
    label_h = 0.8  # raised height
    label_r = 3    # label dot radius

    for name, (px, py) in SLOT_POSITIONS.items():
        if name == "g1_case":
            label_y = py - G1_CASE_D / 2 - 8
        else:
            label_y = py - 22
        label_dot = (
            cq.Workplane("XY")
            .workplane(offset=STAND_H)
            .center(px, label_y)
            .circle(label_r)
            .extrude(label_h)
        )
        base = base.union(label_dot)

    # -------------------------------------------------------------------------
    # BOTTOM ACCESS PANEL (for inserting/accessing USB hub)
    # -------------------------------------------------------------------------
    # Simple rectangular cutout on bottom for hub access
    bottom_panel = (
        cq.Workplane("XY")
        .workplane(offset=-0.5)
        .center(0, STAND_D / 2 - HUB_D / 2 - WALL)
        .rect(HUB_W + 10, HUB_D + 5)
        .extrude(BASE_H - 2)
    )
    base = base.cut(bottom_panel)

    # -------------------------------------------------------------------------
    # RUBBER FEET recesses (4 corners)
    # -------------------------------------------------------------------------
    FOOT_DIA = 10
    FOOT_DEPTH = 1.5
    foot_inset = 15

    for fx, fy in [
        (-STAND_W / 2 + foot_inset, -STAND_D / 2 + foot_inset),
        (STAND_W / 2 - foot_inset, -STAND_D / 2 + foot_inset),
        (-STAND_W / 2 + foot_inset, STAND_D / 2 - foot_inset),
        (STAND_W / 2 - foot_inset, STAND_D / 2 - foot_inset),
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
# BUILD CABLE COVER (bottom plate to hide cables)
# =============================================================================

def build_cable_cover():
    """
    Thin plate that clips onto the bottom of the stand to hide
    the USB hub and cable routing. Simple friction fit.
    """
    cover = (
        cq.Workplane("XY")
        .box(STAND_W - WALL * 2 - 1, STAND_D - WALL * 2 - 1, 2, centered=[True, True, False])
    )
    cover = cover.edges("|Z").fillet(CORNER_R - 1)

    # Hub access window (so you can still reach the hub if needed)
    hub_window = (
        cq.Workplane("XY")
        .workplane(offset=-0.5)
        .center(0, STAND_D / 2 - HUB_D / 2 - WALL)
        .rect(HUB_W - 5, HUB_D - 5)
        .extrude(3)
    )
    cover = cover.cut(hub_window)

    # Shift down to sit below the base
    cover = cover.translate((0, 0, -2.5))

    return cover


# =============================================================================
# BUILD AND DISPLAY
# =============================================================================

stand = build_stand()
cable_cover = build_cable_cover()

show_object(stand, name="charging_stand", options={"color": (0.2, 0.2, 0.22, 0.95)})
show_object(cable_cover, name="cable_cover", options={"color": (0.15, 0.15, 0.17, 0.8)})
