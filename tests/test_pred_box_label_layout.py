"""
The label of the storage box after Pred (round 29, p262, dev-notes/r29/boxlabel-plan.md): Pred's flat plate, sized after
the box's label width, with a large field at the left, two lines at the right and a row of up to five Cullenect symbols
under them. Fusion-free, cm inside, the cases in mm (project CLAUDE.md).

Pred's file at 5 x 4 x 6 (fusion-auftraege/pred_read2.out): Label:1 EmptyLabel x 81.25 ... 148.75, y 6.45 ... 7.3,
z 12.45 ... 36.95 mm; Label_M_Screws 0.4 mm thicker towards the front (raised letters). The box's label width is
min(X * 42 + 20 - 159.5, 85) mm (predBox.PRED, Pred's _LabelWidth).
"""

import os

import pytest

from tests.test_joint_origin_layout import _load

layout = _load("predBoxLabelLayout")
catalog = _load("cullenectCatalog")

ICONS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "gridfinityUtils", "cullenectIcons")

SCREW = (1.456, 1.0)
NUT = (1.0, 0.866024)


def mm(value):
    return round(value * 10, 4)


class TestPlate:
    @pytest.mark.parametrize("cells, width", [(4, 25.5), (5, 67.5), (6, 82.0), (7, 82.0), (20, 82.0)])
    def test_width_is_the_box_label_width_less_3_mm(self, cells, width):
        assert mm(layout.plateWidth(cells)) == pytest.approx(width)

    def test_preds_plate_at_5_cells(self):
        """EmptyLabel 67.5 x 24.5 x 0.85 mm"""
        assert (mm(layout.plateWidth(5)), mm(layout.PLATE_HEIGHT), mm(layout.PLATE_THICKNESS)) == pytest.approx((67.5, 24.5, 0.85))

    def test_preds_rounded_corners_and_chamfer(self):
        """Label/Sketch1 arcs of 3.5 mm, Chamfer1 0.2 mm (r29_walk/Label.json): 1389.6464 mm3 at 5 cells"""
        assert (mm(layout.PLATE_CORNER_RADIUS), mm(layout.PLATE_CHAMFER)) == pytest.approx((3.5, 0.2))

    def test_raised_marking_is_preds_04_mm(self):
        """Label_M_Screws: y 6.05 ... 7.3 against 6.45 ... 7.3"""
        assert mm(layout.MARKING_DEPTH) == pytest.approx(0.4)

    def test_a_box_is_at_least_4_cells_wide(self):
        assert layout.sizeProblem(3) is not None
        assert layout.sizeProblem(4) is None

    def test_where_the_plate_sits_in_the_holder(self):
        """Pred at 5 x 4 x 6, box middle x 115 mm, middle height 24.7 mm: back face at y 7.3, centred"""
        assert mm(layout.SEAT_Y) == pytest.approx(7.3)


def _right(lay):
    return lay.textMinX, lay.textMaxX


