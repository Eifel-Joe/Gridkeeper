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
from .predBoxParts import DEFAULT_HINGE, seatJointOriginName

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


def seats(d: PredBoxDims, hinge: str = DEFAULT_HINGE) -> list[Seat]:
    """The seats in the order of predBoxParts.SEAT_NAMES, the hinges' for the chosen variant"""
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
    ] + [Seat(name, mm(x), mm(y), mm(z), (1, 0, 0), (0, 0, 1)) for (name, (x, y, z)) in zip(('Hinge 1', 'Hinge 2'), hingeOrigins(hinge))]


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


# the handle reaches 14.25 mm past each label edge (Pred's file: 99 mm at 5 x 4 x 6, 113.5 mm at 7 x 5 x 10)
HANDLE_PAST_LABEL = 28.5


def handleWidth(d: PredBoxDims) -> Dim:
    """
    The handle's width, the one measure of a small part that follows the box: the label width + 28.5 mm, so 57 mm at 4
    cells wide, 99 mm at 5 and 113.5 mm from 6 on (Jörg 17.11.2026: "Der Griff bleibt bei Max. 113,5mm stehen. Breiter
    macht keinen Sinn."). The inserted handle's width dimension gets this expression
    """
    return d.labelWidth + mm(HANDLE_PAST_LABEL)


def seatJointOriginPoints(d: PredBoxDims, hinge: str = DEFAULT_HINGE) -> list[tuple[str, Dim, Dim, Dim]]:
    """
    The box's joint origins at the seats, for baseGenerator.createPointJointOrigins: upright, X along X; a part's
    joint takes its turn about z (turnAboutZ). Round 28, plan task 5
    """
    return [(seatJointOriginName(seat.name), seat.x, seat.y, seat.z) for seat in seats(d, hinge)]


def handleHalfWidth(d: PredBoxDims) -> Dim:
    """The expression the inserted handle's one size dimension (HandleHalfWidth, resources/predBox/handle.f3d) gets"""
    return handleWidth(d) / 2


# The hinges in their print position beside the box, jointed there at their component's origin (Jörg 17.11.2026, "Ja,
# beides" to Vorschlag J): each variant with the corner of its body box (least x, y, z) where Hinge_M3x30's is in Pred's
# file, the second 5 mm beside it in y from its own depth; they don't follow the box size. mm, from
# fusion-auftraege/r28_tmp/pred_parts.json and the part files (r28_extract.l5-l7.out)
M3X30_CORNER = (-61.2502, 36.5039, -12.2095)
# per variant: the corner of its bodies in its component, and its depth in y
HINGE_BODY_BOX = {
    'M3x30': ((-9.2516, -4.0, 0.0), 12.8),
    'Pinned': ((-9.2516, -4.0, 0.0), 12.8),
    'Plain': ((-76.2325, -3.5, 0.0), 12.0),
}
HINGE_GAP = 5.0


def hingeOrigins(hinge: str) -> list[tuple[float, float, float]]:
    """Where the two hinges' component origins go in the box's frame, mm"""
    (low, depth) = HINGE_BODY_BOX[hinge]
    first = tuple(round(c - l, 4) for c, l in zip(M3X30_CORNER, low))
    return [first, (first[0], round(first[1] + depth + HINGE_GAP, 4), first[2])]
