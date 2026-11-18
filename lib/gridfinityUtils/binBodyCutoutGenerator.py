import adsk.core, adsk.fusion, traceback
import os
import math

from ...lib.gridfinityUtils import geometryUtils
from ...lib import fusion360utils as futil
from ...lib.gridfinityUtils import filletUtils
from . import const, combineUtils, faceUtils, commonUtils, sketchUtils, extrudeUtils, baseGenerator, edgeUtils, scoopSides
from .baseGeneratorInput import BaseGeneratorInput
from .binBodyCutoutGeneratorInput import BinBodyCutoutGeneratorInput
from .dim import Dim, valueInput
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
        valueInput(input.originZ)
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
        scoopMaxRadius = Dim.max(
            Dim.min(Dim.length(input.scoopMaxRadius), Dim.asLength(input.height) - Dim.length(const.BIN_SCOOP_TOP_MARGIN)),
            Dim.length(input.filletRadius),
        )
        filletUtils.createFillet(
            scoopEdges,
            scoopMaxRadius,
            False,
            targetComponent,
            name=f'{name} scoop',
        )
    # fillet inner cutout
    innerCutoutVerticalFaces = faceUtils.getVerticalEdges(innerCutoutBody.faces)
    filletUtils.createFillet(
        innerCutoutVerticalFaces,
        input.filletRadius,
        True,
        targetComponent,
        name=f'{name} corner fillets',
    )
    # the bottom fillet runs along the floor from the first wall without a scoop, the back as before round 48, through
    # the corners. A wall without a scoop the chain doesn't reach, between two scoops, adds its edge. Four scoops leave
    # no straight bottom edge
    plainSides = [side for side in scoopSides.SIDES_ORDER if side not in input.scoopSides]
    if input.hasBottomFillet and len(plainSides) > 0:
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
            input.filletRadius,
            True,
            targetComponent,
            name=f'{name} bottom fillet',
        )

    return innerCutoutBody
