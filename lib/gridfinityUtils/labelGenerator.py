import os
import math
import adsk.core, adsk.fusion

from . import const, commonUtils, combineUtils, appearanceUtils, textStyles, binLabelLayout, sketchUtils
from .dim import Dim, valueInput, applyTo

LABEL_STYLE_OUTLINE = 'Outline'
LABEL_STYLE_ENGRAVED = 'Engraved'
LABEL_STYLE_EMBOSSED = 'Embossed'
# a socket for exchangeable Cullenect inserts instead of a label, see cullenect
LABEL_STYLE_CULLENECT = 'Cullenect'
LABEL_STYLES = [LABEL_STYLE_OUTLINE, LABEL_STYLE_ENGRAVED, LABEL_STYLE_EMBOSSED, LABEL_STYLE_CULLENECT]

LABEL_ICON_NONE = 'None'
LABEL_ICONS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labelIcons')

# icons are grouped by type in folders, these types come first in this order, any others after them
LABEL_ICON_TYPE_ORDER = ['screws', 'nuts', 'washers', 'inserts', 'magnets', 'crimps']

def iconName(fileName: str) -> str:
    """hex-nut.svg shows as Hex nut"""
    return os.path.splitext(fileName)[0].replace('-', ' ').capitalize()

class LabelIcon():
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path

    @property
    def previewFolder(self) -> str:
        """Dropdown preview images, rendered by tools/labelIcons.py, empty when there are none"""
        folder = os.path.splitext(self.path)[0]
        return folder if os.path.isfile(os.path.join(folder, '16x16.png')) else ''

def listIconGroups() -> list[list[LabelIcon]]:
    """Icons grouped by type in the order shown, svg files outside a type folder come last"""
    if not os.path.isdir(LABEL_ICONS_FOLDER):
        return []
    def svgIcons(folder: str) -> list[LabelIcon]:
        fileNames = sorted(fileName for fileName in os.listdir(folder) if fileName.lower().endswith('.svg'))
        return [LabelIcon(iconName(fileName), os.path.join(folder, fileName)) for fileName in fileNames]
    types = [entry for entry in os.listdir(LABEL_ICONS_FOLDER) if os.path.isdir(os.path.join(LABEL_ICONS_FOLDER, entry))]
    types.sort(key=lambda entry: (LABEL_ICON_TYPE_ORDER.index(entry) if entry in LABEL_ICON_TYPE_ORDER else len(LABEL_ICON_TYPE_ORDER), entry))
    groups = [svgIcons(os.path.join(LABEL_ICONS_FOLDER, entry)) for entry in types] + [svgIcons(LABEL_ICONS_FOLDER)]
    return [group for group in groups if len(group) > 0]

def iconPath(name: str) -> str | None:
    return next((icon.path for group in listIconGroups() for icon in group if icon.name == name), None)

class BinLabelDefinition():
    """What goes on one label tab, the text parameter drives the text so it can be edited later"""
    def __init__(self, textParameter: adsk.fusion.UserParameter = None, iconPath: str = None):
        self.textParameter = textParameter
        self.iconPath = iconPath

    @property
    def isEmpty(self) -> bool:
        return self.textParameter is None and self.iconPath is None

class BinLabelInput():
    def __init__(self):
        self.style = LABEL_STYLE_OUTLINE
        self.isBold = True
        self.depth = const.BIN_LABEL_DEPTH
        self.definition: BinLabelDefinition = None
        # label area on the tab top face, the dims let it follow the parameters
        self.originX: Dim = None
        self.originY: Dim = None
        self.originZ: Dim = None
        self.width: Dim = None
        self.length: float = 0
        # turns the label down towards the front about its back edge, for tilted tab tops
        self.tiltAngle: float = 0
        # '#RRGGBB' keeps the letters as bodies of their own in this color, empty joins or cuts them, see labelColors
        self.color: str = ''

def _curveBounds(curves) -> tuple[float, float, float, float] | None:
    """Min and max x and y over sampled points of the given geometry curves"""
    bounds = None
    for curve in curves:
        line = adsk.core.Line3D.cast(curve)
        if line is not None:
            # the ends are its extremes, svg symbols are mostly lines, a thousand of them for a round one
            points = [line.startPoint, line.endPoint]
        else:
            evaluator = curve.evaluator
            (_, start, end) = evaluator.getParameterExtents()
            parameters = [start + (end - start) * i / 16 for i in range(17)]
            (_, points) = evaluator.getPointsAtParameters(parameters)
        for point in points:
            if bounds is None:
                bounds = [point.x, point.y, point.x, point.y]
            bounds = [min(bounds[0], point.x), min(bounds[1], point.y), max(bounds[2], point.x), max(bounds[3], point.y)]
    return tuple(bounds) if bounds is not None else None

