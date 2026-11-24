import adsk.core, adsk.fusion

from ...lib import tagUtils
from ...lib import placementUtils
from ...lib import assembly
from ...lib import configJson
from ...lib import rebuildUtils
from ...lib.gridfinityUtils import commonUtils, componentNames, designIntent, parameterUtils
from ...lib.gridfinityUtils import predBoxConfig, predBoxSeats, predBoxInsert
from ...lib.gridfinityUtils.predBox import PredBoxDims
from ...lib.gridfinityUtils.predBoxGenerator import createPredBox, PredBoxOptions
from ...lib.gridfinityUtils.jointOriginLayout import cellJointOriginPoints, createOffsetJointOrigins
from ...lib.gridfinityUtils.dim import Dim
from ...lib.ui.unsupportedDesignTypeException import UnsupportedDesignTypeException
from .inputState import InputState

# Builds the storage box after Pred's parametric Gridfinity Storage Box v1.1 from an InputState, without the dialog.
# Pred: https://www.printables.com/model/543553 (CC BY-NC), rebuilt in code for Gridkeeper (round 27, p260).

LOG_PREFIX = 'Gridfinity box'

# User parameter names are stored in user documents, keep these literal
BOX_PARAMETER_BASE_NAME = 'gfBox'
# boxes are built where they stand, no move of this name, see rebuildUtils.findTarget
BOX_PLACEMENT_FEATURE = 'Box placement'
# name the boxes start with, so ones without a tag still count when placing new ones
BOX_NAME_PREFIX = 'Box '
# the components of a set in the box's own component, the lid is split off the box like in Pred's file
BOX_COMPONENT_NAME = 'Box'
LID_COMPONENT_NAME = 'Lid'
# joint origins (decided 16.11.2026), the seats of the small parts follow in round 28
CELL_JOINT_ORIGIN = 'Cell joint origin'
STACK_BOTTOM_JOINT_ORIGIN = 'Stack bottom joint origin'
STACK_TOP_JOINT_ORIGIN = 'Stack top joint origin'
LID_JOINT_ORIGIN = 'Lid joint origin'
LID_JOINT_NAME = 'Lid on box'
SEAT_JOINT_ORIGINS = 'Seat joint origin'
# placement grid for new boxes, beside bins, baseplates, inserts and other boxes
PLACEMENT_CELL_LENGTH = 4.2


def boxProblem(state: InputState) -> str | None:
    return predBoxConfig.boxProblem(state)


def boxName(state: InputState) -> str:
    return predBoxConfig.boxName(state)


def outerSize(state: InputState) -> tuple[float, float]:
    return (state.gridX * 4.2 + 2.0, state.gridY * 4.2 + 2.0)


def buildBox(
    des: adsk.fusion.Design,
    state: InputState,
    settings: list[dict],
    mayChangeDocument: bool = True,
    parameterPrefix: str | None = None,
    occurrenceTransform: adsk.core.Matrix3D | None = None,
    oldPlace: assembly.OldPlace | None = None,
) -> list[adsk.fusion.BRepBody]:
    """
    Builds box and lid into the design, tagged with the settings to show later, see settingsUtils.snapshotInputs.
    Returns the box body and the lid body. The set is a component of its own in the container Boxes with the
    components Box and Lid, the lid jointed shut on the box; a part design is switched to hybrid for it unless the
    document may not change (a preview), see designIntent.structurePlan. A rebuild in place (rebuildBox) gives the
    prefix of the parameters it keeps, the transform of the old set and where the old one is
    """
    if des.designType == 0:
        raise UnsupportedDesignTypeException('Timeline must be enabled for the generator to work, projects with disabled design history currently are not supported')
    problem = boxProblem(state)
    if problem is not None:
        raise ValueError(problem)
    plan = designIntent.structurePlan(des.designIntent, mayChangeDocument, assembly.rebuildKind(oldPlace))
    return assembly.buildWithStructure(des, plan, lambda: _buildBox(des, state, settings, plan, parameterPrefix, occurrenceTransform, oldPlace, forOk=mayChangeDocument))


