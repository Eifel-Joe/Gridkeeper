"""
The storage box after Pred's parametric Gridfinity Storage Box v1.1
(https://www.printables.com/model/543553, CC BY-NC, by Pred), rebuilt in code for Gridkeeper (round 27, p260).

The generator follows Pred's timeline of the component "Box" step by step (the step names "#N Name" are Pred's, see
fusion-auftraege/r27_pred_walk.log). Its own sketches are drawn from world coordinates with every point dimensioned
(predSketch), so they are fully constrained and follow the gfBox parameters; Pred's sketches on body faces become
sketches on offset planes. Coordinates are Pred's frame: outer corner at x = y = 0, z = 0 on top of the 2.8 mm bottom.
"""

import math
from dataclasses import dataclass

import adsk.core, adsk.fusion

from .dim import Dim, valueInput
from .predBox import PredBoxDims
from .predSketch import WorldSketch, collection

ROOT2 = math.sqrt(2)
# Pred's sweep profile: centre of the 0.5 mm arc in the lid's socket lip, mm under the top (2.057107 mm)
ARC_CENTER_BELOW_TOP = 52.2 - (50.85 - 0.5 * ROOT2)


def mm(value: float) -> Dim:
    return Dim.length(round(value / 10, 9))


@dataclass
class PredBoxOptions:
    hasMagnets: bool = False
    magnetDepth: float = 0.24
    magnetDiameter: float = 0.65


@dataclass
class PredBoxBodies:
    base: adsk.fusion.BRepBody
    lid: adsk.fusion.BRepBody