def _sketchCurvesBounds(sketch: adsk.fusion.Sketch) -> tuple[float, float, float, float] | None:
    return _curveBounds([curve.geometry for curve in sketch.sketchCurves])

def _applyStyle(textInput: adsk.fusion.SketchTextInput, style: str):
    """Font and boldness of the text style, see textStyles. The font stays with the sketch text, so a later change of
    its text parameter keeps it"""
    (fontName, isBold) = textStyles.fontAndBold(style)
    if fontName is not None:
        textInput.fontName = fontName
    if isBold:
        textInput.textStyle = adsk.fusion.TextStyles.TextStyleBold

def _addText(
    sketch: adsk.fusion.Sketch,
    text: str,
    height: float,
    corner: adsk.core.Point3D,
    diagonal: adsk.core.Point3D,
    style: str,
    isCentered: bool,
) -> adsk.fusion.SketchText:
    textInput = sketch.sketchTexts.createInput2(text, height)
    textInput.setAsMultiLine(
        corner,
        diagonal,
        adsk.core.HorizontalAlignments.CenterHorizontalAlignment if isCentered else adsk.core.HorizontalAlignments.LeftHorizontalAlignment,
        adsk.core.VerticalAlignments.MiddleVerticalAlignment,
        0,
    )
    _applyStyle(textInput, style)
    return sketch.sketchTexts.add(textInput)

def _measureText(sketch: adsk.fusion.Sketch, text: str, height: float, style: str) -> tuple[float, float] | None:
    """Width and height of the letters of the text style at the given text height, measured on a throwaway text
    with a box wide enough not to wrap"""
    origin = adsk.core.Point3D.create(0, 0, 0)
    probe = _addText(sketch, text, height, origin, adsk.core.Point3D.create(height * len(text) * 10, height * 10, 0), style, False)
    bounds = _curveBounds(probe.asCurves())
    probe.deleteMe()
    return None if bounds is None else (bounds[2] - bounds[0], bounds[3] - bounds[1])

def _iconProfiles(sketch: adsk.fusion.Sketch) -> list[adsk.fusion.Profile]:
    """Filled regions of the icon, profiles nested an odd number of times are its holes"""
    profiles = list(sketch.profiles)
    def contains(outer: adsk.fusion.Profile, inner: adsk.fusion.Profile) -> bool:
        a = outer.boundingBox
        b = inner.boundingBox
        tolerance = const.DEFAULT_FILTER_TOLERANCE
        return outer != inner \
            and a.minPoint.x <= b.minPoint.x + tolerance and a.minPoint.y <= b.minPoint.y + tolerance \
            and a.maxPoint.x >= b.maxPoint.x - tolerance and a.maxPoint.y >= b.maxPoint.y - tolerance \
            and (a.maxPoint.x - a.minPoint.x) * (a.maxPoint.y - a.minPoint.y) > (b.maxPoint.x - b.minPoint.x) * (b.maxPoint.y - b.minPoint.y)
    return [profile for profile in profiles if sum(1 for other in profiles if contains(other, profile)) % 2 == 0]

def _importMeasured(sketch: adsk.fusion.Sketch, path: str, x: float, y: float, scale: float, keep: bool = False) -> tuple[float, float, float, float] | None:
    """Bounds of the svg imported at the given position and scale into the sketch when kept, else into a throwaway
    sketch on the same plane. Deleting the sketch is quick, deleting curves one by one took 0.3 s each, minutes for the
    thousand curves of a Cullenect hardware symbol"""
    target = sketch if keep else sketch.parentComponent.sketches.add(sketch.referencePlane)
    target.importSVG(path, x, y, scale)
    bounds = _sketchCurvesBounds(target)
    if not keep:
        target.deleteMe()
    return bounds

def _importIcon(sketch: adsk.fusion.Sketch, path: str, minX: float, minY: float, height: float):
    """Imports the svg scaled to the given height with its bottom left corner at the given point.
    How the svg units and import position map to the sketch isn't documented, so the svg is imported
    to measure both and then imported where it belongs"""
    bounds = _importMeasured(sketch, path, 0, 0, 1)
    if bounds is None:
        return
    scale = height / (bounds[3] - bounds[1])
    scaled = _importMeasured(sketch, path, 0, 0, scale)
    # the position moves the import by a unit step in each direction, one way or the other
    stepped = _importMeasured(sketch, path, 1, 1, scale)
    directionX = 1 if stepped[0] >= scaled[0] else -1
    directionY = 1 if stepped[1] >= scaled[1] else -1
    targetMinX = minX
    targetMinY = minY
    placed = _importMeasured(sketch, path, (targetMinX - scaled[0]) * directionX, (targetMinY - scaled[1]) * directionY, scale, keep=True)
    commonUtils.debugLog(f'icon {os.path.basename(path)} placed at {placed[0]:.3f}, {placed[1]:.3f}, expected {targetMinX:.3f}, {targetMinY:.3f}')

