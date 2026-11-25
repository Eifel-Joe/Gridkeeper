import adsk.core, adsk.fusion
import copy
import dataclasses
from dataclasses import dataclass

from ...lib import tagUtils
from ...lib import configJson
from ...lib import placementUtils
from ...lib import rebuildUtils
from ...lib import assembly
from ...lib import labelFaces
from ...lib.gridfinityUtils import combineUtils
from ...lib.gridfinityUtils import geometryUtils
from ...lib.gridfinityUtils import faceUtils
from ...lib.gridfinityUtils import shellUtils
from ...lib.gridfinityUtils import commonUtils
from ...lib.gridfinityUtils import const
from ...lib.gridfinityUtils import raisedDividers
from ...lib.gridfinityUtils import parameterUtils
from ...lib.gridfinityUtils import designIntent
from ...lib.gridfinityUtils.dim import Dim, isZero
from ...lib.gridfinityUtils.jointOriginLayout import createOffsetJointOrigins
from ...lib.gridfinityUtils.baseGenerator import createFootGrid, cutBaseClearance, cutWallJunctionPockets, footCenters, cellCenters, createCellJointOrigins, keepBodiesInCells, cutOutsideShape, cutShapeWallJunctionPockets
from ...lib.gridfinityUtils.baseGeneratorInput import BaseGeneratorInput
from ...lib.gridfinityUtils.binBodyGenerator import createGridfinityBinBody, createShapeCavity, createBinLipSupport, binBodyTopHeight, createCompartmentCutout, compartmentCutoutFilletRadius, tabTopClearance, createTabLabel, hollowTabWallThickness
from ...lib.gridfinityUtils import labelGenerator
from ...lib.gridfinityUtils import labelColors
from ...lib.gridfinityUtils import binLabelLayout
from ...lib.gridfinityUtils import compartmentLayout
from ...lib.gridfinityUtils import binShape
from ...lib.gridfinityUtils import binGrid
from ...lib.gridfinityUtils import wallCreases
from ...lib.gridfinityUtils import scoopSides
from ...lib.gridfinityUtils.wallCreaseGenerator import createCreaseFolds
from ...lib.gridfinityUtils.binBodyGeneratorInput import BinBodyGeneratorInput, BinBodyCompartmentDefinition
from ...lib.gridfinityUtils.binBodyLipGeneratorInput import LIP_TYPE_FULL, lipTopTrimHeight
from ...lib.gridfinityUtils.binBodyTabGeneratorInput import BinBodyTabGeneratorInput
from ...lib.gridfinityUtils.binBodyTabGenerator import createGridfinityBinBodyTab, createTabHollowCuts, TabCavity, TabWallOpenings, tabFilletAllowance
from ...lib.gridfinityUtils.cullenectSocketGenerator import createCullenectSocket
from ...lib.gridfinityUtils import cullenect
from ...lib.gridfinityUtils import binCell
from ...lib.ui.unsupportedDesignTypeException import UnsupportedDesignTypeException
from .inputState import InputState

# Builds bins from an InputState, without the dialog, so the same settings always build the same bin

LOG_PREFIX = 'Gridfinity bin'

BIN_TYPE_HOLLOW = 'Hollow'
BIN_TYPE_SHELLED = 'Shelled'
BIN_TYPE_SOLID = 'Solid'

# default name of bins generated before tagging, keep as is even if the naming changes
BIN_LEGACY_NAME_PREFIX = 'Gridfinity bin '

# User parameter names are stored in user documents, keep these literal
BIN_PARAMETER_BASE_NAME = 'gfBin'
BIN_HEIGHT_PARAMETER = 'heightU'
BIN_LABEL_PARAMETER = 'label'
# the units of the bin, its own like the rest
BIN_HEIGHT_UNIT_PARAMETER = 'heightUnit'
BIN_BASE_WIDTH_PARAMETER = 'baseWidth'
BIN_BASE_LENGTH_PARAMETER = 'baseLength'
BIN_PARAMETERS = [BIN_HEIGHT_PARAMETER, BIN_HEIGHT_UNIT_PARAMETER, BIN_BASE_WIDTH_PARAMETER, BIN_BASE_LENGTH_PARAMETER]

# Labels of the parameters in the tag are stored in user documents, keep these literal
PARAMETER_LABEL_BASE_WIDTH = 'Base width unit'
PARAMETER_LABEL_BASE_LENGTH = 'Base length unit'
PARAMETER_LABEL_BIN_HEIGHT = 'Bin height (u)'
PARAMETER_LABEL_HEIGHT_UNIT = 'Height unit'
PARAMETER_LABEL_LABEL = 'Label'
# config fields the parameters stand for, lengths in mm like the config, see configJson
PARAMETER_FIELDS = {
    PARAMETER_LABEL_BASE_WIDTH: 'baseWidth',
    PARAMETER_LABEL_BASE_LENGTH: 'baseLength',
    PARAMETER_LABEL_BIN_HEIGHT: 'binHeight',
    PARAMETER_LABEL_HEIGHT_UNIT: 'heightUnit',
    PARAMETER_LABEL_LABEL: 'labelText',
}

# the move placing the bin, rebuilding in place reads the spot from it, see rebuildUtils
BIN_PLACEMENT_FEATURE = 'Bin placement'
# the same move of the colored labels in the bin's Text component (round 13)

# where a bin goes, stored in configs, keep these literal
PLACEMENT_AUTO = 'Snap to free spot'
PLACEMENT_CENTER = 'Center on origin'
PLACEMENT_OPTIONS = [PLACEMENT_AUTO, PLACEMENT_CENTER]

def binDisplayName(state: InputState) -> str:
    return 'Gridfinity bin {}x{}x{}{}'.format(
        binGrid.formatSize(state.binLength),
        binGrid.formatSize(state.binWidth),
        int(state.binHeight),
        ' half grid' if state.isHalfGrid else '',
    )

def gridDivisions(state: InputState) -> int:
    """Grid cells per base unit of the bin outline, see binGrid.outlineDivisions"""
    return binGrid.outlineDivisions(state.binWidth, state.binLength, state.isHalfGrid)

def feetSize(state: InputState) -> tuple[float, float]:
    """The bin size in feet, half ones in a half grid, ending in a half foot for a whole grid bin ending in a half"""
    feetPerUnit = binGrid.feetPerUnit(state.isHalfGrid)
    return (state.binWidth * feetPerUnit, state.binLength * feetPerUnit)

def feetGridSize(state: InputState) -> tuple[int, int]:
    """Columns and rows of feet, the shape is drawn in, a half foot counts as one"""
    (columns, rows) = feetSize(state)
    return (len(binGrid.footSpans(columns)), len(binGrid.footSpans(rows)))

