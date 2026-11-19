"""
Dividers raised up into the stacking lip. The feet of a bin stacked on top have a groove on every grid line, so a
divider wall lying on one can go up to the top of the lip and run out in its profile, like the lip around the bin.
Dividers between grid lines stay below the lip, they would run into the feet.

Only the choice of walls is here, without Fusion, the body is made by binBodyGenerator.
"""

import math
from dataclasses import dataclass

# a line of the compartment grid counts as a grid line within this, in grid units
GRID_LINE_TOLERANCE = 1e-6


@dataclass(frozen=True)
class DividerSegment:
    """
    A run of divider wall on a line of the compartment grid. Axis 'x' is a wall across x, between compartment columns
    line - 1 and line, running along y from row start to end, end excluded. Axis 'y' is one across y, between rows,
    running along x over columns start to end
    """
    axis: str
    line: int
    start: int
    end: int


def isGridLine(line: int, count: int, binUnits: float) -> bool:
    """Whether line of a compartment grid count divisions over binUnits whole grid units lies on a grid line"""
    position = line * binUnits / count
    return abs(position - round(position)) < GRID_LINE_TOLERANCE


def _owners(pockets: list[dict]) -> dict[tuple[int, int], int]:
    """The pocket index of every cell"""
    owners = {}
    for (index, item) in enumerate(pockets):
        for x in range(item['x'], item['x'] + item['width']):
            for y in range(item['y'], item['y'] + item['length']):
                owners[(x, y)] = index
    return owners


def _runs(isWall: list[bool]) -> list[tuple[int, int]]:
    """Start and end, excluded, of every run of True"""
    runs = []
    start = None
    for (index, value) in enumerate(isWall + [False]):
        if value and start is None:
            start = index
        elif not value and start is not None:
            runs.append((start, index))
            start = None
    return runs


def gridLineSegments(pockets: list[dict], columns: int, rows: int, binWidth: float, binLength: float) -> list[DividerSegment]:
    """
    Divider walls on grid lines of a bin binWidth by binLength grid units, its compartment grid columns by rows cells
    tiled by the pockets, see compartmentLayout.normalizePockets. A wall is where the cells on both sides of a line
    belong to different pockets, a pocket spanning the line leaves a gap
    """
    owners = _owners(pockets)
    segments = []
    for line in range(1, columns):
        if isGridLine(line, columns, binWidth):
            walls = [owners.get((line - 1, y)) != owners.get((line, y)) for y in range(rows)]
            segments += [DividerSegment('x', line, start, end) for (start, end) in _runs(walls)]
    for line in range(1, rows):
        if isGridLine(line, rows, binLength):
            walls = [owners.get((x, line - 1)) != owners.get((x, line)) for x in range(columns)]
            segments += [DividerSegment('y', line, start, end) for (start, end) in _runs(walls)]
    return segments


def segmentsForBin(
    isEnabled: bool,
    hasLip: bool,
    isHollow: bool,
    isShaped: bool,
    pockets: list[dict],
    columns: int,
    rows: int,
    binWidth: float,
    binLength: float,
) -> list[DividerSegment]:
    """The dividers to raise, none unless asked for on a hollow bin with a lip to run out in and plain compartments"""
    if not (isEnabled and hasLip and isHollow and not isShaped):
        return []
    return gridLineSegments(pockets, columns, rows, binWidth, binLength)


def optionEnabled(
    generateBody: bool,
    hasLip: bool,
    isHollow: bool,
    isShaped: bool,
    isCreased: bool,
    compartmentCount: int,
) -> bool:
    """Whether the dialog offers raising the dividers: a hollow bin body with a lip and more than one compartment"""
    hasCompartments = not isCreased and compartmentCount > 1
    return generateBody and hasLip and isHollow and not isShaped and hasCompartments


def ridgeBox(
    tipHalf: float,
    lowFace: float,
    highFace: float,
    *,
    tipLift: float,
    minDepth: float,
    maxDepth: float,
) -> tuple[float, float, float]:
    """
    The box a raised divider's ridge is cut from by the feet of a bin stacked on top, round 50 (p650): the lip's
    profile on both sides. Decided: the ridge is centred on the grid line, tipHalf either side, where the groove
    between two feet is; the divider is a little off it, its faces lowFace and highFace from the grid line. Under each
    side the ridge runs at 45 degrees in to that side's divider face, the full lip's support (from tipLift under the
    tip, -1.2 mm straight down) or the light lip's chamfer (from the body top), so nothing overhangs the compartment.
    Returns how deep under the body top the box starts and the 45 degree chamfers of its low and high bottom edge, all
    in cm. It starts at least minDepth down, where the dividers were lowered to, and at most maxDepth, the compartment
    floor: cut off there, its chamfers shorten by as much (one height unit, decided)
    """
    chamfers = [max(0.0, tipHalf - face) for face in (lowFace, highFace)]
    depth = max(minDepth, max(chamfers) - tipLift)
    cut = max(0.0, depth - maxDepth)
    return (depth - cut, max(0.0, chamfers[0] - cut), max(0.0, chamfers[1] - cut))


