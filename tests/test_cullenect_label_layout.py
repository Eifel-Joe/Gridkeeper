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
        assert layout.fittedLineHeight(0.5, 2.0, 1.0) == approx(0.25 * (1 - layout.TEXT_WIDTH_RESERVE))

    def test_no_space_keeps_the_height(self):
        # nothing sensible to shrink to, the generator leaves the text as it is
        assert layout.fittedLineHeight(0.5, 2.0, 0) == approx(0.5)

    def test_text_as_wide_as_the_space_keeps_a_reserve(self):
        # Fusion lays text out by the advance of its letters, wider than their outlines that were measured: a line
        # fitted exactly ran out of its box (p84), it keeps a reserve
        assert layout.fittedLineHeight(0.5, 3.4, 3.4) * 3.4 / 0.5 <= 3.4 * (1 - layout.TEXT_WIDTH_RESERVE) + 1e-9

    def test_welle_6mm_fits_with_the_reserve(self):
        # p84: the user's 1U insert, "Welle 6mm" measured 34.27 mm wide at 5 mm, 34 mm of room, fitted to 4.96 mm and
        # broken in two by Fusion. Fitted now it leaves the reserve free
        height = layout.fittedLineHeight(0.5, 3.427, 3.4)
        assert 3.427 * height / 0.5 <= 3.4 * (1 - layout.TEXT_WIDTH_RESERVE) + 1e-9
        assert layout.TEXT_WIDTH_RESERVE >= 0.03

    def test_text_well_inside_the_reserve_keeps_its_height(self):
        assert layout.fittedLineHeight(0.5, 1.8, 3.4) == approx(0.5)


class TestWidthExpression:
    def test_units_follow_the_base_width_parameter(self):
        assert layout.widthExpression(1, None, 'gfBaseWidth', 0) == 'gfBaseWidth * 1 - 6 mm'

    def test_half_units_and_an_offset(self):
        assert layout.widthExpression(1.5, None, 'gfBaseWidth', -0.01) == 'gfBaseWidth * 1.5 - 6 mm - 0.1 mm'

    def test_free_width_is_a_plain_length_with_its_offset(self):
        assert layout.widthExpression(None, 2.5, None, 0) == '25 mm'
        assert layout.widthExpression(None, 2.5, None, 0.02) == '25 mm + 0.2 mm'


class TestLabelTitle:
    def test_units_and_the_first_line(self):
        assert layout.labelTitle(1, None, ['M3x10', 'DIN 912']) == 'Gridfinity label 1U M3x10'

    def test_free_width(self):
        assert layout.labelTitle(None, 2.5, []) == 'Gridfinity label 25 mm'

    def test_long_text_is_cut(self):
        assert layout.labelTitle(2, None, ['A very long first line of text']) == 'Gridfinity label 2U A very long first li…'


def _touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write('<svg/>')


class TestSymbolChoice:
    SCREW = ('socket', 'machine', 'full', 'hex', False, False)

    def test_screw_file(self, tmp_path):
        name = 'screw_socket_machine_full_hex_noflange_nosec.svg'
        _touch(str(tmp_path / 'screws' / name))
        assert layout.symbolChoice(str(tmp_path), True, self.SCREW, 'none') == (str(tmp_path / 'screws' / name), True)

    def test_screw_without_file_has_no_symbol(self, tmp_path):
        assert layout.symbolChoice(str(tmp_path), True, self.SCREW, 'none') == (None, True)

    def test_screw_wins_over_hardware(self, tmp_path):
        _touch(str(tmp_path / 'hardware' / 'nut.svg'))
        assert layout.symbolChoice(str(tmp_path), True, self.SCREW, 'nut')[1] is True

    def test_hardware_by_its_file_name(self, tmp_path):
        _touch(str(tmp_path / 'hardware' / 'tnut_1.svg'))
        assert layout.symbolChoice(str(tmp_path), False, self.SCREW, 'tnut_1') == (str(tmp_path / 'hardware' / 'tnut_1.svg'), False)

    def test_no_symbol(self, tmp_path):
        assert layout.symbolChoice(str(tmp_path), False, self.SCREW, 'none') == (None, False)


def _svg(tmp_path, width, height):
    path = tmp_path / 'icon.svg'
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm"><path d="M0,0"/></svg>')
    return str(path)


