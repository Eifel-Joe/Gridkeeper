"""
Fully constrained sketches drawn from world coordinates, for the box after Pred (round 27).

Shapes are given with points as three dims in the box's frame (cm). The sketch collects them and, on close(), draws and
binds them the way the existing generators do (the shapes way, as decided):
- rounded rectangles as in baseGenerator: sketchUtils.createRectangle, four fillets, equal radii, one radius dimension;
- every other shape as a chain (sketchChain): its first point from the origin, every further point with dimensions to
  points already fixed, real horizontal and vertical lines with that condition; circles by centre and diameter.
Dimensions get the expression abs(a - b) of the world dims, so the sketch follows the box parameters. Sketch planes must
be the component's base planes or offsets of them, so the sketch origin lies on the world axes of the plane.
"""

import math
import adsk.core, adsk.fusion

from .dim import Dim, applyTo, lengthExpression
from .sketchUtils import deferSketchCompute, createRectangle
from . import sketchChain

_EPS = 1e-7


def _axis(vector):
    values = (vector.x, vector.y, vector.z)
    index = max(range(3), key=lambda i: abs(values[i]))
    return index, (1 if values[index] > 0 else -1)


def _value(dim):
    return dim.value if isinstance(dim, Dim) else dim


def _dim(value):
    return value if isinstance(value, Dim) else Dim.length(value)


def fixablePoints(worldPoints, xAxis, yAxis) -> set:
    """
    The points whose two sketch coordinates are plain numbers, no expression on a box parameter in them (round 39,
    p480): such a point never moves when a parameter changes, the chain fixes it in place instead of binding it with two
    dimensions, see sketchChain. The coordinate along the sketch's normal is left aside, it only places the plane
    """
    def plain(value):
        # by the kind, not by class: tests load the dim module more than once
        return not getattr(value, 'isExpression', False)
    return {index for (index, world) in enumerate(worldPoints) if plain(world[xAxis[0]]) and plain(world[yAxis[0]])}


