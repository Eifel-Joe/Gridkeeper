import adsk.core, adsk.fusion

from . import const, commonUtils, combineUtils, filletUtils, sketchUtils, cullenectLabelLayout, cullenectCatalog, textStyles
from .labelGenerator import _measureText, _iconProfiles, _importIcon, _applyStyle, holdTextHeight
from .dim import Dim, valueInput, lengthInput

# Insert for the Cullenect label system, after cullenect_base_v2 and cullenect_label_generate in Cullenect.scad by
# CullenJWebb (MIT), https://github.com/CullenJWebb/Cullenect-Labels: a 1.2 mm plate with rounded corners whose middle
# layer is set in all around as the latch, text at the left and a symbol at the right, two layers high (p130)

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
        # one text parameter per line, drives that line so it can be edited later like the bin labels
        self.textParameters: list[adsk.fusion.UserParameter] = []
        self.iconPath: str | None = None
        self.isScrew: bool = False
        self.surface: str = SURFACE_EMBOSSED
        # one of textStyles.STYLES, Heavy (Arial Black) prints with a 0.4 mm nozzle (p130)
        self.textStyle: str = textStyles.DEFAULT_INSERT_STYLE


def _offsetPlane(offset: float, targetComponent: adsk.fusion.Component, name: str) -> adsk.fusion.ConstructionPlane:
    planeInput: adsk.fusion.ConstructionPlaneInput = targetComponent.constructionPlanes.createInput()
    planeInput.setByOffset(targetComponent.xYConstructionPlane, lengthInput(offset))
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


def _cutExtrude(profiles: list, distance: float, targetBody: adsk.fusion.BRepBody, targetComponent: adsk.fusion.Component, name: str) -> adsk.fusion.ExtrudeFeature:
    """Cuts the profiles down into the target body only"""
    extrudeFeatures = targetComponent.features.extrudeFeatures
    extrudeInput = extrudeFeatures.createInput(commonUtils.objectCollectionFromList(profiles), adsk.fusion.FeatureOperations.CutFeatureOperation)
    extrudeInput.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(distance)),
        adsk.fusion.ExtentDirections.NegativeExtentDirection,
    )
    extrudeInput.participantBodies = [targetBody]
    extrude = extrudeFeatures.add(extrudeInput)
    extrude.name = name
    return extrude


