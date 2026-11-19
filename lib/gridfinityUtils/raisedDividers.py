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
    A corner of compartment grid cell column, row whose two sides go up to the top, rounded like the corners below.
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


def isCornerEdge(
    corner: FilletCorner,
    cornerAt: tuple[float, float],
    grids: tuple[float, float],
    *,
    reach: float,
    bottomZ: float,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    tolerance: float = 1e-3,
    levelTolerance: float = 1e-5,
) -> bool:
    """
    Whether a straight edge of the finished bin, start to end x, y, z, belongs to the chain the corner is rounded
    along: from the top of the corner fillet below, bottomZ, up the corner of the divider's and the wall's faces, then
    where the divider's top meets the lip, or another divider's at a crossing, up to the top. These don't lie in one
    plane (round 50): the lip runs out of the wall's face into the cell, the divider's top back to its middle. The edge
    stays on the corner's side of both lines, grids x and y, an outer wall's grid line, which the lip runs back to at
    the top, or a raised divider's middle, where its top's ridge is, and no further into the cell from them than reach,
    the lip's widest. Level edges are none of it
    """
    for point in (start, end):
        for (axis, side) in ((0, corner.sideX), (1, corner.sideY)):
            # into the cell from the grid line, the cell lies on the far side of its own side
            into = (grids[axis] - point[axis]) * side
            if into < -tolerance or into > reach + tolerance:
                return False
        if point[2] < bottomZ - tolerance:
            return False
    # Level only when it doesn't rise at all: upstream v2.4.0.0's lower lip socket ends the lip's inner face in an edge
    # rising 3.55 um to the top, in cm below the position tolerance. Taken for level, the corner stopped short of the
    # top in ledges of 1.40 mm2 (round 12, shape tests in Fusion). 0.1 um: ten times Fusion's point resolution (about
    # 1e-6 cm), so a level edge's noise stays level (review round 12), and 35 times below the 3.55 um rise
    return abs(start[2] - end[2]) > levelTolerance


def _same(a, b, tolerance: float) -> bool:
    return all(abs(p - q) <= tolerance for (p, q) in zip(a, b))


# Edges of the body that meet share a vertex, its point exactly: joined within this, a short edge between two others
# joins up too. Joined within 10 um, a 7 um edge where the lip's top face lies 4 um off the stacked feet's left a
# corner's path ambiguous, no path, and the fillet tried instead failed (round 50, shown in Fusion)
CHAIN_JOIN_TOLERANCE = 1e-6


def chainPath(edges: list[tuple[tuple, tuple]], tolerance: float = CHAIN_JOIN_TOLERANCE) -> list[int] | None:
    """
    The order of a corner's chain edges, each a start and end point whose last coordinate is the height, so they make
    one path from the lowest point up, the path its section is swept along. None where they don't join up into one,
    as above a wall thicker than the lip, which leaves a level ledge between them
    """
    if len(edges) == 0:
        return None
    first = min(range(len(edges)), key=lambda index: min(edges[index][0][-1], edges[index][1][-1]))
    (start, end) = edges[first]
    point = start if start[-1] > end[-1] else end
    order = [first]
    while len(order) < len(edges):
        following = [index for index in range(len(edges)) if index not in order and (_same(edges[index][0], point, tolerance) or _same(edges[index][1], point, tolerance))]
        if len(following) != 1:
            return None
        (start, end) = edges[following[0]]
        point = end if _same(start, point, tolerance) else start
        order.append(following[0])
    return order


