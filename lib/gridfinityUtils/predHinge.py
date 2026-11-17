"""
Pred's hinges (components Hinge_M3x30, Hinge_Pined and Hinge of Pred's parametric Gridfinity Storage Box v1.1,
https://www.printables.com/model/543553, CC BY-NC, by Pred) drawn in code, round 29 (Nutzer 17.11.2026: "Wir zeichnen die
Teile im Code.", "Am besten doch alle Scharniere mit Auswahl im Generator."). Until round 28 they were inserted from
resources/predBox/hinge*.f3d, which fails in the execute of a command with inputs (fusion-auftraege/r28_cmdvariants.log).

Each hinge lies in Pred's part frame (that of its .f3d), in print position: the knuckles' axis along z through
(CENTER x | 0), the leaves standing up in +y, length 0..31.6 in z. Pred's steps are read in
fusion-auftraege/r29_walk/Hinge_M3x30.json, Hinge_Pined.json and Hinge.json; the plan, and why it is built this way, in
dev-notes/r29/hinge-plan.md. The three variants share one shape (a U of two leaves on a bar, three knuckles); they differ
in the radii, the leaves' thickness and depth, and their extras (M3x30: screw hole, nut trap, counterbore with bridges;
Pinned: hole for the printed pin, two counterbores, the pin; Plain: the knuckles turn on a core printed in place).
Pred's measures hang on the box's slot (HingeSlotLength 32, Depth 9, Width 2, FromBack 3) and the tolerance 0.15; they
are values here (no user parameters). Every sketch is fully constrained (predSketch, sketchChain; Nutzer: "Denk nur dran,
dass alle Zeichnungen vollständig bestimmt sein müssen."). No mirrored features (README of round 29, Mirror6): Pred's
Mirror2/3/4 are built as counterparts. Values here are mm, Fusion gets cm.
Tested in tests/test_pred_hinge.py, the shape against Pred's in fusion-auftraege/r29_hinge_check.py.
"""

import json
import math
import os
from dataclasses import dataclass

import adsk.core, adsk.fusion

from .dim import Dim, valueInput
from .predSketch import WorldSketch, collection

# -- Pred's slot and tolerance ----------------------------------------------------------------------------------------

SLOT_LENGTH = 32.0
SLOT_DEPTH = 9.0
SLOT_WIDTH = 2.0
SLOT_FROM_BACK = 3.0
TOLERANCE = 0.15

LENGTH = SLOT_LENGTH - 0.4
THIRD = (SLOT_LENGTH - 2 * TOLERANCE) / 3
GAP = TOLERANCE
BOTTOM = TOLERANCE          # the leaves' and bar's underside (Pred's line HingeTolerane above y 0)
BAR_TOP = 2.5
# Pred's slot model in HingeBaseTopology: its back wall's corner (y BAR_TOP + 0.2) lies on the clearance circle, its
# inner corner is chamfered 1 x 1; the leaves sit in it with an inset
SLOT_MODEL_Y = BAR_TOP + 0.2
SLOT_MODEL_CHAMFER = 1.0


@dataclass(frozen=True)
class HingeShape:
    pred: str
    bodyNames: tuple
    knuckle: float          # radius of the knuckles
    clearance: float        # radius cut free around a knuckle where the other leaf's bar passes
    core: float             # radius of the core through the knuckles (screw / pin hole, or the printed core)
    leafWidth: float
    leafDepth: float
    inset: float            # the leaves' and the bar chamfer's distance inside Pred's slot model
    rightLeaf: float = None  # x of the right leaf's outer face where Pred fixed it (Plain: 60 mm from the origin)


