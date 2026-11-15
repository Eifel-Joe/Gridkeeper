import adsk.core, adsk.fusion, traceback
import os
import math
import copy

from ...lib import fusion360utils as futil
from . import const, combineUtils, faceUtils, commonUtils, sketchUtils, extrudeUtils, baseGenerator, edgeUtils, filletUtils, geometryUtils, patternUtils, binShape
from .binBodyCutoutGenerator import createGridfinityBinBodyCutout
from .binBodyCutoutGeneratorInput import BinBodyCutoutGeneratorInput
from .baseGeneratorInput import BaseGeneratorInput
from .binBodyGeneratorInput import BinBodyGeneratorInput, BinBodyCompartmentDefinition
from .binBodyTabGeneratorInput import BinBodyTabGeneratorInput
from .binBodyTabGenerator import createGridfinityBinBodyTab, createTabHollowCuts, TabCavity, TabWallOpenings, TabHollowCuts
from .labelGenerator import BinLabelDefinition, BinLabelInput, createLabel, LABEL_STYLE_EMBOSSED, LABEL_STYLE_ENGRAVED, LABEL_STYLE_CULLENECT
from . import cullenect, binLabelLayout
from .cullenectSocketGenerator import createCullenectSocket, SocketPlacement
from .binBodyLipGeneratorInput import BinBodyLipGeneratorInput
from .binBodyLipGenerator import createGridfinityBinBodyLip, createStackedFootCutters
from .raisedDividers import DividerSegment, FilletCorner, filletCorners, isCornerChainEdge, chainRuns, runOffset, cornerPlaneAxes
from .dim import Dim, valueInput, applyTo
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

def uniformCompartments(countX, countY):
    compartments: list[BinBodyCompartmentDefinition] = []
    for i in range(countX):
        for j in range(countY):
            compartments.append(BinBodyCompartmentDefinition(i, j, 1, 1))
    return compartments

def patternCompartments(entities, input, spacingX, spacingY, targetComponent, name, computeOption=None):
    pattern = patternUtils.recPatternGrid(
        commonUtils.objectCollectionFromList(entities),
        (input.compartmentsByX, input.compartmentsByY),
        (spacingX, spacingY),
        targetComponent,
        computeOption,
        name=name,
    )
    return pattern

def patternCompartmentBodies(bodies, input, spacingX, spacingY, targetComponent, name):
    if not bodies or input.compartmentsByX * input.compartmentsByY == 1:
        return bodies
    pattern = patternCompartments(bodies, input, spacingX, spacingY, targetComponent, name)
    return bodies + list(pattern.bodies)


def binBodyTopHeight(input: BinBodyGeneratorInput) -> Dim:
    """Height of the body top above the base top"""
    if input.heightUnit.value >= const.BIN_BASE_HEIGHT:
        # the first unit holds the base, only its part above the base height belongs to the body
        return input.binHeight * input.heightUnit - Dim.length(const.BIN_BASE_HEIGHT)
    return (input.binHeight - Dim.number(1)) * input.heightUnit

