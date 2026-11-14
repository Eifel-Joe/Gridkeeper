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


# Fillets up to the top (p83): a compartment corner gets one where both its sides go up to the top, a raised divider
# or an outer wall, but not both outer walls, the bin's own corner is round already
Corner = raised.FilletCorner


def test_three_columns_fillet_where_the_dividers_meet_the_outer_walls():
    segments = [Segment('x', 1, 0, 1), Segment('x', 2, 0, 1)]
    assert sorted(raised.filletCorners(segments, 3, 1)) == sorted([
        Corner(0, 0, 1, -1), Corner(0, 0, 1, 1),
        Corner(1, 0, -1, -1), Corner(1, 0, -1, 1), Corner(1, 0, 1, -1), Corner(1, 0, 1, 1),
        Corner(2, 0, -1, -1), Corner(2, 0, -1, 1),
    ])


def test_crossing_dividers_fillet_all_four_corners():
    segments = [Segment('x', 1, 0, 2), Segment('y', 1, 0, 2)]
    corners = raised.filletCorners(segments, 2, 2)
    # the crossing in the middle, one per cell
    assert {Corner(0, 0, 1, 1), Corner(1, 0, -1, 1), Corner(0, 1, 1, -1), Corner(1, 1, -1, -1)} <= set(corners)
    # and the four ends against the outer walls, two each
    assert len(corners) == 4 + 8


def test_no_fillet_where_a_raised_divider_meets_one_that_stays_down():
    # 4x2, the row divider spans only columns 0..2 on the grid, the column divider at line 1 rises over both rows
    segments = [Segment('x', 1, 0, 2)]
    corners = raised.filletCorners(segments, 2, 2)
    # the row divider at line 1 stays down, the crossing gets nothing
    assert all(not (corner.column in (0, 1) and corner.row == 0 and corner.sideY == 1) for corner in corners)
    assert all(not (corner.row == 1 and corner.sideY == -1) for corner in corners)
    assert len(corners) == 4


def test_no_fillet_without_raised_dividers():
    assert raised.filletCorners([], 3, 2) == []


# Which edges of the finished bin make up the chain a corner is filleted along (p83, variant C). Lengths in mm here,
# the code is unit free. Taken from Fusion: 3x2 bin, 3 columns, wall 1.2, divider 1 low x face at 41.433, front wall
# inner face y 1.2, lip face 1.9, corner fillet tops at 15.5, top 19.8
CORNER = Corner(0, 0, 1, -1)  # cell 0, its high x side against divider 1, low y side against the front wall
CORNER_AT = (41.433, 1.2)


def chain(start, end, corner=CORNER, at=CORNER_AT):
    return raised.isCornerChainEdge(corner, at, 3, 1, wall=1.2, lipOverhang=0.71, bottomZ=15.5, start=start, end=end)


def test_chain_takes_the_edges_up_the_wall_chamfer_and_lip():
    assert chain((41.433, 1.2, 15.5), (41.433, 1.2, 16.0))
    assert chain((41.433, 1.2, 16.0), (41.433, 1.9, 16.7))
    assert chain((41.433, 1.9, 16.7), (41.433, 1.9, 18.6))
    assert chain((41.433, 0.7, 19.8), (41.433, 1.9, 18.6))


def test_chain_leaves_edges_along_the_divider_or_the_wall():
    # the top of the divider, the top of the corner fillet below, the lip's chamfer along the wall
    assert not chain((41.433, 82.8, 19.8), (41.433, 0.7, 19.8))
    assert not chain((41.433, 1.2, 15.5), (41.433, 3.75, 15.5))
    assert not chain((41.433, 1.9, 16.7), (3.75, 1.9, 16.7))


def test_chain_starts_at_the_top_of_the_corner_fillet():
    assert not chain((41.433, 1.2, 3.55), (41.433, 1.2, 15.5))


def test_chain_on_the_other_side_of_the_divider_and_at_the_back_wall():
    assert chain((42.633, 1.9, 15.5), (42.633, 1.9, 18.6), Corner(1, 0, -1, -1), (42.633, 1.2))
    assert not chain((41.433, 1.9, 15.5), (41.433, 1.9, 18.6), Corner(1, 0, -1, -1), (42.633, 1.2))
    assert chain((41.433, 81.6, 16.7), (41.433, 81.6, 18.6), Corner(0, 0, 1, 1), (41.433, 82.3))
    assert not chain((41.433, 1.9, 16.7), (41.433, 1.9, 18.6), Corner(0, 0, 1, 1), (41.433, 82.3))


def test_chain_of_a_crossing_is_its_vertical_edge():
    crossing = Corner(0, 0, 1, 1)
    at = (40.0, 30.0)
    assert raised.isCornerChainEdge(crossing, at, 2, 2, wall=1.2, lipOverhang=0.71, bottomZ=15.5, start=(40.0, 30.0, 15.5), end=(40.0, 30.0, 19.8))
    assert not raised.isCornerChainEdge(crossing, at, 2, 2, wall=1.2, lipOverhang=0.71, bottomZ=15.5, start=(40.0, 30.0, 19.8), end=(40.0, 40.0, 19.8))