SHAPES = {
    'M3x30': HingeShape('Hinge_M3x30', ('BottomHingePart_M3x30', 'TopHingePart_M3x30'),
                        knuckle=8 / 2, clearance=(8 + 2 * TOLERANCE) / 2, core=3.5 / 2,
                        leafWidth=SLOT_WIDTH - 0.4, leafDepth=SLOT_DEPTH - 0.2, inset=0.2),
    'Pinned': HingeShape('Hinge_Pined', ('BottomHingePart_M3x30', 'TopHingePart_M3x30', 'Hinge pin'),
                         knuckle=8 / 2, clearance=(8 + 2 * TOLERANCE) / 2, core=3.5 / 2,
                         leafWidth=SLOT_WIDTH - 0.4, leafDepth=SLOT_DEPTH - 0.2, inset=0.2),
    'Plain': HingeShape('Hinge', ('BottomHingePart', 'TopHingePart'),
                        knuckle=7 / 2, clearance=(7 + 3 * TOLERANCE) / 2, core=4 / 2,
                        leafWidth=SLOT_WIDTH - 0.2, leafDepth=SLOT_DEPTH - 0.5, inset=0.1, rightLeaf=-60.0),
}
# Plain: Pred's HingeInnerDiameter + 2 HingeTolerane, the hole of the middle knuckle around the printed core
PLAIN_HOLE = (4 + 2 * TOLERANCE) / 2


def _halfWidths(shape: HingeShape):
    """(slot model's back, leaf inner, leaf outer, bar end, bar chamfer's top) about the axis, mm"""
    back = math.sqrt(shape.clearance ** 2 - SLOT_MODEL_Y ** 2)
    inner = back + SLOT_FROM_BACK + shape.inset
    outer = inner + shape.leafWidth
    # the bar chamfer runs parallel to the slot model's (45 degrees through its inner corner) at the inset
    line = back + SLOT_FROM_BACK - SLOT_MODEL_CHAMFER - SLOT_MODEL_Y + shape.inset * math.sqrt(2)
    return back, inner, outer, line + BAR_TOP, inner - line


def center(shape: HingeShape) -> float:
    """x of the knuckles' axis: 0, Plain's from its right leaf at -60"""
    if shape.rightLeaf is None:
        return 0.0
    return shape.rightLeaf - _halfWidths(shape)[2]


def outline(shape: HingeShape):
    """Pred's HingeBaseTopology outline: two leaves on a bar, from the left leaf's top outer corner (x, y in mm)"""
    _, inner, outer, barEnd, chamferTop = _halfWidths(shape)
    c = center(shape)
    depth = shape.leafDepth
    half = [(-outer, depth), (-outer, BOTTOM), (outer, BOTTOM), (outer, depth), (inner, depth), (inner, chamferTop),
            (barEnd, BAR_TOP), (-barEnd, BAR_TOP), (-inner, chamferTop), (-inner, depth)]
    return [(c + x, y) for x, y in half]


def sectionSketch(shape: HingeShape):
    """Points and curves (sketchChain) of the section: the outline and the knuckle circle; all its profiles together
    are the body before the cuts (Pred's Extrude1/2/6/7/13 together: his clearance ring above the bar is cut away
    again over the whole length by Extrude17/18/19)"""
    points = outline(shape)
    curves = [{'kind': 'line', 'a': i, 'b': (i + 1) % len(points)} for i in range(len(points))]
    points.append((center(shape), 0.0))
    curves.append({'kind': 'circle', 'center': len(points) - 1})
    return points, curves


CLEARANCE_SECTOR = 80.0     # degrees above and below the horizontal on the cut side


def clearanceSketch(shape: HingeShape, side: int):
    """Points and curves of the ring between knuckle and clearance on one side of the axis (side -1 left, +1 right), as
    the sector 80 degrees above and below the horizontal. It covers the ring where the bar passes (y 0.15..2.5, within
    some 40 degrees); the rest of the ring is never solid. Not split on the axis: an outline on the world axes has no
    point to start its chain from (sketchChain.anchor)"""
    c = center(shape)
    a = math.radians(CLEARANCE_SECTOR)
    ends = []
    for radius in (shape.clearance, shape.knuckle):
        for sign in (1, -1):
            ends.append((c + side * radius * math.cos(a), sign * radius * math.sin(a)))
    points = ends + [(c, 0.0)]
    # outer arc top to bottom, line in, inner arc bottom to top, line out
    curves = [{'kind': 'arc', 'center': 4, 'start': 0, 'end': 1}, {'kind': 'line', 'a': 1, 'b': 3},
              {'kind': 'arc', 'center': 4, 'start': 3, 'end': 2}, {'kind': 'line', 'a': 2, 'b': 0}]
    return points, curves


def clearanceRanges():
    """(side, z from, z to): Pred's Extrude17/18 free the left bar from the outer knuckles, Extrude19 the right one from
    the middle knuckle"""
    return [(-1, 0.0, THIRD + GAP), (-1, LENGTH - THIRD - GAP, LENGTH), (1, THIRD, LENGTH - THIRD)]


