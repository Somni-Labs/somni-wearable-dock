#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Re-slice Top Tray — slice only, no print
#
# Steps:
#   1. Delete any existing slicer job
#   2. Apply the slicer K8s Job (clones latest from GitHub, slices, validates,
#      uploads gcode to Moonraker)
#   3. Wait for completion
#   4. Show logs and validation results
#   5. Verify gcode is on the printer
# ============================================================================

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
NAMESPACE="utilities"
JOB_NAME="slice-top-tray"
JOB_MANIFEST="$REPO_DIR/k8s/slice-top-tray.yaml"
MOONRAKER="${MOONRAKER_URL:-http://192.168.1.15:7125}"
GCODE_FILE="v1-charging-stand-top-tray.gcode"

echo "╔══════════════════════════════════════════════════════╗"
echo "║  🔪 Re-slice Top Tray (with lid floor fix)          ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: Clean up old job ─────────────────────────────────────────────
echo "1️⃣  Cleaning up old slicer job..."
kubectl delete job "$JOB_NAME" -n "$NAMESPACE" 2>/dev/null \
    && echo "   Deleted old job" \
    || echo "   No old job to delete"
echo ""

# ── Step 2: Apply slicer job ─────────────────────────────────────────────
echo "2️⃣  Applying slicer job (clones latest from GitHub)..."
kubectl apply -f "$JOB_MANIFEST"
echo ""

# ── Step 3: Wait for completion ──────────────────────────────────────────
echo "3️⃣  Waiting for slicer job to complete (timeout: 10 min)..."
if kubectl wait --for=condition=complete --timeout=600s "job/$JOB_NAME" -n "$NAMESPACE"; then
    echo "   ✅ Slicer job completed successfully"
else
    echo "   ❌ Slicer job failed or timed out"
    echo ""
    echo "   === INIT CONTAINER LOGS (git clone) ==="
    kubectl logs "job/$JOB_NAME" -n "$NAMESPACE" -c fetch-stl 2>/dev/null || true
    echo ""
    echo "   === SLICER CONTAINER LOGS ==="
    kubectl logs "job/$JOB_NAME" -n "$NAMESPACE" -c slicer 2>/dev/null || true
    exit 1
fi
echo ""

# ── Step 4: Show logs ────────────────────────────────────────────────────
echo "4️⃣  Slicer output:"
echo ""
echo "   --- git clone ---"
kubectl logs "job/$JOB_NAME" -n "$NAMESPACE" -c fetch-stl 2>/dev/null | sed 's/^/   /'
echo ""
echo "   --- slice + validate + upload ---"
kubectl logs "job/$JOB_NAME" -n "$NAMESPACE" -c slicer 2>/dev/null | sed 's/^/   /'
echo ""

# ── Step 5: Verify gcode on printer ──────────────────────────────────────
echo "5️⃣  Verifying gcode on printer..."
if curl -s --connect-timeout 5 "$MOONRAKER/server/files/metadata?filename=$GCODE_FILE" \
    | jq -e '.result.filename' > /dev/null 2>&1; then
    EST_TIME=$(curl -s "$MOONRAKER/server/files/metadata?filename=$GCODE_FILE" \
        | jq -r '.result.estimated_time // 0')
    EST_HOURS=$(echo "scale=1; $EST_TIME / 3600" | bc 2>/dev/null || echo "?")
    LAYER_HEIGHT=$(curl -s "$MOONRAKER/server/files/metadata?filename=$GCODE_FILE" \
        | jq -r '.result.layer_height // "?"')
    FIRST_LAYER_BED=$(curl -s "$MOONRAKER/server/files/metadata?filename=$GCODE_FILE" \
        | jq -r '.result.first_layer_bed_temp // "?"')
    FIRST_LAYER_EXT=$(curl -s "$MOONRAKER/server/files/metadata?filename=$GCODE_FILE" \
        | jq -r '.result.first_layer_extr_temp // "?"')
    FILE_SIZE=$(curl -s "$MOONRAKER/server/files/metadata?filename=$GCODE_FILE" \
        | jq -r '.result.size // 0')
    FILE_SIZE_MB=$(echo "scale=1; $FILE_SIZE / 1048576" | bc 2>/dev/null || echo "?")

    echo "   ✅ Gcode uploaded: $GCODE_FILE"
    echo ""
    echo "   ┌─────────────────────────────────────┐"
    echo "   │  📋 Slice Summary                    │"
    echo "   ├─────────────────────────────────────┤"
    echo "   │  File size:      ${FILE_SIZE_MB} MB"
    echo "   │  Est. time:      ${EST_HOURS}h"
    echo "   │  Layer height:   ${LAYER_HEIGHT}mm"
    echo "   │  Bed temp:       ${FIRST_LAYER_BED}°C"
    echo "   │  Nozzle temp:    ${FIRST_LAYER_EXT}°C"
    echo "   │  Supports:       YES (auto)"
    echo "   │  Brim:           5mm"
    echo "   │  Part:           Top tray (flipped, with lid floor)"
    echo "   └─────────────────────────────────────┘"
else
    echo "   ❌ Gcode file not found on printer: $GCODE_FILE"
    echo "   The slicer logs above should show why the upload failed."
    exit 1
fi

echo ""
echo "✅ Slice complete. Gcode is on the printer."
echo ""
echo "   To print, run:"
echo "   curl -X POST $MOONRAKER/printer/print/start \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"filename\": \"$GCODE_FILE\"}'"
echo ""
