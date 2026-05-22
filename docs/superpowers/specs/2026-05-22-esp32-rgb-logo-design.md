# ESP32, RGB Underglow, and Backlit Logo

**Date**: 2026-05-22
**Status**: Approved

## Overview

Add three features to the bottom tray: an ESP32 microcontroller mount, a WS2812B RGB LED underglow strip, and a backlit "Somni Labs" logo cut into the front wall. The ESP32 drives the LEDs and can be extended with future functionality. Power comes from spare USB-A ports on the VanBon charger already inside the stand.

## 1. ESP32 Mount

**Board:** ESP32-DevKitC V4 (55mm x 28mm PCB, ~12mm tall with components)

**Location:** Front-left corner of the bottom tray interior, on the floor (Z = BASE_H = 3mm). The board's short edge (28mm, with USB port) faces the front wall. The long edge (55mm) runs along Y (front to back).

**Position (board center):**
- X = -STAND_W/2 + WALL + ESP32_W/2 = -117.5 + 14.5 = -103mm
- Y = -STAND_D/2 + WALL + ESP32_L/2 = -85 + 28 = -57mm
- This places the board in the left side pocket, between the front wall and the charger bay left edge (X = -73). No overlap with cable winding posts (which start at X = -95 inward from the charger edge).

**Mount geometry:**
- 4 standoff posts: 3mm diameter, 2mm tall, positioned at the DevKitC V4 mounting holes (roughly 2mm inset from each corner of the 55x28mm footprint)
- Two cradle walls on the left and front sides: 1.5mm thick, 6mm tall, running the length of each board edge — the board drops in from above and is held snugly against the corner
- Open on the right and rear sides for cable access

**USB port access:**
- Rectangular slot cut through the front wall: 12mm wide x 8mm tall
- Positioned to align with the Micro-USB port on the DevKitC V4 (centered on the board's short edge at X = -103mm, Z = BASE_H + ESP32_STANDOFF_H + 4mm)
- The USB cable plugs in from outside the front wall for power and programming

**Clearances:**
- Board top (3mm floor + 2mm standoffs + 12mm board = 17mm) is well below the tray top (SPLIT_Z = 41mm)
- Board right edge at X = -103 + 14.5 = -88.5mm; charger bay left edge at X = -73mm — 15.5mm clear
- Front-row cable arch clips start at FRONT_START = -81mm (X) — no overlap

## 2. "Somni Labs" Backlit Logo

**Text:** "Somni Labs" in a sans-serif font

**Technique:** Text is recessed into the exterior face of the front wall. The recess cuts through most of the 2.5mm wall thickness, leaving a 0.6mm thin wall (2 print layers at 0.3mm). This thin shell acts as a natural light diffuser — the RGB strip behind it creates a soft, even glow through the letter shapes.

**Dimensions:**
- Text width: ~120mm, centered horizontally on the front wall (X = 0)
- Text height: ~12mm (font size chosen to produce ~12mm cap height)
- Vertical position: centered on the front wall face, roughly Z = 20mm from the base (vertically centered in the 41mm wall height)

**CadQuery implementation:** Use `cq.Workplane.text()` to create the text geometry, then cut it as a recess from the exterior face of the front wall. The cut depth = WALL - 0.6mm = 1.9mm.

## 3. RGB Underglow

**Strip:** WS2812B (NeoPixel) addressable LED strip, 30 LEDs/m density, 10mm wide, 5V DC.

**Path:** U-shaped route along three sides of the bottom tray interior:
- Left side wall (bottom to top in Y): ~170mm
- Front wall (left to right in X): ~235mm
- Right side wall (top to bottom in Y): ~170mm
- Total: ~575mm, approximately 18 LEDs

The strip does NOT run along the back wall — the iPad back wall blocks the view and there's no visual benefit.

**LED channel:**
- Groove cut into the floor of the bottom tray, running along the inner base of the three walls
- Channel dimensions: 12mm wide (10mm strip + 1mm clearance per side) x 4mm deep
- The strip sits in the channel, adhesive side down, held by friction and the channel walls
- Channel is inset 1mm from the inner wall face so light reflects off the wall before exiting

**Light exit slots:**
- Narrow horizontal slot cut through the bottom of the exterior walls on all three sides (front + left + right)
- Slot dimensions: 3mm tall x continuous length matching the interior channel
- Slot bottom edge starts at Z = 1mm (just above the desk surface / rubber feet)
- Light spills downward onto the desk surface, creating the underglow effect

**Logo backlighting:** The front section of the LED channel runs directly behind the "Somni Labs" logo recess. The same LEDs that create the front underglow also backlight the logo. No additional LEDs needed.

## 4. Wiring

**Power:**
- ESP32: powered via Micro-USB cable from VanBon USB-A port (5V, <500mA)
- LED strip: powered from the same USB cable or a second VanBon USB-A port. 18 LEDs at 60mA max each = 1.08A peak (full white). Typical animated patterns draw 300-500mA.

**Data:**
- Single GPIO wire from ESP32 to LED strip DIN (data in) pad
- Wire routes through a small floor channel from the ESP32 position to the start of the LED channel (left side wall)

**Floor wiring channels:**
- 6mm wide x 3mm deep groove in the floor connecting:
  1. ESP32 position → left wall LED channel start (for the data wire)
  2. ESP32 position → charger bay area (for the USB power cable from VanBon)
- These are shallow grooves — cables sit in them and the top tray covers everything

## 5. Constants

New parametric constants to add:

```python
# --- ESP32 DevKitC V4 mount ---
ESP32_L = 55 + 1          # board length + tolerance (X)
ESP32_W = 28 + 1          # board width + tolerance (Y)
ESP32_H = 12              # board height (tallest component)
ESP32_STANDOFF_H = 2      # standoff post height
ESP32_STANDOFF_D = 3      # standoff post diameter
ESP32_CRADLE_H = 6        # cradle wall height
ESP32_CRADLE_T = 1.5      # cradle wall thickness
ESP32_USB_SLOT_W = 12     # USB port slot width through front wall
ESP32_USB_SLOT_H = 8      # USB port slot height through front wall

# --- RGB LED strip (WS2812B 30/m) ---
LED_CHANNEL_W = 12        # channel width (10mm strip + clearance)
LED_CHANNEL_D = 4         # channel depth into floor
LED_SLOT_H = 3            # light exit slot height on exterior walls
LED_SLOT_Z = 1            # slot bottom edge Z (above desk)

# --- Logo ---
LOGO_TEXT = "Somni Labs"
LOGO_WIDTH = 120          # approximate text span
LOGO_FONT_SIZE = 12       # cap height in mm
LOGO_RECESS_DEPTH = 1.9   # cut depth (WALL - 0.6mm diffuser)
LOGO_Z = 20               # vertical center of text on front wall
```

## 6. Print Impact

These changes only affect the bottom tray:
- LED channels and wiring grooves are subtractive (cuts) — no added print time
- Logo recess is subtractive — no added print time
- ESP32 standoffs and cradle walls add minimal material (~2g)
- Light exit slots are subtractive — slightly reduce print time
- **Net impact: approximately zero additional print time**

## Files Changed

| File | Change |
|------|--------|
| `designs/v1-charging-stand.py` | Add constants, modify `build_bottom_tray()` to add ESP32 mount, LED channels, light exit slots, logo recess, wiring grooves |
| `CLAUDE.md` | Document ESP32 + RGB + logo features |
