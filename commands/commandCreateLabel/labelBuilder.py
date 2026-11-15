import os
import adsk.core, adsk.fusion

from ...lib import tagUtils
from ...lib import placementUtils
from ...lib import assembly
from ...lib.gridfinityUtils import cullenectLabelGenerator, cullenectLabelLayout
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
    return cullenectLabelLayout.insertProblem(width, height, iconPath, isScrew, isSymbolMissing, len(labelLines(state)), state.offsetX, state.offsetY)

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
    joint origin of no pocket or one too small: nothing is built (Joerg 15.11.2026)"""
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
) -> list[adsk.fusion.BRepBody]:
    """
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

    plan = designIntent.structurePlan(des.designIntent, mayChangeDocument)
    # the root is active afterwards, also after a failed build, a part design switched for it goes back then, see
    # assembly.buildWithStructure
    return assembly.buildWithStructure(des, plan, lambda: _buildLabel(des, state, settings, root, name, width, height, plan, pocket))

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
) -> list[adsk.fusion.BRepBody]:
    # the container comes before the insert's timeline group, see assembly.partPlace
    place = assembly.partPlace(des, plan, tagUtils.KIND_LABELS, None)
    originalTimelineCount = des.timeline.count
    if place.isComponent:
        occurrence = assembly.addOccurrence(des, place.parent, name, isMovable=True)
        occurrence.activate()
        labelComponent: adsk.fusion.Component = occurrence.component
    else:
        occurrence = None
        labelComponent: adsk.fusion.Component = des.rootComponent

    # pick the spot before generating, so none of this insert's geometry can count as an obstacle
    # beside bins and baseplates too, not into the first bin at the origin (p100)
    placement = placementUtils.findPlacement(
        des,
        [tagUtils.TAG_LABEL, tagUtils.TAG_BIN, tagUtils.TAG_BASEPLATE],
        LABEL_NAME_PREFIX,
        (0, 0, width, height),
        state.baseWidth,
        PLACEMENT_CELL_LENGTH,
    )

    prefix = parameterUtils.nextFreePrefix(des, LABEL_PARAMETER_BASE_NAME, LABEL_PARAMETERS)
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
        )
        baseWidthName = baseWidthParameter.name
        labelParameters.append(['Base width unit', baseWidthName])
    widthParameter = des.userParameters.add(
        parameterUtils.parameterName(prefix, LABEL_WIDTH_PARAMETER),
        adsk.core.ValueInput.createByString(cullenectLabelLayout.widthExpression(
            state.widthUnits if state.useUnits else None,
            None if state.useUnits else state.freeWidth,
            baseWidthName,
            state.offsetX,
        )),
        'mm',
        f'{name} width',
    )
    labelParameters.append(['Insert width', widthParameter.name])
    # each line drives its text, so it can be edited later like the bin labels
    lines = labelLines(state)
    textParameters = []
    for (index, line) in enumerate(lines):
        textParameter = parameterUtils.addTextParameter(
            des,
            parameterUtils.parameterName(prefix, LABEL_TEXT_PARAMETERS[index]),
            line,
            f'{name} text line {index + 1}',
        )
        textParameters.append(textParameter)
        labelParameters.append([f'Text line {index + 1}', textParameter.name])

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
    appearanceUtils.colorBodies(marking, state.textColor)

    # mark generated geometry so it can be told apart from the rest of the design
    for body in bodies:
        tagUtils.tagBody(body, tagUtils.TAG_LABEL, settings, labelParameters)

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
        joint.name = f'{name} in pocket'

    if des.designType == adsk.fusion.DesignTypes.ParametricDesignType:
        group = des.timeline.timelineGroups.add(originalTimelineCount, des.timeline.count - 1)
        group.name = name
    return bodies