class TestIconSize:
    def test_drawn_at_its_svg_size(self, tmp_path):
        assert layout.iconSize(_svg(tmp_path, 14.56, 10), 3.6, 1.1) == approx((1.456, 1.0))

    def test_at_most_as_tall_as_the_insert(self, tmp_path):
        assert layout.iconSize(_svg(tmp_path, 20, 22), 3.6, 1.1) == approx((1.0, 1.1))

    def test_at_most_as_wide_as_the_insert_without_its_margins(self, tmp_path):
        # a screw on a 10 mm insert is scaled down to 9 mm, it ends at the right edge
        assert layout.iconSize(_svg(tmp_path, 14.56, 10), 1.0, 1.1) == approx((0.9, 0.9 / 1.456))


class TestLayoutProblem:
    def test_a_1u_insert_with_screw_and_text_is_fine(self):
        assert layout.layoutProblem(layout.labelLayout(3.6, 1.1, SCREW, True, 1)) is None

    def test_half_unit_with_screw_leaves_no_room_for_text(self, tmp_path):
        size = layout.iconSize(_svg(tmp_path, 14.56, 10), 1.5, 1.1, True)
        assert 'text' in layout.layoutProblem(layout.labelLayout(1.5, 1.1, size, True, 1))

    def test_half_unit_with_screw_and_no_text_is_fine(self, tmp_path):
        size = layout.iconSize(_svg(tmp_path, 14.56, 10), 1.5, 1.1, True)
        assert layout.layoutProblem(layout.labelLayout(1.5, 1.1, size, True, 0)) is None

    def test_too_low(self):
        assert layout.layoutProblem(layout.labelLayout(3.6, 0.09, None, False, 0)) is not None


class TestInsertProblem:
    def test_fine(self, tmp_path):
        assert layout.insertProblem(3.6, 1.1, _svg(tmp_path, 14.56, 10), True, False, 1, 0, 0) is None

    def test_width_out_of_range(self):
        assert 'wide' in layout.insertProblem(0.5, 1.1, None, False, False, 1, 0, 0)

    def test_corrections_are_small(self):
        assert 'orrection' in layout.insertProblem(3.6, 1.1, None, False, False, 1, 0, -0.2)
        assert 'orrection' in layout.insertProblem(3.6, 1.1, None, False, False, 1, 0.11, 0)

    def test_a_chosen_symbol_without_svg(self):
        assert 'svg' in layout.insertProblem(3.6, 1.1, None, True, True, 1, 0, 0)

    def test_no_room_for_text(self, tmp_path):
        assert 'text' in layout.insertProblem(1.5, 1.1, _svg(tmp_path, 14.56, 10), True, False, 1, 0, 0)


class TestNarrowHardware:
    # crimp_butt_splice: 14.56 x 5.76 mm, keeps a right margin like its gap to top and bottom
    def test_wide_hardware_stays_on_a_narrow_insert(self, tmp_path):
        size = layout.iconSize(_svg(tmp_path, 14.56, 5.76), 1.0, 1.1, False)
        result = layout.labelLayout(1.0, 1.1, size, False, 0)
        assert result.iconMaxX - size[0] >= 0.1 - 1e-9
        assert result.iconMaxX <= 1.0 + 1e-9
        assert layout.layoutProblem(result) is None

    def test_hardware_that_fits_keeps_its_size(self, tmp_path):
        assert layout.iconSize(_svg(tmp_path, 10, 8.66), 3.6, 1.1, False) == approx((1.0, 0.866))

    def test_a_symbol_off_the_insert_is_a_problem(self):
        result = layout.labelLayout(1.0, 1.1, (1.2, 0.5), False, 0)
        assert 'symbol' in layout.layoutProblem(result)


class TestMovedLayout:
    """The insert is drawn where it goes, so letters a later text adds go there too"""

    def test_text_and_symbol_move_by_the_offset(self):
        original = layout.labelLayout(3.6, 1.1, SCREW, True, 2)
        moved = layout.movedLayout(original, 0.5, 1.5)
        assert moved.textMinX == approx(original.textMinX + 0.5)
        assert moved.textMaxX == approx(original.textMaxX + 0.5)
        assert moved.iconMaxX == approx(original.iconMaxX + 0.5)
        assert moved.iconCenterY == approx(original.iconCenterY + 1.5)
        assert moved.lineCenters == approx([center + 1.5 for center in original.lineCenters])
        assert moved.lineHeights == original.lineHeights
        assert (moved.width, moved.height, moved.iconWidth) == (original.width, original.height, original.iconWidth)

    def test_without_symbol_stays_without(self):
        moved = layout.movedLayout(layout.labelLayout(3.6, 1.1, None, False, 1), 0, 1.5)
        assert moved.iconMaxX is None


