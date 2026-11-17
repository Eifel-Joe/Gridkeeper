"""
Where the small parts of the storage box after Pred's parametric Gridfinity Storage Box v1.1
(https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric, CC BY-NC, by Pred) sit, round
28 (p261). Fusion-free: each seat is a point and two axes in the box's frame (see predBox), its coordinates dims on the
box parameters, so the joint origins built there follow a size change.

Measured in Pred's file at 5 x 4 x 6 and 7 x 5 x 10 (fusion-auftraege/r28_tmp/pred_parts.json, tests/test_pred_box_seats.py):
- Latch: Pred's Latch:1 in front on the left, its origin 31 mm from the left wall, 0.25 mm in front of the wall, 0.05 mm
  under the box top; its x along -X, its z into the box. Jörg 16.11.2026: "Latches 2 vorne und 2 jeweils einer seitlich
  hinten": the other front one 31 mm from the right wall, the side ones 31 mm from the back wall, each turned to its wall.
- Handle pin: Pred's HandlePin ends at the handle bolt plane (the generator's lab(77.75)) and is centred on the bolt
  hole, 3.75 mm from the front and on the box middle height; the right one turned half round about z.
- Handle: on the pin axis in the box middle, it hangs from there (26.5 mm down, 3.5 mm up in Pred's file).
"""

from dataclasses import dataclass

from .dim import Dim
from .predBox import PredBoxDims

Axis = tuple[float, float, float]


def mm(value: float) -> Dim:
    return Dim.length(round(value / 10, 9))


# Pred's measures, mm
LATCH_FROM_WALL = 31.0
LATCH_OUT = 0.25
LATCH_UNDER_TOP = 0.05
BOLT_FROM_FRONT = 3.75
# the generator's label holders: x relative to the label edge, Pred measured with the left label edge at 79.75 mm
LABEL_EDGE = 79.75
BOLT_PLANE = 77.75


@dataclass(frozen=True)
class Seat:
    name: str
    x: Dim
    y: Dim
    z: Dim
    xAxis: Axis
    zAxis: Axis


def yAxis(seat: Seat) -> Axis:
    """z x x, the seat's third axis"""
    (zx, zy, zz), (xx, xy, xz) = seat.zAxis, seat.xAxis
    return (zy * xz - zz * xy, zz * xx - zx * xz, zx * xy - zy * xx)


def boltPlane(d: PredBoxDims) -> Dim:
    """x of the left handle bolt plane, as predBoxGenerator's lab(77.75)"""
    return d.midX - d.labelWidth / 2 + mm(BOLT_PLANE - LABEL_EDGE)


def boltHeight(d: PredBoxDims) -> Dim:
    """z of the handle bolt axis, as predBoxGenerator's mid(24.7): the box middle height"""
    return d.midZ


def seats(d: PredBoxDims) -> list[Seat]:
    """The seats in the order of predBoxParts.SEAT_NAMES"""
    W, L = d.outerWidth, d.outerLength
    latchZ = d.bodyTop - mm(LATCH_UNDER_TOP)
    out, fromWall = mm(LATCH_OUT), mm(LATCH_FROM_WALL)
    bolt = boltPlane(d)
    boltY, boltZ = mm(BOLT_FROM_FRONT), boltHeight(d)
    return [
        Seat('Latch front left', fromWall, out, latchZ, (-1, 0, 0), (0, 1, 0)),
        Seat('Latch front right', W - fromWall, out, latchZ, (-1, 0, 0), (0, 1, 0)),
        Seat('Latch left', out, L - fromWall, latchZ, (0, 1, 0), (1, 0, 0)),
        Seat('Latch right', W - out, L - fromWall, latchZ, (0, -1, 0), (-1, 0, 0)),
        Seat('Handle', d.midX, boltY, boltZ, (1, 0, 0), (0, 0, 1)),
        Seat('Handle pin left', bolt, boltY, boltZ, (1, 0, 0), (0, 0, 1)),
        Seat('Handle pin right', d.midX * 2 - bolt, boltY, boltZ, (-1, 0, 0), (0, 0, 1)),
    ]


def turnAboutZ(reference: Seat, seat: Seat) -> int:
    """
    Degrees about z that turn the reference seat's axes into the seat's, a multiple of 90. The box's joint origins stand
    upright with X along X (baseGenerator.createPointJointOrigins), a part's joint takes this angle from the pose of its
    first seat, the one Pred's file shows (round 28)
    """
    for angle in (0, 90, 180, -90):
        if _turned(reference.xAxis, angle) == tuple(seat.xAxis) and _turned(reference.zAxis, angle) == tuple(seat.zAxis):
            return angle
    raise ValueError(f'{seat.name} is no turn about z of {reference.name}')


def _turned(axis: Axis, angle: int) -> Axis:
    cos, sin = {0: (1, 0), 90: (0, 1), 180: (-1, 0), -90: (0, -1)}[angle]
    x, y, z = axis
    return (x * cos - y * sin + 0, x * sin + y * cos + 0, z)
