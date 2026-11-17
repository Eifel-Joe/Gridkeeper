import os
import adsk.core, adsk.fusion

from ...lib import tagUtils
from ...lib import placementUtils
from ...lib import assembly
from ...lib import configJson
from ...lib import rebuildUtils
from ...lib.gridfinityUtils import cullenectLabelGenerator, cullenectLabelLayout, labelConfig
from ...lib.gridfinityUtils import commonUtils, designIntent, labelColors, appearanceUtils
from ...lib.gridfinityUtils import parameterUtils
from ...lib.gridfinityUtils import const
from ...lib.gridfinityUtils import cullenect
from ...lib.gridfinityUtils.baseGenerator import createPointJointOrigins
from ...lib.gridfinityUtils.dim import Dim
from ...lib.ui.unsupportedDesignTypeException import UnsupportedDesignTypeException
from .inputState import InputState

# Builds Cullenect inserts from an InputState, without the dialog, so the same settings always build the same insert.
# Cullenect labels by CullenJWebb (MIT), https://github.com/CullenJWebb/Cullenect-Labels

LOG_PREFIX = 'Gridfinity label'

ICONS_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'lib', 'gridfinityUtils', 'cullenectIcons',
)

# User parameter names are stored in user documents, keep these literal
LABEL_PARAMETER_BASE_NAME = 'gfLabel'
# the base unit of the insert, its own like a bin's, see binBuilder.BIN_PARAMETERS
LABEL_BASE_WIDTH_PARAMETER = 'baseWidth'
LABEL_WIDTH_PARAMETER = 'width'
LABEL_TEXT_PARAMETERS = ['text1', 'text2']
LABEL_PARAMETERS = [LABEL_BASE_WIDTH_PARAMETER, LABEL_WIDTH_PARAMETER] + LABEL_TEXT_PARAMETERS

# inserts are drawn at their spot and have no placement move, rebuildUtils.findTarget looks for one of this name and
# finds none (round 18)
LABEL_PLACEMENT_FEATURE = 'Label placement'

# name the inserts start with, so ones without a tag still count when placing new ones
LABEL_NAME_PREFIX = 'Gridfinity label'
NO_HARDWARE = 'none'

# grid the inserts are placed on so they don't pile up, a cell holds a 1U insert
PLACEMENT_CELL_LENGTH = 1.5

def labelSize(state: InputState) -> tuple[float, float]:
    return cullenectLabelLayout.labelSize(
        state.widthUnits if state.useUnits else None,
        None if state.useUnits else state.freeWidth,
        state.baseWidth,
        state.offsetX,
        state.offsetY,
    )

def labelLines(state: InputState) -> list[str]:
    return [line for line in (state.line1, state.line2) if len(line.strip()) > 0]

def labelSymbol(state: InputState) -> tuple[str | None, bool]:
    return cullenectLabelLayout.symbolChoice(
        ICONS_FOLDER,
        state.showScrew,
        (state.head, state.shaft, state.threads, state.driver, state.flange, state.security),
        state.hardware,
    )

def labelProblem(state: InputState) -> str | None:
    """Why the insert can't be built with these settings, none if it can"""
    if not labelColors.isColor(state.textColor):
        return labelColors.colorProblem(labelColors.CUSTOM_CHOICE, state.textColor)
    if state.useUnits and state.baseWidth < const.BASE_UNIT_MIN:
        return f'The base width unit is at least {const.BASE_UNIT_MIN * 10:g} mm'
    (width, height) = labelSize(state)
    (iconPath, isScrew) = labelSymbol(state)
    isSymbolMissing = iconPath is None and (state.showScrew or state.hardware != NO_HARDWARE)
    return cullenectLabelLayout.insertProblem(width, height, iconPath, isScrew, isSymbolMissing, len(labelLines(state)), state.offsetX, state.offsetY, state.textStyle, state.surface == cullenectLabelGenerator.SURFACE_DEBOSSED)

# the joint origin at the middle of the insert's bottom, see cullenect.pocketJointOriginName for the pockets' (p160)
INSERT_JOINT_ORIGIN = 'Insert joint origin'