def test_marking_is_two_layers():
    # text and symbol of an insert are two 0.2 mm layers thick (Nutzer 15.11.2026, p130)
    const = sys.modules["cullenectLabelLayoutTestPackage.const"]
    assert const.CULLENECT_MARKING_DEPTH == approx(0.04)
    assert not hasattr(const, "CULLENECT_LAYER")


# --- round 13 (p100, p160): an insert jointed into a pocket has to fit it, compared in mm since an insert and a bin
# have base units of their own

def test_insert_fits_pocket_of_same_units():
    assert layout.insertFitsPocket(36.0, 11.0, 36.3, 11.3)


def test_insert_wider_than_pocket_does_not_fit():
    assert not layout.insertFitsPocket(78.0, 11.0, 36.3, 11.3)


def test_insert_of_larger_base_unit_does_not_fit():
    # 2U on a 12 mm base unit... in the pocket of 2U on an 11 mm base: 2*120-6 = 234 > 2*110-6+0.3 = 214.3
    assert not layout.insertFitsPocket(2 * 120 - 6, 11.0, 2 * 110 - 6 + 0.3, 11.3)


def test_insert_with_printer_offset_up_to_the_pocket_fits():
    assert layout.insertFitsPocket(36.3, 11.3, 36.3, 11.3)
    assert not layout.insertFitsPocket(36.31, 11.0, 36.3, 11.3)


def test_pocket_misfit_text_is_literal():
    assert layout.POCKET_MISFIT == "This pocket is too small for the insert, pick one that fits"


DESCENT = 0.294


def _lowestDescender(result):
    # the lower line's baseline is under its middle by half its height, the descenders go below by DESCENT
    height = result.lineHeights[-1]
    return result.lineCenters[-1] - height / 2 - DESCENT * height


class TestDescenders:
    # round 17, p110: two lines on an insert made lower by its height correction, the descenders stay on it
    def test_descenders_stay_inside_with_minus_1mm(self):
        result = layout.labelLayout(3.6, 1.0, None, False, 2, 'Heavy')
        assert _lowestDescender(result) >= -1e-9
        assert result.lineHeights[0] == approx(result.lineHeights[1])
        assert result.lineHeights[0] < 0.35
        assert layout.layoutProblem(result) is None

    @pytest.mark.parametrize('style', ['Regular', 'Bold', 'Heavy'])
    def test_without_correction_two_lines_keep_their_height(self, style):
        assert layout.labelLayout(3.6, 1.1, None, False, 2, style).lineHeights == approx([0.35, 0.35])

    def test_one_line_is_unchanged(self):
        assert layout.labelLayout(3.6, 1.0, None, False, 1, 'Heavy').lineHeights == approx([0.5])

    def test_floor_stops_the_descender_shrink(self):
        # 9 mm high: the descenders would need 2.5 mm letters, Heavy goes down to 3.05 mm only
        result = layout.labelLayout(3.6, 0.9, None, False, 2, 'Heavy')
        assert result.lineHeights == approx([0.04 / 0.1313] * 2)
        assert 'Two lines' in layout.layoutProblem(result)

    def test_text_already_below_its_floor_is_not_shrunk(self):
        # Regular at 3.5 mm is below its 4.43 mm floor already, at 10 mm high its descenders would need it smaller
        result = layout.labelLayout(3.6, 1.0, None, False, 2, 'Regular')
        assert result.lineHeights == approx([0.35, 0.35])
        assert 'Two lines' in layout.layoutProblem(result)

    def test_insert_problem_reports_the_floor(self):
        assert 'Two lines' in layout.insertProblem(3.6, 1.0, None, False, False, 2, 0, -0.1, textStyle='Regular')
        assert layout.insertProblem(3.6, 1.0, None, False, False, 2, 0, -0.1, textStyle='Heavy') is None
