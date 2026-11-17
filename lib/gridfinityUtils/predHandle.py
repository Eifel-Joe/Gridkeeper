"""
The handle of the storage box after Pred's parametric Gridfinity Storage Box v1.1
(https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric, CC BY-NC, by Pred), drawn in
code (round 29, Nutzer 17.11.2026: "Wir zeichnen die Teile im Code."). Before, resources/predBox/handle.f3d was inserted,
which fails in a command with a dialog (fusion-auftraege/r28_cmdvariants.log).

Built as fusion-auftraege/r28_handle_build.py did, whose result had Pred's volume at both widths (r28_handle_build.l5.out):
- the half profile on XZ: arm -H .. -H + 7 from z 3.5 down to -11.5, arcs r 8 and r 15 about (-H + 15 | -11.5), bar to
  the middle (x = 0) between z -19.5 and -26.5 (Pred's sketch LabelAndHandleHolder, r28_handle_diag.l3.out);
- Extrude 7 mm symmetric, Fillet r 3.5 at the arm's 2 top edges, Chamfer 1 mm at 14 edges, the pin hole d 3.5 through
  the arm, the body mirrored at YZ and combined (a body mirror, not a feature mirror of chamfers: round 27, Mirror6).
The part frame is the seat (predBoxSeats 'Handle'): origin in the handle's middle on the pin axis, z up. The one size is
the half width H, an expression on the box parameters (predBoxSeats.handleHalfWidth; Nutzer 17.11.2026: "Der Griff bleibt
bei Max. 113,5mm stehen. Breiter macht keinen Sinn."). No user parameters. Tested in tests/test_pred_handle.py.
"""

import math
import adsk.core, adsk.fusion

from .dim import Dim, DimKind
from . import predSketch

BODY_NAME = 'Handle'
JOINT_ORIGIN_NAME = 'Handle joint origin'
PROFILE_SKETCH = 'Handle profile'
HOLE_SKETCH = 'Pin hole'
# Pred's Fillet1 and Chamfer1 (r28_handle_diag.l3.out); another count means the edge choice went wrong
FILLET_EDGES = 2
CHAMFER_EDGES = 14

# mm
THICKNESS = 7.0
ABOVE_AXIS = 3.5
ARM_LENGTH = 15.0
INNER_RADIUS = 8.0
OUTER_RADIUS = 15.0
FILLET_RADIUS = 3.5
CHAMFER = 1.0
HOLE_DIAMETER = 3.5
# how far the hole's cut reaches past the arm's outer face, so it ends in the air, not flush with the face
HOLE_PAST_ARM = 1.0

_EPS = 1e-5


def _mm(value: float) -> Dim:
    return Dim.length(round(value / 10, 9))


def profile(halfWidth: Dim) -> list[dict]:
    """
    The half profile, left arm, its curves with world points (x, 0, z) as dims, x on the half width:
    lines {'kind': 'line', 'start', 'end'}, arcs {'kind': 'arc', 'center', 'start', 'end'}. The arcs and the straight
    parts meet tangentially by their places; the sketch chain fixes the points by dimensions, no tangency (sketchChain)
    """
    zero = _mm(0)
    armOut = zero - halfWidth
    armIn = armOut + _mm(THICKNESS)
    center = armOut + _mm(OUTER_RADIUS)
    top = _mm(ABOVE_AXIS)
    armEnd = _mm(ABOVE_AXIS - ARM_LENGTH)
    barTop = _mm(ABOVE_AXIS - ARM_LENGTH - INNER_RADIUS)
    barBottom = _mm(ABOVE_AXIS - ARM_LENGTH - OUTER_RADIUS)

    def P(x, z):
        return (x, zero, z)

    def line(a, b):
        return {'kind': 'line', 'start': a, 'end': b}
    # The order is the chain's (sketchChain fixes the curves in this order): the arm's outer line before the arcs, so
    # its lower end is vertical under the top corner and dimensioned, and the r 15 arc holds the bar's bottom end by its
    # height only. Held by the circle alone, the arc's end at -H had a second solution 30 mm to the right, and from 4 to
    # 5 units Fusion took it (r29_handle_check Lauf 1: Fillet1/Chamfer1 lost their edges, V 5732.9733 instead of
    # 6136.8299); the bar end's height doesn't change with the width. test_a_width_change_cannot_flip_an_outline_point
    return [
        line(P(armOut, top), P(armIn, top)),
        line(P(armOut, armEnd), P(armOut, top)),
        line(P(armIn, top), P(armIn, armEnd)),
        {'kind': 'arc', 'center': P(center, armEnd), 'start': P(armIn, armEnd), 'end': P(center, barTop)},
        line(P(center, barTop), P(zero, barTop)),
        line(P(zero, barTop), P(zero, barBottom)),
        {'kind': 'arc', 'center': P(center, armEnd), 'start': P(center, barBottom), 'end': P(armOut, armEnd)},
        line(P(zero, barBottom), P(center, barBottom)),
    ]


