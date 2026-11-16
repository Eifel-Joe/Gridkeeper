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
from . import predBoxEdges

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

    def sweep(self, sketch: adsk.fusion.Sketch, path: adsk.fusion.Path, operation, name, bodies):
        sweeps = self.features.sweepFeatures
        sweepInput = sweeps.createInput(collection(list(sketch.profiles)), path, operation)
        sweepInput.orientation = adsk.fusion.SweepOrientationTypes.PerpendicularOrientationType
        sweepInput.participantBodies = bodies
        feature = sweeps.add(sweepInput)
        feature.name = name
        return feature

    def along(self, profiles, operation, axis: int, distance: Dim, start: Dim = None, bodies=None, name=None):
        """Extrude along a world axis: distance signed in world direction, start a world coordinate on that axis
        (the sketch planes here are all parallel to base planes through the origin)"""
        sketch = profiles[0].parentSketch
        normal = sketch.xDirection.crossProduct(sketch.yDirection)
        sign = 1 if (normal.x, normal.y, normal.z)[axis] > 0 else -1
        planeAt = sketch.origin
        planeValue = (planeAt.x, planeAt.y, planeAt.z)[axis]
        startOffset = None
        if start is not None:
            startOffset = (start - Dim.length(planeValue)) * sign if abs(planeValue) > 1e-9 else start * sign
        bodies = bodies if bodies is not None else [self.base]
        return self.extrude(profiles, operation, distance * sign, start=startOffset, bodies=bodies, name=name)

    def _pick(self, step, values, faces=False, body=None):
        body = body or self.base
        expected = predBoxEdges.expectedItems(step, values)
        edgeItems = [item for item in expected if item['kind'] != 'face']
        faceItems = [item for item in expected if item['kind'] == 'face']
        picked = []
        if edgeItems:
            picked += predBoxEdges.matchItems(edgeItems, list(body.edges), _edgeItem)
        if faceItems:
            picked += predBoxEdges.matchItems(faceItems, list(body.faces), _faceItem)
        return picked

    def chamfer(self, step, name=None, body=None):
        [edgeSet] = predBoxEdges.PRED_EDGES[step]
        items = self._pick(step, self.dims.values(), body=body)
        chamfers = self.features.chamferFeatures

        def add(tangentChain):
            chamferInput = chamfers.createInput2()
            chamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
                collection(items), valueInput(Dim.length(edgeSet['distance'])), tangentChain)
            return chamfers.add(chamferInput)
        feature = _withTangentChainFallback(add)
        feature.name = name or step.split(' ')[1]
        self.step(step)
        return feature

    def fillet(self, step, name=None, body=None):
        [edgeSet] = predBoxEdges.PRED_EDGES[step]
        items = self._pick(step, self.dims.values(), body=body)
        fillets = self.features.filletFeatures

        def add(tangentChain):
            filletInput = fillets.createInput()
            filletInput.edgeSetInputs.addConstantRadiusEdgeSet(
                collection(items), valueInput(Dim.length(edgeSet['radius'])), tangentChain)
            return fillets.add(filletInput)
        feature = _withTangentChainFallback(add)
        feature.name = name or step.split(' ')[1]
        self.step(step)
        return feature

    def mirror(self, features, plane, step):
        mirrors = self.features.mirrorFeatures
        feature = mirrors.add(mirrors.createInput(collection(features), plane))
        feature.name = step.split(' ')[1]
        self.step(step)
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

        # the grid comes after the lid is split off (createPredBox): sockets in the floor, bin seats under the lid
        sweep1 = self.sweep(cut1.sketch, cellPath, adsk.fusion.FeatureOperations.CutFeatureOperation, 'Sweep1',
                            [self.base, self.lid])
        self.step('#10 Sweep1')
        join = WorldSketch(self.component, self.sweepPlane, 'SweepJoin')
        join.polyline(xz([(31, self.top(10)), (48.8, self.top(10)), (49.6, self.top(9.2)), (49.6, self.top(7.4)),
                          (51.75, self.top(5.25)), (31, self.top(5.25))]))
        join.close()
        sweep2 = self.sweep(join.sketch, cellPath, adsk.fusion.FeatureOperations.JoinFeatureOperation, 'Sweep2', [self.lid])
        self.step('#11 Sweep2')
        cut2 = WorldSketch(self.component, self.sweepPlane, 'SweepCut2')
        cut2.polyline(xz([(31, self.top(8.8)), (48.3, self.top(8.8)), (48.8, self.top(8.3)), (48.8, self.top(5.6)),
                          (49.15, self.top(5.25)), (31, self.top(5.25))]))
        cut2.close()
        sweep4 = self.sweep(cut2.sketch, cellPath, adsk.fusion.FeatureOperations.CutFeatureOperation, 'Sweep4', [self.lid])
        self.step('#12 Sweep4')

        floor, magnets, blends = self.floorPads()
        self.step('#13 Sketch21')
        floorCut = self.extrude([floor], adsk.fusion.FeatureOperations.CutFeatureOperation, mm(-1.6), bodies=[self.base],
                                name='Floor')
        # Nutzer: "Versuche b" - the 5.05 mm blends of the pads into the floor edges as a fillet, not as sketch arcs
        edges = [edge for edge in self.base.edges if _isVerticalAt(edge, blends, -0.16, 0.0)]
        if len(edges) != len(blends):
            raise ValueError(f'floor pads: {len(edges)} blend edges found, {len(blends)} expected')
        fillets = self.features.filletFeatures
        filletInput = fillets.createInput()
        filletInput.edgeSetInputs.addConstantRadiusEdgeSet(collection(edges), valueInput(mm(5.05)), False)
        blend = fillets.add(filletInput)
        blend.name = 'Floor pad blends'
        self.step('#14 Extrude56')
        patterned = [sweep1, sweep2, sweep4, floorCut, blend]
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
                     start=d.bodyTop, bodies=[self.lid], name='Cell ridges')
        self.step('#17 Extrude5')

    # -- Pred #18 to #43: wall recesses, opening tab, handle and label holders ----------------------------------

    def lab(self, x: float) -> Dim:
        """x that hangs on the label edge (Pred measured at 5 x 4 x 6, left half; 79.75 mm is the left label edge)"""
        return self.dims.midX - self.dims.labelWidth / 2 + mm(x - 79.75)

    def mid(self, z: float) -> Dim:
        """z that hangs on the middle height (24.7 mm at height 6)"""
        return self.dims.midZ + mm(z - 24.7)

    def walls(self):
        d = self.dims
        c = self.component
        cut = adsk.fusion.FeatureOperations.CutFeatureOperation
        join = adsk.fusion.FeatureOperations.JoinFeatureOperation
        W, L, top, bottom = d.outerWidth, d.outerLength, d.bodyTop, d.bottom
        y0, x0 = mm(0), mm(0)

        def xzRect(sketch, xa, xb, za, zb, y):
            sketch.rectangle((xa, y, za), (xb, y, za), (xb, y, zb), (xa, y, zb))

        front = WorldSketch(c, c.xZConstructionPlane, 'FrontFeatures')
        for xa, xb in ((mm(21), mm(41)), (mm(56), W - mm(56)), (W - mm(41), W - mm(21))):
            xzRect(front, xa, xb, bottom, top, y0)
        front.close()
        self.step('#18 FrontFeatures')
        self.along(list(front.sketch.profiles), cut, 1, mm(7.5), name='Front recesses')
        self.step('#19 Extrude7')

        self.frontPlane = self.offsetPlane(c.xZConstructionPlane, 1, mm(7.5), 'FrontRecessPlane')
        y = mm(7.5)
        left, right = d.midX - d.labelWidth / 2, d.midX + d.labelWidth / 2
        tab = WorldSketch(c, self.frontPlane, 'OpeningTab')
        lid = d.lidCut
        tab.polyline([(left, y, lid), (left + mm(2.5), y, lid), (right - mm(2.5), y, lid), (right, y, lid),
                      (right, y, self.top(1)), (left, y, self.top(1))])
        tab.polyline([(left + mm(2.5), y, lid), (left + mm(2.5), y, self.top(4)), (right - mm(2.5), y, self.top(4)),
                      (right - mm(2.5), y, lid)], closed=False)
        tab.close()
        tabProfiles = list(tab.sketch.profiles)
        self.along(tabProfiles, join, 1, mm(-5), name='Opening tab')
        self.step('#20 Extrude17')
        # the pocket is the lower of the two regions (6 mm high, the ring around it 9 mm)
        inner = [min(tabProfiles, key=lambda profile: _worldHeight(tab.sketch, profile))]
        self.along(inner, cut, 1, mm(-2.5), name='Opening tab pocket')
        self.step('#21 Extrude21')
        self.chamfer('#22 Chamfer7')
        self.fillet('#23 Fillet4')
        self.chamfer('#24 Chamfer10')

        side = WorldSketch(c, c.yZConstructionPlane, 'SideCutouts')
        for ya, yb in ((mm(21), mm(41)), (mm(56), L - mm(56)), (L - mm(41), L - mm(21))):
            side.rectangle((x0, ya, bottom), (x0, yb, bottom), (x0, yb, top), (x0, ya, top))
        side.close()
        self.step('#25 SideCutouts')
        sideProfiles = list(side.sketch.profiles)
        self.along(sideProfiles, cut, 0, mm(7.5), name='Left recesses')
        self.step('#26 Extrude8')
        self.along(sideProfiles, cut, 0, mm(-7.5), start=W, name='Right recesses')
        self.step('#27 Extrude9')

        backPlane = self.offsetPlane(c.xZConstructionPlane, 1, L, 'BackPlane')
        back = WorldSketch(c, backPlane, 'BackCutouts')
        xzRect(back, d.backCutoutWidth, W - d.backCutoutWidth, bottom, top, L)
        back.close()
        self.step('#28 BackCutouts')
        self.along(list(back.sketch.profiles), cut, 1, mm(-7.5), name='Back recess')
        self.step('#29 Extrude10')

        self.holders()
        self.fillet('#43 Fillet11')

    def holders(self):
        """Pred's LabelAndHandleHolder and HandleBoltHoles for the left half, mirrored to the right (#30 to #42)"""
        c = self.component
        cut = adsk.fusion.FeatureOperations.CutFeatureOperation
        join = adsk.fusion.FeatureOperations.JoinFeatureOperation
        y = mm(7.5)
        lab, mid, midX = self.lab, self.mid, self.dims.midX

        blocks = WorldSketch(c, self.frontPlane, 'HandleHolders')
        for xa, xb in ((60.25, 65.25), (72.75, 77.75)):
            blocks.rectangle((lab(xa), y, mid(14.7)), (lab(xb), y, mid(14.7)), (lab(xb), y, mid(34.7)), (lab(xa), y, mid(34.7)))
        blocks.close()
        self.step('#30 LabelAndHandleHolder')
        handleHolders = self.along(list(blocks.sketch.profiles), join, 1, mm(-7.5), name='Handle holders')
        self.step('#31 Extrude46')
        chamfer26 = self.chamfer('#32 Chamfer26')
        fillet10 = self.fillet('#33 Fillet10')

        def P(x, z):
            return (x if isinstance(x, Dim) else lab(x), y, mid(z))

        # the label rail: left side and bottom up to the middle, open at the top (Pred's profiles 4 to 10 and 13)
        rail = WorldSketch(c, self.frontPlane, 'LabelRail')
        rail.line(P(midX, 10.95), P(84.75, 10.95))
        rail.arc(P(84.75, 15.95), P(84.75, 10.95), P(79.75, 15.95))
        rail.line(P(79.75, 15.95), P(79.75, 33.45))
        rail.arc(P(84.75, 33.45), P(79.75, 33.45), P(84.75, 38.45))
        rail.polyline([P(84.75, 38.45), P(84.75, 35.95), P(82.25, 33.45), P(82.25, 15.95), P(84.75, 13.45),
                       P(midX, 13.45), P(midX, 10.95)], closed=False)
        rail.close()
        self.step('#34 HandleBoltHoles')
        railJoin = self.along(list(rail.sketch.profiles), join, 1, mm(-2.5), name='Label rail')
        self.step('#35 Extrude49')
        # the slot the label slides in: the rail without its outer band below the top corner (profiles 5 and 6)
        slot = WorldSketch(c, self.frontPlane, 'LabelSlot')
        slot.line(P(midX, 12.2), P(84.75, 12.2))
        slot.arc(P(84.75, 15.95), P(84.75, 12.2), P(81, 15.95))
        slot.polyline([P(81, 15.95), P(81, 33.45), P(79.75, 33.45)], closed=False)
        slot.arc(P(84.75, 33.45), P(79.75, 33.45), P(84.75, 38.45))
        slot.polyline([P(84.75, 38.45), P(84.75, 35.95), P(82.25, 33.45), P(82.25, 15.95), P(84.75, 13.45),
                       P(midX, 13.45), P(midX, 12.2)], closed=False)
        slot.close()
        railCut = self.along(list(slot.sketch.profiles), cut, 1, mm(-1.25), name='Label slot')
        self.step('#36 Extrude51')

        boltPlane = self.offsetPlane(c.yZConstructionPlane, 0, lab(77.75), 'HandleBoltPlane')
        bolt = WorldSketch(c, boltPlane, 'HandleBoltHoles')
        center = (lab(77.75), mm(3.75), mid(24.7))
        for diameter in (3.0, 3.5, 5.5):
            bolt.circle(center, mm(diameter))
        bolt.close()
        disc, ring, counterbore = bolt.profilesByArea([math.pi * 1.5 ** 2, math.pi * (1.75 ** 2 - 1.5 ** 2),
                                                       math.pi * (2.75 ** 2 - 1.75 ** 2)])
        hole = self.along([disc, ring], cut, 0, mm(-5), name='Handle bolt hole')
        self.step('#37 Extrude47')
        pinHole = self.along([disc], cut, 0, mm(-17.5), name='Handle pin hole')
        self.step('#38 Extrude55')
        sink = self.along([counterbore], cut, 0, mm(-3.5), name='Handle bolt head')
        self.step('#39 Extrude48')
        chamfer29 = self.chamfer('#40 Chamfer29')
        chamfer30 = self.chamfer('#41 Chamfer30')
        self.mirror([handleHolders, chamfer26, fillet10, railJoin, railCut, hole, sink, chamfer29, chamfer30, pinHole],
                    self.midXPlane, '#42 Mirror6')

    # -- Pred #44 to #59: catch tabs, catch slides, stacking tabs ------------------------------------------------

    def catches(self):
        d = self.dims
        c = self.component
        cut = adsk.fusion.FeatureOperations.CutFeatureOperation
        join = adsk.fusion.FeatureOperations.JoinFeatureOperation
        # four tab columns per latch, four rows: one at the bottom, three hanging on the top (lid cut, -10, -20 mm)
        columns = ((24, 26), (27, 29), (33, 35), (36, 38))
        rows = ((mm(-2.8), mm(2.2)), (self.top(30), self.top(25)), (self.top(20), self.top(15)), (self.top(10), self.top(5)))

        front = WorldSketch(c, self.frontPlane, 'FrontCatchTabs')
        y = mm(7.5)
        for xa, xb in columns:
            for za, zb in rows:
                front.rectangle((mm(xa), y, za), (mm(xb), y, za), (mm(xb), y, zb), (mm(xa), y, zb))
        front.close()
        self.step('#44 FrontCatchTabs')
        self.frontTabs = self.along(list(front.sketch.profiles), join, 1, mm(-3.5), name='Front catch tabs')
        self.step('#45 FrontCatchTabExtrude')
        self.frontTabChamfer = self.chamfer('#46 Chamfer1')

        sidePlane = self.offsetPlane(c.yZConstructionPlane, 0, mm(7.5), 'SideRecessPlane')
        side = WorldSketch(c, sidePlane, 'SideCatchTabs')
        x = mm(7.5)
        for ya, yb in columns:
            for za, zb in rows:
                side.rectangle((x, mm(ya), za), (x, mm(yb), za), (x, mm(yb), zb), (x, mm(ya), zb))
        side.close()
        self.step('#47 SideCatchTabs')
        self.sideTabs = self.along(list(side.sketch.profiles), join, 0, mm(-3.5), name='Side catch tabs')
        self.step('#48 Extrude12')
        self.sideTabChamfer = self.chamfer('#49 Chamfer2')

        # catch slides: 2 x 4 mm slots at the latch edges, open 4 mm at the top and at the bottom
        self.topPlane = self.offsetPlane(c.xYConstructionPlane, 2, d.bodyTop, 'TopPlane')
        slides = WorldSketch(c, self.topPlane, 'TopFeaturesAndCatchSlides')
        top = d.bodyTop
        L = d.outerLength
        for xa, xb in ((mm(19), mm(21)), (mm(41), mm(43))):
            slides.rectangle((xa, mm(1.75), top), (xb, mm(1.75), top), (xb, mm(5.75), top), (xa, mm(5.75), top))
        for ya, yb in ((mm(19), mm(21)), (mm(41), mm(43)), (L - mm(43), L - mm(41)), (L - mm(21), L - mm(19))):
            slides.rectangle((mm(1.75), ya, top), (mm(5.75), ya, top), (mm(5.75), yb, top), (mm(1.75), yb, top))
        slides.close()
        self.step('#50 TopFeaturesAndCatchSlides')
        slideProfiles = list(slides.sketch.profiles)
        self.slideTop = self.along(slideProfiles, cut, 2, mm(-4), name='Catch slides top')
        self.step('#51 Extrude13')
        self.slide = self.along(slideProfiles, cut, 2, d.catchSlideDepth * -1, start=self.top(6), name='Catch slides')
        self.step('#52 Extrude14')
        self.slideBottom = self.along(slideProfiles, cut, 2, mm(4), start=d.bottom, name='Catch slides bottom')
        self.step('#53 Extrude15')
        self.slideFillet = self.fillet('#54 Fillet2')

        # stacking: a quarter ring on top of each corner, a matching groove under each corner
        # Nutzer: "Versuche b" - full circles and two radius lines instead of concentric arcs
        stack = WorldSketch(c, self.topPlane, 'StackingTab')
        corner = (mm(14), mm(14), top)
        stack.circle(corner, mm(21.5))
        stack.circle(corner, mm(16.5))
        stack.line(corner, (mm(14), mm(3.25), top))
        stack.line(corner, (mm(3.25), mm(14), top))
        stack.close()
        tabProfiles = stack.profilesWhere(lambda x, y: x < 1.4 and y < 1.4 and 0.825 < math.hypot(x - 1.4, y - 1.4) < 1.075)
        self.stackTab = self.along(tabProfiles, join, 2, mm(1.5), name='Stacking tab')
        self.step('#55 Extrude16')
        self.stackChamfer = self.chamfer('#56 Chamfer3')
        bottomPlane = self.offsetPlane(c.xYConstructionPlane, 2, d.bottom, 'BottomPlane')
        groove = WorldSketch(c, bottomPlane, 'BottomFeatures')
        z = d.bottom
        corner = (mm(14), mm(14), z)
        # as the stacking tab: circles and radius lines, the 1 mm straight ends as open polylines on the radius lines
        groove.circle(corner, mm(22))
        groove.circle(corner, mm(15))
        groove.line(corner, (mm(14), mm(3), z))
        groove.line(corner, (mm(3), mm(14), z))
        groove.polyline([(mm(14), mm(3), z), (mm(15), mm(3), z), (mm(15), mm(6.5), z), (mm(14), mm(6.5), z)], closed=False)
        groove.polyline([(mm(3), mm(14), z), (mm(3), mm(15), z), (mm(6.5), mm(15), z), (mm(6.5), mm(14), z)], closed=False)
        groove.close()
        self.step('#57 BottomFeatures')
        def inGroove(x, y):
            ring = x < 1.4 and y < 1.4 and 0.75 < math.hypot(x - 1.4, y - 1.4) < 1.1
            return ring or (1.4 < x < 1.5 and 0.3 < y < 0.65) or (0.3 < x < 0.65 and 1.4 < y < 1.5)
        self.stackGroove = self.along(groove.profilesWhere(inGroove), cut, 2, mm(2.5), name='Stacking groove')
        self.step('#58 Extrude20')
        self.grooveChamfer = self.chamfer('#59 Chamfer9')

    # -- Pred #60 to #85: lid alignment, hinge socket, mirrors, side groove, split, lid pins, final chamfers --------

    def lidAndHinge(self):
        d = self.dims
        c = self.component
        cut = adsk.fusion.FeatureOperations.CutFeatureOperation
        join = adsk.fusion.FeatureOperations.JoinFeatureOperation
        z = d.lidCut
        L, W = d.outerLength, d.outerWidth

        def rect(sketch, xa, xb, ya, yb):
            sketch.rectangle((xa, ya, z), (xb, ya, z), (xb, yb, z), (xa, yb, z))

        def back(value):
            return L - mm(188 - value)

        side = WorldSketch(c, self.lidPlane, 'LidAlignmentSide')
        rect(side, mm(3.25), mm(6.75), mm(46.5), mm(52.5))
        rect(side, mm(3.75), mm(6.25), mm(47), mm(52))
        side.close()
        sideRing, sideInner = side.profilesByArea([21 - 12.5, 12.5])
        front = WorldSketch(c, self.lidPlane, 'LidAlignmentFront')
        rect(front, mm(46.5), mm(52.5), mm(3.25), mm(6.75))
        rect(front, mm(47), mm(52), mm(3.75), mm(6.25))
        corner = (mm(14), mm(14), z)
        for radius in (8.75, 9.25, 10.75, 11.25):
            front.arc(corner, (mm(14 - radius), mm(14), z), (mm(14), mm(14 - radius), z))
        front.polyline([(mm(14), mm(2.75), z), (mm(14), mm(3.25), z), (mm(14), mm(4.75), z), (mm(14), mm(5.25), z)], closed=False)
        front.polyline([(mm(2.75), mm(14), z), (mm(3.25), mm(14), z), (mm(4.75), mm(14), z), (mm(5.25), mm(14), z)], closed=False)
        front.polyline([(mm(14), mm(5.25), z), (mm(14.5), mm(5.25), z), (mm(14.5), mm(2.75), z), (mm(14), mm(2.75), z)], closed=False)
        front.polyline([(mm(5.25), mm(14), z), (mm(5.25), mm(14.5), z), (mm(2.75), mm(14.5), z), (mm(2.75), mm(14), z)], closed=False)
        front.close()
        self.step('#60 LidAndBasePlaneFeatures')
        sideSocket = self.along([sideRing, sideInner], cut, 2, mm(5), name='Lid pin socket side')
        self.step('#61 Extrude22')
        frontSocket = self.along(list(front.sketch.profiles), cut, 2, mm(5), name='Lid pin sockets front')
        self.step('#62 Extrude23')

        # hinge socket at the back left, symmetric about the lid cut
        def symmetric(rects, operation, half, name, step):
            sketch = WorldSketch(c, self.lidPlane, name)
            for xa, xb, ya, yb in rects:
                rect(sketch, mm(xa), mm(xb), back(ya), back(yb))
            sketch.close()
            extrudes = self.features.extrudeFeatures
            extrudeInput = extrudes.createInput(collection(list(sketch.sketch.profiles)), operation)
            extrudeInput.setSymmetricExtent(valueInput(mm(half)), False)
            extrudeInput.participantBodies = [self.base]
            feature = extrudes.add(extrudeInput)
            feature.name = name
            self.step(step)
            return feature

        hinge = [
            symmetric([(21.125, 55.125, 182.5, 188)], cut, 2.7, 'Hinge slot', '#63 Extrude24'),
            symmetric([(22.125, 54.125, 182.9, 185), (38.625, 53.625, 179.3, 181.3), (22.625, 37.625, 179.3, 181.3)],
                      cut, 9, 'Hinge tab slots', '#64 Extrude25'),
            symmetric([(42.625, 49.625, 181.3, 182.9), (26.625, 33.625, 181.3, 182.9)], cut, 5.6, 'Hinge axle room', '#65 Extrude26'),
            symmetric([(42.625, 49.625, 181.3, 182.5), (26.625, 33.625, 181.3, 182.5)], join, 2.6, 'Hinge axle seats', '#66 Extrude27'),
        ]
        hinge += [self.chamfer('#67 Chamfer13'), self.chamfer('#68 Chamfer14'), self.fillet('#69 Fillet5'),
                  self.chamfer('#70 Chamfer18')]

        # side groove for the latches of a stacked box, around the whole box (Pred's SideGroove and Sweep3)
        groove = WorldSketch(c, self.midXPlane, 'SideGroove')
        x = d.midX
        groove.polyline([(x, mm(0), mm(8.2)), (x, mm(0), mm(6.2)), (x, mm(1), mm(7.2))])
        groove.polyline([(x, mm(0), self.top(19)), (x, mm(0), self.top(21)), (x, mm(1), self.top(20))])
        groove.close()
        self.step('#71 SideGroove')
        mirror1 = self.mirror([self.sideTabs, self.sideTabChamfer, self.stackTab, self.stackChamfer, self.stackGroove,
                               self.grooveChamfer, sideSocket], self.midYPlane, '#72 Mirror1')
        self.mirror([self.frontTabs, self.frontTabChamfer, self.sideTabs, self.sideTabChamfer, mirror1, self.slideTop,
                     self.slide, self.slideBottom, self.slideFillet, self.stackTab, self.stackChamfer, self.stackGroove,
                     self.grooveChamfer, sideSocket, frontSocket] + hinge, self.midXPlane, '#73 Mirror2')
        outline = [curve for curve in self.footprint.sketch.sketchCurves.sketchLines
                   if abs(curve.startSketchPoint.geometry.y) < 1e-9 and abs(curve.endSketchPoint.geometry.y) < 1e-9]
        path = self.features.createPath(outline[0], True)
        sweeps = self.features.sweepFeatures
        sweepInput = sweeps.createInput(collection(list(groove.sketch.profiles)), path, cut)
        sweepInput.participantBodies = [self.base]
        sweeps.add(sweepInput).name = 'Side groove'
        self.step('#74 Sweep3')

        splits = self.features.splitBodyFeatures
        split = splits.add(splits.createInput(self.base, self.lidPlane, True))
        split.name = 'Lid'
        bodies = sorted([split.bodies.item(i) for i in range(split.bodies.count)], key=lambda body: body.boundingBox.minPoint.z)
        self.base, self.lid = bodies[0], bodies[-1]
        self.base.name, self.lid.name = 'Base', 'Lid'
        self.step('#75 Split1')

        # lid pins on the base rim, into the sockets of the lid
        frontPins = front.profilesByArea([12.5, math.pi / 4 * (10.75 ** 2 - 9.25 ** 2)])
        frontPin = self.along(frontPins, join, 2, mm(2.5), bodies=[self.base], name='Lid pins front')
        self.step('#76 Extrude31')
        frontPinChamfer = self.chamfer('#77 Chamfer20')
        sidePin = self.along([sideInner], join, 2, mm(2.5), bodies=[self.base], name='Lid pin side')
        self.step('#78 Extrude32')
        sidePinChamfer = self.chamfer('#79 Chamfer19')
        mirror3 = self.mirror([sidePin, sidePinChamfer], self.midYPlane, '#80 Mirror3')
        self.mirror([frontPin, frontPinChamfer, sidePin, sidePinChamfer, mirror3], self.midXPlane, '#81 Mirror4')
        self.chamfer('#82 Chamfer21', body=self.lid)
        self.chamfer('#83 Chamfer11', body=self.base)
        self.chamfer('#84 Chamfer12', body=self.lid)

    def floorPads(self):
        """Pred's Sketch21 for the first cell, built the way Nutzer chose ("Versuche b", 16.11.2026): floor inside
        12.85..49.15 mm with 1.15 mm corners; each pad is a circle (magnet / 2 + 0.75 mm) and two lines from the circle
        to the floor edges, the 5.05 mm blends of Pred's arcs follow as a fillet after the cut (floorGrid).
        Returns the floor profile, the magnet profiles and the places (x, y in cm) of the edges to blend."""
        R = self.options.magnetDiameter * 10 / 2 + 0.75
        e0, e1 = 12.85, 49.15
        b = 5.05
        z = mm(0)

        def p(x, y):
            return (mm(x), mm(y), z)

        sketch = WorldSketch(self.component, self.component.xYConstructionPlane, 'FloorPads')
        sketch.roundedRectangle(mm(e0), mm(e0), mm(e1), mm(e1), z, mm(1.15))
        pads = [(e0 + b, e0 + b, 1, 1), (e1 - b, e0 + b, -1, 1), (e1 - b, e1 - b, -1, -1), (e0 + b, e1 - b, 1, -1)]
        blends = []
        for px, py, sx, sy in pads:
            wallY = e0 if sy > 0 else e1
            wallX = e0 if sx > 0 else e1
            sketch.circle(p(px, py), mm(2 * R))
            sketch.circle(p(px, py), Dim.length(self.options.magnetDiameter))
            # the pad reaches the floor edges along the circle's tangents (Pred's blends start where they meet it)
            sketch.line(p(px + sx * R, wallY), p(px + sx * R, py))
            sketch.line(p(wallX, py + sy * R), p(px, py + sy * R))
            blends += [((px + sx * R) / 10, wallY / 10), (wallX / 10, (py + sy * R) / 10)]
        sketch.close()
        floor = sketch.profiles([((mm(e0), mm(e0), 0), (mm(e1), mm(e1), 0))])[0]
        magnet = math.pi * (self.options.magnetDiameter * 10 / 2) ** 2
        magnets = [profile for profile in sketch.sketch.profiles if abs(profile.areaProperties().area * 100 - magnet) < 1e-3]
        if len(magnets) != 4:
            raise ValueError(f'FloorPads: {len(magnets)} magnet profiles')
        return floor, magnets, blends


