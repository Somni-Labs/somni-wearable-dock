# Separate Mudra Pole Insert — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separate the Mudra L-pole from the top tray into its own snap-in part, eliminating 20+ hours of support material print time.

**Architecture:** The Mudra pole becomes a standalone CadQuery part (`build_mudra_pole()`) with cantilever snap clips on its base. The top tray gets a rectangular through-socket with snap engagement pockets where the pole used to be built inline. Cable routing is inherently continuous because the socket is a through-hole aligned with the existing `mudra_cable` floor cut.

**Tech Stack:** CadQuery (Python), PrusaSlicer CLI, K8s Job YAML, Moonraker API

---

### Task 1: Add `build_mudra_pole()` function to the design file

**Files:**
- Modify: `designs/v1-charging-stand.py` (add new function after `build_ipad_cover()`, before the BUILD AND DISPLAY section — around line 1120)

The new function builds the Mudra L-pole as a standalone part at the origin, with snap clip tabs extending downward from the base.

- [ ] **Step 1: Add `build_mudra_pole()` function**

Insert the following function after the `build_ipad_cover()` function (after line 1119) and before the `# BUILD AND DISPLAY` section (line 1122):

```python
# =============================================================================
# BUILD MUDRA POLE (separate snap-in part)
# =============================================================================

def build_mudra_pole():
    """Mudra Link L-pole with flush charger pocket and snap-clip base.

    Standalone part that inserts into a socket on the top tray.
    Printed upright — no supports needed.

    Geometry (unchanged from original inline design):
      - Vertical post: MUDRA_POLE_D x MUDRA_POLE_W x MUDRA_POLE_H
      - Horizontal shelf at top: MUDRA_SHELF_L x MUDRA_POLE_W x MUDRA_SHELF_H
      - Flush charger pocket in shelf top (open from above, chamfered lip)
      - Internal cable channel: vertical cavity + horizontal slot to charger bay
      - Cable exits through the open bottom face of the pole base

    New: snap clip tabs on the base that catch the underside of the top tray.
    """

    # ── Vertical post at origin ──────────────────────────────────────────
    post = (
        cq.Workplane("XY")
        .rect(MUDRA_POLE_D, MUDRA_POLE_W)
        .extrude(MUDRA_POLE_H)
    )

    # ── Horizontal shelf extending right (+X) from top of post ───────────
    shelf = (
        cq.Workplane("XY")
        .workplane(offset=MUDRA_POLE_H - MUDRA_SHELF_H)
        .center(MUDRA_POLE_D / 2 + MUDRA_SHELF_L / 2, 0)
        .rect(MUDRA_SHELF_L, MUDRA_POLE_W)
        .extrude(MUDRA_SHELF_H)
    )

    pole = post.union(shelf)

    # ── Charger bay — flush pocket cut from shelf top ────────────────────
    charger_bay_x = MUDRA_POLE_D / 2 + MUDRA_SHELF_L / 2
    shelf_top_z = MUDRA_POLE_H

    charger_bay = (
        cq.Workplane("XY")
        .workplane(offset=shelf_top_z - MUDRA_CHARGER_H)
        .center(charger_bay_x, 0)
        .rect(MUDRA_CHARGER_D, MUDRA_CHARGER_W)
        .extrude(MUDRA_CHARGER_H + 1)
    )
    pole = pole.cut(charger_bay)

    # ── Chamfered lip around charger pocket opening ──────────────────────
    chamfer_lip = (
        cq.Workplane("XY")
        .workplane(offset=shelf_top_z + 0.1)
        .center(charger_bay_x, 0)
        .rect(MUDRA_CHARGER_D + 4, MUDRA_CHARGER_W + 4)
        .workplane(offset=-2.0)
        .center(charger_bay_x, 0)
        .rect(MUDRA_CHARGER_D, MUDRA_CHARGER_W)
        .loft()
    )
    pole = pole.cut(chamfer_lip)

    # ── Cable channel — horizontal slot from charger bay to post ─────────
    cable_slot_z = shelf_top_z - MUDRA_CHARGER_H
    slot_length = charger_bay_x - MUDRA_CHARGER_D / 2
    cable_horiz = (
        cq.Workplane("XY")
        .workplane(offset=cable_slot_z)
        .center(slot_length / 2, 0)
        .rect(slot_length + 2, MUDRA_CABLE_CH_W)
        .extrude(MUDRA_CABLE_CH_W)
    )
    pole = pole.cut(cable_horiz)

    # ── Vertical cable cavity through the post ───────────────────────────
    cable_cavity_vert = (
        cq.Workplane("XY")
        .rect(MUDRA_CABLE_CH_D, MUDRA_CABLE_CH_W)
        .extrude(cable_slot_z + MUDRA_CABLE_CH_W + 1)
    )
    pole = pole.cut(cable_cavity_vert)

    # ── Snap clip tabs on the base ───────────────────────────────────────
    # Two cantilever hooks, one on each long side (the MUDRA_POLE_D / X-axis
    # faces). They extend downward from the pole base into negative Z.
    # When inserting the pole into the socket, the hooks flex inward, pass
    # through the socket, and snap out to catch the bottom face of the top tray.
    for side_sign in [-1, 1]:
        clip_x = side_sign * (MUDRA_POLE_D / 2 + SNAP_HOOK / 2)

        # Cantilever arm extending downward from pole base
        arm = (
            cq.Workplane("XY")
            .workplane(offset=-SNAP_CLIP_H)
            .center(clip_x, 0)
            .rect(SNAP_HOOK, SNAP_CLIP_W)
            .extrude(SNAP_CLIP_H)
        )
        pole = pole.union(arm)

        # Hook nub at the bottom of the arm (outward-facing)
        # Catches the underside of the top tray floor
        nub_x = clip_x + side_sign * (SNAP_HOOK / 2)
        nub = (
            cq.Workplane("XY")
            .workplane(offset=-SNAP_CLIP_H)
            .center(nub_x, 0)
            .rect(SNAP_HOOK, SNAP_CLIP_W)
            .extrude(SNAP_HOOK)
        )
        pole = pole.union(nub)

    return pole
```

