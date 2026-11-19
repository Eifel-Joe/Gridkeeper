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


# Round 50, p650 extension: the lip's profile on both sides of a raised divider. In cm, a 1.2 mm divider 0.32 mm and
# 0.88 mm off the grid line, a full lip's tip 2.846 mm from it
FULL_TIP = 0.2846
LIGHT_TIP = 0.215


def test_a_full_ridge_has_its_support_down_to_both_divider_faces():
    (depth, chamferLow, chamferHigh) = raised.ridgeBox(FULL_TIP, 0.032, 0.088, tipLift=-0.12, minDepth=0.05, maxDepth=10)
    # each side 45 degrees from the tip to its divider face, under 1.2 mm straight below the tip
    assert chamferLow == pytest.approx(FULL_TIP - 0.032)
    assert chamferHigh == pytest.approx(FULL_TIP - 0.088)
    assert depth == pytest.approx(0.12 + FULL_TIP - 0.032)


def test_a_light_ridge_has_its_chamfer_under_the_body_top():
    (depth, chamferLow, chamferHigh) = raised.ridgeBox(LIGHT_TIP, 0.032, 0.088, tipLift=0, minDepth=0.05, maxDepth=10)
    assert (depth, chamferLow, chamferHigh) == pytest.approx((LIGHT_TIP - 0.032, LIGHT_TIP - 0.032, LIGHT_TIP - 0.088))


def test_a_ridge_reaches_at_least_down_to_the_lowered_dividers():
    # a divider as wide as the ridge needs no chamfer, the box still starts where the dividers were lowered to
    (depth, chamferLow, chamferHigh) = raised.ridgeBox(LIGHT_TIP, 0.3, 0.3, tipLift=0, minDepth=0.05, maxDepth=10)
    assert (depth, chamferLow, chamferHigh) == pytest.approx((0.05, 0, 0))


def test_a_ridge_is_cut_off_at_the_compartment_floor():
    # one height unit: about 1 mm of compartment, the support's lower part is cut off and its chamfers shorten by as much
    (depth, chamferLow, chamferHigh) = raised.ridgeBox(FULL_TIP, 0.032, 0.088, tipLift=-0.12, minDepth=0.05, maxDepth=0.1)
    cut = 0.12 + FULL_TIP - 0.032 - 0.1
    assert depth == pytest.approx(0.1)
    assert chamferLow == pytest.approx(max(0, FULL_TIP - 0.032 - cut))
    assert chamferHigh == pytest.approx(max(0, FULL_TIP - 0.088 - cut))


def test_the_sides_of_a_compartment_on_raised_dividers():
    segments = [Segment('x', 1, 0, 3), Segment('y', 1, 0, 2), Segment('y', 2, 0, 2)]
    # a 2x3 grid: the front left compartment has its right and back on raised dividers
    assert raised.raisedSides((0, 0, 1, 1), segments) == frozenset({'right', 'back'})
    assert raised.raisedSides((1, 1, 1, 1), segments) == frozenset({'left', 'front', 'back'})
    assert raised.raisedSides((0, 2, 2, 1), segments) == frozenset({'front'})
    assert raised.raisedSides((0, 0, 1, 1), []) == frozenset()


def test_a_ridge_cut_off_a_little_keeps_shorter_chamfers():
    (depth, chamferLow, chamferHigh) = raised.ridgeBox(FULL_TIP, 0.032, 0.088, tipLift=-0.12, minDepth=0.05, maxDepth=0.3)
    cut = 0.12 + FULL_TIP - 0.032 - 0.3
    assert (depth, chamferLow, chamferHigh) == pytest.approx((0.3, FULL_TIP - 0.032 - cut, FULL_TIP - 0.088 - cut))


# Round 50, decided option a: a compartment corner beside a ridge is rounded only as far as what covers it from above
def test_a_corner_fillet_within_both_cover_strips_keeps_its_radius():
    assert raised.coveredCornerRadius(0.255, 0.28, 0.3) == pytest.approx(0.255)


