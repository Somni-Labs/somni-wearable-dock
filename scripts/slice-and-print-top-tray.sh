#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Slice & Print — Top Tray (separated iPad wall version)
#
# Steps:
#   1. Delete any old slicer job
#   2. Update the STL ConfigMap from the local repo output
#   3. Apply the slicer K8s Job (clones repo, slices, validates, uploads gcode)
#   4. Wait for the job to complete and show logs
#   5. Run pre-print checks
#   6. Optionally start the print
# ============================================================================

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
NAMESPACE="utilities"
JOB_NAME="slice-top-tray"
JOB_MANIFEST="$REPO_DIR/k8s/slice-top-tray.yaml"
MOONRAKER="${MOONRAKER_URL:-http://192.168.1.15:7125}"
GCODE_FILE="v1-charging-stand-top-tray.gcode"

echo "╔══════════════════════════════════════════════════╗"
echo "║  🖨️  Slice & Print — Top Tray                    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── Step 1: Clean up old job ──────────────────────────────────────────────
echo "1️⃣  Cleaning up old slicer job..."
kubectl delete job "$JOB_NAME" -n "$NAMESPACE" 2>/dev/null && echo "   Deleted old job" || echo "   No old job to delete"
echo ""

# ── Step 2: Apply slicer job ──────────────────────────────────────────────
echo "2️⃣  Applying slicer job..."
kubectl apply -f "$JOB_MANIFEST"
echo ""

# ── Step 3: Wait for job completion ───────────────────────────────────────
echo "3️⃣  Waiting for slicer job to complete (timeout: 10 min)..."
if kubectl wait --for=condition=complete --timeout=600s "job/$JOB_NAME" -n "$NAMESPACE"; then
    echo "   ✅ Slicer job completed successfully"
else
    echo "   ❌ Slicer job failed or timed out"
    echo ""
    echo "   === INIT CONTAINER LOGS ==="
    kubectl logs "job/$JOB_NAME" -n "$NAMESPACE" -c fetch-stl 2>/dev/null || true
    echo ""
    echo "   === SLICER CONTAINER LOGS ==="
    kubectl logs "job/$JOB_NAME" -n "$NAMESPACE" -c slicer 2>/dev/null || true
    exit 1
fi
echo ""

# ── Step 4: Show slicer logs ─────────────────────────────────────────────
echo "4️⃣  Slicer logs:"
echo "   --- init (git clone) ---"
kubectl logs "job/$JOB_NAME" -n "$NAMESPACE" -c fetch-stl 2>/dev/null | sed 's/^/   /'
echo ""
echo "   --- slicer ---"
kubectl logs "job/$JOB_NAME" -n "$NAMESPACE" -c slicer 2>/dev/null | sed 's/^/   /'
echo ""

# ── Step 5: Pre-print checks ─────────────────────────────────────────────
echo "5️⃣  Running pre-print checks..."
echo ""

# Check printer reachable
if curl -s --connect-timeout 5 "$MOONRAKER/printer/info" > /dev/null 2>&1; then
    echo "   ✅ Printer reachable at $MOONRAKER"
else
    echo "   ❌ Printer not reachable at $MOONRAKER"
    echo "   Power on the QIDI Q2 and re-run this script, or start manually from Fluidd."
    exit 1
fi

# Check printer state
PRINTER_STATE=$(curl -s "$MOONRAKER/printer/info" | jq -r '.result.state // "unknown"')
echo "   Printer state: $PRINTER_STATE"
if [ "$PRINTER_STATE" != "ready" ]; then
    echo "   ⚠️  Printer is not ready (state: $PRINTER_STATE)"
    echo "   Wait for it to be ready before printing."
    exit 1
fi

# Check print state
PRINT_STATE=$(curl -s "$MOONRAKER/printer/objects/query?print_stats" | jq -r '.result.status.print_stats.state // "unknown"')
echo "   Print state: $PRINT_STATE"
if [ "$PRINT_STATE" != "standby" ]; then
    echo "   ⚠️  Printer is not on standby (state: $PRINT_STATE)"
    exit 1
fi

# Verify gcode file was uploaded
if curl -s "$MOONRAKER/server/files/metadata?filename=$GCODE_FILE" | jq -e '.result.filename' > /dev/null 2>&1; then
    EST_TIME=$(curl -s "$MOONRAKER/server/files/metadata?filename=$GCODE_FILE" | jq -r '.result.estimated_time // 0')
    EST_HOURS=$(echo "$EST_TIME / 3600" | bc -l 2>/dev/null | xargs printf "%.1f" 2>/dev/null || echo "?")
    echo "   ✅ Gcode file uploaded: $GCODE_FILE"
    echo "   ⏱️  Estimated print time: ${EST_HOURS}h"
else
    echo "   ❌ Gcode file not found on printer: $GCODE_FILE"
    exit 1
fi

# Check filament
bash "$REPO_DIR/scripts/pre-print-check.sh" "$GCODE_FILE" 2>/dev/null && PRE_CHECK_OK=true || PRE_CHECK_OK=false
echo ""

# ── Step 6: Start print ──────────────────────────────────────────────────
echo "6️⃣  Ready to print!"
echo ""
echo "   File: $GCODE_FILE"
echo "   Part: Top tray (flipped, ~17mm tall, no supports)"
echo "   Material: PLA+ (215°C nozzle, 60°C bed)"
echo ""
read -p "   Start print now? [y/N] " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   🚀 Starting print..."
    curl -s -X POST "$MOONRAKER/printer/print/start" \
        -H "Content-Type: application/json" \
        -d "{\"filename\": \"$GCODE_FILE\"}"
    echo ""
    echo "   ✅ Print started! Monitor at http://192.168.1.15/"
else
    echo "   Skipped. Start manually from Fluidd or run:"
    echo "   curl -X POST $MOONRAKER/printer/print/start -H 'Content-Type: application/json' -d '{\"filename\": \"$GCODE_FILE\"}'"
fi

echo ""
echo "Done! 🎉"
