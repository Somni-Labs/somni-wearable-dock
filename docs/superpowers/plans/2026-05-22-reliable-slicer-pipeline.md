# Reliable Slicer Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the PrusaSlicer INI parsing bug that caused spaghetti prints, add post-slice gcode validation, and add a pre-print Moonraker check script.

**Architecture:** Flat INI file (no section headers) fixes the root cause. A `validate_gcode()` bash function in the slicer job validates gcode after slicing. A standalone `scripts/pre-print-check.sh` queries Moonraker before printing.

**Tech Stack:** Bash, PrusaSlicer CLI, Moonraker REST API, curl, awk, jq, Kubernetes Job YAML

---

## File Structure

| File | Role |
|------|------|
| `k8s/slice-all-parts.yaml` | Modify: flat INI, delete `fix_temps()`, add `validate_gcode()` |
| `scripts/pre-print-check.sh` | Create: standalone pre-print validation script |
| `CLAUDE.md` | Modify: update lessons learned, document new pipeline |

---

### Task 1: Fix the INI Profile and Delete fix_temps()

**Files:**
- Modify: `k8s/slice-all-parts.yaml`

- [ ] **Step 1: Replace the sectioned INI with a flat key=value INI**

In `k8s/slice-all-parts.yaml`, replace lines 27-68 (the heredoc content from `cat > "$INI"` through `PROFILE`) with:

```yaml
          cat > "$INI" << 'PROFILE'
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
          PROFILE
```

The only change vs. the old content: the three section header lines (`[print:PLA+]`, `[filament:PLA+]`, `[printer:QIDI_Q2]`) are replaced with comment lines (`# --- Print settings ---`, etc.).

- [ ] **Step 2: Delete the fix_temps() function**

Remove lines 72-85 (the entire `fix_temps()` function definition):

```bash
          fix_temps() {
            local FILE="$1"
            echo "  Post-processing temps in $FILE"
            ...
            head -25 "$FILE" | grep -E "(M104|M109|M140|M190)" || echo "  NONE"
          }
```

- [ ] **Step 3: Remove fix_temps calls from each slice section**

Remove these three lines (one per part):
- `fix_temps /tmp/bottom.gcode` (after bottom tray slice)
- `fix_temps /tmp/top.gcode` (after top tray slice)
- `fix_temps /tmp/cover.gcode` (after iPad cover slice)

- [ ] **Step 4: Update the job header echo**

Change `echo "=== PrusaSlicer — All 3 Parts (with temp post-processing) ==="` to:
```bash
          echo "=== PrusaSlicer — All 3 Parts (with gcode validation) ==="
```

- [ ] **Step 5: Commit**

```bash
git add k8s/slice-all-parts.yaml
git commit -m "fix: replace sectioned INI with flat key=value format

PrusaSlicer --load requires flat INI without [section] headers.
The section headers caused silent fallback to defaults for all
settings (bed temp 0C, supports off, etc). Remove fix_temps()
workaround — no longer needed."
```

---

### Task 2: Add validate_gcode() Function

**Files:**
- Modify: `k8s/slice-all-parts.yaml`

- [ ] **Step 1: Add the validate_gcode() function after the sed whitespace strip**

Insert immediately after the `sed -i 's/^[[:space:]]*//' "$INI"` line:

