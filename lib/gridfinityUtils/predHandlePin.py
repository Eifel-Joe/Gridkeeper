"""
Pred's handle pin (component HandlePin of Pred's parametric Gridfinity Storage Box v1.1,
https://www.printables.com/model/543553, CC BY-NC, by Pred) drawn in code, round 29 (17.11.2026: the parts are drawn
in code). Until round 28 it was inserted from resources/predBox/handlePin.f3d, which fails in the execute of a
command with inputs (fusion-auftraege/r28_cmdvariants.log).

The pin lies in Pred's part frame (that of handlePin.f3d): its axis along x through (y 3.75 | z 24.7) mm, tip at x 58.05,
head end at x 77.75. Pred's steps (fusion-auftraege/r29_walk/HandlePin.json) end on faces of his handle (planes x 60.25
and 74.25 with offsets 0.2). The pin is a part of its own and must not hang on faces of the handle (it is drawn into an
empty component, and the handle is another part), so the same end positions become fixed distances. Both sketches lie
on one plane at the tip, x 58.05, and everything is extruded towards +x:
  Extrude1 shaft d 2.6 over 19.7, Extrude2 tip d 3.5 over 2, Extrude3 head d 5.1 from 16.4 over 3.3, Chamfer1 1 mm at
  the tip, then cuts: below z 23.4 over the whole length, the 0.6 mm slot 4 deep, above z 26.0 over the tip.
Every sketch is fully constrained (predSketch, sketchChain; requirement of 17.11.2026: all sketches
fully constrained). No user parameters, no mirrored features. Values here are mm, Fusion gets cm.
Tested in tests/test_pred_handle_pin.py, the shape against Pred's in fusion-auftraege/r29_pin_check.py.
"""

import math

import adsk.core, adsk.fusion

from .dim import Dim, valueInput, lengthInput
from . import fusionLists
from .predSketch import WorldSketch, collection

BODY_NAME = 'Handle pin'
JOINT_ORIGIN = ('Handle pin joint origin', (77.75, 3.75, 24.7))

# (y, z) of the pin's axis
AXIS = (3.75, 24.7)
X_TIP = 58.05
X_SHOULDER = 60.05
X_HEAD = 74.45
X_END = 77.75
SHAFT_DIAMETER = 2.6
TIP_DIAMETER = 3.5
HEAD_DIAMETER = 5.1
DIAMETERS = (SHAFT_DIAMETER, TIP_DIAMETER, HEAD_DIAMETER)
CHAMFER = 1.0
# the flats and the slot (Pred's Sketch2): bottom flat up to, top flat from, slot across y
BOTTOM_CUT_Z = 23.4
TOP_CUT_Z = 26.0
SLOT_WIDTH = 0.6
# the cut rectangles reach over the head (y 1.2 to 6.3, z 22.15 and 27.25) as Pred's do
CUT_HALF_WIDTH = HEAD_DIAMETER / 2
SLOT_DEPTH = 4.0


def _mm(value: float) -> Dim:
    return Dim.length(round(value / 10, 9))


def cutRanges():
    """(cut, x from, x to) in mm: Pred's Extrude4 to the head's end face, Extrude5 4 mm, Extrude6 to the shoulder"""
    return [('bottom', X_TIP, X_END), ('slot', X_TIP, X_TIP + SLOT_DEPTH), ('top', X_TIP, X_SHOULDER)]


def cutSketch():
    """Points (y, z) in mm and lines (index pairs) of the cut sketch: one outline of the bottom flat, the slot and the top
    flat (an I lying on its side), and the two lines that part the slot from the flats, so there are three profiles"""
    y, z = AXIS
    low, high = y - CUT_HALF_WIDTH, y + CUT_HALF_WIDTH
    left, right = y - SLOT_WIDTH / 2, y + SLOT_WIDTH / 2
    bottom, top = z - CUT_HALF_WIDTH, z + CUT_HALF_WIDTH
    points = [(low, bottom), (high, bottom), (high, BOTTOM_CUT_Z), (right, BOTTOM_CUT_Z), (right, TOP_CUT_Z),
              (high, TOP_CUT_Z), (high, top), (low, top), (low, TOP_CUT_Z), (left, TOP_CUT_Z), (left, BOTTOM_CUT_Z),
              (low, BOTTOM_CUT_Z)]
    points = [(round(a, 6), round(b, 6)) for a, b in points]
    lines = [(i, (i + 1) % len(points)) for i in range(len(points))] + [(10, 3), (9, 4)]
    return points, lines


def _cutBoxes():
    """World boxes (mm) of the three cut profiles, by name"""
    y, z = AXIS
    low, high = y - CUT_HALF_WIDTH, y + CUT_HALF_WIDTH
    left, right = y - SLOT_WIDTH / 2, y + SLOT_WIDTH / 2
    return {
        'bottom': ((X_TIP, low, z - CUT_HALF_WIDTH), (X_TIP, high, BOTTOM_CUT_Z)),
        'slot': ((X_TIP, left, BOTTOM_CUT_Z), (X_TIP, right, TOP_CUT_Z)),
        'top': ((X_TIP, low, TOP_CUT_Z), (X_TIP, high, z + CUT_HALF_WIDTH)),
    }


