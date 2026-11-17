import os
import adsk.core, adsk.fusion

from ...lib import tagUtils
from ...lib import placementUtils
from ...lib import assembly
from ...lib import configJson
from ...lib import rebuildUtils
from ...lib.gridfinityUtils import predBoxLabel, predBoxLabelLayout, predBoxSeats, boxLabelConfig
from ...lib.gridfinityUtils import designIntent, labelColors, appearanceUtils, parameterUtils, commonUtils
from ...lib.ui.unsupportedDesignTypeException import UnsupportedDesignTypeException
from .inputState import InputState

# Builds the label of a box after Pred's parametric Gridfinity Storage Box v1.1
# (https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric, CC BY-NC, by Pred) from an
# InputState, round 29 (p262, dev-notes/r29/boxlabel-plan.md): Gridkeeper text and Cullenect symbols
# (https://github.com/CullenJWebb/Cullenect-Labels, MIT, by CullenJWebb) on Pred's plate. A command of its own, not part
# of the box command (Jörg 17.11.2026: "weil man es so besser auch mal austauschen könnte").

ICONS_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'lib', 'gridfinityUtils', 'cullenectIcons',
)

# user parameter names are stored in user documents, keep these literal
PARAMETER_BASE_NAME = 'gfBoxLabel'
TEXT_PARAMETER_NAMES = boxLabelConfig.TEXT_PARAMETER_NAMES
HOLDER_JOINT_SUFFIX = boxLabelConfig.HOLDER_JOINT_SUFFIX
# the move of the bodies built into the root (a preview in a part design) to their spot, a rebuild finds the spot by it
PLACEMENT_FEATURE = 'Box label placement'
LOG_PREFIX = 'Gridkeeper box label'
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
    return predBoxLabelLayout.cellsOfBoxWidth(max(body.boundingBox.maxPoint.x - body.boundingBox.minPoint.x for body in bodies))


def buildBoxLabel(
    des: adsk.fusion.Design,
    state: InputState,
    settings: list[dict],
    mayChangeDocument: bool = True,
    box: adsk.fusion.JointOrigin | None = None,
    parameterPrefix: str | None = None,
    occurrenceTransform: adsk.core.Matrix3D | None = None,
    rootSpot: tuple[float, float] | None = None,
    oldPlace: assembly.OldPlace | None = None,
) -> tuple[list[adsk.fusion.BRepBody], predBoxLabelLayout.BoxLabelLayout]:
    """
    The label into a component of its own in the boxes' container, its text and symbols in a Text component in it, as
    the inserts'. With the label joint origin of a box it is jointed into that box's holder, without it lies beside the
    boxes, bins, baseplates and inserts there are. A part design is switched to hybrid unless the document may not change
    (a preview), see designIntent.structurePlan. The plate is tagged with the settings to show later, see
    settingsUtils.snapshotInputs, and the config to rebuild and clone it. A rebuild in place (rebuildBoxLabel) gives the
    prefix of the parameters it keeps, the transform of the old component or the spot of bodies in the root, and where
    the old one is. Returns the plate first, then text and symbols, and the layout
    """
    if des.designType == 0:
        raise UnsupportedDesignTypeException('Timeline must be enabled for the generator to work, projects with disabled design history currently are not supported')
    problem = labelProblem(state)
    if problem is not None:
        raise ValueError(problem)
    if box is not None and not isBoxLabelJointOrigin(box):
        raise ValueError(f'Pick the {predBoxSeats.LABEL_JOINT_ORIGIN} of a box')
    plan = designIntent.structurePlan(des.designIntent, mayChangeDocument, assembly.rebuildKind(oldPlace))
    return assembly.buildWithStructure(des, plan, lambda: _buildBoxLabel(des, state, settings, plan, box, parameterPrefix, occurrenceTransform, rootSpot, oldPlace))