def _iconMeasure(sketch: adsk.fusion.Sketch, path: str) -> tuple[float, int] | None:
    """Width of the drawn icon per unit of its height and the number of its points, from an import into a throwaway
    sketch on the same plane"""
    target = sketch.parentComponent.sketches.add(sketch.referencePlane)
    target.importSVG(path, 0, 0, 1)
    bounds = _sketchCurvesBounds(target)
    points = target.sketchPoints.count - 1
    target.deleteMe()
    if bounds is None or bounds[3] - bounds[1] <= 0:
        return None
    return ((bounds[2] - bounds[0]) / (bounds[3] - bounds[1]), points)


def _offsetPlane(component: adsk.fusion.Component, base: adsk.fusion.ConstructionPlane, offset: Dim, name: str) -> adsk.fusion.ConstructionPlane:
    planeInput = component.constructionPlanes.createInput()
    planeInput.setByOffset(base, valueInput(offset))
    plane = component.constructionPlanes.add(planeInput)
    plane.name = name
    plane.isLightBulbOn = False
    return plane


def _pointOf(component: adsk.fusion.Component, planes: tuple, name: str) -> adsk.fusion.ConstructionPoint:
    pointInput = component.constructionPoints.createInput()
    pointInput.setByThreePlanes(*planes)
    point = component.constructionPoints.add(pointInput)
    point.name = name
    point.isLightBulbOn = False
    return point


def _labelPlane(
    component: adsk.fusion.Component,
    placement: binLabelLayout.BinLabelPlacement,
    length: float,
    name: str,
) -> tuple[adsk.fusion.ConstructionPlane, adsk.fusion.ConstructionAxis]:
    """
    The plane of the label face and its back edge, both following the bin's parameters. Flat it is the plane at the
    label's height. Tilted it goes through three points made of offset planes, the back edge at both sides and the
    front edge: a plane at an angle to the back edge (setByAngle) turned to the other side when the height changed
    (Fusion 15.11.2026), the one through the points kept its side through height, width, length and text. The points
    go around so its normal points up: a sketch seen from below shows its text mirrored. Its sketch has the projection
    of the component origin as its origin, sketch x may run against model x
    """
    top = _offsetPlane(component, component.xYConstructionPlane, placement.planeZ, f'{name} plane')
    back = _offsetPlane(component, component.xZConstructionPlane, placement.hingeY, f'{name} back plane')
    # the points only need to be apart along the back edge, the label's own x is held by the sketch's dims
    side = _offsetPlane(component, component.yZConstructionPlane, Dim.length(1), f'{name} side plane')
    left = _pointOf(component, (component.yZConstructionPlane, back, top), f'{name} back left')
    right = _pointOf(component, (side, back, top), f'{name} back right')
    axisInput = component.constructionAxes.createInput()
    axisInput.setByTwoPoints(left, right)
    edge = component.constructionAxes.add(axisInput)
    edge.name = f'{name} back edge'
    edge.isLightBulbOn = False
    if placement.tiltAngle == 0:
        return (top, edge)
    front = _offsetPlane(component, component.xZConstructionPlane, placement.hingeY - Dim.length(length * math.cos(placement.tiltAngle)), f'{name} front plane')
    low = _offsetPlane(component, component.xYConstructionPlane, placement.planeZ - Dim.length(length * math.sin(placement.tiltAngle)), f'{name} front edge plane')
    frontLeft = _pointOf(component, (component.yZConstructionPlane, front, low), f'{name} front left')
    planeInput = component.constructionPlanes.createInput()
    # back left, front left, back right: their normal points up
    planeInput.setByThreePoints(left, frontLeft, right)
    plane = component.constructionPlanes.add(planeInput)
    plane.name = f'{name} face plane'
    plane.isLightBulbOn = False
    return (plane, edge)


def _magnitude(value: Dim) -> Dim:
    """A distance dimension is a length, so a model x left of the origin is driven by its negative, the point stays on
    its side of the origin as long as the parameters keep it there"""
    return value if value.value >= 0 else Dim.length(0) - value