def pocketSizeMm(pocket: adsk.fusion.JointOrigin | None) -> tuple[float, float] | None:
    """The size of the Cullenect pocket the joint origin is on, from its tag, none for any other joint origin"""
    if pocket is None or not pocket.isValid:
        return None
    native = pocket.nativeObject or pocket
    attribute = native.attributes.itemByName(tagUtils.TAG_GROUP, tagUtils.TAG_POCKET)
    return cullenect.readPocketTagValue(attribute.value) if attribute is not None else None

def pocketProblem(state: InputState, pocket: adsk.fusion.JointOrigin | None) -> str | None:
    """Why the insert can't go into the chosen pocket, none without one or when it fits. A pocket that's gone, a
    joint origin of no pocket or one too small: nothing is built (Nutzer 15.11.2026)"""
    if pocket is None:
        return None
    size = pocketSizeMm(pocket)
    (width, height) = labelSize(state)
    if size is None or not cullenectLabelLayout.insertFitsPocket(width * 10, height * 10, *size):
        return cullenectLabelLayout.POCKET_MISFIT
    return None

def labelName(state: InputState) -> str:
    return cullenectLabelLayout.labelTitle(
        state.widthUnits if state.useUnits else None,
        None if state.useUnits else state.freeWidth,
        labelLines(state),
    )

def buildLabel(
    des: adsk.fusion.Design,
    state: InputState,
    settings: list[dict],
    mayChangeDocument: bool = True,
    pocket: adsk.fusion.JointOrigin | None = None,
    corner: tuple[float, float] | None = None,
    parameterPrefix: str | None = None,
    occurrenceTransform: adsk.core.Matrix3D | None = None,
    oldPlace: assembly.OldPlace | None = None,
) -> list[adsk.fusion.BRepBody]:
    """
    A rebuild in place (round 18, p150, see rebuildLabel) gives the corner the insert is drawn from, the prefix of the
    parameters it keeps, the transform of its component and where the old one is; a new insert finds its own spot.
    Builds the insert into the design, tagged with the settings to show later, see settingsUtils.snapshotInputs.
    Returns the insert body first, then the text and symbol bodies. The insert is a component of its own in the
    container Label, its text and symbol bodies in a component Text inside it (round 13, p90), a part design is switched
    to hybrid for it unless the document may not change (a preview), see designIntent.structurePlan.
    A joint origin sits at the middle of its bottom. With a pocket, a joint origin of a Cullenect pocket of a bin, the
    insert is jointed into it (round 13, p100, p160), else it goes beside every bin, baseplate and insert there is
    """
    if des.designType == 0:
        raise UnsupportedDesignTypeException('Timeline must be enabled for the generator to work, projects with disabled design history currently are not supported')
    problem = labelProblem(state) or pocketProblem(state, pocket)
    if problem is not None:
        raise ValueError(problem)
    (width, height) = labelSize(state)
    root = adsk.fusion.Component.cast(des.rootComponent)
    name = labelName(state)

    plan = designIntent.structurePlan(des.designIntent, mayChangeDocument, assembly.rebuildKind(oldPlace))
    # the root is active afterwards, also after a failed build, a part design switched for it goes back then, see
    # assembly.buildWithStructure
    return assembly.buildWithStructure(des, plan, lambda: _buildLabel(des, state, settings, root, name, width, height, plan, pocket, corner, parameterPrefix, occurrenceTransform, oldPlace))