def _buildBox(
    des: adsk.fusion.Design,
    state: InputState,
    settings: list[dict],
    plan: designIntent.StructurePlan,
    parameterPrefix: str | None,
    occurrenceTransform: adsk.core.Matrix3D | None,
    oldPlace: assembly.OldPlace | None,
    forOk: bool = True,
) -> list[adsk.fusion.BRepBody]:
    name = boxName(state)
    # the container comes before the box's timeline group, see assembly.partPlace
    place = assembly.partPlace(des, plan, tagUtils.KIND_BOXES, oldPlace)
    originalTimelinePosition = des.timeline.markerPosition
    (width, length) = outerSize(state)
    if place.isComponent and occurrenceTransform is None:
        # a new set goes beside the parts there are, moved there as a whole
        (x, y) = placementUtils.findPlacement(
            des,
            [tagUtils.TAG_BOX, tagUtils.TAG_LABEL, tagUtils.TAG_BIN, tagUtils.TAG_BASEPLATE],
            BOX_NAME_PREFIX,
            (0, 0, width, length),
            PLACEMENT_CELL_LENGTH,
            PLACEMENT_CELL_LENGTH,
        )
        occurrenceTransform = adsk.core.Matrix3D.create()
        occurrenceTransform.translation = adsk.core.Vector3D.create(x, y, 0)
    if place.isComponent:
        setOccurrence = assembly.addOccurrence(des, place.parent, name, occurrenceTransform, isMovable=True)
        setOccurrence.activate()
        setComponent = setOccurrence.component
    else:
        setOccurrence = None
        setComponent = des.rootComponent

    reuse = parameterPrefix is not None
    prefix = parameterPrefix or parameterUtils.nextFreePrefix(des, BOX_PARAMETER_BASE_NAME, predBoxConfig.PARAMETERS, tagUtils.usedBodyIds(des, tagUtils.TAG_BOX))
    parameters = []
    boxParameters = []
    for (field, label, value) in [
        ('baseWidth', 'Width (units)', state.gridX),
        ('baseLength', 'Length (units)', state.gridY),
        ('heightU', 'Height (units)', state.heightU),
    ]:
        parameter = parameterUtils.addUnitlessParameter(des, parameterUtils.parameterName(prefix, field), value, f'{name} {label.lower()}', reuse)
        tagUtils.tagParameterField(parameter, predBoxConfig.PARAMETER_FIELDS[label], prefix)
        parameters.append(parameter)
        boxParameters.append([label, parameter.name])
    dims = PredBoxDims(*[Dim.parameter(parameter) for parameter in parameters])
    # by name: with the lid's top four options of the same kind, a field moved in one of them went unnoticed (review R30)
    options = PredBoxOptions(**predBoxConfig.boxOptions(state)._asdict())
    bodies = createPredBox(setComponent, dims, options)
    base, lid = bodies.base, bodies.lid

    boxComponent = lidComponent = setComponent
    boxOccurrence = lidOccurrence = None
    if setOccurrence is not None:
        # the lid split off the box like in Pred's file, each into its own component (Task 1, r27_spike: stays parametric)
        nativeSet = setOccurrence.nativeObject or setOccurrence
        boxNative = nativeSet.component.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        componentNames.name(boxNative.component, BOX_COMPONENT_NAME)
        lidNative = nativeSet.component.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        componentNames.name(lidNative.component, LID_COMPONENT_NAME)
        # Fusion names a second set's components "Box (1)", the role tells them apart, see rebuildUtils
        boxNative.component.attributes.add(tagUtils.TAG_GROUP, tagUtils.TAG_PART_ROLE, BOX_COMPONENT_NAME)
        lidNative.component.attributes.add(tagUtils.TAG_GROUP, tagUtils.TAG_PART_ROLE, LID_COMPONENT_NAME)
        base = base.moveToComponent(boxNative)
        lid = lid.moveToComponent(lidNative)
        boxComponent, lidComponent = boxNative.component, lidNative.component
        boxOccurrence = assembly.inContext(boxNative, setOccurrence)
        lidOccurrence = assembly.inContext(lidNative, setOccurrence)
        if lidOccurrence.isGroundToParent:
            lidOccurrence.isGroundToParent = False

    config = configJson.stateToJson(configJson.GENERATOR_BOX, state)
    for body in (base, lid):
        # with the names it gave, a rebuild keeps the ones the user changed (round 58, see rebuildUtils.keptName)
        tagUtils.tagBody(rebuildUtils.nativeBody(body), tagUtils.TAG_BOX, settings, boxParameters, config, prefix,
                         name=name, bodyName=rebuildUtils.nativeBody(body).name)

    # joint origins last, they don't follow moves (as binBuilder); without sketches since round 45 (p480, offsets on the
    # origin point, see jointOriginLayout.createOffsetJointOrigins). The floor cells always: the bin dialog
    # joints a new bin into one (round 31, p312), state.hasJointOrigins of older configs is left aside;
    # an older box without them gets them when it is rebuilt, its joints move over by name, see rebuildBox.
    # Only for OK (round 36, p296): the six calls took 20-100 s, 75 s in a preview that is thrown away and that
    # nothing joints to (rebuildUtils.rebuild hands the preview's bodies back as they are); the lid lies shut on the
    # box by its geometry, the joint only holds it there
    if forOk:
        centers = [(column, row, Dim.length(x), Dim.length(y)) for (column, row, x, y) in predBoxConfig.cellCenters(state.gridX, state.gridY)]
        createOffsetJointOrigins(cellJointOriginPoints(centers, CELL_JOINT_ORIGIN, Dim.length(predBoxConfig.CELL_JOINT_Z)), boxComponent, name=CELL_JOINT_ORIGIN)
        (stackBottom,) = createOffsetJointOrigins([(STACK_BOTTOM_JOINT_ORIGIN, dims.midX, dims.midY, dims.bottom)], boxComponent, name=STACK_BOTTOM_JOINT_ORIGIN)
        (stackTop,) = createOffsetJointOrigins([(STACK_TOP_JOINT_ORIGIN, dims.midX, dims.midY, dims.bodyTop)], lidComponent, name=STACK_TOP_JOINT_ORIGIN)
        # the seats of the small parts (round 28): latches, handle and its pins, upright like the others, each part's joint
        # turns it, see predBoxSeats.turnAboutZ; a box of bodies in the root gets no parts, so no seats either (review)
        if boxOccurrence is not None:
            createOffsetJointOrigins(predBoxSeats.seatJointOriginPoints(dims, state.hinge), boxComponent, name=SEAT_JOINT_ORIGINS)
        if boxOccurrence is not None:
            (boxSide,) = createOffsetJointOrigins([(LID_JOINT_ORIGIN, dims.midX, dims.midY, dims.lidCut)], boxComponent, name=LID_JOINT_ORIGIN)
            (lidSide,) = createOffsetJointOrigins([(LID_JOINT_ORIGIN, dims.midX, dims.midY, dims.lidCut)], lidComponent, name=LID_JOINT_ORIGIN)
            # the lid shut on the box, rigid like Pred's closed box; it's part of the set, a rebuild makes it anew (rigid)
            jointInput = des.rootComponent.joints.createInput(assembly.inContext(lidSide, lidOccurrence), assembly.inContext(boxSide, boxOccurrence))
            jointInput.setAsRigidJointMotion()
            joint = des.rootComponent.joints.add(jointInput)
            joint.name = f'{name} {LID_JOINT_NAME}'

    # the small parts after Pred (round 28): latches, handle and pins jointed at their seats, hinges beside the box; a
    # box of bodies in the root (a part design kept as it is) has no components to joint, it stays without them.
    # A preview leaves them out (round 36, p295): inserting them made every preview slow, it shows box and lid,
    # OK builds the whole set
    partBodies = predBoxInsert.insertParts(des, setOccurrence, boxOccurrence, dims, state.hinge, name, assembly.inContext) if boxOccurrence is not None and forOk else []

    if des.designType == adsk.fusion.DesignTypes.ParametricDesignType:
        group = des.timeline.timelineGroups.add(originalTimelinePosition, des.timeline.markerPosition - 1)
        group.name = name
    # the native bodies, as binBuilder: those moveToComponent gives back are seen through the Box and Lid occurrences,
    # the snapshot tests found them neither among the design's bodies nor with their tag (r27_snap 17.11.2026)
    return [rebuildUtils.nativeBody(base), rebuildUtils.nativeBody(lid)] + partBodies