def chainRuns(edges: list[tuple[tuple, tuple]], tolerance: float = CHAIN_JOIN_TOLERANCE, stepTolerance: float = 1e-3) -> list[list[int]] | None:
    """
    The corner's chain edges as runs that each make one path from their lowest point up, the runs from the lowest up
    (round 15, p101). A wall thicker than the lip leaves a level ledge between the wall's face and the lip's, its edge
    isn't in the chain, so the chain falls in two runs, each swept on its own. None where a run branches
    """
    if len(edges) == 0:
        return None
    # edges that share an end belong to one run
    groups: list[list[int]] = []
    for index in range(len(edges)):
        touching = [group for group in groups if any(_same(a, b, tolerance) for other in group for a in edges[other] for b in edges[index])]
        merged = [index] + [member for group in touching for member in group]
        groups = [group for group in groups if group not in touching] + [sorted(merged)]
    runs = []
    for group in groups:
        order = chainPath([edges[index] for index in group], tolerance)
        if order is None:
            return None
        runs.append([group[position] for position in order])
    runs.sort(key=lambda run: min(point[-1] for index in run for point in edges[index]))
    # each run starts at the height the one below ends and aside of it, a level step between them: anything else, a
    # stray edge beside the chain, is no ledge and the corner is filleted as before (review round 15)
    for (below, above) in zip(runs, runs[1:]):
        top = max((point for index in below for point in edges[index]), key=lambda point: point[-1])
        bottom = min((point for index in above for point in edges[index]), key=lambda point: point[-1])
        if abs(top[-1] - bottom[-1]) > stepTolerance or _same(top[:-1], bottom[:-1], stepTolerance):
            return None
    return runs


def runOffset(edges: list[tuple[tuple, tuple]], runs: list[list[int]], run: int) -> tuple:
    """How far the lowest point of a run is from that of the first, along each coordinate: where its section goes"""
    def lowest(indices):
        return min((point for index in indices for point in edges[index]), key=lambda point: point[-1])
    (base, start) = (lowest(runs[0]), lowest(runs[run]))
    return tuple(s - b for (s, b) in zip(start, base))



def supportCornerPath(offset: float, *, supportTopZ: float, bottomZ: float, tolerance: float = 1e-4) -> list[tuple[float, float]]:
    """
    The path of a corner beside a full lip's support below its edges, as points (out from the wall's face into the cell,
    z): the corner's edges start offset out from the wall's face at bottomZ, on the support. The support runs straight
    down from the lip's tip to supportTopZ, then back to the wall's face at 45 degrees; the path starts where it
    leaves the wall's face and goes up its corner, 45 degrees out, then straight up to bottomZ (round 50)
    """
    knee = min(supportTopZ, bottomZ)
    points = [(0.0, knee - offset), (offset, knee)]
    if knee < bottomZ - tolerance:
        points.append((offset, bottomZ))
    return points

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


# The chamfers of a raised divider's flat top under a trimmed lip, cm, at most a quarter of the wall: a 1.2 mm divider
# keeps 0.6 mm flat, as wide as the trimmed lip's crown (decided 19.11.2026)
DIVIDER_TOP_CHAMFER = 0.03


def dividerTop(start, wall, top, *, isTrimmed: bool, smaller=min) -> list[tuple]:
    """
    The top of a raised divider in its section, as points (across, z) from its low face at start to its high face,
    wall thick, round 50 (decided 19.11.2026): the divider goes straight up as thick as below. Under an untrimmed lip
    its top is a roof at the lip's 45 degrees, its ridge in the middle at the lip's top; under a trimmed lip, whose top
    isn't pointed either, a flat top at the trimmed top chamfered at 45 degrees on both sides, see DIVIDER_TOP_CHAMFER.
    Numbers or Dims; smaller takes the smaller of two, Dim.min for Dims. Rejected: the lip's whole profile or its top
    contour wider than the divider, they put a ledge into the compartments (both built and dropped, 19.11.2026)
    """
    if not isTrimmed:
        half = wall / 2
        return [(start, top - half), (start + half, top), (start + wall, top - half)]
    chamfer = smaller(DIVIDER_TOP_CHAMFER, wall / 4)
    return [(start, top - chamfer), (start + chamfer, top), (start + wall - chamfer, top), (start + wall, top - chamfer)]


# how far under the outer face of an outer wall a raised divider ends, cm: a hair, so the outer faces stay the wall's alone
RIDGE_WALL_MARGIN = 0.01