def gapRanges():
    """Pred's Extrude20/21: the gaps between the knuckles"""
    return [(THIRD, THIRD + GAP), (LENGTH - THIRD - GAP, LENGTH - THIRD)]


def circlesSketch(cx: float, count: int):
    """Points and curves of 'count' circles about the axis (cx | 0). Their centre lies on a world axis, which the chain
    cannot dimension from the origin (no zero dimensions, no alignment to the origin): it hangs on a construction line
    from a point off the axes"""
    points = [(cx + 1.0, 1.0), (cx, 0.0)]
    curves = [{'kind': 'line', 'a': 0, 'b': 1, 'construction': True}]
    return points, curves + [{'kind': 'circle', 'center': 1} for _ in range(count)]


# -- the tabs (Pred's HingeTabDetails, Extrude14, Chamfer1/2, Mirror2/3) -------------------------------------------------

TAB_HEIGHT = 1.3
TAB_Y = (3.0, 5.6)
TAB_LENGTH = 5.8
TAB_FROM_END = 7.8          # the tab's middle below the end z LENGTH
TAB_CORNER = 1.2            # Chamfer1, equal distance, on the four edges across the tab
TAB_RAMP = 1.3              # Chamfer2 on the tab's outer top edge


def tabOctagon(lower: bool):
    """The tab's section on the leaf (y, z in mm): Pred's rectangle with Chamfer1's corners cut, as the sketch draws it
    (an extruded rectangle chamfered across is this octagon extruded). lower: Mirror2's counterpart at z LENGTH / 2"""
    y0, y1 = TAB_Y
    middle = LENGTH - TAB_FROM_END
    z0, z1 = middle - TAB_LENGTH / 2, middle + TAB_LENGTH / 2
    k = TAB_CORNER
    points = [(y0 + k, z0), (y1 - k, z0), (y1, z0 + k), (y1, z1 - k), (y1 - k, z1), (y0 + k, z1), (y0, z1 - k), (y0, z0 + k)]
    if lower:
        points = [(y, LENGTH - z) for y, z in points]
    return points


def tabRampEdge(shape: HingeShape, side: int, lower: bool):
    """Chamfer2's edge: the tab's outer top edge along z, as ((x, y, z), (x, y, z)) in mm; side -1 left, +1 right"""
    outer = _halfWidths(shape)[2] + TAB_HEIGHT
    zs = sorted(z for y, z in tabOctagon(lower) if abs(y - TAB_Y[1]) < 1e-9)
    x = center(shape) + side * outer
    return (x, TAB_Y[1], zs[0]), (x, TAB_Y[1], zs[-1])


# -- M3x30: nut trap, screw hole, counterbore and bridges (Sketch3/4/5, Extrude22-26) --------------------------------

NUT_FLATS = 5.5
NUT_DEPTH = 3.5
COUNTERBORE = 5.5
COUNTERBORE_DEPTH = 3.5 + 0.4
THIN_BRIDGE = 0.2
THICK_BRIDGE = 0.4


def hexagon(cx: float):
    """Pred's Sketch3: a regular hexagon across flats NUT_FLATS about the axis, flats parallel to x (x, y in mm)"""
    r = NUT_FLATS / math.sqrt(3)
    h = NUT_FLATS / 2
    return [(cx + r, 0.0), (cx + r / 2, h), (cx - r / 2, h), (cx - r, 0.0), (cx - r / 2, -h), (cx + r / 2, -h)]


def _bridgeLines():
    """Pred's Sketch5 lines about the axis: a square and a square turned 45 degrees, all tangent to the screw hole
    (r 1.75), as chords of the counterbore (r 2.75)"""
    r = COUNTERBORE / 2
    a = SHAPES['M3x30'].core
    e = math.sqrt(r * r - a * a)
    lines = [((-e, a), (e, a)), ((-e, -a), (e, -a)), ((a, -e), (a, e)), ((-a, -e), (-a, e))]
    d = a * math.sqrt(2)
    m, h = d / 2, e / math.sqrt(2)
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        # the chord sx x + sy y = d
        lines.append(((sx * (m + h), sy * (m - h)), (sx * (m - h), sy * (m + h))))
    return lines