def rebuildBox(
    des: adsk.fusion.Design,
    body: adsk.fusion.BRepBody,
    state: InputState,
    settings: list[dict],
    isPreview: bool,
) -> tuple[list[adsk.fusion.BRepBody], list[str]]:
    """
    Builds the set anew in place of the one the body (box or lid) is of, keeping the features after it, see
    rebuildUtils.rebuild; the new set takes the old one's transform, the joints of the user on its joint origins move
    over to those of the same name. Returns the bodies and what of the later features needs a look
    """
    problem = boxProblem(state)
    if problem is not None:
        raise ValueError(problem)
    target = rebuildUtils.findTarget(des, body, tagUtils.TAG_BOX, BOX_PLACEMENT_FEATURE)
    prefix = rebuildUtils.bodyId(target.bodies[0], BOX_PARAMETER_BASE_NAME)
    if not isPreview:
        newConfig = configJson.stateToJson(configJson.GENERATOR_BOX, state)
        commonUtils.fileLog(f'{LOG_PREFIX} rebuilding {target.group.name}, {rebuildUtils.configChanges(configJson.GENERATOR_BOX, target.bodies[0], newConfig)}')

    def build(placement, parameterPrefix, transform, oldPlace):
        # box and lid only: rebuildUtils.bodyMap pairs the old set's tagged bodies with as many new ones, the small
        # parts (round 28) aren't tagged and come and go with the set's timeline group
        bodies = buildBox(des, state, settings, not isPreview, parameterPrefix, transform, oldPlace)
        return [body for body in bodies if tagUtils.readBodyTag(body) is not None]
    # the names of the old set's parts by role, read before it is gone, a part the user renamed keeps that name
    oldPartNames = _partNames(target.occurrence)
    # the old set hidden by its light bulb in a preview, Fusion won't suppress a set's group (round 39, p481)
    (bodies, notes) = rebuildUtils.rebuild(des, target, prefix, BOX_PARAMETER_BASE_NAME, isPreview, build, 'box', jointsByName=True,
                                           hideByLightBulb=True, namePrefix=BOX_NAME_PREFIX)
    if not isPreview:
        _renameParts(bodies, oldPartNames)
    return (bodies, notes)