def createGridfinityBinBody(
    input: BinBodyGeneratorInput,
    targetComponent: adsk.fusion.Component,
) -> tuple[adsk.fusion.BRepBody, list[adsk.fusion.BRepBody], list[tuple[int, int, SocketPlacement]]]:
    """The bin body, the bodies of its colored labels, see createLabel, and its Cullenect pockets with the index of
    their compartment and the number of compartments, see cullenect.pocketJointOriginName"""
    bodyWidth = input.baseWidth * input.binWidth - Dim.length(input.xyClearance * 2)
    bodyLength = input.baseLength * input.binLength - Dim.length(input.xyClearance * 2)
    wall = Dim.length(input.wallThickness)
    # everything sitting on the bin top uses this dim, so it follows the height parameters
    binBodyTotalHeight = binBodyTopHeight(input)
    features: adsk.fusion.Features = targetComponent.features
    binBodyExtrude = extrudeUtils.createBox(
        bodyWidth,
        bodyLength,
        binBodyTotalHeight,
        targetComponent,
        targetComponent.xYConstructionPlane,
        name='Bin body',
    )
    binBody = binBodyExtrude.bodies.item(0)
    binBody.name = 'Bin body'

    bodiesToMerge: list[adsk.fusion.BRepBody] = []
    bodiesToSubtract: list[adsk.fusion.BRepBody] = []
    raisedCorners: list[tuple[FilletCorner, tuple[Dim, Dim]]] = []
    raisedCornersBottomZ = None
    # hollow tabs are cut once joined, the walls behind them close the hollows
    tabHollowCuts: list[adsk.fusion.BRepBody] = []

    # round corners
    filletUtils.filletEdgesByLength(
        binBodyExtrude.faces,
        input.binCornerFilletRadius,
        binBodyTotalHeight.value,
        targetComponent,
        name='Bin body corner fillets',
    )

    if input.hasLip:
        lipOriginPoint = adsk.core.Point3D.create(0, 0, binBodyTotalHeight.value)
        lipInput = BinBodyLipGeneratorInput()
        lipInput.baseLength = input.baseLength
        lipInput.baseWidth = input.baseWidth
        lipInput.binLength = input.binLength
        lipInput.binWidth = input.binWidth
        lipInput.hasLipNotches = input.hasLipNotches
        lipInput.xyClearance = input.xyClearance
        lipInput.binCornerFilletRadius = input.binCornerFilletRadius
        lipInput.origin = lipOriginPoint
        lipInput.originZ = binBodyTotalHeight
        lipInput.shapeCells = input.shapeCells
        lipInput.shapeCellsPerFoot = input.shapeCellsPerFoot
        lipBody = createGridfinityBinBodyLip(lipInput, targetComponent)

        hasLipBottomChamfer = input.hasLipBottomChamfer and input.wallThickness < const.BIN_LIP_WALL_THICKNESS
        if hasLipBottomChamfer and input.shapeCells is not None:
            # the inside of the walls widening at 45 degrees into the lip, so it doesn't overhang the cavity
            combineUtils.cutBody(
                lipBody,
                commonUtils.objectCollectionFromList([createShapeLipBottomChamfer(input, binBodyTotalHeight, targetComponent)]),
                targetComponent,
                name='Lip bottom chamfer cut',
            )
        elif hasLipBottomChamfer:
            lipBottomChamferSize = max(const.BIN_BODY_CUTOUT_BOTTOM_FILLET_RADIUS, input.binCornerFilletRadius - input.wallThickness)
            lipBottomChamferExtrude = extrudeUtils.createBoxAtPoint(
                bodyWidth - wall * 2,
                (bodyLength - wall - Dim.length(const.BIN_LIP_WALL_THICKNESS - input.xyClearance)) if input.hasScoop else (bodyLength - wall * 2),
                lipBottomChamferSize,
                targetComponent,
                adsk.core.Point3D.create(
                    input.wallThickness,
                    (const.BIN_LIP_WALL_THICKNESS - input.xyClearance) if input.hasScoop else input.wallThickness,
                    lipOriginPoint.z,
                ),
                binBodyTotalHeight,
                name='Lip bottom chamfer box',
            )
            filletUtils.filletEdgesByLength(
                lipBottomChamferExtrude.faces,
                lipBottomChamferSize,
                lipBottomChamferSize,
                targetComponent,
                name='Lip bottom chamfer box fillets',
            )
            lipBottomChamferExtrudeTopFace = faceUtils.getTopFace(lipBottomChamferExtrude.bodies.item(0))
            scoopSideEdge = min([edge for edge in lipBottomChamferExtrudeTopFace.edges if geometryUtils.isCollinearToX(edge)], key=lambda x: x.boundingBox.minPoint.y)

            edgesToChamfer = list(scoopSideEdge.tangentiallyConnectedEdges)[3:] if input.hasScoop else scoopSideEdge.tangentiallyConnectedEdges
            chamferFeatures: adsk.fusion.ChamferFeatures = features.chamferFeatures
            bottomLipChamferInput = chamferFeatures.createInput2()
            bottomLipChamferEdges = commonUtils.objectCollectionFromList(edgesToChamfer)
            bottomLipChamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
                bottomLipChamferEdges,
                adsk.core.ValueInput.createByReal(lipBottomChamferSize),
                False)
            chamferFeatures.add(bottomLipChamferInput).name = 'Lip bottom chamfer'
            combineUtils.cutBody(lipBody, commonUtils.objectCollectionFromList(lipBottomChamferExtrude.bodies), targetComponent, name='Lip bottom chamfer cut')

        bodiesToMerge.append(lipBody)

    if not input.isSolid:
        compartmentsMinX = wall
        compartmentsMaxX = bodyWidth - wall
        compartmentsMinY = Dim.length(const.BIN_LIP_WALL_THICKNESS - input.xyClearance) if input.hasLip and input.hasScoop else wall
        compartmentsMaxY = bodyLength - wall

        totalCompartmentsWidth = compartmentsMaxX - compartmentsMinX
        totalCompartmentsLength = compartmentsMaxY - compartmentsMinY

        compartmentWidthUnit = (totalCompartmentsWidth - wall * (input.compartmentsByX - 1)) / input.compartmentsByX
        compartmentLengthUnit = (totalCompartmentsLength - wall * (input.compartmentsByY - 1)) / input.compartmentsByY

        def compartmentPlacement(compartment: BinBodyCompartmentDefinition) -> tuple[Dim, Dim, Dim, Dim]:
            """X, y, width and length of the compartment cavity"""
            return (
                compartmentsMinX + (compartmentWidthUnit + wall) * compartment.positionX,
                compartmentsMinY + (compartmentLengthUnit + wall) * compartment.positionY,
                compartmentWidthUnit * compartment.width + wall * (compartment.width - 1),
                compartmentLengthUnit * compartment.length + wall * (compartment.length - 1),
            )

        def tabPlacement(compartmentX: Dim, compartmentY: Dim, compartmentLength: Dim) -> tuple[Dim, Dim, Dim]:
            """X and y of the tab's back top corner, along the compartment's back wall, and its length"""
            return (
                compartmentX + input.baseWidth * max(0, min(input.tabPosition, input.binWidth - input.tabLength)),
                compartmentY + compartmentLength,
                input.baseWidth * max(0, min(input.tabLength, input.binWidth)),
            )

        useCompartmentPattern = input.isUniformCompartments and len(input.compartments) > 1
        compartmentsToBuild = input.compartments[:1] if useCompartmentPattern else input.compartments
        for compartmentIndex, compartment in enumerate(compartmentsToBuild):
            compartmentName = 'Compartment' if len(compartmentsToBuild) == 1 else f'Compartment {compartmentIndex + 1}'
            (compartmentX, compartmentY, compartmentWidth, compartmentLength) = compartmentPlacement(compartment)
            # full depth compartments keep their floor thickness, shallower ones keep their depth from the top
            fullCompartmentDepth = binBodyTotalHeight - Dim.length(const.BIN_COMPARTMENT_BOTTOM_THICKNESS)
            compartmentDepth = fullCompartmentDepth if compartment.depth >= fullCompartmentDepth.value else compartment.depth

            compartmentTabInput = BinBodyTabGeneratorInput()
            (tabOriginX, tabOriginY, tabLength) = tabPlacement(compartmentX, compartmentY, compartmentLength)
            compartmentTabInput.origin = adsk.core.Point3D.create(tabOriginX.value, tabOriginY.value, binBodyTotalHeight.value)
            compartmentTabInput.originX = tabOriginX
            compartmentTabInput.originY = tabOriginY
            compartmentTabInput.originZ = binBodyTotalHeight
            compartmentTabInput.length = tabLength
            compartmentTabInput.width = input.tabWidth
            compartmentTabInput.overhangAngle = input.tabOverhangAngle
            compartmentTabInput.labelAngle = input.tabTopAngle
            compartmentTabInput.topClearance = tabTopClearance(input.labelStyle)
            # a hollow tab of a single compartment is opened through the outer walls of the bin, with more compartments
            # the hollows are left closed
            tabOpenings = None
            if input.isTabHollow and len(input.compartments) == 1:
                tabOpenings = TabWallOpenings(
                    input.wallThickness * 2,
                    back=True,
                    minXSide=input.isTabOpenThroughSides,
                    maxXSide=input.isTabOpenThroughSides,
                )

            [compartmentMerges, compartmentCuts, compartmentHollowCuts] = createCompartment(
                input.wallThickness,
                compartmentX,
                compartmentY,
                binBodyTotalHeight,
                compartmentWidth,
                compartmentLength,
                compartmentDepth,
                input.binCornerFilletRadius - input.wallThickness,
                input.hasScoop,
                input.scoopMaxRadius,
                input.hasTab,
                compartmentTabInput,
                hollowTabWallThickness(input.wallThickness, input.labelStyle) if input.isTabHollow else None,
                tabOpenings,
                targetComponent,
                name=compartmentName,
            )
            if useCompartmentPattern:
                # These cavities are identical and disjoint, so copy their cut faces instead
                # of creating every cutter body and asking Combine to intersect them all.
                # Optimized compute assumes every instance meets the same surrounding geometry;
                # revisit if uniform compartments ever stop being identical.
                # Patterning a cut feature requires design history, which entry.py enforces.
                seedCut = combineUtils.cutBody(
                    binBody, commonUtils.objectCollectionFromList(compartmentCuts), targetComponent, name='Compartment cut')
                patternCompartments(
                    [seedCut], input,
                    compartmentWidthUnit + wall,
                    compartmentLengthUnit + wall,
                    targetComponent, 'Compartment cuts pattern',
                    adsk.fusion.PatternComputeOptions.OptimizedPatternCompute,
                )
                compartmentCuts = []
                compartmentMerges = patternCompartmentBodies(
                    compartmentMerges, input,
                    compartmentWidthUnit + wall,
                    compartmentLengthUnit + wall,
                    targetComponent, 'Label tabs pattern',
                )
                compartmentHollowCuts = TabHollowCuts(hollow=patternCompartmentBodies(
                    compartmentHollowCuts.hollow, input,
                    compartmentWidthUnit + wall,
                    compartmentLengthUnit + wall,
                    targetComponent, 'Label tab hollows pattern',
                ))
            bodiesToSubtract.extend(compartmentCuts)
            tabHollowCuts.extend(compartmentHollowCuts.all())
            bodiesToMerge.extend(compartmentMerges)

        if len(input.compartments) > 1:
            compartmentsTopClearance = createCompartmentCutout(
                input.wallThickness,
                compartmentsMinX,
                compartmentsMinY,
                binBodyTotalHeight,
                bodyWidth - wall * 2,
                bodyLength - wall - compartmentsMinY,
                const.BIN_TAB_TOP_CLEARANCE,
                input.binCornerFilletRadius - input.wallThickness,
                False,
                0,
                False,
                targetComponent,
                name='Compartments top clearance',
            )
            bodiesToSubtract.append(compartmentsTopClearance)

        if input.hasLip and len(input.raisedDividers) > 0:
            # p83: the corners the raised dividers make, filleted once the bin is in one body
            raisedCorners = raisedDividerCorners(
                input.raisedDividers,
                (compartmentsMinX, compartmentsMinY),
                (compartmentWidthUnit + wall, compartmentLengthUnit + wall),
                (input.compartmentsByX, input.compartmentsByY),
                wall,
            )
            raisedCornersBottomZ = binBodyTotalHeight - Dim.length(const.BIN_TAB_TOP_CLEARANCE)
            bodiesToMerge.extend(createRaisedDividers(
                input.raisedDividers,
                (compartmentsMinX, compartmentsMinY),
                (compartmentWidthUnit + wall, compartmentLengthUnit + wall),
                (input.compartmentsByX, input.compartmentsByY),
                wall,
                binBodyTotalHeight,
                lipInput,
                targetComponent,
            ))

    if len(bodiesToSubtract) > 0:
        combineUtils.cutBody(
            binBody,
            commonUtils.objectCollectionFromList(bodiesToSubtract),
            targetComponent,
            name='Bin body cutouts cut',
        )
    if len(bodiesToMerge) > 0:
        combineUtils.joinBodies(
            binBody,
            commonUtils.objectCollectionFromList(bodiesToMerge),
            targetComponent,
            name='Bin body lip and tabs join',
        )
    if len(tabHollowCuts) > 0:
        combineUtils.cutBody(
            binBody,
            commonUtils.objectCollectionFromList(tabHollowCuts),
            targetComponent,
            name='Label tab hollows cut',
        )

    if len(raisedCorners) > 0:
        roundRaisedDividerCorners(
            binBody,
            raisedCorners,
            (input.compartmentsByX, input.compartmentsByY),
            input.wallThickness,
            raisedCornersBottomZ,
            compartmentCutoutFilletRadius(input.binCornerFilletRadius - input.wallThickness),
            lipInput,
            targetComponent,
        )

    labelBodies: list[adsk.fusion.BRepBody] = []
    pockets: list[tuple[int, int, SocketPlacement]] = []
    if not input.isSolid and input.hasTab:
        # every compartment gets its own label, also where the tabs come from a pattern. A Cullenect socket goes into
        # every tab, the inserts carry the labels
        isCullenect = input.labelStyle == LABEL_STYLE_CULLENECT
        for compartmentIndex, compartment in enumerate(input.compartments):
            if not isCullenect and (compartment.label is None or compartment.label.isEmpty):
                continue
            (compartmentX, compartmentY, compartmentWidth, compartmentLength) = compartmentPlacement(compartment)
            (tabOriginX, tabOriginY, tabLength) = tabPlacement(compartmentX, compartmentY, compartmentLength)
            # tabs are trimmed to their compartment, as an expression (p60)
            (labelMinX, labelMaxX) = binLabelLayout.labelSpan(tabOriginX, tabLength, compartmentX, compartmentWidth)
            labelName = 'Label' if len(input.compartments) == 1 else f'Compartment {compartmentIndex + 1} label'
            if isCullenect:
                if not cullenect.socketFitsDepth(compartmentLength.value, input.tabWidth, input.cullenectSocketOffset):
                    # the tab fills the compartment, the socket would cut into the divider in front
                    commonUtils.debugLog(f'{labelName}: compartment {compartmentLength.value * 10:.2f} mm long, too short for a Cullenect socket')
                    continue
                pocket = createCullenectSocket(
                    labelMinX,
                    labelMaxX,
                    tabOriginY,
                    input.tabWidth,
                    binBodyTotalHeight - Dim.length(tabTopClearance(input.labelStyle)),
                    input.cullenectUnitWidth,
                    input.cullenectSocketOffset,
                    input.tabOverhangAngle,
                    binBody,
                    targetComponent,
                    name=labelName,
                )
                if pocket is not None:
                    pockets.append((compartmentIndex, len(input.compartments), pocket))
                continue
            labelBodies += createTabLabel(
                compartment.label,
                input.labelStyle,
                input.isLabelBold,
                labelMinX,
                labelMaxX,
                tabOriginY,
                input.tabWidth,
                binBodyTotalHeight,
                binBody,
                targetComponent,
                input.tabTopAngle,
                input.labelColor,
                name=labelName,
                textOccurrence=input.textOccurrence,
                targetOccurrence=input.binOccurrence,
                binPlacement=input.binPlacement,
            )

    return (binBody, labelBodies, pockets)

