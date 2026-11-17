from dataclasses import dataclass

# Settings of a storage box after Pred's parametric Gridfinity Storage Box v1.1 (round 27, p260), lengths in cm


@dataclass
class InputState:
    # size in grid cells of 42 mm and in height units of 7 mm, Pred's Grid_X, Grid_Y and GridfinityUnit
    gridX: int
    gridY: int
    heightU: int
    # magnet holes in the floor pads, Pred's MagnetHoleDiameter, off by default
    hasMagnets: bool
    magnetDepth: float
    magnetDiameter: float
    # a joint origin in every cell of the floor, to joint bins into the box
    hasJointOrigins: bool
    # which of Pred's hinges the set gets, one of predBoxParts.HINGES (round 28, Jörg 17.11.2026: "alle drei zum
    # auswählen ist besser")
    hinge: str