def createHandle(component: adsk.fusion.Component, halfWidth: str) -> list[adsk.fusion.BRepBody]:
    """
    Draws Pred's handle into the given empty component and gives its one body, named Handle. halfWidth is the
    expression of the half width, e.g. predBoxSeats.handleHalfWidth(dims).expression or '49.5 mm'
    """
    H = Dim(component.parentDesign.unitsManager.evaluateExpression(halfWidth, 'cm'), halfWidth, DimKind.EXPRESSION, True)
    world = predSketch.WorldSketch(component, component.xZConstructionPlane, PROFILE_SKETCH)
    for curve in profile(H):
        if curve['kind'] == 'line':
            world.line(curve['start'], curve['end'])
        else:
            world.arc(curve['center'], curve['start'], curve['end'])
    sketch = world.close()
    if sketch.profiles.count != 1:
        raise RuntimeError(f'{PROFILE_SKETCH}: {sketch.profiles.count} profiles instead of 1')

    features = component.features
    extrudeInput = features.extrudeFeatures.createInput(sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extrudeInput.setSymmetricExtent(_value(THICKNESS), True)
    body = features.extrudeFeatures.add(extrudeInput).bodies.item(0)
    body.name = BODY_NAME

    h = H.value
    half = _cm(THICKNESS / 2)
    top = _cm(ABOVE_AXIS)

    def edges(test):
        return [e for e in body.edges if test(e.startVertex.geometry, e.endVertex.geometry)]

    # Fillet1: the arm's two top edges, along X on the top face's sides
    topEdges = edges(lambda a, b: _near(a.z, top) and _near(b.z, top) and _near(abs(a.y), half) and _near(a.y, b.y))
    if len(topEdges) != FILLET_EDGES:
        raise RuntimeError(f'handle fillet: {len(topEdges)} edges instead of {FILLET_EDGES}')
    filletInput = features.filletFeatures.createInput()
    filletInput.edgeSetInputs.addConstantRadiusEdgeSet(predSketch.collection(topEdges), _value(FILLET_RADIUS), False)
    features.filletFeatures.add(filletInput)

    def chamferEdge(a, b):
        # the outline on both sides, not at the middle (mirrored onto the other half) nor at the fillet's start, and
        # across the arm where the fillet starts (z 0 after the fillet r 3.5 from z 3.5)
        if _near(abs(a.y), half) and _near(abs(b.y), half) and _near(a.y, b.y):
            atMiddle = _near(a.x, 0) and _near(b.x, 0)
            atRoundStart = _near(a.z, 0) and _near(b.z, 0)
            return not atMiddle and not atRoundStart
        across = _near(a.z, 0) and _near(b.z, 0) and _near(a.x, b.x) and not _near(a.y, b.y)
        return across and (_near(a.x, -h) or _near(a.x, -h + _cm(THICKNESS)))
    chamferEdges = edges(chamferEdge)
    if len(chamferEdges) != CHAMFER_EDGES:
        raise RuntimeError(f'handle chamfer: {len(chamferEdges)} edges instead of {CHAMFER_EDGES}')
    chamferInput = features.chamferFeatures.createInput2()
    chamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(predSketch.collection(chamferEdges), _value(CHAMFER), False)
    features.chamferFeatures.add(chamferInput)

    _pinHole(component, body, halfWidth)

    mirrorInput = features.mirrorFeatures.createInput(predSketch.collection([body]), component.yZConstructionPlane)
    mirrorInput.isCombine = True
    features.mirrorFeatures.add(mirrorInput)

    jointInput = component.jointOrigins.createInput(adsk.fusion.JointGeometry.createByPoint(component.originConstructionPoint))
    component.jointOrigins.add(jointInput).name = JOINT_ORIGIN_NAME
    return [body]


def _pinHole(component: adsk.fusion.Component, body: adsk.fusion.BRepBody, halfWidth: str):
    """
    The pin hole d 3.5 on the pin axis (x along X at y = z = 0), cut from the YZ plane into the half body only. Along the
    pin axis's band the half profile is the arm alone (the bar lies at z <= -19.5,
    test_the_pin_hole_cut_along_x_meets_the_arm_only), so the cut is Pred's Extrude2 through the arm. On the YZ plane
    the circle sits on the sketch origin: no face to pick, no projection (r28_handle_build needed addWithoutEdges and a
    projected origin on the arm face).
    The cut reaches symmetric H + 1 mm to each side, past the arm's outer face at -H, as an expression on the half width.
    Through all from the YZ plane failed: "Could not complete Through All Extrude, body not found to extrude through"
    (fusion-auftraege/r29_handle_check.l1.out); a plain distance needs no body at the sketch plane
    """
    sketch = component.sketches.add(component.yZConstructionPlane)
    sketch.name = HOLE_SKETCH
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), _cm(HOLE_DIAMETER / 2))
    sketch.geometricConstraints.addCoincident(circle.centerSketchPoint, sketch.originPoint)
    dimension = sketch.sketchDimensions.addDiameterDimension(circle, adsk.core.Point3D.create(0.3, 0.3, 0), True)
    dimension.parameter.expression = f'{HOLE_DIAMETER:g} mm'
    # 1e-3 mm2 as in r28_handle_build (review: 1e-4 mm2 was tighter than needed at areaProperties' default accuracy)
    disc = [p for p in sketch.profiles if abs(p.areaProperties().area - math.pi * _cm(HOLE_DIAMETER / 2) ** 2) < 1e-5]
    if len(disc) != 1:
        raise RuntimeError(f'{HOLE_SKETCH}: {len(disc)} circle profiles instead of 1')
    cutInput = component.features.extrudeFeatures.createInput(disc[0], adsk.fusion.FeatureOperations.CutFeatureOperation)
    cutInput.setSymmetricExtent(adsk.core.ValueInput.createByString(f'({halfWidth}) + {HOLE_PAST_ARM:g} mm'), False)
    cutInput.participantBodies = [body]
    component.features.extrudeFeatures.add(cutInput)


def _cm(value: float) -> float:
    return value / 10


def _value(value: float) -> adsk.core.ValueInput:
    return adsk.core.ValueInput.createByString(f'{value:g} mm')


def _near(a: float, b: float) -> bool:
    return abs(a - b) < _EPS