def bridgeSketch(cx: float):
    """Points and curves of the bridge sketch: the counterbore circle and Pred's eight lines (without his projected
    screw hole circle: no profile we extrude touches it but at a tangent point, see bridgeLayers)"""
    points, curves = [], []
    for (x0, y0), (x1, y1) in _bridgeLines():
        points += [(cx + x0, y0), (cx + x1, y1)]
        curves.append({'kind': 'line', 'a': len(points) - 2, 'b': len(points) - 1})
    # the circle last: its centre may lie on the origin and hangs on the lines' points
    points.append((cx, 0.0))
    curves.append({'kind': 'circle', 'center': len(points) - 1})
    return points, curves


def bridgeLayers(x: float, y: float):
    """The bridge layers (THIN_BRIDGE, THICK_BRIDGE) a profile of the bridge sketch goes into, from its box centre (x, y
    about the axis, world). Pred (Extrude25/26): the four tips beyond both 45-degree chords into both; the pieces beyond
    the squares in the quadrants x y < 0 into the thin layer, x y > 0 into the thick one; the pieces on the axes inside
    the 45-degree chords, and everything inside the squares but their corners, into none.
    Tested against all 33 of Pred's profiles in tests/test_pred_hinge.py"""
    near = min(abs(x), abs(y)) < 0.3
    distance = math.hypot(x, y)
    if near:
        return (THIN_BRIDGE, THICK_BRIDGE) if distance > 2.4 else ()
    if distance < 1.7:
        return ()
    return (THIN_BRIDGE,) if x * y < 0 else (THICK_BRIDGE,)


# -- Pinned: the printed pin (Pred's Body21: Sketch6/7, Extrude27-32, Chamfer3/4, Fillet1) -----------------------------

PIN_HEAD = 5.1 / 2          # Sketch6: the counterbore circle offset -0.2
PIN_SHAFT = 4.1 / 2         # Sketch6: the hole circle (d 4.5) offset -0.2
PIN_HEAD_LENGTH = 3.3
PIN_INNER_CHAMFER = 0.5     # Chamfer4, on the concave edges where the shaft meets the heads
PIN_TIP_ACROSS = 1.5        # Chamfer3, two distances: across the end face
PIN_TIP_ALONG = 2.5         #   and along the head
PIN_SLOT = 1.0              # Sketch7, Extrude30: 1 wide, 7.5 deep from the head end
PIN_SLOT_DEPTH = 7.5
PIN_FLAT = math.sqrt(PIN_HEAD ** 2 - 2.0 ** 2)   # Sketch7's lines x = +-2 end on the head circle
PIN_FILLET = 0.5            # Fillet1 on the slot's bottom edges
PIN_HOLE = 4.5 / 2          # the hole through the knuckles (Sketch4 circle d 4.5, Extrude23)
PIN_HOLE_CHAMFER = 0.5      # Chamfer5 (two distances 0.5 / 0.5) at the counterbores' floor


def pinProfile():
    """Half section of the pin about its axis (r, z in mm), heads, shaft and chamfers as a revolve: the two-distance
    chamfer is drawn, so it has no side to choose"""
    z = LENGTH
    return [(0.0, 0.0), (PIN_HEAD, 0.0), (PIN_HEAD, PIN_HEAD_LENGTH), (PIN_SHAFT, PIN_HEAD_LENGTH + PIN_INNER_CHAMFER),
            (PIN_SHAFT, z - PIN_HEAD_LENGTH - PIN_INNER_CHAMFER), (PIN_HEAD, z - PIN_HEAD_LENGTH),
            (PIN_HEAD, z - PIN_TIP_ALONG), (PIN_HEAD - PIN_TIP_ACROSS, z), (0.0, z)]


def pinCuts():
    """(name, outline (x, y in mm about the axis), z from, z to): Extrude31's flat over the whole length; Extrude30's slot
    and Extrude32's other flat over the slot's depth, as one T-shaped profile. The outlines reach past the heads
    (Pred's do too: his slot is 7 long)"""
    w = PIN_HEAD + 0.05
    s = PIN_SLOT / 2
    flat = [(-w, PIN_FLAT), (w, PIN_FLAT), (w, w), (-w, w)]
    slot = [(-w, -w), (w, -w), (w, -PIN_FLAT), (s, -PIN_FLAT), (s, w), (-s, w), (-s, -PIN_FLAT), (-w, -PIN_FLAT)]
    return [('Pin flat', flat, 0.0, LENGTH), ('Pin slot', slot, LENGTH - PIN_SLOT_DEPTH, LENGTH)]


