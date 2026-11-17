"""
Where the small parts of the storage box after Pred's parametric Gridfinity Storage Box v1.1
(https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric, CC BY-NC, by Pred) sit, round
28 (p261). Fusion-free: each seat is a point and two axes in the box's frame (see predBox), its coordinates dims on the
box parameters, so the joint origins built there follow a size change.

Measured in Pred's file at 5 x 4 x 6 and 7 x 5 x 10 (fusion-auftraege/r28_tmp/pred_parts.json, tests/test_pred_box_seats.py):
- Latch: Pred's Latch:1 in front on the left, its origin 31 mm from the left wall, 0.25 mm in front of the wall, 0.05 mm
  under the box top; its x along -X, its z into the box. Nutzer 16.11.2026: "Latches 2 vorne und 2 jeweils einer seitlich
  hinten": the other front one 31 mm from the right wall, the side ones 31 mm from the back wall, each turned to its wall.
- Handle pin: Pred's HandlePin ends at the handle bolt plane (the generator's lab(77.75)) and is centred on the bolt
  hole, 3.75 mm from the front and on the box middle height; the right one turned half round about z.
- Handle: on the pin axis in the box middle, it hangs from there (26.5 mm down, 3.5 mm up in Pred's file).
"""

from dataclasses import dataclass

from .dim import Dim
from .predBox import PredBoxDims
from .predBoxParts import seatJointOriginName

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


# the handle reaches 14.25 mm past each label edge (Pred's file: 99 mm at 5 x 4 x 6, 113.5 mm at 7 x 5 x 10)
HANDLE_PAST_LABEL = 28.5


def handleWidth(d: PredBoxDims) -> Dim:
    """
    The handle's width, the one measure of a small part that follows the box: the label width + 28.5 mm, so 57 mm at 4
    cells wide, 99 mm at 5 and 113.5 mm from 6 on (Nutzer 17.11.2026: "Der Griff bleibt bei Max. 113,5mm stehen. Breiter
    macht keinen Sinn."). The inserted handle's width dimension gets this expression
    """
    return d.labelWidth + mm(HANDLE_PAST_LABEL)


def seatJointOriginPoints(d: PredBoxDims) -> list[tuple[str, Dim, Dim, Dim]]:
    """
    The box's joint origins at the seats, for baseGenerator.createPointJointOrigins: upright, X along X; a part's
    joint takes its turn about z (turnAboutZ). Round 28, plan task 5
    """
    return [(seatJointOriginName(seat.name), seat.x, seat.y, seat.z) for seat in seats(d)]


def handleHalfWidth(d: PredBoxDims) -> Dim:
    """The expression the inserted handle's one size dimension (HandleHalfWidth, resources/predBox/handle.f3d) gets"""
    return handleWidth(d) / 2


# the hinges beside the box in their print position (plan decision 6): the first where Pred's Hinge_M3x30:1 is, mm
# (fusion-auftraege/r28_tmp/pred_parts.json), the second beside it in y with a gap of 5 mm (Pred's file has one hinge)
PRED_HINGE_ORIGIN = (-51.9986, 40.5039, -12.2095)
HINGE_DEPTH = 12.8
HINGE_GAP = 5.0


def hingePlaces() -> list[tuple[float, float, float]]:
    """Where the hinges' origins go in the set, mm; they don't follow the box size"""
    x, y, z = PRED_HINGE_ORIGIN
    return [(x, y, z), (x, round(y + HINGE_DEPTH + HINGE_GAP, 4), z)]


def placeInSet(native, setOccurrence, inContext, transform):
    """
    Puts a part's occurrence where transform says, transform in the set's frame; returns its proxy from the root.

    Root cause (r28_insert_check l1, 17.11.2026): Fusion refuses a transform on the native occurrence in the set's
    component ("transform overrides can only be set on Occurrence proxy from root component"), it takes it only on the
    proxy from the root, and there transform2 is in the root's frame (Occurrence.transform2: "in its assembly
    context"). So the set's world transform goes onto transform first; a set moved in its container keeps its hinges
    beside it. The second hinge needs none of this: addExistingComponent takes its transform in the set's frame when
    it's made. Test: tests/test_pred_box_seats.py
    """
    world = transform.copy()
    world.transformBy(setOccurrence.transform2)
    occurrence = inContext(native, setOccurrence)
    occurrence.transform2 = world
    return occurrence


def placeAllInSet(first, addCopy, setOccurrence, inContext, transforms):
    """
    The first occurrence and one copy per further transform (addCopy makes one in the set's component), each put at
    its transform (set's frame) through placeInSet; returns their proxies from the root.

    Root cause (r28_insert_check l3, 17.11.2026): a copy made by addExistingComponent with its place, after the first
    was put, lay at first place + its place (second hinge at y 98.81 = 40.50 + 58.30 mm). Why Fusion composes them
    isn't known; putting each copy through its proxy sets an absolute place, so what the copy starts with doesn't
    matter. Test: tests/test_pred_box_seats.py
    """
    occurrences = [first] + [addCopy() for _ in transforms[1:]]
    return [placeInSet(occurrence, setOccurrence, inContext, transform) for occurrence, transform in zip(occurrences, transforms)]
