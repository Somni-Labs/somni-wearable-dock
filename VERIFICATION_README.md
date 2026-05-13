# Omi DevKit 2 Pocket Verification Guide

## Quick Test (Recommended)

**Print and cut test:**
1. Print `omi_pocket_template.svg` at **100% scale** (NO scaling!)
2. Cut out the **RED outline** carefully with scissors or craft knife
3. Test fit your Omi DevKit 2 pendant through the cutout
4. ✅ **Pass**: Pendant slides through with slight clearance  
5. ❌ **Fail**: Adjust `TOL` parameter in `designs/v1-charging-stand.py`

## Files Generated

| File | Purpose | How to Use |
|------|---------|------------|
| `omi_pocket_template.svg` | 📄 **Print template** | Print 1:1, cut out RED line, test fit |
| `omi_pocket_dimensions.txt` | 📋 Dimensions reference | Check measurements vs your calipers |
| `omi_pocket_2d.dxf` | 🔧 CAD import (precise) | Open in CAD software for verification |
| `omi_pocket_template.step` | 🔧 3D CAD model | Import into Fusion 360, SolidWorks, etc. |
| `omi_pocket_coordinates.csv` | 📊 Coordinate data | Manual verification, spreadsheet analysis |
| `omi_pocket_outline.gcode` | ⚙️ CNC template cut | Run on CNC router (1mm deep template) |

## Verification Checklist

- [ ] **Shape**: Six-sided diamond (NOT triangle or circle)  
- [ ] **Top facet**: ~25mm wide, narrow section at top
- [ ] **Bottom point**: Single point at bottom (NOT rounded)
- [ ] **Width**: 42mm max (41mm pendant + 1mm tolerance)
- [ ] **Height**: 41mm max (40mm pendant + 1mm tolerance)
- [ ] **Fit**: Pendant slides through with 0.5mm clearance all around

## Current Design Values

```python
# From designs/v1-charging-stand.py
TOL = 0.5                    # Print tolerance per side
OMI_W = 41 + TOL * 2        # 42mm pocket width  
OMI_H = 40 + TOL * 2        # 41mm pocket height
OMI_THICK = 13              # 13mm pendant thickness
OMI_CRADLE_DEPTH = 15       # 15mm pocket depth (13+2)
OMI_VERTEX_R = 3            # 3mm fillet radius
```

## If Fit is Wrong

**Too tight** (pendant doesn't fit):
- Increase `TOL = 0.75` (1.5mm total tolerance)

**Too loose** (pendant falls through):  
- Decrease `TOL = 0.25` (0.5mm total tolerance)

**Shape doesn't match**:
- Verify pendant measurements with calipers
- Check six-sided diamond vs pendant silhouette
- Consider custom shape adjustments

## What's Next

1. ✅ Verify fit with template
2. ✅ Confirm pocket depth accommodates 13mm thickness  
3. ✅ 3D print full charging stand
4. ✅ Test actual pendant charging alignment