def _roundedSlab(width: Dim, height: float, inset: float, bottom: float, thickness: float, origin: tuple[float, float], targetComponent: adsk.fusion.Component, name: str) -> adsk.fusion.BRepBody:
    """Plate of the insert outline set in by `inset` all around, from `bottom` up by `thickness`, corners rounded, the
    outline's bottom left corner at `origin`"""
    plane = _offsetPlane(bottom, targetComponent, f'{name} plane')
    sketch: adsk.fusion.Sketch = targetComponent.sketches.add(plane)
    sketch.name = f'{name} sketch'
    insetDim = Dim.length(inset)
    (originX, originY) = origin
    isAtOrigin = inset == 0 and originX == 0 and originY == 0
    sketchUtils.createRectangle(
        width - insetDim * 2 if inset > 0 else width,
        height - inset * 2,
        adsk.core.Point3D.create(originX + inset, originY + inset, 0),
        sketch,
        None if isAtOrigin else Dim.length(originX + inset),
        None if isAtOrigin else Dim.length(originY + inset),
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
    """Fixes everything drawn in the sketch where it is, imported curves and the baseline of a text have no constraints of
    their own. Deferred, an imported symbol has hundreds of points and the sketch would be solved again for each"""
    with sketchUtils.deferSketchCompute(sketch):
        for curve in list(sketch.sketchCurves):
            # a text's baseline was fixed before its text went on it and is left as it is, see _texts
            if not curve.isFixed:
                curve.isFixed = True
        origin = sketch.originPoint
        for point in list(sketch.sketchPoints):
            if point != origin:
                point.isFixed = True


def _addLineText(sketch: adsk.fusion.Sketch, text: str, height: float, baseline: adsk.fusion.SketchLine, style: str) -> adsk.fusion.SketchText:
    """Text standing on the baseline from its start, on one line however long it gets, see _texts"""
    textInput = sketch.sketchTexts.createInput2(text, height)
    textInput.setAsAlongPath(baseline, True, adsk.core.HorizontalAlignments.LeftHorizontalAlignment, 0)
    _applyStyle(textInput, style)
    sketchText = sketch.sketchTexts.add(textInput)
    holdTextHeight(sketchText, height)
    return sketchText


def _texts(sketch: adsk.fusion.Sketch, layout: cullenectLabelLayout.LabelLayout, lines: list[str], textParameters: list, style: str, withTwins: bool, timer: commonUtils.StepTimer) -> tuple[list, list]:
    """The text lines at the left, each shrunk to fit in front of the symbol, as live text driven by its text parameter
    so it can be edited later, and with twins a second text on top of each, driven by the same parameter. Each line
    stands on a fixed baseline; Fusion may not report a sketch with live text as fully constrained, the one exception allowed
    on 14.11.2026 (p50, see the spec). Exploding the text into fixed curves kept it from changing, that was round 4.
    The twins are there for a second extrusion: Fusion refuses to extrude the same text twice in one run ("invalid
    input argument"), and cutting with the bodies of the first instead loses letters a later text adds.
    Returns the texts and their twins, no twins without"""
    # 1 mm more before a symbol or the right edge, so a width made a little smaller later keeps them apart (p52, p233)
    available = cullenectLabelLayout.textFitWidth(layout)
    texts = []
    twins = []
    for (index, (text, lineHeight, center)) in enumerate(zip(lines, layout.lineHeights, layout.lineCenters)):
        # measured in its own font: Arial Black runs ~20 % wider than Arial and is fitted by that
        measured = _measureText(sketch, text, lineHeight, style)
        textHeight = cullenectLabelLayout.fittedLineHeight(lineHeight, measured[0] if measured is not None else 0, available)
        # a long text shrinks to fit, the command hints at it when it gets too thin to print (p130)
        textStyles.noteText(text, style, textHeight)
        # Each line stands on a line of its own instead of in a box (p84, p70): Fusion breaks text in a box where it
        # takes it for longer than the box, by the advance of the letters, wider than their outlines that were
        # measured. The "Welle 6mm" label, fitted to exactly 34 mm, came out as two lines hanging off the insert, and a
        # text made longer later broke the same way. Text along a line never breaks, a longer text runs on to the
        # right, towards the symbol. Tried in Fusion 14.11.2026: one band of letters up to 170 mm long, the extrusion
        # takes the letters a longer text adds. Its baseline goes under the middle by half the capitals' height, as
        # the middle alignment of the box did. Rejected: a box wider to the right, it would reach over the symbol
        start = adsk.core.Point3D.create(layout.textMinX, center - textHeight / 2, 0)
        end = adsk.core.Point3D.create(layout.textMaxX, center - textHeight / 2, 0)
        baseline = sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
        baseline.isConstruction = True
        # fixed before the text goes on it: fixing a path that carries text leaves the text invalid for an extrusion
        # ("invalid input argument", tried in Fusion 14.11.2026), see _fixSketch
        baseline.isFixed = True
        lineTexts = [_addLineText(sketch, text, textHeight, baseline, style) for _ in range(2 if withTwins else 1)]
        if index < len(textParameters) and textParameters[index] is not None:
            for sketchText in lineTexts:
                sketchText.textParameter.expression = textParameters[index].name
        texts.append(lineTexts[0])
        twins += lineTexts[1:]
        timer.step(f'text line {len(text)} characters')
    _fixSketch(sketch)
    timer.step('text baselines fixed')
    return (texts, twins)


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
    origin: tuple[float, float] = (0, 0),
    markingComponent: adsk.fusion.Component | None = None,
    baseOccurrence: adsk.fusion.Occurrence | None = None,
    markingOccurrence: adsk.fusion.Occurrence | None = None,
) -> tuple[adsk.fusion.BRepBody, list[adsk.fusion.BRepBody]]:
    """The insert with its bottom left corner at `origin`, and the text and symbol as bodies of their own so they can
    be printed in another colour: on top of the insert when embossed, set into it when debossed or flush. Debossed keeps
    the filling but hides it, flush shows it. The outline follows the width dim, the symbol is moved along with it.
    The text and symbol are built in the marking component, the Text component of the insert (round 13, p90), the
    insert's own one without. Built there rather than moved there: letters a later text adds come from the same
    extrusion and land in Text too, a move would leave them behind. Cuts into the insert from there take the bodies as
    seen from the root through the occurrences, Fusion refused them otherwise (15.11.2026), see assembly.inContext.
    Returns the insert and the text and symbol bodies, one per letter or symbol part, none without text and symbol"""
    timer = commonUtils.StepTimer(name)
    markingComponent = markingComponent or targetComponent
    width = input.width
    height = input.height
    thickness = const.CULLENECT_LABEL_THICKNESS
    latchBottom = const.CULLENECT_LATCH_BOTTOM
    latchTop = const.CULLENECT_LATCH_BOTTOM + const.CULLENECT_LATCH_HEIGHT

    lines = [line for line in input.lines if len(line.strip()) > 0]
    # debossed, the symbol keeps off the rim over the latch (round 17, p140)
    rim = cullenectLabelLayout.DEBOSS_RIM if input.surface == SURFACE_DEBOSSED else 0
    size = cullenectLabelLayout.iconSize(input.iconPath, width.value, height, input.isScrew, rim) if input.iconPath is not None else None
    layout = cullenectLabelLayout.labelLayout(width.value, height, size, input.isScrew, len(lines), input.textStyle, rim)
    problem = cullenectLabelLayout.layoutProblem(layout)
    if problem is not None:
        raise ValueError(problem)
    # drawn where the insert goes rather than moved there afterwards: a move takes the letter bodies there are, and
    # letters a later text adds would stay behind at the origin
    layout = cullenectLabelLayout.movedLayout(layout, *origin)

    base = _roundedSlab(width, height, 0, 0, latchBottom, origin, targetComponent, f'{name} bottom')
    latch = _roundedSlab(width, height, const.CULLENECT_LATCH_INSET, latchBottom, latchTop - latchBottom, origin, targetComponent, f'{name} latch')
    top = _roundedSlab(width, height, 0, latchTop, thickness - latchTop, origin, targetComponent, f'{name} top')
    combineUtils.joinBodies(base, commonUtils.objectCollectionFromList([latch, top]), targetComponent, name=f'{name} join')
    base.name = name
    timer.step('insert')

    isEmbossed = input.surface == SURFACE_EMBOSSED
    plane = _offsetPlane(thickness, markingComponent, f'{name} text plane')
    # the insert as seen from the marking component's features, see the docstring
    baseInContext = base.createForAssemblyContext(baseOccurrence) if baseOccurrence is not None else base
    depth = const.CULLENECT_MARKING_DEPTH
    textBodies = []
    iconBodies = []
    if len(lines) > 0:
        textSketch: adsk.fusion.Sketch = markingComponent.sketches.add(plane)
        textSketch.name = f'{name} text sketch'
        (texts, twins) = _texts(textSketch, layout, lines, input.textParameters, input.textStyle, not isEmbossed, timer)
        if len(texts) > 0:
            if not isEmbossed:
                # cut by the twin texts, not by the bodies of the filling: a combine takes the letter bodies there
                # are, a later text with more letters would lose them as tools
                _cutExtrude(twins, depth, baseInContext, markingComponent, f'{name} text cut')
            textBodies = list(_extrude(texts, depth, isEmbossed, markingComponent, f'{name} text').bodies)
            timer.step('text extruded')
    if size is not None:
        iconSketch: adsk.fusion.Sketch = markingComponent.sketches.add(plane)
        iconSketch.name = f'{name} icon sketch'
        profiles = _iconProfilesPlaced(iconSketch, input.iconPath, layout, size, timer)
        if len(profiles) > 0:
            iconBodies = list(_extrude(profiles, depth, isEmbossed, markingComponent, f'{name} icon').bodies)
            # the symbol stays at the right edge when the width parameter changes
            shiftX = width - Dim.length(width.value)
            if shiftX.isExpression:
                moveInput = markingComponent.features.moveFeatures.createInput2(commonUtils.objectCollectionFromList(iconBodies))
                moveInput.defineAsTranslateXYZ(valueInput(shiftX), valueInput(Dim.length(0)), valueInput(Dim.length(0)), True)
                markingComponent.features.moveFeatures.add(moveInput).name = f'{name} icon placement'
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
        if len(iconBodies) > 0:
            # the symbol is fixed, its bodies stay the same
            iconTools = [body.createForAssemblyContext(markingOccurrence) for body in iconBodies] if markingOccurrence is not None else iconBodies
            combineUtils.cutBody(baseInContext, commonUtils.objectCollectionFromList(iconTools), targetComponent, True, name=f'{name} symbol cut')
        if input.surface == SURFACE_DEBOSSED:
            for part in parts:
                part.isLightBulbOn = False
        timer.step('text cut')
    timer.total()
    commonUtils.debugLog(f'{name}: insert {width.value * 10:.2f} x {height * 10:.2f} mm, {input.surface.lower()}, {len(lines)} lines, icon {input.iconPath}')
    return (base, parts)
