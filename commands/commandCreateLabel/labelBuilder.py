import os
import adsk.core, adsk.fusion

from ...lib import tagUtils
from ...lib import placementUtils
from ...lib.gridfinityUtils import cullenectLabelGenerator, cullenectLabelLayout
from ...lib.gridfinityUtils import parameterUtils
from ...lib.gridfinityUtils import sharedParameters
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
LABEL_WIDTH_PARAMETER = 'width'
LABEL_TEXT_PARAMETERS = ['text1', 'text2']
LABEL_PARAMETERS = [sharedParameters.BASE_WIDTH_FALLBACK_PARAMETER, LABEL_WIDTH_PARAMETER] + LABEL_TEXT_PARAMETERS

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
    if state.useUnits and state.baseWidth < sharedParameters.BASE_UNIT_MIN:
        return f'The base width unit is at least {sharedParameters.BASE_UNIT_MIN * 10:g} mm'
    (width, height) = labelSize(state)
    (iconPath, isScrew) = labelSymbol(state)
    isSymbolMissing = iconPath is None and (state.showScrew or state.hardware != NO_HARDWARE)
    return cullenectLabelLayout.insertProblem(width, height, iconPath, isScrew, isSymbolMissing, len(labelLines(state)), state.offsetX, state.offsetY)

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
) -> list[adsk.fusion.BRepBody]:
    """
    Builds the insert into the design, tagged with the settings to show later, see settingsUtils.snapshotInputs.
    Returns the insert body first, then the text and symbol bodies
    """
    if des.designType == 0:
        raise UnsupportedDesignTypeException('Timeline must be enabled for the generator to work, projects with disabled design history currently are not supported')
    problem = labelProblem(state)
    if problem is not None:
        raise ValueError(problem)
    (width, height) = labelSize(state)
    root = adsk.fusion.Component.cast(des.rootComponent)
    name = labelName(state)

    originalTimelineCount = des.timeline.count
    if des.designIntent == adsk.fusion.DesignIntentTypes.HybridDesignIntentType:
        # create new component, only allowed in hybrid intent type
        occurrence = adsk.fusion.Occurrences.cast(root.occurrences).addNewComponent(adsk.core.Matrix3D.create())
        occurrence.component.name = name
        occurrence.activate()
        labelComponent: adsk.fusion.Component = occurrence.component
    else:
        labelComponent: adsk.fusion.Component = des.rootComponent

    # pick the spot before generating, so none of this insert's geometry can count as an obstacle
    placement = placementUtils.findPlacement(
        des,
        tagUtils.TAG_LABEL,
        LABEL_NAME_PREFIX,
        (0, 0, width, height),
        state.baseWidth,
        PLACEMENT_CELL_LENGTH,
    )

    prefix = parameterUtils.nextFreePrefix(des, LABEL_PARAMETER_BASE_NAME, LABEL_PARAMETERS)
    labelParameters = []
    baseWidthName = None
    if state.useUnits:
        # the shared base width, like the bins and baseplates of the design, so an insert follows a change of the grid
        baseWidthParameter = sharedParameters.findOrCreateSharedLengthParameter(
            des,
            tagUtils.TAG_BASE_WIDTH_PARAMETER,
            sharedParameters.BASE_WIDTH_PARAMETER,
            'base width unit',
            sharedParameters.BASE_UNIT_MIN,
            state.baseWidth,
            parameterUtils.parameterName(prefix, sharedParameters.BASE_WIDTH_FALLBACK_PARAMETER),
            'label',
            LOG_PREFIX,
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
    labelInput.isBold = state.isBold
    # drawn at its spot, not moved there: a move would leave behind letters a later text adds
    (base, marking) = cullenectLabelGenerator.createCullenectLabel(labelInput, labelComponent, name=name, origin=placement)
    bodies = [base] + marking

    # mark generated geometry so it can be told apart from the rest of the design
    for body in bodies:
        tagUtils.tagBody(body, tagUtils.TAG_LABEL, settings, labelParameters)

    if des.designType == adsk.fusion.DesignTypes.ParametricDesignType:
        group = des.timeline.timelineGroups.add(originalTimelineCount, des.timeline.count - 1)
        group.name = name
    return bodies
