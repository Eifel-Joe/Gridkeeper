import adsk.core, adsk.fusion

from .dim import Dim, valueInput

# Joint origins at the cells of bin feet and baseplate sockets (round 15, p170). They used to share one sketch with
# reference dimensions and stayed put when the grid parameters changed; now each is a point of its own built by
# baseGenerator.createPointJointOrigins, which drives its dims. Names stay as they were, joints made on them keep them


def createOffsetJointOrigins(
    points: list[tuple[str, Dim, Dim, Dim]],
    targetComponent: 'adsk.fusion.Component',
    *,
    name: str,
) -> 'list[adsk.fusion.JointOrigin]':
    """
    Joint origins named as given at x, y, z, Z up and X along X, as baseGenerator.createPointJointOrigins makes them,
    without a sketch (round 45, p480): each on the component's origin point, its offsets X, Y, Z the point's dims, so it
    follows the parameters they hold (an expression) or stays put (a number), signed. Same place and axes as the sketch
    way, 160 ms and 4 model parameters against 846 ms and 8 with plane, sketch, point and two dimensions; a box makes
    35 of them (fusion-auftraege/r45_probe.log). Sketches don't follow moves of bodies, neither do these: the caller
    passes the spots after the placement. name is the family's name, kept for the caller's symmetry with
    createPointJointOrigins (it named their planes and sketches). Tested in tests/test_offset_joint_origins.py
    """
    jointOrigins = []
    for (pointName, x, y, z) in points:
        jointOriginInput = targetComponent.jointOrigins.createInput(adsk.fusion.JointGeometry.createByPoint(targetComponent.originConstructionPoint))
        jointOriginInput.offsetX = valueInput(x)
        jointOriginInput.offsetY = valueInput(y)
        jointOriginInput.offsetZ = valueInput(z)
        jointOrigin = targetComponent.jointOrigins.add(jointOriginInput)
        jointOrigin.name = pointName
        jointOrigins.append(jointOrigin)
    return jointOrigins


def jointOriginPlace(jointOrigin) -> 'adsk.core.Point3D':
    """
    Where a joint origin is, in its component (a native one) or the root (a proxy): its transform's translation. The
    geometry's origin is the point it is made on, without the offsets of createOffsetJointOrigins (the component's
    origin for the box's joint origins since round 45, fusion-auftraege/r45_probe.log); for a joint origin on a sketch
    point both are the same point. Tested in tests/test_offset_joint_origins.py
    """
    translation = jointOrigin.transform.translation
    return adsk.core.Point3D.create(translation.x, translation.y, translation.z)


def cellJointOriginPoints(centers: list[tuple[int, int, Dim, Dim]], name: str, z: Dim) -> list[tuple[str, Dim, Dim, Dim]]:
    """The name, x, y and z of a joint origin at each cell center, named by its column and row from 1"""
    return [(f'{name} {column + 1}-{row + 1}', x, y, z) for (column, row, x, y) in centers]