def _partNames(setOccurrence: adsk.fusion.Occurrence | None) -> dict[str, str]:
    """The names of a set's parts by their role, box, lid and small parts"""
    names = {}
    for child in (setOccurrence.childOccurrences if setOccurrence is not None else []):
        role = rebuildUtils.partRole(child.component)
        if role:
            names.setdefault(role, child.component.name)
    return names


def _renameParts(bodies: list[adsk.fusion.BRepBody], oldPartNames: dict[str, str]):
    """
    The new set is built while the old one still has its components, Fusion names the new ones "Box (2)", "Lid (2)"
    (r27_cmd 17.11.2026), the small parts "Latch (1)" and so on (review round 28). With the old set gone the names are
    free again, a name another set still holds stays taken. A part the user renamed gets that name, see _partNames
    """
    components = []
    for body in bodies:
        component = rebuildUtils.nativeBody(body).parentComponent
        if component not in components:
            components.append(component)
        # the set holding box and lid, and with them the small parts' components
        occurrences = component.parentDesign.rootComponent.allOccurrencesByComponent(component)
        setOccurrence = occurrences.item(0).assemblyContext if occurrences.count > 0 else None
        for child in (setOccurrence.childOccurrences if setOccurrence is not None else []):
            if child.component not in components:
                components.append(child.component)
    for component in components:
        role = rebuildUtils.partRole(component)
        # the user's name of the old part of that role, else the role without Fusion's counter (round 58)
        name = rebuildUtils.rebuiltPartName(component.name, role, oldPartNames.get(role)) if role else None
        if name is not None:
            try:
                component.name = name
            except RuntimeError as err:
                commonUtils.fileLog(f'{LOG_PREFIX} {component.name} kept its name, {err}')
