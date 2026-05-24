"""Tests for iPad slot dimensions — portrait 13" iPad Pro/Air."""

import sys
from pathlib import Path

# Load constants without executing cadquery/show_object code
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

IPAD_WIDTH_BARE = 213   # mm — measured short dimension (portrait width)
IPAD_HEIGHT_BARE = 267  # mm — measured tall dimension (portrait height)
STAND_W = C["STAND_W"]  # 240mm


class TestIpadSlotPortraitOrientation:
    """iPad slot must match portrait 13" iPad Pro/Air."""

    def test_slot_width_fits_portrait_ipad_with_tolerance(self):
        """IPAD_SLOT_W must be >= iPad portrait width (213mm) + at least 1mm tolerance."""
        assert C["IPAD_SLOT_W"] >= IPAD_WIDTH_BARE + 1, (
            f"IPAD_SLOT_W={C['IPAD_SLOT_W']} too narrow for 213mm iPad + tolerance"
        )

    def test_slot_width_fits_within_stand(self):
        """IPAD_SLOT_W must leave at least 5mm total margin within 240mm stand width."""
        assert C["IPAD_SLOT_W"] <= STAND_W - 5, (
            f"IPAD_SLOT_W={C['IPAD_SLOT_W']} exceeds safe stand width ({STAND_W}mm)"
        )

    def test_slot_width_sized_for_portrait_not_landscape(self):
        """IPAD_SLOT_W must be less than STAND_W (portrait backdrop, not landscape pocket).

        The slot is a wide backdrop — intentionally wider than the bare iPad
        (213mm) to fill the stand width. The real guard is that it stays under
        STAND_W so it's clearly portrait orientation, not landscape (268mm+).
        """
        assert C["IPAD_SLOT_W"] < STAND_W, (
            f"IPAD_SLOT_W={C['IPAD_SLOT_W']} >= STAND_W={STAND_W} — looks like landscape"
        )
        assert C["IPAD_SLOT_W"] >= IPAD_WIDTH_BARE, (
            f"IPAD_SLOT_W={C['IPAD_SLOT_W']} narrower than bare iPad ({IPAD_WIDTH_BARE}mm)"
        )

    def test_slot_gap_accommodates_device_thickness(self):
        """IPAD_SLOT_GAP must fit 5.1mm bare iPad + some case allowance (at least 6mm)."""
        assert C["IPAD_SLOT_GAP"] >= 6, (
            f"IPAD_SLOT_GAP={C['IPAD_SLOT_GAP']} too narrow for iPad + case"
        )

    def test_back_wall_height_unchanged_at_60mm(self):
        """IPAD_BACK_H must remain 60mm as decided."""
        assert C["IPAD_BACK_H"] == 60, (
            f"IPAD_BACK_H={C['IPAD_BACK_H']}, expected 60"
        )
