"""
Pred's handle drawn in code (round 29, Nutzer 17.11.2026: "Wir zeichnen die Teile im Code."), after
fusion-auftraege/r28_handle_build.py, whose half profile gave Pred's volume at both widths (r28_handle_build.l5.out).
The profile is fully determined by the sketch chain (Nutzer: "Denk nur dran, dass alle Zeichnungen vollständig bestimmt
sein müssen."), its one size is the half width H as an expression on the box parameters (predBoxSeats.handleHalfWidth).
Lengths in mm here, cm in the module.
"""

import ast
import math
import os
import re
import sys

import pytest

from tests.test_joint_origin_layout import _load

chainPlan = _load("sketchChain")


def _loadHandle():
    modules = [sys.modules["adsk.core"], sys.modules["adsk.fusion"]]
    for module in modules:
        module.__getattr__ = lambda name: type(name, (), {})
    try:
        return _load("predHandle")
    finally:
        for module in modules:
            del module.__getattr__


handle = _loadHandle()
Dim, DimKind = handle.Dim, handle.DimKind
SOURCE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "gridfinityUtils", "predHandle.py")
PARAMETER = "HW"
# Pred's profile area in its box sketch LabelAndHandleHolder (r28_handle_diag.l3.out, r28_handle_build.l5.out)
PRED_AREA = 472.9491


def _H(mmValue):
    return Dim(mmValue / 10, PARAMETER, DimKind.EXPRESSION)


def _mm(point):
    return tuple(round(v.value * 10, 6) for v in point)


def _curves(mmValue):
    return handle.profile(_H(mmValue))


def _chainInput(curves):
    """As WorldSketch does it on the XZ plane: points once each, sketch x = world x, sketch y = world -z"""
    worlds, index, out = [], {}, []

    def point(world):
        key = tuple(round(v.value * 1e5) for v in world)
        if key not in index:
            index[key] = len(worlds)
            worlds.append(world)
        return index[key]
    for curve in curves:
        if curve["kind"] == "line":
            out.append({"kind": "line", "a": point(curve["start"]), "b": point(curve["end"])})
        else:
            out.append({"kind": "arc", "center": point(curve["center"]), "start": point(curve["start"]), "end": point(curve["end"])})
    points = [(w[0].value, -w[2].value) for w in worlds]
    return worlds, points, out


def _evaluate(expression, hValue):
    """A sketch dimension's expression in cm, H set to hValue (mm)"""
    text = re.sub(r"(\d+(?:\.\d+)?)\s*mm", r"(\1 / 10)", expression)
    return eval(text, {"abs": abs, PARAMETER: hValue / 10})


@pytest.mark.parametrize("H", [49.5, 56.75, 28.5])
def test_the_half_profile_is_the_templates(H):
    """r28_handle_build: arm -H .. -H + 7 from z 3.5 down to -11.5, arcs r 8 and r 15 about (-H + 15 | -11.5), bar to the
    middle between z -19.5 and -26.5"""
    curves = _curves(H)
    lines = sorted((_mm(c["start"]), _mm(c["end"])) for c in curves if c["kind"] == "line")
    expected = [((-H, 0, 3.5), (-H + 7, 0, 3.5)), ((-H + 7, 0, 3.5), (-H + 7, 0, -11.5)),
                ((-H + 15, 0, -19.5), (0, 0, -19.5)), ((0, 0, -19.5), (0, 0, -26.5)),
                ((0, 0, -26.5), (-H + 15, 0, -26.5)), ((-H, 0, -11.5), (-H, 0, 3.5))]
    assert lines == sorted(tuple(tuple(round(v, 6) for v in p) for p in pair) for pair in expected)
    arcs = sorted((_mm(c["center"]), math.dist(_mm(c["center"]), _mm(c["start"])), math.dist(_mm(c["center"]), _mm(c["end"])))
                  for c in curves if c["kind"] == "arc")
    assert [a[0] for a in arcs] == [(-H + 15, 0, -11.5)] * 2
    assert sorted(round(a[1], 6) for a in arcs) == [8, 15]
    assert all(round(a[1], 6) == round(a[2], 6) for a in arcs)


def _area(H):
    """Arm 7 x 15, bar 7 x (H - 15), the quarter ring between r 15 and r 8"""
    return 7 * 15 + 7 * (H - 15) + math.pi * (15 ** 2 - 8 ** 2) / 4


def test_the_profile_area_is_preds():
    """Pred's file is at H 49.5 (5 x 4 x 6)"""
    assert _area(49.5) == pytest.approx(PRED_AREA, abs=1e-4)


@pytest.mark.parametrize("H", [49.5, 56.75, 28.5])
def test_the_profile_encloses_that_area(H):
    """The region's x extent at each height (fine scan) adds up to the area"""
    expected = _area(H)
    curves = _curves(H)
    step = 0.005
    area = 0.0
    z = -26.5 + step / 2
    while z < 3.5:
        area += _width(curves, z) * step
        z += step
    assert area == pytest.approx(expected, rel=2e-4)


def _crossings(curves, z):
    """x where the outline crosses the height z (mm)"""
    xs = []
    for c in curves:
        if c["kind"] == "line":
            (x0, _, z0), (x1, _, z1) = _mm(c["start"]), _mm(c["end"])
            if z0 != z1 and min(z0, z1) <= z < max(z0, z1):
                xs.append(x0 + (z - z0) * (x1 - x0) / (z1 - z0))
        else:
            (cx, _, cz) = _mm(c["center"])
            r = math.dist(_mm(c["center"]), _mm(c["start"]))
            # the arcs are the lower left quarters: x <= cx, z <= cz
            if cz - r <= z < cz:
                xs.append(cx - math.sqrt(r * r - (z - cz) ** 2))
    return sorted(xs)


