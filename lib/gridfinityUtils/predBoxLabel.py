import adsk.core, adsk.fusion

from . import commonUtils, combineUtils, cullenectLabelLayout, predBoxLabelLayout, textStyles
from .cullenectCatalog import svgSize
from .cullenectLabelGenerator import _offsetPlane, _extrude, _cutExtrude, _texts, _fixSketch
from .labelGenerator import _importIcon, _iconProfiles
from .predBoxLabelLayout import BoxLabelLayout, PLATE_HEIGHT, PLATE_THICKNESS, PLATE_CORNER_RADIUS, PLATE_CHAMFER, MARKING_DEPTH
from .predSketch import WorldSketch
from .predBoxSeats import LABEL_JOINT_ORIGIN

# The label of the storage box after Pred's parametric Gridfinity Storage Box v1.1
# (https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric, CC BY-NC, by Pred), round 29
# (p262, dev-notes/r29/boxlabel-plan.md): Pred's flat plate (Label, Label_M_Screws in Pred's file), Gridkeeper text and
# Cullenect symbols (https://github.com/CullenJWebb/Cullenect-Labels, MIT, by CullenJWebb) on it, raised, debossed or
# flush like on the Cullenect inserts. Built by the box label command, not the box command (decided 17.11.2026: so it
# can be swapped out more easily).
#
# Part frame: the plate lies flat as it is printed, text up (+z), the middle of its back face at the origin; the box
# label joint origin there has Z along +y and X along +x, so jointed to the box's Label joint origin (upright, X along
# X, predBoxSeats.labelSeat) the plate stands in the holder: +y up, the text towards the front (-y of the box).
# Every sketch is fully constrained (requirement of 17.11.2026: all sketches fully
# constrained); the text sketches on fixed baselines like the inserts' (p50, round 6: Fusion reports them constrained).

SURFACE_EMBOSSED = 'Embossed'
SURFACE_DEBOSSED = 'Debossed'
SURFACE_FLUSH = 'Flush'
SURFACES = [SURFACE_EMBOSSED, SURFACE_DEBOSSED, SURFACE_FLUSH]

PLATE_BODY_NAME = predBoxLabelLayout.PLATE_BODY_NAME


class BoxLabelInput():
    def __init__(self):
        self.cells: int = 5
        # the large text at the left, empty for none
        self.bigText: str = ''
        # up to two lines at the right, empty ones are left out
        self.lines: list[str] = []
        # a text parameter for the large text and each line in self.lines, None to leave it plain
        self.bigTextParameter: adsk.fusion.UserParameter | None = None
        self.lineParameters: list[adsk.fusion.UserParameter | None] = []
        # svg paths of the chosen symbols, in their order, up to five
        self.symbolPaths: list[str] = []
        self.surface: str = SURFACE_EMBOSSED
        self.textStyle: str = textStyles.DEFAULT_INSERT_STYLE


def boxLabelLayout(input: BoxLabelInput) -> BoxLabelLayout:
    sizes = [tuple(value / 10 for value in svgSize(path)) for path in input.symbolPaths]
    lines = [line for line in input.lines if len(line.strip()) > 0]
    return predBoxLabelLayout.labelLayout(predBoxLabelLayout.plateWidth(input.cells), len(input.bigText.strip()) > 0, len(lines), sizes)


def _plate(width: float, component: adsk.fusion.Component, name: str) -> adsk.fusion.BRepBody:
    """Pred's plate (Label in Pred's file, r29_walk/Label.json) centred on the origin, from z = 0 up by its thickness:
    Sketch1 a rectangle with corners rounded 3.5 mm, drawn as predSketch's rounded rectangle (createRectangle with its
    corner dimensioned from the origin, four equal fillets, one radius dimension), Chamfer1 0.2 mm all round on front and
    back as tangent chains"""
    plateSketch = WorldSketch(component, component.xYConstructionPlane, f'{name} plate sketch')
    plateSketch.roundedRectangle(-width / 2, -PLATE_HEIGHT / 2, width / 2, PLATE_HEIGHT / 2, 0, PLATE_CORNER_RADIUS)
    sketch = plateSketch.close()
    extrude = _extrude([sketch.profiles.item(0)], PLATE_THICKNESS, True, component, f'{name} plate')
    body = extrude.bodies.item(0)
    body.name = PLATE_BODY_NAME
    # one edge of each face, the tangent chain takes the rest of its outline, as baseGenerator's chamfers
    edges = adsk.core.ObjectCollection.create()
    for faces in (extrude.startFaces, extrude.endFaces):
        edges.add(faces.item(0).edges.item(0))
    chamferInput = component.features.chamferFeatures.createInput2()
    chamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, adsk.core.ValueInput.createByReal(PLATE_CHAMFER), True)
    component.features.chamferFeatures.add(chamferInput).name = f'{name} plate chamfer'
    return body


def _labelJointOrigin(component: adsk.fusion.Component) -> adsk.fusion.JointOrigin:
    """At the origin, the middle of the back face: Z along +y, X along +x, see the frame above. On the origin point
    rather than a sketch point: a dimension of zero would be needed (sketchChain: never a dimension of zero)"""
    geometry = adsk.fusion.JointGeometry.createByPoint(component.originConstructionPoint)
    jointInput = component.jointOrigins.createInput(geometry)
    jointInput.zAxisEntity = component.yConstructionAxis
    jointInput.xAxisEntity = component.xConstructionAxis
    jointOrigin = component.jointOrigins.add(jointInput)
    jointOrigin.name = LABEL_JOINT_ORIGIN
    return jointOrigin


