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