- [ ] **Step 2: Verify syntax by running the export script**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 -c "exec(open('designs/v1-charging-stand.py').read().replace('from cq_server.ui import ui, show_object', '# removed').replace('show_object', '# show_object'))"`

Expected: No syntax errors. The function is defined but not yet called — this just verifies it parses cleanly alongside the rest of the file.

- [ ] **Step 3: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add build_mudra_pole() function for standalone snap-in pole

Standalone L-pole part with charger pocket, cable channels, and
cantilever snap clips on the base. Prints upright with no supports.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 2: Replace inline pole with socket cut in `build_top_tray()`

**Files:**
- Modify: `designs/v1-charging-stand.py` — lines 752–878 of `build_top_tray()`

Remove the entire inline pole construction and replace it with a rectangular through-socket and snap engagement pockets.

- [ ] **Step 1: Remove the inline pole construction (lines 763–878)**

Delete the following code block in `build_top_tray()` — everything from `# Build L-pole at ORIGIN` (line 763) through the last `base = base.cut(mudra_horiz_channel)` (line 878). 

**Keep these lines** (they stay — they're the cable pass-through and position variables):
```python
    mx, my = SLOT_POSITIONS["mudra"]

    # Cable pass-through in the base (rectangular, matching cavity)
    mudra_cable = (
        cq.Workplane("XY")
        .center(mx, my)
        .rect(MUDRA_CABLE_CH_D, MUDRA_CABLE_CH_W)
        .extrude(STAND_H)
    )
    base = base.cut(mudra_cable)
```

**Remove** everything from line 763 (`# Build L-pole at ORIGIN, then translate.`) through line 878 (`base = base.cut(mudra_horiz_channel)`). That's the post, shelf, union, charger bay, chamfer lip, cable channels (local), pole translate, base union, and cable channels (world coordinate re-cuts).

- [ ] **Step 2: Add the socket cut in place of the removed code**

After the `base = base.cut(mudra_cable)` line (which stays), add:

```python
    # ── Mudra pole socket — through-hole for snap-in pole insert ─────────
    # Rectangular through-hole where the standalone pole drops in from above.
    # The socket is slightly oversized (SNAP_TOL per side) for easy insertion.
    _socket_w = MUDRA_POLE_D + SNAP_TOL * 2   # 20.6mm in X
    _socket_d = MUDRA_POLE_W + SNAP_TOL * 2   # 22.6mm in Y
    mudra_socket = (
        cq.Workplane("XY")
        .workplane(offset=SPLIT_Z - 0.5)
        .center(mx, my)
        .rect(_socket_w, _socket_d)
        .extrude(TOP_H + 1)
    )
    base = base.cut(mudra_socket)

    # ── Snap hook engagement pockets on the bottom face ──────────────────
    # Small recesses on the bottom face of the top tray around the socket,
    # one on each X-axis face. These give the snap hooks room to spring
    # out and catch after passing through the socket.
    _pocket_w = SNAP_CLIP_W + SNAP_TOL * 2    # 12.6mm
    _pocket_depth = SNAP_HOOK                  # 1.2mm into tray bottom face
    _pocket_h = SNAP_HOOK * 2                  # 2.4mm
    for side_sign in [-1, 1]:
        pocket_x = mx + side_sign * (_socket_w / 2 + _pocket_depth / 2)
        snap_pocket = (
            cq.Workplane("XY")
            .workplane(offset=SPLIT_Z - _pocket_h)
            .center(pocket_x, my)
            .rect(_pocket_depth, _pocket_w)
            .extrude(_pocket_h + 0.5)
        )
        base = base.cut(snap_pocket)
```

- [ ] **Step 3: Verify the build succeeds**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py`

Expected: Build succeeds, 3 STL files exported. The top tray should now have a rectangular hole where the pole used to be.

- [ ] **Step 4: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "refactor: replace inline Mudra pole with socket cut in top tray

Remove ~115 lines of pole construction from build_top_tray() and replace
with a through-socket + snap engagement pockets. The pole is now a
separate snap-in part (build_mudra_pole). Eliminates support material.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 3: Wire up `build_mudra_pole()` in BUILD AND DISPLAY section

**Files:**
- Modify: `designs/v1-charging-stand.py` — BUILD AND DISPLAY section (around line 1122)

Add the mudra pole to the build calls and `show_object()` display.

- [ ] **Step 1: Add mudra pole build and show_object call**

In the BUILD AND DISPLAY section, change:

```python
bottom_tray = build_bottom_tray()
top_tray = build_top_tray()
ipad_cover = build_ipad_cover()

show_object(bottom_tray, name="bottom_tray",
            options={"color": (0.15, 0.15, 0.17, 0.9)})
show_object(top_tray, name="top_tray",
            options={"color": (0.2, 0.2, 0.22, 0.95)})
show_object(ipad_cover, name="ipad_cover",
            options={"color": (0.3, 0.3, 0.32, 0.9)})
```

To:

```python
bottom_tray = build_bottom_tray()
top_tray = build_top_tray()
ipad_cover = build_ipad_cover()
mudra_pole = build_mudra_pole()

show_object(bottom_tray, name="bottom_tray",
            options={"color": (0.15, 0.15, 0.17, 0.9)})
show_object(top_tray, name="top_tray",
            options={"color": (0.2, 0.2, 0.22, 0.95)})
show_object(ipad_cover, name="ipad_cover",
            options={"color": (0.3, 0.3, 0.32, 0.9)})

# Mudra pole displayed at its assembly position (inserted into the top tray socket)
mx, my = SLOT_POSITIONS["mudra"]
show_object(mudra_pole.translate((mx, my, STAND_H)),
            name="mudra_pole",
            options={"color": (0.25, 0.25, 0.27, 0.95)})
```

- [ ] **Step 2: Verify full build succeeds**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py`

Expected: Build succeeds. Still only 3 STL exports (mudra pole export added in next task).

- [ ] **Step 3: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: wire up mudra pole in build and cadquery-server preview

Build the standalone mudra pole and show it at its assembly position
in the cadquery-server browser preview.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 4: Add mudra pole export to `export_charging_stand.py`

**Files:**
- Modify: `export_charging_stand.py`

Add the 4th export: mudra pole STL (no rotation — prints upright) and STEP (assembly position).

- [ ] **Step 1: Add mudra pole to the exec_globals extraction**

In `export_stl_files()`, after the line:
```python
        ipad_cover = exec_globals.get('ipad_cover')
```

Add:
```python
        mudra_pole = exec_globals.get('mudra_pole')
```

- [ ] **Step 2: Add mudra pole Z=0 translation**

After the iPad cover Z=0 translation block:
```python
    # iPad cover plate — translate to Z=0 for printing
    if ipad_cover:
        cover_bb = ipad_cover.val().BoundingBox()
        cover_print = ipad_cover.translate((0, 0, -cover_bb.zmin))
```

Add:
```python
    # Mudra pole — translate to Z=0 for printing (no rotation, prints upright)
    if mudra_pole:
        pole_bb = mudra_pole.val().BoundingBox()
        pole_print = mudra_pole.translate((0, 0, -pole_bb.zmin))
```

- [ ] **Step 3: Add mudra pole print info line**

After:
```python
    if ipad_cover:
        print(f"   iPad cover: translated Z by {-cover_bb.zmin:+.1f}mm (was Z={cover_bb.zmin:.1f})")
```

Add:
```python
    if mudra_pole:
        print(f"   Mudra pole: translated Z by {-pole_bb.zmin:+.1f}mm (was Z={pole_bb.zmin:.1f})")
```

- [ ] **Step 4: Add mudra pole STL and STEP export**

After the iPad cover export block (after `print(f"... iPad cover STEP ...")`), add:

```python
        # Mudra pole — snap-in part (no rotation, prints upright)
        if mudra_pole:
            pole_stl_path = output_dir / "v1-charging-stand-mudra-pole.stl"
            cq.exporters.export(pole_print, str(pole_stl_path))
            print(f"✅ {pole_stl_path} - Mudra pole (snap-in, prints upright)")

            pole_step_path = output_dir / "v1-charging-stand-mudra-pole.step"
            cq.exporters.export(mudra_pole, str(pole_step_path))
            print(f"✅ {pole_step_path} - Mudra pole STEP (origin position)")
```

- [ ] **Step 5: Update `print_print_info()` to mention 4 parts**

In the `print_print_info()` function, change:
```python
    print(f"   Supports: Likely needed for Mudra pole overhang")
```
To:
```python
    print(f"   Supports: Top tray and mudra pole need NO supports (pole prints upright)")
```

And change:
```python
    print(f"   Print orientation: Bottom tray down, top tray upside down")
```
To:
```python
    print(f"   Print orientation: Bottom tray down, top tray upside down, mudra pole upright")
```

- [ ] **Step 6: Verify the full export runs successfully**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py`

Expected: 4 STL files and 4 STEP files in `output/`:
- `v1-charging-stand-bottom-tray.stl` / `.step`
- `v1-charging-stand-top-tray.stl` / `.step`
- `v1-charging-stand-ipad-cover.stl` / `.step`
- `v1-charging-stand-mudra-pole.stl` / `.step`

- [ ] **Step 7: Commit**

```bash
git add export_charging_stand.py
git commit -m "feat: export mudra pole as 4th STL/STEP part

No rotation needed — pole prints upright with no supports.
Assembly now has 4 printable parts.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 5: Add 4th slice+validate+upload section to slicer K8s Job

**Files:**
- Modify: `k8s/slice-all-parts.yaml`

Add mudra pole slicing with no `--require-supports` flag, plus a 4th ConfigMap volume.

- [ ] **Step 1: Update the header comment**

Change:
```
echo "=== PrusaSlicer — All 3 Parts (with gcode validation) ==="
```
To:
```
echo "=== PrusaSlicer — All 4 Parts (with gcode validation) ==="
```

- [ ] **Step 2: Remove `--require-supports` from the top tray validation**

The top tray no longer has the Mudra pole overhang, so it no longer needs support material. Change:

```bash
          validate_gcode /tmp/top.gcode --require-supports
```
To:
```bash
          validate_gcode /tmp/top.gcode
```

- [ ] **Step 3: Add the mudra pole slice+validate+upload section**

After the iPad cover section (after the `echo ""` that follows the iPad cover upload), add:

```bash
          # ── MUDRA POLE ──
          echo "--- Slicing mudra pole ---"
          $SLICER --load "$INI" --center 137,147 \
            --output /tmp/pole.gcode --export-gcode /tmp/input-pole/mudra-pole.stl
          validate_gcode /tmp/pole.gcode
          echo "--- Uploading mudra pole ---"
          curl -s -X DELETE "$MOONRAKER/server/files/gcodes/v1-charging-stand-mudra-pole.gcode" || true
          sleep 2
          curl -s -X POST "$MOONRAKER/server/files/upload" \
            -F "file=@/tmp/pole.gcode;filename=v1-charging-stand-mudra-pole.gcode" \
            -F "root=gcodes"
          echo ""
```

- [ ] **Step 4: Add the 4th volume mount**

In the `volumeMounts` section, after:
```yaml
        - name: input-cover
          mountPath: /tmp/input-cover
```

Add:
```yaml
        - name: input-pole
          mountPath: /tmp/input-pole
```

- [ ] **Step 5: Add the 4th volume definition**

In the `volumes` section, after:
```yaml
      - name: input-cover
        configMap:
          name: slicer-stl-input-ipad-cover
```

Add:
```yaml
      - name: input-pole
        configMap:
          name: slicer-stl-input-mudra-pole
```

- [ ] **Step 6: Commit**

```bash
git add k8s/slice-all-parts.yaml
git commit -m "feat: add mudra pole to slicer job (4th part, no supports)

Top tray no longer requires supports either since the pole is separate.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 6: Update `CLAUDE.md` to document 4-part assembly

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the Architecture section**

Change:
```markdown
- **`designs/v1-charging-stand.py`** — Main CadQuery parametric design (3 parts: bottom tray, top tray, iPad cover plate)
```
To:
```markdown
- **`designs/v1-charging-stand.py`** — Main CadQuery parametric design (4 parts: bottom tray, top tray, mudra pole, iPad cover plate)
```

- [ ] **Step 2: Update the design file docstring**

In `designs/v1-charging-stand.py`, update the module docstring (line 1) to mention 4 parts. Change:
```
  4. Mudra Link            — wristband DRAPES over L-pole shelf, cable exits tip
```
To:
```
  4. Mudra Link            — wristband DRAPES over separate snap-in L-pole shelf
```

And update the `build_top_tray()` docstring (line 549) from:
```python
    """Top tray: device pockets, Mudra pole, iPad wall. Sits on bottom tray."""
```
To:
```python
    """Top tray: device pockets, Mudra pole socket, iPad wall. Sits on bottom tray."""
```

- [ ] **Step 3: Add separate Mudra pole to Lessons Learned**

After the "Multi-part assemblies need separate STL exports" lesson, add:

```markdown
### Separate parts eliminate support material waste

The Mudra L-pole overhang required 48% of the top tray's filament for support material (110m, 20+ extra hours). Separating the pole into its own snap-in part eliminates supports entirely — the pole prints upright and the top tray has a simple through-socket. Assembly: 4 parts (bottom tray, top tray, mudra pole, iPad cover plate).
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md designs/v1-charging-stand.py
git commit -m "docs: document 4-part assembly and separate pole design rationale

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 7: Full build verification, push, and cadquery-server preview

**Files:**
- No new changes — this is a verification and deployment task

- [ ] **Step 1: Run full export to verify all 4 parts build**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py`

Expected output includes:
- `v1-charging-stand-bottom-tray.stl`
- `v1-charging-stand-top-tray.stl`
- `v1-charging-stand-ipad-cover.stl`
- `v1-charging-stand-mudra-pole.stl`
- Plus 4 matching STEP files

- [ ] **Step 2: Verify output files exist and have reasonable sizes**

Run: `ls -lh output/*.stl output/*.step`

Expected: 8 files. Mudra pole STL should be small (~50-200 KB). Top tray STL should be smaller than before (no pole geometry).

- [ ] **Step 3: Push to GitHub**

Run: `git push origin main`

- [ ] **Step 4: Restart cadquery-server for visual preview**

Run: `kubectl rollout restart deployment cadquery-server -n utilities`

Wait for git-sync to pull the latest commit, then check the browser preview. The mudra pole should appear as a separate highlighted part at its assembly position on the top tray.

- [ ] **Step 5: Verify preview in browser**

Check the cadquery-server preview. Confirm:
- Top tray has a rectangular socket hole (no pole)
- Mudra pole is visible as a separate part at the correct position
- Snap clips visible on the pole base
- All other parts unchanged
