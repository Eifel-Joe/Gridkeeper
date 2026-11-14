"""
Tests for the layout of a Cullenect insert: its size from grid units or a free width, where the text and the symbol go.
Layout after cullenect_label_generate in Cullenect.scad by CullenJWebb (MIT), https://github.com/CullenJWebb/Cullenect-Labels
"""

import os
import sys
import importlib.util

import pytest
from pytest import approx


def _load_layout():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(project_root, "lib", "gridfinityUtils")
    # the module imports const as a sibling module, load both under a throwaway package
    package = "cullenectLabelLayoutTestPackage"
    if package not in sys.modules:
        packageSpec = importlib.util.spec_from_loader(package, loader=None, is_package=True)
        packageModule = importlib.util.module_from_spec(packageSpec)
        packageModule.__path__ = [folder]
        sys.modules[package] = packageModule
    spec = importlib.util.spec_from_file_location(package + ".cullenectLabelLayout", os.path.join(folder, "cullenectLabelLayout.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


layout = _load_layout()

SCREW = (1.456, 1.0)


class TestLabelSize:
    def test_one_unit_is_the_cullenect_insert(self):
        assert layout.labelSize(1, None, 4.2, 0, 0) == approx((3.6, 1.1))

    def test_two_units(self):
        assert layout.labelSize(2, None, 4.2, 0, 0) == approx((7.8, 1.1))

    def test_half_units_follow_the_grid(self):
        assert layout.labelSize(1.5, None, 4.2, 0, 0) == approx((5.7, 1.1))

    def test_other_grid_width(self):
        assert layout.labelSize(1, None, 5.0, 0, 0) == approx((4.4, 1.1))

    def test_free_width(self):
        assert layout.labelSize(None, 2.5, 4.2, 0, 0) == approx((2.5, 1.1))

    def test_offsets_correct_width_and_height(self):
        assert layout.labelSize(1, None, 4.2, -0.01, 0.01) == approx((3.59, 1.11))

    def test_offsets_apply_to_a_free_width_too(self):
        assert layout.labelSize(None, 2.5, 4.2, -0.01, 0) == approx((2.49, 1.1))

    def test_needs_units_or_a_width(self):
        with pytest.raises(ValueError):
            layout.labelSize(None, None, 4.2, 0, 0)


class TestValidWidth:
    @pytest.mark.parametrize("width", [1.0, 3.6, 30.0])
    def test_inside(self, width):
        assert layout.validWidth(width) is True

    @pytest.mark.parametrize("width", [0.9, 30.1, 0, -1])
    def test_outside(self, width):
        assert layout.validWidth(width) is False


class TestLabelLayout:
    def test_screw_sits_at_the_right_edge(self):
        result = layout.labelLayout(3.6, 1.1, SCREW, True, 1)
        assert result.width == approx(3.6)
        assert result.height == approx(1.1)
        assert result.iconMaxX == approx(3.6)
        assert result.iconCenterY == approx(0.55)

    def test_text_ends_before_the_screw(self):
        result = layout.labelLayout(3.6, 1.1, SCREW, True, 1)
        assert result.textMinX == approx(0.1)
        assert result.textMaxX == approx(3.6 - 1.456 - 0.1)

    def test_hardware_keeps_a_margin_like_its_gap_to_top_and_bottom(self):
        result = layout.labelLayout(3.6, 1.1, (0.8, 0.8), False, 1)
        assert result.iconMaxX == approx(3.45)
        assert result.textMaxX == approx(3.45 - 0.8 - 0.1)

    def test_hardware_as_tall_as_the_label_goes_to_the_edge(self):
        result = layout.labelLayout(3.6, 1.1, (1.2, 1.2), False, 1)
        assert result.iconMaxX == approx(3.6)

    def test_text_alone_uses_the_width_with_margins(self):
        result = layout.labelLayout(3.6, 1.1, None, False, 1)
        assert result.iconMaxX is None
        assert result.textMaxX == approx(3.5)

    def test_one_line_is_as_tall_as_cullenects_font_size_5(self):
        result = layout.labelLayout(3.6, 1.1, None, False, 1)
        assert result.lineHeights == approx([0.5])
        assert result.lineCenters == approx([0.55])

    def test_two_lines_are_stacked_around_the_middle(self):
        result = layout.labelLayout(3.6, 1.1, None, False, 2)
        assert result.lineHeights == approx([0.35, 0.35])
        (top, bottom) = result.lineCenters
        assert top > 0.55 > bottom
        assert top - 0.55 == approx(0.55 - bottom)
        # the letters keep a gap and stay on the insert
        assert top - bottom - 0.35 >= 0.1
        assert top + 0.35 / 2 <= 1.1 - 0.1
        assert bottom - 0.35 / 2 >= 0.1

    def test_empty_insert_is_valid(self):
        result = layout.labelLayout(3.6, 1.1, None, False, 0)
        assert result.lineHeights == []
        assert result.lineCenters == []
        assert result.iconMaxX is None

    def test_too_many_lines(self):
        with pytest.raises(ValueError):
            layout.labelLayout(3.6, 1.1, None, False, 3)


class TestFittedLineHeight:
    def test_text_that_fits_keeps_its_height(self):
        assert layout.fittedLineHeight(0.5, 1.8, 1.944) == approx(0.5)

    def test_wide_text_shrinks_to_the_space(self):
        assert layout.fittedLineHeight(0.5, 2.0, 1.0) == approx(0.25)

    def test_no_space_keeps_the_height(self):
        # nothing sensible to shrink to, the generator leaves the text as it is
        assert layout.fittedLineHeight(0.5, 2.0, 0) == approx(0.5)
