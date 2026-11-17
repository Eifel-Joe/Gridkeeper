"""
Tests for Pred's hinges drawn in code (round 29, Jörg 17.11.2026: "Wir zeichnen die Teile im Code.", "Am besten doch alle
Scharniere mit Auswahl im Generator."). Expected values come from Pred's components read step by step
(fusion-auftraege/r29_walk/Hinge_M3x30.json, Hinge_Pined.json, Hinge.json; mm, rounded there to 0.0001). The plan data of
predHinge is Fusion-free; what needs Fusion is checked in its source (ast), the shape itself in Fusion
(fusion-auftraege/r29_hinge_check.py).
"""

import ast
import math
import os
import sys

import pytest

from tests.test_joint_origin_layout import _load


def _loadHinge():
    """predSketch needs Fusion's types in annotations; stand-ins as in test_pred_sketch_arcs"""
    modules = [sys.modules["adsk.core"], sys.modules["adsk.fusion"]]
    for module in modules:
        module.__getattr__ = lambda name: type(name, (), {})
    try:
        return _load("predHinge")
    finally:
        for module in modules:
            del module.__getattr__


hinge = _loadHinge()
chainPlan = _load("sketchChain")
parts = _load("predBoxParts")

SOURCE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "gridfinityUtils", "predHinge.py")


def _exactly_determined(points, curves):
    constraints = chainPlan.chain(points, curves)
    assert chainPlan.rank(points, curves, constraints) == chainPlan.variableCount(points, curves)
    weight = sum(2 if c[0] == "originAt" else 1 for c in constraints)
    assert weight == chainPlan.variableCount(points, curves) - chainPlan.inherentCount(curves)


def _close(a, b, tolerance=1.5e-4):
    assert len(a) == len(b)
    for p, q in zip(a, b):
        assert max(abs(x - y) for x, y in zip(p, q)) < tolerance, (p, q)


# -- the variants ----------------------------------------------------------------------------------------------------

def test_variants_are_the_parts_hinges():
    assert set(hinge.SHAPES) == set(parts.HINGES)


def test_body_names_are_preds():
    assert hinge.SHAPES["M3x30"].bodyNames == ("BottomHingePart_M3x30", "TopHingePart_M3x30")
    assert hinge.SHAPES["Pinned"].bodyNames == ("BottomHingePart_M3x30", "TopHingePart_M3x30", "Hinge pin")
    assert hinge.SHAPES["Plain"].bodyNames == ("BottomHingePart", "TopHingePart")
    assert parts.BODY_NAMES["hingePinned.f3d"] == {"Body21": "Hinge pin"}


def test_lengths_follow_preds_slot():
    """Pred: length HingeSlotLength - 0.4, thirds (HingeSlotLength - 2 HingeTolerane) / 3, gap HingeTolerane"""
    assert hinge.LENGTH == pytest.approx(31.6)
    assert hinge.THIRD == pytest.approx(10.5666667, abs=1e-7)
    assert hinge.GAP == 0.15


# -- the section -----------------------------------------------------------------------------------------------------

M3X30_OUTLINE = [(-7.9516, 8.8), (-7.9516, 0.15), (7.9516, 0.15), (7.9516, 8.8), (6.3516, 8.8), (6.3516, 3.6172),
                 (5.2344, 2.5), (-5.2344, 2.5), (-6.3516, 3.6172), (-6.3516, 8.8)]
PLAIN_OUTLINE = [(-74.9325, 8.5), (-74.9325, 0.15), (-60.0, 0.15), (-60.0, 8.5), (-61.8, 8.5), (-61.8, 3.6586),
                 (-62.9586, 2.5), (-71.9739, 2.5), (-73.1325, 3.6586), (-73.1325, 8.5)]


def test_outline_is_preds():
    """Pred's HingeBaseTopology, the y 0..0.15 strip below the line HingeTolerane above the bottom left out (no profile
    there is ever extruded)"""
    _close(hinge.outline(hinge.SHAPES["M3x30"]), M3X30_OUTLINE)
    _close(hinge.outline(hinge.SHAPES["Pinned"]), M3X30_OUTLINE)
    _close(hinge.outline(hinge.SHAPES["Plain"]), PLAIN_OUTLINE)


def test_plain_right_leaf_is_60_from_the_origin():
    assert hinge.outline(hinge.SHAPES["Plain"])[2][0] == pytest.approx(-60.0, abs=1e-9)