```bash
          validate_gcode() {
            local FILE="$1"
            local REQUIRE_SUPPORTS="${2:-}"
            local ERRORS=0

            echo "  Validating $FILE..."

            # Check 1: Bed temperature — M140 or M190 with target >= 55
            local BED_TEMP
            BED_TEMP=$(grep -oP '^M1[49]0 S\K[0-9]+' "$FILE" | head -1)
            if [ -z "$BED_TEMP" ] || [ "$BED_TEMP" -lt 55 ]; then
              echo "  FAIL: Bed temperature missing or too low (got: ${BED_TEMP:-none}, need >= 55)"
              ERRORS=$((ERRORS + 1))
            else
              echo "  OK: Bed temperature = ${BED_TEMP}C"
            fi

            # Check 2: Extruder temperature — M104 or M109 with target >= 210
            local EXT_TEMP
            EXT_TEMP=$(grep -oP '^M10[49] S\K[0-9]+' "$FILE" | sort -n | tail -1)
            if [ -z "$EXT_TEMP" ] || [ "$EXT_TEMP" -lt 210 ]; then
              echo "  FAIL: Extruder temperature missing or too low (got: ${EXT_TEMP:-none}, need >= 210)"
              ERRORS=$((ERRORS + 1))
            else
              echo "  OK: Extruder temperature = ${EXT_TEMP}C"
            fi

            # Check 3: Support material (conditional)
            if [ "$REQUIRE_SUPPORTS" = "--require-supports" ]; then
              local SUPPORT_LINES
              SUPPORT_LINES=$(grep -c ';TYPE:Support' "$FILE" || true)
              if [ "$SUPPORT_LINES" -eq 0 ]; then
                echo "  FAIL: No support material found (;TYPE:Support missing)"
                ERRORS=$((ERRORS + 1))
              else
                echo "  OK: Support material present ($SUPPORT_LINES sections)"
              fi
            fi

            # Check 4: Layer count sanity (> 10 layers)
            local LAYER_COUNT
            LAYER_COUNT=$(grep -c ';LAYER_CHANGE' "$FILE" || true)
            if [ "$LAYER_COUNT" -lt 10 ]; then
              echo "  FAIL: Only $LAYER_COUNT layers — file may be corrupt or empty"
              ERRORS=$((ERRORS + 1))
            else
              echo "  OK: $LAYER_COUNT layers"
            fi

            # Check 5: Coordinate bounds (X <= 275, Y <= 295)
            local X_MAX Y_MAX
            X_MAX=$(awk '/^G1 .*X[0-9]/ { match($0, /X([0-9.]+)/, a); if (a[1]+0 > max) max=a[1]+0 } END { printf "%.1f", max }' "$FILE")
            Y_MAX=$(awk '/^G1 .*Y[0-9]/ { match($0, /Y([0-9.]+)/, a); if (a[1]+0 > max) max=a[1]+0 } END { printf "%.1f", max }' "$FILE")
            if [ "$(echo "$X_MAX > 275" | bc -l)" -eq 1 ]; then
              echo "  FAIL: X coordinate out of bounds (max X = ${X_MAX}, limit 275)"
              ERRORS=$((ERRORS + 1))
            else
              echo "  OK: X max = ${X_MAX} (limit 275)"
            fi
            if [ "$(echo "$Y_MAX > 295" | bc -l)" -eq 1 ]; then
              echo "  FAIL: Y coordinate out of bounds (max Y = ${Y_MAX}, limit 295)"
              ERRORS=$((ERRORS + 1))
            else
              echo "  OK: Y max = ${Y_MAX} (limit 295)"
            fi

            if [ "$ERRORS" -gt 0 ]; then
              echo "  ABORT: $ERRORS validation error(s) in $FILE"
              exit 1
            fi
            echo "  PASS: All checks passed for $FILE"
          }
```

- [ ] **Step 2: Call validate_gcode() after each slice (before upload)**

Replace the bottom tray section:
```bash
          # ── BOTTOM TRAY ──
          echo "--- Slicing bottom tray ---"
          $SLICER --load "$INI" --center 137,147 \
            --output /tmp/bottom.gcode --export-gcode /tmp/input-bottom/bottom-tray.stl
          validate_gcode /tmp/bottom.gcode
          echo "--- Uploading bottom tray ---"
```

Replace the top tray section:
```bash
          # ── TOP TRAY ──
          echo "--- Slicing top tray ---"
          $SLICER --load "$INI" --center 137,147 \
            --output /tmp/top.gcode --export-gcode /tmp/input-top/top-tray.stl
          validate_gcode /tmp/top.gcode --require-supports
          echo "--- Uploading top tray ---"
```

Replace the iPad cover section:
```bash
          # ── IPAD COVER ──
          echo "--- Slicing iPad cover ---"
          $SLICER --load "$INI" --center 137,147 \
            --output /tmp/cover.gcode --export-gcode /tmp/input-cover/ipad-cover.stl
          validate_gcode /tmp/cover.gcode
          echo "--- Uploading iPad cover ---"
```

