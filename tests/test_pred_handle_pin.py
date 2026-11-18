"""
Tests for Pred's handle pin drawn in code (round 29, 17.11.2026: the parts are drawn in code). Expected values
come from Pred's HandlePin read step by step (fusion-auftraege/r29_walk/HandlePin.json): Sketch1's profile areas, the
body box and the volume after Extrude6, 138.1225 mm3. The plan data of predHandlePin is Fusion-free; what needs Fusion is
checked in its source (ast), the shape itself in Fusion (fusion-auftraege/r29_pin_check.py).
"""

import ast
import math
import os
import sys

import pytest

from tests.test_joint_origin_layout import _load


def _loadPin():
    """predSketch needs Fusion's types in annotations; stand-ins as in test_pred_sketch_arcs"""
    modules = [sys.modules["adsk.core"], sys.modules["adsk.fusion"]]
    for module in modules:
        module.__getattr__ = lambda name: type(name, (), {})
    try:
        return _load("predHandlePin")
    finally:
        for module in modules:
            del module.__getattr__


pin = _loadPin()
chainPlan = _load("sketchChain")

SOURCE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "gridfinityUtils", "predHandlePin.py")


def _exactly_determined(points, curves):
    constraints = chainPlan.chain(points, curves)
    assert chainPlan.rank(points, curves, constraints) == chainPlan.variableCount(points, curves)
    weight = sum(2 if c[0] == "originAt" else 1 for c in constraints)
    assert weight == chainPlan.variableCount(points, curves) - chainPlan.inherentCount(curves)


def test_profile_sketch_is_exactly_determined():
    """All sketches must be fully constrained. Three circles on one centre"""
    points = [pin.AXIS]
    curves = [{"kind": "circle", "center": 0} for _ in pin.DIAMETERS]
    _exactly_determined(points, curves)


def test_cut_sketch_is_exactly_determined():
    points, lines = pin.cutSketch()
    curves = [{"kind": "line", "a": a, "b": b} for a, b in lines]
    _exactly_determined(points, curves)
    # every point on a line, no loose point
    assert {p for line in lines for p in line} == set(range(len(points)))


def test_profile_areas_are_preds():
    """Pred's Sketch1 profiles 3, 4 and 2: disk r 1.3, ring 1.3-1.75, ring 1.75-2.55 (mm2)"""
    radii = [0.0] + [d / 2 for d in sorted(pin.DIAMETERS)]
    areas = [math.pi * (outer ** 2 - inner ** 2) for inner, outer in zip(radii, radii[1:])]
    assert [round(a, 4) for a in areas] == [5.3093, 4.3118, 10.8071]


def _chordIntegral(r, low, high):
    """Integral of the chord width 2 sqrt(r2 - t2) over t from low to high, closed (review: Simpson over the root's ends
    was 4e-4 mm3 off, 40 % of the tolerance)"""
    def G(t):
        t = max(-r, min(r, t))
        return t * math.sqrt(max(r * r - t * t, 0.0)) + r * r * math.asin(t / r)
    return G(high) - G(low) if high > low else 0.0


def _section(r, zLow, zHigh, slot):
    """Area of the disk of radius r about the axis between heights zLow and zHigh (about the axis), less the slot of
    half width slot around the axis' y: where the chord is wider than the slot the slot takes 2 slot, elsewhere all"""
    low, high = max(-r, zLow), min(r, zHigh)
    if high <= low:
        return 0.0
    disk = _chordIntegral(r, low, high)
    if slot <= 0:
        return disk
    if slot >= r:
        return 0.0
    c = math.sqrt(r * r - slot * slot)
    inner = (max(low, -c), min(high, c))
    taken = 2 * slot * max(0.0, inner[1] - inner[0])
    taken += _chordIntegral(r, low, min(high, -c)) + _chordIntegral(r, max(low, c), high)
    return disk - taken


def _planned_volume():
    """The body the plan builds, integrated along x from its sections: extrudes as radius per x range, the chamfer as a
    radius growing 1:1, the cuts as bands in z and the slot in y (all relative to the axis)"""
    yAxis, zAxis = pin.AXIS
    steps = {name: (x0, x1) for name, x0, x1 in pin.cutRanges()}
    (bottomZ, topZ) = (pin.BOTTOM_CUT_Z - zAxis, pin.TOP_CUT_Z - zAxis)
    slot = pin.SLOT_WIDTH / 2
    edges = sorted({pin.X_TIP, pin.X_TIP + pin.CHAMFER, pin.X_SHOULDER, pin.X_HEAD, pin.X_END}
                   | {x for x0, x1 in steps.values() for x in (x0, x1)})
    volume = 0.0
    for a, b in zip(edges, edges[1:]):
        # the extrude and the cuts of the piece from its middle: at the piece's ends the neighbours' would count
        middle = (a + b) / 2
        inside = {name: x0 <= middle <= x1 for name, (x0, x1) in steps.items()}
        zLow = bottomZ if inside["bottom"] else -99
        zHigh = topZ if inside["top"] else 99
        width = slot if inside["slot"] else 0.0

        def area(x):
            if middle < pin.X_SHOULDER:
                r = pin.TIP_DIAMETER / 2 - max(0.0, pin.CHAMFER - (x - pin.X_TIP))
            elif middle < pin.X_HEAD:
                r = pin.SHAFT_DIAMETER / 2
            else:
                r = pin.HEAD_DIAMETER / 2
            return _section(r, zLow, zHigh, width)
        # sections change with x only on the chamfer, there r is linear but the cuts make the area no polynomial
        n = 2 if middle > pin.X_TIP + pin.CHAMFER else 400
        h = (b - a) / n
        volume += h / 3 * sum((1 if i in (0, n) else 4 if i % 2 else 2) * area(a + i * h) for i in range(n + 1))
    return volume


