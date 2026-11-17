"""
The 3MF export's print layout (round r29-export, spec dev-notes/specs/2026-11-17-r29-export-drucklage.md): each part
turned into its print orientation, the parts spread over the print bed with spacing, further plates for what doesn't
fit, the purge tower's corner kept free when the label text is painted. Fusion-free and in mm, as threeMf.MeshObject.

Nutzer 17.11.2026: "Noch in 1.1.0, mit Druckbett-Auswahl. Auch für die 3MF bei Bins und Baseplates wichtig. Ebenso
Labels. Natürlich nur wenn es mehrere Druckteile sind. Auch wichtig ist ein Abstand der Teile zueinander, gerne
einstellbar. Und bei zweifarbigem Export auch eine freie Fläche für den Purgetower."
"""

import dataclasses
import math

ROTATE_NONE = 'none'
# about the part's x axis, right-handed: +90 takes +y up, so the -y face goes down
ROTATE_X_PLUS_90 = 'x+90'
ROTATE_X_MINUS_90 = 'x-90'
ROTATE_X_180 = 'x180'
ROTATIONS = (ROTATE_NONE, ROTATE_X_PLUS_90, ROTATE_X_MINUS_90, ROTATE_X_180)

# the Cullenect insert's and the box label's surface whose text is level with the plate, cullenectLabelGenerator and
# predBoxLabel SURFACE_FLUSH
SURFACE_FLUSH = 'Flush'
# the body of the Pinned hinge that is the pin, predHinge.SHAPES['Pinned']
HINGE_PIN_BODY = 'Hinge pin'
# Bambu Studio's gap between plates, a fifth of the plate (PartPlate.cpp LOGICAL_PART_PLATE_GAP)
PLATE_GAP = 1 / 5

# Defaults of the export dialog, Nutzer 17.11.2026 (D2): 5 mm between the parts and to the bed's edge, a 50 mm square
# for the purge tower (Bambu's tower is 35 mm wide, the rest is room for its brim and moving it)
DEFAULT_SPACING = 5.0
DEFAULT_PURGE = 50.0


def printRotation(role: str | None, bodyName: str, surface: str | None) -> str:
    """
    How a part turns into its print orientation, in its own frame: a part of a box set in its component's frame, which
    the set's joints only turn about z, so one rule holds for every seat (the four latches). Pred's latch, handle pin,
    hinges and box lie as printed there; the handle lies flat on its -y face, 7 mm high; the Pinned hinge's pin on its
    flat. The lid stays as built (Nutzer 17.11.2026, D1). A Flush label lies on its text, every other label on its
    underside as it's built in (Nutzer 17.11.2026). Bins and baseplates stand as designed
    """
    if role == 'Handle':
        return ROTATE_X_PLUS_90
    if role == 'Hinge' and bodyName == HINGE_PIN_BODY:
        return ROTATE_X_MINUS_90
    if surface == SURFACE_FLUSH:
        return ROTATE_X_180
    return ROTATE_NONE


def rotated(vertices: list[tuple[float, float, float]], rotation: str) -> list[tuple[float, float, float]]:
    """The vertices turned about the x axis through the origin, proper rotations, so the triangles keep facing out"""
    if rotation == ROTATE_NONE:
        return vertices
    if rotation == ROTATE_X_PLUS_90:
        return [(x, -z, y) for (x, y, z) in vertices]
    if rotation == ROTATE_X_MINUS_90:
        return [(x, z, -y) for (x, y, z) in vertices]
    if rotation == ROTATE_X_180:
        return [(x, -y, -z) for (x, y, z) in vertices]
    raise ValueError(f'unknown rotation {rotation}')


@dataclasses.dataclass
class Placement:
    # counted from 0
    plate: int
    # the footprint's corner nearest the plate's origin, mm on the plate
    x: float
    y: float
    # turned 90° about z, its width along y
    turned: bool = False


@dataclasses.dataclass
class _Shelf:
    y: float
    depth: float
    x: float


@dataclasses.dataclass
class _Plate:
    shelves: list = dataclasses.field(default_factory=list)
    nextY: float = 0.0


