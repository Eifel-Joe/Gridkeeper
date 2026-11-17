import os
import adsk.core, adsk.fusion

from ...lib import tagUtils
from ...lib import placementUtils
from ...lib import assembly
from ...lib.gridfinityUtils import predBoxLabel, predBoxLabelLayout, predBoxSeats
from ...lib.gridfinityUtils import designIntent, labelColors, appearanceUtils, parameterUtils
from ...lib.ui.unsupportedDesignTypeException import UnsupportedDesignTypeException
from .inputState import InputState

# Builds the label of a box after Pred's parametric Gridfinity Storage Box v1.1
# (https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric, CC BY-NC, by Pred) from an
# InputState, round 29 (p262, dev-notes/r29/boxlabel-plan.md): Gridkeeper text and Cullenect symbols
# (https://github.com/CullenJWebb/Cullenect-Labels, MIT, by CullenJWebb) on Pred's plate. A command of its own, not part
# of the box command (Nutzer 17.11.2026: "weil man es so besser auch mal austauschen könnte").

ICONS_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'lib', 'gridfinityUtils', 'cullenectIcons',
)

# user parameter names are stored in user documents, keep these literal
PARAMETER_BASE_NAME = 'gfBoxLabel'
TEXT_PARAMETERS = ['bigText', 'text1', 'text2']
HOLDER_JOINT_SUFFIX = ' in holder'
# grid free spots are looked for on, without a box
PLACEMENT_CELL = 4.2


def symbolPaths(state: InputState) -> list[str]:
    """The svgs of the chosen symbols in their order, empty places left out"""
    paths = dict(predBoxLabelLayout.symbolChoices(ICONS_FOLDER))
    return [paths[name] for name in state.symbols if paths.get(name) is not None]


def boxLabelInput(state: InputState) -> predBoxLabel.BoxLabelInput:
    labelInput = predBoxLabel.BoxLabelInput()
    labelInput.cells = state.cells
    labelInput.bigText = state.bigText
    labelInput.lines = [state.line1, state.line2]
    labelInput.symbolPaths = symbolPaths(state)
    labelInput.surface = state.surface
    labelInput.textStyle = state.textStyle
    return labelInput


def labelProblem(state: InputState) -> str | None:
    """Why the label can't be built with these settings, none if it can"""
    if not labelColors.isColor(state.textColor):
        return labelColors.colorProblem(labelColors.CUSTOM_CHOICE, state.textColor)
    return predBoxLabelLayout.sizeProblem(state.cells)


def labelLayout(state: InputState) -> predBoxLabelLayout.BoxLabelLayout | None:
    return predBoxLabel.boxLabelLayout(boxLabelInput(state)) if labelProblem(state) is None else None


def labelName(state: InputState) -> str:
    return predBoxLabelLayout.labelTitle(state.cells, state.bigText, [state.line1, state.line2])


def isBoxLabelJointOrigin(jointOrigin: adsk.fusion.JointOrigin | None) -> bool:
    """The joint origin a box command built at the label holder, predBoxSeats.LABEL_JOINT_ORIGIN"""
    return jointOrigin is not None and jointOrigin.isValid and jointOrigin.name == predBoxSeats.LABEL_JOINT_ORIGIN \
        and boxCells(jointOrigin) is not None


def boxCells(jointOrigin: adsk.fusion.JointOrigin) -> int | None:
    """The width in grid cells of the box the label joint origin is of, from its outer width (cells x 42 mm + 20 mm):
    the widest body of the joint origin's component, the box itself. Read from the geometry, so a box whose width
    parameter was changed since gives its width now"""
    native = jointOrigin.nativeObject or jointOrigin
    bodies = list(native.parentComponent.bRepBodies)
    if len(bodies) == 0:
        return None
    width = max(body.boundingBox.maxPoint.x - body.boundingBox.minPoint.x for body in bodies)
    cells = round((width * 10 - 20) / 42)
    return cells if cells >= predBoxLabelLayout.MIN_CELLS else None


def buildBoxLabel(
    des: adsk.fusion.Design,
    state: InputState,
    mayChangeDocument: bool = True,
    box: adsk.fusion.JointOrigin | None = None,
) -> tuple[list[adsk.fusion.BRepBody], predBoxLabelLayout.BoxLabelLayout]:
    """
    The label into a component of its own in the boxes' container, its text and symbols in a Text component in it, as
    the inserts'. With the label joint origin of a box it is jointed into that box's holder, without it lies beside the
    boxes, bins, baseplates and inserts there are. A part design is switched to hybrid unless the document may not change
    (a preview), see designIntent.structurePlan. Returns the plate first, then text and symbols, and the layout
    """
    if des.designType == 0:
        raise UnsupportedDesignTypeException('Timeline must be enabled for the generator to work, projects with disabled design history currently are not supported')
    problem = labelProblem(state)
    if problem is not None:
        raise ValueError(problem)
    if box is not None and not isBoxLabelJointOrigin(box):
        raise ValueError(f'Pick the {predBoxSeats.LABEL_JOINT_ORIGIN} of a box')
    plan = designIntent.structurePlan(des.designIntent, mayChangeDocument, assembly.rebuildKind(None))
    return assembly.buildWithStructure(des, plan, lambda: _buildBoxLabel(des, state, plan, box))


