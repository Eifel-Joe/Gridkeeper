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

def compartmentScoopSides(own, binSides: frozenset, *, hasTab: bool) -> frozenset:
    """
    The walls with a scoop of one compartment: its own walls from the layout editor, the bin's without a choice of its
    own (compartmentLayout.pocket). Every compartment carries its own tab on its back wall, so the tab locks the back
    of each
    """
    if own is None:
        return binSides
    return scoopSides(FRONT in own, BACK in own, LEFT in own, RIGHT in own, hasTab=hasTab)

def outerScoopWalls(compartments, columns: int, rows: int) -> frozenset:
    """
    The bin walls where any compartment along them has a scoop on that wall, compartments as (x, y, width, length,
    walls) in grid cells. There the cavities start at the inside of the lip and the lip bottom chamfer leaves the wall
    out, for all compartments along it so the grid stays even
    """
    walls = set()
    for (x, y, width, length, sides) in compartments:
        if FRONT in sides and y == 0:
            walls.add(FRONT)
        if BACK in sides and y + length == rows:
            walls.add(BACK)
        if LEFT in sides and x == 0:
            walls.add(LEFT)
        if RIGHT in sides and x + width == columns:
            walls.add(RIGHT)
    return frozenset(walls)

def scoopRadiusSpanLimits(sides: frozenset, width, length, floorMargin) -> list:
    """
    Limits of a compartment's scoop radius from its size: on an axis with scoops on both walls at most half the span
    less the floor margin, so a strip of flat floor stays between them. An axis with one scoop keeps the limits it had
    before round 48. Works on numbers and Dims alike
    """
    limits = []
    if FRONT in sides and BACK in sides:
        limits.append(length / 2 - floorMargin)
    if LEFT in sides and RIGHT in sides:
        limits.append(width / 2 - floorMargin)
    return limits

def tabOpeningDepth(insets: dict, wallThickness: float) -> float:
    """
    How deep a hollow tab is opened through the back and side walls from the cavity: through the thickest of them and
    a wall more, twice the wall without a scoop there as before round 48. A scoop wall starts the cavity at the
    lip's inner edge, deeper than the wall (review round 48). Insets as from wallInsets, in cm
    """
    return max(insets[BACK], insets[LEFT], insets[RIGHT]) + wallThickness

def boxBounds(origin, width: float, length: float):
    """XY bounds of a box from its corner and size, for touchesScoopWall"""
    return ((origin[0], origin[1]), (origin[0] + width, origin[1] + length))