def createRaisedDividers(
    segments: list[DividerSegment],
    compartmentsMin: tuple[Dim, Dim],
    pitch: tuple[Dim, Dim],
    counts: tuple[int, int],
    wall: Dim,
    binBodyTotalHeight: Dim,
    lipInput: BinBodyLipGeneratorInput,
    targetComponent: adsk.fusion.Component,
) -> list[adsk.fusion.BRepBody]:
    """
    Divider walls on grid lines from below the compartments top clearance up to the top of the lip, cut by the feet of
    a bin stacked on top like a notched lip, so they run out in the lip's profile. A wall a little off its grid line,
    as dividers over more units are, gets the part that fits. Segments reach a wall further where they meet a
    crossing divider, and half a wall into the outer walls, which keeps every box corner off the sketch axes
    """
    boxes: list[adsk.fusion.BRepBody] = []
    bottomZ = binBodyTotalHeight - Dim.length(const.BIN_TAB_TOP_CLEARANCE)
    height = const.BIN_TAB_TOP_CLEARANCE + const.BIN_LIP_EXTRA_HEIGHT - const.BIN_LIP_TOP_RECESS_HEIGHT
    for (index, segment) in enumerate(segments):
        # across is the axis the wall stands on, along the one it runs on
        (across, along) = (0, 1) if segment.axis == 'x' else (1, 0)
        wallStart = compartmentsMin[across] + pitch[across] * segment.line - wall
        startReach = wall / 2 if segment.start == 0 else wall
        endReach = wall / 2 if segment.end == counts[along] else wall
        # the first cavity starts at the min, the last one ends a wall short of the next pitch
        runStart = compartmentsMin[along] + pitch[along] * segment.start - startReach
        runLength = pitch[along] * (segment.end - segment.start) - wall + startReach + endReach
        (originX, originY, width, length) = (wallStart, runStart, wall, runLength) if segment.axis == 'x' else (runStart, wallStart, runLength, wall)
        box = extrudeUtils.createBoxAtPoint(
            width,
            length,
            height,
            targetComponent,
            adsk.core.Point3D.create(originX.value, originY.value, bottomZ.value),
            bottomZ,
            originX=originX,
            originY=originY,
            name=f'Raised divider {index + 1}',
        )
        boxes.append(box.bodies.item(0))
    # Each box is cut on its own and every body is returned, the bin joins them all. Root cause of p82: the boxes were
    # joined into one body first, but Fusion's join leaves bodies that don't touch apart, so parallel walls came back
    # as one body, the others stayed loose in the design (two boxes 3 cm apart, joined: two bodies, shown in Fusion).
    # Each box stands on a compartment wall and so touches the bin. The cutters are kept until the last cut takes them
    cutters = createStackedFootCutters(lipInput, targetComponent, name='Raised divider foot cutout')
    dividers: list[adsk.fusion.BRepBody] = []
    for (index, box) in enumerate(boxes):
        isLast = index == len(boxes) - 1
        cut = combineUtils.cutBody(
            box,
            commonUtils.objectCollectionFromList(cutters),
            targetComponent,
            isKeepToolBodies=not isLast,
            name=f'Raised divider {index + 1} foot cut',
        )
        # a cut keeping its tools lists them among its bodies too (shown in Fusion), the last cut takes them, so a
        # join of them later would lose its tools
        dividers.extend(body for body in cut.bodies if all(body != cutter for cutter in cutters))
    return dividers