def outlineCellsPerFoot(state: InputState) -> int:
    return binGrid.outlineCellsPerFoot(state.binWidth, state.binLength, state.isHalfGrid)

def shapeCells(state: InputState) -> list[tuple[int, int]]:
    """Feet the bin stands on, as drawn, all of them without a custom shape, see feetGridSize"""
    (columns, rows) = feetGridSize(state)
    if not state.hasCustomShape:
        return binShape.rectangle(columns, rows)
    return binShape.normalizeShape(state.shapeCells, columns, rows)

def outlineCells(state: InputState) -> list[tuple[int, int]]:
    """Cells of the outline grid the bin covers, half cells in a half grid or for sizes ending in a half, see gridDivisions"""
    return binShape.footShapeToOutline(shapeCells(state), *feetSize(state), outlineCellsPerFoot(state))

def shelledTabOriginY(baseLength: float, binLength: float, xyClearance: float) -> Dim:
    """
    Y of the tab's back top corner in a shelled bin: the back wall, the shell keeps the outer size. A shelled bin builds
    no scoop, so there is no front placement at the lip's inner edge (round 34, p281; the original generator had one
    for a light lip, which never ran)
    """
    return baseLength * binLength - Dim.length(xyClearance * 2)

def isShaped(state: InputState) -> bool:
    """A custom shape leaving cells out, a full one builds a plain bin"""
    return state.hasCustomShape and not binShape.isRectangle(shapeCells(state), *feetGridSize(state))

def centeredPlacement(state: InputState, baseWidth: Dim, baseLength: Dim) -> tuple[Dim, Dim]:
    """
    XY offset moving the bin, built from the origin into +X and +Y, so its footprint is centered on the origin. Made
    of the bin's base unit parameters, so the move keeps it centered when they change in the parameter table (round
    54, p670): plain numbers kept the old left edge and the bin grew to the right. Same value at build time as before.
    The size counts in base units, half grid and custom shape included (a shape is centered on its rectangle).
    Tested in tests/test_bin_centered_placement.py
    """
    return (
        (Dim.length(state.xyClearance * 2) - baseWidth * state.binWidth) / 2,
        (Dim.length(state.xyClearance * 2) - baseLength * state.binLength) / 2,
    )

def shapeError(state: InputState) -> str | None:
    """Why the shaped bin can't be built, none when it can or the bin is a plain rectangle"""
    if not isShaped(state):
        return None
    return binShape.shapeError(shapeCells(state))

def creaseLayout(state: InputState) -> list[tuple[wallCreases.WallSide, int]]:
    """
    Creased walls of the bin with their panel count, none when it gets no creases. A creased bin has a single compartment and a solid label tab,
    the folds would run into dividers and tab hollows
    """
    if not state.generateBody or not state.hasCreases:
        return []
    if state.binType not in [BIN_TYPE_HOLLOW, BIN_TYPE_SHELLED]:
        return []
    if state.binHeight < state.creaseMinHeight:
        return []
    # a scoop braces its wall already. A creased bin has a single compartment without a layout, so its scoop walls are
    # the bin's, the outer walls of binBodyInput.scoopSides alike
    # in outline grid cells, the lengths in base units scale along
    divisions = gridDivisions(state)
    return wallCreases.creaseLayout(
        outlineCells(state),
        state.baseWidth / divisions,
        state.baseLength / divisions,
        state.creaseMinLength * divisions,
        state.creaseMaxPanelLength * divisions,
        binScoopSides(state),
    )

def binScoopsBuilt(state: InputState) -> bool:
    """Only a plain hollow bin builds scoops"""
    return state.binType == BIN_TYPE_HOLLOW and not isShaped(state)

def binScoopSides(state: InputState) -> frozenset:
    """The walls with a scoop of the bin's checkboxes, see scoopSides (round 48); compartments may have their own"""
    return scoopSides.stateScoopSides(state, buildsScoop=binScoopsBuilt(state))

def tagged(parameter: adsk.fusion.UserParameter, field: str, owner: str) -> adsk.fusion.UserParameter:
    """The parameter tagged with the config field it holds and the bin it's of, see tagUtils.tagParameterField"""
    tagUtils.tagParameterField(parameter, field, owner)
    return parameter

def compartmentLabelField(index: int) -> str:
    """The config field of a compartment's own label, the label of its pocket, see compartmentLayout"""
    return f'compartmentPockets.{index}.label'

def createLabelDefinition(
    design: adsk.fusion.Design,
    binParameterPrefix: str,
    parameterName: str,
    text: str,
    icon: str,
    reuse: bool = False,
    field: str = 'labelText',
) -> labelGenerator.BinLabelDefinition | None:
    """
    The text goes into a text parameter so the label can be edited later, tagged with the config field the text
    comes from, nothing for a blank label
    """
    textParameter = None
    if len(text.strip()) > 0:
        textParameter = tagged(parameterUtils.addTextParameter(
            design,
            parameterUtils.parameterName(binParameterPrefix, parameterName),
            text,
            'Gridfinity bin label text',
            reuse,
        ), field, binParameterPrefix)
    definition = labelGenerator.BinLabelDefinition(textParameter, labelGenerator.iconPath(icon))
    return None if definition.isEmpty else definition

def buildBin(
    des: adsk.fusion.Design,
    state: InputState,
    settings: list[dict],
    placement: tuple[float, float] | None = None,
    parameterPrefix: str | None = None,
    occurrenceTransform: adsk.core.Matrix3D | None = None,
    oldPlace: assembly.OldPlace | None = None,
    mayChangeDocument: bool = True,
    cell: adsk.fusion.JointOrigin | None = None,
) -> list[adsk.fusion.BRepBody]:
    """
    Builds the bin into the design at the timeline marker, tagged with the settings to show later, see
    settingsUtils.snapshotInputs. A new bin is a component of its own in the container Bins, a part design is switched
    to hybrid for it unless the document may not change (a preview). A bin rebuilt in place keeps the placement, the
    parameters by their prefix, the transform of its component and the place the old one had, see rebuildUtils and
    assembly.OldPlace, a new one goes to a free spot. A bin centered on the origin is centered again, its size may have
    changed. With a cell, a joint origin of a baseplate's socket or of a box's floor (round 31, p312), the bin is
    jointed into it with its front left cell instead, see binCell.placementSource
    """
    if des.designType == adsk.fusion.DesignTypes.DirectDesignType:
        raise UnsupportedDesignTypeException('Timeline must be enabled for the generator to work, projects with disabled design history currently are not supported')
    # a bin in a cell is built and tagged as snapped, see binCell.storedPosition
    state = dataclasses.replace(state, placement=binCell.storedPosition(state.placement, cell is not None, PLACEMENT_AUTO))
    plan = designIntent.structurePlan(des.designIntent, mayChangeDocument, assembly.rebuildKind(oldPlace))
    # the root is active afterwards, also after a failed build, see assembly.buildWithStructure. A rebuild in place
    # builds through here as well, see rebuildBin
    return assembly.buildWithStructure(des, plan, lambda: _buildBin(des, state, settings, placement, parameterPrefix, occurrenceTransform, plan, oldPlace, cell))