class WorldSketch:
    def __init__(self, component: adsk.fusion.Component, plane, name: str):
        self.component = component
        self.sketch: adsk.fusion.Sketch = component.sketches.add(plane)
        self.sketch.name = name
        origin, xAxis, yAxis, _ = self.sketch.transform.getAsCoordinateSystem()
        self.xAxis = _axis(xAxis)
        self.yAxis = _axis(yAxis)
        originValues = (origin.x, origin.y, origin.z)
        if abs(originValues[self.xAxis[0]]) > _EPS or abs(originValues[self.yAxis[0]]) > _EPS:
            raise ValueError(f'sketch {name}: the plane must pass through the world axes')
        self.worldPoints = []
        self.pointIndex = {}
        self.curves = []
        self.roundedRectangles = []
        self.closed = False
        # see isInMm and _drive (round 59); from the sketch made, the latch passes a stand-in for the component that
        # only adds the sketch (predLatch._faceSketch), it has no design
        self.isDocumentInMm = isInMm(getattr(getattr(self.sketch, 'parentComponent', None), 'parentDesign', None))

    # -- collecting ------------------------------------------------------------------------------------------------

    def point(self, world) -> int:
        key = tuple(round(_value(v) * 1e5) for v in world)
        if key not in self.pointIndex:
            self.pointIndex[key] = len(self.worldPoints)
            self.worldPoints.append(world)
        return self.pointIndex[key]

    def line(self, start, end, construction=False):
        self.curves.append({'kind': 'line', 'a': self.point(start), 'b': self.point(end), 'construction': construction})

    def polyline(self, points, closed=True):
        for a, b in zip(points, points[1:]):
            self.line(a, b)
        if closed:
            self.line(points[-1], points[0])

    def rectangle(self, a, b, c, d):
        self.polyline([a, b, c, d])

    def arc(self, center, start, end):
        """The shorter arc from start to end around center (Pred's arcs are at most 180 degrees)"""
        self.curves.append({'kind': 'arc', 'center': self.point(center), 'start': self.point(start), 'end': self.point(end)})

    def circle(self, center, diameter: Dim):
        self.curves.append({'kind': 'circle', 'center': self.point(center), 'diameter': _dim(diameter)})

    def roundedRectangle(self, x0, y0, x1, y1, z, radius: Dim):
        """Axis-parallel rectangle with rounded corners in a plane parallel to XY; coordinates are dims"""
        self.roundedRectangles.append((_dim(x0), _dim(y0), _dim(x1), _dim(y1), _dim(z), _dim(radius)))

    # -- drawing -----------------------------------------------------------------------------------------------------

    def _inMm(self) -> bool:
        return getattr(self, 'isDocumentInMm', True)

    def _sketchPoint3D(self, world):
        return self.sketch.modelToSketchSpace(adsk.core.Point3D.create(*[_value(v) for v in world]))

    def _coordinate(self, index, axis):
        """The world dim behind a point's sketch x (axis 0) or y (axis 1)"""
        worldAxis = (self.xAxis if axis == 0 else self.yAxis)[0]
        return _dim(self.worldPoints[index][worldAxis])

    def close(self) -> adsk.fusion.Sketch:
        if self.closed:
            return self.sketch
        self.closed = True
        with deferSketchCompute(self.sketch):
            for rectangle in self.roundedRectangles:
                self._roundedRectangle(*rectangle)
            if self.curves:
                self._chain()
        return self.sketch

    def _roundedRectangle(self, x0, y0, x1, y1, z, radius):
        """As baseGenerator's rounded cut: rectangle, four fillets, equal radii, one radius dimension"""
        corner = self._sketchPoint3D((x0, y0, z))
        corner.z = 0
        if self.xAxis != (0, 1) or self.yAxis != (1, 1):
            raise ValueError(f'{self.sketch.name}: rounded rectangles only on planes parallel to XY')
        sides = list(createRectangle(x1 - x0, y1 - y0, corner, self.sketch,
                                     x0 if abs(x0.value) > _EPS else None, y0 if abs(y0.value) > _EPS else None))
        arcs = self.sketch.sketchCurves.sketchArcs
        fillets = []
        for first, second in zip(sides, sides[1:] + sides[:1]):
            fillets.append(arcs.addFillet(first, first.endSketchPoint.geometry, second, second.startSketchPoint.geometry, radius.value))
        for fillet in fillets[1:]:
            self.sketch.geometricConstraints.addEqual(fillets[0], fillet)
        _drive(self.sketch.sketchDimensions.addRadialDimension(fillets[0], fillets[0].startSketchPoint.geometry, True).parameter, radius, self._inMm())

    def _chain(self):
        geometry = [self._sketchPoint3D(world) for world in self.worldPoints]
        plan = sketchChain.chain([(g.x, g.y) for g in geometry],
                                 [{k: v for k, v in curve.items() if k in ('kind', 'a', 'b', 'center', 'start', 'end')}
                                  for curve in self.curves],
                                 fixable=fixablePoints(self.worldPoints, self.xAxis, self.yAxis))
        sketchPoints = {}
        used = set()
        for curve in self.curves:
            for key in ('a', 'b', 'start', 'end'):
                if key in curve:
                    used.add(curve[key])
            if curve['kind'] == 'circle':
                used.add(curve['center'])
        for index in sorted(used):
            sketchPoints[index] = self.sketch.sketchPoints.add(geometry[index])
        drawn = []
        for curve in self.curves:
            if curve['kind'] == 'line':
                item = self.sketch.sketchCurves.sketchLines.addByTwoPoints(sketchPoints[curve['a']], sketchPoints[curve['b']])
                item.isConstruction = curve['construction']
            elif curve['kind'] == 'arc':
                c = geometry[curve['center']]
                first, second, sweep = arcDrawing(*[(geometry[curve[k]].x, geometry[curve[k]].y) for k in ('center', 'start', 'end')])
                item = self.sketch.sketchCurves.sketchArcs.addByCenterStartSweep(c, sketchPoints[curve[first]], sweep)
                self.sketch.geometricConstraints.addCoincident(item.endSketchPoint, sketchPoints[curve[second]])
                if curve['center'] in sketchPoints:
                    self.sketch.geometricConstraints.addCoincident(item.centerSketchPoint, sketchPoints[curve['center']])
                else:
                    sketchPoints[curve['center']] = item.centerSketchPoint
            else:
                item = self.sketch.sketchCurves.sketchCircles.addByCenterRadius(
                    sketchPoints[curve['center']], curve['diameter'].value / 2)
            drawn.append(item)
        self._apply(plan, drawn, sketchPoints, geometry)

    def _apply(self, plan, drawn, sketchPoints, geometry):
        constraints = self.sketch.geometricConstraints
        dimensions = self.sketch.sketchDimensions
        H = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
        V = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
        for number, item in enumerate(plan):
            kind = item[0]
            if kind == 'horizontal':
                constraints.addHorizontal(drawn[item[1]])
            elif kind == 'vertical':
                constraints.addVertical(drawn[item[1]])
            elif kind == 'originAt':
                constraints.addCoincident(self.sketch.originPoint, sketchPoints[item[1]])
            elif kind == 'fixed':
                # a plain-number point, fixed where it is: no dimension, no model parameter (round 39, p480)
                sketchPoints[item[1]].isFixed = True
            elif kind == 'diameter':
                circle = drawn[item[1]]
                c = circle.centerSketchPoint.geometry
                dimension = dimensions.addDiameterDimension(circle, adsk.core.Point3D.create(c.x + 0.4, c.y + 0.1, 0), True)
                _drive(dimension.parameter, self.curves[item[1]]['diameter'], self._inMm())
            else:
                i, j = item[1], item[2]
                axis = 0 if kind == 'hdim' else 1
                second = self.sketch.originPoint if j is None else sketchPoints[j]
                a = geometry[i]
                b = adsk.core.Point3D.create(0, 0, 0) if j is None else geometry[j]
                shift = 0.05 * (number % 7)
                text = adsk.core.Point3D.create((a.x + b.x) / 2 + 0.25 + shift, (a.y + b.y) / 2 + 0.25 + shift, 0)
                dimension = dimensions.addDistanceDimension(second, sketchPoints[i], H if axis == 0 else V, text, True)
                value = self._coordinate(i, axis) if j is None else self._coordinate(i, axis) - self._coordinate(j, axis)
                _drive(dimension.parameter, value.abs(), self._inMm())

    # -- reading -----------------------------------------------------------------------------------------------------

    def profiles(self, boxes, tolerance=1e-4):
        """The sketch profiles whose world bounding boxes are the given ((min x, y, z), (max x, y, z)), in that order"""
        self.close()
        candidates = []
        for profile in self.sketch.profiles:
            box = profile.boundingBox
            a = self.sketch.sketchToModelSpace(box.minPoint)
            b = self.sketch.sketchToModelSpace(box.maxPoint)
            low = [min(a.x, b.x), min(a.y, b.y), min(a.z, b.z)]
            high = [max(a.x, b.x), max(a.y, b.y), max(a.z, b.z)]
            candidates.append((profile, low, high))
        found = []
        for low, high in boxes:
            low = [_value(v) for v in low]
            high = [_value(v) for v in high]
            match = [p for p, l, h in candidates
                     if all(abs(l[i] - low[i]) < tolerance and abs(h[i] - high[i]) < tolerance for i in range(3))]
            if len(match) != 1:
                raise ValueError(f'{self.sketch.name}: {len(match)} profiles in box {low}..{high}')
            found.append(match[0])
        return found

    def profilesWhere(self, inside):
        """The profiles whose centroid lies where inside(x, y) holds, x and y the world coordinates along the sketch's
        axes (cm); for shapes cut out of circles, which split into pieces"""
        self.close()
        found = []
        for profile in self.sketch.profiles:
            centroid = self.sketch.sketchToModelSpace(profile.areaProperties().centroid)
            world = (centroid.x, centroid.y, centroid.z)
            if inside(world[self.xAxis[0]], world[self.yAxis[0]]):
                found.append(profile)
        if not found:
            raise ValueError(f'{self.sketch.name}: no profile in the region')
        return found

    def profilesByArea(self, areas, tolerance=1e-3):
        """The profiles with the given areas (mm2), in that order; for regions whose area does not change with the box"""
        self.close()
        found = []
        for area in areas:
            match = [profile for profile in self.sketch.profiles if abs(profile.areaProperties().area * 100 - area) < tolerance]
            if len(match) != 1:
                raise ValueError(f'{self.sketch.name}: {len(match)} profiles with area {area} mm2')
            found.append(match[0])
        return found