def test_planned_volume_is_preds():
    assert _planned_volume() == pytest.approx(138.1225, abs=0.001)


def test_planned_box_is_preds():
    yAxis, zAxis = pin.AXIS
    r = pin.HEAD_DIAMETER / 2
    box = ((pin.X_TIP, yAxis - r, pin.BOTTOM_CUT_Z), (pin.X_END, yAxis + r, zAxis + r))
    assert [[round(v, 4) for v in corner] for corner in box] == [[58.05, 1.2, 23.4], [77.75, 6.3, 27.25]]


def test_cuts_reach_preds_faces():
    """Pred's Extrude4 to the head's end face, Extrude5 4 mm, Extrude6 to the shoulder (r29_walk)"""
    assert {name: (round(x0, 4), round(x1, 4)) for name, x0, x1 in pin.cutRanges()} == {
        "bottom": (58.05, 77.75), "slot": (58.05, 62.05), "top": (58.05, 60.05)}


def test_joint_origin_is_the_f3ds():
    """handlePin.f3d: Handle pin joint origin at (7.775, 0.375, 2.47) cm, axes as the part (r28_extract.l2.out)"""
    name, point = pin.JOINT_ORIGIN
    assert name == "Handle pin joint origin"
    assert point == (77.75, 3.75, 24.7)


# -- source ------------------------------------------------------------------------------------------------------------

def _source():
    return open(SOURCE, encoding="utf-8").read()


def _function(name):
    tree = ast.parse(_source())
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def test_create_handle_pin_takes_the_component_and_returns_its_body():
    function = _function("createHandlePin")
    assert [a.arg for a in function.args.args] == ["component"]
    returns = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
    assert len(returns) == 1 and isinstance(returns[0].value, ast.List) and len(returns[0].value.elts) == 1


def test_the_body_is_named_handle_pin():
    assert pin.BODY_NAME == "Handle pin"
    assert ".name = BODY_NAME" in ast.unparse(_function("createHandlePin"))


def test_no_mirror_and_no_user_parameters():
    """README round 29: no feature mirror of chamfers or fillets, no user parameters"""
    source = _source()
    assert "mirrorFeatures" not in source and "userParameters" not in source


def test_joint_origin_by_the_shared_helper():
    assert "createPointJointOrigins" in ast.unparse(_function("createHandlePin"))


def test_the_extrudes_use_the_planned_profiles_and_ranges():
    """Review round 29: the volume test checks the constants, this pins how createHandlePin uses them (the Fusion check
    r29_pin_check compares the shape itself)"""
    calls = [ast.unparse(node) for node in sorted(
        (node for node in ast.walk(_function("createHandlePin"))
         if isinstance(node, ast.Call) and ast.unparse(node.func) == "_extrude"), key=lambda node: node.lineno)]
    assert calls == [
        "_extrude(component, [shaft], newBody, X_END - X_TIP, name='Shaft')",
        "_extrude(component, [tipRing], join, X_SHOULDER - X_TIP, body=body, name='Tip')",
        "_extrude(component, [tipRing, headRing], join, X_END - X_HEAD, start=X_HEAD - X_TIP, body=body, name='Head')",
        "_extrude(component, [cutProfile], cut, x1 - x0, start=x0 - X_TIP if x0 != X_TIP else None, body=body, name=f'Cut {name}')",
    ]
    source = ast.unparse(_function("createHandlePin"))
    assert "[shaft, tipRing, headRing] = profile.profilesByArea([_ringArea(0, SHAFT_DIAMETER), _ringArea(SHAFT_DIAMETER, TIP_DIAMETER), _ringArea(TIP_DIAMETER, HEAD_DIAMETER)])" in source
    assert "for (name, x0, x1), cutProfile in zip(cutRanges(), found)" in source
    assert "cuts.profiles([tuple((tuple((_mm(v) for v in corner)) for corner in boxes[name])) for name in names])" in source