class _Builder:
    def __init__(self, component: adsk.fusion.Component, dims: PredBoxDims, options: PredBoxOptions, onStep):
        self.component = component
        self.features = component.features
        self.dims = dims
        self.options = options
        self.onStep = onStep or (lambda name: None)
        self.base = None
        self.lid = None

    # -- helpers -------------------------------------------------------------------------------------------------

    def top(self, below: float) -> Dim:
        """z that hangs on the top of the box body: below mm under it (Pred's lid features)"""
        return self.dims.bodyTop - mm(below) if below else self.dims.bodyTop

    def step(self, name: str):
        self.onStep(name)

    def offsetPlane(self, base: adsk.fusion.ConstructionPlane, axis: int, target: Dim, name: str):
        """Plane parallel to a base plane at the world coordinate target on the given axis (0 x, 1 y, 2 z)"""
        planes = self.component.constructionPlanes
        planeInput = planes.createInput()
        planeInput.setByOffset(base, valueInput(target))
        plane = planes.add(planeInput)
        origin = plane.geometry.origin
        if abs((origin.x, origin.y, origin.z)[axis] - target.value) > 1e-6:
            # the base plane's normal points the other way
            plane.deleteMe()
            planeInput = planes.createInput()
            planeInput.setByOffset(base, valueInput(target * -1))
            plane = planes.add(planeInput)
        plane.name = name
        return plane

    def extrude(self, profiles, operation, distance: Dim, start: Dim = None, bodies=None, name=None):
        extrudes = self.features.extrudeFeatures
        extrudeInput = extrudes.createInput(collection(profiles), operation)
        extrudeInput.setDistanceExtent(False, valueInput(distance))
        if start is not None:
            extrudeInput.startExtent = adsk.fusion.OffsetStartDefinition.create(valueInput(start))
        if bodies is not None:
            extrudeInput.participantBodies = bodies
        feature = extrudes.add(extrudeInput)
        if name:
            feature.name = name
        return feature

    def sweep(self, sketch: adsk.fusion.Sketch, path: adsk.fusion.Path, operation, name):
        sweeps = self.features.sweepFeatures
        sweepInput = sweeps.createInput(collection(list(sketch.profiles)), path, operation)
        sweepInput.orientation = adsk.fusion.SweepOrientationTypes.PerpendicularOrientationType
        sweepInput.participantBodies = [self.base]
        feature = sweeps.add(sweepInput)
        feature.name = name
        return feature

    # -- Pred #1 to #17: body, planes, floor grid ------------------------------------------------------------------

    def body(self):
        d = self.dims
        z0 = mm(0)
        sketch = WorldSketch(self.component, self.component.xYConstructionPlane, 'Footprint')
        sketch.roundedRectangle(mm(0), mm(0), d.outerWidth, d.outerLength, z0, mm(14))
        sketch.roundedRectangle(mm(10), mm(10), d.outerWidth - mm(10), d.outerLength - mm(10), z0, mm(4))
        sketch.close()
        self.footprint = sketch
        outline = sketch.profiles([((0, 0, 0), (d.outerWidth, d.outerLength, 0)),
                                   ((1, 1, 0), (d.outerWidth - mm(10), d.outerLength - mm(10), 0))])
        self.step('#1 BaseWithGridfinityBinFootprint')
        first = self.extrude(outline, adsk.fusion.FeatureOperations.NewBodyFeatureOperation, mm(-2.8), name='Bottom')
        self.base = first.bodies.item(0)
        self.base.name = 'Base'
        self.step('#2 Extrude1')
        self.extrude(outline, adsk.fusion.FeatureOperations.JoinFeatureOperation, d.bodyTop, bodies=[self.base], name='Walls')
        self.step('#3 Extrude4')
        self.extrude(outline[1:], adsk.fusion.FeatureOperations.CutFeatureOperation, d.innerCutDepth, start=d.innerCutStart,
                     bodies=[self.base], name='Inside')
        self.step('#4 Extrude3')
        c = self.component
        self.lidPlane = self.offsetPlane(c.xYConstructionPlane, 2, d.lidCut, 'LidCutPlane')
        self.step('#5 LidCutPlane')
        self.sweepPlane = self.offsetPlane(c.xZConstructionPlane, 1, mm(31), 'GridfinitySweepSketchPlane')
        self.step('#6 GridfinitySweepSketchPlane')
        self.midXPlane = self.offsetPlane(c.yZConstructionPlane, 0, d.midX, 'BoxMidplane_Y')
        self.step('#7 BoxMidplane_Y')
        self.midYPlane = self.offsetPlane(c.xZConstructionPlane, 1, d.midY, 'BoxMidplane_X')
        self.step('#8 BoxMidplane_X')

    def floorGrid(self):
        d = self.dims
        y = mm(31)

        def xz(points):
            return [(mm(x), y, z if isinstance(z, Dim) else mm(z)) for x, z in points]

        # Pred's GridfinityBinSweepProfile split into the regions each sweep takes, upper part hangs on the top
        # the 45 degree line from (49.85, 49.45) is tangent to the 0.5 mm arc whose centre is 0.5 mm left of x 51.75
        arcCenterBelowTop = ARC_CENTER_BELOW_TOP
        tangent = (51.25 - 0.5 / ROOT2, 52.2 - arcCenterBelowTop + 0.5 / ROOT2)
        lower = xz([(31, 0), (49.15, 0), (49.85, 0.7), (49.85, 2.5), (51.5, 4.15), (31, 4.15)])
        upperCut = [(31, self.top(8.8)), (48.3, self.top(8.8)), (48.8, self.top(8.3)), (48.8, self.top(5.6)),
                    (49.15, self.top(5.25)), (49.85, self.top(4.55)), (49.85, self.top(2.75)),
                    (tangent[0], self.top(52.2 - tangent[1]))]
        afterArc = [(51.25, self.top(arcCenterBelowTop - 0.5)), (52, self.top(arcCenterBelowTop - 0.5)),
                    (52, self.top(0)), (31, self.top(0))]

        cut1 = WorldSketch(self.component, self.sweepPlane, 'SweepCut1')
        cut1.polyline(lower)
        points = xz(upperCut)
        cut1.polyline(points, closed=False)
        rest = xz(afterArc)
        cut1.arc((mm(51.25), y, self.top(arcCenterBelowTop)), points[-1], rest[0])
        cut1.polyline(rest, closed=False)
        cut1.line(rest[-1], points[0])
        cut1.close()
        self.step('#9 GridfinityBinSweepProfile')

        path = WorldSketch(self.component, self.component.xYConstructionPlane, 'CellPath')
        path.roundedRectangle(mm(10), mm(10), mm(52), mm(52), mm(0), mm(4))
        pathSketch = path.close()
        cellPath = self.features.createPath(pathSketch.sketchCurves.item(0), True)

        sweep1 = self.sweep(cut1.sketch, cellPath, adsk.fusion.FeatureOperations.CutFeatureOperation, 'Sweep1')
        self.step('#10 Sweep1')
        join = WorldSketch(self.component, self.sweepPlane, 'SweepJoin')
        join.polyline(xz([(31, self.top(10)), (48.8, self.top(10)), (49.6, self.top(9.2)), (49.6, self.top(7.4)),
                          (51.75, self.top(5.25)), (31, self.top(5.25))]))
        join.close()
        sweep2 = self.sweep(join.sketch, cellPath, adsk.fusion.FeatureOperations.JoinFeatureOperation, 'Sweep2')
        self.step('#11 Sweep2')
        cut2 = WorldSketch(self.component, self.sweepPlane, 'SweepCut2')
        cut2.polyline(xz([(31, self.top(8.8)), (48.3, self.top(8.8)), (48.8, self.top(8.3)), (48.8, self.top(5.6)),
                          (49.15, self.top(5.25)), (31, self.top(5.25))]))
        cut2.close()
        sweep4 = self.sweep(cut2.sketch, cellPath, adsk.fusion.FeatureOperations.CutFeatureOperation, 'Sweep4')
        self.step('#12 Sweep4')

        floor, magnets = self.floorPads()
        self.step('#13 Sketch21')
        floorCut = self.extrude([floor], adsk.fusion.FeatureOperations.CutFeatureOperation, mm(-1.6), bodies=[self.base],
                                name='Floor')
        self.step('#14 Extrude56')
        patterned = [sweep1, sweep2, sweep4, floorCut]
        if self.options.hasMagnets:
            magnetCut = self.extrude(magnets, adsk.fusion.FeatureOperations.CutFeatureOperation,
                                     Dim.length(-self.options.magnetDepth), bodies=[self.base], name='Magnets')
            patterned.append(magnetCut)
        self.step('#15 Extrude57')
        patterns = self.features.rectangularPatternFeatures
        patternInput = patterns.createInput(collection(patterned), self.component.xConstructionAxis,
                                            valueInput(d.gridX), valueInput(mm(42)),
                                            adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
        patternInput.setDirectionTwo(self.component.yConstructionAxis, valueInput(d.gridY), valueInput(mm(42)))
        pattern = patterns.add(patternInput)
        pattern.name = 'Cells'
        self.step('#16 R-Pattern1')
        # Pred's Extrude5: from the top down to the plane of the socket lip (0.5 mm over the arc centre)
        innerProfile = self.footprint.profiles([((1, 1, 0), (d.outerWidth - mm(10), d.outerLength - mm(10), 0))])
        self.extrude(innerProfile, adsk.fusion.FeatureOperations.CutFeatureOperation, mm(-(ARC_CENTER_BELOW_TOP - 0.5)),
                     start=d.bodyTop, bodies=[self.base], name='Cell ridges')
        self.step('#17 Extrude5')

    def floorPads(self):
        """Pred's Sketch21 for the first cell: floor inside 12.85..49.15 mm with 1.15 mm corners, a pad around
        each magnet (radius magnet / 2 + 0.75 mm) blended into the floor edges with 5.05 mm arcs"""
        R = self.options.magnetDiameter * 10 / 2 + 0.75
        b = 5.05
        e0, e1 = 12.85, 49.15
        z = mm(0)

        def p(x, y):
            return (mm(x), mm(y), z)

        sketch = WorldSketch(self.component, self.component.xYConstructionPlane, 'FloorPads')
        pads = [(e0 + b, e0 + b, 1, 1), (e1 - b, e0 + b, -1, 1), (e1 - b, e1 - b, -1, -1), (e0 + b, e1 - b, 1, -1)]
        for px, py, sx, sy in pads:
            tangentA, tangentB = p(px + sx * R, py), p(px, py + sy * R)
            sketch.arc(p(px, py), tangentA, tangentB)
            sketch.arc(p(px + sx * (R + b), py), tangentA, p(px + sx * (R + b), py - sy * b))
            sketch.arc(p(px, py + sy * (R + b)), tangentB, p(px - sx * b, py + sy * (R + b)))
            sketch.circle(p(px, py), Dim.length(self.options.magnetDiameter))
        # outline, split where the blends meet it
        r = 1.15
        a = e0 + b + R + b   # 26.95 at 6.5 mm magnets
        bb = e1 - b - R - b  # 35.05
        corners = [((e0 + r, e0 + r), (e0, e0 + r), (e0 + r, e0)), ((e1 - r, e0 + r), (e1 - r, e0), (e1, e0 + r)),
                   ((e1 - r, e1 - r), (e1, e1 - r), (e1 - r, e1)), ((e0 + r, e1 - r), (e0 + r, e1), (e0, e1 - r))]
        edges = [[(e0 + r, e0), (a, e0), (bb, e0), (e1 - r, e0)], [(e1, e0 + r), (e1, a), (e1, bb), (e1, e1 - r)],
                 [(e1 - r, e1), (bb, e1), (a, e1), (e0 + r, e1)], [(e0, e1 - r), (e0, bb), (e0, a), (e0, e0 + r)]]
        for center, start, end in corners:
            sketch.arc(p(*center), p(*start), p(*end))
        for edge in edges:
            for first, second in zip(edge, edge[1:]):
                sketch.line(p(*first), p(*second))
        sketch.close()
        floor = sketch.profiles([((mm(e0), mm(e0), 0), (mm(e1), mm(e1), 0))])[0]
        half = self.options.magnetDiameter / 2
        magnets = sketch.profiles([((mm(px) - Dim.length(half), mm(py) - Dim.length(half), 0),
                                    (mm(px) + Dim.length(half), mm(py) + Dim.length(half), 0)) for px, py, _, _ in pads])
        return floor, magnets


def createPredBox(component: adsk.fusion.Component, dims: PredBoxDims, options: PredBoxOptions, onStep=None) -> PredBoxBodies:
    builder = _Builder(component, dims, options, onStep)
    builder.body()
    builder.floorGrid()
    return PredBoxBodies(builder.base, builder.lid)