def _textLayout(minX: float, maxX: float, heights: list[float], centers: list[float]) -> cullenectLabelLayout.LabelLayout:
    """A field of the box label in the shape cullenectLabelGenerator._texts fits its lines to"""
    return cullenectLabelLayout.LabelLayout(
        width=maxX - minX, height=PLATE_HEIGHT, textMinX=minX, textMaxX=maxX, iconMaxX=None, iconCenterY=0,
        lineHeights=heights, lineCenters=centers)


def createBoxLabel(
    input: BoxLabelInput,
    component: adsk.fusion.Component,
    *,
    name: str,
    markingComponent: adsk.fusion.Component | None = None,
    baseOccurrence: adsk.fusion.Occurrence | None = None,
    markingOccurrence: adsk.fusion.Occurrence | None = None,
) -> tuple[adsk.fusion.BRepBody, list[adsk.fusion.BRepBody], adsk.fusion.JointOrigin, BoxLabelLayout]:
    """
    The plate in the component and its text and symbols in the marking component (the Text component of the label, as
    the inserts', cullenectLabelGenerator.createCullenectLabel), the label joint origin at the origin. Raised on the
    plate, cut into it when debossed or flush, as the inserts; debossed keeps the filling but hides it.
    Returns the plate, the text and symbol bodies, the joint origin and the layout (how many symbols were left out)
    """
    timer = commonUtils.StepTimer(name)
    markingComponent = markingComponent or component
    layout = boxLabelLayout(input)
    width = layout.width

    plate = _plate(width, component, name)
    timer.step('plate')
    jointOrigin = _labelJointOrigin(component)

    isEmbossed = input.surface == SURFACE_EMBOSSED
    plane = _offsetPlane(PLATE_THICKNESS, markingComponent, f'{name} text plane')
    plateInContext = plate.createForAssemblyContext(baseOccurrence) if baseOccurrence is not None else plate
    textBodies = []
    iconBodies = []

    fields = []
    if layout.bigHeight is not None:
        fields.append(('large text', [input.bigText.strip()], [input.bigTextParameter],
                       _textLayout(layout.bigMinX, layout.bigMaxX, [layout.bigHeight], [layout.bigCenterY])))
    lines = [(line.strip(), parameter) for (line, parameter) in zip(input.lines, list(input.lineParameters) + [None] * len(input.lines)) if len(line.strip()) > 0]
    if len(lines) > 0:
        fields.append(('lines', [line for (line, _) in lines], [parameter for (_, parameter) in lines],
                       _textLayout(layout.textMinX, layout.textMaxX, layout.lineHeights, layout.lineCenters)))
    for (fieldName, texts, parameters, fieldLayout) in fields:
        sketch: adsk.fusion.Sketch = markingComponent.sketches.add(plane)
        sketch.name = f'{name} {fieldName} sketch'
        (fieldTexts, twins) = _texts(sketch, fieldLayout, texts, parameters, input.textStyle, not isEmbossed, timer)
        if len(fieldTexts) == 0:
            continue
        if not isEmbossed:
            # cut by the twin texts, as the inserts: a later longer text keeps its letters as tools
            _cutExtrude(twins, MARKING_DEPTH, plateInContext, markingComponent, f'{name} {fieldName} cut')
        textBodies += list(_extrude(fieldTexts, MARKING_DEPTH, isEmbossed, markingComponent, f'{name} {fieldName}').bodies)
        timer.step(f'{fieldName} extruded')

    for (index, (path, (left, centerY, _symbolWidth, symbolHeight))) in enumerate(zip(input.symbolPaths, layout.symbolBoxes)):
        sketch: adsk.fusion.Sketch = markingComponent.sketches.add(plane)
        sketch.name = f'{name} symbol {index + 1} sketch'
        _importIcon(sketch, path, left, centerY - symbolHeight / 2, symbolHeight)
        _fixSketch(sketch)
        profiles = _iconProfiles(sketch)
        if len(profiles) > 0:
            bodies = list(_extrude(profiles, MARKING_DEPTH, isEmbossed, markingComponent, f'{name} symbol {index + 1}').bodies)
            if not isEmbossed:
                tools = [body.createForAssemblyContext(markingOccurrence) for body in bodies] if markingOccurrence is not None else bodies
                combineUtils.cutBody(plateInContext, commonUtils.objectCollectionFromList(tools), component, True, name=f'{name} symbol {index + 1} cut')
            iconBodies += bodies
        timer.step(f'symbol {index + 1}')

    for (index, body) in enumerate(textBodies):
        body.name = f'{PLATE_BODY_NAME} text {index + 1}'
    for (index, body) in enumerate(iconBodies):
        body.name = f'{PLATE_BODY_NAME} symbol {index + 1}'
    parts = textBodies + iconBodies
    if input.surface == SURFACE_DEBOSSED:
        for part in parts:
            part.isLightBulbOn = False
    timer.total()
    return (plate, parts, jointOrigin, layout)
