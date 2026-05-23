# Separate iPad Back Wall Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the iPad back wall from the top tray into a separate slide-in piece, reducing the top tray print height from ~77mm to ~17mm.

**Architecture:** Remove the `ipad_back` union from `build_top_tray()`, add a tongue-and-groove rail in its place, create a new `build_ipad_wall()` function that builds the wall as a standalone flat slab with a tongue tab, and update the export script and CLAUDE.md.

**Tech Stack:** CadQuery (Python), cadquery-server, PrusaSlicer, Moonraker

**Spec:** `docs/superpowers/specs/2026-05-23-separate-ipad-wall-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `designs/v1-charging-stand.py` | Modify | Add `IPAD_WALL_TOL` constant, remove wall union from `build_top_tray()`, add groove rail cut, add `build_ipad_wall()` function, add `show_object()` call, update `build_top_tray()` docstring |
| `export_charging_stand.py` | Modify | Add iPad wall STL/STEP export |
| `CLAUDE.md` | Modify | Update architecture (5 parts), add lesson learned |
| `tests/test_ipad_wall_dimensions.py` | Create | Dimensional tests for the iPad wall and groove geometry |

---

### Task 1: Add dimensional tests for iPad wall

**Files:**
- Create: `tests/test_ipad_wall_dimensions.py`

- [ ] **Step 1: Write the test file**

This test file uses the same `_load_constants()` pattern as `tests/test_ipad_slot_dimensions.py` — it parses constants from the design file without executing CadQuery.

```python
"""Tests for iPad wall separation — tongue-and-groove dimensions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "designs"))


def _load_constants():
    """Parse constant assignments from the design file without executing it."""
    design_path = Path(__file__).parent.parent / "designs" / "v1-charging-stand.py"
    src = design_path.read_text()
    constants = {}
    for line in src.splitlines():
        line = line.split("#")[0].strip()
        if "=" in line and not line.startswith(("def ", "class ", "import ", "from ")):
            lhs, _, rhs = line.partition("=")
            lhs = lhs.strip()
            rhs = rhs.strip()
            if lhs.isupper() or (lhs.replace("_", "").isupper() and "_" in lhs):
                try:
                    constants[lhs] = eval(rhs, {"__builtins__": {}}, constants)
                except Exception:
                    pass
    return constants


C = _load_constants()


class TestIpadWallTolerance:
    """IPAD_WALL_TOL must exist and be tighter than the global TOL."""

    def test_ipad_wall_tol_exists(self):
        assert "IPAD_WALL_TOL" in C, "IPAD_WALL_TOL constant not defined"

    def test_ipad_wall_tol_tighter_than_global(self):
        assert C["IPAD_WALL_TOL"] < C["TOL"], (
            f"IPAD_WALL_TOL={C['IPAD_WALL_TOL']} should be < TOL={C['TOL']}"
        )

    def test_ipad_wall_tol_in_range(self):
        """Should be 0.2-0.6mm — tight enough to hold, loose enough to slide."""
        assert 0.2 <= C["IPAD_WALL_TOL"] <= 0.6, (
            f"IPAD_WALL_TOL={C['IPAD_WALL_TOL']} outside sane range [0.2, 0.6]"
        )


class TestIpadWallGrooveDimensions:
    """Groove in top tray must accommodate the wall tongue."""

    def test_groove_depth_positive(self):
        """Groove depth (3mm) must be positive and reasonable."""
        groove_depth = 3  # hardcoded in spec
        assert groove_depth > 0
        assert groove_depth <= C.get("IPAD_BACK_THICK", 4), (
            "Groove deeper than wall thickness makes no sense"
        )

    def test_tongue_fits_in_groove(self):
        """Tongue (3mm - TOL) must be smaller than groove (3mm)."""
        groove = 3
        tongue = groove - C["IPAD_WALL_TOL"]
        assert tongue < groove, "Tongue must be smaller than groove"
        assert tongue > 0, "Tongue dimension must be positive"

    def test_clearance_per_side(self):
        """Clearance per side should be IPAD_WALL_TOL / 2 = 0.2mm."""
        clearance = C["IPAD_WALL_TOL"] / 2
        assert 0.1 <= clearance <= 0.4, (
            f"Clearance per side {clearance}mm outside sane range"
        )


class TestIpadWallDimensions:
    """Wall body dimensions must match existing constants."""

    def test_wall_width_matches_slot(self):
        """Wall width should be IPAD_SLOT_W + 10."""
        expected_width = C["IPAD_SLOT_W"] + 10
        assert expected_width <= C["STAND_W"], (
            f"Wall width {expected_width}mm exceeds stand width {C['STAND_W']}mm"
        )

    def test_wall_height_is_ipad_back_h(self):
        """Wall height must equal IPAD_BACK_H (60mm)."""
        assert C["IPAD_BACK_H"] == 60, (
            f"IPAD_BACK_H={C['IPAD_BACK_H']}, expected 60"
        )

    def test_wall_thickness_is_ipad_back_thick(self):
        """Wall thickness must equal IPAD_BACK_THICK (4mm)."""
        assert C["IPAD_BACK_THICK"] == 4, (
            f"IPAD_BACK_THICK={C['IPAD_BACK_THICK']}, expected 4"
        )

    def test_front_lip_remains(self):
        """IPAD_LIP_H must still be defined (front lip stays on top tray)."""
        assert "IPAD_LIP_H" in C, "IPAD_LIP_H not found — front lip must remain"
        assert C["IPAD_LIP_H"] > 0, "IPAD_LIP_H must be positive"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python -m pytest tests/test_ipad_wall_dimensions.py -v`

Expected: `TestIpadWallTolerance::test_ipad_wall_tol_exists` FAILS with `AssertionError: IPAD_WALL_TOL constant not defined`. Other tests that depend on `IPAD_WALL_TOL` also fail. Tests that only check existing constants (`IPAD_BACK_H`, `IPAD_BACK_THICK`, `IPAD_LIP_H`) should PASS.

- [ ] **Step 3: Commit test file**

```bash
git add tests/test_ipad_wall_dimensions.py
git commit -m "test: add dimensional tests for separate iPad wall"
```

---

### Task 2: Add `IPAD_WALL_TOL` constant and remove wall from top tray

**Files:**
- Modify: `designs/v1-charging-stand.py`

- [ ] **Step 1: Add `IPAD_WALL_TOL` constant**

Add after the `IPAD_LIP_H` constant (line ~264 in the constants section, near the other iPad constants):

```python
IPAD_WALL_TOL = 0.4        # tongue-and-groove tolerance (tighter than global TOL for snug slide fit)
```

- [ ] **Step 2: Run the tolerance tests to verify they pass**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python -m pytest tests/test_ipad_wall_dimensions.py::TestIpadWallTolerance -v`

Expected: All 3 tests PASS.

- [ ] **Step 3: Remove the `ipad_back` union from `build_top_tray()`**

In `build_top_tray()`, find and **delete** the iPad back wall block (the block that builds and unions the 60mm tall wall). This is approximately lines 1524-1532 in the design file on the cadquery-server. The code to remove:

```python
    # ── Back wall — the iPad leans against this ──────────────────────
    ipad_back = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H)
        .center(0, STAND_D / 2 - IPAD_BACK_THICK / 2)
        .rect(IPAD_SLOT_W + 10, IPAD_BACK_THICK)
        .extrude(IPAD_BACK_H)
    )
    base = base.union(ipad_back)
```

Replace with:

```python
    # ── iPad back wall groove — wall slides in as separate part ──────
    # Groove cut into the top surface at the rear edge. The separate
    # iPad wall's tongue tab slides into this groove from either side.
    # Cut AFTER the edge fillets so groove edges stay sharp.
    _groove_depth = 3      # groove depth into surface (Y)
    _groove_h = 3          # groove height (Z, cut down from top)
    _groove_w = IPAD_SLOT_W + 10 + 2  # wall width + exits both sides
    _groove_y = STAND_D / 2 - IPAD_BACK_THICK / 2  # same Y as old wall
    ipad_wall_groove = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H - _groove_h)
        .center(0, _groove_y)
        .rect(_groove_w, _groove_depth)
        .extrude(_groove_h + 0.5)
    )
    base = base.cut(ipad_wall_groove)
```

- [ ] **Step 4: Verify the front lip code is still present**

Confirm these lines are still in `build_top_tray()` (they should be immediately below where the wall union was, now immediately below the groove cut):

```python
    # ── Front lip — prevents iPad sliding forward ────────────────────
    ipad_lip = (
        cq.Workplane("XY")
        .workplane(offset=STAND_H)
        .center(0, ipad_y - IPAD_SLOT_GAP / 2 - IPAD_BACK_THICK / 2)
        .rect(IPAD_SLOT_W - 10, IPAD_BACK_THICK)
        .extrude(IPAD_LIP_H)
    )
    base = base.union(ipad_lip)
```

- [ ] **Step 5: Run all dimension tests**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python -m pytest tests/test_ipad_wall_dimensions.py -v`

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: remove iPad back wall from top tray, add tongue groove rail"
```

---

### Task 3: Add `build_ipad_wall()` function

**Files:**
- Modify: `designs/v1-charging-stand.py`

- [ ] **Step 1: Add `build_ipad_wall()` function**

Add this function after `build_ipad_cover()` and before `build_mudra_pole()`:

```python
# =============================================================================
# BUILD IPAD WALL (separate slide-in part)
# =============================================================================

def build_ipad_wall():
    """iPad back wall — separate slide-in piece with tongue tab.

    The iPad leans against this wall. It slides into a groove on the
    top tray's rear edge from either side. Prints flat on its back
    (245mm x 60mm face on build plate, only 4mm tall).

    Built at origin: centered on X, Z=0 at the bottom edge.
    The tongue tab extends in +Y from the wall's back face.
    """
    _wall_w = IPAD_SLOT_W + 10     # 245mm — same as the old union wall
    _wall_h = IPAD_BACK_H          # 60mm
    _wall_t = IPAD_BACK_THICK      # 4mm

    # ── Wall body ────────────────────────────────────────────────────
    wall = (
        cq.Workplane("XY")
        .rect(_wall_w, _wall_t)
        .extrude(_wall_h)
    )

    # ── Tongue tab on the bottom edge ────────────────────────────────
    # Extends from the back face (+Y) of the wall, runs full width.
    # Sized to slide into the groove on the top tray with IPAD_WALL_TOL
    # clearance per side.
    _tongue_depth = 3 - IPAD_WALL_TOL   # 2.6mm (into groove)
    _tongue_h = 3 - IPAD_WALL_TOL       # 2.6mm (groove height minus clearance)
    tongue = (
        cq.Workplane("XY")
        .workplane(offset=0)
        .center(0, _wall_t / 2 + _tongue_depth / 2)
        .rect(_wall_w - IPAD_WALL_TOL * 2, _tongue_depth)
        .extrude(_tongue_h)
    )
    wall = wall.union(tongue)

    return wall
```

- [ ] **Step 2: Add `show_object()` call for the iPad wall**

At the bottom of the file, after the existing `show_object(ipad_cover, ...)` call and before the Mudra pole section, add:

```python
ipad_wall = build_ipad_wall()

# iPad wall displayed at assembly position (inserted into rear groove)
_ipad_wall_y = STAND_D / 2 - IPAD_BACK_THICK / 2
ipad_wall_assembly = ipad_wall.translate((0, _ipad_wall_y, STAND_H))
show_object(ipad_wall_assembly,
            name="ipad_wall",
            options={"color": (0.28, 0.28, 0.30, 0.95)})
```

Also update the bare `ipad_wall = build_ipad_wall()` to be available at the module level (near `bottom_tray`, `top_tray`, `ipad_cover`, `mudra_pole`). The `ipad_wall` variable must be accessible to the export script via `exec_globals`.

Find the build section:

```python
bottom_tray = build_bottom_tray()
top_tray = build_top_tray()
ipad_cover = build_ipad_cover()
mudra_pole = build_mudra_pole()
```

Change to:

```python
bottom_tray = build_bottom_tray()
top_tray = build_top_tray()
ipad_cover = build_ipad_cover()
ipad_wall = build_ipad_wall()
mudra_pole = build_mudra_pole()
```

Then update the `show_object` section — replace the assembly/show block added above with just the assembly+show (since `ipad_wall` is already built):

```python
# iPad wall displayed at assembly position (inserted into rear groove)
_ipad_wall_y = STAND_D / 2 - IPAD_BACK_THICK / 2
ipad_wall_assembly = ipad_wall.translate((0, _ipad_wall_y, STAND_H))
show_object(ipad_wall_assembly,
            name="ipad_wall",
            options={"color": (0.28, 0.28, 0.30, 0.95)})
```

- [ ] **Step 3: Update `build_top_tray()` docstring**

Change:

```python
def build_top_tray():
    """Top tray: device pockets, Mudra pole socket, iPad wall. Sits on bottom tray."""
```

To:

```python
def build_top_tray():
    """Top tray: device pockets, Mudra pole socket, iPad groove. Sits on bottom tray."""
```

- [ ] **Step 4: Verify the design builds successfully**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python -c "exec(open('designs/v1-charging-stand.py').read().replace('from cq_server.ui import ui, show_object', 'show_object = lambda *a, **k: None'))"`

Expected: No errors. If CadQuery is not installed locally, verify via the cadquery-server pod:

Run: `kubectl -n utilities exec cadquery-server-fcd55c7bd-qq5hw -- python3 -c "import sys; sys.path.insert(0,'/projects/somni-wearable-dock'); exec(open('/projects/somni-wearable-dock/designs/v1-charging-stand.py').read())"`

Note: This will only work after pushing to GitHub and restarting the cadquery-server pod. For local verification, run the export script instead (Task 4).

- [ ] **Step 5: Commit**

```bash
git add designs/v1-charging-stand.py
git commit -m "feat: add build_ipad_wall() and show_object for cadquery-server preview"
```

---

### Task 4: Update export script

**Files:**
- Modify: `export_charging_stand.py`

- [ ] **Step 1: Add iPad wall to the exec_globals extraction**

In `export_stl_files()`, after the line that extracts `ipad_cover`:

```python
        ipad_cover = exec_globals.get('ipad_cover')
```

Add:

```python
        ipad_wall = exec_globals.get('ipad_wall')
```

- [ ] **Step 2: Add iPad wall print preparation**

After the `if ipad_cover:` block that creates `cover_print`, add:

```python
    # iPad wall — prints flat on its back, no rotation needed.
    # The wide face (245mm x 60mm) sits on the build plate, 4mm tall.
    if ipad_wall:
        wall_bb = ipad_wall.val().BoundingBox()
        wall_print = ipad_wall.translate((0, 0, -wall_bb.zmin))
        print(f"   iPad wall: translated Z by {-wall_bb.zmin:+.1f}mm (was Z={wall_bb.zmin:.1f})")
```

- [ ] **Step 3: Add iPad wall STL/STEP export**

After the iPad cover export block (`if ipad_cover: ... cover_step_path`), add:

```python
        # iPad back wall — slide-in piece
        if ipad_wall:
            wall_stl_path = output_dir / "v1-charging-stand-ipad-wall.stl"
            cq.exporters.export(wall_print, str(wall_stl_path))
            print(f"✅ {wall_stl_path} - iPad back wall (slide-in)")

            wall_step_path = output_dir / "v1-charging-stand-ipad-wall.step"
            cq.exporters.export(ipad_wall, str(wall_step_path))
            print(f"✅ {wall_step_path} - iPad wall STEP (assembly position)")
```

- [ ] **Step 4: Update `print_print_info()` to mention 5 parts**

In the `print_print_info()` function, update the supports line:

```python
    print(f"   Supports: Top tray and mudra pole need NO supports (pole prints upright)")
```

Change to:

```python
    print(f"   Supports: Top tray, mudra pole, and iPad wall need NO supports")
```

- [ ] **Step 5: Run the export script to verify everything builds**

Run: `cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && python3 export_charging_stand.py`

Expected: All STL/STEP files exported successfully, including the new:
- `output/v1-charging-stand-ipad-wall.stl`
- `output/v1-charging-stand-ipad-wall.step`

- [ ] **Step 6: Commit**

```bash
git add export_charging_stand.py
git commit -m "feat: add iPad wall to STL/STEP export pipeline"
```

---

### Task 5: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update architecture line**

Change the first architecture bullet:

```markdown
- **`designs/v1-charging-stand.py`** — Main CadQuery parametric design (4 parts: bottom tray, top tray, mudra pole, iPad cover plate)
```

To:

```markdown
- **`designs/v1-charging-stand.py`** — Main CadQuery parametric design (5 parts: bottom tray, top tray, mudra pole, iPad cover plate, iPad back wall)
```

- [ ] **Step 2: Add lesson learned**

Add a new subsection at the end of the "Lessons Learned" section:

```markdown
### Tall vertical walls should be separate parts printed flat

The iPad back wall (60mm tall, 4mm thick, 245mm wide) was originally unioned onto the top tray. When the top tray is flipped for printing, the wall becomes the tallest feature (~77mm total), adding hours of print time for a simple flat slab. Separating the wall into a slide-in tongue-and-groove piece lets it print flat on its back (4mm tall, ~15 minutes) and cuts the top tray print from ~77mm to ~17mm.

**Rule of thumb:** If a feature adds significant height to a flipped print but is geometrically simple (flat wall, shelf, bracket), make it a separate part that prints in its natural orientation.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update architecture to 5 parts, add lesson on tall wall separation"
```

---

### Task 6: Push and verify cadquery-server preview

- [ ] **Step 1: Push to GitHub**

```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-wearable-dock && git push
```

- [ ] **Step 2: Restart cadquery-server to trigger git-sync**

```bash
kubectl rollout restart deployment cadquery-server -n utilities
```

- [ ] **Step 3: Wait for pod to be ready**

```bash
kubectl -n utilities rollout status deployment cadquery-server --timeout=120s
```

- [ ] **Step 4: Verify the design renders**

Check that the cadquery-server pod starts successfully and the design file loads without errors:

```bash
kubectl -n utilities logs deployment/cadquery-server --tail=20
```

Expected: No Python errors. The server should load `v1-charging-stand.py` and render all objects including the new `ipad_wall`.