@pytest.mark.parametrize("name,radii", [("M3x30", (4.0, 4.15, 1.75)), ("Pinned", (4.0, 4.15, 1.75)),
                                         ("Plain", (3.5, 3.725, 2.0))])
def test_radii_are_preds(name, radii):
    shape = hinge.SHAPES[name]
    assert (shape.knuckle, shape.clearance, shape.core) == pytest.approx(radii)


def test_leaves_fit_the_slots():
    """Auftrag: 31.6 in 32, 1.6 / 1.8 in 2, 8.8 / 8.5 in 9"""
    for name, width, depth in (("M3x30", 1.6, 8.8), ("Pinned", 1.6, 8.8), ("Plain", 1.8, 8.5)):
        points = hinge.outline(hinge.SHAPES[name])
        assert points[0][1] == pytest.approx(depth)
        assert points[9][0] - points[0][0] == pytest.approx(width)
        assert width < 2 and depth < 9 and hinge.LENGTH < 32


def test_section_sketch_is_exactly_determined():
    for shape in hinge.SHAPES.values():
        points, curves = hinge.sectionSketch(shape)
        _exactly_determined(points, curves)


def test_clearance_sketches_are_exactly_determined():
    for shape in hinge.SHAPES.values():
        for side in (-1, 1):
            points, curves = hinge.clearanceSketch(shape, side)
            _exactly_determined(points, curves)
            # no arcs (r29_hinge_check l1: the sector of two arcs was over-constrained in Fusion), only lines and the
            # knuckle and clearance circles; the lines lie on the cut side of the axis
            assert {c["kind"] for c in curves} == {"line", "circle"}
            assert sum(1 for c in curves if c["kind"] == "circle") == 2
            assert all(side * (x - hinge.center(shape)) >= -1e-12 for x, y in points)


@pytest.mark.parametrize("name", ["M3x30", "Plain"])
def test_circle_sketches_are_exactly_determined(name):
    """Circles about the axis alone (gaps, screw and pin hole): their centre lies on a world axis, so it hangs on a
    construction line to a point off the axes"""
    for count in (1, 2, 3):
        points, curves = hinge.circlesSketch(hinge.center(hinge.SHAPES[name]), count)
        assert sum(1 for c in curves if c["kind"] == "circle") == count
        assert all(c.get("construction") for c in curves if c["kind"] == "line")
        _exactly_determined(points, curves)


def test_cut_ranges_are_preds():
    """Pred's Extrude17 0..10.7167, Extrude18 20.8833..31.6 (left), Extrude19 10.5667..21.0333 (right), Extrude20/21
    the gaps 10.5667..10.7167 and 20.8833..21.0333"""
    ranges = [(side, round(a, 4), round(b, 4)) for side, a, b in hinge.clearanceRanges()]
    assert ranges == [(-1, 0.0, 10.7167), (-1, 20.8833, 31.6), (1, 10.5667, 21.0333)]
    assert [(round(a, 4), round(b, 4)) for a, b in hinge.gapRanges()] == [(10.5667, 10.7167), (20.8833, 21.0333)]


# -- the tabs --------------------------------------------------------------------------------------------------------

def test_tab_is_preds_rectangle_with_chamfered_corners():
    """Pred's HingeTabDetails: rectangle y 3..5.6, z 20.9..26.7 (centre 7.8 below the end), corners chamfered 1.2
    (Chamfer1), mirrored at z 15.8 (Mirror2)"""
    upper = hinge.tabOctagon(lower=False)
    assert min(y for y, z in upper) == pytest.approx(3.0) and max(y for y, z in upper) == pytest.approx(5.6)
    assert min(z for y, z in upper) == pytest.approx(20.9) and max(z for y, z in upper) == pytest.approx(26.7)
    lower = hinge.tabOctagon(lower=True)
    _close(sorted(lower), sorted((y, hinge.LENGTH - z) for y, z in upper), 1e-9)
    # area: 2.6 x 5.8 less four corners 1.2 x 1.2 / 2; Pred's Chamfer1 took 3.744 mm3 at 1.3 depth
    area = 0.5 * abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(upper, upper[1:] + upper[:1])))
    assert area == pytest.approx(2.6 * 5.8 - 2 * 1.2 ** 2)
    assert (2 * 1.2 ** 2) * 1.3 == pytest.approx(2839.1505 - 2835.4065, abs=1e-4)


def test_tab_sketch_is_exactly_determined():
    for lower in (False, True):
        points = hinge.tabOctagon(lower)
        curves = [{"kind": "line", "a": i, "b": (i + 1) % len(points)} for i in range(len(points))]
        _exactly_determined(points, curves)