# -- drawing in Fusion ---------------------------------------------------------------------------------------------------

_EDGE_TOLERANCE = 2e-3      # mm; Pred's edges are read rounded to 0.0001
_EDGES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'predHingeEdges.json')


def _mm(value: float) -> Dim:
    return Dim.length(value / 10)


def _world(x, y, z):
    return (_mm(x), _mm(y), _mm(z))


def _plane(component: adsk.fusion.Component, axis: int, at: float, name: str):
    """The base plane normal to the axis (0 x, 1 y, 2 z), or its offset at the coordinate 'at' (mm); the offset's side
    is checked as in predBoxGenerator.offsetPlane"""
    base = (component.yZConstructionPlane, component.xZConstructionPlane, component.xYConstructionPlane)[axis]
    if abs(at) < 1e-9:
        return base
    planes = component.constructionPlanes
    target = at / 10
    for sign in (1, -1):
        planeInput = planes.createInput()
        planeInput.setByOffset(base, valueInput(_mm(at * sign)))
        plane = planes.add(planeInput)
        origin = plane.geometry.origin
        if abs((origin.x, origin.y, origin.z)[axis] - target) < 1e-6:
            plane.name = name
            plane.isLightBulbOn = False
            return plane
        plane.deleteMe()
    raise ValueError(f'hinge: no plane {name}')


def _sketchAxis(sketch: adsk.fusion.Sketch, axis: int):
    """(the sketch plane's coordinate along the axis in mm, the sign of its normal along it)"""
    origin, xAxis, yAxis, _ = sketch.transform.getAsCoordinateSystem()
    normal = xAxis.crossProduct(yAxis)
    return (origin.x, origin.y, origin.z)[axis] * 10, (1 if (normal.x, normal.y, normal.z)[axis] > 0 else -1)


def _extrude(component, profiles, operation, start: float, end: float, axis: int = 2, bodies=None, name=None):
    """Extrude the profiles from 'start' to 'end' along the axis (world coordinates, mm)"""
    features = component.features.extrudeFeatures
    plane, sign = _sketchAxis(profiles[0].parentSketch, axis)
    extrudeInput = features.createInput(collection(profiles), operation)
    extrudeInput.setDistanceExtent(False, valueInput(_mm((end - start) * sign)))
    if abs(start - plane) > 1e-9:
        extrudeInput.startExtent = adsk.fusion.OffsetStartDefinition.create(valueInput(_mm((start - plane) * sign)))
    if bodies is not None:
        extrudeInput.participantBodies = list(bodies)
    feature = features.add(extrudeInput)
    if name:
        feature.name = name
    return feature


def _drawPlan(component, plane, name, points, curves, at=0.0, axis=2, diameters=()):
    """A WorldSketch from a plan: points are the plane's two world coordinates in mm, (x, y) at z = at for axis 2,
    (y, z) at x = at for axis 0; circles take the diameters (mm) in their order"""
    sketch = WorldSketch(component, plane, name)

    def world(p):
        return _world(p[0], p[1], at) if axis == 2 else _world(at, p[0], p[1])
    sizes = iter(diameters)
    for curve in curves:
        if curve['kind'] == 'line':
            sketch.line(world(points[curve['a']]), world(points[curve['b']]), curve.get('construction', False))
        elif curve['kind'] == 'arc':
            sketch.arc(world(points[curve['center']]), world(points[curve['start']]), world(points[curve['end']]))
        else:
            sketch.circle(world(points[curve['center']]), _mm(next(sizes)))
    sketch.close()
    sketch.sketch.isVisible = False
    return sketch


def _polygonPlan(points):
    return points, [{'kind': 'line', 'a': i, 'b': (i + 1) % len(points)} for i in range(len(points))]




def _ringArea(inner: float, outer: float) -> float:
    return math.pi * (outer ** 2 - inner ** 2)


