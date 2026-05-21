# Somni Wearable Dock

Parametric charging stand for wearable devices, designed in CadQuery and printed on a QIDI Q2 via Klipper/Moonraker.

## Architecture

- **`designs/v1-charging-stand.py`** — Main CadQuery parametric design (3 parts: bottom tray, top tray, iPad cover plate)
- **`export_charging_stand.py`** — STL/STEP export script (strips cq_server dependency, flips top tray for printing)
- **`k8s/slice-all-parts.yaml`** — K8s Job template for PrusaSlicer slicing + Moonraker upload
- **`output/`** — Generated STL/STEP files
- Live preview via `cadquery-server` deployment in K8s (`utilities` namespace), synced from GitHub via git-sync init container

## QIDI Q2 Printer

- **Moonraker API**: `http://192.168.1.15:7125`
- **Actual build volume**: X: 0-275, Y: 0-295, Z: 0-265 (NOT the marketed 245x255)
- **Bed shape for PrusaSlicer**: `0x0,275x0,275x295,0x295`, center `137,147`
- **Klipper gcode flavor** in all slicer profiles

## Lessons Learned

### PrusaSlicer ignores filament temperatures from combined INI profiles

PrusaSlicer does NOT reliably parse `[filament]` section temperatures when all sections (`[print]`, `[filament]`, `[printer]`) are combined in a single INI file loaded via `--load`. It falls back to defaults: extruder 200C, bed 0C. The `start_gcode` field with `\n` escapes is also not interpreted correctly.

**Fix**: Post-process the generated gcode with `sed` to replace `M104 S200` / `M109 S200` with correct temperatures and inject `M140`/`M190` bed heating commands. The K8s slicer job template in `k8s/slice-all-parts.yaml` has the `fix_temps()` function that does this automatically.

### Always check the filament sensor before starting a print

The QIDI Q2 has a `filament_switch_sensor` in Klipper but it ships **disabled by default**. Query it via Moonraker before printing:

```
GET /printer/objects/query?filament_switch_sensor+filament_switch_sensor
```

If `enabled: false` or `filament_detected: false`, enable it with the `ENABLE_ALL_SENSOR` gcode macro before starting the print. The printer will happily run an entire job with an empty extruder if the sensor is off.

### CadQuery boolean operations can fill internal cavities at union joints

When building a part in local coordinates (e.g., the Mudra pole), cutting internal cavities, then `union()`-ing it onto the main body, the solid material from the main body can fill the cavity at the junction. **Always re-cut the cavity in world coordinates after the union** to guarantee it's continuous.

### Bottom tray should be open-top (no ceiling)

An enclosed bottom tray with cable pass-through holes is much harder to use than an open-top tray. Making the bottom tray an open box lets you:
1. Drop in the charger from above
2. Route cables freely with full visibility
3. Wrap excess cable on posts and cinch with Velcro
4. Snap the top tray on as a lid

The top tray has its own cable pass-through holes where needed — the bottom tray doesn't need them.

### cadquery-server preview cycle

After any design change:
1. `python3 export_charging_stand.py` — verify build succeeds locally
2. `git commit && git push` — push to GitHub
3. `kubectl rollout restart deployment cadquery-server -n utilities` — restart to trigger git-sync
4. Check preview in browser

### Hidden cable routing needs continuous paths verified

When designing internal cable tunnels (like the iPad cable tunnel), always verify the path is continuous by checking:
- Floor holes cut through from the layer below
- Tunnel connects to the floor hole without gaps
- Exit openings break through both side walls
- Cover plates / rails don't block the cable path

### Multi-part assemblies need separate STL exports

Each printable part needs its own STL at Z=0. The top tray must be flipped 180 degrees (rotate around X axis) so the flat pocket surface prints face-down on the build plate. The export script handles this automatically.
