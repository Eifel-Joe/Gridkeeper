import adsk.core, adsk.fusion, traceback
import os
import math

from ...lib.gridfinityUtils import geometryUtils
from ...lib import fusion360utils as futil
from ...lib.gridfinityUtils import filletUtils
from . import const, combineUtils, faceUtils, commonUtils, sketchUtils, extrudeUtils, baseGenerator, edgeUtils, scoopSides
from .baseGeneratorInput import BaseGeneratorInput
from .binBodyCutoutGeneratorInput import BinBodyCutoutGeneratorInput
from .dim import Dim, lengthInput
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

def getInnerCutoutWallFaces(
    innerCutout: adsk.fusion.BRepBody
    ) -> dict[str, adsk.fusion.BRepFace]:
    """The flat wall faces of the cavity cutter by the bin wall they face, see scoopSides"""
    (front, back) = faceUtils.getNormalFaceExtremes(innerCutout.faces, 'y')
    (left, right) = faceUtils.getNormalFaceExtremes(innerCutout.faces, 'x')
    return {scoopSides.FRONT: front, scoopSides.BACK: back, scoopSides.LEFT: left, scoopSides.RIGHT: right}

def cornerFilletGroups(body: adsk.fusion.BRepBody, edges: list, radius: float, cornerRadii: dict | None) -> list[tuple[float, list]]:
    """
    The vertical edges of a cavity cutter by the radius of their corner: (left or right, front or back) as the keys of
    cornerRadii, radius for corners not in it; edges of a corner of radius 0 are left out (round 50)
    """
    if not cornerRadii:
        return [(radius, edges)]
    box = body.boundingBox
    (midX, midY) = ((box.minPoint.x + box.maxPoint.x) / 2, (box.minPoint.y + box.maxPoint.y) / 2)
    groups: dict[float, list] = {}
    for edge in edges:
        point = edge.startVertex.geometry
        corner = (scoopSides.LEFT if point.x < midX else scoopSides.RIGHT, scoopSides.FRONT if point.y < midY else scoopSides.BACK)
        edgeRadius = round(cornerRadii.get(corner, radius), 6)
        if edgeRadius > const.DEFAULT_FILTER_TOLERANCE * 10:
            groups.setdefault(edgeRadius, []).append(edge)
    return sorted(groups.items(), key=lambda item: -item[0])

def createGridfinityBinBodyCutout(
    input: BinBodyCutoutGeneratorInput,
    targetComponent: adsk.fusion.Component,
    *,
    name: str,
):
    """The body and all its features are named after the given name"""

    cutoutPlaneInput: adsk.fusion.ConstructionPlaneInput = targetComponent.constructionPlanes.createInput()
    cutoutPlaneInput.setByOffset(
        targetComponent.xYConstructionPlane,
        lengthInput(input.originZ)
    )
    cutoutConstructionPlane = targetComponent.constructionPlanes.add(cutoutPlaneInput)
    cutoutConstructionPlane.name = f'{name} plane'
    innerCutoutSketch: adsk.fusion.Sketch = targetComponent.sketches.add(cutoutConstructionPlane)
    innerCutoutSketch.name = f'{name} sketch'
    sketchUtils.createRectangle(
        input.width,
        input.length,
        adsk.core.Point3D.create(input.origin.x, input.origin.y, 0),
        innerCutoutSketch,
        startX=input.originX,
        startY=input.originY,
    )

    innerCutout = extrudeUtils.simpleDistanceExtrude(
        innerCutoutSketch.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        input.height,
        adsk.fusion.ExtentDirections.NegativeExtentDirection,
        [],
        targetComponent,
        name=name,
    )
    innerCutoutBody = innerCutout.bodies.item(0)
    innerCutoutBody.name = name

    # scoops, the bottom edges of every scoop wall in one fillet so two scoops meeting at a corner blend there
    if len(input.scoopSides) > 0:
        wallFaces = getInnerCutoutWallFaces(innerCutoutBody)
        scoopEdges = [
            faceUtils.getBottomHorizontalEdge(wallFaces[side].edges)
            for side in scoopSides.SIDES_ORDER if side in input.scoopSides
        ]
        # a margin less deep than the cutout at most and as round as its corners at least, an expression of the cutout
        # depth so it still fits once the height unit changes, see const.BIN_SCOOP_TOP_MARGIN
        scoopRadius = Dim.min(Dim.length(input.scoopMaxRadius), Dim.asLength(input.height) - Dim.length(const.BIN_SCOOP_TOP_MARGIN))
        # two scoops facing each other share the span, a single one per axis keeps the limit it had before round 48
        for limit in scoopSides.scoopRadiusSpanLimits(
            input.scoopSides, Dim.asLength(input.width), Dim.asLength(input.length), Dim.length(const.BIN_SCOOP_FLOOR_MARGIN)):
            scoopRadius = Dim.min(scoopRadius, limit)
        scoopMaxRadius = Dim.max(scoopRadius, Dim.length(input.filletRadius))
        filletUtils.createFillet(
            scoopEdges,
            scoopMaxRadius,
            False,
            targetComponent,
            name=f'{name} scoop',
        )
    # fillet inner cutout, corners of their own radius each in a fillet of their own (round 50), none where it's 0
    innerCutoutVerticalFaces = faceUtils.getVerticalEdges(innerCutoutBody.faces)
    for (radius, edges) in cornerFilletGroups(innerCutoutBody, innerCutoutVerticalFaces, input.filletRadius, input.cornerRadii):
        filletUtils.createFillet(
            edges,
            radius,
            True,
            targetComponent,
            name=f'{name} corner fillets' if radius == input.filletRadius else f'{name} corner fillets {radius * 10:.2f} mm',
        )
    # the bottom fillet runs along the floor from the first wall without a scoop, the back as before round 48, through
    # the corners. With more than one scoop the floor edges stay sharp, Fusion can't fillet a chain running into two
    # scoops, see scoopSides.bottomFilletSides
    plainSides = scoopSides.bottomFilletSides(input.scoopSides)
    floorRadius = scoopSides.floorFilletRadius(input.filletRadius, input.cornerRadii)
    # beside a scoop no deeper than the cavity (p652)
    floorRadius = scoopSides.scoopFloorRadius(floorRadius, Dim.asLength(input.height).value, input.scoopSides, margin=const.BIN_SCOOP_TOP_MARGIN)
    if input.hasBottomFillet and len(plainSides) > 0 and floorRadius > const.DEFAULT_FILTER_TOLERANCE * 10:
        # recalculate faces after fillet
        wallFaces = getInnerCutoutWallFaces(innerCutoutBody)
        bottomEdges = []
        chained = set()
        for side in plainSides:
            edge = faceUtils.getBottomHorizontalEdge(wallFaces[side].edges)
            if edge.tempId in chained:
                continue
            bottomEdges.append(edge)
            chained.update(chainEdge.tempId for chainEdge in edge.tangentiallyConnectedEdges)

        filletUtils.createFillet(
            bottomEdges,
            floorRadius,
            True,
            targetComponent,
            name=f'{name} bottom fillet',
        )

    return innerCutoutBody
