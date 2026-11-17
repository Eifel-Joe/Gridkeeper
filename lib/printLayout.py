"""
The 3MF export's print layout (round r29-export, spec dev-notes/specs/2026-11-17-r29-export-drucklage.md): each part
turned into its print orientation, the parts spread over the print bed with spacing, further plates for what doesn't
fit, the purge tower's corner kept free when the label text is painted. Fusion-free and in mm, as threeMf.MeshObject.

Nutzer 17.11.2026: "Noch in 1.1.0, mit Druckbett-Auswahl. Auch für die 3MF bei Bins und Baseplates wichtig. Ebenso
Labels. Natürlich nur wenn es mehrere Druckteile sind. Auch wichtig ist ein Abstand der Teile zueinander, gerne
einstellbar. Und bei zweifarbigem Export auch eine freie Fläche für den Purgetower."
"""

import dataclasses

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


def arrange(footprints: list[tuple[float, float]], bed: tuple[float, float], spacing: float, purge: float) -> tuple[list[Placement], list[int], list[int]]:
    """
    Where each footprint (width along x, depth along y) goes, in shelves along x, the deepest first, the plate's back
    right corner a purge square wide kept free (none for 0). A footprint turns 90° when it fits no other way, the purge
    square counted (review r29-export). One larger than the bed gets a plate of its own and is named in the first list,
    one that fits the bed but not beside the purge square gets a plate of its own without it and is named in the
    second. A single part lies in the middle of the bed, unless that touches the purge corner
    """
    (bedWidth, bedDepth) = bed
    right = bedWidth - spacing
    back = bedDepth - spacing
    # never more than the bed between the spacing, a larger one only leaves every part a plate of its own
    purge = min(purge, right - spacing, back - spacing)
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
    # the ways a footprint fits the bed, unturned first: (width, depth, turned)
    ways = {}
    tooLarge = []
    for (index, (width, depth)) in enumerate(footprints):
        options = [option for option in ((width, depth, False), (depth, width, True)) if fits(option[0], option[1])]
        if options:
            ways[index] = options
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

    noPurge = []
    order = sorted(ways, key=lambda index: (-ways[index][0][1], -ways[index][0][0]))
    for index in order:
        for (width, depth, turned) in ways[index]:
            position = place(width, depth)
            if position is not None:
                placements[index] = Placement(position[0], position[1], position[2], turned)
                break
        else:
            noPurge.append(index)

    # alone on a plate in its middle: too large for the bed, or for the bed beside the purge square
    for index in sorted(tooLarge + noPurge):
        (width, depth, turned) = ways[index][0] if index in ways else (*footprints[index], False)
        plates.append(_Plate())
        placements[index] = Placement(len(plates) - 1, (bedWidth - width) / 2, (bedDepth - depth) / 2, turned)

    if len(footprints) == 1 and not tooLarge and not noPurge:
        (width, depth, turned) = next(way for way in ways[0] if way[2] == placements[0].turned)
        middle = ((bedWidth - width) / 2, (bedDepth - depth) / 2)
        if corner is None or not _touches((middle[0], middle[1], middle[0] + width, middle[1] + depth), corner, spacing):
            placements[0] = Placement(0, middle[0], middle[1], turned)

    return (placements, sorted(tooLarge), sorted(noPurge))


def _touches(box: tuple, corner: tuple, spacing: float) -> bool:
    """Whether the box (x0, y0, x1, y1) comes closer to the corner square than the spacing"""
    return box[0] < corner[2] + spacing - 1e-9 and corner[0] < box[2] + spacing - 1e-9 \
        and box[1] < corner[3] + spacing - 1e-9 and corner[1] < box[3] + spacing - 1e-9


def plateFileName(name: str, plate: int, plateCount: int) -> str:
    """The 3MF of a plate (Nutzer 17.11.2026: one 3MF per plate), the name alone when there is one plate"""
    return name if plateCount == 1 else f'{name}, plate {plate + 1}'


