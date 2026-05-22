# Somni Wearable Dock

Parametric charging stand for wearable devices, designed in CadQuery and printed on a QIDI Q2 via Klipper/Moonraker.

## Architecture

- **`designs/v1-charging-stand.py`** — Main CadQuery parametric design (4 parts: bottom tray, top tray, mudra pole, iPad cover plate)
- **`export_charging_stand.py`** — STL/STEP export script (strips cq_server dependency, flips top tray for printing)
- **`k8s/slice-all-parts.yaml`** — K8s Job template for PrusaSlicer slicing + Moonraker upload
- **`output/`** — Generated STL/STEP files
- **`scripts/pre-print-check.sh`** — Pre-print validation (Moonraker API checks: printer state, filament, gcode metadata)
- Live preview via `cadquery-server` deployment in K8s (`utilities` namespace), synced from GitHub via git-sync init container

## QIDI Q2 Printer

- **Moonraker API**: `http://192.168.1.15:7125`
- **Actual build volume**: X: 0-275, Y: 0-295, Z: 0-265 (NOT the marketed 245x255)
- **Bed shape for PrusaSlicer**: `0x0,275x0,275x295,0x295`, center `137,147`
- **Klipper gcode flavor** in all slicer profiles

## Lessons Learned

### PrusaSlicer `--load` requires flat INI — no section headers

PrusaSlicer's `--load` flag expects a flat key=value INI file (like those exported via File > Export > Export Config). If the file contains `[section]` headers (like `[print:PLA+]`, `[filament:PLA+]`, `[printer:QIDI_Q2]`), PrusaSlicer silently ignores all settings and falls back to defaults (extruder 200C, bed 0C, supports off, etc).

**Fix**: Use comment-based grouping (`# --- Print settings ---`) instead of section headers. The K8s slicer job in `k8s/slice-all-parts.yaml` uses a flat INI with all settings as top-level key=value pairs.

### Post-slice gcode validation is mandatory

After slicing, the `validate_gcode()` function in `k8s/slice-all-parts.yaml` checks the generated gcode for: bed temperature >= 55C, extruder temperature >= 210C, layer count > 10, coordinate bounds within build volume (X <= 275, Y <= 295), and support material presence (for parts with `--require-supports` flag). If any check fails, the job aborts before uploading to Moonraker.

### Always run pre-print-check.sh before starting a print

The `scripts/pre-print-check.sh` script validates printer readiness via Moonraker API before any print:

```
./scripts/pre-print-check.sh <gcode-filename>
```

It checks: printer reachable, printer state ready, not already printing, filament sensor enabled (auto-enables if disabled), filament detected, gcode file exists, bed temp > 0 in metadata, estimated time > 60s.

### Always check the filament sensor before starting a print

The QIDI Q2 has a `filament_switch_sensor` in Klipper but it ships **disabled by default**. The `scripts/pre-print-check.sh` script handles this automatically — it queries the sensor state, enables it via the `ENABLE_ALL_SENSOR` macro if disabled, and verifies filament is physically present before allowing the print to start.

Manual check if needed:
```
GET /printer/objects/query?filament_switch_sensor+filament_switch_sensor
```

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

### Separate parts eliminate support material waste

The Mudra L-pole overhang required 48% of the top tray's filament for support material (110m, 20+ extra hours). Separating the pole into its own snap-in part eliminates supports entirely — the pole prints upright and the top tray has a simple through-socket. Assembly: 4 parts (bottom tray, top tray, mudra pole, iPad cover plate).

## Errors Encountered and Fixed

### PrusaSlicer "Move out of range" error

**Error**: `Move out of range: -1.001 217.928` — print failed immediately.

**Cause**: Wrong bed dimensions in the slicer profile. Used the marketed 245x255mm instead of the actual 275x295mm build volume. Also, YAML heredoc indentation added leading whitespace to the INI file, which PrusaSlicer silently misparses.

**Fix**: 
1. Corrected `bed_shape = 0x0,275x0,275x295,0x295` and `--center 137,147`
2. Added `sed -i 's/^[[:space:]]*//' "$INI"` to strip leading whitespace from the INI after writing it from a YAML heredoc

### PrusaSlicer container stuck on ARM node

**Error**: Image pull hung indefinitely — the `cznewt/prusa-slicer:latest` image is amd64-only.

**Cause**: K8s scheduled the slicer Job on an ARM node (Raspberry Pi).

**Fix**: Added `nodeSelector: kubernetes.io/arch: amd64` to the Job spec to force scheduling on an x86 node.

### Charger bay too small — wrong dimensions used

**Error**: The VanBon charger (134x68x33mm) didn't fit in the bay designed for placeholder dimensions (88x55x17mm).

**Cause**: Design used estimated charger dimensions instead of actual caliper measurements.

**Fix**: Updated `CHARGER_W=138`, `CHARGER_D=72`, `CHARGER_H=35` (measured + 4mm tolerance). Increased `SPLIT_Z` from 22 to 41mm and `STAND_H` from 38 to 58mm to accommodate the taller charger.

### Corner tabs blocked charger insertion

**Error**: 3mm corner retention tabs reduced the charger bay opening to 132x66mm — smaller than the 134x68mm charger body.

**Fix**: Removed corner tabs entirely, replaced with low-profile 5mm tall ledge strips around the perimeter that support the charger without blocking insertion from above.

### Internal ribs blocked cable routing

**Error**: Spine and cross ribs inside the bottom tray prevented cables from crossing between device lanes and blocked the charger bay.

**Fix**: Progressively simplified from full ribs → zone-based ribs → raised ribs with clearance → complete removal. The open cavity with cable winding posts and Velcro slots provides better organization than rigid ribs.

### Bottom tray had a solid ceiling (couldn't access interior)

**Error**: The cavity cut used `SPLIT_Z - BASE_H - WALL` height, leaving a 2.5mm solid ceiling. The charger couldn't be dropped in from above.

**Fix**: Changed cavity height to `SPLIT_Z - BASE_H + 1` to cut through the top surface. The bottom tray is now an open box — the top tray acts as the lid.

### Printer ran entire job with no filament loaded

**Error**: The QIDI Q2 completed a full print job extruding nothing — the filament wasn't physically loaded in the extruder.

**Cause**: The `filament_switch_sensor` was **disabled by default** in Klipper config, so no runout/presence detection occurred.

**Fix**: Query the sensor state via Moonraker before every print. If disabled, run the `ENABLE_ALL_SENSOR` Klipper macro. This is now a mandatory pre-print check.

### Bed temperature at 0C during print

**Error**: First print ran with bed heater completely off (target 0C). PLA+ adhesion was poor.

**Cause**: PrusaSlicer's `--load` flag silently ignores settings from INI files with `[section]` headers. It fell back to the default `bed_temperature = 0`.

**Fix**: Removed section headers from the INI profile (flat key=value format). The `validate_gcode()` function now checks that bed temp commands are present and >= 55C before uploading. The `pre-print-check.sh` script also checks the metadata `first_layer_bed_temp > 0` before starting.

### Moonraker upload 500 error (disk space / file locking)

**Error**: `FileNotFoundError: '/tmp/moonraker.upload-XXXXX.mru'` — upload failed with 500 Internal Server Error.

**Cause**: Race condition when deleting and immediately re-uploading the same filename. Moonraker's temp file was cleaned up before the move completed.

**Fix**: Added `sleep 2` between the delete and upload operations in the slicer job to avoid the race condition.