def _buildBoxLabel(
    des: adsk.fusion.Design,
    state: InputState,
    settings: list[dict],
    plan: designIntent.StructurePlan,
    box: adsk.fusion.JointOrigin | None,
    parameterPrefix: str | None,
    occurrenceTransform: adsk.core.Matrix3D | None,
    rootSpot: tuple[float, float] | None,
    oldPlace: assembly.OldPlace | None,
) -> tuple[list[adsk.fusion.BRepBody], predBoxLabelLayout.BoxLabelLayout]:
    root = des.rootComponent
    name = labelName(state)
    width = predBoxLabelLayout.plateWidth(state.cells)
    height = predBoxLabelLayout.PLATE_HEIGHT
    place = assembly.partPlace(des, plan, tagUtils.KIND_BOXES, oldPlace)
    originalTimelinePosition = des.timeline.markerPosition

    # a free spot before anything of the label is there; jointed to a box, the joint places it. Bodies in the root (a
    # preview in a part design) can't be jointed, they go to a free spot too (review). A rebuilt free label stays where
    # the old one was: its component's transform, or the spot its bodies were moved to
    transform = occurrenceTransform if occurrenceTransform is not None else adsk.core.Matrix3D.create()
    spot = None
    if not place.isComponent and rootSpot is not None:
        spot = rootSpot
    elif occurrenceTransform is None and (box is None or not place.isComponent):
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

    # a rebuilt label keeps its parameters, the old ones are still there and are taken over, see rebuildUtils.rebuild
    reuse = parameterPrefix is not None
    prefix = parameterPrefix or parameterUtils.nextFreePrefix(des, PARAMETER_BASE_NAME, TEXT_PARAMETER_NAMES, tagUtils.usedBodyIds(des, tagUtils.TAG_BOX_LABEL))
    texts = [state.bigText, state.line1, state.line2]
    parameters = [
        parameterUtils.addTextParameter(des, parameterUtils.parameterName(prefix, field), text.strip(), f'{name} {field}', reuse)
        if len(text.strip()) > 0 else None
        for (field, text) in zip(TEXT_PARAMETER_NAMES, texts)
    ]
    # labelled for the settings page and the rebuild, which takes their values back, see boxLabelConfig.PARAMETER_FIELDS
    labelParameters = boxLabelConfig.parameterLabels([parameter.name if parameter is not None else None for parameter in parameters])
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
    # the export takes the plate as a part with its marking, Flush lies on its text (p380, round r29-export); the
    # settings menu, rebuild and clone take the whole config (1.1.0, Jörg: "Die Box-Labels haben die Punkte [...] nicht")
    tagUtils.tagBody(plate, tagUtils.TAG_BOX_LABEL, settings, labelParameters, configJson.stateToJson(configJson.GENERATOR_BOX_LABEL, state), prefix)
    if occurrence is None and spot is not None:
        # no occurrence to carry the spot: the bodies themselves move there
        placementUtils.moveBodies([plate] + marking, spot[0], spot[1], component, name=PLACEMENT_FEATURE)

    if box is not None and occurrence is not None:
        # the label moves into the holder, the box stays where it is
        jointInput = root.joints.createInput(assembly.inContext(jointOrigin, occurrence), box)
        jointInput.setAsRigidJointMotion()
        joint = root.joints.add(jointInput)
        joint.name = f'{name}{HOLDER_JOINT_SUFFIX}'
        # Fusion turned off the box's Label joint origin for the joint, it stays shown
        assembly.keepShown(box)

    if des.designType == adsk.fusion.DesignTypes.ParametricDesignType:
        group = des.timeline.timelineGroups.add(originalTimelinePosition, des.timeline.markerPosition - 1)
        group.name = name
    return ([plate] + marking, layout)


def labelHolder(des: adsk.fusion.Design, body: adsk.fusion.BRepBody) -> adsk.fusion.JointOrigin | None:
    """
    The label joint origin of the box the label the body is of was jointed into by the box label command, as seen from
    the root, none when it wasn't: the other side of its joint "... in holder" on the label's own joint origin. A joint
    of the user's own isn't the command's, it stays a later feature (as labelBuilder.insertPocket)
    """
    component = rebuildUtils.nativeBody(body).parentComponent
    for joint in des.rootComponent.allJoints:
        if not boxLabelConfig.isHolderJointName(joint.name):
            continue
        sides = [
            (adsk.fusion.JointOrigin.cast(joint.geometryOrOriginOne), joint.occurrenceOne),
            (adsk.fusion.JointOrigin.cast(joint.geometryOrOriginTwo), joint.occurrenceTwo),
        ]
        for ((side, _), (other, otherOccurrence)) in (sides, sides[::-1]):
            if side is None or other is None or (side.nativeObject or side).parentComponent != component:
                continue
            holder = _inRoot(des, other, otherOccurrence)
            if isBoxLabelJointOrigin(holder):
                return holder
    return None