def _projectedEdge(sketch: adsk.fusion.Sketch, edge: adsk.fusion.ConstructionAxis) -> tuple[adsk.fusion.SketchLine, int]:
    """The back edge in the sketch, and which way the front is along sketch y, where model y is lower"""
    projected = [entity for entity in sketch.project(edge) if adsk.fusion.SketchLine.cast(entity) is not None]
    edgeLine = adsk.fusion.SketchLine.cast(projected[0])
    edgeStart = edgeLine.startSketchPoint.geometry
    stepped = sketch.sketchToModelSpace(adsk.core.Point3D.create(edgeStart.x, edgeStart.y + 0.1, 0))
    front = -1 if stepped.y > sketch.sketchToModelSpace(edgeStart).y else 1
    return (edgeLine, front)


def _faceSketchPoint(sketch: adsk.fusion.Sketch, placement: binLabelLayout.BinLabelPlacement, x: float, fromBack: float) -> adsk.core.Point3D:
    """The point of the label face at model x and the distance from the back edge, in sketch space"""
    return sketch.modelToSketchSpace(adsk.core.Point3D.create(
        x,
        placement.hingeY.value - fromBack * math.cos(placement.tiltAngle),
        placement.planeZ.value - fromBack * math.sin(placement.tiltAngle),
    ))


def _baselineTexts(
    sketch: adsk.fusion.Sketch,
    edge: adsk.fusion.ConstructionAxis,
    placement: binLabelLayout.BinLabelPlacement,
    text: str,
    textHeight: float,
    textParameter: adsk.fusion.UserParameter,
    style: str,
    count: int,
) -> list[adsk.fusion.SketchText]:
    """
    The text standing on a line parallel to the back edge, its ends driven by the label's x, as one text or as twins
    driven by the same parameter, see cullenectLabelGenerator._texts. Text along a line never breaks into lines, a box
    did for a text made longer (p84). Before the text the sketch is fully constrained, with it Fusion doesn't say so,
    the exception Joerg allowed (p50)
    """
    (edgeLine, front) = _projectedEdge(sketch, edge)
    start = _faceSketchPoint(sketch, placement, placement.baselineStartX.value, placement.baselineFromBack)
    end = _faceSketchPoint(sketch, placement, placement.baselineEndX.value, placement.baselineFromBack)
    baseline = sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
    baseline.isConstruction = True
    sketch.geometricConstraints.addParallel(baseline, edgeLine)
    dimensions = sketch.sketchDimensions
    edgeStart = edgeLine.startSketchPoint.geometry
    offset = dimensions.addOffsetDimension(edgeLine, baseline, adsk.core.Point3D.create((start.x + end.x) / 2, (edgeStart.y + start.y) / 2, 0))
    offset.parameter.value = placement.baselineFromBack
    ends = []
    for (point, modelX, at) in ((baseline.startSketchPoint, placement.baselineStartX, start), (baseline.endSketchPoint, placement.baselineEndX, end)):
        dimension = dimensions.addDistanceDimension(sketch.originPoint, point, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(at.x, at.y + front * 0.2, 0))
        applyTo(dimension.parameter, _magnitude(modelX))
        ends.append(dimension)
    texts = []
    for _ in range(count):
        textInput = sketch.sketchTexts.createInput2(text, textHeight)
        alignment = adsk.core.HorizontalAlignments.CenterHorizontalAlignment if placement.isCentered else adsk.core.HorizontalAlignments.LeftHorizontalAlignment
        textInput.setAsAlongPath(baseline, True, alignment, 0)
        _applyStyle(textInput, style)
        sketchText = sketch.sketchTexts.add(textInput)
        sketchText.textParameter.expression = textParameter.name
        texts.append(sketchText)
    if not placement.isCentered and len(texts) > 0:
        # Text along a line starts its first letter later than the line by that letter's lead, the text box put the
        # letter itself at its side: after an icon the gap came out 2.6 mm instead of 1.8 mm (snapshots, Fusion
        # 15.11.2026). The line starts earlier by what the letters are off
        bounds = _curveBounds(texts[0].asCurves())
        if bounds is not None:
            left = min(sketch.sketchToModelSpace(adsk.core.Point3D.create(x, bounds[1], 0)).x for x in (bounds[0], bounds[2]))
            lead = left - placement.baselineStartX.value
            if abs(lead) > const.DEFAULT_FILTER_TOLERANCE:
                startX = _magnitude(placement.baselineStartX - Dim.length(lead))
                if startX.isExpression:
                    ends[0].parameter.expression = startX.expression
                else:
                    ends[0].parameter.value = startX.value
    return texts


