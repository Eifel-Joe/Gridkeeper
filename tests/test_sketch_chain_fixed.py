"""
Round 39 (p480): the chain fixes a point whose sketch coordinates are plain numbers instead of binding it with two
dimensions. Every dimension is a model parameter of the document, and Fusion's calls get dearer with each parameter in
it (fusion-auftraege/r39_probe2.log: an expression 7.5 ms with 900 fixed points, 107 ms with 900 dimensions); a fixed
point is no parameter. Points that hang on a box parameter keep their dimensions.
"""

import math

from tests.test_joint_origin_layout import _load
from tests.test_sketch_chain import arc, circle, line, rectangle, rounded

plan = _load("sketchChain")


def check(points, curves, constraints):
    """Exactly determined with fixed points counted as two conditions, no zero dimension"""
    assert plan.rank(points, curves, constraints) == plan.variableCount(points, curves)
    weight = sum(2 if c[0] in ("originAt", "fixed") else 1 for c in constraints)
    assert weight == plan.variableCount(points, curves) - plan.inherentCount(curves)
    assert {c[0] for c in constraints} <= {"horizontal", "vertical", "hdim", "vdim", "diameter", "originAt", "fixed"}
    for c in constraints:
        if c[0] in ("hdim", "vdim"):
            axis = 0 if c[0] == "hdim" else 1
            other = 0.0 if c[2] is None else points[c[2]][axis]
            assert abs(points[c[1]][axis] - other) > 1e-9, "zero dimension"


def fixed(constraints):
    return sorted(c[1] for c in constraints if c[0] == "fixed")


def test_nothing_fixable_gives_todays_plan():
    for points, curves in [rectangle(1, 1, 3, 2), rounded(0, 0, 23, 18.8, 1.4), rectangle(0, 0, 3, 2)]:
        assert plan.chain(points, curves, frozenset()) == plan.chain(points, curves)


def test_a_polygon_of_plain_numbers_is_all_fixed():
    points = [(3.1, 0.2), (4.915, 0.2), (4.985, 0.07), (4.985, 0.25), (5.15, 0.415), (3.1, 0.415)]
    curves = [line(i, (i + 1) % 6) for i in range(6)]
    constraints = plan.chain(points, curves, frozenset(range(6)))
    check(points, curves, constraints)
    assert fixed(constraints) == list(range(6))
    assert all(c[0] == "fixed" for c in constraints)


def test_a_level_line_end_is_fixed_only_beside_a_fixable_neighbour():
    points, curves = rectangle(1, 1, 3, 2)
    # 0 is the anchor; 1 is level with it. Fixable both: fixed, no condition on the line
    constraints = plan.chain(points, curves, frozenset({0, 1}))
    check(points, curves, constraints)
    assert fixed(constraints) == [0, 1]
    assert ("horizontal", 0) not in constraints
    # the neighbour hangs on a parameter: the line keeps its condition and the end its one dimension
    constraints = plan.chain(points, curves, frozenset({1}))
    check(points, curves, constraints)
    assert 1 not in fixed(constraints)
    assert ("horizontal", 0) in constraints


def arcPoints(curves):
    return {c[k] for c in curves if c["kind"] == "arc" for k in ("center", "start", "end")}


def test_arc_ends_and_centres_are_never_fixed():
    """Fusion rejected a fixed-point plan around four concentric arcs (LidAlignmentFront) as over-constrained, though
    exact by rank (fusion-auftraege/r39_front.log: the second arc's end dimension); without fixed points on the arcs the
    same sketch is fully constrained. Arc points keep their dimensions as before round 39"""
    cx = cy = 1.4
    points = [(cx, cy), (cx - 1.075, cy), (cx, cy - 1.075), (cx, cy - 0.825), (cx - 0.825, cy)]
    curves = [arc(0, 1, 2), line(2, 3), arc(0, 3, 4), line(4, 1)]
    constraints = plan.chain(points, curves, frozenset(range(5)))
    check(points, curves, constraints)
    assert fixed(constraints) == []
    assert constraints == plan.chain(points, curves)


def test_the_lid_alignment_front_fixes_only_points_off_the_arcs():
    """predBoxGenerator.lidAndHinge, LidAlignmentFront (mm): two rectangles, four arcs about (14, 14), the lines on
    the arcs' ends"""
    points, index, curves = [], {}, []

    def p(x, y):
        key = (round(x, 6), round(y, 6))
        if key not in index:
            index[key] = len(points)
            points.append((x / 10, y / 10))
        return index[key]

    def poly(ps, closed):
        for a, b in zip(ps, ps[1:] + (ps[:1] if closed else [])):
            curves.append(line(p(*a), p(*b)))
    poly([(46.5, 3.25), (52.5, 3.25), (52.5, 6.75), (46.5, 6.75)], True)
    poly([(47, 3.75), (52, 3.75), (52, 6.25), (47, 6.25)], True)
    for r in (8.75, 9.25, 10.75, 11.25):
        curves.append(arc(p(14, 14), p(14 - r, 14), p(14, 14 - r)))
    poly([(14, 2.75), (14, 3.25), (14, 4.75), (14, 5.25)], False)
    poly([(2.75, 14), (3.25, 14), (4.75, 14), (5.25, 14)], False)
    poly([(14, 5.25), (14.5, 5.25), (14.5, 2.75), (14, 2.75)], False)
    poly([(5.25, 14), (5.25, 14.5), (2.75, 14.5), (2.75, 14)], False)
    constraints = plan.chain(points, curves, frozenset(range(len(points))))
    check(points, curves, constraints)
    assert not set(fixed(constraints)) & arcPoints(curves)
    assert len(fixed(constraints)) >= 8


def test_a_centre_on_the_chord_of_two_known_ends_keeps_its_dimension():
    # the line's two ends first, then the arc between them: its centre has one degree of freedom left
    r = 1.0
    points = [(2.0, 1.0), (4.0, 1.0), (3.0, 1.0)]
    curves = [line(0, 1), arc(2, 1, 0)]
    constraints = plan.chain(points, curves, frozenset({0, 1, 2}))
    check(points, curves, constraints)
    # the line's ends are the arc's: none fixed, the chain as before
    assert fixed(constraints) == []


def test_a_circle_centre_is_fixed_and_keeps_its_diameter():
    points = [(0.375, 2.47)]
    curves = [circle(0), circle(0)]
    constraints = plan.chain(points, curves, frozenset({0}))
    check(points, curves, constraints)
    assert sorted(c[0] for c in constraints) == ["diameter", "diameter", "fixed"]


def test_an_anchor_on_the_origin_stays_on_it():
    points, curves = rectangle(0, 0, 3, 2)
    constraints = plan.chain(points, curves, frozenset(range(4)))
    check(points, curves, constraints)
    assert ("originAt", 0) in constraints
    assert fixed(constraints) == [1, 2, 3]


def test_a_shape_half_fixable_stays_determined():
    points, curves = rounded(0, 0, 23, 18.8, 1.4)
    constraints = plan.chain(points, curves, frozenset(range(0, 12, 2)))
    check(points, curves, constraints)


def test_fixed_counts_two_rows_in_the_rank():
    points = [(1.0, 2.0)]
    assert plan.rank(points, [], [("fixed", 0)]) == 2
