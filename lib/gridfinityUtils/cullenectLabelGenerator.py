import adsk.core, adsk.fusion

from . import const, commonUtils, combineUtils, filletUtils, sketchUtils, cullenectLabelLayout, cullenectCatalog
from .labelGenerator import _addText, _measureText, _iconProfiles, _importIcon
from .dim import Dim, valueInput

# Insert for the Cullenect label system, after cullenect_base_v2 and cullenect_label_generate in Cullenect.scad by
# CullenJWebb (MIT), https://github.com/CullenJWebb/Cullenect-Labels: a 1.2 mm plate with rounded corners whose middle
# layer is set in all around as the latch, text at the left and a symbol at the right, one layer high

SURFACE_EMBOSSED = 'Embossed'
SURFACE_DEBOSSED = 'Debossed'
SURFACE_FLUSH = 'Flush'
SURFACES = [SURFACE_EMBOSSED, SURFACE_DEBOSSED, SURFACE_FLUSH]


class CullenectLabelInput():
    def __init__(self):
        # width as a dim, so the insert follows the width parameter, height in cm
        self.width: Dim = None
        self.height: float = const.CULLENECT_LABEL_HEIGHT
        self.lines: list[str] = []
        self.iconPath: str | None = None
        self.isScrew: bool = False
        self.surface: str = SURFACE_EMBOSSED
        self.isBold: bool = False


def _offsetPlane(offset: float, targetComponent: adsk.fusion.Component, name: str) -> adsk.fusion.ConstructionPlane:
    planeInput: adsk.fusion.ConstructionPlaneInput = targetComponent.constructionPlanes.createInput()
    planeInput.setByOffset(targetComponent.xYConstructionPlane, adsk.core.ValueInput.createByReal(offset))
    plane = targetComponent.constructionPlanes.add(planeInput)
    plane.name = name
    plane.isLightBulbOn = False
    return plane


def _extrude(profiles: list, distance: float, isUp: bool, targetComponent: adsk.fusion.Component, name: str) -> adsk.fusion.ExtrudeFeature:
    extrudeFeatures = targetComponent.features.extrudeFeatures
    extrudeInput = extrudeFeatures.createInput(commonUtils.objectCollectionFromList(profiles), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extrudeInput.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(distance)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection if isUp else adsk.fusion.ExtentDirections.NegativeExtentDirection,
    )
    extrude = extrudeFeatures.add(extrudeInput)
    extrude.name = name
    return extrude


def _roundedSlab(width: Dim, height: float, inset: float, bottom: float, thickness: float, targetComponent: adsk.fusion.Component, name: str) -> adsk.fusion.BRepBody:
    """Plate of the insert outline set in by `inset` all around, from `bottom` up by `thickness`, corners rounded"""
    plane = _offsetPlane(bottom, targetComponent, f'{name} plane')
    sketch: adsk.fusion.Sketch = targetComponent.sketches.add(plane)
    sketch.name = f'{name} sketch'
    insetDim = Dim.length(inset)
    sketchUtils.createRectangle(
        width - insetDim * 2 if inset > 0 else width,
        height - inset * 2,
        adsk.core.Point3D.create(inset, inset, 0),
        sketch,
        insetDim if inset > 0 else None,
        insetDim if inset > 0 else None,
    )
    extrude = _extrude([sketch.profiles.item(0)], thickness, True, targetComponent, name)
    body = extrude.bodies.item(0)
    body.name = name
    verticalEdges = [
        edge for edge in body.edges
        if abs(edge.boundingBox.maxPoint.z - edge.boundingBox.minPoint.z - thickness) < const.DEFAULT_FILTER_TOLERANCE
    ]
    filletUtils.createFillet(verticalEdges, const.CULLENECT_CORNER_RADIUS, False, targetComponent, name=f'{name} corners')
    return body


def _fixSketch(sketch: adsk.fusion.Sketch):
    """Fixes everything drawn in the sketch where it is, imported and exploded curves have no constraints of their own.
    Deferred, a text has hundreds of points and the sketch would be solved again for each of them"""
    with sketchUtils.deferSketchCompute(sketch):
        for curve in list(sketch.sketchCurves):
            curve.isFixed = True
        origin = sketch.originPoint
        for point in list(sketch.sketchPoints):
            if point != origin:
                point.isFixed = True


def _textProfiles(sketch: adsk.fusion.Sketch, layout: cullenectLabelLayout.LabelLayout, lines: list[str], isBold: bool, timer: commonUtils.StepTimer) -> list:
    """The text lines at the left, each shrunk to fit in front of the symbol, exploded into curves and fixed: live
    sketch text never counts as fully constrained, see the spec"""
    available = layout.textMaxX - layout.textMinX
    for (text, lineHeight, center) in zip(lines, layout.lineHeights, layout.lineCenters):
        measured = _measureText(sketch, text, lineHeight, isBold)
        textHeight = cullenectLabelLayout.fittedLineHeight(lineHeight, measured[0] if measured is not None else 0, available)
        # the box is taller than the letters, the middle alignment puts the capitals in its middle
        sketchText = _addText(
            sketch,
            text,
            textHeight,
            adsk.core.Point3D.create(layout.textMinX, center - lineHeight * 1.5, 0),
            adsk.core.Point3D.create(layout.textMaxX, center + lineHeight * 1.5, 0),
            isBold,
            False,
        )
        timer.step(f'text line {len(text)} characters')
        sketchText.explode()
        timer.step('text exploded')
    _fixSketch(sketch)
    timer.step('text fixed')
    profiles = _iconProfiles(sketch)
    timer.step(f'{len(profiles)} text profiles')
    return profiles


