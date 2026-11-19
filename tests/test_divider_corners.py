"""
Tests for the corners beside raised dividers (p83, round 50): which cell corners are rounded up to the
top, which edges of the finished bin they are rounded along, and the path those edges make.
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
Segment = raised.DividerSegment


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
    # 2x2, only the column divider at line 1 rises, over both rows, the row divider at line 1 stays down
    segments = [Segment('x', 1, 0, 2)]
    corners = raised.filletCorners(segments, 2, 2)
    # so the crossing gets nothing, only the ends against the front and back walls
    assert all(not (corner.column in (0, 1) and corner.row == 0 and corner.sideY == 1) for corner in corners)
    assert all(not (corner.row == 1 and corner.sideY == -1) for corner in corners)
    assert len(corners) == 4


def test_no_fillet_without_raised_dividers():
    assert raised.filletCorners([], 3, 2) == []



# Round 50: the edges a corner is rounded along no longer lie in one plane, the lip runs out of the wall's face into
# the cell, the divider's top back to its middle. Lengths in mm here, the code is unit free. Full 2x3x5 as measured in
# Fusion 19.11.2026: body top 16.0, the 1.2 mm divider 1 with its middle on grid line x 41.75 and its low face at
# 41.15, front wall on grid line y 0 (outer face 0.25) with its inner face at 1.45, the lip 2.15 from its grid line at
# its widest, the untrimmed lip's top at 20.4, the divider's roof from 19.8 to its ridge there
CORNER = Corner(0, 0, 1, -1)  # cell 0, its high x side against divider 1, low y side against the front wall
CORNER_AT = (41.15, 1.45)
LINES = (41.75, 0.0)


def edge(start, end, corner=CORNER, at=CORNER_AT, lines=LINES):
    return raised.isCornerEdge(corner, at, lines, reach=2.15, bottomZ=15.5, start=start, end=end)


def test_corner_edges_run_up_the_faces_the_lip_and_the_roof():
    # up the corner of the two faces, along the divider's face up the lip's chamfer and straight part, then up the roof
    assert edge((41.15, 1.45, 15.5), (41.15, 1.45, 16.7))
    assert edge((41.15, 1.45, 16.7), (41.15, 2.15, 17.4))
    assert edge((41.15, 2.15, 17.4), (41.15, 2.15, 18.5))
    assert edge((41.15, 2.15, 18.5), (41.15, 1.55, 19.1))
    assert edge((41.15, 1.55, 19.1), (41.75, 0.95, 19.7))


def test_corner_edges_leave_level_edges_along_the_divider_or_the_wall():
    assert not edge((41.15, 1.45, 15.5), (41.15, 30.0, 15.5))
    assert not edge((41.15, 2.15, 18.5), (41.15, 30.0, 18.5))
    assert not edge((41.75, 0.95, 19.7), (41.75, 0.95 + 1e-6, 19.7))


def test_corner_edges_start_at_the_top_of_the_corner_below():
    assert not edge((41.15, 1.45, 3.55), (41.15, 1.45, 15.5))


def test_corner_edges_stay_on_the_corners_side_of_the_dividers_middle_and_the_wall_line():
    # the other cell's corner beyond the divider, a corner further along the divider
    assert not edge((42.35, 1.45, 15.5), (42.35, 1.45, 16.95))
    assert not edge((41.15, 30.0, 15.5), (41.15, 30.0, 16.95))
    # the roof's ridge lies on the divider's middle, the lip's top reaches back to the wall's grid line
    assert edge((41.15, 0.65, 19.8), (41.75, 0.025, 20.4))
    assert not edge((41.75, 0.65, 19.8), (41.80, 0.6, 20.4))


def test_corner_edges_of_the_corner_across_the_divider():
    across = Corner(1, 0, -1, -1)
    assert raised.isCornerEdge(across, (42.35, 1.45), LINES, reach=2.15, bottomZ=15.5, start=(42.35, 1.45, 15.5), end=(42.35, 1.45, 16.95))
    assert not raised.isCornerEdge(across, (42.35, 1.45), LINES, reach=2.15, bottomZ=15.5, start=(41.15, 1.45, 15.5), end=(41.15, 1.45, 16.95))


# The edges of a corner as a path to sweep its section along (p83, hand test): from the top of the corner below up,
# edges as start and end points, the last coordinate the height. Points in the plane of the face as before, or in 3D
def test_chain_path_runs_bottom_up_whatever_order_and_direction():
    edges = [((1.2, 16.0), (1.2, 15.5)), ((1.9, 18.6), (1.9, 16.7)), ((1.9, 16.7), (1.2, 16.0)), ((0.7, 19.8), (1.9, 18.6))]
    assert raised.chainPath(edges) == [0, 2, 1, 3]


def test_chain_path_in_3d_up_the_mitre():
    edges = [((40.3, 1.45, 17.8), (39.6, 2.15, 18.5)), ((41.15, 1.45, 15.5), (41.15, 1.45, 16.95)),
             ((39.6, 2.15, 18.6), (40.9, 0.85, 19.8)), ((41.15, 1.45, 16.95), (40.3, 1.45, 17.8)),
             ((39.6, 2.15, 18.5), (39.6, 2.15, 18.6))]
    assert raised.chainPath(edges) == [1, 3, 0, 4, 2]
    assert raised.chainRuns(edges) == [[1, 3, 0, 4, 2]]


def test_chain_path_of_a_broken_chain_is_none():
    # a wall thicker than the lip leaves a level ledge between wall and lip, which is no part of the chain
    edges = [((2.0, 15.5), (2.0, 16.0)), ((1.9, 16.0), (1.9, 18.6))]
    assert raised.chainPath(edges) is None


def test_chain_path_of_a_crossing_is_its_edge():
    assert raised.chainPath([((30.0, 19.8), (30.0, 15.5))]) == [0]


# Round 12: upstream v2.4.0.0 lowers the lip socket by the clearance times (sqrt(2) - 1), the lip's inner face then
# ends in an edge rising 3.55 um to the top. The generator works in cm, where the old 1e-3 counted it as level and the
# corner's sweep stopped short of the top: ledges of 1.40 mm2, 3.55 um deep, found by the shape tests in Fusion
CM_AT = (4.1433, 0.12)


def chain_cm(start, end):
    return raised.isCornerEdge(CORNER, CM_AT, (4.2033, 0.0), reach=0.215, bottomZ=1.55, start=start, end=end)


def test_chain_takes_the_last_few_microns_of_the_lip_in_cm():
    assert chain_cm((4.1433, 0.07, 1.979645), (4.1433, 0.07, 1.98))
    # still no level edge
    assert not chain_cm((4.1433, 0.07, 1.98), (4.1433, 8.28, 1.98))


def test_chain_path_runs_up_to_the_top_through_the_last_few_microns_in_cm():
    edges = [((0.12, 1.6), (0.12, 1.55)), ((0.19, 1.86), (0.19, 1.67)), ((0.19, 1.67), (0.12, 1.6)),
             ((0.07, 1.979645), (0.19, 1.86)), ((0.07, 1.979645), (0.07, 1.98))]
    assert raised.chainPath(edges) == [0, 2, 1, 3, 4]


@pytest.mark.parametrize("noise", [5e-7, 5e-6])
def test_chain_keeps_float_noise_of_the_kernel_level_in_cm(noise):
    # review round 12: Fusion's point resolution is about 1e-6 cm, an edge meant level may rise that much
    assert not chain_cm((4.1433, 0.07, 1.98), (4.1433, 0.19, 1.98 + noise))


def test_chain_path_takes_a_few_microns_in_the_middle_in_cm():
    # edges joined at a vertex of the body share its point exactly, so a short edge in the middle joins up as well:
    # with a join tolerance of 10 um it was ambiguous, the corner fell back to a fillet Fusion couldn't make
    edges = [((0.12, 1.6), (0.12, 1.55)), ((0.12, 1.6), (0.12, 1.600355)), ((0.12, 1.600355), (0.19, 1.67))]
    assert raised.chainPath(edges) == [0, 1, 2]


def test_chain_path_up_the_mitre_through_a_step_of_a_few_microns():
    # Fusion 19.11.2026, corner of a divider at the front wall in cm: the lip's top face lies 4 um off the stacked
    # feet's, a corner's path has an edge of 7 um there
    mm = [((41.150, 2.596, 30.000), (41.150, 2.596, 29.500)), ((41.150, 1.900, 30.696), (41.150, 2.596, 30.000)),
          ((41.150, 1.900, 30.950), (41.150, 1.900, 30.696)), ((39.604, 1.900, 32.496), (41.150, 1.900, 30.950)),
          ((39.600, 0.596, 33.800), (39.600, 1.896, 32.500)), ((39.600, 1.896, 32.500), (39.604, 1.900, 32.496))]
    edges = [tuple(tuple(v / 10 for v in point) for point in edge) for edge in mm]
    assert raised.chainRuns(edges) == [[0, 1, 2, 3, 5, 4]]


# p101 (round 15): a wall thicker than the lip leaves a level ledge between the corner's edges, measured in Fusion
# 15.11.2026 at a 3 mm wall, (other axis, z) in mm: the wall's face up to the ledge, the lip's face above it. Each run is
# swept on its own

LEDGE_3MM = [
    ((1.5, 18.896), (1.9, 18.496)),
    ((1.5, 18.896), (1.5, 19.8)),
    ((1.9, 18.496), (1.9, 16.0)),
    ((3.0, 16.0), (3.0, 15.5)),
]


def test_a_ledge_splits_the_chain_in_two_runs():
    assert raised.chainRuns(LEDGE_3MM) == [[3], [2, 0, 1]]


def test_one_run_without_a_ledge():
    edges = [((30.0, 15.5), (30.0, 16.0)), ((30.0, 16.0), (29.1, 16.9)), ((29.1, 16.9), (29.1, 19.8))]
    assert raised.chainRuns(edges) == [[0, 1, 2]]


def test_a_branching_chain_has_no_runs():
    edges = [((1.0, 0.0), (1.0, 1.0)), ((1.0, 1.0), (1.0, 2.0)), ((1.0, 1.0), (2.0, 1.5))]
    assert raised.chainRuns(edges) is None


def test_three_runs_up_a_double_ledge():
    edges = [((3.0, 15.5), (3.0, 16.0)), ((2.5, 16.0), (2.5, 17.0)), ((1.9, 17.0), (1.9, 19.8))]
    assert raised.chainRuns(edges) == [[0], [1], [2]]


def test_runs_that_dont_meet_at_a_ledge_are_no_runs():
    # a stray edge beside the chain, overlapping it in height: filleted as before, not swept on its own
    edges = [((3.0, 15.5), (3.0, 16.0)), ((1.9, 16.0), (1.9, 19.8)), ((5.0, 17.0), (5.0, 18.0))]
    assert raised.chainRuns(edges) is None


def test_runs_at_one_spot_are_no_ledge():
    # a gap in height with no step aside isn't a ledge
    edges = [((3.0, 15.5), (3.0, 16.0)), ((3.0, 16.5), (3.0, 19.8))]
    assert raised.chainRuns(edges) is None


def test_the_run_above_the_ledge_moves_over_by_it_and_up_to_it():
    runs = raised.chainRuns(LEDGE_3MM)
    assert raised.runOffset(LEDGE_3MM, runs, 0) == (0, 0)
    (shift, rise) = raised.runOffset(LEDGE_3MM, runs, 1)
    assert shift == pytest.approx(1.9 - 3.0)
    assert rise == pytest.approx(16.0 - 15.5)



# Round 50: beside a full lip's support the corner starts lower, where the support leaves the wall's face, and its path
# goes up the support's corner: 45 degrees out by the support's depth, then straight up to the top of the corner below.
# (along the wall's normal into the cell, z), cm, measured in Fusion: support 1.4 mm deep, turning out 1.2 mm under the
# body top at 3.0, the corner below ending 0.5 mm under it
def flat(points):
    return [value for point in points for value in point]


def test_support_path_runs_out_at_45_degrees_then_up():
    assert flat(raised.supportCornerPath(0.14, supportTopZ=2.88, bottomZ=2.95)) == pytest.approx(flat([(0, 2.74), (0.14, 2.88), (0.14, 2.95)]))


def test_support_path_without_a_straight_part_when_the_corner_below_ends_lower():
    # a tab top offset deeper than the support's straight part: the corner below ends on its 45 degree part, its edges
    # start 0.6 mm out from the wall there
    assert flat(raised.supportCornerPath(0.06, supportTopZ=2.88, bottomZ=2.8)) == pytest.approx(flat([(0, 2.74), (0.06, 2.8)]))


# Review round 50: a wall thicker than the lip's reach has its face further from its grid line than the lip reaches
# into the cell; the corner's edges up that face belong to the chain too, else the corner was filleted and stayed sharp
# from the corner below up to the ledge. Light lip, a 3 mm wall: its face 3.25 mm from the grid line, the lip 2.15 mm
def test_corner_edges_up_a_thick_walls_face():
    corner = Corner(0, 0, 1, -1)
    at = (41.15, 3.25)
    assert raised.isCornerEdge(corner, at, LINES, reach=2.15, bottomZ=15.5, start=(41.15, 3.25, 15.5), end=(41.15, 3.25, 16.0))
    # still nothing beyond the face into the cell
    assert not raised.isCornerEdge(corner, at, LINES, reach=2.15, bottomZ=15.5, start=(41.15, 3.4, 15.5), end=(41.15, 3.4, 16.0))