# -- M3x30 extras ----------------------------------------------------------------------------------------------------

def test_nut_hexagon_is_preds():
    """Pred's Sketch3: a regular hexagon across flats 5.5, flats parallel to x, area 26.1973 mm2"""
    points = hinge.hexagon(0.0)
    area = 0.5 * abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:] + points[:1])))
    assert area == pytest.approx(26.1973, abs=1e-4)
    assert max(abs(y) for x, y in points) == pytest.approx(2.75)
    curves = [{"kind": "line", "a": i, "b": (i + 1) % 6} for i in range(6)]
    _exactly_determined(points, curves)


def test_bridge_sketch_is_exactly_determined():
    points, curves = hinge.bridgeSketch(0.0)
    _exactly_determined(points, curves)


def _originAnchors(points, curves):
    """Points the chain fixes wholly from the origin: put on it, or dimensioned from it in x and in y"""
    plan = chainPlan.chain(points, curves)
    fromOrigin = {}
    for c in plan:
        if len(c) == 3 and c[2] is None:
            fromOrigin.setdefault(c[1], set()).add(c[0])
    return {c[1] for c in plan if c[0] == "originAt"} | {p for p, kinds in fromOrigin.items() if kinds == {"hdim", "vdim"}}


def _allPlans():
    for shape in hinge.SHAPES.values():
        c = hinge.center(shape)
        yield hinge.sectionSketch(shape)
        for side in (-1, 1):
            yield hinge.clearanceSketch(shape, side)
        for count in (1, 2, 3):
            yield hinge.circlesSketch(c, count)
        yield hinge.tabSketch()
        yield hinge.bridgeSketch(c)
        points = hinge.hexagon(c)
        yield points, [{"kind": "line", "a": i, "b": (i + 1) % len(points)} for i in range(len(points))]
    points = hinge.pinProfile()
    yield points, [{"kind": "line", "a": i, "b": (i + 1) % len(points)} for i in range(len(points))]
    for name, points, z0, z1 in hinge.pinCuts():
        yield points, [{"kind": "line", "a": i, "b": (i + 1) % len(points)} for i in range(len(points))]


def test_every_sketch_hangs_on_one_origin_anchor():
    """r29_hinge_diag (18:24): in the bridge sketch, eight chords each dimensioned from the origin, Fusion refused the
    second anchor's dimension (hdim origin-P2, VCS_SKETCH_OVER_CONSTRAINTS) in every case tried (plane z 3.9 or XY,
    compute deferred or not, empty or built). The sketches Fusion took have one point fixed wholly from the origin (the
    tabs two; a circle's centre may take one of its two dimensions from the origin). Every sketch now is one shape
    (construction lines join its parts) with one such anchor"""
    for points, curves in _allPlans():
        assert len(_originAnchors(points, curves)) == 1
        _exactly_determined(points, curves)


def _pointsOnCircles(points, curves, radii):
    """Points of the plan lying on one of its circles (radii in the circles' order)"""
    circles = [(points[c["center"]], r) for c, r in zip([c for c in curves if c["kind"] == "circle"], radii)]
    return [p for p in points for (cx, cy), r in circles if abs(math.hypot(p[0] - cx, p[1] - cy) - r) < 1e-3]


def test_no_point_on_a_circle():
    """r29_hinge_check l1/l2: sketches with points exactly on a circle of the same sketch (the sector's arc ends, the
    bridge chords' ends) were over-constrained in Fusion; every sketch with circles keeps its points off them"""
    for shape in hinge.SHAPES.values():
        c = hinge.center(shape)
        points, curves = hinge.sectionSketch(shape)
        assert not _pointsOnCircles(points, curves, [shape.knuckle])
        for side in (-1, 1):
            points, curves = hinge.clearanceSketch(shape, side)
            assert not _pointsOnCircles(points, curves, [shape.knuckle, shape.clearance])
        for count in (2, 3):
            points, curves = hinge.circlesSketch(c, count)
            assert not _pointsOnCircles(points, curves, [shape.core, hinge.PLAIN_HOLE, shape.clearance][:count])
    points, curves = hinge.bridgeSketch(0.0)
    assert not _pointsOnCircles(points, curves, [hinge.COUNTERBORE / 2])


