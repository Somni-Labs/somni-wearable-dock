# Cyberpunk Diffuser Bars — Design Spec

## Summary

Add subtle fragmented horizontal light bars recessed into the exterior walls of the bottom tray. Each bar is a shallow recess cut from the outside, leaving a 1.0mm thin-wall diffuser that glows when backlit by the existing U-shaped WS2812B LED strip. The pattern is asymmetric and restrained — cyberpunk but not overwrought.

## Constraints

- **Recess depth:** 1.5mm into the 2.5mm wall (leaves 1.0mm diffuser skin)
- **Bar height:** 3mm tall each
- **Minimum spacing:** 6mm solid wall between adjacent bars
- **Edge clearance:** No cuts within 5mm of top edge (snap clips at Z=50) or bottom edge (floor at Z=0)
- **Usable Z range:** Z=6 to Z=44
- **No new LED routing:** Uses existing U-shaped strip (left, front, right walls)
- **Sharp rectangular edges:** No fillets on bar recesses (cyberpunk aesthetic)
- **Structural integrity:** Narrow bars with wide solid sections between them preserve wall rigidity

## Layout

### Left wall (-X side, ~175mm along Y)

3 bars, staggered heights:

| Bar | Length | Z center | Y offset | Notes |
|-----|--------|----------|----------|-------|
| 1   | 60mm   | Z=15     | toward front | longest bar, low placement |
| 2   | 25mm   | Z=30     | toward front | short, high |
| 3   | 40mm   | Z=10     | toward rear  | medium, lowest |

### Right wall (+X side, ~175mm along Y)

3 bars, asymmetric to left wall:

| Bar | Length | Z center | Y offset | Notes |
|-----|--------|----------|----------|-------|
| 1   | 45mm   | Z=25     | centered     | medium, mid-height |
| 2   | 20mm   | Z=12     | toward rear  | shortest, low |
| 3   | 55mm   | Z=35     | toward front | long, highest |

### Front wall (-Y side, ~240mm along X)

Logo stays at Z=20, center. Two short accent bars flanking it:

| Bar | Length | Z center | X offset | Notes |
|-----|--------|----------|----------|-------|
| 1   | 30mm   | Z=35     | near left edge  | above logo height |
| 2   | 25mm   | Z=12     | near right edge | below logo height |

## Implementation

All cuts happen in `build_bottom_tray()` after the existing LED channel/slot code. Each bar is a `cq.Workplane("XY")` box cut from the exterior wall face inward by 1.5mm, 3mm tall, at the specified length and position.

### Parameters (new constants)

```python
# --- Cyberpunk diffuser bars ---
CYBER_BAR_H = 3            # bar height (Z)
CYBER_BAR_DEPTH = 1.5      # recess depth (leaves 1.0mm diffuser)
CYBER_DIFFUSER_T = 1.0     # remaining wall thickness (diffuser skin)
```

### No changes to

- LED strip channel geometry
- LED exit slots at base
- Backlit logo
- Top tray, device tray, or any other part
- QuinLED / ESP32 / servo mounts
- Snap clips or structural features

## Verification

After export + push + cadquery-server restart, verify:
1. Bars visible as recesses on exterior walls in 3D preview
2. No interference with interior components (LED channel, mounts, wiring grooves)
3. Wall integrity — solid wall remains between and around all bars
4. Logo unobstructed on front wall