Note: only the top tray gets `--require-supports`.

- [ ] **Step 3: Verify the complete YAML is well-formed**

Run: `python3 -c "import yaml; yaml.safe_load(open('k8s/slice-all-parts.yaml'))"`
Expected: No output (success)

- [ ] **Step 4: Commit**

```bash
git add k8s/slice-all-parts.yaml
git commit -m "feat: add post-slice gcode validator

validate_gcode() checks bed temp, extruder temp, layer count,
coordinate bounds, and (optionally) support material presence.
Aborts the slicer job before upload if any check fails."
```

---

### Task 3: Create Pre-Print Check Script

**Files:**
- Create: `scripts/pre-print-check.sh`

- [ ] **Step 1: Create scripts directory**

```bash
mkdir -p scripts
```

- [ ] **Step 2: Write the pre-print-check.sh script**

Create `scripts/pre-print-check.sh` with this content:

```bash
#!/usr/bin/env bash
# Pre-print validation — checks printer readiness and gcode sanity
# before starting a print via Moonraker.
#
# Usage: ./scripts/pre-print-check.sh <gcode-filename>
# Example: ./scripts/pre-print-check.sh v1-charging-stand-top-tray.gcode
#
# Exit 0 = safe to print, exit 1 = problem found (details printed)
#
# Dependencies: curl, jq

set -euo pipefail

MOONRAKER="${MOONRAKER_URL:-http://192.168.1.15:7125}"
FILENAME="${1:-}"

if [ -z "$FILENAME" ]; then
  echo "Usage: $0 <gcode-filename>"
  echo "Example: $0 v1-charging-stand-top-tray.gcode"
  exit 1
fi

ERRORS=0

fail() {
  echo "FAIL: $1"
  if [ -n "${2:-}" ]; then
    echo "  Fix: $2"
  fi
  ERRORS=$((ERRORS + 1))
}

ok() {
  echo "  OK: $1"
}

echo "=== Pre-Print Check: $FILENAME ==="
echo "  Moonraker: $MOONRAKER"
echo ""

# --- Check 1: Printer reachable ---
echo "--- Printer connectivity ---"
PRINTER_INFO=$(curl -s --max-time 5 "$MOONRAKER/printer/info" 2>/dev/null) || {
  fail "Printer unreachable at $MOONRAKER" "Check network connection and Moonraker service"
  echo ""
  echo "ABORT: $ERRORS error(s). Cannot proceed."
  exit 1
}

# --- Check 2: Printer state is "ready" ---
PRINTER_STATE=$(echo "$PRINTER_INFO" | jq -r '.result.state')
if [ "$PRINTER_STATE" != "ready" ]; then
  fail "Printer state is '$PRINTER_STATE' (need 'ready')" "Resolve printer error/shutdown first"
else
  ok "Printer state: ready"
fi

# --- Check 3: Not already printing ---
echo ""
echo "--- Print state ---"
PRINT_STATS=$(curl -s --max-time 5 "$MOONRAKER/printer/objects/query?print_stats" | jq -r '.result.status.print_stats.state')
if [ "$PRINT_STATS" != "standby" ]; then
  fail "Print state is '$PRINT_STATS' (need 'standby')" "Wait for current print to finish or cancel it"
else
  ok "Print state: standby (idle)"
fi

# --- Check 4: Filament sensor enabled ---
echo ""
echo "--- Filament sensor ---"
SENSOR_DATA=$(curl -s --max-time 5 "$MOONRAKER/printer/objects/query?filament_switch_sensor%20filament_switch_sensor")
SENSOR_ENABLED=$(echo "$SENSOR_DATA" | jq -r '.result.status["filament_switch_sensor filament_switch_sensor"].enabled')
FILAMENT_DETECTED=$(echo "$SENSOR_DATA" | jq -r '.result.status["filament_switch_sensor filament_switch_sensor"].filament_detected')

if [ "$SENSOR_ENABLED" != "true" ]; then
  echo "  WARN: Filament sensor disabled — enabling via ENABLE_ALL_SENSOR macro..."
  curl -s --max-time 5 -X POST "$MOONRAKER/printer/gcode/script" \
    -H "Content-Type: application/json" \
    -d '{"script": "ENABLE_ALL_SENSOR"}' > /dev/null
  sleep 2
  # Re-query
  SENSOR_DATA=$(curl -s --max-time 5 "$MOONRAKER/printer/objects/query?filament_switch_sensor%20filament_switch_sensor")
  SENSOR_ENABLED=$(echo "$SENSOR_DATA" | jq -r '.result.status["filament_switch_sensor filament_switch_sensor"].enabled')
  FILAMENT_DETECTED=$(echo "$SENSOR_DATA" | jq -r '.result.status["filament_switch_sensor filament_switch_sensor"].filament_detected')
  if [ "$SENSOR_ENABLED" != "true" ]; then
    fail "Filament sensor still disabled after ENABLE_ALL_SENSOR" "Check Klipper config for sensor definition"
  else
    ok "Filament sensor enabled (auto-fixed)"
  fi
else
  ok "Filament sensor enabled"
fi

# --- Check 5: Filament detected ---
if [ "$FILAMENT_DETECTED" != "true" ]; then
  fail "No filament detected by sensor" "Load filament into extruder before printing"
else
  ok "Filament detected"
fi

# --- Check 6: Gcode file exists on printer ---
echo ""
echo "--- Gcode file: $FILENAME ---"
METADATA=$(curl -s --max-time 5 "$MOONRAKER/server/files/metadata?filename=$FILENAME")
METADATA_ERROR=$(echo "$METADATA" | jq -r '.error.message // empty')
if [ -n "$METADATA_ERROR" ]; then
  fail "File '$FILENAME' not found on printer" "Upload the gcode file first (check slicer job ran successfully)"
else
  ok "File exists on printer"

  # --- Check 7: Bed temperature in metadata ---
  BED_TEMP=$(echo "$METADATA" | jq -r '.result.first_layer_bed_temp // 0')
  if [ "$BED_TEMP" = "0" ] || [ "$BED_TEMP" = "null" ]; then
    fail "Gcode first_layer_bed_temp is 0 — slicer profile likely broken" "Re-slice with corrected profile (flat INI, no section headers)"
  else
    ok "Bed temperature: ${BED_TEMP}C"
  fi

  # --- Check 8: Estimated time sanity ---
  EST_TIME=$(echo "$METADATA" | jq -r '.result.estimated_time // 0')
  if [ "$EST_TIME" -lt 60 ] 2>/dev/null; then
    fail "Estimated print time suspiciously low (${EST_TIME}s)" "Re-slice — file may be corrupt"
  else
    HOURS=$(( EST_TIME / 3600 ))
    MINS=$(( (EST_TIME % 3600) / 60 ))
    ok "Estimated time: ${HOURS}h ${MINS}m"
  fi
fi

# --- Summary ---
echo ""
if [ "$ERRORS" -gt 0 ]; then
  echo "ABORT: $ERRORS pre-flight error(s). Do NOT start print."
  exit 1
else
  echo "PRE-FLIGHT PASSED — safe to print '$FILENAME'"
  exit 0
fi
```