def _withTangentChainFallback(add):
    """Pred's edges as they are; where Fusion cannot end the chamfer there (#40 Chamfer29, ASM_BL_END_TOO_CMPLX,
    fusion-auftraege/r27_chamfer29.out) the same edges as a tangent chain, which the Fusion UI selects by default and
    which gives Pred's volume"""
    try:
        return add(False)
    except RuntimeError as error:
        if 'ASM_BL_END_TOO_CMPLX' not in str(error):
            raise
        return add(True)


def _isVerticalAt(edge, places, zLow, zHigh, tolerance=1e-6):
    geometry = edge.geometry
    if geometry.objectType != adsk.core.Line3D.classType():
        return False
    a, b = edge.startVertex.geometry, edge.endVertex.geometry
    if abs(a.x - b.x) > tolerance or abs(a.y - b.y) > tolerance:
        return False
    if abs(min(a.z, b.z) - zLow) > tolerance or abs(max(a.z, b.z) - zHigh) > tolerance:
        return False
    return any(abs(a.x - x) < tolerance and abs(a.y - y) < tolerance for x, y in places)


def _worldHeight(sketch, profile):
    box = profile.boundingBox
    return abs(sketch.sketchToModelSpace(box.maxPoint).z - sketch.sketchToModelSpace(box.minPoint).z)