def _buildLabel(
    des: adsk.fusion.Design,
    state: InputState,
    settings: list[dict],
    root: adsk.fusion.Component,
    name: str,
    width: float,
    height: float,
    plan: designIntent.StructurePlan,
    pocket: adsk.fusion.JointOrigin | None = None,
    corner: tuple[float, float] | None = None,
    parameterPrefix: str | None = None,
    occurrenceTransform: adsk.core.Matrix3D | None = None,
    oldPlace: assembly.OldPlace | None = None,
) -> list[adsk.fusion.BRepBody]:
    # the container comes before the insert's timeline group, see assembly.partPlace
    place = assembly.partPlace(des, plan, tagUtils.KIND_LABELS, oldPlace)
    # the marker is right after the old insert's group when rebuilding in place, at the end otherwise (as binBuilder)
    originalTimelinePosition = des.timeline.markerPosition
    if place.isComponent:
        occurrence = assembly.addOccurrence(des, place.parent, name, occurrenceTransform, isMovable=True)
        occurrence.activate()
        labelComponent: adsk.fusion.Component = occurrence.component
    else:
        occurrence = None
        labelComponent: adsk.fusion.Component = des.rootComponent

    # pick the spot before generating, so none of this insert's geometry can count as an obstacle
    # beside bins and baseplates too, not into the first bin at the origin (p100). A rebuilt one stays where it was
    placement = corner if corner is not None else placementUtils.findPlacement(
        des,
        [tagUtils.TAG_LABEL, tagUtils.TAG_BIN, tagUtils.TAG_BASEPLATE],
        LABEL_NAME_PREFIX,
        (0, 0, width, height),
        state.baseWidth,
        PLACEMENT_CELL_LENGTH,
    )

    # a rebuilt insert keeps its parameters, the old ones are still there and are taken over, see rebuildUtils.rebuild
    reuse = parameterPrefix is not None
    prefix = parameterPrefix or parameterUtils.nextFreePrefix(des, LABEL_PARAMETER_BASE_NAME, LABEL_PARAMETERS)
    labelParameters = []
    baseWidthName = None
    if state.useUnits:
        # the insert's own base width, like the bins have theirs since upstream v2.4.0.0, changing it changes no
        # other insert or bin
        baseWidthParameter = parameterUtils.addLengthParameter(
            des,
            parameterUtils.parameterName(prefix, LABEL_BASE_WIDTH_PARAMETER),
            state.baseWidth,
            f'{name} base width unit',
            reuse,
        )
        baseWidthName = baseWidthParameter.name
        labelParameters.append(['Base width unit', baseWidthName])
    widthName = parameterUtils.parameterName(prefix, LABEL_WIDTH_PARAMETER)
    widthExpression = cullenectLabelLayout.widthExpression(
        state.widthUnits if state.useUnits else None,
        None if state.useUnits else state.freeWidth,
        baseWidthName,
        state.offsetX,
    )
    reusedWidth = parameterUtils.reusedParameter(des, widthName, lambda parameter: parameter.expression == widthExpression, widthExpression) if reuse else None
    widthParameter = reusedWidth or des.userParameters.add(widthName, adsk.core.ValueInput.createByString(widthExpression), 'mm', f'{name} width')
    labelParameters.append(['Insert width', widthParameter.name])
    # each line drives its text, so it can be edited later like the bin labels
    lines = labelLines(state)
    textParameters = []
    # labelled by the line it was typed in, a rebuild puts it back there, see labelConfig.textLines
    for (index, (line, label)) in enumerate(labelConfig.textLines(state.line1, state.line2)):
        textParameter = parameterUtils.addTextParameter(
            des,
            parameterUtils.parameterName(prefix, LABEL_TEXT_PARAMETERS[index]),
            line,
            f'{name} text line {index + 1}',
            reuse,
        )
        textParameters.append(textParameter)
        labelParameters.append([label, textParameter.name])

    (iconPath, isScrew) = labelSymbol(state)
    labelInput = cullenectLabelGenerator.CullenectLabelInput()
    labelInput.width = Dim.parameter(widthParameter)
    labelInput.height = height
    labelInput.lines = lines
    labelInput.textParameters = textParameters
    labelInput.iconPath = iconPath
    labelInput.isScrew = isScrew
    labelInput.surface = state.surface
    labelInput.textStyle = state.textStyle
    # drawn at its spot, not moved there: a move would leave behind letters a later text adds
    # its text and symbol go into a Text component of the insert (round 13, p90), none without them or as root bodies
    textOccurrence = assembly.addOccurrence(des, occurrence, assembly.TEXT_COMPONENT_NAME) if occurrence is not None and (len(lines) > 0 or iconPath is not None) else None
    (base, marking) = cullenectLabelGenerator.createCullenectLabel(
        labelInput,
        labelComponent,
        name=name,
        origin=placement,
        markingComponent=textOccurrence.component if textOccurrence is not None else None,
        baseOccurrence=occurrence if textOccurrence is not None else None,
        markingOccurrence=textOccurrence,
    )
    bodies = [base] + marking
    # on the Text occurrence too, the letters a longer text adds show it (p120)
    appearanceUtils.colorPart(marking, textOccurrence, state.textColor)

    # mark generated geometry so it can be told apart from the rest of the design
    for body in bodies:
        # with the config, so the insert can be rebuilt, cloned and its config saved like a bin (round 18, p150)
        tagUtils.tagBody(body, tagUtils.TAG_LABEL, settings, labelParameters, configJson.stateToJson(configJson.GENERATOR_LABEL, state), prefix)

    # at the middle of the bottom, following the width parameter, X along the width like the pockets' (p160)
    (insertJointOrigin,) = createPointJointOrigins(
        [(INSERT_JOINT_ORIGIN, Dim.length(placement[0]) + labelInput.width / 2, Dim.length(placement[1] + height / 2), Dim.length(0))],
        labelComponent,
        name=INSERT_JOINT_ORIGIN,
    )
    if pocket is not None and occurrence is not None:
        # the insert moves into the pocket, the bin stays where it is. A preview in a part design builds bodies into
        # the root, which a joint can't move, it shows the insert beside the bins then
        jointInput = root.joints.createInput(assembly.inContext(insertJointOrigin, occurrence), pocket)
        jointInput.setAsRigidJointMotion()
        joint = root.joints.add(jointInput)
        joint.name = f'{name}{labelConfig.POCKET_JOINT_SUFFIX}'
        # Fusion turned off the pocket's joint origin for the joint, it stays shown (as the box label's holder)
        assembly.keepShown(pocket)

    if des.designType == adsk.fusion.DesignTypes.ParametricDesignType:
        group = des.timeline.timelineGroups.add(originalTimelinePosition, des.timeline.markerPosition - 1)
        group.name = name
    return bodies

