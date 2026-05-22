# Reliable Slicer Pipeline + Pre-Print Validation

**Date**: 2026-05-22
**Status**: Approved
**Trigger**: Top tray print spaghettified because PrusaSlicer silently ignored support_material setting from sectioned INI file

## Problem

The K8s slicer job (`k8s/slice-all-parts.yaml`) writes a PrusaSlicer profile with `[print:PLA+]`, `[filament:PLA+]`, and `[printer:QIDI_Q2]` section headers. PrusaSlicer's `--load` flag expects a **flat key=value INI** with no section headers. When it encounters section headers, it silently falls back to defaults for all settings in those sections.

This caused two documented failures:
1. **Bed temperature 0C** — PrusaSlicer defaulted to `bed_temperature = 0` instead of the specified 60C. Worked around with `fix_temps()` sed post-processing.
2. **Support material off** — PrusaSlicer defaulted to `support_material = 0` instead of the specified 1. No workaround existed. The top tray (102mm tall, printed flipped with 36mm horizontal Mudra shelf overhang) printed without supports and spaghettified at ~Z=11mm.

The `fix_temps()` function is a band-aid that only patches temperature commands. Other settings (supports, fan speeds, infill density, retraction, etc.) were also silently wrong but happened not to cause visible failures — until now.

## Solution

Three changes that eliminate the root cause and add two defense layers:

### 1. Fix the INI Profile (Root Cause)

Remove section headers from the slicer profile. The INI becomes a flat key=value file with comment-based grouping:

```ini
# --- Print settings ---
layer_height = 0.2
first_layer_height = 0.25
perimeters = 3
top_solid_layers = 5
bottom_solid_layers = 4
fill_density = 20%
fill_pattern = gyroid
external_perimeter_speed = 40
infill_speed = 60
travel_speed = 150
bridge_speed = 25
support_material = 1
support_material_auto = 1
support_material_spacing = 2
support_material_angle = 0
skirts = 2
skirt_distance = 5
brim_width = 0

# --- Filament settings (PLA+) ---
temperature = 215
first_layer_temperature = 220
bed_temperature = 60
first_layer_bed_temperature = 65
fan_always_on = 1
min_fan_speed = 100
max_fan_speed = 100
bridge_fan_speed = 100

# --- Printer settings (QIDI Q2) ---
gcode_flavor = klipper
bed_shape = 0x0,275x0,275x295,0x295
max_print_height = 265
nozzle_diameter = 0.4
retract_length = 0.8
retract_speed = 40
retract_lift = 0.2
start_gcode = G28\nG1 Z5 F5000
end_gcode = END_PRINT
```

The `fix_temps()` function is deleted entirely. PrusaSlicer will emit correct temperature, support, and all other commands natively from the flat INI.

The `sed -i 's/^[[:space:]]*//' "$INI"` line is retained — it strips leading whitespace that YAML heredocs add, which is still necessary.

### 2. Post-Slice Gcode Validator

A `validate_gcode()` bash function runs after each slice, before upload. It parses the generated gcode and asserts critical settings are present and correct.

**Checks:**

| Check | Assertion | How |
|-------|-----------|-----|
| Bed temperature | `M190` or `M140` command present with target >= 55C | grep + awk on gcode |
| Extruder temperature | `M109` or `M104` command present with target >= 210C | grep + awk on gcode |
| Support material | `;TYPE:Support` lines present | grep on gcode |
| Layer count | More than 10 `LAYER_CHANGE` markers (sanity — not empty/corrupt) | grep -c on gcode |
| Coordinate bounds | No G1 X values > 275, no G1 Y values > 295 (all moves, including travel) | grep + awk on gcode |

**Support check nuance:** The support check is conditional. It only applies to parts that need supports (tall parts with overhangs). The validator accepts a `--require-supports` flag. In the slicer job:
- Bottom tray (41mm, no overhangs): no `--require-supports`
- Top tray (102mm, Mudra shelf overhang): `--require-supports`
- iPad cover (2mm flat plate): no `--require-supports`

