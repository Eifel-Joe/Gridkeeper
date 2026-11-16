"""
Fully constrained sketches drawn from world coordinates, for the box after Pred (round 27).

Shapes are given with points as three dims in the box's frame (cm). The sketch collects them and, on close(), draws
them and binds them the way the existing generators do (Nutzer: "Ja, Formen-Weg"): lines horizontal or vertical, arcs
tangent, radii and diameters, one anchor per shape and lengths between its points. sketchPlan picks exactly as many of
those as the sketch has degrees of freedom. Dimensions get the expression abs(a - b) of the world dims, so the sketch
follows the box parameters. Sketch planes must be the component's base planes or offsets of them, so the sketch origin
lies on the world axes of the plane.
"""

import math
import adsk.core, adsk.fusion

from .dim import Dim, applyTo
from .sketchUtils import deferSketchCompute
from . import sketchPlan

_EPS = 1e-7


def _axis(vector):
    values = (vector.x, vector.y, vector.z)
    index = max(range(3), key=lambda i: abs(values[i]))
    return index, (1 if values[index] > 0 else -1)


def _value(dim):
    return dim.value if isinstance(dim, Dim) else dim


def _dim(value):
    return value if isinstance(value, Dim) else Dim.length(value)


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
        self.closed = False

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
        r = radius
        corners = [
            ((x0 + r, y0 + r), (x0, y0 + r), (x0 + r, y0)),
            ((x1 - r, y0 + r), (x1 - r, y0), (x1, y0 + r)),
            ((x1 - r, y1 - r), (x1, y1 - r), (x1 - r, y1)),
            ((x0 + r, y1 - r), (x0 + r, y1), (x0, y1 - r)),
        ]
        for index, (center, start, end) in enumerate(corners):
            self.arc((*center, z), (*start, z), (*end, z))
            nextStart = corners[(index + 1) % 4][1]
            self.line((*end, z), (*nextStart, z))

    # -- drawing -----------------------------------------------------------------------------------------------------

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
        geometry = [self._sketchPoint3D(world) for world in self.worldPoints]
        points2d = [(g.x, g.y) for g in geometry]
        planCurves = [{k: v for k, v in curve.items() if k in ('kind', 'a', 'b', 'center', 'start', 'end')}
                      for curve in self.curves]
        plan = sketchPlan.planConstraints(points2d, planCurves)
        H = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
        V = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
        with deferSketchCompute(self.sketch):
            sketchPoints = {}
            arcCenters = {curve['center'] for curve in self.curves if curve['kind'] == 'arc'}
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
                    c, s, e = geometry[curve['center']], geometry[curve['start']], geometry[curve['end']]
                    a0 = math.atan2(s.y - c.y, s.x - c.x)
                    a1 = math.atan2(e.y - c.y, e.x - c.x)
                    sweep = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
                    item = self.sketch.sketchCurves.sketchArcs.addByCenterStartSweep(c, sketchPoints[curve['start']], sweep)
                    self.sketch.geometricConstraints.addCoincident(item.endSketchPoint, sketchPoints[curve['end']])
                    if curve['center'] in sketchPoints:
                        self.sketch.geometricConstraints.addCoincident(item.centerSketchPoint, sketchPoints[curve['center']])
                    else:
                        sketchPoints[curve['center']] = item.centerSketchPoint
                else:
                    item = self.sketch.sketchCurves.sketchCircles.addByCenterRadius(
                        sketchPoints[curve['center']], curve['diameter'].value / 2)
                drawn.append(item)
            del arcCenters
            self._apply(plan, drawn, sketchPoints, geometry, H, V)
        return self.sketch

    def _apply(self, plan, drawn, sketchPoints, geometry, H, V):
        constraints = self.sketch.geometricConstraints
        dimensions = self.sketch.sketchDimensions
        for number, item in enumerate(plan):
            kind = item[0]
            if kind == 'horizontal':
                constraints.addHorizontal(drawn[item[1]])
            elif kind == 'vertical':
                constraints.addVertical(drawn[item[1]])
            elif kind == 'originOnLine':
                constraints.addCoincident(self.sketch.originPoint, drawn[item[1]])
            elif kind == 'tangent':
                constraints.addTangent(drawn[item[1]], drawn[item[2]])
            elif kind == 'radius':
                arc = drawn[item[1]]
                c = arc.centerSketchPoint.geometry
                dimensions.addRadialDimension(arc, adsk.core.Point3D.create(c.x + 0.3, c.y + 0.3, 0), True)
            elif kind == 'diameter':
                circle = drawn[item[1]]
                c = circle.centerSketchPoint.geometry
                dimension = dimensions.addDiameterDimension(circle, adsk.core.Point3D.create(c.x + 0.4, c.y + 0.1, 0), True)
                applyTo(dimension.parameter, self.curves[item[1]]['diameter'])
            else:
                i, j = item[1], item[2]
                axis = 0 if kind == 'hdim' else 1
                first = sketchPoints[i]
                second = self.sketch.originPoint if j is None else sketchPoints[j]
                a, b = geometry[i], (adsk.core.Point3D.create(0, 0, 0) if j is None else geometry[j])
                # spread the texts so no two dimensions share a text point
                shift = 0.05 * (number % 7)
                text = adsk.core.Point3D.create((a.x + b.x) / 2 + 0.25 + shift, (a.y + b.y) / 2 + 0.25 + shift, 0)
                dimension = dimensions.addDistanceDimension(second, first, H if axis == 0 else V, text, True)
                value = self._coordinate(i, axis) if j is None else self._coordinate(i, axis) - self._coordinate(j, axis)
                applyTo(dimension.parameter, value.abs())

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


def collection(items) -> adsk.core.ObjectCollection:
    result = adsk.core.ObjectCollection.create()
    for item in items:
        result.add(item)
    return result