- [ ] **Step 3: Make the script executable**

```bash
chmod +x scripts/pre-print-check.sh
```

- [ ] **Step 4: Test the script against the live printer**

Run: `./scripts/pre-print-check.sh v1-charging-stand-top-tray.gcode`

Expected output (all checks pass or filament sensor gets auto-enabled):
```
=== Pre-Print Check: v1-charging-stand-top-tray.gcode ===
  Moonraker: http://192.168.1.15:7125

--- Printer connectivity ---
  OK: Printer state: ready

--- Print state ---
  OK: Print state: standby (idle)

--- Filament sensor ---
  WARN: Filament sensor disabled — enabling via ENABLE_ALL_SENSOR macro...
  OK: Filament sensor enabled (auto-fixed)
  OK: Filament detected

--- Gcode file: v1-charging-stand-top-tray.gcode ---
  OK: File exists on printer
  OK: Bed temperature: 65C
  OK: Estimated time: 16h 44m

PRE-FLIGHT PASSED — safe to print 'v1-charging-stand-top-tray.gcode'
```

Note: The bed temp check will currently FAIL (shows 0) because the existing gcode on the printer was sliced with the broken sectioned INI. This confirms the validator catches the bug. After re-slicing with the fixed INI, this check will pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/pre-print-check.sh
git commit -m "feat: add pre-print validation script