def _profileCentre(sketch: WorldSketch, profile):
    """World x, y (mm) of the centre of the profile's box"""
    box = profile.boundingBox
    middle = adsk.core.Point3D.create((box.minPoint.x + box.maxPoint.x) / 2, (box.minPoint.y + box.maxPoint.y) / 2, 0)
    p = sketch.sketch.sketchToModelSpace(middle)
    return p.x * 10, p.y * 10


# -- edges -------------------------------------------------------------------------------------------------------------

def _close(a, b):
    return max(abs(x - y) for x, y in zip(a, b)) < _EDGE_TOLERANCE


def _mmPoint(point):
    return (point.x * 10, point.y * 10, point.z * 10)


def _ends(edge, p, q):
    a, b = _mmPoint(edge.startVertex.geometry), _mmPoint(edge.endVertex.geometry)
    return (_close(a, p) and _close(b, q)) or (_close(a, q) and _close(b, p))


def _edgeMatches(edge, item) -> bool:
    """An edge as Pred's lists give it (mm, part frame): line ends, arc centre, radius and ends, circle centre and
    radius"""
    geometry = edge.geometry
    if 'line' in item:
        return adsk.core.Line3D.cast(geometry) is not None and _ends(edge, *item['line'])
    if 'arc' in item:
        arc = adsk.core.Arc3D.cast(geometry)
        c, r, p, q = item['arc']
        return (arc is not None and _close(_mmPoint(arc.center), c) and abs(arc.radius * 10 - r) < _EDGE_TOLERANCE
                and _ends(edge, p, q))
    circle = adsk.core.Circle3D.cast(geometry)
    c, r = item['circle']
    return circle is not None and _close(_mmPoint(circle.center), c) and abs(circle.radius * 10 - r) < _EDGE_TOLERANCE


def _edges(bodies, items, label):
    found = []
    for item in items:
        match = [edge for body in bodies for edge in body.edges if _edgeMatches(edge, item)]
        if len(match) != 1:
            raise ValueError(f'hinge {label}: {len(match)} edges for {item}')
        found.append(match[0])
    return found


def _chamfer(component, bodies, items, distance: float, name: str):
    chamfers = component.features.chamferFeatures
    chamferInput = chamfers.createInput2()
    chamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        collection(_edges(bodies, items, name)), valueInput(_mm(distance)), True)
    feature = chamfers.add(chamferInput)
    feature.name = name
    return feature


def predChamfers(variant: str):
    """Pred's chamfers on leaves and knuckles, in his order: [{'pred', 'distance', 'edges'}] (predHingeEdges.json, made
    from fusion-auftraege/r29_walk by dev-notes/r29/hinge-edges-gen.py; mm, part frame)"""
    with open(_EDGES_FILE, encoding='utf-8') as f:
        return json.load(f).get(variant, [])


# -- the parts ---------------------------------------------------------------------------------------------------------

def _base(component, shape: HingeShape):
    """Leaves, bar and knuckles in one body, the clearances and gaps cut (Pred's Extrude1-21 without the tabs)"""
    xy = component.xYConstructionPlane
    newBody = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    c = center(shape)

    points, curves = sectionSketch(shape)
    section = _drawPlan(component, xy, 'Hinge section', points, curves, diameters=[2 * shape.knuckle])
    _extrude(component, list(section.sketch.profiles), newBody, 0.0, LENGTH, name='Hinge body')

    for side, label in ((-1, 'left'), (1, 'right')):
        points, curves = clearanceSketch(shape, side)
        sketch = _drawPlan(component, xy, f'Clearance {label}', points, curves)
        (profile,) = list(sketch.sketch.profiles)
        for number, (_, z0, z1) in enumerate([r for r in clearanceRanges() if r[0] == side]):
            _extrude(component, [profile], cut, z0, z1, name=f'Clearance {label} {number + 1}')

    radii = [shape.core] + ([PLAIN_HOLE] if shape is SHAPES['Plain'] else []) + [shape.clearance]
    points, curves = circlesSketch(c, len(radii))
    gaps = _drawPlan(component, xy, 'Gaps', points, curves, diameters=[2 * r for r in radii])
    rings = gaps.profilesByArea([_ringArea(a, b) for a, b in zip(radii, radii[1:])])
    for number, (z0, z1) in enumerate(gapRanges()):
        _extrude(component, rings, cut, z0, z1, name=f'Gap {number + 1}')
    if shape is SHAPES['Plain']:
        # the middle knuckle turns on the core (Pred's Extrude7 left out the ring inside HingeInnerDiameter + 2 tol.)
        _extrude(component, rings[:1], cut, THIRD + GAP, LENGTH - THIRD - GAP, name='Knuckle hole')


