"""
Tests for the constraint chain of the box sketches (round 27, task 3b, Jörg: "Ja, Formen-Weg"). A rank picking plan
was rejected by Fusion (fusion-auftraege/r27_sketches2/3.out); the chain fixes the points one after another like
sketchUtils.createRectangle: a shape's first point from the origin, every further point with exactly two dimensions to
points already fixed, real horizontal/vertical lines with that condition instead of a dimension. Never a dimension of
zero, never an alignment to the origin, never a tangency.
"""

import math

from tests.test_joint_origin_layout import _load

plan = _load("sketchChain")


def line(a, b):
    return {"kind": "line", "a": a, "b": b}


def arc(center, start, end):
    return {"kind": "arc", "center": center, "start": start, "end": end}


def circle(center):
    return {"kind": "circle", "center": center}


def check(points, curves, constraints):
    """Exactly determined, no zero dimension, only the kinds of conditions the chain may use"""
    assert plan.rank(points, curves, constraints) == plan.variableCount(points, curves)
    weight = sum(2 if c[0] == "originAt" else 1 for c in constraints)
    assert weight == plan.variableCount(points, curves) - plan.inherentCount(curves)
    assert {c[0] for c in constraints} <= {"horizontal", "vertical", "hdim", "vdim", "diameter", "originAt"}
    for c in constraints:
        if c[0] in ("horizontal", "vertical"):
            (ax, ay), (bx, by) = points[curves[c[1]]["a"]], points[curves[c[1]]["b"]]
            assert abs((ay - by) if c[0] == "horizontal" else (ax - bx)) < 1e-9
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
    constraints = plan.chain(points, curves)
    check(points, curves, constraints)
    kinds = sorted(c[0] for c in constraints)
    assert kinds == ["hdim", "hdim", "hdim", "horizontal", "horizontal", "vdim", "vdim", "vertical"]


def test_rectangle_on_the_origin_starts_there():
    points, curves = rectangle(0, 0, 3, 2)
    constraints = plan.chain(points, curves)
    check(points, curves, constraints)
    assert ("originAt", 0) in constraints


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
    check(points, curves, plan.chain(points, curves))


def test_two_shapes_each_get_their_own_anchor():
    p1, c1 = rounded(0, 0, 23, 18.8, 1.4)
    p2, c2 = rounded(1, 1, 22, 17.8, 0.4)
    points = p1 + p2
    curves = c1 + [dict(c, **{k: v + 12 for k, v in c.items() if k != "kind"}) for c in c2]
    check(points, curves, plan.chain(points, curves))


def test_circles_in_a_rectangle():
    points, curves = rectangle(1, 1, 5, 3)
    points = points + [(2, 2), (4, 2)]
    curves = curves + [circle(4), circle(5)]
    check(points, curves, plan.chain(points, curves))


def test_concentric_circles_share_their_center():
    """A shape of a single point has nothing else to hang on, it gets both origin dimensions (probe2 V3/V6 took that)"""
    points = [(0.375, 2.47)]
    curves = [circle(0), circle(0), circle(0)]
    constraints = plan.chain(points, curves)
    check(points, curves, constraints)
    assert sorted(c[0] for c in constraints) == ["diameter", "diameter", "diameter", "hdim", "vdim"]


def test_polygon_with_slanted_lines():
    # Pred's sweep profile, lower region (cm)
    points = [(3.1, 0), (4.915, 0), (4.985, 0.07), (4.985, 0.25), (5.15, 0.415), (3.1, 0.415)]
    curves = [line(i, (i + 1) % 6) for i in range(6)]
    check(points, curves, plan.chain(points, curves))


def test_arc_tangent_to_a_slanted_line():
    # the lid lip: 45 degree line into a 0.5 mm arc, then a horizontal line from the arc's top (cm)
    r = 0.05
    c = (5.125, 5.0143)
    t = (c[0] - r / math.sqrt(2), c[1] + r / math.sqrt(2))
    points = [(4.985, t[1] - (t[0] - 4.985)), t, c, (c[0], c[1] + r), (5.2, c[1] + r), (5.2, 5.22), (3.1, 5.22), (3.1, 4.9)]
    curves = [line(0, 1), arc(2, 1, 3), line(3, 4), line(4, 5), line(5, 6), line(6, 7), line(7, 0)]
    check(points, curves, plan.chain(points, curves))


def test_quarter_ring_with_two_arcs():
    # stacking tab: arcs around (1.4, 1.4) with 1.075 and 0.825 cm, closed by two lines
    cx = cy = 1.4
    points = [(cx, cy), (cx - 1.075, cy), (cx, cy - 1.075), (cx, cy - 0.825), (cx - 0.825, cy)]
    curves = [arc(0, 1, 2), line(2, 3), arc(0, 3, 4), line(4, 1)]
    check(points, curves, plan.chain(points, curves))


def test_points_on_the_axes_get_no_zero_dimension():
    # the side groove triangle starts on the wall x = 0 of the sketch
    points = [(0.0, 0.82), (0.0, 0.62), (0.1, 0.72)]
    curves = [line(0, 1), line(1, 2), line(2, 0)]
    check(points, curves, plan.chain(points, curves))


def test_floor_pad_with_blends_and_magnet():
    # Pred's pad in the first cell corner: pad arc r 4, blends r 5.05 to the floor edges, magnet circle (cm)
    R, b, e0 = 0.4, 0.505, 1.285
    px = py = e0 + b
    points = [(px, py), (px + R, py), (px, py + R), (px + R + b, py), (px + R + b, py - b), (px, py + R + b),
              (px - b, py + R + b), (e0, e0 + 0.115), (e0 + 0.115, e0), (e0 + 0.115, e0 + 0.115)]
    curves = [arc(0, 1, 2), arc(3, 1, 4), arc(5, 2, 6), circle(0), line(4, 8), arc(9, 8, 7), line(7, 6)]
    check(points, curves, plan.chain(points, curves))
