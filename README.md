# Wearable Charging Stand

3D printable unified charging dock for 6 non-Apple wearable devices, with a hidden internal slim 4-port USB-C wall charger and cable management.

## Devices

| Slot | Device | Charger Type | Cradle Style |
|------|--------|-------------|--------------|
| 1 | Omi Pendant (DevKit 2) | Pogo-pin magnetic cable | Circular cup (25mm) |
| 2 | Ultrahuman Ring Air | USB-C puck dock (~50mm) | Circular cup |
| 3 | Even Realities R1 Ring | NFC magnetic dock (~45mm) | Circular cup |
| 4 | Even Realities G1 Glasses | USB-C case (~170×70mm) | Rectangular shelf |
| 5 | Omi Developer Edition | Triangle pendant charger | Triangular pocket |
| 6 | Mudra Link Wristband | Proprietary cable | Rectangular pocket |

## Design Features

- **Single AC input** — one cable from the wall to the internal multi-port USB-C charger
- **Hidden cable routing** — channels inside the base route cables from the charger to each cradle
- **Bottom access panel** — removable cover (v2) / removable top tray (v1) to install the charger and manage cables
- **Cradle-per-charger** — each device's existing charger sits in a fitted pocket; cables route through pass-through holes
- **Rubber feet recesses** — stick-on feet for grip and airflow
- **Clean desktop aesthetic** — dark PETG, rounded edges, no visible cables

## Design Files

| File | Description |
|------|-------------|
| `designs/v1-charging-stand.py` | Two-part snap-fit design (bottom tray + top tray), with iPad slot |
| `designs/v2-charging-stand.py` | Single-piece design with bottom access panel |
| `stl/` | Exported STL files ready for slicing |

## Dimensions

All cradle dimensions are parametric and defined at the top of the design file. After a test print, measure your actual chargers and adjust the `TOL` (tolerance) and individual device dimensions as needed.

**Note:** Some charger dimensions are estimated from product photos since manufacturers don't publish exact specs. Adjust after test fitting:
- Ultrahuman Ring charger: estimated ~50mm diameter puck
- Even R1 charger: estimated ~45mm diameter dock
- Even G1 case: estimated ~170×70×40mm
- Omi Dev Edition: estimated ~35mm triangle side

## Print Settings

- **Material:** PETG (dark grey/black recommended)
- **Layer height:** 0.2mm
- **Infill:** 20%
- **Walls:** 3 perimeters
- **Supports:** Minimal (cradle cups print fine without)

## Internal USB-C Charger

The stand houses a **slim flat 4-port USB-C wall charger** inside the base, centered under the G2 case shelf. A single AC cable feeds the charger from behind; short USB-C cables route from each output to the cradles through the internal channels.

**Recess dimensions:** 88 × 55 × 17 mm (W × D × H), includes ~3 mm tolerance per side.

### Why a wall charger instead of a USB-C data hub

A passive USB-C "hub" shares a single upstream PD profile across all downstreams, so it can't reliably negotiate independent charging for 6 wearables that each expect their own power profile. A multi-port USB-C wall charger contains independent regulators per port — the architecture each wearable's bundled charger expects.

### Recommended charger class

Look for a **slim flat 4-port USB-C wall charger** at ~30–35 W total with a mix of USB-C and USB-A outputs (typically 1× USB-C PD + 1× USB-C + 2× USB-A). The recess accepts the common "flat brick" form factor (≈83 × 44 × 14 mm).

- ✅ **Fits:** BUDI 34W 4-Port Flat USB-C Wall Charger (slim profile, 20W PD on the primary USB-C port). Any flat 4-port charger within the recess envelope and ≥30 W total works.
- ❌ **Does not fit:** UGREEN Nexode 65W/100W and similar GaN multi-port chargers — they are roughly 65 × 65 × 33 mm because they contain a full wall-AC supply in a cube form factor.
- ❌ **Do not use** a USB-C data hub (CalDigit, Anker thin hubs, etc.) for power splitting — they cannot independently power-deliver to multiple downstreams.

Total wearable load is well under 30 W (each device draws ≤5 W), so a 30–35 W charger has headroom even when everything is on the dock simultaneously.

## Editing

Designs use [CadQuery](https://cadquery.readthedocs.io/) and render via [cadquery-server](https://github.com/robodk/cadquery-server).

```bash
pip install cadquery cadquery-server
cq-server /path/to/designs/
```

## License

MIT