# Parts of the corner fillet radius tried in turn where a corner can't be swept and Fusion can't close a fillet of the
# full one (ASM_BL_CAP_COMPLEX, shown in Fusion): walls of 2 and 3 mm stick out past the grid line and are cut by the
# feet of a stacked bin at the top, a 0.4 mm wall leaves too little divider for a 3.3 mm fillet. 80 % rounds those of
# 0.4 and 2 mm, 40 % 3 mm walls
RAISED_CORNER_FILLET_FALLBACKS = (1.0, 0.8, 0.6, 0.4)

def raisedDividerCorners(
    segments: list[DividerSegment],
    compartmentsMin: tuple[Dim, Dim],
    pitch: tuple[Dim, Dim],
    counts: tuple[int, int],
    wall: Dim,
) -> list[tuple[FilletCorner, tuple[Dim, Dim]]]:
    """
    The cell corners the raised dividers make, each with where the corner of the cavity is: on the low side of a cell
    at its start, on the high side a wall short of the next one
    """
    corners = []
    for corner in filletCorners(segments, counts[0], counts[1]):
        x = compartmentsMin[0] + pitch[0] * (corner.column if corner.sideX == -1 else corner.column + 1)
        y = compartmentsMin[1] + pitch[1] * (corner.row if corner.sideY == -1 else corner.row + 1)
        corners.append((corner, (x - wall if corner.sideX == 1 else x, y - wall if corner.sideY == 1 else y)))
    return corners

def raisedCornerChain(
    binBody: adsk.fusion.BRepBody,
    corner: FilletCorner,
    cornerAt: tuple[float, float],
    counts: tuple[int, int],
    wallThickness: float,
    bottomZ: float,
) -> list[adsk.fusion.BRepEdge]:
    """The edges of the body a corner goes up along, see isCornerChainEdge"""
    edges = []
    for edge in binBody.edges:
        if not isinstance(edge.geometry, adsk.core.Line3D):
            continue
        start = edge.startVertex.geometry
        end = edge.endVertex.geometry
        if isCornerChainEdge(
            corner, cornerAt, counts[0], counts[1],
            # the lip reaches into the compartment by less than its top section
            wall=wallThickness, lipOverhang=const.BIN_BASE_TOP_SECTION_HEIGH, bottomZ=bottomZ,
            start=(start.x, start.y, start.z), end=(end.x, end.y, end.z),
        ):
            edges.append(edge)
    return edges

