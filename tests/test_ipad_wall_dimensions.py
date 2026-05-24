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


class TestIpadWallSlotDimensions:
    """Captive slot in tray body must hold the wall blade securely."""

    def test_slot_z_depth_provides_leverage(self):
        """IPAD_SLOT_Z_DEPTH must give a reasonable height-to-engagement ratio."""
        slot_z = C["IPAD_SLOT_Z_DEPTH"]
        wall_h = C["IPAD_BACK_H"]
        ratio = wall_h / slot_z
        assert slot_z >= 8, (
            f"IPAD_SLOT_Z_DEPTH={slot_z}mm too shallow — wall will wobble"
        )
        assert ratio <= 8, (
            f"Height-to-engagement ratio {ratio:.1f}:1 too high (wobble risk)"
        )

    def test_slot_z_fits_below_channel_floor(self):
        """Slot must fit between SPLIT_Z and the iPad channel floor (Z=52.5)."""
        split_z = C["SPLIT_Z"]
        slot_top = split_z + 1 + C["IPAD_SLOT_Z_DEPTH"]
        # Channel floor is at SPLIT_Z + 1 + 8 + 2.5 = 52.5
        channel_floor = split_z + 1 + 8 + 2.5
        assert slot_top <= channel_floor, (
            f"Slot top Z={slot_top}mm breaches channel floor at Z={channel_floor}mm"
        )

    def test_slot_y_depth_provides_grip(self):
        """IPAD_SLOT_Y_DEPTH must be deep enough for front-back grip."""
        assert C["IPAD_SLOT_Y_DEPTH"] >= 6, (
            f"IPAD_SLOT_Y_DEPTH={C['IPAD_SLOT_Y_DEPTH']}mm — need >= 6mm for grip"
        )

    def test_blade_fits_in_slot(self):
        """Blade (slot - TOL) must be smaller than slot in both Z and Y."""
        blade_z = C["IPAD_SLOT_Z_DEPTH"] - C["IPAD_WALL_TOL"]
        blade_y = C["IPAD_SLOT_Y_DEPTH"] - C["IPAD_WALL_TOL"]
        assert blade_z > 0, "Blade Z must be positive"
        assert blade_y > 0, "Blade Y must be positive"
        assert blade_z < C["IPAD_SLOT_Z_DEPTH"], "Blade must be smaller than slot"

    def test_clearance_per_side(self):
        """Clearance per side should be IPAD_WALL_TOL / 2 = 0.2mm."""
        clearance = C["IPAD_WALL_TOL"] / 2
        assert 0.1 <= clearance <= 0.4, (
            f"Clearance per side {clearance}mm outside sane range"
        )

    def test_detent_exists(self):
        """Snap detent constants must be defined for slide retention."""
        assert "IPAD_DETENT_H" in C, "IPAD_DETENT_H not defined"
        assert C["IPAD_DETENT_H"] > 0, "IPAD_DETENT_H must be positive"
        assert C["IPAD_DETENT_H"] <= 1.0, (
            f"IPAD_DETENT_H={C['IPAD_DETENT_H']}mm too tall"
        )


class TestIpadWallDimensions:
    """Wall body dimensions must match existing constants."""

    def test_wall_width_fits_build_plate(self):
        """Wall width (IPAD_SLOT_W + 10) must fit the QIDI Q2 build plate (275mm)."""
        expected_width = C["IPAD_SLOT_W"] + 10
        assert expected_width <= 275, (
            f"Wall width {expected_width}mm exceeds QIDI Q2 build plate (275mm)"
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