def _buildBoxLabel(
    des: adsk.fusion.Design,
    state: InputState,
    plan: designIntent.StructurePlan,
    box: adsk.fusion.JointOrigin | None,
) -> tuple[list[adsk.fusion.BRepBody], predBoxLabelLayout.BoxLabelLayout]:
    root = des.rootComponent
    name = labelName(state)
    width = predBoxLabelLayout.plateWidth(state.cells)
    height = predBoxLabelLayout.PLATE_HEIGHT
    place = assembly.partPlace(des, plan, tagUtils.KIND_BOXES, None)
    originalTimelinePosition = des.timeline.markerPosition

    # a free spot before anything of the label is there; jointed to a box, the joint places it. Bodies in the root (a
    # preview in a part design) can't be jointed, they go to a free spot too (review)
    transform = adsk.core.Matrix3D.create()
    spot = None
    if box is None or not place.isComponent:
        (x, y) = placementUtils.findPlacement(
            des,
            [tagUtils.TAG_BOX, tagUtils.TAG_LABEL, tagUtils.TAG_BIN, tagUtils.TAG_BASEPLATE],
            # the label's bodies aren't tagged, found by name: 'Box label', 'Box label text 1', ... (review)
            predBoxLabel.PLATE_BODY_NAME,
            (0, 0, width, height),
            PLACEMENT_CELL,
            PLACEMENT_CELL,
        )
        spot = (x + width / 2, y + height / 2)
        transform.translation = adsk.core.Vector3D.create(spot[0], spot[1], 0)
    if place.isComponent:
        occurrence = assembly.addOccurrence(des, place.parent, name, transform, isMovable=True)
        occurrence.activate()
        component: adsk.fusion.Component = occurrence.component
    else:
        occurrence = None
        component = root

    prefix = parameterUtils.nextFreePrefix(des, PARAMETER_BASE_NAME, TEXT_PARAMETERS)
    texts = [state.bigText, state.line1, state.line2]
    parameters = [
        parameterUtils.addTextParameter(des, parameterUtils.parameterName(prefix, field), text.strip(), f'{name} {field}')
        if len(text.strip()) > 0 else None
        for (field, text) in zip(TEXT_PARAMETERS, texts)
    ]
    labelInput = boxLabelInput(state)
    labelInput.bigTextParameter = parameters[0]
    labelInput.lineParameters = parameters[1:]

    hasMarking = any(len(text.strip()) > 0 for text in texts) or len(labelInput.symbolPaths) > 0
    textOccurrence = assembly.addOccurrence(des, occurrence, assembly.TEXT_COMPONENT_NAME) if occurrence is not None and hasMarking else None
    (plate, marking, jointOrigin, layout) = predBoxLabel.createBoxLabel(
        labelInput,
        component,
        name=name,
        markingComponent=textOccurrence.component if textOccurrence is not None else None,
        baseOccurrence=occurrence if textOccurrence is not None else None,
        markingOccurrence=textOccurrence,
    )
    appearanceUtils.colorPart(marking, textOccurrence, state.textColor)
    # the export takes the plate as a part with its marking, Flush lies on its text (p380, round r29-export)
    tagUtils.tagBody(plate, tagUtils.TAG_BOX_LABEL, config={'surface': state.surface})
    if occurrence is None and spot is not None:
        # no occurrence to carry the spot: the bodies themselves move there
        placementUtils.moveBodies([plate] + marking, spot[0], spot[1], component, name=f'{name} placement')

    if box is not None and occurrence is not None:
        # the label moves into the holder, the box stays where it is
        jointInput = root.joints.createInput(assembly.inContext(jointOrigin, occurrence), box)
        jointInput.setAsRigidJointMotion()
        joint = root.joints.add(jointInput)
        joint.name = f'{name}{HOLDER_JOINT_SUFFIX}'

    if des.designType == adsk.fusion.DesignTypes.ParametricDesignType:
        group = des.timeline.timelineGroups.add(originalTimelinePosition, des.timeline.markerPosition - 1)
        group.name = name
    return ([plate] + marking, layout)
