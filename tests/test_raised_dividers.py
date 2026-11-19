"""
Tests for dividers raised up into the stacking lip: which divider walls lie on grid lines.
"""

import os
import pytest
import importlib.util


def _load(name, *path):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location(name, os.path.join(project_root, *path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


raised = _load("raisedDividers", "lib", "gridfinityUtils", "raisedDividers.py")
layout = _load("compartmentLayout", "lib", "gridfinityUtils", "compartmentLayout.py")
Segment = raised.DividerSegment


def single_cells(columns, rows):
    return layout.normalizePockets([], columns, rows)


def test_uniform_4x2_rises_everywhere():
    assert raised.gridLineSegments(single_cells(4, 2), 4, 2, 4, 2) == [
        Segment('x', 1, 0, 2),
        Segment('x', 2, 0, 2),
        Segment('x', 3, 0, 2),
        Segment('y', 1, 0, 4),
    ]


def test_three_on_four_units_has_none():
    assert raised.gridLineSegments(single_cells(3, 1), 3, 1, 4, 1) == []


def test_half_cells_rise_only_on_whole_lines():
    segments = raised.gridLineSegments(single_cells(8, 2), 8, 2, 4, 2)
    assert [(s.axis, s.line) for s in segments] == [('x', 2), ('x', 4), ('x', 6), ('y', 1)]
    assert segments[-1] == Segment('y', 1, 0, 8)


def test_merged_cells_have_no_divider_on_their_inner_line():
    # The 4x2 case: one compartment over the whole front row, one over 2 cells and two single ones behind
    pockets = layout.normalizePockets([
        layout.pocket(0, 0, 4, 1),
        layout.pocket(0, 1, 2, 1),
        layout.pocket(2, 1),
        layout.pocket(3, 1),
    ], 4, 2)
    assert raised.gridLineSegments(pockets, 4, 2, 4, 2) == [
        Segment('x', 2, 1, 2),
        Segment('x', 3, 1, 2),
        Segment('y', 1, 0, 4),
    ]


def test_half_unit_bin_width():
    segments = raised.gridLineSegments(single_cells(5, 1), 5, 1, 2.5, 1)
    assert segments == [Segment('x', 2, 0, 1), Segment('x', 4, 0, 1)]


def test_single_compartment_has_none():
    assert raised.gridLineSegments(single_cells(1, 1), 1, 1, 3, 2) == []


def test_divider_runs_split_where_a_pocket_spans_the_line():
    # a 1x2 pocket on the left over both rows, the right column split: the y line only rises on the right
    pockets = layout.normalizePockets([layout.pocket(0, 0, 1, 2)], 2, 2)
    assert raised.gridLineSegments(pockets, 2, 2, 2, 2) == [
        Segment('x', 1, 0, 2),
        Segment('y', 1, 1, 2),
    ]


def test_disabled_without_lip_or_hollow_body():
    pockets = single_cells(2, 1)
    enabled = dict(isEnabled=True, hasLip=True, isHollow=True, isShaped=False)
    assert raised.segmentsForBin(**enabled, pockets=pockets, columns=2, rows=1, binWidth=2, binLength=1) == [Segment('x', 1, 0, 1)]
    for (key, value) in [('isEnabled', False), ('hasLip', False), ('isHollow', False), ('isShaped', True)]:
        flags = dict(enabled, **{key: value})
        assert raised.segmentsForBin(**flags, pockets=pockets, columns=2, rows=1, binWidth=2, binLength=1) == [], key


def test_half_grid_bin_counts_whole_units_not_feet():
    # a half grid bin 1.5 units wide has 3 feet, with 3 compartments only the line at 1 unit is a grid line. The
    # builder passes the size in units, passed in feet every line would rise
    assert raised.gridLineSegments(single_cells(3, 1), 3, 1, 1.5, 1) == [Segment('x', 2, 0, 1)]


def test_option_needs_compartments_besides_a_hollow_bin_with_a_lip():
    enabled = dict(generateBody=True, hasLip=True, isHollow=True, isShaped=False, isCreased=False, compartmentCount=3)
    assert raised.optionEnabled(**enabled) is True
    for (key, value) in [
        ('generateBody', False), ('hasLip', False), ('isHollow', False), ('isShaped', True),
        # a creased bin has a single compartment, see binBuilder.creaseLayout
        ('isCreased', True),
        # also cells merged into one compartment, no divider is left to raise
        ('compartmentCount', 1),
    ]:
        assert raised.optionEnabled(**dict(enabled, **{key: value})) is False, key


# Round 50, decided 19.11.2026: a raised divider goes straight up as thick as it is below; under an untrimmed lip its
# top is a roof at the lip's 45 degrees with its ridge at the lip's top, under a trimmed lip a flat top at the trimmed
# top chamfered at 45 degrees on both sides, as wide as the lip's crown. In cm: a 1.2 mm divider, its low face at
# 41.15 mm, the lip's top at 20 mm
def flat(points):
    return [value for point in points for value in point]


def test_under_an_untrimmed_lip_the_top_is_a_roof():
    top = raised.dividerTop(4.115, 0.12, 2.0, isTrimmed=False)
    assert flat(top) == pytest.approx(flat([(4.115, 1.94), (4.175, 2.0), (4.235, 1.94)]))


def test_under_a_trimmed_lip_the_top_is_flat_and_chamfered():
    top = raised.dividerTop(4.115, 0.12, 2.0, isTrimmed=True)
    # 0.3 mm chamfers, 0.6 mm flat, as the trimmed lip's crown
    assert flat(top) == pytest.approx(flat([(4.115, 1.97), (4.145, 2.0), (4.205, 2.0), (4.235, 1.97)]))
    assert raised.DIVIDER_TOP_CHAMFER == pytest.approx(0.03)


def test_a_thin_divider_keeps_half_its_top_flat():
    top = raised.dividerTop(1.0, 0.04, 2.0, isTrimmed=True)
    assert flat(top) == pytest.approx(flat([(1.0, 1.99), (1.01, 2.0), (1.03, 2.0), (1.04, 1.99)]))


def test_the_top_takes_a_smaller_of_its_own():
    # the generator hands Fusion's min for parameters that follow the model
    calls = []
    def smaller(a, b):
        calls.append((a, b))
        return min(a, b)
    raised.dividerTop(4.115, 0.12, 2.0, isTrimmed=True, smaller=smaller)
    assert calls == [(raised.DIVIDER_TOP_CHAMFER, 0.03)]
