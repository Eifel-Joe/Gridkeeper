"""
Dividers raised up into the stacking lip. The feet of a bin stacked on top have a groove on every grid line, so a
divider wall lying on one can go up to the top of the lip and run out in its profile, like the lip around the bin.
Dividers between grid lines stay below the lip, they would run into the feet.

Only the choice of walls is here, without Fusion, the body is made by binBodyGenerator.
"""

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


@dataclass(frozen=True, order=True)
class FilletCorner:
    """
    A corner of compartment grid cell column, row whose two sides go up to the top, filleted like the corners below.
    Side x -1 is the cell's low x side, 1 its high one, side y likewise
    """
    column: int
    row: int
    sideX: int
    sideY: int


def _isRaised(segments: list[DividerSegment], axis: str, line: int, cell: int) -> bool:
    """Whether a raised divider on this line of the axis covers the cell"""
    return any(s.axis == axis and s.line == line and s.start <= cell < s.end for s in segments)


def filletCorners(segments: list[DividerSegment], columns: int, rows: int) -> list[FilletCorner]:
    """
    Cell corners the raised dividers make, where both sides of the corner go up to the top, a raised divider or an
    outer wall. Corners of two outer walls are left out, the bin's own corners are round already
    """
    corners = []
    for column in range(columns):
        for row in range(rows):
            for sideX in (-1, 1):
                for sideY in (-1, 1):
                    lineX = column if sideX == -1 else column + 1
                    lineY = row if sideY == -1 else row + 1
                    outerX = lineX in (0, columns)
                    outerY = lineY in (0, rows)
                    upX = outerX or _isRaised(segments, 'x', lineX, row)
                    upY = outerY or _isRaised(segments, 'y', lineY, column)
                    if upX and upY and not (outerX and outerY):
                        corners.append(FilletCorner(column, row, sideX, sideY))
    return corners


def cornerPlaneAxes(corner: FilletCorner, columns: int) -> tuple[int, int]:
    """
    The axis of the plane a corner's raised divider face lies in, and the other one across which its edges go up: a
    raised side across x stands in the plane of x, a corner against an outer wall across x has its divider across y.
    A crossing takes the plane of x
    """
    lineX = corner.column if corner.sideX == -1 else corner.column + 1
    return (0, 1) if lineX not in (0, columns) else (1, 0)


def isCornerChainEdge(
    corner: FilletCorner,
    cornerAt: tuple[float, float],
    columns: int,
    rows: int,
    *,
    wall: float,
    lipOverhang: float,
    bottomZ: float,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    tolerance: float = 1e-3,
    levelTolerance: float = 1e-5,
) -> bool:
    """
    Whether a straight edge of the finished bin, start to end x, y, z, belongs to the chain the corner is filleted
    along: from the top of the corner fillet below, bottomZ, up the outer wall, the chamfer under the lip and the lip
    to the top, or up a crossing. It lies in the face of the raised divider, which meets the cell at cornerAt, and
    stays within the wall behind the corner and the lip's overhang into the cell in front of it. Edges along the
    divider or the wall, and level ones, are none of it
    """
    (planeAxis, otherAxis) = cornerPlaneAxes(corner, columns)
    side = corner.sideY if planeAxis == 0 else corner.sideX
    plane = cornerAt[planeAxis]
    other = cornerAt[otherAxis]
    # the wall lies on the corner's side of it, the lip reaches into the cell
    (low, high) = (other - wall, other + lipOverhang) if side == -1 else (other - lipOverhang, other + wall)
    for point in (start, end):
        if abs(point[planeAxis] - plane) > tolerance:
            return False
        if not low - tolerance <= point[otherAxis] <= high + tolerance:
            return False
        if point[2] < bottomZ - tolerance:
            return False
    # Level only when it doesn't rise at all: upstream v2.4.0.0's lower lip socket ends the lip's inner face in an edge
    # rising 3.55 um to the top, in cm below the position tolerance. Taken for level, the corner stopped short of the
    # top in ledges of 1.40 mm2 (round 12, shape tests in Fusion). 0.1 um: ten times Fusion's point resolution (about
    # 1e-6 cm), so a level edge's noise stays level (review round 12), and 35 times below the 3.55 um rise
    return abs(start[2] - end[2]) > levelTolerance


def chainPath(edges: list[tuple[tuple[float, float], tuple[float, float]]], tolerance: float = 1e-3) -> list[int] | None:
    """
    The order of a corner's chain edges, each a start and end in its plane, so they make one path from the lowest
    point up, the path its section is swept along. None where they don't join up into one, as above a wall thicker
    than the lip, which leaves a level ledge between them
    """
    def same(a, b):
        return abs(a[0] - b[0]) <= tolerance and abs(a[1] - b[1]) <= tolerance

    if len(edges) == 0:
        return None
    first = min(range(len(edges)), key=lambda index: min(edges[index][0][1], edges[index][1][1]))
    (start, end) = edges[first]
    point = start if start[1] > end[1] else end
    order = [first]
    while len(order) < len(edges):
        following = [index for index in range(len(edges)) if index not in order and (same(edges[index][0], point) or same(edges[index][1], point))]
        if len(following) != 1:
            return None
        (start, end) = edges[following[0]]
        point = end if same(start, point) else start
        order.append(following[0])
    return order


def chainRuns(edges: list[tuple[tuple[float, float], tuple[float, float]]], tolerance: float = 1e-3) -> list[list[int]] | None:
    """
    The corner's chain edges as runs that each make one path from their lowest point up, the runs from the lowest up
    (round 15, p101). A wall thicker than the lip leaves a level ledge between the wall's face and the lip's, its edge
    isn't in the chain, so the chain falls in two runs, each swept on its own. None where a run branches
    """
    def same(a, b):
        return abs(a[0] - b[0]) <= tolerance and abs(a[1] - b[1]) <= tolerance

    if len(edges) == 0:
        return None
    # edges that share an end belong to one run
    groups: list[list[int]] = []
    for index in range(len(edges)):
        touching = [group for group in groups if any(same(a, b) for other in group for a in edges[other] for b in edges[index])]
        merged = [index] + [member for group in touching for member in group]
        groups = [group for group in groups if group not in touching] + [sorted(merged)]
    runs = []
    for group in groups:
        order = chainPath([edges[index] for index in group], tolerance)
        if order is None:
            return None
        runs.append([group[position] for position in order])
    runs.sort(key=lambda run: min(point[1] for index in run for point in edges[index]))
    # each run starts at the height the one below ends and aside of it, a level step between them: anything else, a
    # stray edge beside the chain, is no ledge and the corner is filleted as before (review round 15)
    for (below, above) in zip(runs, runs[1:]):
        top = max((point for index in below for point in edges[index]), key=lambda point: point[1])
        bottom = min((point for index in above for point in edges[index]), key=lambda point: point[1])
        if abs(top[1] - bottom[1]) > tolerance or abs(top[0] - bottom[0]) <= tolerance:
            return None
    return runs


def runOffset(edges: list[tuple[tuple[float, float], tuple[float, float]]], runs: list[list[int]], run: int) -> tuple[float, float]:
    """How far the lowest point of a run is from that of the first, aside and up: where its section goes"""
    def lowest(indices):
        return min((point for index in indices for point in edges[index]), key=lambda point: point[1])
    (base, start) = (lowest(runs[0]), lowest(runs[run]))
    return (start[0] - base[0], start[1] - base[1])


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