def _tabs(component, shape: HingeShape):
    """Pred's four tabs: Extrude14 with Chamfer1 drawn as octagons, Mirror2/3 as counterparts, Chamfer2 on each"""
    join = adsk.fusion.FeatureOperations.JoinFeatureOperation
    c = center(shape)
    outer = _halfWidths(shape)[2]
    for side, label in ((-1, 'left'), (1, 'right')):
        x = c + side * outer
        plane = _plane(component, 0, x, f'Leaf {label}')
        points, curves = [], []
        for lower in (False, True):
            octagon, lines = _polygonPlan(tabOctagon(lower))
            curves += [{'kind': 'line', 'a': l['a'] + len(points), 'b': l['b'] + len(points)} for l in lines]
            points += octagon
        sketch = _drawPlan(component, plane, f'Tabs {label}', points, curves, at=x, axis=0)
        _extrude(component, list(sketch.sketch.profiles), join, x, x + side * TAB_HEIGHT, axis=0, name=f'Tabs {label}')
    ramps = [{'line': list(tabRampEdge(shape, side, lower))} for side in (-1, 1) for lower in (False, True)]
    _chamfer(component, list(component.bRepBodies), ramps, TAB_RAMP, 'Tab ramps')


def _bottomTop(component, shape: HingeShape):
    """(Bottom, Top): the body with the left leaf, the one with the right, named as Pred's"""
    c = center(shape)
    bodies = sorted(component.bRepBodies, key=lambda b: b.boundingBox.minPoint.x)
    if len(bodies) != 2:
        raise ValueError(f'hinge: {len(bodies)} bodies, expected 2')
    if not bodies[0].boundingBox.minPoint.x * 10 < c - shape.knuckle - 1 < bodies[1].boundingBox.minPoint.x * 10:
        raise ValueError('hinge: the bodies are not parted at the axis')
    bottom, top = bodies
    bottom.name, top.name = shape.bodyNames[0], shape.bodyNames[1]
    return bottom, top


def _m3x30(component, shape: HingeShape):
    """Nut trap, screw hole (parts the body), counterbore and its two bridge layers (Pred's Sketch3-5, Extrude22-26)"""
    xy = component.xYConstructionPlane
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    join = adsk.fusion.FeatureOperations.JoinFeatureOperation
    c = center(shape)
    points, curves = _polygonPlan(hexagon(c))
    nut = _drawPlan(component, xy, 'Nut trap', points, curves)
    _extrude(component, list(nut.sketch.profiles), cut, LENGTH - NUT_DEPTH, LENGTH, name='Nut trap')
    points, curves = circlesSketch(c, 2)
    holes = _drawPlan(component, xy, 'Screw hole', points, curves, diameters=[2 * shape.core, COUNTERBORE])
    core, ring = holes.profilesByArea([_ringArea(0, shape.core), _ringArea(shape.core, COUNTERBORE / 2)])
    _extrude(component, [core], cut, 0.0, LENGTH - NUT_DEPTH, name='Screw hole')
    bottom, top = _bottomTop(component, shape)
    _extrude(component, [ring], cut, 0.0, COUNTERBORE_DEPTH, bodies=[top], name='Counterbore')

    plane = _plane(component, 2, COUNTERBORE_DEPTH, 'Counterbore floor')
    points, curves = bridgeSketch(c)
    bridges = _drawPlan(component, plane, 'Bridges', points, curves, at=COUNTERBORE_DEPTH, diameters=[COUNTERBORE])
    centres = [(profile, _profileCentre(bridges, profile)) for profile in bridges.sketch.profiles]
    for layer, label in ((THIN_BRIDGE, 'thin'), (THICK_BRIDGE, 'thick')):
        chosen = [profile for profile, (x, y) in centres if layer in bridgeLayers(x - c, y)]
        if len(chosen) != 12:
            raise ValueError(f'hinge: {len(chosen)} profiles for the {label} bridge, Pred has 12')
        _extrude(component, chosen, join, COUNTERBORE_DEPTH, COUNTERBORE_DEPTH - layer, bodies=[top],
                 name=f'Bridge {label}')
    return bottom, top