def _point(p):
    return [p.x, p.y, p.z]


def _edgeItem(edge):
    geometry = edge.geometry
    kind = geometry.objectType.split('::')[-1]
    if kind == 'Line3D':
        return {'kind': 'line', 'start': _point(geometry.startPoint), 'end': _point(geometry.endPoint)}
    if kind == 'Arc3D':
        return {'kind': 'arc', 'center': _point(geometry.center), 'radius': geometry.radius,
                'start': _point(edge.startVertex.geometry), 'end': _point(edge.endVertex.geometry)}
    if kind == 'Circle3D':
        return {'kind': 'circle', 'center': _point(geometry.center), 'radius': geometry.radius}
    box = edge.boundingBox
    return {'kind': kind, 'min': _point(box.minPoint), 'max': _point(box.maxPoint)}


def _faceItem(face):
    box = face.boundingBox
    return {'kind': 'face', 'min': _point(box.minPoint), 'max': _point(box.maxPoint)}


def createPredBox(component: adsk.fusion.Component, dims: PredBoxDims, options: PredBoxOptions, onStep=None) -> PredBoxBodies:
    builder = _Builder(component, dims, options, onStep)
    builder.body()
    # Pred's order, except the cell grid (#9 to #17): it comes after the split, so the many chamfers before it work on a
    # body of a few hundred faces instead of 2800 (7 to 8 s each, fusion-auftraege/r27_steps.out). The grid lies inside
    # the walls and touches none of the faces those features use, the shape stays the same.
    builder.walls()
    builder.catches()
    builder.lidAndHinge()
    builder.floorGrid()
    builder.chamfer('#85 Chamfer16', body=builder.lid)
    return PredBoxBodies(builder.base, builder.lid)
