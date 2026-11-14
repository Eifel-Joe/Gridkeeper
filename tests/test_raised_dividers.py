"""
Tests for dividers raised up into the stacking lip: which divider walls lie on grid lines.
"""

import os
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
    # Jörg's 4x2: one compartment over the whole front row, one over 2 cells and two single ones behind
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