**Failure behavior:** If any assertion fails, the function prints a clear error message identifying exactly what was wrong and exits non-zero. The slicer job aborts — no gcode is uploaded to Moonraker.

**Location:** Inline bash function in `k8s/slice-all-parts.yaml`, called between the `$SLICER` command and the `curl` upload for each part.

### 3. Pre-Print Check Script

A standalone script at `scripts/pre-print-check.sh` that validates printer readiness before starting a print. Called manually or by future automation.

**Usage:**
```bash
./scripts/pre-print-check.sh <gcode-filename>
# Example:
./scripts/pre-print-check.sh v1-charging-stand-top-tray.gcode
```

**Checks:**

| Check | API Endpoint | Assertion | On Failure |
|-------|-------------|-----------|------------|
| Printer reachable | `GET /printer/info` | HTTP 200, state present | Abort: "Printer unreachable" |
| Printer ready | `GET /printer/info` | `state == "ready"` | Abort: show current state |
| Not already printing | `GET /printer/objects/query?print_stats` | `state == "standby"` | Abort: "Print already active" |
| Filament sensor enabled | `GET /printer/objects/query?filament_switch_sensor...` | `enabled == true` | Auto-fix: run `ENABLE_ALL_SENSOR` macro via `POST /printer/gcode/script`, re-check |
| Filament detected | Same endpoint | `filament_detected == true` | Abort: "Load filament before printing" |
| Gcode file exists | `GET /server/files/metadata?filename=...` | HTTP 200 | Abort: "File not found on printer" |
| Gcode bed temp | Same metadata response | `first_layer_bed_temp > 0` | Abort: "Bed temp is 0 — slicer profile broken" |
| Gcode estimated time | Same metadata response | `estimated_time > 60` | Abort: "Estimated time suspiciously low" |

**Dependencies:** `curl` and `jq` (both available in standard container images and on the host).

**Moonraker base URL:** Hardcoded as `MOONRAKER="http://192.168.1.15:7125"` with an optional `$MOONRAKER_URL` env var override.

**Exit behavior:**
- Exit 0 + "Pre-flight passed — safe to print `<filename>`"
- Exit non-zero + specific error message + remediation instructions

**Filament sensor auto-fix:** When the sensor is disabled (not broken, just turned off — which is the QIDI Q2 default), the script automatically enables it by sending the `ENABLE_ALL_SENSOR` gcode macro, waits 2 seconds, then re-queries. If it's still disabled after the fix attempt, it aborts. This matches the existing CLAUDE.md lesson about the sensor shipping disabled.

### 4. CLAUDE.md Updates

**Remove:** The "PrusaSlicer ignores filament temperatures from combined INI profiles" lesson and its `fix_temps()` documentation. This was a misdiagnosis — the real issue was section headers, not PrusaSlicer behavior.

**Add:** New lesson documenting the flat INI requirement:

> ### PrusaSlicer `--load` requires flat INI — no section headers
>
> PrusaSlicer's `--load` flag expects a flat key=value INI file. If the file contains `[section]` headers (like `[print:PLA+]`), PrusaSlicer silently ignores all settings and falls back to defaults. Use comment-based grouping (`# --- Print settings ---`) instead of section headers.

**Update:** The "Always check the filament sensor before starting a print" lesson to reference the new `scripts/pre-print-check.sh` script as the standard way to do this.

**Add:** Documentation of the post-slice validation and pre-print check as mandatory pipeline steps.

## Files Changed

| File | Change |
|------|--------|
| `k8s/slice-all-parts.yaml` | Remove section headers from INI, delete `fix_temps()`, add `validate_gcode()`, call validator after each slice |
| `scripts/pre-print-check.sh` | New file — pre-print validation script |
| `CLAUDE.md` | Update lessons learned, document new pipeline |

## What This Prevents

- Spaghetti from missing supports (the immediate failure)
- Silent wrong temperatures (the previous band-aided failure)
- Silent wrong fan/infill/retraction settings (never caught, possibly affecting print quality)
- Printing with no filament loaded (filament sensor check)
- Printing on a cold bed (metadata check)
- Uploading corrupt/empty gcode (layer count check)
- Out-of-bounds moves (coordinate check)
