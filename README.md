# Wearable Charging Stand

3D printable unified charging dock for 6 non-Apple wearable devices, with single USB-C input and hidden cable management.

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

- **Single USB-C input** — one cable from wall adapter to internal USB-C hub
- **Hidden cable routing** — channels inside the base route cables from hub to each cradle
- **Bottom access panel** — removable cover to access USB hub and manage cables
- **Cradle-per-charger** — each device's existing charger sits in a fitted pocket; cables route through pass-through holes
- **Rubber feet recesses** — stick-on feet for grip and airflow
- **Clean desktop aesthetic** — dark PETG, rounded edges, no visible cables

## Design Files

| File | Description |
|------|-------------|
| `designs/v1-charging-stand.py` | Main CadQuery design — parametric, all dimensions tunable |
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

## Internal USB Hub

Use a compact 4-6 port USB-C hub that fits in the rear recess (65×30×12mm). Route short USB-C cables from the hub to each charger through the internal channels. The hub powers from a single USB-C wall adapter (≥30W recommended for charging all devices simultaneously).

## Editing

Designs use [CadQuery](https://cadquery.readthedocs.io/) and render via [cadquery-server](https://github.com/robodk/cadquery-server).

```bash
pip install cadquery cadquery-server
cq-server /path/to/designs/
```

## License

MIT
