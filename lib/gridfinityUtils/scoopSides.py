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

def stateScoopSides(state, *, buildsScoop: bool) -> frozenset:
    """The walls with a scoop of a bin dialog's state; none unless the bin builds scoops, only plain hollow ones do"""
    if not buildsScoop:
        return frozenset()
    return scoopSides(state.hasScoop, state.hasScoopBack, state.hasScoopLeft, state.hasScoopRight, hasTab=state.hasTab)

def wallInsets(sides: frozenset, wall, scoopInset) -> dict:
    """
    How far the cavity starts in from each wall of the outline: the wall thickness, on a scoop wall the scoop inset.
    With a lip that's the lip's inner edge, the scoop runs up into the lip without a step (the front before round 48)
    """
    return {side: scoopInset if side in sides else wall for side in SIDES_ORDER}

def touchesScoopWall(edgeMin, edgeMax, boxMin, boxMax, sides: frozenset, tolerance: float = 0.001) -> bool:
    """
    Whether an edge on the top of a box, its XY bounds given, lies on or ends at a wall with a scoop: the wall's line
    and its corner arcs. The lip bottom chamfer leaves these out, the scoop runs up into the lip there. In cm, the
    tolerance far below the corner arcs, a bounding box may be a little loose
    """
    return any([
        FRONT in sides and edgeMin[1] <= boxMin[1] + tolerance,
        BACK in sides and edgeMax[1] >= boxMax[1] - tolerance,
        LEFT in sides and edgeMin[0] <= boxMin[0] + tolerance,
        RIGHT in sides and edgeMax[0] >= boxMax[0] - tolerance,
    ])
