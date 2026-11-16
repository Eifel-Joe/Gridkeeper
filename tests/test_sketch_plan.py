"""
Tests for the constraint plan of the box sketches (round 27, task 3b, Jörg: "Ja, Formen-Weg"): lines get
horizontal/vertical conditions, arcs tangency, each shape one anchor, then lengths, until every degree of freedom is
bound exactly once. Fusion rejected sketches whose points were each dimensioned to the origin (fusion-auftraege/
r27_probe*.out), so the plan never puts two dimensions between the same two points, never both origin dimensions on
one point and never a zero dimension.
"""

import math

from tests.test_joint_origin_layout import _load

plan = _load("sketchPlan")


def line(a, b):
    return {"kind": "line", "a": a, "b": b}


def arc(center, start, end):
    return {"kind": "arc", "center": center, "start": start, "end": end}


def circle(center):
    return {"kind": "circle", "center": center}


def check(points, curves, constraints):
    """Exactly determined, and the three rules Fusion needs"""
    assert plan.rank(points, curves, constraints) == plan.variableCount(points, curves)
    assert len(constraints) == plan.variableCount(points, curves) - plan.inherentCount(curves)
    pairs = [frozenset((c[1], c[2])) for c in constraints if c[0] in ("hdim", "vdim")]
    assert len(pairs) == len(set(pairs)), "two dimensions between the same two points"
    originPoints = [c[1] for c in constraints if c[0] in ("hdim", "vdim") and c[2] is None]
    assert len(originPoints) == len(set(originPoints)), "both origin dimensions on one point"
    for c in constraints:
        if c[0] in ("hdim", "vdim"):
            axis = 0 if c[0] == "hdim" else 1
            other = 0.0 if c[2] is None else points[c[2]][axis]
            assert abs(points[c[1]][axis] - other) > 1e-9, "zero dimension"


def rectangle(x0, y0, x1, y1, offset=0):
    points = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    curves = [line(offset + i, offset + (i + 1) % 4) for i in range(4)]
    return points, curves


def test_rectangle_like_create_rectangle():
    points, curves = rectangle(1, 1, 3, 2)
    constraints = plan.planConstraints(points, curves)
    check(points, curves, constraints)
    kinds = sorted(c[0] for c in constraints)
    assert kinds == ["hdim", "hdim", "horizontal", "horizontal", "vdim", "vdim", "vertical", "vertical"]


def test_rectangle_on_the_origin_lies_on_it():
    points, curves = rectangle(0, 0, 3, 2)
    constraints = plan.planConstraints(points, curves)
    check(points, curves, constraints)
    assert ("originOnLine", 0, "horizontal") in constraints and ("originOnLine", 3, "vertical") in constraints


def rounded(x0, y0, x1, y1, r):
    points = [
        (x0 + r, y0 + r), (x0, y0 + r), (x0 + r, y0),
        (x1 - r, y0 + r), (x1 - r, y0), (x1, y0 + r),
        (x1 - r, y1 - r), (x1, y1 - r), (x1 - r, y1),
        (x0 + r, y1 - r), (x0 + r, y1), (x0, y1 - r),
    ]
    curves = []
    for k in range(4):
        c, s, e = 3 * k, 3 * k + 1, 3 * k + 2
        curves.append(arc(c, s, e))
        curves.append(line(e, 3 * ((k + 1) % 4) + 1))
    return points, curves


def test_rounded_rectangle():
    points, curves = rounded(0, 0, 23, 18.8, 1.4)
    constraints = plan.planConstraints(points, curves)
    check(points, curves, constraints)
    assert len([c for c in constraints if c[0] == "tangent"]) == 8


def test_two_shapes_each_get_their_own_anchor():
    p1, c1 = rounded(0, 0, 23, 18.8, 1.4)
    p2, c2 = rounded(1, 1, 22, 17.8, 0.4)
    points = p1 + p2
    curves = c1 + [dict(c, **{k: v + 12 for k, v in c.items() if k != "kind"}) for c in c2]
    check(points, curves, plan.planConstraints(points, curves))


def test_circles_in_a_rectangle():
    points, curves = rectangle(1, 1, 5, 3)
    points = points + [(2, 2), (4, 2)]
    curves = curves + [circle(4), circle(5)]
    check(points, curves, plan.planConstraints(points, curves))


def test_concentric_circles_share_their_center():
    """A shape of a single point has nothing else to hang on, it gets both origin dimensions (probe2 V3/V6 took that)"""
    points = [(0.375, 2.47)]
    curves = [circle(0), circle(0), circle(0)]
    constraints = plan.planConstraints(points, curves)
    assert plan.rank(points, curves, constraints) == plan.variableCount(points, curves) == len(constraints)
    assert sorted(c[0] for c in constraints) == ["diameter", "diameter", "diameter", "hdim", "vdim"]


def test_polygon_with_slanted_lines():
    # Pred's sweep profile, lower region (cm)
    points = [(3.1, 0), (4.915, 0), (4.985, 0.07), (4.985, 0.25), (5.15, 0.415), (3.1, 0.415)]
    curves = [line(i, (i + 1) % 6) for i in range(6)]
    check(points, curves, plan.planConstraints(points, curves))


def test_arc_tangent_to_a_slanted_line():
    # the lid lip: 45 degree line into a 0.5 mm arc, then a horizontal line from the arc's top (cm)
    r = 0.05
    c = (5.125, 5.0143)
    t = (c[0] - r / math.sqrt(2), c[1] + r / math.sqrt(2))
    points = [(4.985, t[1] - (t[0] - 4.985)), t, c, (c[0], c[1] + r), (5.2, c[1] + r), (5.2, 5.22), (3.1, 5.22), (3.1, 4.9)]
    curves = [line(0, 1), arc(2, 1, 3), line(3, 4), line(4, 5), line(5, 6), line(6, 7), line(7, 0)]
    constraints = plan.planConstraints(points, curves)
    check(points, curves, constraints)
    assert ("tangent", 1, 0) in constraints


def test_quarter_ring_with_two_arcs():
    # stacking tab: arcs around (1.4, 1.4) with 1.075 and 0.825 cm, closed by two lines
    cx = cy = 1.4
    points = [(cx, cy), (cx - 1.075, cy), (cx, cy - 1.075), (cx, cy - 0.825), (cx - 0.825, cy)]
    curves = [arc(0, 1, 2), line(2, 3), arc(0, 3, 4), line(4, 1)]
    check(points, curves, plan.planConstraints(points, curves))