def insertComponent(des: adsk.fusion.Design, body: adsk.fusion.BRepBody) -> adsk.fusion.Component:
    """The component of the insert a body is of: its own, or for a letter or symbol in the insert's Text component the
    one above it. Text and symbol are tagged too, a right click on the letters starts the rebuild from them (review)"""
    component = rebuildUtils.nativeBody(body).parentComponent
    if component.name.startswith(assembly.TEXT_COMPONENT_NAME):
        occurrences = des.rootComponent.allOccurrencesByComponent(component)
        parent = occurrences.item(0).assemblyContext if occurrences.count > 0 else None
        if parent is not None:
            return parent.component
    return component

def insertPocket(des: adsk.fusion.Design, body: adsk.fusion.BRepBody) -> adsk.fusion.JointOrigin | None:
    """The pocket joint origin the insert the body is of was jointed into by the label command, as seen from the root,
    none when it wasn't: the other side of its joint "... in pocket" on the Insert joint origin, when that is a pocket
    (round 18, p150). A joint of the user's own isn't the command's, it stays a later feature (review)"""
    component = insertComponent(des, body)
    for joint in des.rootComponent.allJoints:
        if not labelConfig.isPocketJointName(joint.name):
            continue
        sides = [
            (adsk.fusion.JointOrigin.cast(joint.geometryOrOriginOne), joint.occurrenceOne),
            (adsk.fusion.JointOrigin.cast(joint.geometryOrOriginTwo), joint.occurrenceTwo),
        ]
        for ((side, _), (other, otherOccurrence)) in (sides, sides[::-1]):
            if side is not None and other is not None and side.name == INSERT_JOINT_ORIGIN                     and (side.nativeObject or side).parentComponent == component and pocketSizeMm(other) is not None:
                return _inRoot(des, other, otherOccurrence)
    return None

def _inRoot(des: adsk.fusion.Design, jointOrigin: adsk.fusion.JointOrigin, occurrence: adsk.fusion.Occurrence | None = None) -> adsk.fusion.JointOrigin:
    """The joint origin as seen from the root, through the occurrence of its component. The sides of a joint came
    without one (assemblyContext None), a selection input refused them: "3 : invalid argument selection", the label
    dialog stopped half built (round 20, p220, r20_pocket_probe: the proxy through the bin's occurrence selects)"""
    if jointOrigin.assemblyContext is not None:
        return jointOrigin
    native = jointOrigin.nativeObject or jointOrigin
    # the joint's own occurrence of that side: a bin copied in Fusion has a second occurrence of its component, the
    # first one would put the insert into the other bin (review round 20)
    if occurrence is not None and occurrence.component == native.parentComponent and (occurrence.assemblyContext is not None or occurrence.nativeObject is None):
        return native.createForAssemblyContext(occurrence)
    occurrences = des.rootComponent.allOccurrencesByComponent(native.parentComponent)
    # a bin's component is in the design once, see assembly.addOccurrence; one in the root has no occurrence
    return native.createForAssemblyContext(occurrences.item(0)) if occurrences.count > 0 else native