def _inRoot(des: adsk.fusion.Design, jointOrigin: adsk.fusion.JointOrigin, occurrence: adsk.fusion.Occurrence | None) -> adsk.fusion.JointOrigin:
    """The joint origin as seen from the root, through the occurrence of its component, as labelBuilder._inRoot: the
    sides of a joint may come without one, a selection input refuses those (round 20, p220)"""
    if jointOrigin.assemblyContext is not None:
        return jointOrigin
    native = jointOrigin.nativeObject or jointOrigin
    if occurrence is not None and occurrence.component == native.parentComponent:
        return native.createForAssemblyContext(occurrence)
    occurrences = des.rootComponent.allOccurrencesByComponent(native.parentComponent)
    return native.createForAssemblyContext(occurrences.item(0)) if occurrences.count > 0 else native


def _isAfter(target: rebuildUtils.RebuildTarget, box: adsk.fusion.JointOrigin | None) -> bool:
    """Whether the box comes after the label in the timeline: the rebuild builds right after the old group, where that
    box isn't there yet (as labelBuilder._isAfter). The box's component sits in its set, either may be the later one"""
    occurrence = box.assemblyContext if box is not None else None
    while occurrence is not None:
        item = (occurrence.nativeObject or occurrence).timelineObject
        if item is not None and any(later == item for later in target.laterItems):
            return True
        occurrence = occurrence.assemblyContext
    return False


def rebuildBoxLabel(
    des: adsk.fusion.Design,
    body: adsk.fusion.BRepBody,
    state: InputState,
    settings: list[dict],
    isPreview: bool,
    box: adsk.fusion.JointOrigin | None = None,
) -> tuple[list[adsk.fusion.BRepBody], list[str]]:
    """
    Builds the label in place of the one the body is of, keeping the features after it, see rebuildUtils.rebuild (as
    labelBuilder.rebuildLabel). Its joint into a holder goes with the old group, the box given joints the new one into
    it again; without one it stays where the old one was. Joints of the user's own on its joint origin move over to the
    new one's. Returns the bodies and what of the later features needs a look
    """
    problem = labelProblem(state)
    if problem is not None:
        raise ValueError(problem)
    if box is not None and not isBoxLabelJointOrigin(box):
        raise ValueError(f'Pick the {predBoxSeats.LABEL_JOINT_ORIGIN} of a box')
    target = rebuildUtils.findTarget(des, body, tagUtils.TAG_BOX_LABEL, PLACEMENT_FEATURE)
    if _isAfter(target, box):
        raise ValueError("The box comes after the label in the timeline, the label can't be rebuilt into its holder in place")
    prefix = rebuildUtils.bodyId(target.bodies[0], PARAMETER_BASE_NAME)
    # the holder the old label leaves, Fusion turned it off for the old joint, see assembly.keepShown
    oldHolder = labelHolder(des, body)
    if not isPreview:
        newConfig = configJson.stateToJson(configJson.GENERATOR_BOX_LABEL, state)
        commonUtils.fileLog(f'{LOG_PREFIX} rebuilding {target.group.name}, {rebuildUtils.configChanges(configJson.GENERATOR_BOX_LABEL, target.bodies[0], newConfig)}')

    def build(placement, parameterPrefix, transform, oldPlace):
        # a jointed label is placed by its joint, a free one keeps its component's transform or the move of its bodies
        rootSpot = placement if target.occurrence is None and box is None else None
        (bodies, _) = buildBoxLabel(des, state, settings, not isPreview, box, parameterPrefix, None if box is not None else transform, rootSpot, oldPlace)
        # only the plate takes the place of the old one, its text and symbols are bodies of their own
        return bodies[:1]
    result = rebuildUtils.rebuild(des, target, prefix, PARAMETER_BASE_NAME, isPreview, build, 'box label', jointsByName=True)
    if not isPreview:
        # with the timeline at its end again: the one left and the one the new label went into (review)
        assembly.keepShown(oldHolder)
        assembly.keepShown(box)
    return result
