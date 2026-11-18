"""
Pred's latch (Latch_Experimental) drawn in code, round 29 (17.11.2026: the parts are drawn in code, all sketches
must be fully constrained). Plan: dev-notes/r29/latch-plan.md.

Pred builds the left half and mirrors the finished body (Mirror1, with its fillets and chamfers) and patterns the slot
features (R-Pattern2, with two chamfers). Gridkeeper builds both halves and both slots directly (README round 29: no
mirroring of fillets or chamfers). The numbers below are Pred's, from fusion-auftraege/r29_walk/Latch_Experimental.json
(mm): the volume after each step of Pred's half.
"""

import ast
import math
import os
import sys

from tests.test_joint_origin_layout import _load


def _loadLatch():
    """The module with the Fusion types its modules name in annotations stood in for while loading"""
    modules = [sys.modules["adsk.core"], sys.modules["adsk.fusion"]]
    for module in modules:
        module.__getattr__ = lambda name: type(name, (), {})
    try:
        return _load("predLatch")
    finally:
        for module in modules:
            del module.__getattr__


latch = _loadLatch()
chainPlan = sys.modules["jointOriginLayoutTestPackage.sketchChain"]

SOURCE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "gridfinityUtils", "predLatch.py")

# Pred's half: volume after each step (mm3), walk JSON "after"
PRED_AFTER = {
    "Extrude1": 1323.98, "Extrude2": 1613.63, "Extrude5": 1656.63,
    "Fillet3": 1645.308, "Extrude6": 1605.288, "Extrude7": 1628.088, "Extrude3": 1633.188,
    "R-Pattern2": 1618.9912, "Extrude4": 1639.91, "Chamfer3": 1616.0345,
}
PRED_VOLUME = 3232.0691
EPS = 1e-6


# -- helpers ----------------------------------------------------------------------------------------------------------

def _inside(p, a, b):
    """p lies strictly inside the segment a-b"""
    cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    if abs(cross) > EPS:
        return False
    t = ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)
    return EPS < t < 1 - EPS


def _assertPlanar(segments):
    """No endpoint inside another segment, no doubled segment, no crossing: every meeting is at shared ends"""
    keys = set()
    for a, b in segments:
        key = tuple(sorted([tuple(round(v, 6) for v in a), tuple(round(v, 6) for v in b)]))
        assert key not in keys, f"doubled segment {key}"
        keys.add(key)
    points = {p for s in segments for p in s}
    for a, b in segments:
        for p in points:
            assert not _inside(p, a, b), f"{p} inside {a}-{b}"
    for i, (a, b) in enumerate(segments):
        for c, d in segments[i + 1:]:
            def side(p, q, r):
                return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
            s1, s2, s3, s4 = side(a, b, c), side(a, b, d), side(c, d, a), side(c, d, b)
            assert not (s1 * s2 < -EPS and s3 * s4 < -EPS), f"{a}-{b} crosses {c}-{d}"


def _chainCheck(lines, construction=(), circles=()):
    """The chain of WorldSketch binds every point: rank of the conditions = number of variables"""
    points = []
    index = {}

    def point(p):
        key = tuple(round(v, 6) for v in p)
        if key not in index:
            index[key] = len(points)
            points.append(p)
        return index[key]
    curves = [{"kind": "line", "a": point(a), "b": point(b)} for a, b in list(lines) + list(construction)]
    curves += [{"kind": "circle", "center": point(c)} for c, _ in circles]
    constraints = chainPlan.chain(points, curves)
    assert chainPlan.rank(points, curves, constraints) == chainPlan.variableCount(points, curves)
    weight = sum(2 if c[0] == "originAt" else 1 for c in constraints)
    assert weight == chainPlan.variableCount(points, curves)