def _buildBin(
    des: adsk.fusion.Design,
    state: InputState,
    settings: list[dict],
    placement: tuple[float, float] | None = None,
    parameterPrefix: str | None = None,
    occurrenceTransform: adsk.core.Matrix3D | None = None,
    plan: designIntent.StructurePlan | None = None,
    oldPlace: assembly.OldPlace | None = None,
    cell: adsk.fusion.JointOrigin | None = None,
) -> list[adsk.fusion.BRepBody]:
    # creased bins have a single compartment and a solid tab, see creaseLayout
    creases = creaseLayout(state)
    compartmentsX: int = 1 if len(creases) > 0 else state.compartmentsX
    compartmentsY: int = 1 if len(creases) > 0 else state.compartmentsY

    isHollow = state.binType == BIN_TYPE_HOLLOW
    isSolid = state.binType == BIN_TYPE_SOLID
    isShelled = state.binType == BIN_TYPE_SHELLED
    # a custom shape leaving cells out, without lip, scoop and tab for now. It's drawn in feet, its outline may be in half cells
    cells = shapeCells(state)
    shaped = isShaped(state)
    outline = outlineCells(state)
    cellsPerFoot = outlineCellsPerFoot(state)
    # the bin size in feet, half ones in a half grid, the feet grid cells are as much smaller
    halfGrid = state.isHalfGrid
    feetPerUnit = binGrid.feetPerUnit(halfGrid)
    columns = state.binWidth * feetPerUnit
    rows = state.binLength * feetPerUnit

    if shapeError(state) is not None:
        raise ValueError(shapeError(state))
    root = adsk.fusion.Component.cast(des.rootComponent)

    xyClearance = state.xyClearance
    binName = binDisplayName(state)

    # the container comes before the bin's timeline group, a rebuild deletes the group, see assembly.partPlace
    place = assembly.partPlace(des, plan or designIntent.structurePlan(des.designIntent, False), tagUtils.KIND_BINS, oldPlace)
    # the marker is before the features after a bin rebuilt in place, at the end otherwise
    originalTimelinePosition = des.timeline.markerPosition
    if place.isComponent:
        newCmpOcc = assembly.addOccurrence(des, place.parent, binName, occurrenceTransform, isMovable=True)
        newCmpOcc.activate()
        gridfinityBinComponent: adsk.fusion.Component = newCmpOcc.component
    else:
        newCmpOcc = None
        gridfinityBinComponent: adsk.fusion.Component = des.rootComponent
    features: adsk.fusion.Features = gridfinityBinComponent.features

    # pick the spot before generating, so none of this bin's geometry can count as an obstacle. A bin going into a cell
    # is moved there by its joint, it stays at the origin of its component (round 31). Before upstream's Center on
    # origin, the kept spot of a rebuild and a free one (round 38). A centered bin's offset is made of its base unit
    # parameters once they are there, see centeredPlacement (round 54)
    source = binCell.placementSource(state.placement == PLACEMENT_CENTER, cell is not None and newCmpOcc is not None, placement is not None)
    spot = (0, 0) if source in ('cell', 'center') else placement if source == 'kept' else placementUtils.findPlacement(
        des,
        tagUtils.TAG_BIN,
        BIN_LEGACY_NAME_PREFIX,
        (
            0,
            0,
            state.binWidth * state.baseWidth - xyClearance * 2,
            state.binLength * state.baseLength - xyClearance * 2,
        ),
        state.baseWidth,
        state.baseLength,
    )

    reuseParameters = parameterPrefix is not None
    # the bin's id too, see tagUtils.tagBody
    binParameterPrefix = parameterPrefix or parameterUtils.nextFreePrefix(des, BIN_PARAMETER_BASE_NAME, BIN_PARAMETERS, tagUtils.usedBodyIds(des, tagUtils.TAG_BIN))
    # every bin has units of its own, changing one bin's parameters changes no other bin
    baseWidthParameter = tagged(parameterUtils.addLengthParameter(
        des,
        parameterUtils.parameterName(binParameterPrefix, BIN_BASE_WIDTH_PARAMETER),
        state.baseWidth,
        'Gridfinity bin base width unit',
        reuseParameters,
    ), 'baseWidth', binParameterPrefix)
    baseLengthParameter = tagged(parameterUtils.addLengthParameter(
        des,
        parameterUtils.parameterName(binParameterPrefix, BIN_BASE_LENGTH_PARAMETER),
        state.baseLength,
        'Gridfinity bin base length unit',
        reuseParameters,
    ), 'baseLength', binParameterPrefix)
    baseWidth = Dim.parameter(baseWidthParameter)
    baseLength = Dim.parameter(baseLengthParameter)
    # the offset the bin is moved by, Dims: the move and what is placed after it follow a centered bin's parameters
    binPlacement = centeredPlacement(state, baseWidth, baseLength) if source == 'center' else (Dim.length(spot[0]), Dim.length(spot[1]))
    gridWidth = baseWidth / feetPerUnit if halfGrid else baseWidth
    gridLength = baseLength / feetPerUnit if halfGrid else baseLength
    # user parameters driving the bin, kept in its tag to show with its settings
    binParameters = [[PARAMETER_LABEL_BASE_WIDTH, baseWidthParameter.name], [PARAMETER_LABEL_BASE_LENGTH, baseLengthParameter.name]]

    # create base interface
    baseGeneratorInput = BaseGeneratorInput()
    baseGeneratorInput.originPoint = geometryUtils.createOffsetPoint(
        gridfinityBinComponent.originConstructionPoint.geometry,
        byX=-xyClearance,
        byY=-xyClearance,
    )
    baseGeneratorInput.baseWidth = gridWidth
    baseGeneratorInput.baseLength = gridLength
    baseGeneratorInput.xyClearance = xyClearance
    # half feet have no room for holes
    baseGeneratorInput.hasScrewHoles = state.hasScrewHoles and not isShelled and not halfGrid
    baseGeneratorInput.hasMagnetCutouts = state.hasMagnetCutouts and not isShelled and not halfGrid
    baseGeneratorInput.hasMagnetCutoutsTabs = state.hasMagnetCutoutsTabs and not isShelled and not halfGrid
    baseGeneratorInput.screwHolesDiameter = state.screwHoleDiameter
    baseGeneratorInput.magnetCutoutsDiameter = state.magnetCutoutDiameter
    baseGeneratorInput.magnetCutoutsDepth = state.magnetCutoutDepth

    # the grid of the outline, for the shape and creases, in half cells for a whole grid bin ending in a half, see gridDivisions
    if gridDivisions(state) == feetPerUnit:
        outlineGrid = baseGeneratorInput
    else:
        outlineGrid = copy.copy(baseGeneratorInput)
        outlineGrid.baseWidth = baseWidth / gridDivisions(state)
        outlineGrid.baseLength = baseLength / gridDivisions(state)

    baseBodies: list[adsk.fusion.BRepBody]
    if state.generateBase:
        baseBodies = createFootGrid(
            baseGeneratorInput,
            columns,
            rows,
            gridfinityBinComponent,
        )
        if shaped:
            baseBodies = keepBodiesInCells(baseBodies, cells, baseGeneratorInput, gridfinityBinComponent, name='Foot outside shape remove')

    # create bin body
    binBodyInput = BinBodyGeneratorInput()
    binBodyInput.hasLip = state.hasLip
    binBodyInput.shapeCells = outline if shaped else None
    binBodyInput.shapeCellsPerFoot = cellsPerFoot
    binBodyInput.hasLipNotches = state.hasLipNotches
    binBodyInput.lipType = state.lipType
    binBodyInput.lipTopTrimHeight = lipTopTrimHeight(state.isLipTopTrimmed)
    binBodyInput.binWidth = columns
    binBodyInput.binLength = rows
    binBodyInput.binHeight = Dim.number(state.binHeight)
    binBodyInput.baseWidth = gridWidth
    binBodyInput.baseLength = gridLength
    binBodyInput.heightUnit = Dim.length(state.heightUnit)
    binBodyInput.xyClearance = xyClearance
    binBodyInput.binCornerFilletRadius = const.BIN_CORNER_FILLET_RADIUS - xyClearance
    # a shaped hollow bin gets its cavity once trimmed to the shape
    binBodyInput.isSolid = isSolid or isShelled or shaped
    binBodyInput.hasLipBottomChamfer = not isSolid
    binBodyInput.wallThickness = state.wallThickness
    binBodyInput.scoopMaxRadius = state.scoopMaxRadius
    binBodyInput.hasTab = state.hasTab and isHollow and not shaped
    # in base units like the size, the body counts in feet
    binBodyInput.tabLength = state.tabLength * feetPerUnit
    binBodyInput.tabWidth = state.tabWidth
    binBodyInput.tabPosition = state.tabPosition * feetPerUnit
    binBodyInput.tabOverhangAngle = state.tabOverhangAngle
    binBodyInput.isTabHollow = state.isTabHollow and len(creases) == 0
    binBodyInput.isTabOpenThroughSides = state.isTabOpenThroughSides
    binBodyInput.tabTopAngle = state.tabTopAngle
    binBodyInput.tabTopOffset = state.tabTopOffset
    binBodyInput.labelStyle = state.labelStyle
    binBodyInput.isLabelBold = state.isLabelBold
    binBodyInput.labelColor = state.labelColor
    # colored labels go into a Text component of the bin, made with the first of them
    binBodyInput.binOccurrence = newCmpOcc
    binBodyInput.textOccurrence = assembly.TextOccurrence(des, newCmpOcc)
    binBodyInput.binPlacement = binPlacement
    binBodyInput.cullenectSocketOffset = state.cullenectSocketOffset
    binBodyInput.cullenectUnitWidth = baseWidth
    isCullenect = state.labelStyle == labelGenerator.LABEL_STYLE_CULLENECT
    if isCullenect:
        # the socket needs a flat tab top wide enough for it, a wider tab of the user stays
        binBodyInput.tabTopAngle = 0
        binBodyInput.tabWidth = cullenect.effectiveTabWidth(
            state.tabWidth,
            state.tabOverhangAngle,
            tabFilletAllowance(state.tabOverhangAngle, 0),
            state.cullenectSocketOffset,
        )
    binBodyInput.compartmentsByX = compartmentsX
    binBodyInput.compartmentsByY = compartmentsY

    # label text and icon per compartment, the label tab section fills in the ones left blank
    # without the layout the grid is uniform, also for pockets saved with the layout hidden
    pockets = compartmentLayout.normalizePockets(state.compartmentPockets if state.showCompartmentsLayout and len(creases) == 0 else [], compartmentsX, compartmentsY)
    compartmentLabels: list[tuple[str, str]] = [(item['label'], item['icon']) for item in pockets]
    # pockets come in pattern order, single full depth cells are built once and patterned
    binBodyInput.isUniformCompartments = compartmentLayout.isUniform(pockets)
    binBodyInput.compartments = []
    for item in pockets:
        compartment = BinBodyCompartmentDefinition(item['x'], item['y'], item['width'], item['length'])
        if item['depth'] is not None:
            compartment.depth = item['depth'] / 10
        # a compartment's own scoop walls from the layout editor, the bin's without (round 48)
        compartment.scoopSides = scoopSides.compartmentScoopSides(
            item.get('scoops') if binScoopsBuilt(state) else None, binScoopSides(state), hasTab=state.hasTab)
        binBodyInput.compartments.append(compartment)
    binBodyInput.scoopSides = scoopSides.outerScoopWalls(
        [(c.positionX, c.positionY, c.width, c.length, c.scoopSides) for c in binBodyInput.compartments],
        compartmentsX, compartmentsY,
    )
    # grid lines are whole grid units also on a half grid, the feet of any bin stacked on top have a groove there
    binBodyInput.raisedDividers = raisedDividers.segmentsForBin(
        state.hasDividersToTop, state.hasLip, isHollow, shaped,
        pockets, compartmentsX, compartmentsY, state.binWidth, state.binLength,
    )

    binBody: adsk.fusion.BRepBody
    # colored labels, bodies of their own beside the bin body, see labelGenerator.createLabel
    labelBodies: list[adsk.fusion.BRepBody] = []
    # Cullenect pockets as (compartment index, compartments, placement), a joint origin goes on each (p160)
    pockets: list[tuple[int, int, object]] = []

    if state.generateBody:
        binBodyInput.binHeight = Dim.parameter(tagged(parameterUtils.addUnitlessParameter(
            des,
            parameterUtils.parameterName(binParameterPrefix, BIN_HEIGHT_PARAMETER),
            state.binHeight,
            'Gridfinity bin height, in height units',
            reuseParameters,
        ), 'binHeight', binParameterPrefix))
        binParameters.append([PARAMETER_LABEL_BIN_HEIGHT, binBodyInput.binHeight.expression])
        # Cullenect tabs get a socket, the text goes on the inserts
        if binBodyInput.hasTab and not isCullenect:
            for compartmentIndex, compartment in enumerate(binBodyInput.compartments):
                (compartmentText, compartmentIcon) = compartmentLabels[compartmentIndex] if compartmentIndex < len(compartmentLabels) else ('', compartmentLayout.DEFAULT_ICON)
                compartment.label = createLabelDefinition(
                    des,
                    binParameterPrefix,
                    BIN_LABEL_PARAMETER if len(binBodyInput.compartments) == 1 else f'{BIN_LABEL_PARAMETER}{compartmentIndex + 1}',
                    compartmentText or state.labelText,
                    state.labelIcon if compartmentIcon == compartmentLayout.DEFAULT_ICON else compartmentIcon,
                    reuseParameters,
                    # a compartment without its own label shows the bin's
                    compartmentLabelField(compartmentIndex) if compartmentText else 'labelText',
                )
                if compartment.label is not None and compartment.label.textParameter is not None:
                    binParameters.append([
                        PARAMETER_LABEL_LABEL if len(binBodyInput.compartments) == 1 else f'Compartment {compartmentIndex + 1} label',
                        compartment.label.textParameter.name,
                    ])
        binBodyInput.heightUnit = Dim.parameter(tagged(parameterUtils.addLengthParameter(
            des,
            parameterUtils.parameterName(binParameterPrefix, BIN_HEIGHT_UNIT_PARAMETER),
            state.heightUnit,
            'Gridfinity bin height unit',
            reuseParameters,
        ), 'heightUnit', binParameterPrefix))
        binParameters.append([PARAMETER_LABEL_HEIGHT_UNIT, binBodyInput.heightUnit.expression])
        (binBody, labelBodies, pockets) = createGridfinityBinBody(
            binBodyInput,
            gridfinityBinComponent,
        )
    combineFeatures = gridfinityBinComponent.features.combineFeatures

    # merge everything before the clearance cut, so the cut only has to reference the bin body
    if state.generateBody and state.generateBase:
        toolBodies = commonUtils.objectCollectionFromList(baseBodies)
        combineFeatureInput = combineFeatures.createInput(binBody, toolBodies)
        combineFeatures.add(combineFeatureInput).name = 'Bin body and feet join'
        binBody.name = binName

    # feet only touch each other along edges, so without a body they stay separate
    clearanceBodies = [binBody] if state.generateBody else baseBodies
    if shaped and (state.generateBody or state.generateBase):
        # the body is built over the whole grid, the outline trims it down to the shape
        cutOutsideShape(outline, outlineGrid, clearanceBodies, gridfinityBinComponent, name='Outer clearance trim')
    elif state.generateBase:
        # the body is built inside the clearance already, alone it has nothing to trim
        cutBaseClearance(
            baseGeneratorInput,
            columns,
            rows,
            clearanceBodies,
            gridfinityBinComponent,
        )

    if state.generateBody and state.generateBase:
        # curve up the gaps between feet along the walls instead of leaving flat overhangs,
        # shaped bins need them at the inner corners too, the shell follows the pockets cut before it
        if shaped:
            cutShapeWallJunctionPockets(
                outlineGrid,
                outline,
                binBody,
                gridfinityBinComponent,
                (binGrid.footLines(columns, cellsPerFoot), binGrid.footLines(rows, cellsPerFoot)),
            )
        elif columns > 1 or rows > 1:
            cutWallJunctionPockets(baseGeneratorInput, columns, rows, binBody, gridfinityBinComponent)

    if shaped and isHollow and state.generateBody:
        cavity = createShapeCavity(
            outline,
            outlineGrid,
            binBodyInput.wallThickness,
            binBodyTopHeight(binBodyInput),
            gridfinityBinComponent,
            name='Cavity',
        )
        if binBodyInput.hasLip and binBodyInput.lipType == LIP_TYPE_FULL:
            # taken out of the cavity, so it stays clear of what was cut out of the body before
            lipSupport = createBinLipSupport(binBodyInput, const.BIN_COMPARTMENT_BOTTOM_THICKNESS, gridfinityBinComponent)
            if lipSupport is not None:
                combineUtils.cutBody(cavity, commonUtils.objectCollectionFromList([lipSupport]), gridfinityBinComponent, name='Lip support from cavity cut')
        combineUtils.cutBody(binBody, commonUtils.objectCollectionFromList([cavity]), gridfinityBinComponent, name='Cavity cut')

    if state.generateBody and len(creases) > 0:
        # panels from where the floor fillet ends up the inside of the wall to the body top
        wallOffset = xyClearance + binBodyInput.wallThickness
        creaseBottomZ = const.BIN_COMPARTMENT_BOTTOM_THICKNESS + compartmentCutoutFilletRadius(
            binShape.cornerRadius(True, baseGeneratorInput.cornerFilletRadius, wallOffset)
        )
        creaseTopZ = binBodyTopHeight(binBodyInput)
        creaseDepth = state.creaseDepth
        if isHollow:
            # the inside follows the dent, so the wall keeps its thickness, a shell does it by itself.
            # Joined before the dent is cut, the dent goes deeper than the wall and would get filled back in
            innerFolds = createCreaseFolds(creases, outlineGrid, wallOffset, creaseDepth, creaseBottomZ, creaseTopZ, gridfinityBinComponent, name='Wall crease inside')
            combineUtils.joinBodies(binBody, commonUtils.objectCollectionFromList(innerFolds), gridfinityBinComponent, name='Wall creases inside join')
        outerFolds = createCreaseFolds(creases, outlineGrid, xyClearance, creaseDepth, creaseBottomZ, creaseTopZ, gridfinityBinComponent, name='Wall crease')
        combineUtils.cutBody(binBody, commonUtils.objectCollectionFromList(outerFolds), gridfinityBinComponent, name='Wall creases cut')

    if isShelled and state.generateBody:
        # the body already stands the xy clearance in from the cell border, so the walls take the full thickness
        # face.boundingBox.maxPoint.z ~ face.boundingBox.minPoint.z => face horizontal
        # largest horizontal face
        horizontalFaces = [face for face in binBody.faces if geometryUtils.isHorizontal(face)]
        topFace = faceUtils.maxByArea(horizontalFaces)
        topFaceMinPoint = topFace.boundingBox.minPoint
        if binBodyInput.hasLip:
            splitBodyFeatures = features.splitBodyFeatures
            splitBodyInput = splitBodyFeatures.createInput(
                binBody,
                topFace,
                True
            )
            splitBodies = splitBodyFeatures.add(splitBodyInput)
            splitBodies.name = 'Shell split at lip'
            bottomBody = min(splitBodies.bodies, key=lambda x: x.boundingBox.minPoint.z)
            topBody = max(splitBodies.bodies, key=lambda x: x.boundingBox.minPoint.z)
            horizontalFaces = [face for face in bottomBody.faces if geometryUtils.isHorizontal(face)]
            topFace = faceUtils.maxByArea(horizontalFaces)
            shellUtils.simpleShell([topFace], binBodyInput.wallThickness, gridfinityBinComponent, name='Shell', isRounded=state.isShellRounded)
            toolBodies = adsk.core.ObjectCollection.create()
            toolBodies.add(topBody)
            if binBodyInput.lipType == LIP_TYPE_FULL:
                # the shell has the wall thickness for a floor
                lipSupport = createBinLipSupport(binBodyInput, binBodyInput.wallThickness, gridfinityBinComponent)
                if lipSupport is not None:
                    toolBodies.add(lipSupport)
            combineAfterShellFeatureInput = combineFeatures.createInput(bottomBody, toolBodies)
            combineAfterShellFeature = combineFeatures.add(combineAfterShellFeatureInput)
            combineAfterShellFeature.name = 'Shell and lip join'
            binBody = combineAfterShellFeature.bodies.item(0)
        else:
            shellUtils.simpleShell([topFace], binBodyInput.wallThickness, gridfinityBinComponent, name='Shell', isRounded=state.isShellRounded)

        if state.hasTab and not shaped:
            compartmentTabInput = BinBodyTabGeneratorInput()
            tabOriginX = Dim.length(binBodyInput.wallThickness) + binBodyInput.baseWidth * max(0, min(binBodyInput.tabPosition, binBodyInput.binWidth - binBodyInput.tabLength))
            tabOriginY = shelledTabOriginY(binBodyInput.baseLength, binBodyInput.binLength, binBodyInput.xyClearance)
            tabOriginZ = binBodyTopHeight(binBodyInput)
            compartmentTabInput.origin = adsk.core.Point3D.create(tabOriginX.value, tabOriginY.value, tabOriginZ.value)
            compartmentTabInput.originX = tabOriginX
            compartmentTabInput.originY = tabOriginY
            compartmentTabInput.originZ = tabOriginZ
            compartmentTabInput.length = binBodyInput.baseWidth * max(0, min(binBodyInput.tabLength, binBodyInput.binWidth)) - Dim.length(binBodyInput.wallThickness * 2 + binBodyInput.xyClearance * 2)
            compartmentTabInput.width = binBodyInput.tabWidth
            compartmentTabInput.overhangAngle = binBodyInput.tabOverhangAngle
            compartmentTabInput.labelAngle = binBodyInput.tabTopAngle
            compartmentTabInput.topClearance = tabTopClearance(binBodyInput.labelStyle, binBodyInput.tabTopOffset)
            tabBody = createGridfinityBinBodyTab(compartmentTabInput, gridfinityBinComponent, name='Label tab')

            # trim the tab to the shell interior, its ends would otherwise poke out past the rounded outer corners,
            # intersecting leaves a single body, so nothing has to be picked out of the pieces
            shellThickness = Dim.length(binBodyInput.wallThickness)
            shellInteriorCornerFilletRadius = binBodyInput.binCornerFilletRadius - binBodyInput.wallThickness
            bodyWidth = binBodyInput.baseWidth * binBodyInput.binWidth - Dim.length(xyClearance * 2)
            bodyLength = binBodyInput.baseLength * binBodyInput.binLength - Dim.length(xyClearance * 2)
            shellInterior = createCompartmentCutout(
                binBodyInput.wallThickness,
                shellThickness,
                shellThickness,
                tabOriginZ,
                bodyWidth - shellThickness * 2,
                bodyLength - shellThickness * 2,
                tabOriginZ,
                shellInteriorCornerFilletRadius,
                frozenset(),
                0,
                False,
                gridfinityBinComponent,
                name='Shell interior',
            )
            intersectTabInput = combineFeatures.createInput(tabBody, commonUtils.objectCollectionFromList([shellInterior]))
            intersectTabInput.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
            intersectTabInput.isKeepToolBodies = True
            intersectTabFeature = combineFeatures.add(intersectTabInput)
            intersectTabFeature.name = 'Label tab trim'
            trimmedTabBodies = [body for body in list(intersectTabFeature.bodies) if not body.revisionId == shellInterior.revisionId]
            tabHollowCuts: list[adsk.fusion.BRepBody] = []
            if binBodyInput.isTabHollow:
                # the tab sits on the back wall, opened through it so the hollow isn't sealed
                shellInteriorMaxX = bodyWidth - shellThickness
                tabMaxX = tabOriginX + compartmentTabInput.length
                tabHollowCuts = createTabHollowCuts(
                    compartmentTabInput,
                    # as expressions, so they follow a changed base width (round 15, p60)
                    Dim.max(tabOriginX, shellThickness),
                    Dim.min(tabMaxX, shellInteriorMaxX),
                    hollowTabWallThickness(shellThickness.value, binBodyInput.labelStyle),
                    shellInterior,
                    TabCavity(shellThickness, shellInteriorMaxX, bodyLength - shellThickness, compartmentCutoutFilletRadius(shellInteriorCornerFilletRadius)),
                    TabWallOpenings(
                        shellThickness.value * 2,
                        back=True,
                        minXSide=binBodyInput.isTabOpenThroughSides,
                        maxXSide=binBodyInput.isTabOpenThroughSides,
                    ),
                    gridfinityBinComponent,
                    name='Label tab',
                ).all()
            gridfinityBinComponent.features.removeFeatures.add(shellInterior).name = 'Shell interior remove'
            combineUtils.joinBodies(binBody, commonUtils.objectCollectionFromList(trimmedTabBodies), gridfinityBinComponent, name='Label tab join')
            if len(tabHollowCuts) > 0:
                combineUtils.cutBody(binBody, commonUtils.objectCollectionFromList(tabHollowCuts), gridfinityBinComponent, name='Label tab hollow cut')

            if isCullenect:
                shelledPocket = createCullenectSocket(
                    tabOriginX,
                    tabOriginX + compartmentTabInput.length,
                    tabOriginY,
                    binBodyInput.tabWidth,
                    tabOriginZ - Dim.length(tabTopClearance(binBodyInput.labelStyle, binBodyInput.tabTopOffset)),
                    binBodyInput.cullenectUnitWidth,
                    binBodyInput.cullenectSocketOffset,
                    binBodyInput.tabOverhangAngle,
                    binBody,
                    gridfinityBinComponent,
                    name='Label',
                )
                if shelledPocket is not None:
                    pockets.append((0, 1, shelledPocket))
            shelledLabel = None if isCullenect else createLabelDefinition(des, binParameterPrefix, BIN_LABEL_PARAMETER, state.labelText, state.labelIcon, reuseParameters)
            if shelledLabel is not None and shelledLabel.textParameter is not None:
                binParameters.append([PARAMETER_LABEL_LABEL, shelledLabel.textParameter.name])
            if shelledLabel is not None:
                labelBodies += createTabLabel(
                    shelledLabel,
                    binBodyInput.labelStyle,
                    binBodyInput.isLabelBold,
                    tabOriginX,
                    tabOriginX + compartmentTabInput.length,
                    tabOriginY,
                    binBodyInput.tabWidth,
                    tabOriginZ,
                    binBody,
                    gridfinityBinComponent,
                    binBodyInput.tabTopAngle,
                    binBodyInput.tabTopOffset,
                    binBodyInput.labelColor,
                    name='Label',
                    textOccurrence=binBodyInput.textOccurrence,
                    targetOccurrence=binBodyInput.binOccurrence,
                    binPlacement=binPlacement,
                )

    generatedBodies: list[adsk.fusion.BRepBody] = []
    if state.generateBody or state.generateBase:
        generatedBodies = [binBody] if state.generateBody else baseBodies
        # colored labels stand apart from the bin body and are part of what was built. They are drawn where the bin ends
        # up and aren't moved with it: a move takes the bodies there are, the letters a longer text adds stayed behind
        # (round 14, p72)
        movedBodies = generatedBodies + labelBodies
        if not (isZero(binPlacement[0]) and isZero(binPlacement[1])):
            placementUtils.moveBodies(generatedBodies, *binPlacement, gridfinityBinComponent, name=BIN_PLACEMENT_FEATURE)
        # mark generated geometry so later bins can tell it apart from the rest of the design,
        # with the settings it was generated with to show later. Labels aren't bins, they'd count as bins of their own
        for body in generatedBodies:
            tagUtils.tagBody(body, tagUtils.TAG_BIN, settings, binParameters, configJson.stateToJson(configJson.GENERATOR_BIN, state), binParameterPrefix, binName, body.name)
        # the letters of outline labels in their own color, as a slicer can print them, see labelFaces. A colored label
        # has letter bodies of its own instead (p86)
        if labelColors.paintsOutlineLetterFaces(state.generateBody, state.labelStyle == labelGenerator.LABEL_STYLE_OUTLINE, state.labelColor):
            try:
                labelFaces.paintLetterFaces(des, binBody)
            except Exception as err:
                commonUtils.debugLog(f'{LOG_PREFIX} label letters not colored, {err}')
        generatedBodies = movedBodies

    if state.generateBase and state.hasJointOrigins:
        # last, after the placement, joint origin offsets don't follow body moves
        centers = footCenters(
            gridWidth,
            gridLength,
            xyClearance,
            columns,
            rows,
            None if isZero(binPlacement[0]) else binPlacement[0],
            None if isZero(binPlacement[1]) else binPlacement[1],
        )
        createCellJointOrigins(
            [center for center in centers if not shaped or (center[0], center[1]) in set(cells)],
            gridfinityBinComponent,
            name='Foot joint origin',
        )

    if len(pockets) > 0:
        # always, the label command joints an insert into them (p160, 15.11.2026). After the placement like the
        # feet's, with the size of the pocket in mm, an insert and a bin have base units of their own
        offsetX = binPlacement[0]
        offsetY = binPlacement[1]
        jointOrigins = createOffsetJointOrigins(
            [(cullenect.pocketJointOriginName(index, count), pocket.centerX + offsetX, pocket.centerY + offsetY, pocket.floorZ) for (index, count, pocket) in pockets],
            gridfinityBinComponent,
            name='Pocket joint origin',
        )
        for (jointOrigin, (_, _, pocket)) in zip(jointOrigins, pockets):
            jointOrigin.attributes.add(tagUtils.TAG_GROUP, tagUtils.TAG_POCKET, cullenect.pocketTagValue(*cullenect.pocketSizeMm(pocket.units, baseWidth.value, state.cullenectSocketOffset)))

    if cell is not None and newCmpOcc is not None:
        # into the cell picked, with the center of the bin's front left cell (round 31, p312: the cell
        # is the front left corner of a bin larger than 1x1). A joint origin of its own: the foot ones sit in half feet
        # in a half grid and a shaped bin may leave the corner out. After the placement like the feet's, in the bin's
        # timeline group like an insert's joint into its pocket, a rebuild joints the new bin again, see rebuildBin. A
        # preview in a part design builds bodies into the root, which a joint can't move, it shows the bin beside
        [(_, _, x, y)] = cellCenters(
            baseWidth,
            baseLength,
            xyClearance,
            range(1),
            range(1),
            None if isZero(binPlacement[0]) else binPlacement[0],
            None if isZero(binPlacement[1]) else binPlacement[1],
        )
        (placementOrigin,) = createOffsetJointOrigins(
            [(binCell.PLACEMENT_JOINT_ORIGIN, x, y, Dim.length(-const.BIN_BASE_HEIGHT))],
            gridfinityBinComponent,
            name=binCell.PLACEMENT_JOINT_ORIGIN,
        )
        jointInput = root.joints.createInput(assembly.inContext(placementOrigin, newCmpOcc), cell)
        jointInput.setAsRigidJointMotion()
        joint = root.joints.add(jointInput)
        joint.name = binCell.cellJointName(binName)
        # Fusion turns off a joint origin a joint uses, the cell stays shown for the next bin (as an insert's pocket)
        assembly.keepShown(cell)

    # group features in timeline
    binGroup = des.timeline.timelineGroups.add(originalTimelinePosition, des.timeline.markerPosition - 1)
    binGroup.name = binName
    return generatedBodies