def _heldIcon(
    sketch: adsk.fusion.Sketch,
    edge: adsk.fusion.ConstructionAxis,
    placement: binLabelLayout.BinLabelPlacement,
    path: str,
    iconSize: float,
    name: str,
) -> list[adsk.fusion.Profile]:
    """
    A small icon drawn on the label face and held there by dims: its imported curves are let go, one of its points is
    driven by the label's x and kept at its distance from the back edge, every other point at its distance from that
    one (Fusion 15.11.2026, proposal A, see binLabelLayout.ICON_POINTS_HELD_BY_DIMS). Where sketch x runs against model
    x the import is turned half round, it would stand on its head otherwise
    """
    corner = _faceSketchPoint(sketch, placement, placement.iconMinX.value, placement.iconMinFromBack)
    _importIcon(sketch, path, corner.x, corner.y, iconSize)
    curves = list(sketch.sketchCurves)
    points = [point for point in sketch.sketchPoints if point != sketch.originPoint]
    if len(points) == 0:
        return []
    # projected before the compute is deferred, a projection into a deferred sketch came back empty (Fusion
    # 15.11.2026), and after the icon's points are counted, its own aren't to be held
    (edgeLine, front) = _projectedEdge(sketch, edge)
    with sketchUtils.deferSketchCompute(sketch):
        for curve in curves:
            if curve.isFixed:
                curve.isFixed = False
        for point in points:
            if point.isFixed:
                point.isFixed = False
        (_, xAxis, _, _) = sketch.transform.getAsCoordinateSystem()
        if xAxis.x < 0:
            turn = adsk.core.Matrix3D.create()
            turn.setToRotation(math.pi, adsk.core.Vector3D.create(0, 0, 1), corner)
            sketch.move(commonUtils.objectCollectionFromList(curves), turn)
        anchor = points[0]
        dimensions = sketch.sketchDimensions
        horizontal = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
        vertical = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
        anchorX = sketch.sketchToModelSpace(anchor.geometry).x
        across = dimensions.addDistanceDimension(sketch.originPoint, anchor, horizontal, adsk.core.Point3D.create(anchor.geometry.x, anchor.geometry.y + front * 0.2, 0))
        applyTo(across.parameter, _magnitude(placement.iconMinX + Dim.length(anchorX - placement.iconMinX.value)))
        dimensions.addDistanceDimension(edgeLine.startSketchPoint, anchor, vertical, adsk.core.Point3D.create(anchor.geometry.x - 0.2, anchor.geometry.y, 0))
        refused = 0
        for point in points[1:]:
            for orientation in (horizontal, vertical):
                try:
                    dimensions.addDistanceDimension(anchor, point, orientation, point.geometry)
                except RuntimeError:
                    # already held, by a constraint of the import or the dims so far
                    refused += 1
    commonUtils.debugLog(f'{name}: icon {os.path.basename(path)} held by dims, {len(points)} points, {refused} dims not needed')
    return _iconProfiles(sketch)


def _movedIcon(
    component: adsk.fusion.Component,
    input: BinLabelInput,
    placement: binLabelLayout.BinLabelPlacement,
    path: str,
    iconSize: float,
    isEmbossed: bool,
    isOutline: bool,
    name: str,
) -> list[adsk.fusion.BRepBody]:
    """
    A large icon as bodies of its own, laid out flat at the label's current spot, turned down by the tilt and moved
    by how far the parametric spot is from there, as labels were built before round 14. Its bodies don't change with
    the text, so the move keeps all of them, but its fixed curves wouldn't follow the label's x and holding hundreds of
    points by dims took over a minute (Fusion 15.11.2026, proposal A). The text is never moved
    """
    flat = _offsetPlane(component, component.xYConstructionPlane, Dim.length(placement.planeZ.value), f'{name} icon plane')
    sketch: adsk.fusion.Sketch = component.sketches.add(flat)
    sketch.name = f'{name} icon sketch'
    _importIcon(sketch, path, placement.iconMinX.value, placement.hingeY.value - placement.iconMinFromBack, iconSize)
    profiles = _iconProfiles(sketch)
    if len(profiles) == 0:
        return []
    def extrude(isThin: bool) -> adsk.fusion.ExtrudeFeature:
        return _extrudeOnFace(component, profiles, adsk.fusion.FeatureOperations.NewBodyFeatureOperation, isEmbossed, flat, input.depth, f'{name} icon', None, isThin)
    if isOutline:
        try:
            iconExtrude = extrude(True)
        except RuntimeError as err:
            commonUtils.debugLog(f'{name}: outline extrude of the icon failed, engraving instead, {err}')
            iconExtrude = extrude(False)
    else:
        iconExtrude = extrude(False)
    bodies = list(iconExtrude.bodies)
    features = component.features
    if placement.tiltAngle != 0:
        # turning about +x takes the front edge down
        tilt = adsk.core.Matrix3D.create()
        tilt.setToRotation(placement.tiltAngle, adsk.core.Vector3D.create(1, 0, 0), adsk.core.Point3D.create(0, placement.hingeY.value, placement.planeZ.value))
        tiltInput = features.moveFeatures.createInput2(commonUtils.objectCollectionFromList(bodies))
        tiltInput.defineAsFreeMove(tilt)
        features.moveFeatures.add(tiltInput).name = f'{name} icon tilt'
    shiftX = placement.iconMinX - Dim.length(placement.iconMinX.value)
    shiftY = placement.hingeY - Dim.length(placement.hingeY.value)
    shiftZ = placement.planeZ - Dim.length(placement.planeZ.value)
    if shiftX.isExpression or shiftY.isExpression or shiftZ.isExpression:
        moveInput = features.moveFeatures.createInput2(commonUtils.objectCollectionFromList(bodies))
        moveInput.defineAsTranslateXYZ(valueInput(shiftX), valueInput(shiftY), valueInput(shiftZ), True)
        features.moveFeatures.add(moveInput).name = f'{name} icon placement'
    commonUtils.debugLog(f'{name}: icon {os.path.basename(path)} moved into place')
    return bodies