def _iconProfilesPlaced(sketch: adsk.fusion.Sketch, iconPath: str, layout: cullenectLabelLayout.LabelLayout, iconSize: tuple[float, float], timer: commonUtils.StepTimer) -> list:
    (iconWidth, iconHeight) = iconSize
    _importIcon(sketch, iconPath, layout.iconMaxX - iconWidth, layout.iconCenterY - iconHeight / 2, iconHeight)
    timer.step('icon imported')
    _fixSketch(sketch)
    timer.step('icon fixed')
    profiles = _iconProfiles(sketch)
    timer.step(f'{len(profiles)} icon profiles')
    return profiles


def createCullenectLabel(
    input: CullenectLabelInput,
    targetComponent: adsk.fusion.Component,
    *,
    name: str,
) -> tuple[adsk.fusion.BRepBody, list[adsk.fusion.BRepBody]]:
    """The insert with its bottom left corner at the origin, and the text and symbol as bodies of their own so they can
    be printed in another colour: on top of the insert when embossed, set into it when debossed or flush. Debossed keeps
    the filling but hides it, flush shows it. The outline follows the width dim, the symbol is moved along with it.
    Returns the insert and the text and symbol bodies, one per letter or symbol part, none without text and symbol"""
    timer = commonUtils.StepTimer(name)
    width = input.width
    height = input.height
    thickness = const.CULLENECT_LABEL_THICKNESS
    latchBottom = const.CULLENECT_LATCH_BOTTOM
    latchTop = const.CULLENECT_LATCH_BOTTOM + const.CULLENECT_LATCH_HEIGHT

    lines = [line for line in input.lines if len(line.strip()) > 0]
    size = cullenectLabelLayout.iconSize(input.iconPath, width.value, height, input.isScrew) if input.iconPath is not None else None
    layout = cullenectLabelLayout.labelLayout(width.value, height, size, input.isScrew, len(lines))
    problem = cullenectLabelLayout.layoutProblem(layout)
    if problem is not None:
        raise ValueError(problem)

    base = _roundedSlab(width, height, 0, 0, latchBottom, targetComponent, f'{name} bottom')
    latch = _roundedSlab(width, height, const.CULLENECT_LATCH_INSET, latchBottom, latchTop - latchBottom, targetComponent, f'{name} latch')
    top = _roundedSlab(width, height, 0, latchTop, thickness - latchTop, targetComponent, f'{name} top')
    combineUtils.joinBodies(base, commonUtils.objectCollectionFromList([latch, top]), targetComponent, name=f'{name} join')
    base.name = name
    timer.step('insert')

    isEmbossed = input.surface == SURFACE_EMBOSSED
    plane = _offsetPlane(thickness, targetComponent, f'{name} text plane')
    depth = const.CULLENECT_LAYER
    textBodies = []
    iconBodies = []
    if len(lines) > 0:
        textSketch: adsk.fusion.Sketch = targetComponent.sketches.add(plane)
        textSketch.name = f'{name} text sketch'
        profiles = _textProfiles(textSketch, layout, lines, input.isBold, timer)
        if len(profiles) > 0:
            textBodies = list(_extrude(profiles, depth, isEmbossed, targetComponent, f'{name} text').bodies)
            timer.step('text extruded')
    if size is not None:
        iconSketch: adsk.fusion.Sketch = targetComponent.sketches.add(plane)
        iconSketch.name = f'{name} icon sketch'
        profiles = _iconProfilesPlaced(iconSketch, input.iconPath, layout, size, timer)
        if len(profiles) > 0:
            iconBodies = list(_extrude(profiles, depth, isEmbossed, targetComponent, f'{name} icon').bodies)
            # the symbol stays at the right edge when the width parameter changes
            shiftX = width - Dim.length(width.value)
            if shiftX.isExpression:
                moveInput = targetComponent.features.moveFeatures.createInput2(commonUtils.objectCollectionFromList(iconBodies))
                moveInput.defineAsTranslateXYZ(valueInput(shiftX), valueInput(Dim.length(0)), valueInput(Dim.length(0)), True)
                targetComponent.features.moveFeatures.add(moveInput).name = f'{name} icon placement'
            timer.step('icon extruded and placed')

    parts = textBodies + iconBodies
    if len(parts) == 0:
        commonUtils.debugLog(f'{name}: empty insert {width.value * 10:.2f} x {height * 10:.2f} mm')
        return (base, [])
    # Fusion keeps letters and symbol that don't touch as bodies of their own, a join doesn't merge them
    for (index, body) in enumerate(textBodies):
        body.name = f'{name} text {index + 1}'
    for (index, body) in enumerate(iconBodies):
        body.name = f'{name} symbol {index + 1}'
    if not isEmbossed:
        combineUtils.cutBody(base, commonUtils.objectCollectionFromList(parts), targetComponent, True, name=f'{name} text cut')
        if input.surface == SURFACE_DEBOSSED:
            for part in parts:
                part.isLightBulbOn = False
        timer.step('text cut')
    timer.total()
    commonUtils.debugLog(f'{name}: insert {width.value * 10:.2f} x {height * 10:.2f} mm, {input.surface.lower()}, {len(lines)} lines, icon {input.iconPath}')
    return (base, parts)
