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


# Nutzer 16.11.2026: "Je Box werden auch 4 Latches gebraucht.", "Latches 2 vorne und 2 jeweils einer seitlich hinten",
# "Handle_Pins werden auch zwei gebraucht.", "Ich würde die Scharniere in Druckposition belassen."
# Nutzer 17.11.2026: "alle drei zum auswählen ist besser": Pred's three hinges (Hinge_M3x30, Hinge_Pined, Hinge), M3x30
# the default; "Ja, beides" to Vorschlag J: they are jointed too, in their print position beside the box
HINGES = ('M3x30', 'Pinned', 'Plain')
DEFAULT_HINGE = 'M3x30'

PARTS = [
    Part('Latch', 4, ['Latch front left', 'Latch front right', 'Latch left', 'Latch right']),
    Part('Handle', 1, ['Handle']),
    Part('Handle pin', 2, ['Handle pin left', 'Handle pin right']),
    Part('Hinge', 2, ['Hinge 1', 'Hinge 2']),
]


# Round 29 (Nutzer 17.11.2026: "Wir zeichnen die Teile im Code."): the roles whose part predBoxInsert.drawPart draws.
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


def partsToDraw(hinge: str, drawn: list[str] = None) -> list[Part]:
    """The parts with the chosen hinge that have a generator (DRAWN_ROLES), in the order of PARTS"""
    roles = DRAWN_ROLES if drawn is None else drawn
    return [part for part in partsFor(hinge) if part.role in roles]