def arrange(footprints: list[tuple[float, float]], bed: tuple[float, float], spacing: float, purge: float) -> tuple[list[Placement], list[int]]:
    """
    Where each footprint (width along x, depth along y) goes, in shelves along x, the deepest first, the plate's back
    right corner a purge square wide kept free (none for 0). A footprint turns 90° only when it fits no other way. One
    larger than the bed, or than the bed beside the purge corner, gets a plate of its own and is named by its index.
    A single part lies in the middle of the bed, unless that touches the purge corner
    """
    (bedWidth, bedDepth) = bed
    right = bedWidth - spacing
    back = bedDepth - spacing
    # the purge square, x0, y0, x1, y1
    corner = (right - purge, back - purge, right, back) if purge > 0 else None

    def limit(y: float, depth: float) -> float:
        """How far right a part may reach at this height, short of the purge square beside it"""
        if corner is not None and y < corner[3] + spacing and y + depth > corner[1] - spacing:
            return corner[0] - spacing
        return right

    def fits(width: float, depth: float) -> bool:
        return width <= right - spacing + 1e-9 and depth <= back - spacing + 1e-9

    placements: list[Placement | None] = [None] * len(footprints)
    sizes = {}
    tooLarge = []
    for (index, (width, depth)) in enumerate(footprints):
        if fits(width, depth):
            sizes[index] = (width, depth, False)
        elif fits(depth, width):
            sizes[index] = (depth, width, True)
        else:
            tooLarge.append(index)

    plates: list[_Plate] = []

    def place(width: float, depth: float) -> tuple[int, float, float] | None:
        for (plateIndex, plate) in enumerate(plates + [_Plate(nextY=spacing)]):
            for shelf in plate.shelves:
                if depth <= shelf.depth + 1e-9 and shelf.x + width <= limit(shelf.y, depth) + 1e-9:
                    position = (plateIndex, shelf.x, shelf.y)
                    shelf.x += width + spacing
                    return position
            if plate.nextY + depth <= back + 1e-9 and spacing + width <= limit(plate.nextY, depth) + 1e-9:
                if plateIndex == len(plates):
                    plates.append(plate)
                shelf = _Shelf(plate.nextY, depth, spacing + width + spacing)
                plate.shelves.append(shelf)
                plate.nextY += depth + spacing
                return (plateIndex, spacing, shelf.y)
        return None

    order = sorted(sizes, key=lambda index: (-sizes[index][1], -sizes[index][0]))
    for index in order:
        (width, depth, turned) = sizes[index]
        position = place(width, depth)
        if position is None:
            # fits the bed but not beside the purge square: alone on a plate, named
            tooLarge.append(index)
            continue
        placements[index] = Placement(position[0], position[1], position[2], turned)

    for index in sorted(tooLarge):
        (width, depth) = footprints[index]
        turned = index in sizes and sizes[index][2]
        if turned:
            (width, depth) = (depth, width)
        plates.append(_Plate())
        placements[index] = Placement(len(plates) - 1, (bedWidth - width) / 2, (bedDepth - depth) / 2, turned)

    if len(footprints) == 1 and not tooLarge:
        (width, depth, turned) = sizes[0]
        middle = ((bedWidth - width) / 2, (bedDepth - depth) / 2)
        clear = corner is None or not (
            middle[0] < corner[2] + spacing and corner[0] < middle[0] + width + spacing
            and middle[1] < corner[3] + spacing and corner[1] < middle[1] + depth + spacing
        )
        if clear:
            placements[0] = Placement(0, middle[0], middle[1], turned)

    return (placements, sorted(tooLarge))


def plateOrigin(plate: int, plateCount: int, bed: tuple[float, float]) -> tuple[float, float]:
    """
    Where a plate lies in Bambu Studio's and OrcaSlicer's world: ceil(sqrt(n)) columns, a fifth of the plate between
    them, the rows towards -y (PartPlate.cpp)
    """
    columns = max(1, math.ceil(math.sqrt(plateCount)))
    return ((plate % columns) * bed[0] * (1 + PLATE_GAP), -(plate // columns) * bed[1] * (1 + PLATE_GAP))


def _bounds(vertices):
    return [(min(v[axis] for v in vertices), max(v[axis] for v in vertices)) for axis in range(3)]


def layOut(groups: list[list], bed: tuple[float, float], spacing: float, purge: float) -> tuple[list[tuple[int, object]], int, list[int]]:
    """
    The meshes (threeMf.MeshObject) placed on their plates, each group as one block keeping its meshes' places to
    each other (the halves of a hinge), standing on z = 0. Returns each mesh with its plate, how many plates, and the
    groups too large for the bed, see arrange
    """
    footprints = []
    for group in groups:
        ((x0, x1), (y0, y1), _) = _bounds([v for meshObject in group for v in meshObject.vertices])
        footprints.append((x1 - x0, y1 - y0))
    (placements, tooLarge) = arrange(footprints, bed, spacing, purge)
    plateCount = max((p.plate for p in placements), default=-1) + 1
    laid = []
    for (group, placement) in zip(groups, placements):
        if placement.turned:
            group = [dataclasses.replace(m, vertices=[(-y, x, z) for (x, y, z) in m.vertices]) for m in group]
        ((x0, _), (y0, _), (z0, _)) = _bounds([v for meshObject in group for v in meshObject.vertices])
        (originX, originY) = plateOrigin(placement.plate, plateCount, bed)
        shift = (originX + placement.x - x0, originY + placement.y - y0, -z0)
        for meshObject in group:
            vertices = [(x + shift[0], y + shift[1], z + shift[2]) for (x, y, z) in meshObject.vertices]
            laid.append((placement.plate, dataclasses.replace(meshObject, vertices=vertices)))
    return (laid, plateCount, tooLarge)
