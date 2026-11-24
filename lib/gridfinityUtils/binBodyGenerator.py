import adsk.core, adsk.fusion, traceback
import os
import math
import copy
from dataclasses import dataclass

from ...lib import fusion360utils as futil
from . import const, combineUtils, faceUtils, commonUtils, sketchUtils, extrudeUtils, baseGenerator, edgeUtils, filletUtils, patternUtils, binShape, scoopSides
from .binBodyCutoutGenerator import createGridfinityBinBodyCutout
from .binBodyCutoutGeneratorInput import BinBodyCutoutGeneratorInput
from .baseGeneratorInput import BaseGeneratorInput
from .binBodyGeneratorInput import BinBodyGeneratorInput, BinBodyCompartmentDefinition
from .binBodyTabGeneratorInput import BinBodyTabGeneratorInput
from .binBodyTabGenerator import createGridfinityBinBodyTab, createTabHollowCuts, TabCavity, TabWallOpenings, TabHollowCuts
from .labelGenerator import BinLabelDefinition, BinLabelInput, createLabel, LABEL_STYLE_EMBOSSED, LABEL_STYLE_ENGRAVED, LABEL_STYLE_CULLENECT
from . import cullenect, binLabelLayout
from .cullenectSocketGenerator import createCullenectSocket, SocketPlacement
from .binBodyLipGeneratorInput import BinBodyLipGeneratorInput, LIP_TYPE_FULL
from .binBodyLipGenerator import createGridfinityBinBodyLip, createStackedFootCutters, createLipSupport, lipInnerInset
from .raisedDividers import DividerSegment, dividerTop, RIDGE_WALL_MARGIN
from .raisedDividers import FilletCorner, filletCorners, isCornerEdge, chainRuns, runOffset, supportCornerPath
from .dim import Dim, valueInput, lengthInput, applyTo
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
    # the support under a full lip, it covers compartment corners from above (round 50)
    lipSupport = None
    # p83: the corners the raised dividers make, rounded up to the top once the bin is in one body
    raisedCorners: list[tuple[FilletCorner, tuple[Dim, Dim]]] = []
    raisedCornersRound = None
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
        lipInput.lipType = input.lipType
        lipInput.topTrimHeight = input.lipTopTrimHeight
        lipInput.xyClearance = input.xyClearance
        lipInput.binCornerFilletRadius = input.binCornerFilletRadius
        lipInput.origin = lipOriginPoint
        lipInput.originZ = binBodyTotalHeight
        lipInput.shapeCells = input.shapeCells
        lipInput.shapeCellsPerFoot = input.shapeCellsPerFoot
        lipBody = createGridfinityBinBodyLip(lipInput, targetComponent)

        hasLipBottomChamfer = input.hasLipBottomChamfer and input.lipType != LIP_TYPE_FULL and input.wallThickness < const.BIN_LIP_WALL_THICKNESS
        if input.lipType == LIP_TYPE_FULL and not input.isSolid:
            # joined once the compartments are cut, solid bodies get theirs with the cavity, see binBuilder
            lipSupport = createBinLipSupport(input, const.BIN_COMPARTMENT_BOTTOM_THICKNESS, targetComponent)
            if lipSupport is not None:
                bodiesToMerge.append(lipSupport)
        if hasLipBottomChamfer and input.shapeCells is not None:
            # the inside of the walls widening at 45 degrees into the lip, so it doesn't overhang the cavity
            combineUtils.cutBody(
                lipBody,
                commonUtils.objectCollectionFromList([createShapeLipBottomChamfer(input, binBodyTotalHeight, targetComponent)]),
                targetComponent,
                name='Lip bottom chamfer cut',
            )
        elif hasLipBottomChamfer and len(input.scoopSides) < len(scoopSides.SIDES_ORDER):
            # with four scoops the inside of the lip has nothing left to widen
            lipBottomChamferSize = max(const.BIN_BODY_CUTOUT_BOTTOM_FILLET_RADIUS, input.binCornerFilletRadius - input.wallThickness)
            # the box starts at the inside of the lip on scoop walls, the scoop runs up into the lip there
            chamferInsets = scoopSides.wallInsets(input.scoopSides, wall, Dim.length(const.BIN_LIP_WALL_THICKNESS - input.xyClearance))
            chamferInsetValues = scoopSides.wallInsets(input.scoopSides, input.wallThickness, const.BIN_LIP_WALL_THICKNESS - input.xyClearance)
            lipBottomChamferExtrude = extrudeUtils.createBoxAtPoint(
                bodyWidth - chamferInsets[scoopSides.LEFT] - chamferInsets[scoopSides.RIGHT],
                bodyLength - chamferInsets[scoopSides.FRONT] - chamferInsets[scoopSides.BACK],
                lipBottomChamferSize,
                targetComponent,
                adsk.core.Point3D.create(
                    chamferInsetValues[scoopSides.LEFT],
                    chamferInsetValues[scoopSides.FRONT],
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
            # round 48: the edges along the scoop walls and their corner arcs are left out, picked by where they lie;
            # before, a single front scoop dropped the first three edges of the top's tangent chain
            # the box's bounds from its placement, a face's bounding box may be drawn loose (review round 48)
            (boxMin, boxMax) = scoopSides.boxBounds(
                (chamferInsetValues[scoopSides.LEFT], chamferInsetValues[scoopSides.FRONT]),
                (bodyWidth - chamferInsets[scoopSides.LEFT] - chamferInsets[scoopSides.RIGHT]).value,
                (bodyLength - chamferInsets[scoopSides.FRONT] - chamferInsets[scoopSides.BACK]).value,
            )
            edgesToChamfer = [
                edge for edge in lipBottomChamferExtrudeTopFace.edges
                if not scoopSides.touchesScoopWall(
                    (edge.boundingBox.minPoint.x, edge.boundingBox.minPoint.y),
                    (edge.boundingBox.maxPoint.x, edge.boundingBox.maxPoint.y),
                    boxMin,
                    boxMax,
                    input.scoopSides,
                )
            ]
            chamferFeatures: adsk.fusion.ChamferFeatures = features.chamferFeatures
            bottomLipChamferInput = chamferFeatures.createInput2()
            bottomLipChamferEdges = commonUtils.objectCollectionFromList(edgesToChamfer)
            bottomLipChamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
                bottomLipChamferEdges,
                lengthInput(lipBottomChamferSize),
                False)
            chamferFeatures.add(bottomLipChamferInput).name = 'Lip bottom chamfer'
            combineUtils.cutBody(lipBody, commonUtils.objectCollectionFromList(lipBottomChamferExtrude.bodies), targetComponent, name='Lip bottom chamfer cut')

        bodiesToMerge.append(lipBody)

    if not input.isSolid:
        # a scoop wall runs up into the inside of the lip, on every wall with a scoop (round 48)
        outerScoopWalls = input.scoopSides if input.hasLip else frozenset()
        scoopInset = lipInnerInset(input.lipType, input.xyClearance)
        compartmentInsets = scoopSides.wallInsets(outerScoopWalls, wall, scoopInset)
        # dividers raised into the lip keep to the grid lines, the compartments along a scoop wall take its inset
        # instead of the whole grid moving off them (round 50, p650), see scoopSides.gridTrims
        (gridInsets, gridTrims) = scoopSides.gridTrims(
            outerScoopWalls, wall, scoopInset, keepGrid=input.hasLip and len(input.raisedDividers) > 0)
        compartmentsMinX = gridInsets[scoopSides.LEFT]
        compartmentsMaxX = bodyWidth - gridInsets[scoopSides.RIGHT]
        compartmentsMinY = gridInsets[scoopSides.FRONT]
        compartmentsMaxY = bodyLength - gridInsets[scoopSides.BACK]

        totalCompartmentsWidth = compartmentsMaxX - compartmentsMinX
        totalCompartmentsLength = compartmentsMaxY - compartmentsMinY

        compartmentWidthUnit = (totalCompartmentsWidth - wall * (input.compartmentsByX - 1)) / input.compartmentsByX
        compartmentLengthUnit = (totalCompartmentsLength - wall * (input.compartmentsByY - 1)) / input.compartmentsByY

        hasRaisedDividers = input.hasLip and len(input.raisedDividers) > 0

        def gridLineAt(axis: str, line: int) -> Dim:
            """Where a grid line of the compartment grid lies, across x for axis 'x', on the body: whole cells of the
            base from the grid's edge, a clearance outside the body"""
            (base, cells, count) = (input.baseWidth, input.binWidth, input.compartmentsByX) if axis == 'x' else (input.baseLength, input.binLength, input.compartmentsByY)
            return base * Dim.number(round(line * cells / count, 6)) - Dim.length(input.xyClearance)

        def compartmentCell(compartment: BinBodyCompartmentDefinition) -> tuple[Dim, Dim, Dim, Dim]:
            """X, y, width and length of the compartment cavity in the grid, shortened along a trimmed scoop wall (round 50)"""
            return scoopSides.trimmedCavity(
                compartmentsMinX + (compartmentWidthUnit + wall) * compartment.positionX,
                compartmentsMinY + (compartmentLengthUnit + wall) * compartment.positionY,
                compartmentWidthUnit * compartment.width + wall * (compartment.width - 1),
                compartmentLengthUnit * compartment.length + wall * (compartment.length - 1),
                (compartment.positionX, compartment.positionY),
                (compartment.width, compartment.length),
                (input.compartmentsByX, input.compartmentsByY),
                gridTrims,
            )

        cavityCornerRadius = compartmentCutoutFilletRadius(input.binCornerFilletRadius - input.wallThickness)

        # a cavity corner between two scoop walls follows the lip's inner corner (p653, round 50)
        scoopCorner = scoopSides.scoopCornerRadius(cavityCornerRadius, input.binCornerFilletRadius, scoopInset.value)

        def cornerRadii(compartment: BinBodyCompartmentDefinition) -> dict | None:
            """The compartment's own corner radii, between two scoop walls"""
            radii = {corner: scoopCorner for corner in scoopSides.scoopWallCorners(
                outerScoopWalls, (compartment.positionX, compartment.positionY),
                (compartment.width, compartment.length), (input.compartmentsByX, input.compartmentsByY))}
            if len(radii) == 0:
                return None
            if len(scoopSides.bottomFilletSides(compartment.scoopSides)) > 0:
                # a floor fillet runs round the corners, all alike at the tightest: corners of different radii broke the
                # floor's outline beside a scoop into edges Fusion found no fillet for (shown in Fusion, round 50)
                return {(sideX, sideY): scoopCorner for sideX in (scoopSides.LEFT, scoopSides.RIGHT) for sideY in (scoopSides.FRONT, scoopSides.BACK)}
            return radii

        def tabPlacement(compartmentX: Dim, compartmentY: Dim, compartmentLength: Dim) -> tuple[Dim, Dim, Dim]:
            """X and y of the tab's back top corner, along the compartment's back wall, and its length"""
            return (
                compartmentX + input.baseWidth * max(0, min(input.tabPosition, input.binWidth - input.tabLength)),
                compartmentY + compartmentLength,
                input.baseWidth * max(0, min(input.tabLength, input.binWidth)),
            )

        # trimmed compartments are patterned only while all are trimmed alike (round 50)
        useCompartmentPattern = (input.isUniformCompartments and len(input.compartments) > 1
            # a corner between two scoop walls of one compartment only (p653, review round 50)
            and all(cornerRadii(compartment) is None for compartment in input.compartments)
            and scoopSides.trimsKeepAlike(gridTrims, (input.compartmentsByX, input.compartmentsByY)))
        compartmentsToBuild = input.compartments[:1] if useCompartmentPattern else input.compartments
        for compartmentIndex, compartment in enumerate(compartmentsToBuild):
            compartmentName = 'Compartment' if len(compartmentsToBuild) == 1 else f'Compartment {compartmentIndex + 1}'
            (compartmentX, compartmentY, compartmentWidth, compartmentLength) = compartmentCell(compartment)
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
            compartmentTabInput.topClearance = tabTopClearance(input.labelStyle, input.tabTopOffset)
            # a hollow tab of a single compartment is opened through the outer walls of the bin, with more compartments
            # the hollows are left closed
            tabOpenings = None
            if input.isTabHollow and len(input.compartments) == 1:
                tabOpenings = TabWallOpenings(
                    # through the wall a side scoop thickens up to the lip's inner edge (review round 48)
                    scoopSides.tabOpeningDepth({side: inset.value for (side, inset) in compartmentInsets.items()}, input.wallThickness),
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
                compartment.scoopSides,
                input.scoopMaxRadius,
                input.hasTab,
                compartmentTabInput,
                hollowTabWallThickness(input.wallThickness, input.labelStyle) if input.isTabHollow else None,
                tabOpenings,
                targetComponent,
                name=compartmentName,
                cornerRadii=cornerRadii(compartment),
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

        # dividers are lowered as far as the tabs
        if len(input.compartments) > 1 and input.tabTopOffset > 0:
            # over the cavities, also where the grid keeps to the grid lines (round 50)
            clearanceInsets = scoopSides.cavityInsets(gridInsets, gridTrims)
            (clearanceMinX, clearanceMinY) = (clearanceInsets[scoopSides.LEFT], clearanceInsets[scoopSides.FRONT])
            # its corners between two scoop walls as the cavities' there (p653)
            clearanceCorners = {corner: scoopCorner for corner in scoopSides.scoopWallCorners(
                outerScoopWalls, (0, 0), (input.compartmentsByX, input.compartmentsByY), (input.compartmentsByX, input.compartmentsByY))}
            compartmentsTopClearance = createCompartmentCutout(
                input.wallThickness,
                clearanceMinX,
                clearanceMinY,
                binBodyTotalHeight,
                bodyWidth - clearanceInsets[scoopSides.RIGHT] - clearanceMinX,
                bodyLength - clearanceInsets[scoopSides.BACK] - clearanceMinY,
                input.tabTopOffset,
                input.binCornerFilletRadius - input.wallThickness,
                frozenset(),
                0,
                False,
                targetComponent,
                name='Compartments top clearance',
                cornerRadii=clearanceCorners or None,
            )
            bodiesToSubtract.append(compartmentsTopClearance)

        if hasRaisedDividers:
            def cellCavity(column: int, row: int) -> tuple[Dim, Dim, Dim, Dim]:
                """X, y, width and length of a single grid cell's cavity, trimmed along a scoop wall"""
                return scoopSides.trimmedCavity(
                    compartmentsMinX + (compartmentWidthUnit + wall) * column,
                    compartmentsMinY + (compartmentLengthUnit + wall) * row,
                    compartmentWidthUnit, compartmentLengthUnit, (column, row), (1, 1),
                    (input.compartmentsByX, input.compartmentsByY), gridTrims,
                )
            # p83: the corners the raised dividers make, rounded up to the top once the bin is in one body, from the
            # top of the corners below, where the raised divider starts
            raisedCorners = raisedDividerCorners(input.raisedDividers, (input.compartmentsByX, input.compartmentsByY), cellCavity)
            def cornerLineAt(axis: str, line: int) -> Dim:
                """How far a corner's edges may go towards a line: an outer wall's grid line, the middle of a raised
                divider, where its top's ridge is"""
                count = input.compartmentsByX if axis == 'x' else input.compartmentsByY
                if line in (0, count):
                    return gridLineAt(axis, line)
                (start, unit) = (compartmentsMinX, compartmentWidthUnit) if axis == 'x' else (compartmentsMinY, compartmentLengthUnit)
                return start + (unit + wall) * line - wall / 2
            raisedCornersRound = RaisedCornersRound(
                gridLineAt=cornerLineAt,
                # the lip as far as it reaches into the cell, at least its top section, a full lip's support further
                reach=max(const.BIN_LIP_WALL_THICKNESS, (lipInnerInset(input.lipType, input.xyClearance) + Dim.length(input.xyClearance)).value),
                bottomZ=binBodyTotalHeight - Dim.length(input.tabTopOffset),
                radius=cavityCornerRadius,
                # a full lip's support turns out to the wall this far under the body top, see supportCornerSweep
                supportTopZ=binBodyTotalHeight - Dim.length(const.BIN_LIP_SUPPORT_WALL_HEIGHT) if lipSupport is not None else None,
            )
            bodiesToMerge.extend(createRaisedDividers(
                input.raisedDividers,
                (compartmentsMinX, compartmentsMinY),
                (compartmentWidthUnit + wall, compartmentLengthUnit + wall),
                (input.compartmentsByX, input.compartmentsByY),
                wall,
                binBodyTotalHeight,
                input.tabTopOffset,
                lipInput,
                targetComponent,
                gridLineAt,
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
        roundRaisedDividerCorners(binBody, raisedCorners, raisedCornersRound, lipInput, targetComponent)

    labelBodies: list[adsk.fusion.BRepBody] = []
    pockets: list[tuple[int, int, SocketPlacement]] = []
    if not input.isSolid and input.hasTab:
        # every compartment gets its own label, also where the tabs come from a pattern. A Cullenect socket goes into
        # every tab, the inserts carry the labels
        isCullenect = input.labelStyle == LABEL_STYLE_CULLENECT
        for compartmentIndex, compartment in enumerate(input.compartments):
            if not isCullenect and (compartment.label is None or compartment.label.isEmpty):
                continue
            (compartmentX, compartmentY, compartmentWidth, compartmentLength) = compartmentCell(compartment)
            (tabOriginX, tabOriginY, tabLength) = tabPlacement(compartmentX, compartmentY, compartmentLength)
            # tabs are trimmed to their compartment, as an expression (p60)
            (labelMinX, labelMaxX) = binLabelLayout.labelSpan(tabOriginX, tabLength, compartmentX, compartmentWidth)
            labelName = 'Label' if len(input.compartments) == 1 else f'Compartment {compartmentIndex + 1} label'
            if isCullenect:
                if not cullenect.socketFitsDepth((tabOriginY - compartmentY).value, input.tabWidth, input.cullenectSocketOffset):
                    # the tab fills the compartment, the socket would cut into the divider in front
                    commonUtils.debugLog(f'{labelName}: compartment {compartmentLength.value * 10:.2f} mm long, too short for a Cullenect socket')
                    continue
                pocket = createCullenectSocket(
                    labelMinX,
                    labelMaxX,
                    tabOriginY,
                    input.tabWidth,
                    binBodyTotalHeight - Dim.length(tabTopClearance(input.labelStyle, input.tabTopOffset)),
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
                input.tabTopOffset,
                input.labelColor,
                name=labelName,
                textOccurrence=input.textOccurrence,
                targetOccurrence=input.binOccurrence,
                binPlacement=input.binPlacement,
            )

    return (binBody, labelBodies, pockets)

def raisedDividerWall(
    axis: str,
    wallStart: Dim,
    wall: Dim,
    runStart: Dim,
    runLength: Dim,
    bottomZ: Dim,
    topZ: Dim,
    isTrimmed: bool,
    targetComponent: adsk.fusion.Component,
    name: str,
) -> adsk.fusion.BRepBody:
    """
    A raised divider, as thick as the divider, from bottomZ straight up and topped at topZ, the lip's top, as
    raisedDividers.dividerTop gives it: a roof under an untrimmed lip, a flat top chamfered on both sides under a
    trimmed one (round 50, decided 19.11.2026). Its section is sketched in a plane across the run at its middle: the
    bottom level, both sides upright, a flat top level, every point placed from the origin by what that leaves free,
    so the sketch is fully constrained; extruded both ways over the run
    """
    (across, along) = (0, 1) if axis == 'x' else (1, 0)
    middle = runStart + runLength / 2
    planeInput: adsk.fusion.ConstructionPlaneInput = targetComponent.constructionPlanes.createInput()
    planeInput.setByOffset(targetComponent.xZConstructionPlane if along == 1 else targetComponent.yZConstructionPlane, valueInput(middle))
    plane = targetComponent.constructionPlanes.add(planeInput)
    plane.name = f'{name} section plane'
    sketch: adsk.fusion.Sketch = targetComponent.sketches.add(plane)
    sketch.name = f'{name} section'
    top = dividerTop(wallStart, wall, topZ, isTrimmed=isTrimmed, smaller=lambda limit, part: Dim.min(Dim.length(limit), part))
    # round the section from the bottom's low corner: bottom, high side, the top back to the low side
    corners = [(wallStart, bottomZ), (wallStart + wall, bottomZ)] + list(reversed(top))
    count = len(corners)
    # line k runs from corner k to the next; the bottom and a flat top are level, both sides upright
    levels = [k for k in range(count) if abs(corners[k][1].value - corners[(k + 1) % count][1].value) < 1e-9]
    uprights = [1, count - 1]

    def held(k: int) -> tuple[bool, bool]:
        """Whether corner k needs a dim across and one in z, the constraints holding the rest"""
        if k == 0:
            return (True, True)
        # on the bottom with corner 0, on the high side with corner 1
        if k == 1 or (k - 1) in levels and k != 2:
            return (True, False)
        # on a side with the bottom's corner
        if k == 2 or k == count - 1:
            return (False, True)
        return (True, True)

    def onSketch(acrossValue: float, z: float) -> adsk.core.Point3D:
        coords = [0.0, 0.0, z]
        coords[across] = acrossValue
        coords[along] = middle.value
        point = sketch.modelToSketchSpace(adsk.core.Point3D.create(*coords))
        point.z = 0
        return point

    # which of the sketch's axes runs across the divider, the other is z
    (origin, step) = (onSketch(0, 0), onSketch(1, 0))
    acrossIsSketchX = abs(step.x - origin.x) > abs(step.y - origin.y)
    points = [onSketch(a.value, z.value) for (a, z) in corners]
    dimensions = sketch.sketchDimensions
    constraints = sketch.geometricConstraints
    with sketchUtils.deferSketchCompute(sketch):
        lines = []
        for k in range(count):
            start = lines[-1].endSketchPoint if lines else points[0]
            end = lines[0].startSketchPoint if k == count - 1 else points[k + 1]
            lines.append(sketch.sketchCurves.sketchLines.addByTwoPoints(start, end))
        # Fusion keeps no horizontal or vertical constraint of its own here: dims on every point left two points free
        # or overconstrained the sketch where it did (shown in Fusion, round 50)
        for k in levels:
            constraints.addHorizontal(lines[k]) if acrossIsSketchX else constraints.addVertical(lines[k])
        for k in uprights:
            constraints.addVertical(lines[k]) if acrossIsSketchX else constraints.addHorizontal(lines[k])
        for k in range(count):
            (a, z) = corners[k]
            at = points[k]
            for (isAcross, value, needed) in ((True, a, held(k)[0]), (False, z, held(k)[1])):
                if not needed:
                    continue
                isSketchX = isAcross == acrossIsSketchX
                orientation = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation if isSketchX else adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
                textAt = adsk.core.Point3D.create(at.x, at.y - 0.3, 0) if isSketchX else adsk.core.Point3D.create(at.x - 0.3, at.y, 0)
                applyTo(dimensions.addDistanceDimension(sketch.originPoint, lines[k].startSketchPoint, orientation, textAt, True).parameter, value.abs())
    extrudes = targetComponent.features.extrudeFeatures
    extrudeInput = extrudes.createInput(sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extrudeInput.setSymmetricExtent(valueInput(runLength), True)
    extrude = extrudes.add(extrudeInput)
    extrude.name = name
    return extrude.bodies.item(0)


def createRaisedDividers(
    segments: list[DividerSegment],
    compartmentsMin: tuple[Dim, Dim],
    pitch: tuple[Dim, Dim],
    counts: tuple[int, int],
    wall: Dim,
    binBodyTotalHeight: Dim,
    topOffset: float,
    lipInput: BinBodyLipGeneratorInput,
    targetComponent: adsk.fusion.Component,
    gridLineAt,
) -> list[adsk.fusion.BRepBody]:
    """
    Raised dividers on grid lines, up to the top of the lip (round 8, p61). Round 50, decided 19.11.2026: each goes
    straight up as thick as the divider, from the divider top lowered by the tab top offset (upstream c2e12c0, round
    38), and ends at the lip's top in a roof or, under a trimmed lip, a chamfered flat top, see raisedDividerWall; then
    it is cut by the feet of a bin stacked on top like the lip. Segments reach a wall further where they meet a
    crossing divider, and to RIDGE_WALL_MARGIN under the outer faces of the outer walls, which keeps every section's
    corner off the sketch axes
    """
    boxes: list[adsk.fusion.BRepBody] = []
    # up to the lip top, trimmed or not (upstream round 17.11.2026, p13)
    topZ = binBodyTotalHeight + Dim.length(const.BIN_LIP_EXTRA_HEIGHT - lipInput.topTrimHeight)
    for (index, segment) in enumerate(segments):
        # across is the axis the wall stands on, along the one it runs on
        (across, along) = (0, 1) if segment.axis == 'x' else (1, 0)
        wallStart = compartmentsMin[across] + pitch[across] * segment.line - wall
        # Up to a hair under the outer face at an outer wall, where the grid starts a wall in (round 50), the feet of a
        # stacked bin shape its end there like the lip: ended half a wall into the wall, or half a wall short of a scoop
        # wall's cavity, it left a gap to the thinner top of the lip, up to 1.1 mm (found by the divider gap check)
        outerReach = wall - Dim.length(RIDGE_WALL_MARGIN)
        startReach = outerReach if segment.start == 0 else wall
        endReach = outerReach if segment.end == counts[along] else wall
        # the first cavity starts at the min, the last one ends a wall short of the next pitch
        runStart = compartmentsMin[along] + pitch[along] * segment.start - startReach
        runLength = pitch[along] * (segment.end - segment.start) - wall + startReach + endReach
        name = f'Raised divider {index + 1}'
        boxes.append(raisedDividerWall(
            segment.axis, wallStart, wall, runStart, runLength, binBodyTotalHeight - Dim.length(topOffset), topZ,
            lipInput.topTrimHeight > 0, targetComponent, name,
        ))
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

# a corner's edges start on the top of the corner below, and on the cavity's corner or off it on one axis, within this
CORNER_START_TOLERANCE = 1e-4


@dataclass
class RaisedCornersRound:
    """How the corners of the raised dividers are rounded, see roundRaisedDividerCorners"""
    # where a grid line of the compartment grid lies, (axis, line) -> Dim
    gridLineAt: object
    # how far the lip and a full lip's support reach into a cell from their grid lines, cm
    reach: float
    # the top of the corners below, where the raised dividers start
    bottomZ: Dim
    # the radius of the corners below, cm
    radius: float
    # where a full lip's support turns out to the wall, None without one
    supportTopZ: Dim | None


def raisedDividerCorners(
    segments: list[DividerSegment],
    counts: tuple[int, int],
    cellCavity,
) -> list[tuple[FilletCorner, tuple[Dim, Dim]]]:
    """
    The cell corners the raised dividers make, each with where the corner of the cavity is: the corner of the cell's
    own cavity, cellCavity(column, row) its x, y, width and length, trimmed along a scoop wall (round 50)
    """
    corners = []
    for corner in filletCorners(segments, counts[0], counts[1]):
        (x, y, width, length) = cellCavity(corner.column, corner.row)
        corners.append((corner, (x if corner.sideX == -1 else x + width, y if corner.sideY == -1 else y + length)))
    return corners

def raisedCornerChain(
    binBody: adsk.fusion.BRepBody,
    corner: FilletCorner,
    cornerAt: tuple[float, float],
    grids: tuple[float, float],
    reach: float,
    bottomZ: float,
) -> list[adsk.fusion.BRepEdge]:
    """The edges of the body a corner goes up along, see raisedDividers.isCornerEdge"""
    edges = []
    for edge in binBody.edges:
        if not isinstance(edge.geometry, adsk.core.Line3D):
            continue
        start = edge.startVertex.geometry
        end = edge.endVertex.geometry
        if isCornerEdge(corner, cornerAt, grids, reach=reach, bottomZ=bottomZ, start=(start.x, start.y, start.z), end=(end.x, end.y, end.z)):
            edges.append(edge)
    return edges

def roundRaisedDividerCorners(
    binBody: adsk.fusion.BRepBody,
    corners: list[tuple[FilletCorner, tuple[Dim, Dim]]],
    rounding: RaisedCornersRound,
    lipInput: BinBodyLipGeneratorInput,
    targetComponent: adsk.fusion.Component,
):
    """
    p83: rounds every corner of a raised divider from the top of the compartment's corner fillet up to the top, over
    the faces of divider and wall, the lip and the divider's top, cast in one piece with the corner below. Root cause of
    the sharp corner: the raised divider is joined on above the compartment cuts, which alone carry the corner fillets,
    so they stop at the divider's top.
    Each corner's section, the square of the radius less its circle, the very section of the corner below, is swept up
    along the edges of its corner without turning: at every height it rounds the corner of the faces there, as the
    corner fillet below does, and follows them as they run into the cell or, up the divider's top, back to its middle.
    Since round 50 the path runs in 3D, its edges no longer in one plane (round 8 swept within the divider's face).
    Rejected in round 8, all shown in Fusion: fill pieces extruded up and cut (sharp corner in the lip, undercuts at the
    top), a rolling ball fillet up the edges (a sickle of 0.36 mm2 on the corner below, the ball runs into the chamfer
    under the lip). The sweeps are cut by the feet of a bin stacked on top, so it still stacks. A wall thicker than the
    lip leaves a level ledge under it, the corner's edges fall in runs there, each swept on its own and only the top one
    cut by the feet (round 15, p101). A corner whose edges make no runs, or that Fusion can't sweep, is filleted
    instead, see filletRaisedDividerCorner
    """
    bottomZ = rounding.bottomZ
    radius = Dim.length(rounding.radius)
    sweeps: list[tuple] = []
    toFillet: list[tuple[int, FilletCorner, tuple[float, float], tuple[float, float]]] = []
    # Each corner's section goes where its edges start, the lowest point of its first run: under a full lip that is
    # the support's face straight down from the lip's tip, not the cavity's corner. Placed at the cavity's corner it
    # was swept 1.4 mm beside its path, inside the support and the lip, and that corner stayed sharp (round 50, shown
    # in Fusion). Moved by a constant from the cavity's corner, like the runs above a ledge
    chains = []
    for (index, (corner, cornerAt)) in enumerate(corners):
        at = (cornerAt[0].value, cornerAt[1].value)
        lineX = corner.column if corner.sideX == -1 else corner.column + 1
        lineY = corner.row if corner.sideY == -1 else corner.row + 1
        grids = (rounding.gridLineAt('x', lineX).value, rounding.gridLineAt('y', lineY).value)
        edges = raisedCornerChain(binBody, corner, at, grids, rounding.reach, bottomZ.value)
        points = [(tuple(edge.startVertex.geometry.asArray()), tuple(edge.endVertex.geometry.asArray())) for edge in edges]
        runs = chainRuns(points)
        if runs is None:
            toFillet.append((index, corner, at, grids))
            continue
        lowest = min((point for i in runs[0] for point in points[i]), key=lambda point: point[2])
        offset = (lowest[0] - at[0], lowest[1] - at[1])
        moved = [axis for axis in (0, 1) if abs(offset[axis]) > CORNER_START_TOLERANCE]
        if abs(lowest[2] - bottomZ.value) > CORNER_START_TOLERANCE or len(moved) > 1 or (len(moved) == 1 and rounding.supportTopZ is None):
            # not on the corner below, nor beside a support: no section to sweep
            commonUtils.debugLog(f'Raised divider corner {index + 1}: its edges start off the corner below, filleted')
            toFillet.append((index, corner, at, grids))
            continue
        startAt = (cornerAt[0] + Dim.length(offset[0]), cornerAt[1] + Dim.length(offset[1]))
        support = (moved[0], offset[moved[0]]) if len(moved) == 1 else None
        chains.append((index, corner, cornerAt, startAt, grids, edges, points, runs, support))
    sketch = raisedCornerSectionsSketch([(chain[1], chain[3]) for chain in chains], bottomZ, radius, targetComponent) if len(chains) > 0 else None
    for (index, corner, cavityAt, cornerAt, grids, edges, points, runs, support) in chains:
        at = (cornerAt[0].value, cornerAt[1].value)
        name = f'Raised divider corner {index + 1}'
        profile = sectionProfile(sketch, at)
        if profile is None:
            toFillet.append((index, corner, at, grids))
            continue
        bodies = []
        # sweeps and section sketches made for the corner, they go again when it is filleted after all
        made = []
        if support is not None:
            piece = supportCornerSweep(corner, cavityAt, support, rounding, targetComponent, name, made)
            if piece is not None:
                bodies.append(piece)
        for (runIndex, run) in enumerate(runs):
            if support is not None and len(bodies) == 0:
                break
            runProfile = profile
            if runIndex > 0:
                (shiftX, shiftY, rise) = runOffset(points, runs, runIndex)
                runAt = (cornerAt[0] + Dim.length(shiftX), cornerAt[1] + Dim.length(shiftY))
                runSketch = raisedCornerSectionsSketch([(corner, runAt)], bottomZ + Dim.length(rise), radius, targetComponent, name=f'{name} run {runIndex + 1}')
                made.append(runSketch)
                runProfile = sectionProfile(runSketch, (runAt[0].value, runAt[1].value))
                if runProfile is None:
                    break
            sweep = sweepCorner(runProfile, [edges[i] for i in run], targetComponent, f'{name} sweep' if len(runs) == 1 else f'{name} sweep {runIndex + 1}')
            if sweep is None:
                break
            made.append(sweep)
            bodies.append(sweep.bodies.item(0))
        if len(bodies) != len(runs) + (1 if support is not None else 0):
            deleteMade(made)
            toFillet.append((index, corner, at, grids))
            continue
        sweeps.append((index, corner, at, grids, bodies, made))
    # the corners whose sweeps stay in the design, on the shared sections; after a failed join their pieces go but the
    # sweeps stay (review round 50)
    joined: list[tuple[int, FilletCorner, tuple[float, float], tuple[float, float]]] = []
    if len(sweeps) > 0:
        # The corners stay sharp at worst, never the bin: a cut or join Fusion fails on leaves their corners to the
        # fillets. The cutters are kept until the last cut, see createRaisedDividers
        cutters = createStackedFootCutters(lipInput, targetComponent, name='Raised divider corners foot cutout')
        rounded: list[adsk.fusion.BRepBody] = []
        for (position, (index, corner, at, grids, bodies, made)) in enumerate(sweeps):
            # only the top run is cut, the pieces below it stay where the feet can't reach
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
                # no loose pieces, sweeps or sketches of a corner that is filleted (review round 50)
                deleteMade(made)
                if position == len(sweeps) - 1:
                    # the last cut was to use up the cutters, they mustn't stay in the bin (review round 15)
                    for cutter in cutters:
                        targetComponent.features.removeFeatures.add(cutter)
                toFillet.append((index, corner, at, grids))
                continue
            # a cut keeping its tools lists them among its bodies too
            rounded.extend(bodies[:-1])
            rounded.extend(piece for piece in cut.bodies if all(piece != cutter for cutter in cutters))
            joined.append((index, corner, at, grids))
        if len(rounded) > 0:
            try:
                combineUtils.joinBodies(binBody, commonUtils.objectCollectionFromList(rounded), targetComponent, name='Raised divider corners join')
            except RuntimeError as error:
                commonUtils.debugLog(f'Raised divider corners: join failed, {error}')
                # their pieces go, those corners are filleted, the ones already to be filleted once (review round 15)
                for piece in rounded:
                    targetComponent.features.removeFeatures.add(piece)
                toFillet.extend(joined)
    if sketch is not None and len(joined) == 0:
        # no sweep left on the shared sections, they go with their plane (review round 50)
        deleteMade([sketch])
    for (index, corner, at, grids) in toFillet:
        filletRaisedDividerCorner(binBody, index, corner, at, grids, rounding.reach, bottomZ.value, rounding.radius, targetComponent)

def deleteMade(made: list):
    """Deletes what was made for a corner, last first, a sketch with its construction plane"""
    for item in reversed(made):
        plane = item.referencePlane if isinstance(item, adsk.fusion.Sketch) else None
        if item.isValid:
            item.deleteMe()
        if plane is not None and plane.isValid:
            plane.deleteMe()

def sweepCorner(
    profile: adsk.fusion.Profile,
    path: list,
    targetComponent: adsk.fusion.Component,
    name: str,
) -> adsk.fusion.SweepFeature | None:
    """A corner's section swept along a path without turning, None where Fusion can't or makes more than one body of it"""
    try:
        sweepPath = targetComponent.features.createPath(commonUtils.objectCollectionFromList(path), False)
        sweepInput = targetComponent.features.sweepFeatures.createInput(profile, sweepPath, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        sweepInput.orientation = adsk.fusion.SweepOrientationTypes.ParallelOrientationType
        sweep = targetComponent.features.sweepFeatures.add(sweepInput)
    except RuntimeError as error:
        commonUtils.debugLog(f'{name} failed, {error}')
        return None
    sweep.name = name
    if sweep.bodies.count != 1:
        # one section along one path is one body, anything else isn't the corner
        commonUtils.debugLog(f'{name} made {sweep.bodies.count} bodies')
        sweep.deleteMe()
        return None
    return sweep

def supportCornerSweep(
    corner: FilletCorner,
    cavityAt: tuple[Dim, Dim],
    support: tuple[int, float],
    rounding: RaisedCornersRound,
    targetComponent: adsk.fusion.Component,
    name: str,
    made: list,
) -> adsk.fusion.BRepBody | None:
    """
    The corner beside a full lip's support, from where the support leaves the wall's face up to the edges the corner is
    swept along above, see raisedDividers.supportCornerPath (round 50). There the cavity's corner fill stands in front
    of the support, its circle 1.4 mm further in than the section's at the support's face: swept from there up, the
    section left a level face of 1.29 mm2 under it (shown in Fusion). Swept from the cavity's corner up the support's
    corner, the section's fill holds all of the cavity's corner fill, the corner is one rounding tangent to the
    support's face; the support's own kinks of 63 and 53 degrees there are gone with it. The path is a sketch in the
    plane of the divider's face, each point placed from the origin by the grid's dims, the section one at its start
    """
    (axis, offset) = support
    other = 1 - axis
    path = supportCornerPath(abs(offset), supportTopZ=rounding.supportTopZ.value, bottomZ=rounding.bottomZ.value, tolerance=CORNER_START_TOLERANCE)
    # out from the wall's face into the cell, along the axis the start lies off the cavity's corner
    direction = 1 if offset > 0 else -1
    # the points as dims, from the cavity's corner and the heights
    knee = rounding.supportTopZ if rounding.supportTopZ.value < rounding.bottomZ.value else rounding.bottomZ
    out = Dim.length(abs(offset))
    dims = [(cavityAt[axis], knee - out), (cavityAt[axis] + out * direction, knee)]
    if len(path) == 3:
        dims.append((cavityAt[axis] + out * direction, rounding.bottomZ))
    planeInput: adsk.fusion.ConstructionPlaneInput = targetComponent.constructionPlanes.createInput()
    planeInput.setByOffset(targetComponent.yZConstructionPlane if other == 0 else targetComponent.xZConstructionPlane, valueInput(cavityAt[other]))
    plane = targetComponent.constructionPlanes.add(planeInput)
    plane.name = f'{name} support path plane'
    made.append(plane)
    sketch: adsk.fusion.Sketch = targetComponent.sketches.add(plane)
    sketch.name = f'{name} support path'
    made.append(sketch)

    def onSketch(along: float, z: float) -> adsk.core.Point3D:
        coords = [0.0, 0.0, z]
        coords[axis] = along
        coords[other] = cavityAt[other].value
        point = sketch.modelToSketchSpace(adsk.core.Point3D.create(*coords))
        point.z = 0
        return point

    # which of the sketch's axes the model's axis along the wall's normal runs on, the other is z
    (origin, step) = (onSketch(0, 0), onSketch(1, 0))
    alongIsSketchX = abs(step.x - origin.x) > abs(step.y - origin.y)
    points = [onSketch(along.value, z.value) for (along, z) in dims]
    lines = []
    dimensions = sketch.sketchDimensions
    with sketchUtils.deferSketchCompute(sketch):
        for (start, end) in zip(points, points[1:]):
            lines.append(sketch.sketchCurves.sketchLines.addByTwoPoints(lines[-1].endSketchPoint if lines else start, end))
        sketchPoints = [lines[0].startSketchPoint] + [line.endSketchPoint for line in lines]
        # each point placed from the origin, sketch distance dimensions are unsigned
        for (point, at, (along, z)) in zip(sketchPoints, points, dims):
            (horizontal, vertical) = (along, z) if alongIsSketchX else (z, along)
            for (orientation, value, textAt) in (
                (adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, horizontal, adsk.core.Point3D.create(at.x, at.y - 0.3, 0)),
                (adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, vertical, adsk.core.Point3D.create(at.x - 0.3, at.y, 0)),
            ):
                applyTo(dimensions.addDistanceDimension(sketch.originPoint, point, orientation, textAt, True).parameter, value.abs())
    sections = raisedCornerSectionsSketch([(corner, cavityAt)], dims[0][1], Dim.length(rounding.radius), targetComponent, name=f'{name} support')
    made.append(sections)
    profile = sectionProfile(sections, (cavityAt[0].value, cavityAt[1].value))
    if profile is None:
        return None
    sweep = sweepCorner(profile, lines, targetComponent, f'{name} support sweep')
    if sweep is None:
        return None
    made.append(sweep)
    return sweep.bodies.item(0)

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
    grids: tuple[float, float],
    reach: float,
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
    edges = raisedCornerChain(binBody, corner, cornerAt, grids, reach, bottomZ)
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


def createBinLipSupport(
    input: BinBodyGeneratorInput,
    floorZ: float,
    targetComponent: adsk.fusion.Component,
) -> adsk.fusion.BRepBody | None:
    """The support under a full lip along the walls of the bin, see createLipSupport. A plain bin's outline is a single cell"""
    if input.shapeCells is not None:
        cells = input.shapeCells
        grid = baseGenerator.shapeGridInput(input.baseWidth, input.baseLength, input.xyClearance, input.shapeCellsPerFoot)
    else:
        cells = [(0, 0)]
        grid = baseGenerator.shapeGridInput(input.baseWidth * input.binWidth, input.baseLength * input.binLength, input.xyClearance)
    return createLipSupport(cells, grid, input.lipType, input.wallThickness, binBodyTopHeight(input), floorZ, targetComponent)

def tabTopClearance(labelStyle: str, topOffset: float) -> float:
    """How far the tab top is below the top of the bin body. Embossed labels stand on a tab lowered by their depth, so they keep the tab's offset"""
    return topOffset + (const.BIN_LABEL_DEPTH if labelStyle == LABEL_STYLE_EMBOSSED else 0)

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
        tabTopOffset: float = const.BIN_TAB_TOP_CLEARANCE,
        color: str = '',
        *,
        name: str,
        textOccurrence=None,
        targetOccurrence: adsk.fusion.Occurrence | None = None,
        binPlacement: tuple[float | Dim, float | Dim] = (0, 0),
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
    labelInput.originZ = tabOriginZ - Dim.length(tabTopClearance(style, tabTopOffset))
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
    planeInput.setByOffset(targetComponent.xYConstructionPlane, lengthInput(topZ))
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
    planeInput.setByOffset(targetComponent.xYConstructionPlane, lengthInput(topZ))
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
        scoopWalls: frozenset,
        scoopMaxRadius: float,
        hasBottomFillet: bool,
        targetComponent: adsk.fusion.Component,
        *,
        name: str,
        cornerRadii: dict | None = None,
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
    innerCutoutInput.scoopSides = scoopWalls
    innerCutoutInput.scoopMaxRadius = scoopMaxRadius
    innerCutoutInput.filletRadius = innerCutoutFilletRadius
    innerCutoutInput.hasBottomFillet = hasBottomFillet
    innerCutoutInput.cornerRadii = cornerRadii

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
        scoopWalls: frozenset,
        scoopMaxRadius: float,
        hasTab: bool,
        tabInput: BinBodyTabGeneratorInput,
        tabHollowWallThickness: float | None,
        tabOpenings: TabWallOpenings | None,
        targetComponent: adsk.fusion.Component,
        *,
        name: str,
        cornerRadii: dict | None = None,
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
        scoopWalls,
        scoopMaxRadius,
        True,
        targetComponent,
        name=f'{name} cavity',
        cornerRadii=cornerRadii,
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