def roundRaisedDividerCorners(
    binBody: adsk.fusion.BRepBody,
    corners: list[tuple[FilletCorner, tuple[Dim, Dim]]],
    counts: tuple[int, int],
    wallThickness: float,
    bottomZ: Dim,
    cornerFilletRadius: float,
    lipInput: BinBodyLipGeneratorInput,
    targetComponent: adsk.fusion.Component,
):
    """
    p83: rounds every corner of a raised divider from the top of the compartment's corner fillet up to the top, over
    the outer wall, the chamfer under the lip and the lip, cast in one piece with the corner below, the chamfer running
    on round it. Root cause of the sharp corner: the raised divider is a box joined on above the compartment cuts,
    which alone carry the corner fillets, so they stopped at the old top of the dividers.
    Each corner's section, the square of the radius less its circle, the very section of the corner below, is swept
    up along the edges of its corner without turning, so it follows the wall in and out and meets the corner below
    without a step. Rejected, all shown in Fusion: fill pieces extruded up and cut by the lip's inner face (sharp
    corner in the lip) or by the feet of a stacked bin (undercuts at the top); a rolling ball fillet up the edges (a
    sickle of 0.36 mm2 left on the corner below, found by Nutzer: the ball can't follow the 0.5 mm of wall under the
    chamfer, it runs into the chamfer).
    The sweeps are cut by the feet of a bin stacked on top, so it still stacks. A wall thicker than the lip leaves a level
    ledge under it, the corner's edges fall in runs there, each swept on its own and only the top one cut by the feet
    (round 15, p101). A corner whose edges make no path or no runs over a ledge, or that Fusion can't sweep, is filleted
    instead, see filletRaisedDividerCorner
    """
    sketch = raisedCornerSectionsSketch(corners, bottomZ, Dim.length(cornerFilletRadius), targetComponent)
    sweeps: list[tuple[int, FilletCorner, tuple[float, float], list[adsk.fusion.BRepBody]]] = []
    toFillet: list[tuple[int, FilletCorner, tuple[float, float]]] = []
    for (index, (corner, cornerAt)) in enumerate(corners):
        at = (cornerAt[0].value, cornerAt[1].value)
        name = f'Raised divider corner {index + 1}'
        edges = raisedCornerChain(binBody, corner, at, counts, wallThickness, bottomZ.value)
        # the edges lie in the face of the raised divider, the path runs across its other axis
        (_, otherAxis) = cornerPlaneAxes(corner, counts[0])
        inPlane = [
            (
                (edge.startVertex.geometry.asArray()[otherAxis], edge.startVertex.geometry.z),
                (edge.endVertex.geometry.asArray()[otherAxis], edge.endVertex.geometry.z),
            )
            for edge in edges
        ]
        runs = chainRuns(inPlane)
        profile = sectionProfile(sketch, at)
        if runs is None or profile is None:
            toFillet.append((index, corner, at))
            continue
        # A wall thicker than the lip leaves a level ledge under the lip, the chain falls in two runs (round 15, p101).
        # Each is swept on its own with the corner's section at its lowest point, the one above the ledge moved over by
        # the ledge and up to it, both by constant offsets: they follow the grid and height parameters like the first
        bodies = []
        # sweeps and run section sketches made for the corner, they go again when it is filleted after all
        made = []
        for (runIndex, run) in enumerate(runs):
            runProfile = profile
            if runIndex > 0:
                (aside, rise) = runOffset(inPlane, runs, runIndex)
                shift = Dim.length(aside)
                runAt = (cornerAt[0] + shift, cornerAt[1]) if otherAxis == 0 else (cornerAt[0], cornerAt[1] + shift)
                runSketch = raisedCornerSectionsSketch([(corner, runAt)], bottomZ + Dim.length(rise), Dim.length(cornerFilletRadius), targetComponent, name=f'{name} run {runIndex + 1}')
                made.append(runSketch)
                runProfile = sectionProfile(runSketch, (runAt[0].value, runAt[1].value))
                if runProfile is None:
                    break
            try:
                path = targetComponent.features.createPath(commonUtils.objectCollectionFromList([edges[i] for i in run]), False)
                sweepInput = targetComponent.features.sweepFeatures.createInput(runProfile, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                sweepInput.orientation = adsk.fusion.SweepOrientationTypes.ParallelOrientationType
                sweep = targetComponent.features.sweepFeatures.add(sweepInput)
            except RuntimeError as error:
                commonUtils.debugLog(f'{name}: sweep of run {runIndex + 1} failed, {error}')
                break
            sweep.name = f'{name} sweep' if len(runs) == 1 else f'{name} sweep {runIndex + 1}'
            made.append(sweep)
            if sweep.bodies.count != 1:
                # one section along one path is one body, anything else isn't the corner
                commonUtils.debugLog(f'{name}: sweep of run {runIndex + 1} made {sweep.bodies.count} bodies')
                sweep.deleteMe()
                break
            bodies.append(sweep.bodies.item(0))
        if len(bodies) != len(runs):
            # the runs swept so far go with their sketches and planes, the corner is filleted as a whole
            for item in reversed(made):
                plane = item.referencePlane if isinstance(item, adsk.fusion.Sketch) else None
                if item.isValid:
                    item.deleteMe()
                if plane is not None and plane.isValid:
                    plane.deleteMe()
            toFillet.append((index, corner, at))
            continue
        sweeps.append((index, corner, at, bodies))
    if len(sweeps) > 0:
        # The corners stay sharp at worst, never the bin: a cut or join Fusion fails on leaves their corners to the
        # fillets. The cutters are kept until the last cut, see createRaisedDividers
        cutters = createStackedFootCutters(lipInput, targetComponent, name='Raised divider corners foot cutout')
        rounded: list[adsk.fusion.BRepBody] = []
        # the corners whose pieces are in rounded
        joined: list[tuple[int, FilletCorner, tuple[float, float]]] = []
        # Below a ledge the run stays as it is: the feet of a bin stacked on top can't reach there past the thick wall,
        # whose corner fillet goes up to the ledge uncut, and cut it ended 0.104 mm under the ledge, a level face of
        # 0.6 mm2 at every corner of a 3 mm wall (round 15, p101, try B)
        for (position, (index, corner, at, bodies)) in enumerate(sweeps):
            # only the top run is cut, a corner goes in only with it, else it's filleted as a whole
            try:
                cut = combineUtils.cutBody(
                    bodies[-1],
                    commonUtils.objectCollectionFromList(cutters),
                    targetComponent,
                    isKeepToolBodies=position < len(sweeps) - 1,
                    name=f'Raised divider corner {index + 1} foot cut',
                )
            except RuntimeError as error:
                commonUtils.debugLog(f'Raised divider corner {index + 1}: foot cut failed, {error}')
                for body in bodies:
                    # no loose pieces of a corner that is filleted
                    targetComponent.features.removeFeatures.add(body)
                if position == len(sweeps) - 1:
                    # the last cut was to use up the cutters, they mustn't stay in the bin (review round 15)
                    for cutter in cutters:
                        targetComponent.features.removeFeatures.add(cutter)
                toFillet.append((index, corner, at))
                continue
            # a cut keeping its tools lists them among its bodies too
            rounded.extend(bodies[:-1])
            rounded.extend(piece for piece in cut.bodies if all(piece != cutter for cutter in cutters))
            joined.append((index, corner, at))
        if len(rounded) > 0:
            try:
                combineUtils.joinBodies(
                    binBody,
                    commonUtils.objectCollectionFromList(rounded),
                    targetComponent,
                    name='Raised divider corners join',
                )
            except RuntimeError as error:
                commonUtils.debugLog(f'Raised divider corners: join failed, {error}')
                # their pieces go, those corners are filleted, the ones already to be filleted once (review round 15)
                for piece in rounded:
                    targetComponent.features.removeFeatures.add(piece)
                toFillet.extend(joined)
    for (index, corner, at) in toFillet:
        filletRaisedDividerCorner(binBody, index, corner, at, counts, wallThickness, bottomZ.value, cornerFilletRadius, targetComponent)

def raisedCornerSectionsSketch(
    corners: list[tuple[FilletCorner, tuple[Dim, Dim]]],
    bottomZ: Dim,
    radius: Dim,
    targetComponent: adsk.fusion.Component,
    name: str = 'Raised divider corners',
) -> adsk.fusion.Sketch:
    """
    The section of every corner where the corner fillet below it ends: the square of the radius in the corner less the
    circle around its inner corner. All in one sketch, each corner placed by dims from the compartment grid, so they
    follow the grid parameters
    """
    planeInput: adsk.fusion.ConstructionPlaneInput = targetComponent.constructionPlanes.createInput()
    planeInput.setByOffset(targetComponent.xYConstructionPlane, valueInput(bottomZ))
    plane = targetComponent.constructionPlanes.add(planeInput)
    plane.name = f'{name} plane'
    sketch: adsk.fusion.Sketch = targetComponent.sketches.add(plane)
    sketch.name = f'{name} sketch'
    constraints: adsk.fusion.GeometricConstraints = sketch.geometricConstraints
    dimensions: adsk.fusion.SketchDimensions = sketch.sketchDimensions
    r = radius.value
    with sketchUtils.deferSketchCompute(sketch):
        for (corner, (cornerX, cornerY)) in corners:
            # into the cell, worked out in the model and turned into the sketch, whose axes may run the other way
            (dirX, dirY) = (-corner.sideX, -corner.sideY)
            (x, y, z) = (cornerX.value, cornerY.value, bottomZ.value)
            def onSketch(pointX, pointY):
                point = sketch.modelToSketchSpace(adsk.core.Point3D.create(pointX, pointY, z))
                point.z = 0
                return point
            cornerPoint = onSketch(x, y)
            alongX = onSketch(x + dirX * r, y)
            alongY = onSketch(x, y + dirY * r)
            center = onSketch(x + dirX * r, y + dirY * r)
            # a quarter counterclockwise on the sketch, from the end along x where that turns the right way, else from
            # the end along y: a negative sweep doesn't go clockwise, it gave arcs on the far side (shown in Fusion)
            turn = (alongX.x - center.x) * (alongY.y - center.y) - (alongX.y - center.y) * (alongY.x - center.x)
            arc = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(center, alongX if turn > 0 else alongY, math.pi / 2)
            (endAlongX, endAlongY) = (arc.startSketchPoint, arc.endSketchPoint) if turn > 0 else (arc.endSketchPoint, arc.startSketchPoint)
            lineX = sketch.sketchCurves.sketchLines.addByTwoPoints(cornerPoint, endAlongX)
            lineY = sketch.sketchCurves.sketchLines.addByTwoPoints(lineX.startSketchPoint, endAlongY)
            constraints.addHorizontal(lineX)
            constraints.addVertical(lineY)
            constraints.addTangent(arc, lineX)
            # the corner and the arc's center both placed from the origin, a center square across from the corner, so
            # the section can't flip to the other side of the wall or the divider: with the lengths and two tangents
            # alone that is a solution too, and Fusion took it for some corners (shown in Fusion). The tangent at the
            # end along x settles the radius, the end along y follows. Sketch distance dimensions are unsigned
            centerX = cornerX + radius * dirX
            centerY = cornerY + radius * dirY
            for (point, value, orientation, textAt) in (
                (lineX.startSketchPoint, cornerX, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, onSketch(x, y - dirY * r)),
                (lineX.startSketchPoint, cornerY, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, onSketch(x - dirX * r, y)),
                (arc.centerSketchPoint, centerX, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, onSketch(x + dirX * r, y + dirY * 2 * r)),
                (arc.centerSketchPoint, centerY, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, onSketch(x + dirX * 2 * r, y + dirY * r)),
            ):
                applyTo(dimensions.addDistanceDimension(sketch.originPoint, point, orientation, textAt, True).parameter, value.abs())
    return sketch

def sectionProfile(sketch: adsk.fusion.Sketch, cornerAt: tuple[float, float]) -> adsk.fusion.Profile | None:
    """The section of the corner at cornerAt among the sketch's profiles, the one whose box has it on a corner"""
    point = sketch.modelToSketchSpace(adsk.core.Point3D.create(cornerAt[0], cornerAt[1], sketch.origin.z))
    cornerAt = (point.x, point.y)
    for index in range(sketch.profiles.count):
        profile = sketch.profiles.item(index)
        box = profile.boundingBox
        boxCorners = [(box.minPoint.x, box.minPoint.y), (box.minPoint.x, box.maxPoint.y), (box.maxPoint.x, box.minPoint.y), (box.maxPoint.x, box.maxPoint.y)]
        if any(abs(x - cornerAt[0]) < 1e-4 and abs(y - cornerAt[1]) < 1e-4 for (x, y) in boxCorners):
            return profile
    return None

def filletRaisedDividerCorner(
    binBody: adsk.fusion.BRepBody,
    index: int,
    corner: FilletCorner,
    cornerAt: tuple[float, float],
    counts: tuple[int, int],
    wallThickness: float,
    bottomZ: float,
    cornerFilletRadius: float,
    targetComponent: adsk.fusion.Component,
):
    """
    A corner that can't be swept, rounded by a rolling ball fillet up its edges instead, a hair under the corner
    fillet's radius: of the same radius both lie on one cylinder and Fusion fails on one side (ASM_INCONS_FACE, shown
    in Fusion). One Fusion can't close gets a smaller radius, see RAISED_CORNER_FILLET_FALLBACKS, one it can't round
    at all stays sharp, the bin is still good to print and stack
    """
    name = f'Raised divider corner {index + 1} fillet'
    edges = raisedCornerChain(binBody, corner, cornerAt, counts, wallThickness, bottomZ)
    if len(edges) == 0:
        commonUtils.debugLog(f'{name}: no edges found')
        return
    radius = cornerFilletRadius - 0.005
    for factor in RAISED_CORNER_FILLET_FALLBACKS:
        filletInput = targetComponent.features.filletFeatures.createInput()
        filletInput.isRollingBallCorner = True
        filletInput.addConstantRadiusEdgeSet(
            commonUtils.objectCollectionFromList(edges),
            adsk.core.ValueInput.createByReal(radius * factor),
            False,
        )
        try:
            fillet = targetComponent.features.filletFeatures.add(filletInput)
        except RuntimeError as error:
            commonUtils.debugLog(f'{name}: fillet of {radius * factor * 10:.2f} mm failed, {error}')
            continue
        fillet.name = name
        return

def tabTopClearance(labelStyle: str) -> float:
    """Embossed labels stand on a tab lowered by their depth, so they keep the tab's clearance"""
    return const.BIN_TAB_TOP_CLEARANCE + (const.BIN_LABEL_DEPTH if labelStyle == LABEL_STYLE_EMBOSSED else 0)

def hollowTabWallThickness(wallThickness: float, labelStyle: str) -> float:
    """Hollow tabs take the wall thickness, thick enough for an engraved label or a socket not to cut through"""
    if labelStyle == LABEL_STYLE_ENGRAVED:
        return max(wallThickness, const.BIN_LABEL_DEPTH + const.BIN_TAB_HOLLOW_MIN_SKIN)
    if labelStyle == LABEL_STYLE_CULLENECT:
        return cullenect.hollowTabWallThickness(wallThickness)
    return wallThickness

def createTabLabel(
        definition: BinLabelDefinition,
        style: str,
        isBold: bool,
        minX: Dim,
        maxX: Dim,
        tabOriginY: Dim,
        tabWidth: float,
        tabOriginZ: Dim,
        targetBody: adsk.fusion.BRepBody,
        targetComponent: adsk.fusion.Component,
        tabTopAngle: float = 0,
        color: str = '',
        *,
        name: str,
        textOccurrence=None,
        targetOccurrence: adsk.fusion.Occurrence | None = None,
        binPlacement: tuple[float, float] = (0, 0),
    ) -> list[adsk.fusion.BRepBody]:
    """Label on the top face of a tab with its back top corner at the tab origin y and z, between the given x.
    On a tilted top the label is as long as the slope, so it still covers the tab width once turned down. The bodies
    of a colored label, see createLabel"""
    labelLength = tabWidth / math.cos(tabTopAngle)
    labelInput = BinLabelInput()
    labelInput.style = style
    labelInput.isBold = isBold
    labelInput.definition = definition
    labelInput.originX = minX
    labelInput.originY = tabOriginY - Dim.length(labelLength)
    labelInput.originZ = tabOriginZ - Dim.length(tabTopClearance(style))
    labelInput.width = maxX - minX
    labelInput.length = labelLength
    labelInput.tiltAngle = tabTopAngle
    labelInput.color = color
    return createLabel(labelInput, targetBody, targetComponent, name=name, textOccurrence=textOccurrence, targetOccurrence=targetOccurrence, binPlacement=binPlacement)


def createShapeLipBottomChamfer(
    input: BinBodyGeneratorInput,
    topZ: Dim,
    targetComponent: adsk.fusion.Component,
) -> adsk.fusion.BRepBody:
    """The inside of the walls of a shaped bin from the body top, narrowing at 45 degrees into the lip"""
    grid = baseGenerator.shapeGridInput(input.baseWidth, input.baseLength, input.xyClearance, input.shapeCellsPerFoot)
    offset = input.xyClearance + input.wallThickness
    # as tall as the plain bin's, its outer corners' radius, a hair less, the taper would close the corner arcs to a point
    height = compartmentCutoutFilletRadius(binShape.cornerRadius(True, grid.cornerFilletRadius, offset)) - 0.001
    planeInput: adsk.fusion.ConstructionPlaneInput = targetComponent.constructionPlanes.createInput()
    planeInput.setByOffset(targetComponent.xYConstructionPlane, valueInput(topZ))
    plane = targetComponent.constructionPlanes.add(planeInput)
    plane.name = 'Lip bottom chamfer plane'
    (sketch, _) = baseGenerator.createShapeOutlineSketch(
        input.shapeCells,
        grid,
        offset,
        plane,
        targetComponent,
        const.BIN_BODY_CUTOUT_BOTTOM_FILLET_RADIUS,
        name='Lip bottom chamfer',
    )
    chamfer = extrudeUtils.taperedExtrude(
        sketch.profiles.item(0),
        height,
        adsk.fusion.ExtentDirections.PositiveExtentDirection,
        targetComponent,
        name='Lip bottom chamfer',
    )
    return chamfer.bodies.item(0)

def createShapeCavity(
    cells: list[tuple[int, int]],
    baseConfiguration: BaseGeneratorInput,
    wallThickness: float,
    topZ: Dim,
    targetComponent: adsk.fusion.Component,
    *,
    name: str,
) -> adsk.fusion.BRepBody:
    """
    Cavity of a shaped bin, the outline moved in by the clearance and the wall from the top down to the floor,
    rounded along the bottom like a plain bin's compartment. Its outer corners are concentric with the bin's,
    see baseGenerator.createShapeOutlineSketch
    """
    planeInput: adsk.fusion.ConstructionPlaneInput = targetComponent.constructionPlanes.createInput()
    planeInput.setByOffset(targetComponent.xYConstructionPlane, valueInput(topZ))
    plane = targetComponent.constructionPlanes.add(planeInput)
    plane.name = f'{name} plane'
    offset = baseConfiguration.xyClearance + wallThickness
    # a plain bin's compartment corners don't go below the bottom fillet either, see compartmentCutoutFilletRadius
    (sketch, _) = baseGenerator.createShapeOutlineSketch(
        cells,
        baseConfiguration,
        offset,
        plane,
        targetComponent,
        const.BIN_BODY_CUTOUT_BOTTOM_FILLET_RADIUS,
        name=name,
    )
    cavityExtrude = extrudeUtils.simpleDistanceExtrude(
        sketch.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        topZ - Dim.length(const.BIN_COMPARTMENT_BOTTOM_THICKNESS),
        adsk.fusion.ExtentDirections.NegativeExtentDirection,
        [],
        targetComponent,
        name=name,
    )
    cavity = cavityExtrude.bodies.item(0)
    cavity.name = name
    # the same radius along the floor as up the outer corners, so they meet in a round corner like a plain bin's
    floorRadius = compartmentCutoutFilletRadius(binShape.cornerRadius(True, baseConfiguration.cornerFilletRadius, offset))
    filletUtils.createFillet(
        list(faceUtils.getBottomFace(cavity).edges),
        floorRadius,
        True,
        targetComponent,
        name=f'{name} bottom fillet',
    )
    return cavity

def compartmentCutoutFilletRadius(cornerFilletRadius: float) -> float:
    return max(const.BIN_BODY_CUTOUT_BOTTOM_FILLET_RADIUS, cornerFilletRadius)

def createCompartmentCutout(
        wallThickness: float,
        originX: Dim,
        originY: Dim,
        originZ: Dim,
        width: Dim,
        length: Dim,
        depth: Dim | float,
        cornerFilletRadius: float,
        hasScoop: bool,
        scoopMaxRadius: float,
        hasBottomFillet: bool,
        targetComponent: adsk.fusion.Component,
        *,
        name: str,
    ) -> adsk.fusion.BRepBody:

    innerCutoutFilletRadius = compartmentCutoutFilletRadius(cornerFilletRadius)
    innerCutoutInput = BinBodyCutoutGeneratorInput()
    innerCutoutInput.origin = adsk.core.Point3D.create(originX.value, originY.value, originZ.value)
    innerCutoutInput.originX = originX
    innerCutoutInput.originY = originY
    innerCutoutInput.originZ = originZ
    innerCutoutInput.width = width
    innerCutoutInput.length = length
    innerCutoutInput.height = depth
    innerCutoutInput.hasScoop = hasScoop
    innerCutoutInput.scoopMaxRadius = scoopMaxRadius
    innerCutoutInput.filletRadius = innerCutoutFilletRadius
    innerCutoutInput.hasBottomFillet = hasBottomFillet

    return createGridfinityBinBodyCutout(innerCutoutInput, targetComponent, name=name)

def createCompartment(
        wallThickness: float,
        originX: Dim,
        originY: Dim,
        originZ: Dim,
        width: Dim,
        length: Dim,
        depth: Dim | float,
        cornerFilletRadius: float,
        hasScoop: bool,
        scoopMaxRadius: float,
        hasTab: bool,
        tabInput: BinBodyTabGeneratorInput,
        tabHollowWallThickness: float | None,
        tabOpenings: TabWallOpenings | None,
        targetComponent: adsk.fusion.Component,
        *,
        name: str,
    ) -> tuple[list[adsk.fusion.BRepBody], list[adsk.fusion.BRepBody], TabHollowCuts]:
    """Bodies to join, bodies to cut, then with a hollow wall thickness, bodies hollowing out the tab once joined
    and opening it through the walls given"""

    bodiesToMerge: list[adsk.fusion.BRepBody] = []
    bodiesToSubtract: list[adsk.fusion.BRepBody] = []
    hollowCuts = TabHollowCuts()

    innerCutoutBody = createCompartmentCutout(
        wallThickness,
        originX,
        originY,
        originZ,
        width,
        length,
        depth,
        cornerFilletRadius,
        hasScoop,
        scoopMaxRadius,
        True,
        targetComponent,
        name=f'{name} cavity',
    )
    bodiesToSubtract.append(innerCutoutBody)

    # label tab
    if hasTab:
        tabBody = createGridfinityBinBodyTab(tabInput, targetComponent, name=f'{name} label tab')

        intersectTabInput = targetComponent.features.combineFeatures.createInput(
            tabBody,
            commonUtils.objectCollectionFromList([innerCutoutBody]),
            )
        intersectTabInput.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
        intersectTabInput.isKeepToolBodies = True
        intersectTabFeature = targetComponent.features.combineFeatures.add(intersectTabInput)
        intersectTabFeature.name = f'{name} label tab trim'
        tabBodies = [body for body in list(intersectTabFeature.bodies) if not body.revisionId == innerCutoutBody.revisionId]
        if tabHollowWallThickness is not None and len(tabBodies) > 0:
            # the tab is trimmed to the compartment, as an expression like the label on it (p60)
            (tabMinX, tabMaxX) = binLabelLayout.labelSpan(tabInput.originX, tabInput.length, originX, width)
            maxX = originX + width
            hollowCuts = createTabHollowCuts(
                tabInput,
                tabMinX,
                tabMaxX,
                tabHollowWallThickness,
                innerCutoutBody,
                TabCavity(originX, maxX, originY + length, compartmentCutoutFilletRadius(cornerFilletRadius)),
                tabOpenings,
                targetComponent,
                name=f'{name} label tab',
            )
        bodiesToMerge = bodiesToMerge + tabBodies
    return (bodiesToMerge, bodiesToSubtract, hollowCuts)