Queries Moonraker API to verify printer readiness before starting
a print: connectivity, print state, filament sensor (auto-enables
if disabled), filament presence, gcode metadata sanity (bed temp,
estimated time)."
```

---

### Task 4: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Replace the "PrusaSlicer ignores filament temperatures" lesson**

Replace the section starting at line 22 (`### PrusaSlicer ignores filament temperatures from combined INI profiles`) through line 26 (ending with `...does this automatically.`) with:

```markdown
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
```

- [ ] **Step 2: Update the "Always check the filament sensor" lesson**

Replace lines 28-36 (the filament sensor lesson) with:

```markdown
### Always check the filament sensor before starting a print

The QIDI Q2 has a `filament_switch_sensor` in Klipper but it ships **disabled by default**. The `scripts/pre-print-check.sh` script handles this automatically — it queries the sensor state, enables it via the `ENABLE_ALL_SENSOR` macro if disabled, and verifies filament is physically present before allowing the print to start.

Manual check if needed:
```
GET /printer/objects/query?filament_switch_sensor+filament_switch_sensor
```
```

- [ ] **Step 3: Update the "Bed temperature at 0C" error entry**

Replace the "Bed temperature at 0C during print" error section (lines 127-132) with:

```markdown
### Bed temperature at 0C during print

**Error**: First print ran with bed heater completely off (target 0C). PLA+ adhesion was poor.

**Cause**: PrusaSlicer's `--load` flag silently ignores settings from INI files with `[section]` headers. It fell back to the default `bed_temperature = 0`.

**Fix**: Removed section headers from the INI profile (flat key=value format). The `validate_gcode()` function now checks that bed temp commands are present and >= 55C before uploading. The `pre-print-check.sh` script also checks the metadata `first_layer_bed_temp > 0` before starting.
```

- [ ] **Step 4: Add Architecture entry for scripts/**

Add to the Architecture section (after the `output/` bullet):

```markdown
- **`scripts/pre-print-check.sh`** — Pre-print validation (Moonraker API checks: printer state, filament, gcode metadata)
```

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with flat INI lesson and pre-print check

Replace outdated fix_temps() workaround documentation with correct
root cause (section headers). Document validate_gcode() and
pre-print-check.sh as mandatory pipeline steps."
```

---

### Task 5: End-to-End Verification

**Files:**
- Read: `k8s/slice-all-parts.yaml` (verify final state)
- Run: `scripts/pre-print-check.sh`

- [ ] **Step 1: Verify the final k8s/slice-all-parts.yaml is valid YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('k8s/slice-all-parts.yaml'))"`
Expected: No output (success)

- [ ] **Step 2: Verify the INI file has no section headers**

Run: `grep -n '^\[' k8s/slice-all-parts.yaml`
Expected: No output (no lines starting with `[` in the INI heredoc)

- [ ] **Step 3: Verify fix_temps is completely gone**

Run: `grep -n 'fix_temps' k8s/slice-all-parts.yaml`
Expected: No output

- [ ] **Step 4: Verify validate_gcode is called for all 3 parts**

Run: `grep -n 'validate_gcode' k8s/slice-all-parts.yaml`
Expected: 4 lines — the function definition + 3 calls (bottom, top with --require-supports, cover)

- [ ] **Step 5: Run pre-print-check.sh against the printer**

Run: `./scripts/pre-print-check.sh v1-charging-stand-top-tray.gcode`
Expected: Script runs, checks complete (bed temp metadata check may fail since old gcode is still on the printer — this is expected and confirms the validator catches the issue)

- [ ] **Step 6: Verify CLAUDE.md has no references to fix_temps()**

Run: `grep -n 'fix_temps' CLAUDE.md`
Expected: No output
