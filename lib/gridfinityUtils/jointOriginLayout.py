import adsk.core, adsk.fusion

from .dim import Dim, valueInput

# Joint origins at the cells of bin feet and baseplate sockets (round 15, p170). They used to share one sketch with
# reference dimensions and stayed put when the grid parameters changed; then each got a sketch point of its own with
# driving dims, since round 46 (p590) an offset joint origin, see createOffsetJointOrigins. Names stay as they were,
# joints made on them keep them


def createOffsetJointOrigins(
    points: list[tuple[str, Dim, Dim, Dim]],
    targetComponent: 'adsk.fusion.Component',
    *,
    name: str,
) -> 'list[adsk.fusion.JointOrigin]':
    """
    Joint origins named as given at x, y, z, Z up and X along X, without a sketch: each on the component's origin
    point, its offsets X, Y, Z the point's dims, so it follows the parameters they hold (an expression) or stays put (a
    number), signed. The box since round 45 (p480), bins, baseplates and inserts since round 46 (p590). They replace
    baseGenerator.createPointJointOrigins, which made a construction plane, a sketch, a sketch point and two driving
    distance dimensions per point (unsigned, so a point left of or below the origin needed its magnitude): same place
    and axes, 160 ms and 4 model parameters against 846 ms and 8 (fusion-auftraege/r45_probe.log). Sketches didn't
    follow moves of bodies, neither do these: the caller passes the spots after the placement. name is the family's
    name, the sketch way named its planes and sketches after it; kept so the callers read alike.
    Tested in tests/test_offset_joint_origins.py
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