def rebuildBin(
    des: adsk.fusion.Design,
    body: adsk.fusion.BRepBody,
    state: InputState,
    settings: list[dict],
    isPreview: bool,
) -> tuple[list[adsk.fusion.BRepBody], list[str]]:
    """
    Builds the bin in place of the one the body is of, keeping the features after it, see rebuildUtils.rebuild, also
    when only settings its parameters hold changed. A bin the bin command jointed into a cell goes into it again
    (round 31). Returns the new bodies and what of the later features needs a look
    """
    target = rebuildUtils.findTarget(des, body, tagUtils.TAG_BIN, BIN_PLACEMENT_FEATURE)
    prefix = rebuildUtils.bodyId(target.bodies[0], BIN_PARAMETER_BASE_NAME)
    if not isPreview:
        newConfig = configJson.stateToJson(configJson.GENERATOR_BIN, state)
        commonUtils.fileLog(f'{LOG_PREFIX} rebuilding {target.group.name} at {target.placement}, {rebuildUtils.configChanges(configJson.GENERATOR_BIN, target.bodies[0], newConfig)}')
    # a bin jointed into a cell keeps it (round 31, spec decision 4): its joint is in the old group and goes with it, the new bin is jointed into the same cell. A cell of a
    # part after the bin in the timeline isn't there where the new one is built, it keeps its place without a joint
    found = binCellOf(des, target)
    cell = found.cell
    notes = []
    if cell is not None and rebuildUtils.comesAfter(target, cell):
        notes.append(f'{target.group.name}: the part of {cell.name} comes after the bin in the timeline, the new bin stays where it was without a joint into the cell')
        cell = None
    elif cell is None and found.wasInCell:
        # its cell was deleted, or a rebuilt baseplate or box no longer has it (spec decision 4, review)
        notes.append(f'{target.group.name}: the cell it was jointed into is gone, the new bin stays where it was without a joint')
    (bodies, rebuildNotes) = rebuildUtils.rebuild(
        des,
        target,
        prefix,
        BIN_PARAMETER_BASE_NAME,
        isPreview,
        # colored labels are bodies of their own beside the bin, only the bin bodies take the place of the old ones.
        # A jointed bin is placed by its joint, a free one keeps the transform of its old component
        lambda placement, parameterPrefix, transform, oldPlace: tagUtils.taggedBodies(buildBin(des, state, settings, placement, parameterPrefix, None if cell is not None else transform, oldPlace, not isPreview, cell=cell), tagUtils.TAG_BIN),
        'bin',
        namePrefix=BIN_LEGACY_NAME_PREFIX,
    )
    if not isPreview and cell is not None:
        # with the timeline at its end again, Fusion turned it off for the old joint too (as rebuildLabel)
        assembly.keepShown(cell)
    return (bodies, rebuildNotes + notes)