def _bounds(vertices):
    return [(min(v[axis] for v in vertices), max(v[axis] for v in vertices)) for axis in range(3)]


# how often the purge square grows to stay free once the plates are centered, see layOut
PURGE_ATTEMPTS = 6


def layOut(groups: list[list], bed: tuple[float, float], spacing: float, purge: float) -> tuple[list[tuple[int, object]], int, list[int], list[int]]:
    """
    The meshes (threeMf.MeshObject) placed on their plates, each group as one block keeping its meshes' places to each
    other (the halves of a hinge), standing on z = 0, in the coordinates of its plate's own file. Returns each mesh
    with its plate, how many plates, the groups too large for the bed and the plates without a free purge corner.

    Bambu Studio and PrusaSlicer move the parts of a 3MF not made by them as one group to the middle of the bed
    (Bambu Studio Plater.cpp center_instances_around_point, Bambu probe A 17.11.2026), so each plate's parts are
    centered here already and stay where they are laid out. Centering moves them towards the purge corner: when a part
    comes too close, the square is laid out larger and tried again
    """
    footprints = []
    for group in groups:
        ((x0, x1), (y0, y1), _) = _bounds([v for meshObject in group for v in meshObject.vertices])
        footprints.append((x1 - x0, y1 - y0))
    (bedWidth, bedDepth) = bed
    corner = (bedWidth - spacing - purge, bedDepth - spacing - purge, bedWidth - spacing, bedDepth - spacing)
    reserve = purge
    for _ in range(PURGE_ATTEMPTS):
        (placements, tooLarge, noPurge) = arrange(footprints, bed, spacing, reserve)
        boxes = []
        for ((width, depth), placement) in zip(footprints, placements):
            (w, d) = (depth, width) if placement.turned else (width, depth)
            boxes.append((placement.x, placement.y, placement.x + w, placement.y + d))
        plateCount = max((p.plate for p in placements), default=-1) + 1
        shifts = []
        for plate in range(plateCount):
            onPlate = [box for (box, p) in zip(boxes, placements) if p.plate == plate]
            shifts.append((
                bedWidth / 2 - (min(b[0] for b in onPlate) + max(b[2] for b in onPlate)) / 2,
                bedDepth / 2 - (min(b[1] for b in onPlate) + max(b[3] for b in onPlate)) / 2,
            ))
        # how far the centered parts reach into the purge square, by plate
        intrusion = {}
        for (index, (box, placement)) in enumerate(zip(boxes, placements)):
            (sx, sy) = shifts[placement.plate]
            moved = (box[0] + sx, box[1] + sy, box[2] + sx, box[3] + sy)
            if purge > 0 and _touches(moved, corner, spacing):
                reach = min(moved[2] + spacing - corner[0], moved[3] + spacing - corner[1])
                intrusion[placement.plate] = max(intrusion.get(placement.plate, 0.0), reach)
        stuck = {placements[index].plate for index in tooLarge + noPurge}
        if all(plate in stuck for plate in intrusion):
            break
        reserve += max(reach for (plate, reach) in intrusion.items() if plate not in stuck)
    laid = []
    for (group, placement) in zip(groups, placements):
        if placement.turned:
            group = [dataclasses.replace(m, vertices=[(-y, x, z) for (x, y, z) in m.vertices]) for m in group]
        ((x0, _), (y0, _), (z0, _)) = _bounds([v for meshObject in group for v in meshObject.vertices])
        (sx, sy) = shifts[placement.plate]
        shift = (placement.x + sx - x0, placement.y + sy - y0, -z0)
        for meshObject in group:
            vertices = [(x + shift[0], y + shift[1], z + shift[2]) for (x, y, z) in meshObject.vertices]
            laid.append((placement.plate, dataclasses.replace(meshObject, vertices=vertices)))
    # the plates without a free purge corner: a centered part reaches into it, or a part had no room beside it
    noPurgePlates = set(intrusion) | {placements[index].plate for index in noPurge}
    return (laid, plateCount, tooLarge, sorted(noPurgePlates))
