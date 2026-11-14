import adsk.core, adsk.fusion

from . import const, commonUtils, combineUtils, filletUtils, sketchUtils, cullenect
from .binBodyTabGenerator import tabFilletAllowance
from .dim import Dim, valueInput

# Socket for exchangeable Cullenect labels, Cullenect.scad by CullenJWebb (MIT),
# https://github.com/CullenJWebb/Cullenect-Labels: a rounded pocket 0.3 mm larger than the insert, 1.2 mm deep, with a
# rib along both long sides 0.2 mm above its floor that the latch of the insert clicks under

def _offsetPlane(base, offset: float, targetComponent: adsk.fusion.Component, name: str) -> adsk.fusion.ConstructionPlane:
    planeInput: adsk.fusion.ConstructionPlaneInput = targetComponent.constructionPlanes.createInput()
    planeInput.setByOffset(base, adsk.core.ValueInput.createByReal(offset))
    plane = targetComponent.constructionPlanes.add(planeInput)
    plane.name = name
    plane.isLightBulbOn = False
    return plane

def _extrude(profiles: adsk.core.ObjectCollection, distance: float, direction, targetComponent: adsk.fusion.Component, name: str) -> adsk.fusion.ExtrudeFeature:
    extrudeFeatures = targetComponent.features.extrudeFeatures
    extrudeInput = extrudeFeatures.createInput(profiles, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extrudeInput.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(distance)), direction)
    extrude = extrudeFeatures.add(extrudeInput)
    extrude.name = name
    return extrude

def createCullenectSocket(
    minX: Dim,
    maxX: Dim,
    tabOriginY: Dim,
    tabWidth: float,
    tabTopZ: Dim,
    baseWidth: Dim,
    socketOffset: float,
    overhangAngle: float,
    targetBody: adsk.fusion.BRepBody,
    targetComponent: adsk.fusion.Component,
    *,
    name: str,
) -> float | None:
    """Cuts the socket into the flat top of a tab between the given x, whose back edge is at the tab origin y, and returns
    its size in label units, none where not even half a unit fits. The socket takes the widest standard label width, so
    original inserts fit compartment tabs too, its width follows the base width parameter like Cullenect's.
    Built like createLabel: at the current spot with sketches on a plane at the current height, then moved by how far
    the parametric spot is from it, so a change of the parameters only changes the move and the width"""
    units = cullenect.socketUnits(maxX.value - minX.value, baseWidth.value, socketOffset)
    if units is None:
        commonUtils.debugLog(f'{name}: tab {(maxX.value - minX.value) * 10:.2f} mm long, too short for a Cullenect socket')
        return None

    features = targetComponent.features
    width = baseWidth * units - Dim.length(const.CULLENECT_WIDTH_REDUCTION) + Dim.length(socketOffset)
    height = cullenect.socketHeight(socketOffset)
    # in the middle of the tab top, but far enough from the front for the overhang below to keep a skin under the floor
    frontInset = cullenect.socketFrontInset(overhangAngle, tabFilletAllowance(overhangAngle, 0))
    centerX = (minX + maxX) / 2
    centerY = tabOriginY - Dim.length(min(tabWidth / 2, tabWidth - frontInset - height / 2))

    socketPlane = _offsetPlane(targetComponent.xYConstructionPlane, tabTopZ.value, targetComponent, f'{name} socket plane')
    socketSketch: adsk.fusion.Sketch = targetComponent.sketches.add(socketPlane)
    socketSketch.name = f'{name} socket sketch'
    sketchUtils.createCenteredRectangle(width, height, adsk.core.Point3D.create(centerX.value, centerY.value, 0), socketSketch)
    socketExtrude = _extrude(
        commonUtils.objectCollectionFromList([socketSketch.profiles.item(0)]),
        const.CULLENECT_LABEL_THICKNESS,
        adsk.fusion.ExtentDirections.NegativeExtentDirection,
        targetComponent,
        f'{name} socket',
    )
    socketBody = socketExtrude.bodies.item(0)
    socketBody.name = f'{name} socket'
    verticalEdges = [
        edge for edge in socketBody.edges
        if abs(edge.boundingBox.maxPoint.z - edge.boundingBox.minPoint.z - const.CULLENECT_LABEL_THICKNESS) < const.DEFAULT_FILTER_TOLERANCE
    ]
    filletUtils.createFillet(verticalEdges, const.CULLENECT_CORNER_RADIUS, False, targetComponent, name=f'{name} socket corners')

    # ribs along the long sides, straight like Cullenect's, the rounded corners leave their ends free
    ribPlane = _offsetPlane(
        socketPlane,
        const.CULLENECT_RIB_BOTTOM - const.CULLENECT_LABEL_THICKNESS,
        targetComponent,
        f'{name} socket ribs plane',
    )
    ribSketch: adsk.fusion.Sketch = targetComponent.sketches.add(ribPlane)
    ribSketch.name = f'{name} socket ribs sketch'
    ribDistance = height / 2 - const.CULLENECT_RIB_WIDTH / 2
    for ribCenterY in (centerY.value - ribDistance, centerY.value + ribDistance):
        sketchUtils.createCenteredRectangle(width, const.CULLENECT_RIB_WIDTH, adsk.core.Point3D.create(centerX.value, ribCenterY, 0), ribSketch)
    ribExtrude = _extrude(
        commonUtils.objectCollectionFromList(list(ribSketch.profiles)),
        const.CULLENECT_RIB_HEIGHT,
        adsk.fusion.ExtentDirections.PositiveExtentDirection,
        targetComponent,
        f'{name} socket ribs',
    )
    combineUtils.cutBody(socketBody, commonUtils.objectCollectionFromList(list(ribExtrude.bodies)), targetComponent, name=f'{name} socket ribs cut')

    shiftX = centerX - Dim.length(centerX.value)
    shiftY = centerY - Dim.length(centerY.value)
    shiftZ = tabTopZ - Dim.length(tabTopZ.value)
    if shiftX.isExpression or shiftY.isExpression or shiftZ.isExpression:
        moveInput = features.moveFeatures.createInput2(commonUtils.objectCollectionFromList([socketBody]))
        moveInput.defineAsTranslateXYZ(valueInput(shiftX), valueInput(shiftY), valueInput(shiftZ), True)
        features.moveFeatures.add(moveInput).name = f'{name} socket placement'

    combineUtils.cutBody(targetBody, commonUtils.objectCollectionFromList([socketBody]), targetComponent, name=f'{name} socket cut')
    commonUtils.debugLog(f'{name}: Cullenect socket {cullenect.describeSocket(units, baseWidth.value, socketOffset)}')
    return units
