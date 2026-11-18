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


def test_an_arc_keeps_the_dimension_of_its_end_on_the_circle():
    cx = cy = 1.4
    points = [(cx, cy), (cx - 1.075, cy), (cx, cy - 1.075), (cx, cy - 0.825), (cx - 0.825, cy)]
    curves = [arc(0, 1, 2), line(2, 3), arc(0, 3, 4), line(4, 1)]
    constraints = plan.chain(points, curves, frozenset(range(5)))
    check(points, curves, constraints)
    # each arc's second end lies on its circle by one dimension, fixing it too would bind the arc twice
    assert len(fixed(constraints)) < 5
    assert any(c[0] in ("hdim", "vdim") for c in constraints)


def test_a_centre_on_the_chord_of_two_known_ends_keeps_its_dimension():
    # the line's two ends first, then the arc between them: its centre has one degree of freedom left
    r = 1.0
    points = [(2.0, 1.0), (4.0, 1.0), (3.0, 1.0)]
    curves = [line(0, 1), arc(2, 1, 0)]
    constraints = plan.chain(points, curves, frozenset({0, 1, 2}))
    check(points, curves, constraints)
    assert fixed(constraints) == [0, 1]


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