def _pinned(component, shape: HingeShape):
    """Hole for the pin (parts the body), a counterbore at each end with its chamfer (Pred's Extrude23/24, Chamfer5,
    Mirror4 as the counterpart)"""
    xy = component.xYConstructionPlane
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    c = center(shape)
    points, curves = circlesSketch(c, 2)
    holes = _drawPlan(component, xy, 'Pin hole', points, curves, diameters=[2 * PIN_HOLE, COUNTERBORE])
    core, ring = holes.profilesByArea([_ringArea(0, PIN_HOLE), _ringArea(PIN_HOLE, COUNTERBORE / 2)])
    _extrude(component, [core], cut, 0.0, LENGTH, name='Pin hole')
    bottom, top = _bottomTop(component, shape)
    _extrude(component, [ring], cut, 0.0, COUNTERBORE_DEPTH, bodies=[top], name='Counterbore 1')
    _extrude(component, [ring], cut, LENGTH - COUNTERBORE_DEPTH, LENGTH, bodies=[top], name='Counterbore 2')
    floors = [{'circle': [(c, 0.0, z), PIN_HOLE]} for z in (COUNTERBORE_DEPTH, LENGTH - COUNTERBORE_DEPTH)]
    _chamfer(component, [top], floors, PIN_HOLE_CHAMFER, 'Counterbore chamfers')
    return bottom, top


def _pin(component, shape: HingeShape):
    """Pred's printed pin (Body21): a revolve of its half section, the flat and the slot cut, the slot's bottom rounded"""
    c = center(shape)
    newBody = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    section = WorldSketch(component, component.xZConstructionPlane, 'Pin section')
    profile = pinProfile()
    for (r0, z0), (r1, z1) in zip(profile, profile[1:] + profile[:1]):
        section.line(_world(c + r0, 0.0, z0), _world(c + r1, 0.0, z1))
    section.close()
    section.sketch.isVisible = False
    revolves = component.features.revolveFeatures
    revolveInput = revolves.createInput(section.sketch.profiles.item(0), component.zConstructionAxis, newBody)
    revolveInput.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
    feature = revolves.add(revolveInput)
    feature.name = 'Pin'
    pin = feature.bodies.item(0)
    pin.name = shape.bodyNames[2]
    for name, outline_, z0, z1 in pinCuts():
        points, curves = _polygonPlan([(c + x, y) for x, y in outline_])
        sketch = _drawPlan(component, component.xYConstructionPlane, name, points, curves)
        _extrude(component, list(sketch.sketch.profiles), cut, z0, z1, bodies=[pin], name=name)
    z = LENGTH - PIN_SLOT_DEPTH
    slotEdges = [{'line': [(c + x, -PIN_FLAT, z), (c + x, PIN_FLAT, z)]} for x in (-PIN_SLOT / 2, PIN_SLOT / 2)]
    fillets = component.features.filletFeatures
    filletInput = fillets.createInput()
    filletInput.edgeSetInputs.addConstantRadiusEdgeSet(
        collection(_edges([pin], slotEdges, 'pin slot')), valueInput(_mm(PIN_FILLET)), True)
    fillets.add(filletInput).name = 'Pin slot rounding'
    return pin


def createHinge(component: adsk.fusion.Component, hinge: str) -> list[adsk.fusion.BRepBody]:
    """Draws the hinge (a key of predBoxParts.HINGES) into the given empty component, in Pred's part frame and print
    position; returns its bodies in Pred's order and with his names (his printed pin as 'Hinge pin')"""
    shape = SHAPES[hinge]
    _base(component, shape)
    _tabs(component, shape)
    if hinge == 'M3x30':
        bodies = list(_m3x30(component, shape))
    elif hinge == 'Pinned':
        bodies = list(_pinned(component, shape))
    else:
        bodies = list(_bottomTop(component, shape))
    for step in predChamfers(hinge):
        _chamfer(component, bodies, step['edges'], step['distance'], f'Pred {step["pred"]}')
    if hinge == 'Pinned':
        bodies.append(_pin(component, shape))
    return bodies
