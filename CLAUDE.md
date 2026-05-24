# Somni Wearable Dock

Parametric charging stand for wearable devices, designed in CadQuery and printed on a QIDI Q2 via Klipper/Moonraker.

## Architecture

- **`designs/v1-charging-stand.py`** — Main CadQuery parametric design (5 parts: bottom tray, top tray, mudra pole, iPad cover plate, iPad back wall)
- **`export_charging_stand.py`** — STL/STEP export script (strips cq_server dependency, flips top tray for printing)
- **`k8s/slice-all-parts.yaml`** — K8s Job template for PrusaSlicer slicing + Moonraker upload
- **`output/`** — Generated STL/STEP files
- **`scripts/pre-print-check.sh`** — Pre-print validation (Moonraker API checks: printer state, filament, gcode metadata)
- **ESP32 mount** — DevKitC V4 pin-header slot-cradle in bottom tray front-left corner, USB port through front wall
- **RGB underglow** — WS2812B LED strip channel (U-shaped: left, front, right walls) with 3mm light exit slots at base
- **Backlit logo** — "Somni Labs" recessed into front wall exterior with 0.6mm thin-wall diffuser, backlit by RGB strip
- **QuinLED-Dig-Uno mount** — WLED controller (50x50mm) in bottom tray front-right corner, onboard level shifting, drives WS2812B LED strip
- **Motorized reveal** — 4x SG90 servo mounts in bottom tray (Y=-37), push rod slots in top tray, servo wiring channels with arch clips
- **Proximity sensor** — VL53L0X ToF laser mount (front wall, right of ESP32) with front wall window for hands-free reveal activation
- **Ghost visualization** — Translucent colored component overlays in cadquery-server preview (ESP32, QuinLED, servos, sensor, charger, LED strip)
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

The Mudra L-pole overhang required 48% of the top tray's filament for support material (110m, 20+ extra hours). Separating the pole into its own snap-in part eliminates supports entirely — the pole prints upright and the top tray has a simple through-socket. Assembly: 5 parts (bottom tray, top tray, mudra pole, iPad cover plate, iPad back wall).

### Tall vertical walls should be separate parts printed flat

The iPad back wall (60mm tall, 4mm thick, 245mm wide) was originally unioned onto the top tray. When the top tray is flipped for printing, the wall becomes the tallest feature (~77mm total), adding hours of print time for a simple flat slab. Separating the wall into a slide-in tongue-and-groove piece lets it print flat on its back (4mm tall, ~15 minutes) and cuts the top tray print from ~77mm to ~17mm.

**Rule of thumb:** If a feature adds significant height to a flipped print but is geometrically simple (flat wall, shelf, bracket), make it a separate part that prints in its natural orientation.

### Mudra pole snap clips need dedicated beefier constants

The tray-to-tray SNAP_* constants (SNAP_HOOK=1.2mm, SNAP_CLIP_W=12mm) are too thin for the Mudra pole clips. A 1.2mm cantilever arm snaps on insertion every time. The Mudra pole now uses dedicated MUDRA_CLIP_* constants: MUDRA_CLIP_T=2.5mm arm thickness, MUDRA_CLIP_W=14mm width, MUDRA_HOOK=2.0mm overhang. The top tray socket engagement pockets are sized to match.

### Flipped prints need a continuous floor — through-cuts fragment the build surface

The top tray is printed flipped (Z=58 on build plate, Z=41 on top). Every through-cut in the tray body (cable holes, push rod slots, mudra socket, iPad cable tunnel, LCD window, iPad blade slot) becomes a hole in the first printed layers. When these cuts are numerous and close together, they fragment the bottom face into disconnected islands that print as flimsy, unconnected pieces with no structural floor.

**Fix**: Added a `LID_FLOOR` (2mm) solid slab across the entire interior of the top tray at Z=SPLIT_Z, inset from the outer walls to avoid interfering with snap clips and wall pass-throughs. After the floor is unioned, only essential through-holes are re-cut: push rod slots (4×12mm, servo rods must pass through), mudra pole socket (20.6×22.6mm, pole drops in), mudra cable hole, device cable pass-throughs (14×9mm each), G2 LCD window, iPad cable vertical hole, and iPad blade slot.

**Rule of thumb:** When a part is printed flipped, verify the bottom face (which becomes the first printed layers) is a single connected surface. Add a continuous floor and re-cut only the minimum necessary through-holes.

### Always enable supports when printing the top tray flipped

The flipped top tray has device pockets (UH, R1, Omi, G2) facing down on the build plate, creating massive unsupported overhangs. PrusaSlicer will even warn about "floating bridge anchors" and "loose extrusions." Without supports, the print spaghettifies immediately.

**Fix**: Set `support_material = 1`, `support_material_auto = 1` in the slicer profile. Add `brim_width = 5` for bed adhesion. The `validate_gcode()` function should check for `;TYPE:Support` presence when slicing the top tray.


## Errors Encountered and Fixed

### Mudra pole snap clips broke on insertion

**Error**: The snap clips on the Mudra pole base snapped off during insertion into the top tray socket. The arms were too thin (1.2mm) to survive the flex required during snap-in.

**Cause**: Used shared SNAP_HOOK (1.2mm) constant — adequate for the wide tray-to-tray clips backed by 2.5mm walls, but far too thin for standalone cantilever arms on a small pole.

**Fix**: Added dedicated MUDRA_CLIP_* constants (MUDRA_CLIP_T=2.5mm, MUDRA_CLIP_W=14mm, MUDRA_HOOK=2.0mm, MUDRA_HOOK_H=2.0mm). Updated both `build_mudra_pole()` clip geometry and the top tray socket engagement pockets to use the new constants. More than 2× the arm thickness of the original design.

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

### Spaghetti print from missing support material

**Error**: Top tray print spaghettified — filament extruded into air with no support structure beneath the pocket overhangs.

**Cause**: The slicer K8s Job (`k8s/slice-top-tray.yaml`) was created with `support_material = 0`, incorrectly assuming the flipped orientation wouldn't need supports. The flipped top tray has all pocket openings facing down.

**Fix**: Changed to `support_material = 1` with `support_material_auto = 1`, added `brim_width = 5`, and added support material validation in the gcode validator to catch this before printing.

### Top tray printed as disconnected islands (no floor)

**Error**: After fixing the spaghetti issue with supports, the top tray printed with many disconnected sections — no continuous floor connecting the device pocket areas. The print was structurally unsound and flimsy.

**Cause**: The top tray had 15+ through-cuts (cable holes, push rod slots, mudra socket, iPad cable tunnel spanning full width, LCD window, iPad blade slot) that fragmented the bottom face (Z=41) into thin strips and isolated patches. When printed flipped, these holes appear in the first layers, preventing the formation of a connected base.

**Fix**: Added a `LID_FLOOR` (2mm) solid floor slab across the interior at Z=SPLIT_Z using `base.union()`. Essential through-holes (push rods, mudra socket, cable pass-throughs) are re-cut at minimum size through the new floor. The iPad cable tunnel, which previously spanned the full 240mm width at Z=42, is now blocked by the floor — the cable routes through the smaller vertical cable hole instead.