def _insertBody(target: rebuildUtils.RebuildTarget) -> adsk.fusion.BRepBody:
    """The insert itself among the tagged bodies of its group, not a letter or the symbol: the order the design finds
    them in isn't given (review). The largest when none is outside a Text component"""
    own = [body for body in target.bodies if not body.parentComponent.name.startswith(assembly.TEXT_COMPONENT_NAME)]
    def area(body: adsk.fusion.BRepBody) -> float:
        box = body.boundingBox
        return (box.maxPoint.x - box.minPoint.x) * (box.maxPoint.y - box.minPoint.y)
    return max(own or target.bodies, key=area)

def _isAfter(target: rebuildUtils.RebuildTarget, pocket: adsk.fusion.JointOrigin | None) -> bool:
    """Whether the pocket's bin comes after the insert in the timeline: the rebuild builds right after the old group,
    where that pocket isn't there yet (review)"""
    occurrence = pocket.assemblyContext if pocket is not None else None
    if occurrence is None:
        return False
    item = (occurrence.nativeObject or occurrence).timelineObject
    return item is not None and any(later == item for later in target.laterItems)

def rebuildLabel(
    des: adsk.fusion.Design,
    body: adsk.fusion.BRepBody,
    state: InputState,
    settings: list[dict],
    isPreview: bool,
    pocket: adsk.fusion.JointOrigin | None = None,
) -> tuple[list[adsk.fusion.BRepBody], list[str]]:
    """
    Builds the insert in place of the one the body is of, keeping the features after it, see rebuildUtils.rebuild
    (upstream v2.4 by Le0Michine, as binBuilder.rebuildBin). Always built anew, not by its parameters: a text set by
    its parameter would come uncolored and unfitted (Hauptsitzung 15.11.2026). It is drawn from the old insert's bottom
    left corner in a new component where the old one was. Its joint into a pocket goes with the old group, the pocket
    given joints the new one into it again. Returns the bodies and what of the later features needs a look
    """
    problem = labelProblem(state) or pocketProblem(state, pocket)
    if problem is not None:
        raise ValueError(problem)
    # inserts aren't moved into place but drawn there, no move of this name: the placement is (0, 0)
    target = rebuildUtils.findTarget(des, body, tagUtils.TAG_LABEL, LABEL_PLACEMENT_FEATURE)
    if _isAfter(target, pocket):
        raise ValueError("The bin of this pocket comes after the insert in the timeline, the insert can't be rebuilt into it in place")
    old = _insertBody(target)
    # the pocket the old insert leaves, Fusion turned it off for the old joint, see assembly.keepShown
    oldPocket = insertPocket(des, body)
    # read where it is built, right after its group: a later move of the body would be taken twice, once in the corner
    # and once when the move gets the new body (review)
    rebuildUtils.rollAfterGroup(target)
    try:
        box = old.boundingBox
        corner = labelConfig.rebuildCorner((box.minPoint.x, box.minPoint.y, box.maxPoint.x, box.maxPoint.y))
    finally:
        des.timeline.moveToEnd()
    prefix = rebuildUtils.bodyId(old, LABEL_PARAMETER_BASE_NAME)
    if not isPreview:
        newConfig = configJson.stateToJson(configJson.GENERATOR_LABEL, state)
        commonUtils.fileLog(f'{LOG_PREFIX} rebuilding {target.group.name} at {corner}, {rebuildUtils.configChanges(configJson.GENERATOR_LABEL, old, newConfig)}')

    def build(placement, parameterPrefix, transform, oldPlace):
        # a jointed insert is placed by its joint, a free one keeps the transform of its old component
        bodies = buildLabel(des, state, settings, not isPreview, pocket, corner, parameterPrefix, None if pocket is not None else transform, oldPlace)
        # only the insert itself takes the place of the old one, its text and symbol are bodies of their own
        return bodies[:1]
    result = rebuildUtils.rebuild(des, target, prefix, LABEL_PARAMETER_BASE_NAME, isPreview, build, 'insert')
    if not isPreview:
        assembly.keepShown(oldPocket)
    return result