# the role of a box's lid component (boxBuilder.LID_COMPONENT_NAME): its stacking grid isn't offered (round 31)
LID_ROLE = 'Lid'

def hasCellParts(des: adsk.fusion.Design) -> bool:
    """Whether the design has a baseplate or a box, the bin dialog offers a cell then (round 31)"""
    return any(len(des.findAttributes(tagUtils.TAG_GROUP, tagName)) > 0 for tagName in (tagUtils.TAG_BASEPLATE, tagUtils.TAG_BOX))

def isCellJointOrigin(jointOrigin: adsk.fusion.JointOrigin | None) -> bool:
    """
    Whether a new bin can be jointed into the joint origin (round 31, p312): a socket of a baseplate or a cell of the
    floor of a box (round 31, not the grid on its lid), by its name and
    the tagged body of its component. Not a foot of a bin, a pocket or a seat
    """
    if jointOrigin is None or not jointOrigin.isValid or binCell.cellOf(jointOrigin.name) is None:
        return False
    component = (jointOrigin.nativeObject or jointOrigin).parentComponent
    # a baseplate or box of bodies in the root (a part design, or built before round 13) has no component a rebuild
    # could move the joint to by name, the bin would lose its cell then (review): not offered
    if component == component.parentDesign.rootComponent:
        return False
    tagName = tagUtils.TAG_BASEPLATE if jointOrigin.name.startswith(binCell.SOCKET_PREFIX) else tagUtils.TAG_BOX
    if tagName == tagUtils.TAG_BOX and rebuildUtils.partRole(component) == LID_ROLE:
        return False
    return any(body.attributes.itemByName(tagUtils.TAG_GROUP, tagName) is not None for body in component.bRepBodies)

