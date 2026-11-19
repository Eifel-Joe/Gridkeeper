import adsk.core, adsk.fusion, traceback
import os
import math
import copy

from ...lib import fusion360utils as futil
from . import const, combineUtils, faceUtils, commonUtils, extrudeUtils, baseGenerator, edgeUtils, filletUtils, geometryUtils, patternUtils, binShape, scoopSides
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
from .raisedDividers import DividerSegment, ridgeBox, raisedSides, cornerRadiusBetween, ridgeTipDepth, TIP, tipCornersBesideRidge, tabTopRise
from .dim import Dim, valueInput
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
                adsk.core.ValueInput.createByReal(lipBottomChamferSize),
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

        # Round 50: raised dividers carry the lip's profile on both sides, a ridge centred on their grid line, its tip
        # as far from it as the lip's tip is from the grid line at the outer wall
        hasRidges = input.hasLip and len(input.raisedDividers) > 0
        ridgeTip = lipInnerInset(input.lipType, input.xyClearance) + Dim.length(input.xyClearance)

        def gridLineAt(axis: str, line: int) -> Dim:
            """Where a grid line of the compartment grid lies, across x for axis 'x', on the body: whole cells of the
            base from the grid's edge, a clearance outside the body"""
            (base, cells, count) = (input.baseWidth, input.binWidth, input.compartmentsByX) if axis == 'x' else (input.baseLength, input.binLength, input.compartmentsByY)
            return base * Dim.number(round(line * cells / count, 6)) - Dim.length(input.xyClearance)

        def ridgeSides(compartment: BinBodyCompartmentDefinition) -> frozenset:
            """The compartment's sides on a raised divider"""
            if not hasRidges:
                return frozenset()
            return raisedSides((compartment.positionX, compartment.positionY, compartment.width, compartment.length), input.raisedDividers)

        def compartmentPlacement(compartment: BinBodyCompartmentDefinition) -> tuple[Dim, Dim, Dim, Dim]:
            """X, y, width and length of the compartment cavity, shortened along a trimmed scoop wall, and starting at
            the ridge's tip on a raised divider with a scoop on it, as at an outer scoop wall (round 50, decided)"""
            (x, y, width, length) = compartmentCell(compartment)
            scoopRidges = ridgeSides(compartment) & compartment.scoopSides
            if scoopSides.LEFT in scoopRidges:
                start = gridLineAt('x', compartment.positionX) + ridgeTip
                (x, width) = (start, x + width - start)
            if scoopSides.RIGHT in scoopRidges:
                width = gridLineAt('x', compartment.positionX + compartment.width) - ridgeTip - x
            if scoopSides.FRONT in scoopRidges:
                start = gridLineAt('y', compartment.positionY) + ridgeTip
                (y, length) = (start, y + length - start)
            if scoopSides.BACK in scoopRidges:
                length = gridLineAt('y', compartment.positionY + compartment.length) - ridgeTip - y
            return (x, y, width, length)

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

        # how deep under the body top the cavities' top is cut: the compartments top clearance, see below
        clearanceDepth = input.tabTopOffset if len(input.compartments) > 1 and input.tabTopOffset > 0 else 0
        cavityCornerRadius = compartmentCutoutFilletRadius(input.binCornerFilletRadius - input.wallThickness)

        def sideCover(compartment: BinBodyCompartmentDefinition, side: str) -> float | None:
            """How wide a strip from the compartment's side covers its corners from above where the cavity's top is
            cut, None for a side that limits nothing (round 50, decided option a, see raisedDividers.coveredCornerRadius)"""
            (column, row, columns, rows) = (compartment.positionX, compartment.positionY, compartment.width, compartment.length)
            line = {scoopSides.LEFT: ('x', column), scoopSides.RIGHT: ('x', column + columns),
                    scoopSides.FRONT: ('y', row), scoopSides.BACK: ('y', row + rows)}[side]
            if side in ridgeSides(compartment):
                if side in compartment.scoopSides:
                    # the cavity starts at the ridge's tip
                    return TIP
                (cellX, cellY, cellWidth, cellLength) = compartmentCell(compartment)
                face = {scoopSides.LEFT: cellX, scoopSides.RIGHT: cellX + cellWidth,
                        scoopSides.FRONT: cellY, scoopSides.BACK: cellY + cellLength}[side]
                overhang = ridgeTip.value - abs((gridLineAt(*line) - face).value)
                # its straight face under the tip reaches down to the cut top, see raisedDividers.ridgeTipDepth
                return overhang
            isOuter = line[1] == 0 or line[1] == (input.compartmentsByX if line[0] == 'x' else input.compartmentsByY)
            if not isOuter:
                return None
            if side in outerScoopWalls:
                # the cavity starts at the lip's tip
                return TIP
            if lipSupport is None or clearanceDepth > const.BIN_LIP_SUPPORT_WALL_HEIGHT:
                return 0
            # a full lip's support, straight down from its tip
            return (scoopInset - wall).value

        # a cavity corner between two scoop walls follows the lip's inner corner (p653, round 50)
        scoopCorner = scoopSides.scoopCornerRadius(cavityCornerRadius, input.binCornerFilletRadius, scoopInset.value)

        def cornerRadii(compartment: BinBodyCompartmentDefinition) -> dict | None:
            """The compartment's own corner radii: beside a ridge, see ridgeCornerRadii, and between two scoop walls"""
            radii = ridgeCornerRadii(compartment) or {}
            for corner in scoopSides.scoopWallCorners(
                outerScoopWalls, (compartment.positionX, compartment.positionY),
                (compartment.width, compartment.length), (input.compartmentsByX, input.compartmentsByY)):
                radii[corner] = min(radii.get(corner, cavityCornerRadius), scoopCorner)
            if len(radii) == 0:
                return None
            if len(scoopSides.bottomFilletSides(compartment.scoopSides)) > 0:
                # a floor fillet runs round the corners, all alike at the tightest, see ridgeCornerRadii
                tightest = min(radii.values())
                return {(sideX, sideY): tightest for sideX in (scoopSides.LEFT, scoopSides.RIGHT) for sideY in (scoopSides.FRONT, scoopSides.BACK)}
            return radii

        def ridgeCornerRadii(compartment: BinBodyCompartmentDefinition) -> dict | None:
            """
            The corners of a compartment beside a ridge, rounded as far as covered (round 50, decided option a), all four
            alike with the tightest: corners of different radii broke the floor's outline beside a scoop into edges
            Fusion found no fillet for (shown in Fusion, the floor fillet at the tightest radius too)
            """
            ridges = ridgeSides(compartment)
            if len(ridges) == 0:
                return None
            radii = {}
            for sideX in (scoopSides.LEFT, scoopSides.RIGHT):
                for sideY in (scoopSides.FRONT, scoopSides.BACK):
                    if sideX not in ridges and sideY not in ridges:
                        continue
                    covers = [sideCover(compartment, side) for side in (sideX, sideY)]
                    if None in covers:
                        # a lowered divider beside: its top takes the fillet's
                        continue
                    radii[(sideX, sideY)] = cornerRadiusBetween(cavityCornerRadius, covers[0], covers[1], tipCorner=scoopCorner)
            if len(radii) == 0:
                return None
            tightest = min(radii.values())
            return {(sideX, sideY): tightest for sideX in (scoopSides.LEFT, scoopSides.RIGHT) for sideY in (scoopSides.FRONT, scoopSides.BACK)}

        def tipCornerFills(compartment: BinBodyCompartmentDefinition, cavity: adsk.fusion.BRepBody, cell: tuple, name: str) -> list[adsk.fusion.BRepBody]:
            """
            Fills of the rounded corners between two tip faces beside a ridge, from the cut cavity top up to the top of
            the lip: the compartments top clearance cut them flat, and above the body top neither the ridge, a box, nor
            the lip reaches past its tip into the corner, a level face was left there (review round 50, 0.29 mm2 ledges
            shown in Fusion at both heights). Each a box in the corner less the compartment's cavity, cut by the feet of
            a stacked bin with the ridges, which round it above the body top as they round the lip at the bin's corners
            """
            sides = (scoopSides.LEFT, scoopSides.RIGHT, scoopSides.FRONT, scoopSides.BACK)
            covers = {side: sideCover(compartment, side) for side in sides}
            radii = cornerRadii(compartment) or {}
            (x, y, width, length) = cell
            fills = []
            for (sideX, sideY) in tipCornersBesideRidge(covers, ridgeSides(compartment)):
                radius = Dim.length(radii.get((sideX, sideY), cavityCornerRadius))
                originX = x if sideX == scoopSides.LEFT else x + width - radius
                originY = y if sideY == scoopSides.FRONT else y + length - radius
                bottomZ = binBodyTotalHeight - Dim.length(clearanceDepth)
                box = extrudeUtils.createBoxAtPoint(
                    radius, radius, clearanceDepth + const.BIN_LIP_EXTRA_HEIGHT - input.lipTopTrimHeight, targetComponent,
                    adsk.core.Point3D.create(originX.value, originY.value, bottomZ.value), bottomZ,
                    originX=originX, originY=originY, name=f'{name} corner fill {sideX} {sideY}',
                ).bodies.item(0)
                if clearanceDepth > 0:
                    # without a cut top the box starts on the cavity's top, nothing to take off
                    combineUtils.cutBody(box, commonUtils.objectCollectionFromList([cavity]), targetComponent, isKeepToolBodies=True, name=f'{name} corner fill {sideX} {sideY} shape')
                fills.append(box)
            return fills

        def tabPlacement(compartment: BinBodyCompartmentDefinition, compartmentX: Dim, compartmentY: Dim, compartmentLength: Dim) -> tuple[Dim, Dim, Dim]:
            """X and y of the tab's back top corner, along the compartment's back wall or, on a raised divider, at its
            ridge's tip (round 50, decided: the ridge would cover a Cullenect socket's back), and its length"""
            if scoopSides.BACK in ridgeSides(compartment):
                back = gridLineAt('y', compartment.positionY + compartment.length) - ridgeTip
            else:
                back = compartmentY + compartmentLength
            return (
                compartmentX + input.baseWidth * max(0, min(input.tabPosition, input.binWidth - input.tabLength)),
                back,
                input.baseWidth * max(0, min(input.tabLength, input.binWidth)),
            )

        # trimmed compartments are patterned only while all are trimmed alike, compartments beside a ridge differ in
        # their tabs and scoops (round 50)
        useCompartmentPattern = (input.isUniformCompartments and len(input.compartments) > 1 and not hasRidges
            # a corner between two scoop walls of one compartment only (p653, review round 50)
            and all(cornerRadii(compartment) is None for compartment in input.compartments)
            and scoopSides.trimsKeepAlike(gridTrims, (input.compartmentsByX, input.compartmentsByY)))
        compartmentsToBuild = input.compartments[:1] if useCompartmentPattern else input.compartments
        # corner fills beside ridges, cut by the stacked feet with the ridges
        cornerFills: list[adsk.fusion.BRepBody] = []
        for compartmentIndex, compartment in enumerate(compartmentsToBuild):
            compartmentName = 'Compartment' if len(compartmentsToBuild) == 1 else f'Compartment {compartmentIndex + 1}'
            (compartmentX, compartmentY, compartmentWidth, compartmentLength) = compartmentPlacement(compartment)
            # full depth compartments keep their floor thickness, shallower ones keep their depth from the top
            fullCompartmentDepth = binBodyTotalHeight - Dim.length(const.BIN_COMPARTMENT_BOTTOM_THICKNESS)
            compartmentDepth = fullCompartmentDepth if compartment.depth >= fullCompartmentDepth.value else compartment.depth

            compartmentTabInput = BinBodyTabGeneratorInput()
            (tabOriginX, tabOriginY, tabLength) = tabPlacement(compartment, compartmentX, compartmentY, compartmentLength)
            compartmentTabInput.origin = adsk.core.Point3D.create(tabOriginX.value, tabOriginY.value, binBodyTotalHeight.value)
            compartmentTabInput.originX = tabOriginX
            compartmentTabInput.originY = tabOriginY
            compartmentTabInput.originZ = binBodyTotalHeight
            compartmentTabInput.length = tabLength
            compartmentTabInput.width = input.tabWidth
            # in front of a ridge the label and its pocket start at the ridge's tip, the tab's body still reaches back
            # to the divider: from the tip it left an open slot behind it, and a hollow tab lost its back wall
            # (review round 50)
            behindTab = compartmentY + compartmentLength - tabOriginY
            if behindTab.value > const.DEFAULT_FILTER_TOLERANCE:
                compartmentTabInput.origin = adsk.core.Point3D.create(tabOriginX.value, (tabOriginY + behindTab).value, binBodyTotalHeight.value)
                compartmentTabInput.originY = tabOriginY + behindTab
                compartmentTabInput.width = input.tabWidth + behindTab.value
            compartmentTabInput.overhangAngle = input.tabOverhangAngle
            compartmentTabInput.labelAngle = input.tabTopAngle
            compartmentTabInput.topClearance = tabTopClearance(input.labelStyle, input.tabTopOffset)
            if behindTab.value > const.DEFAULT_FILTER_TOLERANCE:
                # its sloped top as high at the ridge's tip as the label and pocket expect it there (re-review round 50)
                compartmentTabInput.topClearance -= tabTopRise(behindTab.value, input.tabTopAngle)
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
            cornerFills.extend(tipCornerFills(compartment, compartmentCuts[0], (compartmentX, compartmentY, compartmentWidth, compartmentLength), compartmentName))
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

        if hasRidges:
            # Round 50: the ridges' feet and supports shape the corners, the rounding of p83 is no longer built
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
                gridTrims,
                gridLineAt,
                ridgeTip,
                -ridgeTipDepth(isFullLip=input.lipType == LIP_TYPE_FULL, clearanceDepth=clearanceDepth, supportWall=const.BIN_LIP_SUPPORT_WALL_HEIGHT),
                binBodyTotalHeight.value - const.BIN_COMPARTMENT_BOTTOM_THICKNESS,
                cornerFills,
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
            (tabOriginX, tabOriginY, tabLength) = tabPlacement(compartment, compartmentX, compartmentY, compartmentLength)
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
    trims: dict,
    gridLineAt,
    ridgeTip: Dim,
    tipLift: float,
    floorDepth: float,
    cornerFills: list[adsk.fusion.BRepBody],
) -> list[adsk.fusion.BRepBody]:
    """
    Ridges on the dividers on grid lines, up to the top of the lip, cut by the feet of a bin stacked on top like a
    notched lip, so they run out in the lip's profile on both sides (round 50, decided; until then a flat topped wall
    as thick as the divider, round 8, p61). Each is a box centred on its grid line, as wide as the lip's tips either
    side, from under the divider top down to where its bottom edges, chamfered at 45 degrees in to the divider's faces,
    keep it from overhanging the compartments, see raisedDividers.ridgeBox. Segments reach a wall further where they
    meet a crossing divider, and half a wall into the outer walls, which keeps every box corner off the sketch axes
    """
    boxes: list[adsk.fusion.BRepBody] = []
    for (index, segment) in enumerate(segments):
        # across is the axis the wall stands on, along the one it runs on
        (across, along) = (0, 1) if segment.axis == 'x' else (1, 0)
        wallStart = compartmentsMin[across] + pitch[across] * segment.line - wall
        startReach = wall / 2 if segment.start == 0 else wall
        endReach = wall / 2 if segment.end == counts[along] else wall
        # the first cavity starts at the min, the last one ends a wall short of the next pitch
        runStart = compartmentsMin[along] + pitch[along] * segment.start - startReach
        runLength = pitch[along] * (segment.end - segment.start) - wall + startReach + endReach
        # at a trimmed scoop wall from its trimmed cavity, as before the grid kept to the grid lines (round 50): from
        # the grid's start it reached out under the lip, faces nearly coincident with the lip's (shown in Fusion)
        (startTrim, endTrim) = scoopSides.runTrims(segment.axis, segment.start, segment.end, counts, trims)
        if startTrim is not None:
            runStart = runStart + startTrim
            runLength = runLength - startTrim
        if endTrim is not None:
            runLength = runLength - endTrim
        grid = gridLineAt(segment.axis, segment.line)
        (depth, lowChamfer, highChamfer) = ridgeBox(
            ridgeTip.value,
            (grid - wallStart).value,
            (wallStart + wall - grid).value,
            tipLift=tipLift,
            minDepth=topOffset,
            maxDepth=floorDepth,
        )
        bottomZ = binBodyTotalHeight - Dim.length(depth)
        # up to the lip top, trimmed or not (upstream round 17.11.2026, p13)
        height = depth + const.BIN_LIP_EXTRA_HEIGHT - lipInput.topTrimHeight
        acrossStart = grid - ridgeTip
        if segment.axis == 'x':
            (originX, originY, width, length) = (acrossStart, runStart, ridgeTip * 2, runLength)
        else:
            (originX, originY, width, length) = (runStart, acrossStart, runLength, ridgeTip * 2)
        name = f'Raised divider {index + 1}'
        box = extrudeUtils.createBoxAtPoint(
            width,
            length,
            height,
            targetComponent,
            adsk.core.Point3D.create(originX.value, originY.value, bottomZ.value),
            bottomZ,
            originX=originX,
            originY=originY,
            name=name,
        )
        body = box.bodies.item(0)
        # the bottom edges along the ridge, on its low and high side across
        acrossAxis = 0 if segment.axis == 'x' else 1
        alongRidge = geometryUtils.isCollinearToY if segment.axis == 'x' else geometryUtils.isCollinearToX
        bottomEdges = [edge for edge in faceUtils.getBottomFace(body).edges if alongRidge(edge)]
        lowEdge = min(bottomEdges, key=lambda edge: edge.boundingBox.minPoint.asArray()[acrossAxis])
        highEdge = max(bottomEdges, key=lambda edge: edge.boundingBox.minPoint.asArray()[acrossAxis])
        for (edge, chamfer, side) in ((lowEdge, lowChamfer, 'low'), (highEdge, highChamfer, 'high')):
            # a divider as wide as the ridge on that side needs no support
            if chamfer > const.DEFAULT_FILTER_TOLERANCE:
                filletUtils.createChamfer(commonUtils.objectCollectionFromList([edge]), chamfer, targetComponent, name=f'{name} {side} support')
        boxes.append(body)
    # the corner fills beside the ridges are cut with them, see tipCornerFills
    boxes.extend(cornerFills)
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