def test_a_corner_fillet_is_limited_to_what_its_two_strips_cover():
    # a ridge's 1.97 mm on one side, a full lip's support 1.4 mm on the other
    radius = raised.coveredCornerRadius(1.0, 0.197, 0.14)
    assert radius == pytest.approx(0.197 + 0.14 + (2 * 0.197 * 0.14) ** 0.5)
    # the fillet's farthest point from both faces then lies on the corner of the strips
    assert (radius - 0.197) ** 2 + (radius - 0.14) ** 2 == pytest.approx(radius ** 2)


def test_a_corner_with_one_strip_only_gets_that_strip():
    assert raised.coveredCornerRadius(0.255, 0.077, 0) == pytest.approx(0.077)
    assert raised.coveredCornerRadius(0.255, 0, 0) == 0


# Review round 50: the ridge's straight face under its tip reaches down at least to where the cavities' top is cut,
# else the compartments top clearance left a shelf at a scoop on the ridge (light lip, 0.5 mm) or a level face
def test_the_ridge_tip_reaches_down_to_the_cut_cavity_top():
    assert raised.ridgeTipDepth(isFullLip=True, clearanceDepth=0.05, supportWall=0.12) == pytest.approx(0.12)
    # a little below the cut top, an edge on it made Fusion's combines fail (ASM_EDGECOIN_PROBLEM, shown in Fusion)
    assert raised.ridgeTipDepth(isFullLip=True, clearanceDepth=0.2, supportWall=0.12) == pytest.approx(0.2 + raised.RIDGE_TIP_MARGIN)
    assert raised.ridgeTipDepth(isFullLip=False, clearanceDepth=0.05, supportWall=0.12) == pytest.approx(0.05 + raised.RIDGE_TIP_MARGIN)
    assert raised.ridgeTipDepth(isFullLip=False, clearanceDepth=0, supportWall=0.12) == 0
    assert raised.RIDGE_TIP_MARGIN > 0


# Review round 50: a corner between two faces at the lip's or ridge's tip, an outer scoop wall or a scoop on a ridge,
# follows the rounded corner the feet leave above it, like p653
def test_a_corner_between_two_tip_faces_follows_the_lip():
    assert raised.cornerRadiusBetween(0.255, raised.TIP, raised.TIP, tipCorner=0.14) == pytest.approx(0.14)
    # one tip face and a covering strip: the strip alone
    assert raised.cornerRadiusBetween(0.255, raised.TIP, 0.197, tipCorner=0.14) == pytest.approx(0.197)
    assert raised.cornerRadiusBetween(0.255, 0.197, 0.14, tipCorner=0.14) == pytest.approx(raised.coveredCornerRadius(0.255, 0.197, 0.14))


# Review round 50: a corner between two tip faces beside a ridge is filled up from the cut cavity top to the body top,
# else the compartments top clearance cut its rounding flat (0.29 mm2 ledges, shown in Fusion)
def test_the_corners_between_two_tip_faces_beside_a_ridge_are_filled():
    covers = {'left': raised.TIP, 'right': 0.2, 'front': raised.TIP, 'back': raised.TIP}
    assert raised.tipCornersBesideRidge(covers, frozenset({'front', 'back'})) == [('left', 'front'), ('left', 'back')]
    # two outer scoop walls, no ridge: the top clearance's own corner takes it (p653)
    assert raised.tipCornersBesideRidge(covers, frozenset()) == []


# Re-review round 50: a tab reaching back behind the ridge's tip starts its sloped top higher by as much, so the top is
# where the label and pocket expect it at the tip
def test_a_tab_reaching_back_starts_its_sloped_top_higher():
    import math
    assert raised.tabTopRise(0.25, 0) == 0
    assert raised.tabTopRise(0.25, math.radians(15)) == pytest.approx(0.25 * math.tan(math.radians(15)))