def raisedSides(pocket: tuple[int, int, int, int], segments: list[DividerSegment]) -> frozenset:
    """
    The sides of a compartment, x, y, width and length in cells, that lie on raised dividers: front and back at low and
    high y, left and right at low and high x (round 50)
    """
    (x, y, width, length) = pocket
    sides = set()
    for segment in segments:
        if segment.axis == 'y' and segment.start < x + width and segment.end > x:
            if segment.line == y:
                sides.add('front')
            if segment.line == y + length:
                sides.add('back')
        if segment.axis == 'x' and segment.start < y + length and segment.end > y:
            if segment.line == x:
                sides.add('left')
            if segment.line == x + width:
                sides.add('right')
    return frozenset(sides)


def coveredCornerRadius(radius: float, coverA: float, coverB: float) -> float:
    """
    The largest fillet, at most radius, of a compartment corner that lies wholly under two strips covering it from
    above, coverA and coverB wide from the corner's two faces (round 50, decided option a): a fillet of radius r is
    the square of r less the circle around its centre, covered when r <= min(a, b) or when its point farthest from both
    faces, inside both strips' reach, keeps (r - a)^2 + (r - b)^2 <= r^2, so r <= a + b + sqrt(2ab). Beside a ridge the
    compartment's corner fillet reached past the ridge's tip, the compartments top clearance cut it flat: level faces
    of 0.10 mm2 at every divider meeting the wall (shown in Fusion)
    """
    (a, b) = (max(0.0, coverA), max(0.0, coverB))
    return min(radius, a + b + (2 * a * b) ** 0.5)


# how far the ridge's straight face reaches below the cut cavity top: ending on it, its edge lay on the cavities' and
# Fusion's combines failed there (ASM_EDGECOIN_PROBLEM) or left faces 0.01 mm wide (review round 50, shown in Fusion)
RIDGE_TIP_MARGIN = 0.02


def ridgeTipDepth(*, isFullLip: bool, clearanceDepth: float, supportWall: float) -> float:
    """
    How far the ridge's straight face under its tip reaches below the body top, cm: a full lip's support wall, and at
    least down to where the compartments top clearance cuts the cavities (review round 50: above a scoop on the ridge a
    light lip's chamfer, starting at the body top, left a shelf as deep as the tab top offset, and a full ridge a level
    face with an offset deeper than its support wall)
    """
    cut = clearanceDepth + RIDGE_TIP_MARGIN if clearanceDepth > 0 else 0.0
    return max(supportWall if isFullLip else 0.0, cut)


# a side of a compartment at the lip's or a ridge's tip, an outer scoop wall or a scoop on a ridge, see cornerRadiusBetween
TIP = 'tip'


def cornerRadiusBetween(radius: float, coverA, coverB, *, tipCorner: float) -> float:
    """
    The fillet of a compartment corner beside a ridge, its sides each covered from above by a strip that wide, see
    coveredCornerRadius, or at a tip (TIP). Between two tip faces it follows the rounded corner the feet of a stacked
    bin leave above it, tipCorner, as a corner between two scoop walls does (p653, review round 50: covered by nothing,
    it came out sharp and the whole compartment with it)
    """
    if coverA == TIP and coverB == TIP:
        return min(radius, tipCorner)
    return coveredCornerRadius(radius, 0 if coverA == TIP else coverA, 0 if coverB == TIP else coverB)


def tipCornersBesideRidge(covers: dict, ridges: frozenset) -> list[tuple[str, str]]:
    """
    The corners of a compartment, (left or right, front or back), between two tip faces of which one is a ridge's:
    their rounding is filled up to the body top where the compartments top clearance cut it (review round 50). Covers
    by side as for cornerRadiusBetween
    """
    return [
        (sideX, sideY) for sideX in ('left', 'right') for sideY in ('front', 'back')
        if covers[sideX] == TIP and covers[sideY] == TIP and (sideX in ridges or sideY in ridges)
    ]


def tabTopRise(behind: float, labelAngle: float) -> float:
    """
    How much higher a label tab's top starts at its back when the tab reaches behind the ridge's tip by behind, cm: the
    top slopes down from the back by the label angle, radians, and has to be at its height at the tip, where the label
    and its pocket are placed (re-review round 50)
    """
    return behind * math.tan(labelAngle)