class TestLayout:
    def test_margin_keeps_off_the_holder_lips(self):
        """The lips cover 1 mm of the plate at the sides and bottom, their corners 2.5 mm slanted: 2.5 mm stay free"""
        lay = layout.labelLayout(layout.plateWidth(5), True, 2, [SCREW])
        w, h = 67.5, 24.5
        assert mm(lay.bigMinX) == pytest.approx(-w / 2 + 2.5)
        assert mm(lay.textMaxX) == pytest.approx(w / 2 - 2.5)
        bottom = min(box[1] - box[3] / 2 for box in lay.symbolBoxes)
        assert mm(bottom) >= -h / 2 + 2.5 - 1e-6

    def test_the_large_field_takes_35_percent(self):
        lay = layout.labelLayout(layout.plateWidth(5), True, 2, [])
        usable = 67.5 - 5
        assert mm(lay.bigMaxX - lay.bigMinX) == pytest.approx(usable * 0.35)
        assert mm(lay.textMinX - lay.bigMaxX) == pytest.approx(2.0)
        assert mm(lay.bigHeight) == pytest.approx(12.0)
        assert lay.bigCenterY == pytest.approx(0)

    def test_no_large_text_gives_the_right_field_the_whole_width(self):
        lay = layout.labelLayout(layout.plateWidth(5), False, 2, [])
        assert lay.bigHeight is None
        assert mm(lay.textMinX) == pytest.approx(-67.5 / 2 + 2.5)

    def test_two_lines_above_the_symbol_row(self):
        lay = layout.labelLayout(layout.plateWidth(5), True, 2, [SCREW])
        assert [mm(h) for h in lay.lineHeights] == pytest.approx([4.0, 4.0])
        (upper, lower) = lay.lineCenters
        assert upper > lower
        row = lay.symbolBoxes[0]
        # the row at the bottom of the usable field, 6 mm high
        assert mm(row[1]) == pytest.approx(-24.5 / 2 + 2.5 + 3.0)
        assert mm(row[3]) == pytest.approx(6.0)
        # the lower line's descenders stay above the row: baseline under the centre by half the height
        assert mm(lower - lay.lineHeights[1] / 2) >= mm(row[1] + row[3] / 2) + 0.5
        # the upper line stays under the top margin
        assert mm(upper + lay.lineHeights[0] / 2) <= 24.5 / 2 - 2.5 + 1e-6

    def test_lines_without_symbols_are_centred(self):
        lay = layout.labelLayout(layout.plateWidth(5), True, 2, [])
        assert sum(lay.lineCenters) == pytest.approx(0)
        one = layout.labelLayout(layout.plateWidth(5), True, 1, [])
        assert one.lineCenters == pytest.approx([0])

    def test_symbols_without_lines_are_centred(self):
        lay = layout.labelLayout(layout.plateWidth(5), True, 0, [NUT, NUT])
        assert all(box[1] == pytest.approx(0) for box in lay.symbolBoxes)
        assert lay.lineCenters == []

    def test_symbols_keep_their_shape_at_the_row_height(self):
        lay = layout.labelLayout(layout.plateWidth(6), True, 2, [SCREW, NUT])
        (screw, nut) = lay.symbolBoxes
        assert mm(screw[2]) == pytest.approx(6.0 * 1.456)
        assert (mm(nut[2]), mm(nut[3])) == pytest.approx((6.0 / 0.866024, 6.0), abs=1e-3)
        # one row, left aligned, 1.5 mm apart
        assert mm(screw[0]) == pytest.approx(mm(lay.textMinX))
        assert mm(nut[0] - (screw[0] + screw[2])) == pytest.approx(1.5)

    def test_symbols_that_dont_fit_are_left_out_from_the_right(self):
        """Hauptsitzung: nothing gets smaller, the ones that don't fit are dropped"""
        lay = layout.labelLayout(layout.plateWidth(5), True, 2, [SCREW] * 5)
        assert len(lay.symbolBoxes) + lay.dropped == 5
        assert lay.dropped > 0
        last = lay.symbolBoxes[-1]
        assert last[0] + last[2] <= lay.textMaxX + 1e-9

    def test_up_to_five_symbols(self):
        with pytest.raises(ValueError):
            layout.labelLayout(layout.plateWidth(6), True, 2, [NUT] * 6)

    def test_up_to_two_lines(self):
        with pytest.raises(ValueError):
            layout.labelLayout(layout.plateWidth(6), True, 3, [])

    def test_the_smallest_box_still_takes_one_symbol(self):
        lay = layout.labelLayout(layout.plateWidth(4), True, 2, [SCREW, SCREW])
        assert len(lay.symbolBoxes) == 1 and lay.dropped == 1


class TestSymbolChoices:
    def test_none_first_then_screws_then_hardware(self):
        choices = layout.symbolChoices(ICONS)
        names = [name for (name, _path) in choices]
        assert names[0] == layout.NO_SYMBOL
        assert choices[0][1] is None
        assert "Nut" in names and "Washer" in names
        assert "Socket Hex" in names
        assert names.index("Socket Hex") < names.index("Washer")

    def test_every_choice_but_none_has_its_svg(self):
        for (name, path) in layout.symbolChoices(ICONS)[1:]:
            assert os.path.isfile(path), name

    def test_screws_are_machine_screws_with_full_thread(self):
        paths = [path for (_name, path) in layout.symbolChoices(ICONS)[1:] if "screws" in path]
        assert len(paths) > 0
        assert all("_machine_full_" in os.path.basename(path) and path.endswith("_noflange_nosec.svg") for path in paths)

    def test_choice_names_are_unique(self):
        names = [name for (name, _path) in layout.symbolChoices(ICONS)]
        assert len(names) == len(set(names))


class TestTitle:
    def test_name_with_the_start_of_the_text(self):
        assert layout.labelTitle(5, "M2", ["Socket head", ""]) == "Gridkeeper box label 5 cells M2"

    def test_name_from_the_first_line_without_large_text(self):
        assert layout.labelTitle(5, "", ["Socket head", ""]) == "Gridkeeper box label 5 cells Socket head"

    def test_long_text_is_cut(self):
        assert layout.labelTitle(4, "x" * 30, []).endswith("x" * 20 + "…")


class TestWidthChoices:
    """17.11.2026: the label has fixed widths, so the width is a choice menu, not a free setting. Pred's label widths: box 4 cells 28.5 mm, 5 cells 70.5 mm, from 6 cells 85 mm"""

    def test_three_fixed_widths(self):
        assert layout.widthChoices() == [("Box 4 cells (28.5 mm)", 4), ("Box 5 cells (70.5 mm)", 5), ("Box 6+ cells (85 mm)", 6)]

    def test_every_choice_is_preds_label_width(self):
        for (name, cells) in layout.widthChoices():
            assert f"({mm(layout.labelWidth(cells)):g} mm)" in name

    @pytest.mark.parametrize("cells, name", [(4, "Box 4 cells (28.5 mm)"), (5, "Box 5 cells (70.5 mm)"),
                                             (6, "Box 6+ cells (85 mm)"), (12, "Box 6+ cells (85 mm)")])
    def test_a_picked_box_preselects_its_width(self, cells, name):
        assert layout.widthChoiceFor(cells) == name

    def test_a_choice_gives_its_cells(self):
        assert layout.cellsOfChoice("Box 5 cells (70.5 mm)") == 5
        assert layout.cellsOfChoice("unknown") == 5