def _readSide(read):
    """A side of a joint, none when Fusion refuses to read it (a deleted joint origin)"""
    try:
        return read()
    except RuntimeError:
        return None

@dataclass
class CellOfBin:
    """The cell a bin was jointed into, as seen from the root, and whether it had a joint into one at all: a joint whose
    cell is gone has no cell but was in one"""
    cell: adsk.fusion.JointOrigin | None
    wasInCell: bool

def binCellOf(des: adsk.fusion.Design, target: rebuildUtils.RebuildTarget) -> CellOfBin:
    """The cell the bin was jointed into by the bin command: the other side of its joint "... in cell" on its Cell
    placement joint origin (round 31), as labelBuilder.insertPocket. A joint of the user's own isn't the command's, it
    stays a later feature. A joint whose cell was deleted may refuse to be read, Fusion raises for a deleted object; it
    counts as one without a cell, the rebuild goes on (review)"""
    if target.occurrence is None:
        return CellOfBin(None, False)
    component = (target.occurrence.nativeObject or target.occurrence).component
    wasInCell = False
    for joint in des.rootComponent.allJoints:
        try:
            if not binCell.isCellJointName(joint.name):
                continue
            # each side on its own: the side of a deleted cell may raise, the bin's own side still says it was in one
            sides = [
                (_readSide(lambda: adsk.fusion.JointOrigin.cast(joint.geometryOrOriginOne)), _readSide(lambda: joint.occurrenceOne)),
                (_readSide(lambda: adsk.fusion.JointOrigin.cast(joint.geometryOrOriginTwo)), _readSide(lambda: joint.occurrenceTwo)),
            ]
            for ((side, _), (other, otherOccurrence)) in (sides, sides[::-1]):
                if side is None or side.name != binCell.PLACEMENT_JOINT_ORIGIN or (side.nativeObject or side).parentComponent != component:
                    continue
                wasInCell = True
                if other is not None and binCell.cellOf(other.name) is not None:
                    return CellOfBin(assembly.jointOriginInRoot(des, other, otherOccurrence), True)
        except RuntimeError as err:
            commonUtils.fileLog(f'{LOG_PREFIX} a joint into a cell couldn\'t be read, {err}')
    return CellOfBin(None, wasInCell)

def configWithParameters(config: dict, parameters: list, findParameter) -> dict:
    """The config a bin was built with, with the values its parameters have now, see rebuildUtils.configWithParameters.
    Compartments showing the bin's label each have a parameter of their own, the one edited in Fusion gives the text
    (review round 19, see binLabelLayout.sharedText)"""
    filled = rebuildUtils.configWithParameters(configJson.GENERATOR_BIN, config, parameters, findParameter, PARAMETER_FIELDS)
    texts = [parameter.textValue for (field, parameter) in rebuildUtils.parameterFields(parameters, findParameter, PARAMETER_FIELDS) if field == 'labelText']
    if len(texts) > 0 and 'labelText' in config:
        filled['labelText'] = binLabelLayout.sharedText(config['labelText'], texts)
    return filled