def _ringArea(inner: float, outer: float) -> float:
    return math.pi * ((outer / 2) ** 2 - (inner / 2) ** 2)


def _tipPlane(component: adsk.fusion.Component) -> adsk.fusion.ConstructionPlane:
    """Plane at x = X_TIP, an offset of the YZ plane (its normal is checked as in predBoxGenerator.offsetPlane)"""
    planes = component.constructionPlanes
    target = _mm(X_TIP)
    for sign in (1, -1):
        planeInput = planes.createInput()
        planeInput.setByOffset(component.yZConstructionPlane, lengthInput(target * sign))
        plane = planes.add(planeInput)
        if abs(plane.geometry.origin.x - target.value) < 1e-6:
            plane.name = 'Pin tip plane'
            plane.isLightBulbOn = False
            return plane
        plane.deleteMe()
    raise ValueError('handle pin: no plane at the tip')


def _extrude(component, profiles, operation, distance: float, start: float = None, body=None, name=None):
    """Extrude towards +x: distance and start offset (mm) are signed by the sketch normal's x"""
    features = component.features.extrudeFeatures
    sketch = profiles[0].parentSketch
    normal = sketch.xDirection.crossProduct(sketch.yDirection)
    sign = 1 if normal.x > 0 else -1
    extrudeInput = features.createInput(collection(profiles), operation)
    extrudeInput.setDistanceExtent(False, lengthInput(_mm(distance * sign)))
    if start is not None:
        extrudeInput.startExtent = adsk.fusion.OffsetStartDefinition.create(lengthInput(_mm(start * sign)))
    if body is not None:
        extrudeInput.participantBodies = [body]
    feature = features.add(extrudeInput)
    if name:
        feature.name = name
    return feature


def _tipEdge(body: adsk.fusion.BRepBody) -> adsk.fusion.BRepEdge:
    """The circular edge of the tip's end face (Pred's Chamfer1: Circle3D r 1.75 at x 58.05 on the axis)"""
    y, z = AXIS
    center = (X_TIP / 10, y / 10, z / 10)
    found = []
    for edge in fusionLists.items(body.edges):
        circle = adsk.core.Circle3D.cast(edge.geometry)
        if circle is None:
            continue
        c = circle.center
        if (max(abs(a - b) for a, b in zip((c.x, c.y, c.z), center)) < 1e-6
                and abs(circle.radius - TIP_DIAMETER / 20) < 1e-6):
            found.append(edge)
    if len(found) != 1:
        raise ValueError(f'handle pin: {len(found)} tip edges')
    return found[0]


def createHandlePin(component: adsk.fusion.Component) -> list[adsk.fusion.BRepBody]:
    """Draws the pin into the given empty component (part frame as handlePin.f3d) with its joint origin, returns its
    body"""
    plane = _tipPlane(component)
    y, z = AXIS
    profile = WorldSketch(component, plane, 'Pin profile')
    for diameter in DIAMETERS:
        profile.circle((_mm(X_TIP), _mm(y), _mm(z)), _mm(diameter))
    [shaft, tipRing, headRing] = profile.profilesByArea([
        _ringArea(0, SHAFT_DIAMETER), _ringArea(SHAFT_DIAMETER, TIP_DIAMETER), _ringArea(TIP_DIAMETER, HEAD_DIAMETER)])
    profile.sketch.isVisible = False

    newBody = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    join = adsk.fusion.FeatureOperations.JoinFeatureOperation
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    body = _extrude(component, [shaft], newBody, X_END - X_TIP, name='Shaft').bodies.item(0)
    body.name = BODY_NAME
    _extrude(component, [tipRing], join, X_SHOULDER - X_TIP, body=body, name='Tip')
    _extrude(component, [tipRing, headRing], join, X_END - X_HEAD, start=X_HEAD - X_TIP, body=body, name='Head')

    chamfers = component.features.chamferFeatures
    chamferInput = chamfers.createInput2()
    chamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        collection([_tipEdge(body)]), lengthInput(_mm(CHAMFER)), True)
    chamfers.add(chamferInput).name = 'Tip chamfer'

    cuts = WorldSketch(component, plane, 'Pin cuts')
    points, lines = cutSketch()
    world = [(_mm(X_TIP), _mm(a), _mm(b)) for a, b in points]
    for a, b in lines:
        cuts.line(world[a], world[b])
    boxes = _cutBoxes()
    names = [name for name, _, _ in cutRanges()]
    found = cuts.profiles([tuple(tuple(_mm(v) for v in corner) for corner in boxes[name]) for name in names])
    cuts.sketch.isVisible = False
    for (name, x0, x1), cutProfile in zip(cutRanges(), found):
        _extrude(component, [cutProfile], cut, x1 - x0, start=x0 - X_TIP if x0 != X_TIP else None, body=body,
                 name=f'Cut {name}')

    addJointOrigin(component)
    return [body]


def addJointOrigin(component: adsk.fusion.Component):
    """The pin's joint origin as handlePin.f3d's; apart from the drawing since round 47 (p591): a pin copied into a box set
    (predBoxInsert) gets it the same way"""
    from .jointOriginLayout import createOffsetJointOrigins

    jointName, (jx, jy, jz) = JOINT_ORIGIN
    createOffsetJointOrigins([(jointName, _mm(jx), _mm(jy), _mm(jz))], component, name='Seat')