def _extrudeOnFace(
    component: adsk.fusion.Component,
    profiles: list,
    operation: adsk.fusion.FeatureOperations,
    isUp: bool,
    plane: adsk.fusion.ConstructionPlane,
    depth: float,
    name: str,
    participants: list | None = None,
    isThin: bool = False,
) -> adsk.fusion.ExtrudeFeature:
    """Up out of the face or down into it, whichever way the plane's normal points"""
    extrudeInput = component.features.extrudeFeatures.createInput(commonUtils.objectCollectionFromList(profiles), operation)
    isAlongNormal = (plane.geometry.normal.z > 0) == isUp
    extrudeInput.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(depth)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection if isAlongNormal else adsk.fusion.ExtentDirections.NegativeExtentDirection,
    )
    if isThin:
        extrudeInput.setThinExtrude(adsk.fusion.ThinExtrudeWallLocation.Center, adsk.core.ValueInput.createByReal(const.BIN_LABEL_OUTLINE_THICKNESS))
    if participants is not None:
        extrudeInput.participantBodies = participants
    extrude = component.features.extrudeFeatures.add(extrudeInput)
    extrude.name = name
    return extrude


def createLabel(
    input: BinLabelInput,
    targetBody: adsk.fusion.BRepBody,
    targetComponent: adsk.fusion.Component,
    *,
    name: str,
    textOccurrence=None,
    targetOccurrence: adsk.fusion.Occurrence | None = None,
    binPlacement: tuple[float, float] = (0, 0),
) -> list[adsk.fusion.BRepBody]:
    """
    Icon at the left as tall as the letters of the text after it, standing on their baseline, text alone is centered.
    Drawn at its finished spot on planes that follow the bin's parameters, without a move (round 14, p72): a move takes
    the letter bodies there are, and letters a longer text adds stayed at the origin, untilted and out of the bin. The
    cut or join is the extrusion's own operation on the target body, not a combine with a list of bodies, for the same
    reason. Shown in Fusion 15.11.2026: the letters of a longer text follow height, width, length and tilt, and cut,
    join and the colored cut take them. A large icon is the exception, its bodies are moved, see _movedIcon.
    Planes, sketches and features are named after the given name.
    With a color the label stays bodies of their own in that color, for printing in another filament (p86): raised
    ones stand on the tab, an engraved or outline cut is filled flush by them. They are built in the Text component when
    textOccurrence is given, an assembly.TextOccurrence made on first use (round 13, p90); the cut into the bin from
    there takes it as seen through targetOccurrence, Fusion refused it otherwise, and a twin of the text cuts, Fusion
    won't extrude one text twice. Returns the colored bodies named '<name> text N' from left to right, without a color
    none. They are built where the bin ends up, binPlacement from where it's built, and aren't to be moved with it
    """
    textParameter = input.definition.textParameter
    text = textParameter.textValue if textParameter is not None else ''
    iconPath = input.definition.iconPath
    if len(text) == 0 and iconPath is None:
        return []
    markingOccurrence = textOccurrence.get() if input.color and textOccurrence is not None and textOccurrence.isAvailable else None
    component = markingOccurrence.component if markingOccurrence is not None else targetComponent
    contentWidth = input.width.value - const.BIN_LABEL_SIDE_MARGIN * 2
    contentHeight = input.length - const.BIN_LABEL_MARGIN * 2
    style = textStyles.styleOfBold(input.isBold)
    isEmbossed = input.style == LABEL_STYLE_EMBOSSED
    isOutline = input.style == LABEL_STYLE_OUTLINE
    isColored = bool(input.color)

    # The cut into the bin or the join happens where the bin is when it's built, the colored letters are drawn where the
    # bin ends up: a bin beside others is moved there after it's built (binBuilder, "Bin placement"), and a move of the
    # letter bodies would leave behind the letters a longer text adds (review of round 14). A colored label at the
    # origin draws both on one face
    (shiftX, shiftY) = binPlacement if isColored else (0, 0)
    needsCut = not isColored or not isEmbossed
    isOneFace = not isColored or (shiftX == 0 and shiftY == 0)

    def facePlacement(dx: float, dy: float, lettersHeight: float, iconWidth: float, iconHeight: float) -> binLabelLayout.BinLabelPlacement:
        originX = input.originX + Dim.length(dx) if dx != 0 else input.originX
        originY = input.originY + Dim.length(dy) if dy != 0 else input.originY
        return binLabelLayout.binLabelPlacement(
            originX, originY, input.originZ, input.width, input.length, input.tiltAngle,
            lettersHeight, iconWidth, iconHeight, iconPath is not None, len(text) > 0,
        )

    # (offset, feature name, how many texts: the twin a colored cut needs and the letters on one face)
    faceSpecs = []
    if isOneFace:
        faceSpecs.append(((shiftX, shiftY), name, 2 if isColored and needsCut else 1))
    else:
        if needsCut:
            faceSpecs.append(((0, 0), f'{name} cut', 1))
        faceSpecs.append(((shiftX, shiftY), name, 1))
    # the planes don't depend on the size of the letters and the icon, they're measured on the first face
    faces = []
    for ((dx, dy), faceName, _) in faceSpecs:
        (plane, edge) = _labelPlane(component, facePlacement(dx, dy, 0, 0, 0), input.length, faceName)
        faces.append((plane, edge))
    (firstPlane, _) = faces[0]
    sketch: adsk.fusion.Sketch = component.sketches.add(firstPlane)
    sketch.name = f'{faceSpecs[0][1]} text sketch' if len(text) > 0 else f'{faceSpecs[0][1]} icon sketch'
    (iconAspect, iconPoints) = (0, 0)
    if iconPath is not None:
        (iconAspect, iconPoints) = _iconMeasure(sketch, iconPath) or (1, 0)
    gap = const.BIN_LABEL_ICON_GAP if iconPath is not None else 0
    # the icon is as tall as the letters, so both grow and shrink together. Letters start as tall as the label
    # allows, then everything scales down until the icon, gap and text fit the label width
    iconSize = contentHeight * const.BIN_LABEL_TEXT_HEIGHT_RATIO
    textHeight = contentHeight
    lettersHeight = iconSize
    if len(text) > 0:
        measured = _measureText(sketch, text, textHeight, style)
        if measured is not None and measured[1] > 0:
            (measuredWidth, measuredHeight) = measured
            scale = min(
                contentHeight * const.BIN_LABEL_TEXT_HEIGHT_RATIO / measuredHeight,
                (contentWidth - gap) / (measuredWidth + measuredHeight * iconAspect),
            )
            textHeight *= scale
            lettersHeight = measuredHeight * scale
            iconSize = lettersHeight
        # a long text on a short bin shrinks, the command hints at it when it gets too thin to print (p130)
        textStyles.noteText(text, style, textHeight)
    elif iconPath is not None:
        iconSize = min(contentHeight, contentWidth / iconAspect)
    isIconHeld = iconPath is not None and binLabelLayout.isIconHeldByDims(iconPoints)

    # per face its texts and held icon profiles, on the sketch measured on for the first
    drawn = []
    for (index, (((dx, dy), faceName, textCount), (plane, edge))) in enumerate(zip(faceSpecs, faces)):
        placement = facePlacement(dx, dy, lettersHeight, iconSize * iconAspect, iconSize)
        textSketch = sketch if index == 0 else None
        texts = []
        if len(text) > 0:
            if textSketch is None:
                textSketch = component.sketches.add(plane)
                textSketch.name = f'{faceName} text sketch'
            texts = _baselineTexts(textSketch, edge, placement, text, textHeight, textParameter, style, textCount)
        iconProfiles = []
        if isIconHeld:
            iconSketch = textSketch if textSketch is not None and len(text) == 0 else component.sketches.add(plane)
            iconSketch.name = f'{faceName} icon sketch'
            iconProfiles = _heldIcon(iconSketch, edge, placement, iconPath, iconSize, faceName)
        drawn.append((plane, texts, iconProfiles))
    iconBodies = []
    if iconPath is not None and not isIconHeld:
        unplaced = facePlacement(0, 0, lettersHeight, iconSize * iconAspect, iconSize)
        iconBodies = _movedIcon(component, input, unplaced, iconPath, iconSize, isEmbossed, isOutline, name)
    # the bin as seen from the Text component, Fusion refused it otherwise (round 13)
    target = targetBody.createForAssemblyContext(targetOccurrence) if markingOccurrence is not None and targetOccurrence is not None else targetBody

    # an outline whose thin extrusion failed is engraved, the inlay as well as the cut it fills
    isThin = [isOutline]

    def extrude(plane, profiles: list, operation: adsk.fusion.FeatureOperations, participants: list | None, featureName: str) -> adsk.fusion.ExtrudeFeature:
        if isThin[0]:
            try:
                return _extrudeOnFace(component, profiles, operation, isEmbossed, plane, input.depth, featureName, participants, True)
            except RuntimeError as err:
                commonUtils.debugLog(f'{name}: outline extrude failed, engraving instead, {err}')
                isThin[0] = False
        return _extrudeOnFace(component, profiles, operation, isEmbossed, plane, input.depth, featureName, participants)

    labelBodies = []
    (lettersPlane, lettersTexts, lettersIcon) = drawn[-1]
    if not isColored:
        if len(lettersTexts) + len(lettersIcon) > 0:
            extrude(lettersPlane, lettersTexts + lettersIcon, adsk.fusion.FeatureOperations.JoinFeatureOperation if isEmbossed else adsk.fusion.FeatureOperations.CutFeatureOperation, [target], name)
    else:
        if needsCut:
            (cutPlane, cutTexts, cutIcon) = drawn[0]
            # on one face the twin is the second text, on a face of its own its only one
            cutProfiles = (cutTexts[1:] if isOneFace else cutTexts) + cutIcon
            if len(cutProfiles) > 0:
                extrude(cutPlane, cutProfiles, adsk.fusion.FeatureOperations.CutFeatureOperation, [target], f'{name} cut')
        marked = lettersTexts[:1] + lettersIcon
        if len(marked) > 0:
            labelBodies = list(extrude(lettersPlane, marked, adsk.fusion.FeatureOperations.NewBodyFeatureOperation, None, name).bodies)
    if len(iconBodies) > 0:
        # the moved icon's bodies are the same whatever the text, a combine with them keeps all
        if not isColored:
            if isEmbossed:
                combineUtils.joinBodies(targetBody, commonUtils.objectCollectionFromList(iconBodies), targetComponent, name=f'{name} icon join')
            else:
                combineUtils.cutBody(targetBody, commonUtils.objectCollectionFromList(iconBodies), targetComponent, False, name=f'{name} icon cut')
        else:
            if not isEmbossed:
                tools = [body.createForAssemblyContext(markingOccurrence) for body in iconBodies] if markingOccurrence is not None else iconBodies
                combineUtils.cutBody(target, commonUtils.objectCollectionFromList(tools), targetComponent, True, name=f'{name} icon cut')
            if shiftX != 0 or shiftY != 0:
                # cut where the bin is built, then where it ends up like the letters
                moveInput = component.features.moveFeatures.createInput2(commonUtils.objectCollectionFromList(iconBodies))
                moveInput.defineAsTranslateXYZ(valueInput(Dim.length(shiftX)), valueInput(Dim.length(shiftY)), valueInput(Dim.length(0)), True)
                component.features.moveFeatures.add(moveInput).name = f'{name} icon bin placement'
            labelBodies += iconBodies
    if isColored:
        # names a snapshot pairs them by, Fusion keeps letters that don't touch as bodies of their own
        labelBodies.sort(key=lambda body: (round(body.boundingBox.minPoint.x, 4), body.boundingBox.minPoint.y))
        for (index, body) in enumerate(labelBodies):
            body.name = f'{name} text {index + 1}'
    commonUtils.debugLog(f'{name}: {input.style.lower()}, text parameter {textParameter.name if textParameter is not None else None}, icon {iconPath} ({iconPoints} points), color {input.color or None}')
    # on the Text occurrence, the letters a longer text adds show it (p120)
    appearanceUtils.colorPart(labelBodies, markingOccurrence, input.color)
    return labelBodies