def test_bridge_chords_cross_only_inside():
    """The chords reach past the circle; outside it no two of them meet, so they close no profile there"""
    points, curves = hinge.bridgeSketch(0.0)
    lines = [(points[c["a"]], points[c["b"]]) for c in curves if c["kind"] == "line" and not c.get("construction")]
    r = hinge.COUNTERBORE / 2
    for i, (p, q) in enumerate(lines):
        assert math.hypot(*p) > r and math.hypot(*q) > r
        for (s, t) in lines[i + 1:]:
            d = (q[0] - p[0]) * (t[1] - s[1]) - (q[1] - p[1]) * (t[0] - s[0])
            if abs(d) < 1e-12:
                continue
            u = ((s[0] - p[0]) * (t[1] - s[1]) - (s[1] - p[1]) * (t[0] - s[0])) / d
            v = ((s[0] - p[0]) * (q[1] - p[1]) - (s[1] - p[1]) * (q[0] - p[0])) / d
            if 0 <= u <= 1 and 0 <= v <= 1:
                assert math.hypot(p[0] + u * (q[0] - p[0]), p[1] + u * (q[1] - p[1])) < r


# Pred's Sketch5 profiles (sketch x, sketch y = -world y; bounding boxes) and the layers he extruded them in:
# Extrude25 0.2 mm: 0 1 2 3 4 8 9 10 11 12 18 28, Extrude26 0.4 mm: 0 4 5 6 7 8 12 14 22 30 31 32
SKETCH5 = {
    0: ((-0.2626, -2.7626), (0.2626, -2.4749)), 1: ((-1.75, -2.7374), (0, -1.75)), 2: ((-2.1213, -2.1213), (-1.75, -1.75)),
    3: ((-2.7374, -1.75), (-1.75, 0)), 4: ((-2.7626, -0.2626), (-2.4749, 0.2626)), 5: ((-2.7374, 0), (-1.75, 1.75)),
    6: ((-2.1213, 1.75), (-1.75, 2.1213)), 7: ((-1.75, 1.75), (0, 2.7374)), 8: ((-0.2626, 2.4749), (0.2626, 2.7626)),
    9: ((0, 1.75), (1.75, 2.7374)), 10: ((1.75, 1.75), (2.1213, 2.1213)), 11: ((1.75, 0), (2.7374, 1.75)),
    12: ((2.4749, -0.2626), (2.7626, 0.2626)), 13: ((0, -1.75), (1.2374, -1.2374)), 14: ((0.7249, -1.75), (1.75, -0.7249)),
    15: ((1.2374, -1.2374), (1.75, 0)), 16: ((-0.7249, -2.4749), (0.7249, -1.75)), 17: ((-1.2374, -1.75), (0, -1.2374)),
    18: ((-1.75, -1.75), (-0.7249, -0.7249)), 19: ((-1.75, -1.2374), (-1.2374, 0)), 20: ((-2.4749, -0.7249), (-1.75, 0.7249)),
    21: ((-1.75, 0), (-1.2374, 1.2374)), 22: ((-1.75, 0.7249), (-0.7249, 1.75)), 23: ((-1.2374, 1.2374), (0, 1.75)),
    24: ((-0.7249, 1.75), (0.7249, 2.4749)), 25: ((0, 1.2374), (1.2374, 1.75)), 26: ((1.75, -0.7249), (2.4749, 0.7249)),
    27: ((-1.75, -1.75), (1.75, 1.75)), 28: ((0.7249, 0.7249), (1.75, 1.75)), 29: ((1.2374, 0), (1.75, 1.2374)),
    30: ((0, -2.7374), (1.75, -1.75)), 31: ((1.75, -1.75), (2.7374, 0)), 32: ((1.75, -2.1213), (2.1213, -1.75)),
}
THIN = {0, 1, 2, 3, 4, 8, 9, 10, 11, 12, 18, 28}
THICK = {0, 4, 5, 6, 7, 8, 12, 14, 22, 30, 31, 32}


def test_bridge_layers_pick_preds_profiles():
    """The rule on a profile's box centre (world x, y about the axis) gives Pred's choice for all 33 of his profiles;
    the profiles inside the 1.75 circle, which our sketch does not have, are left out by it too"""
    thin, thick = set(), set()
    for index, ((x0, v0), (x1, v1)) in SKETCH5.items():
        layers = hinge.bridgeLayers((x0 + x1) / 2, -(v0 + v1) / 2)
        if hinge.THIN_BRIDGE in layers:
            thin.add(index)
        if hinge.THICK_BRIDGE in layers:
            thick.add(index)
    assert (thin, thick) == (THIN, THICK)


