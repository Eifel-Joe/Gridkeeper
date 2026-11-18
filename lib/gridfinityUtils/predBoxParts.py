"""
The small parts of the storage box after Pred's parametric Gridfinity Storage Box v1.1
(https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric, CC BY-NC, by Pred), round 28
(p261). Fusion-free: which parts the set holds, how many, and where they are jointed. Since round 29 every part is
drawn in code (predLatch, predHandle, predHandlePin, predHinge; predBoxInsert.drawPart), in the part frame of Pred's
file; the part files of round 28 are gone.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Part:
    # the role tag of the part's component in the set, also its name
    role: str
    count: int
    # the seat each occurrence is jointed to
    seats: list[str] = field(default_factory=list)


# Decided 16.11.2026: 4 latches per box, 2 at the front and one at each side at the back, 2 handle pins, the hinges
# stay in print position.
# Decided 17.11.2026: all three can be picked: Pred's three hinges (Hinge_M3x30, Hinge_Pined, Hinge), M3x30
# the default; they are jointed too, in their print position beside the box
HINGES = ('M3x30', 'Pinned', 'Plain')
DEFAULT_HINGE = 'M3x30'

PARTS = [
    Part('Latch', 4, ['Latch front left', 'Latch front right', 'Latch left', 'Latch right']),
    Part('Handle', 1, ['Handle']),
    Part('Handle pin', 2, ['Handle pin left', 'Handle pin right']),
    Part('Hinge', 2, ['Hinge 1', 'Hinge 2']),
]


# Round 29 (17.11.2026: the parts are drawn in code): the roles whose part predBoxInsert.drawPart draws.
# The others stay out of the set until their generator is there (integration step by step, a click test after each)
DRAWN_ROLES: list[str] = ['Latch', 'Handle', 'Handle pin', 'Hinge']


def partsFor(hinge: str) -> list[Part]:
    """The parts of a set with the hinge variant (one of HINGES); the variant only changes how the hinge is drawn"""
    if hinge not in HINGES:
        raise ValueError(f'unknown hinge {hinge}')
    return list(PARTS)

SEAT_NAMES = [seat for part in PARTS for seat in part.seats]


def seatJointOriginName(seat: str) -> str:
    """The joint origin on the box a part is jointed to; the joint carries the seat's name"""
    return f'{seat} joint origin'


def seatOfJointOriginName(name: str) -> str | None:
    """
    The seat whose joint origin on the box has this name, None for any other joint origin. Round 36 (p293): the four
    latches are one component, so a rebuild tells them apart by the seat the set joints each of them to
    """
    return next((seat for seat in SEAT_NAMES if seatJointOriginName(seat) == name), None)


def partsToDraw(hinge: str, drawn: list[str] = None) -> list[Part]:
    """The parts with the chosen hinge that have a generator (DRAWN_ROLES), in the order of PARTS"""
    roles = DRAWN_ROLES if drawn is None else drawn
    return [part for part in partsFor(hinge) if part.role in roles]