def isInMm(design, units=None) -> bool:
    """Whether the design's lengths are shown in mm, see _drive; none, as on the test stand-ins, counts as mm"""
    if design is None:
        return True
    units = units or adsk.fusion.DistanceUnits
    try:
        return design.fusionUnitsManager.distanceDisplayUnits == units.MillimeterDistanceUnits
    except AttributeError:
        return True


def _drive(parameter, value, isDocumentInMm: bool = True):
    """
    A dimension follows its dim's expression only when the dim depends on a parameter (round 45, p480). Two points that
    hang on the same measure keep their distance whatever the parameter: the dimension stays at the value it was drawn
    with, which is that distance, and costs no Parameter.expression call (129 of 215 per box, 195 ms each in a second box,
    fusion-auftraege/r45_probe.log, r45_profil.log). The sketch stays fully constrained, the dimension is still there.
    Tested in tests/test_pred_sketch_constant.py
    """
    if isinstance(value, Dim) and not value.dependsOnParameters:
        # Round 59: a document not in mm keeps a dimension left as drawn as a rounded text in its units, '0.0787401575
        # in' for 2 mm, and evaluates it again when a parameter change recomputes the sketch: 1e-10 cm off, the two
        # 2 mm roundings of a 4 mm catch slide no longer met in one face, nor the mirrored halves of the handle
        # (fusion-auftraege/r59_paramfaces.log; with every dimension in mm the faces were those of mm,
        # r59_paramfaces2.log, the build in inches 19 s longer). Documents in mm keep it as drawn, without the cost.
        # Tested in tests/test_pred_sketch_constant.py
        if not isDocumentInMm:
            # its value in mm, a constant: the formula would tie it to parameters it doesn't depend on
            parameter.expression = lengthExpression(value.value)
        return
    applyTo(parameter, value)


def arcDrawing(center, start, end):
    """
    How to draw the shorter arc from start to end around center (sketch x, y): from which end ('start' or 'end'), to
    which, and the sweep, always counterclockwise. A negative sweep gave an arc with start and end swapped against the
    points passed: its end tied to the curve's end then over-constrained the mirrored label rail
    (fusion-auftraege/r27_diag3.log, VCS_SKETCH_OVER_CONSTRAINTS). binBodyGenerator draws its corners the same way.
    Tested in tests/test_pred_sketch_arcs.py
    """
    a0 = math.atan2(start[1] - center[1], start[0] - center[0])
    a1 = math.atan2(end[1] - center[1], end[0] - center[0])
    sweep = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    return ('start', 'end', sweep) if sweep > 0 else ('end', 'start', -sweep)


def collection(items) -> adsk.core.ObjectCollection:
    result = adsk.core.ObjectCollection.create()
    for item in items:
        result.add(item)
    return result