def test_bridge_layer_heights_are_preds():
    """Extrude25 0.2 mm and Extrude26 0.4 mm down from the counterbore's floor at 3.9: Top +1.1802 and +2.3016 mm3"""
    assert hinge.COUNTERBORE_DEPTH == pytest.approx(3.9)
    assert (hinge.THIN_BRIDGE, hinge.THICK_BRIDGE) == (0.2, 0.4)


# -- the printed pin (Pinned) ----------------------------------------------------------------------------------------

def _revolvedVolume(profile):
    """Pappus over a closed polygon in (r, z): sum of the triangle-fan terms"""
    volume = 0.0
    for (r0, z0), (r1, z1) in zip(profile, profile[1:] + profile[:1]):
        volume += (r0 * r0 + r0 * r1 + r1 * r1) * (z1 - z0)
    return abs(math.pi * volume / 3)


def test_pin_profile_volume_is_preds_before_the_cuts():
    """Pred's Body21 after Chamfer4 (heads d 5.1 x 3.3, shaft d 4.1, chamfers 0.5 inside, 1.5 x 2.5 at the head): 444.2207"""
    assert _revolvedVolume(hinge.pinProfile()) == pytest.approx(444.2207, abs=5e-4)


def test_pin_head_chamfer_is_1_5_across_and_2_5_along():
    """Chamfer3 two distances: across 1.5 (top face r 1.05) and along 2.5; the other way round it would take 20.2 mm3,
    Pred's took 24.1510 (464.8897 - 440.7387)"""
    profile = hinge.pinProfile()
    assert (1.05, hinge.LENGTH) in [(round(r, 9), round(z, 9)) for r, z in profile]
    assert (2.55, round(hinge.LENGTH - 2.5, 9)) in [(round(r, 9), round(z, 9)) for r, z in profile]


def test_pin_sketches_are_exactly_determined():
    points = hinge.pinProfile()
    curves = [{"kind": "line", "a": i, "b": (i + 1) % len(points)} for i in range(len(points))]
    _exactly_determined(points, curves)
    for name, points, z0, z1 in hinge.pinCuts():
        _exactly_determined(points, [{"kind": "line", "a": i, "b": (i + 1) % len(points)} for i in range(len(points))])


def test_pin_cuts_are_preds():
    """Extrude30: slot 1 wide, 7.5 deep from the head end; Extrude31: flat y > 1.5819 over the whole length; Extrude32:
    flat y < -1.5819 down to the slot's bottom (z 24.1). Slot and lower flat share their range: one T-shaped profile"""
    cuts = {name: (points, z0, z1) for name, points, z0, z1 in hinge.pinCuts()}
    assert set(cuts) == {"Pin flat", "Pin slot"}
    points, z0, z1 = cuts["Pin flat"]
    assert (z0, z1) == (0.0, hinge.LENGTH)
    assert min(y for x, y in points) == pytest.approx(hinge.PIN_FLAT)
    points, z0, z1 = cuts["Pin slot"]
    assert (z0, z1) == pytest.approx((24.1, hinge.LENGTH))
    xs = sorted({round(x, 9) for x, y in points})
    assert -0.5 in xs and 0.5 in xs
    assert max(y for x, y in points) > 2.55 and min(y for x, y in points) < -2.55


def test_pin_flat_is_preds():
    """Sketch7's lines x = +-2 end on the head circle r 2.55: the flats lie at |y| = sqrt(2.55^2 - 2^2)"""
    assert hinge.PIN_FLAT == pytest.approx(1.5819, abs=1e-4)


# -- source checks ---------------------------------------------------------------------------------------------------

def _tree():
    with open(SOURCE, encoding="utf-8") as f:
        return ast.parse(f.read())


def test_no_mirror_features():
    """README: no feature mirroring of chamfers or fillets (Mirror6); Pred's Mirror2/3/4 are built as counterparts"""
    names = {node.attr for node in ast.walk(_tree()) if isinstance(node, ast.Attribute)}
    assert "mirrorFeatures" not in names


def test_create_hinge_signature():
    functions = {node.name: node for node in ast.walk(_tree()) if isinstance(node, ast.FunctionDef)}
    args = [a.arg for a in functions["createHinge"].args.args]
    assert args == ["component", "hinge"]


def test_no_user_parameters():
    names = {node.attr for node in ast.walk(_tree()) if isinstance(node, ast.Attribute)}
    assert "userParameters" not in names