def _area(box, others):
    """A profile's area: its box less the profiles lying inside it (the pockets in the big region)"""
    (x0, y0), (x1, y1) = box
    area = (x1 - x0) * (y1 - y0)
    for (a0, b0), (a1, b1) in others:
        if ((a0, b0), (a1, b1)) != box and x0 <= a0 and a1 <= x1 and y0 <= b0 and b1 <= y1 and (a0, b0, a1, b1) != (x0, y0, x1, y1):
            area -= (a1 - a0) * (b1 - b0)
    return area


def _rank(rows):
    rows = [list(r) for r in rows]
    rank = 0
    columns = len(rows[0])
    for c in range(columns):
        pivot = next((r for r in range(rank, len(rows)) if abs(rows[r][c]) > 1e-9), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for r in range(len(rows)):
            if r != rank:
                f = rows[r][c] / rows[rank][c]
                rows[r] = [x - f * y for x, y in zip(rows[r], rows[rank])]
        rank += 1
    return rank


# -- Sketch1: the footprint over the whole width -----------------------------------------------------------------------

def test_sketch1_is_symmetric_and_has_no_line_on_the_mirror_plane():
    lines = latch.sketch1Lines()
    keys = {tuple(sorted([tuple(round(v, 6) for v in a), tuple(round(v, 6) for v in b)])) for a, b in lines}
    for a, b in lines:
        mirrored = tuple(sorted([(round(-a[0], 6) + 0.0, round(a[1], 6)), (round(-b[0], 6) + 0.0, round(b[1], 6))]))
        assert mirrored in keys, (a, b)
        assert not (abs(a[0]) < EPS and abs(b[0]) < EPS), "line on x = 0"
    assert not any(abs(p[0]) < EPS for s in lines for p in s), "a point on x = 0 splits a line through the middle"


def test_sketch1_is_a_planar_graph():
    _assertPlanar(latch.sketch1Lines())


def test_sketch1_keeps_preds_outline():
    xs = [p[0] for s in latch.sketch1Lines() for p in s]
    ys = [p[1] for s in latch.sketch1Lines() for p in s]
    assert (min(xs), max(xs), min(ys), max(ys)) == (-9.8, 9.8, -36.5, 0.0)


def test_sketch1_is_fully_determined():
    _chainCheck(latch.sketch1Lines())


def test_sketch1_profiles_give_twice_preds_volume():
    boxes = [b for step in latch.SKETCH1_PROFILES.values() for b in step]
    heights = {"Extrude1": 7.0, "Extrude2": 2.5, "Extrude5": 2.0}
    before = {"Extrude1": 0.0, "Extrude2": PRED_AFTER["Extrude1"], "Extrude5": PRED_AFTER["Extrude2"]}
    for step, height in heights.items():
        volume = sum(_area(box, boxes) for box in latch.SKETCH1_PROFILES[step]) * height
        assert abs(volume - 2 * (PRED_AFTER[step] - before[step])) < 1e-6, step


# -- Sketch2: the side faces, both slots, the nose ---------------------------------------------------------------------

def test_sketch2_is_a_planar_graph():
    """The profile lines; Pred's construction line to the mid height crosses the slot's edge, which shapes no profile"""
    shape = latch.sketch2Shape()
    _assertPlanar(shape["lines"])
    points = {p for s in shape["lines"] for p in s}
    for a, b in shape["construction"]:
        for p in (a, b):
            assert not any(_inside(p, c, d) for c, d in shape["lines"]), f"construction end {p} inside a line"


def test_sketch2_has_preds_face_outline_as_its_own_lines():
    lines = {tuple(sorted(s)) for s in latch.sketch2Shape()["lines"]}
    corners = [(0.0, 0.0), (-36.5, 0.0), (-36.5, 7.0), (0.0, 7.0)]
    ys = sorted({p[0] for s in lines for p in s if abs(p[1]) < EPS})
    assert ys[0] == -36.5 and ys[-1] == 0.0
    for corner in corners:
        assert any(corner in s for s in lines), corner


def test_sketch2_holds_both_slots_ten_mm_apart():
    shape = latch.sketch2Shape()
    for shift in (0.0, -10.0):
        for y in (-7.1 + shift, -13.1 + shift):
            assert any(abs(a[0] - y) < EPS and abs(b[0] - y) < EPS for a, b in shape["lines"]), y


def test_sketch2_is_fully_determined():
    shape = latch.sketch2Shape()
    _chainCheck(shape["lines"], shape["construction"], [shape["circle"]])


def test_the_nose_chord_ends_on_the_circle_and_is_bound_by_four_conditions():
    """Horizontal, both ends on the circle, 1.4 mm from the centre: four independent conditions on its four coordinates"""
    shape = latch.sketch2Shape()
    (cy, cz), diameter = shape["circle"]
    (ay, az), (by, bz) = shape["chord"]
    r = diameter / 2
    assert diameter == 3.8 and (cy, cz) == (-33.7, 3.5)
    for y, z in ((ay, az), (by, bz)):
        assert abs(math.hypot(y - cy, z - cz) - r) < 1e-9
        assert abs(z - 2.1) < 1e-9
    rows = [
        [0, 1, 0, -1],                                  # horizontal
        [2 * (ay - cy), 2 * (az - cz), 0, 0],           # start on the circle
        [0, 0, 2 * (by - cy), 2 * (bz - cz)],           # end on the circle
        [0, -1, 0, 0],                                  # 1.4 below the centre
    ]
    assert _rank(rows) == 4


def test_slot_profiles_give_preds_volume_steps():
    """Per side and slot as Pred's: Extrude6 cut 1.45, Extrude7 1 back in, Extrude3 0.75 out"""
    steps = {"Extrude6": ("Fillet3", 1.45, -1), "Extrude7": ("Extrude6", 1.0, 1), "Extrude3": ("Extrude7", 0.75, 1)}
    for step, (previous, depth, sign) in steps.items():
        boxes = latch.SLOT_PROFILES[step]
        area = sum((b[1][0] - b[0][0]) * (b[1][1] - b[0][1]) for b in boxes)
        assert abs(sign * area * depth - 2 * (PRED_AFTER[step] - PRED_AFTER[previous])) < 1e-6, step


def test_nose_profile_gives_preds_extrude4():
    (_, _), diameter = latch.sketch2Shape()["circle"]
    r = diameter / 2
    d = 1.4
    segment = r * r * math.acos(d / r) - d * math.sqrt(r * r - d * d)
    assert abs((math.pi * r * r - segment) * 2.0 - (PRED_AFTER["Extrude4"] - PRED_AFTER["R-Pattern2"])) < 1e-3


# -- edges -------------------------------------------------------------------------------------------------------------

def _counts():
    return {step: [len(items) for _, _, items in latch.edgeSets(step)] for step in latch.EDGE_STEPS}


def test_edge_sets_cover_both_sides_and_both_slots():
    assert _counts() == {
        "Fillet1": [2], "Fillet2": [2], "Chamfer1": [24], "Fillet3": [5],
        "Chamfer5": [16], "Chamfer7": [40], "Chamfer6": [2], "Fillet4": [4],
        "Chamfer2": [3, 28], "Chamfer3": [70],
    }


def test_edge_sets_keep_preds_kinds_and_sizes():
    kinds = {step: [(kind, value) for kind, value, _ in latch.edgeSets(step)] for step in latch.EDGE_STEPS}
    assert kinds["Fillet1"] == [("fillet", 4.0)]
    assert kinds["Chamfer5"] == [("chamfer", 0.375)]
    assert kinds["Chamfer2"] == [("chamfer", 1.0), ("chamfer", 0.25)]
    assert kinds["Fillet4"] == [("fillet", 3.5)]


def test_a_line_ending_on_the_mirror_plane_joins_its_mirror_image():
    [(_, _, items)] = latch.edgeSets("Fillet3")
    lines = [i for i in items if i["kind"] == "line" and abs(i["start"][2] - 2.0) < EPS]
    assert len(lines) == 1
    xs = sorted([lines[0]["start"][0], lines[0]["end"][0]])
    assert xs == [-6.6, 6.6]


def test_mirrored_arcs_and_nurbs_land_on_the_right_side():
    [_, (_, _, items)] = latch.edgeSets("Chamfer2")
    nurbs = [i for i in items if i["kind"] == "NurbsCurve3D"]
    assert len(nurbs) == 4
    assert sorted(round(i["min"][0], 4) for i in nurbs) == [-7.8, -7.8, 5.7365, 5.7365]
    for item in nurbs:
        assert item["min"][0] < item["max"][0]
    arcs = [i for i in items if i["kind"] == "arc" and abs(i["radius"] - 1.0) < EPS]
    assert sorted(a["center"][0] for a in arcs) == [-7.6, 7.6]


def test_the_second_slot_edges_lie_ten_mm_further():
    [(_, _, items)] = latch.edgeSets("Chamfer5")
    ys = sorted({round(p[1], 6) for i in items for p in (i["start"], i["end"])})
    assert ys == [-21.1, -19.1, -11.1, -9.1]


def _line(a, b):
    return {"kind": "line", "start": list(a), "end": list(b)}


def test_match_finds_each_edge_within_the_tolerance_either_way_round():
    candidates = [_line((0, 0, 0), (1, 0, 0)), _line((0, 1, 0), (1, 1, 0))]
    expected = [_line((1.00001, 1, 0), (0, 1, 0))]
    assert latch.matchEdges(expected, candidates, lambda c: c, 2e-4) == [candidates[1]]


def test_match_rounds_like_pred_on_nurbs_boxes():
    candidate = {"kind": "NurbsCurve3D", "min": [-0.78, -3.65, 0.0], "max": [-0.5736541, -3.3, 0.35]}
    expected = [{"kind": "NurbsCurve3D", "min": [-0.78, -3.65, 0.0], "max": [-0.57365, -3.3, 0.35]}]
    assert latch.matchEdges(expected, [candidate], lambda c: c, 2e-4) == [candidate]


def test_match_refuses_a_missing_or_ambiguous_edge():
    candidates = [_line((0, 0, 0), (1, 0, 0)), _line((0, 0, 0.00001), (1, 0, 0))]
    for expected in ([_line((0, 0, 0), (1, 0, 0))], [_line((0, 5, 0), (1, 5, 0))]):
        try:
            latch.matchEdges(expected, candidates, lambda c: c, 2e-4)
        except latch.EdgeNotFound:
            continue
        raise AssertionError(f"no error for {expected}")


# -- the build, read from the source ------------------------------------------------------------------------------------

def _tree():
    return ast.parse(open(SOURCE, encoding="utf-8").read())


def _source():
    return open(SOURCE, encoding="utf-8").read()


def test_create_latch_takes_the_component_and_returns_its_bodies():
    function = next(n for n in _tree().body if isinstance(n, ast.FunctionDef) and n.name == "createLatch")
    assert [a.arg for a in function.args.args] == ["component"]
    returns = [n for n in ast.walk(function) if isinstance(n, ast.Return)]
    assert len(returns) == 1 and isinstance(returns[0].value, ast.List)


def test_no_mirror_no_pattern_no_user_parameters():
    source = _source()
    for word in ("mirrorFeatures", "rectangularPatternFeatures", "circularPatternFeatures", "userParameters"):
        assert word not in source, word


def test_side_sketches_are_made_without_the_face_edges():
    assert "addWithoutEdges" in _source()


def test_the_body_and_the_joint_origin_carry_their_names():
    source = _source()
    assert "'Latch'" in source
    assert "'Latch joint origin'" in source


def test_the_joint_origin_is_the_one_of_latch_f3d():
    """r28_extract: at the part's origin, Z = part +y, X = part -x (180 degrees)"""
    source = _source()
    assert "originConstructionPoint" in source
    assert "zAxisEntity = component.yConstructionAxis" in source
    assert "xAxisEntity = component.xConstructionAxis" in source
    assert "'180 deg'" in source


def test_every_sketch_is_checked_fully_constrained():
    assert "isFullyConstrained" in _source()