def _width(curves, z):
    xs = _crossings(curves, z)
    assert len(xs) % 2 == 0
    return sum(b - a for a, b in zip(xs[::2], xs[1::2]))


@pytest.mark.parametrize("H", [49.5, 56.75, 28.5])
def test_the_pin_hole_cut_along_x_meets_the_arm_only(H):
    """Main session 17.11.2026: the hole is cut through all along X from the YZ plane, so on the pin axis's band
    (|z| <= 1.75 mm, the hole's radius) the half profile may be the arm only, not the bar nor anything else"""
    curves = _curves(H)
    for z in (-1.75, -1.0, 0.0, 1.0, 1.749):
        xs = _crossings(curves, z)
        assert xs == pytest.approx([-H, -H + 7])


@pytest.mark.parametrize("H", [49.5, 56.75, 28.5])
def test_the_profile_is_fully_determined_by_the_chain(H):
    """Every point and curve fixed (rank equals the unknowns), no zero dimension, no tangency"""
    _, points, curves = _chainInput(_curves(H))
    constraints = chainPlan.chain(points, curves)
    assert chainPlan.rank(points, curves, constraints) == chainPlan.variableCount(points, curves)
    weight = sum(2 if c[0] == "originAt" else 1 for c in constraints)
    assert weight == chainPlan.variableCount(points, curves) - chainPlan.inherentCount(curves)
    assert {c[0] for c in constraints} <= {"horizontal", "vertical", "hdim", "vdim", "originAt"}
    used = {p for c in curves for k in ("a", "b", "center", "start", "end") if k in c for p in [c[k]]}
    assert used == set(range(len(points))), "a loose point"


def test_the_dimensions_follow_the_half_width():
    """Each dimension's expression, as WorldSketch gives it (abs of the world dims' difference), evaluated at another
    half width gives that width's distance: the profile follows H, the arm and arcs keep their size"""
    worlds, points, curves = _chainInput(_curves(49.5))
    moved = [_mm(w) for w in _chainInput(_curves(28.5))[0]]
    assert len(moved) == len(worlds)
    for kind, *args in chainPlan.chain(points, curves):
        if kind not in ("hdim", "vdim"):
            continue
        i, j = args
        axis = 0 if kind == "hdim" else 2
        value = worlds[i][axis] if j is None else worlds[i][axis] - worlds[j][axis]
        dimension = value.abs()
        if kind == "hdim":
            assert PARAMETER in dimension.expression and dimension.isExpression
        expected = abs(moved[i][axis] - (0 if j is None else moved[j][axis])) / 10
        assert _evaluate(dimension.expression, 28.5) == pytest.approx(expected)


# -- what needs Fusion, read from the source -------------------------------------------------------------------------

def _tree():
    return ast.parse(open(SOURCE, encoding="utf-8").read())


def _function(name):
    return next(node for node in _tree().body if isinstance(node, ast.FunctionDef) and node.name == name)


def test_create_handle_signature():
    function = _function("createHandle")
    assert [a.arg for a in function.args.args] == ["component", "halfWidth"]
    assert ast.unparse(function.args.args[1].annotation) == "str"


def test_the_profile_is_drawn_by_world_sketch_on_xz():
    source = ast.unparse(_function("createHandle"))
    assert "predSketch.WorldSketch(component, component.xZConstructionPlane" in source
    assert "profile(" in source


def test_the_hole_sketch_is_on_the_yz_plane_centred_and_dimensioned():
    source = ast.unparse(_function("_pinHole"))
    assert "sketches.add(component.yZConstructionPlane)" in source
    assert "addCoincident(circle.centerSketchPoint, sketch.originPoint)" in source
    assert "addDiameterDimension" in source


def test_the_hole_cuts_the_half_body_only_before_the_mirror():
    source = ast.unparse(_function("createHandle"))
    assert source.index("_pinHole(") < source.index("mirrorFeatures")
    hole = ast.unparse(_function("_pinHole"))
    assert "participantBodies = [body]" in hole
    assert "CutFeatureOperation" in hole


def test_only_the_body_is_mirrored_and_combined():
    """No feature mirror of chamfers or fillets (round 27, Mirror6); a body mirror went in round 28"""
    source = ast.unparse(_function("createHandle"))
    assert "mirrorFeatures.createInput(predSketch.collection([body]), component.yZConstructionPlane)" in source
    assert "isCombine = True" in source


def test_name_joint_origin_and_no_user_parameters():
    text = open(SOURCE, encoding="utf-8").read()
    source = ast.unparse(_function("createHandle"))
    assert "body.name = BODY_NAME" in source
    assert handle.BODY_NAME == "Handle"
    assert handle.JOINT_ORIGIN_NAME == "Handle joint origin"
    assert "createByPoint(component.originConstructionPoint)" in source
    assert "userParameters" not in text


def test_chamfer_and_fillet_edge_counts_are_checked():
    """r28_handle_build: Fillet1 at 2 edges, Chamfer1 at 14 (Pred's); the module refuses other counts"""
    source = ast.unparse(_function("createHandle"))
    assert "FILLET_EDGES" in source and "CHAMFER_EDGES" in source
    assert (handle.FILLET_EDGES, handle.CHAMFER_EDGES) == (2, 14)
