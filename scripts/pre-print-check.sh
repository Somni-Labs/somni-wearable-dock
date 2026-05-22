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
  if [ "$BED_TEMP" = "null" ] || [ "$(echo "$BED_TEMP <= 0" | bc -l)" = "1" ]; then
    fail "Gcode first_layer_bed_temp is $BED_TEMP — slicer profile likely broken" "Re-slice with corrected profile (flat INI, no section headers)"
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
