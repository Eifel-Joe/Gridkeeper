"""
Fully constrained sketches drawn from world coordinates, for the box after Pred (round 27).

Every point is given as three dims in the box's frame (cm). The sketch places it and pins it with a horizontal and a
vertical distance dimension from the sketch origin, driven by the dim's expression, or with an alignment to the origin
where the distance is zero. Lines and arcs share these points, arcs get one more alignment of their center, so every
sketch made here is fully constrained and follows the box parameters. Sketch planes must be the component's base planes
or offsets of them, so the sketch origin lies on the world axes of the plane.
"""

import math
import adsk.core, adsk.fusion

from .dim import Dim, applyTo
from .sketchUtils import deferSketchCompute

_EPS = 1e-7


def _axis(vector):
    values = (vector.x, vector.y, vector.z)
    index = max(range(3), key=lambda i: abs(values[i]))
    return index, (1 if values[index] > 0 else -1)


def _value(dim):
    return dim.value if isinstance(dim, Dim) else dim


class WorldSketch:
    def __init__(self, component: adsk.fusion.Component, plane, name: str):
        self.component = component
        self.sketch: adsk.fusion.Sketch = component.sketches.add(plane)
        self.sketch.name = name
        transform = self.sketch.transform
        origin, xAxis, yAxis, _ = transform.getAsCoordinateSystem()
        self.xAxis = _axis(xAxis)
        self.yAxis = _axis(yAxis)
        originValues = (origin.x, origin.y, origin.z)
        if abs(originValues[self.xAxis[0]]) > _EPS or abs(originValues[self.yAxis[0]]) > _EPS:
            raise ValueError(f'sketch {name}: the plane must pass through the world axes')
        self.points = {}
        # Fusion takes only one distance dimension between the same two points (a second one, horizontal after
        # vertical, is "over constrained", fusion-auftraege/r27_probe.out): vertical distances go from the
        # projected component origin, which lies on the sketch origin
        self.verticalOrigin = self.sketch.project(component.originConstructionPoint).item(0)
        self.constraints = self.sketch.geometricConstraints
        self.dimensions = self.sketch.sketchDimensions
        self._defer = deferSketchCompute(self.sketch)
        self._defer.__enter__()

    def close(self):
        self._defer.__exit__(None, None, None)
        return self.sketch

    def _sketchPoint3D(self, world):
        return self.sketch.modelToSketchSpace(adsk.core.Point3D.create(*[_value(v) for v in world]))

    def _align(self, point, horizontal: bool):
        """Puts the point on the sketch's x axis (horizontal) or y axis with the origin"""
        origin = self.sketch.originPoint
        if horizontal:
            self.constraints.addHorizontalPoints(origin, point)
        else:
            self.constraints.addVerticalPoints(origin, point)

    def point(self, world) -> adsk.fusion.SketchPoint:
        key = tuple(round(_value(v) * 1e5) for v in world)
        if key in self.points:
            return self.points[key]
        geometry = self._sketchPoint3D(world)
        point = self.sketch.sketchPoints.add(geometry)
        for (axis, _), sketchValue, orientation in (
                (self.xAxis, geometry.x, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation),
                (self.yAxis, geometry.y, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation)):
            if abs(sketchValue) < _EPS:
                # zero distance: same x as the origin is a vertical alignment, same y a horizontal one
                self._align(point, horizontal=orientation != adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation)
                continue
            textPoint = adsk.core.Point3D.create(geometry.x + 0.2, geometry.y + 0.2, 0)
            fromPoint = self.sketch.originPoint if orientation == adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation else self.verticalOrigin
            dimension = self.dimensions.addDistanceDimension(fromPoint, point, orientation, textPoint, True)
            coordinate = world[axis]
            if isinstance(coordinate, Dim):
                applyTo(dimension.parameter, coordinate.abs())
        self.points[key] = point
        return point

    def line(self, start, end, construction=False) -> adsk.fusion.SketchLine:
        line = self.sketch.sketchCurves.sketchLines.addByTwoPoints(self.point(start), self.point(end))
        line.isConstruction = construction
        return line

    def polyline(self, points, closed=True):
        lines = [self.line(a, b) for a, b in zip(points, points[1:])]
        if closed:
            lines.append(self.line(points[-1], points[0]))
        return lines

    def arc(self, center, start, end) -> adsk.fusion.SketchArc:
        """The shorter arc from start to end around center (Pred's arcs are at most 180 degrees)"""
        c, s, e = self._sketchPoint3D(center), self._sketchPoint3D(start), self._sketchPoint3D(end)
        a0 = math.atan2(s.y - c.y, s.x - c.x)
        a1 = math.atan2(e.y - c.y, e.x - c.x)
        sweep = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        startPoint, endPoint = self.point(start), self.point(end)
        arc = self.sketch.sketchCurves.sketchArcs.addByCenterStartSweep(c, startPoint, sweep)
        self.constraints.addCoincident(arc.endSketchPoint, endPoint)
        center = arc.centerSketchPoint
        # both ends are pinned, the center only needs to know which side: line it up with an end
        for other, otherGeometry in ((endPoint, e), (startPoint, s)):
            if abs(c.x - otherGeometry.x) < _EPS:
                self.constraints.addVerticalPoints(center, other)
                break
            if abs(c.y - otherGeometry.y) < _EPS:
                self.constraints.addHorizontalPoints(center, other)
                break
        else:
            self.dimensions.addRadialDimension(arc, adsk.core.Point3D.create(c.x + 0.3, c.y + 0.3, 0), True)
        return arc

    def circle(self, center, diameter: Dim) -> adsk.fusion.SketchCircle:
        circle = self.sketch.sketchCurves.sketchCircles.addByCenterRadius(self.point(center), _value(diameter) / 2)
        geometry = circle.centerSketchPoint.geometry
        dimension = self.dimensions.addDiameterDimension(circle, adsk.core.Point3D.create(geometry.x + 0.3, geometry.y, 0), True)
        if isinstance(diameter, Dim):
            applyTo(dimension.parameter, diameter)
        return circle

    def roundedRectangle(self, x0, y0, x1, y1, z, radius: Dim, plane='xy'):
        """Axis-parallel rectangle with rounded corners in the plane of two world axes; coordinates are dims"""
        r = radius

        def at(u, v):
            return (u, v, z) if plane == 'xy' else None

        corners = [
            ((x0 + r, y0 + r), (x0, y0 + r), (x0 + r, y0)),
            ((x1 - r, y0 + r), (x1 - r, y0), (x1, y0 + r)),
            ((x1 - r, y1 - r), (x1, y1 - r), (x1 - r, y1)),
            ((x0 + r, y1 - r), (x0 + r, y1), (x0, y1 - r)),
        ]
        for index, (center, start, end) in enumerate(corners):
            self.arc(at(*center), at(*start), at(*end))
            nextStart = corners[(index + 1) % 4][1]
            self.line(at(*end), at(*nextStart))

    def profiles(self, boxes, tolerance=1e-4):
        """The sketch profiles whose world bounding boxes are the given ((min x, y, z), (max x, y, z)), in that order"""
        found = []
        candidates = []
        for profile in self.sketch.profiles:
            box = profile.boundingBox
            a = self.sketch.sketchToModelSpace(box.minPoint)
            b = self.sketch.sketchToModelSpace(box.maxPoint)
            low = [min(a.x, b.x), min(a.y, b.y), min(a.z, b.z)]
            high = [max(a.x, b.x), max(a.y, b.y), max(a.z, b.z)]
            candidates.append((profile, low, high))
        for low, high in boxes:
            low = [_value(v) for v in low]
            high = [_value(v) for v in high]
            match = [p for p, l, h in candidates
                     if all(abs(l[i] - low[i]) < tolerance and abs(h[i] - high[i]) < tolerance for i in range(3))]
            if len(match) != 1:
                raise ValueError(f'{self.sketch.name}: {len(match)} profiles in box {low}..{high}, '
                                 f'have {[(round(l[0]*10,3), round(l[1]*10,3), round(l[2]*10,3), round(h[0]*10,3), round(h[1]*10,3), round(h[2]*10,3)) for _, l, h in candidates]}')
            found.append(match[0])
        return found


def collection(items) -> adsk.core.ObjectCollection:
    result = adsk.core.ObjectCollection.create()
    for item in items:
        result.add(item)
    return result
