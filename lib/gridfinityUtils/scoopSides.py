"""
Walls of a bin that get a scoop (round 48, idea of upstream issue #140 by teateatea). One checkbox per wall; every
compartment gets a scoop at each chosen wall, like the single front scoop before. Front and back run along the bin
width at min and max Y, left and right along its length at min and max X.
Kept free of Fusion imports so it can be unit tested
"""

FRONT = 'front'
BACK = 'back'
LEFT = 'left'
RIGHT = 'right'

# the label tab always sits on the back wall of its compartment, see binBodyGenerator.tabPlacement
TAB_SIDE = BACK

# the bottom fillet of a cavity starts at the first wall without a scoop in this order, the back as before round 48
SIDES_ORDER = (BACK, LEFT, RIGHT, FRONT)

def scoopSides(front: bool, back: bool, left: bool, right: bool, *, hasTab: bool) -> frozenset:
    """The walls with a scoop. Decided: the wall carrying the label tab is locked while the tab is on, at most three then"""
    sides = {side for (side, checked) in [(FRONT, front), (BACK, back), (LEFT, left), (RIGHT, right)] if checked}
    if hasTab:
        sides.discard(TAB_SIDE)
    return frozenset(sides)

def firstPlainSide(sides: frozenset) -> str | None:
    """The first wall without a scoop in SIDES_ORDER, none with four scoops"""
    return next((side for side in SIDES_ORDER if side not in sides), None)
