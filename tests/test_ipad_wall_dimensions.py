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
    """Groove in top tray must accommodate the wall tongue with good leverage."""

    def test_groove_z_depth_provides_leverage(self):
        """IPAD_GROOVE_DEPTH must give a reasonable height-to-engagement ratio."""
        groove_z = C["IPAD_GROOVE_DEPTH"]
        wall_h = C["IPAD_BACK_H"]
        ratio = wall_h / groove_z
        assert groove_z >= 6, (
            f"IPAD_GROOVE_DEPTH={groove_z}mm too shallow — wall will wobble"
        )
        assert ratio <= 12, (
            f"Height-to-engagement ratio {ratio:.1f}:1 too high (wobble risk)"
        )

    def test_groove_z_depth_fits_top_tray(self):
        """Groove must not cut deeper than the top tray thickness."""
        top_h = C["STAND_H"] - C["SPLIT_Z"]
        assert C["IPAD_GROOVE_DEPTH"] < top_h, (
            f"IPAD_GROOVE_DEPTH={C['IPAD_GROOVE_DEPTH']}mm >= TOP_H={top_h}mm"
        )

    def test_tongue_fits_in_groove(self):
        """Tongue (groove - TOL) must be smaller than groove in both Z and Y."""
        groove_z = C["IPAD_GROOVE_DEPTH"]
        groove_y = C["IPAD_GROOVE_Y_DEPTH"]
        tongue_z = groove_z - C["IPAD_WALL_TOL"]
        tongue_y = groove_y - C["IPAD_WALL_TOL"]
        assert tongue_z < groove_z, "Tongue Z must be smaller than groove Z"
        assert tongue_y < groove_y, "Tongue Y must be smaller than groove Y"
        assert tongue_z > 0, "Tongue Z must be positive"
        assert tongue_y > 0, "Tongue Y must be positive"

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
            f"IPAD_DETENT_H={C['IPAD_DETENT_H']}mm too tall — wall won't slide in"
        )

    def test_buttress_exists(self):
        """Buttress constants must be defined for rotational stiffness."""
        assert "IPAD_BUTTRESS_H" in C, "IPAD_BUTTRESS_H not defined"
        assert C["IPAD_BUTTRESS_H"] > 0, "IPAD_BUTTRESS_H must be positive"


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
