"""
The 3MF export's print layout (round r29-export, spec dev-notes/specs/2026-11-17-r29-export-drucklage.md): each part
turned into its print orientation, the parts spread over the print bed with spacing, further plates for what doesn't
fit, the purge tower's corner kept free when the label text is painted. Fusion-free and in mm, as threeMf.MeshObject.

Nutzer 17.11.2026: "Noch in 1.1.0, mit Druckbett-Auswahl. Auch für die 3MF bei Bins und Baseplates wichtig. Ebenso
Labels. Natürlich nur wenn es mehrere Druckteile sind. Auch wichtig ist ein Abstand der Teile zueinander, gerne
einstellbar. Und bei zweifarbigem Export auch eine freie Fläche für den Purgetower."
"""

import dataclasses
import re

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


def purgeSquare(bed: tuple[float, float], spacing: float, purge: float, anchor: tuple[float, float]) -> tuple | None:
    """
    The square kept free for the purge tower, x0, y0, x1, y1, where the slicer puts the tower: its corner nearest the
    origin at the anchor's share of the bed (Bambu Studio's default_wipe_tower_pos, printBeds.purgeAnchor), kept on the
    bed between the spacing. None without a purge square. Never more than the bed between the spacing
    """
    if purge <= 0:
        return None
    (bedWidth, bedDepth) = bed
    purge = min(purge, bedWidth - 2 * spacing, bedDepth - 2 * spacing)
    x0 = min(max(anchor[0] * bedWidth, spacing), bedWidth - spacing - purge)
    y0 = min(max(anchor[1] * bedDepth, spacing), bedDepth - spacing - purge)
    return (x0, y0, x0 + purge, y0 + purge)


def arrange(footprints: list[tuple[float, float]], bed: tuple[float, float], spacing: float, purge: float,
            purgeAnchor: tuple[float, float] = (1.0, 1.0), blocked: list[tuple] = ()) -> tuple[list[Placement], list[int], list[int]]:
    """
    Where each footprint (width along x, depth along y) goes, in shelves along x, the deepest first, keeping the spacing
    from the bed's edge, from each other and from the areas kept free: the purge square at the tower's spot (see
    purgeSquare) and any other blocked ones. A shelf skips past an area in its way, a new
    shelf may start above one. A footprint turns 90° when it fits no other way. One larger than the bed gets a plate
    of its own and is named in the first list, one that fits the bed but not beside the areas gets a plate of its own
    without them and is named in the second. A single part lies in the middle of the bed when that keeps clear
    """
    (bedWidth, bedDepth) = bed
    right = bedWidth - spacing
    back = bedDepth - spacing
    square = purgeSquare(bed, spacing, purge, purgeAnchor)
    areas = list(blocked) + ([square] if square is not None else [])

    def clear(box: tuple) -> bool:
        return not any(_touches(box, area, spacing) for area in areas)

    def fitX(x: float, y: float, width: float, depth: float) -> float | None:
        """The first x from x on where the footprint keeps clear of every area, none past the bed's right edge"""
        while x + width <= right + 1e-9:
            hits = [area for area in areas if _touches((x, y, x + width, y + depth), area, spacing)]
            if not hits:
                return x
            x = max(area[2] for area in hits) + spacing
        return None

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
                if depth <= shelf.depth + 1e-9:
                    x = fitX(shelf.x, shelf.y, width, depth)
                    if x is not None:
                        shelf.x = x + width + spacing
                        return (plateIndex, x, shelf.y)
            # a new shelf on top, or above an area in the way
            starts = sorted({plate.nextY} | {area[3] + spacing for area in areas if area[3] + spacing > plate.nextY})
            for y in starts:
                if y + depth > back + 1e-9:
                    break
                x = fitX(spacing, y, width, depth)
                if x is not None:
                    if plateIndex == len(plates):
                        plates.append(plate)
                    plate.shelves.append(_Shelf(y, depth, x + width + spacing))
                    plate.nextY = y + depth + spacing
                    return (plateIndex, x, y)
        return None

    noRoom = []
    order = sorted(ways, key=lambda index: (-ways[index][0][1], -ways[index][0][0]))
    for index in order:
        for (width, depth, turned) in ways[index]:
            position = place(width, depth)
            if position is not None:
                placements[index] = Placement(position[0], position[1], position[2], turned)
                break
        else:
            noRoom.append(index)

    # alone on a plate in its middle: too large for the bed, or for the bed beside the areas kept free
    for index in sorted(tooLarge + noRoom):
        (width, depth, turned) = ways[index][0] if index in ways else (*footprints[index], False)
        plates.append(_Plate())
        placements[index] = Placement(len(plates) - 1, (bedWidth - width) / 2, (bedDepth - depth) / 2, turned)

    if len(footprints) == 1 and not tooLarge and not noRoom:
        (width, depth, turned) = next(way for way in ways[0] if way[2] == placements[0].turned)
        middle = ((bedWidth - width) / 2, (bedDepth - depth) / 2)
        if clear((middle[0], middle[1], middle[0] + width, middle[1] + depth)):
            placements[0] = Placement(0, middle[0], middle[1], turned)

    return (placements, sorted(tooLarge), sorted(noRoom))


def _touches(box: tuple, area: tuple, spacing: float) -> bool:
    """Whether the box (x0, y0, x1, y1) comes closer to the area than the spacing"""
    return box[0] < area[2] + spacing - 1e-9 and area[0] < box[2] + spacing - 1e-9 \
        and box[1] < area[3] + spacing - 1e-9 and area[1] < box[3] + spacing - 1e-9


def plateFileName(name: str, plate: int, plateCount: int) -> str:
    """The 3MF of a plate (Nutzer 17.11.2026: one 3MF per plate), the name alone when there is one plate"""
    return name if plateCount == 1 else f'{name}, plate {plate + 1}'


def isPlateFileOf(fileName: str, name: str) -> bool:
    """
    Whether the file is a 3MF of the name's plates, see plateFileName: an earlier export of more plates leaves files the
    new one doesn't write (review r29-export), they would be printed with the new ones
    """
    return re.fullmatch(re.escape(name) + r'(, plate \d+)?\.3mf', fileName, re.IGNORECASE) is not None


def _bounds(vertices):
    return [(min(v[axis] for v in vertices), max(v[axis] for v in vertices)) for axis in range(3)]


# how often the layout is tried again to keep the areas free once the plates are centered, see layOut
PURGE_ATTEMPTS = 6


def layOut(groups: list[list], bed: tuple[float, float], spacing: float, purge: float,
           purgeAnchor: tuple[float, float] = (1.0, 1.0)) -> tuple[list[tuple[int, object]], int, list[int], list[int]]:
    """
    The meshes (threeMf.MeshObject) placed on their plates, each group as one block keeping its meshes' places to each
    other (the halves of a hinge), standing on z = 0, in the coordinates of its plate's own file. Returns each mesh
    with its plate, how many plates, the groups too large for the bed and the plates where the purge square couldn't
    be kept free, leaving out those of a part too large for the bed, it is named already.

    Bambu Studio and PrusaSlicer move the parts of a 3MF not made by them as one group to the middle of the bed
    (Bambu Studio Plater.cpp center_instances_around_point, Bambu probe A 17.11.2026), so each plate's parts are
    centered here already and stay where they are laid out. Centering moves them, maybe into the purge square: then
    the layout is tried again with the square blocked where it lies before the move. The best attempt counts: the
    fewest plates with the square taken, then the fewest plates (review r29-export). A printer's excluded area is the
    user's (Nutzer 17.11.2026: „Die Sperrzone ist Sache des Users.“)
    """
    footprints = []
    for group in groups:
        ((x0, x1), (y0, y1), _) = _bounds([v for meshObject in group for v in meshObject.vertices])
        footprints.append((x1 - x0, y1 - y0))
    (bedWidth, bedDepth) = bed
    square = purgeSquare(bed, spacing, purge, purgeAnchor)

    def attempt(blocked: list):
        (placements, tooLarge, noRoom) = arrange(footprints, bed, spacing, purge, purgeAnchor, blocked)
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
        # the plates whose centered parts come too close to the square, and where it lies before the move
        near = set()
        moreBlocked = []
        for (box, placement) in zip(boxes, placements):
            (sx, sy) = shifts[placement.plate]
            moved = (box[0] + sx, box[1] + sy, box[2] + sx, box[3] + sy)
            if square is not None and _touches(moved, square, spacing):
                near.add(placement.plate)
                moreBlocked.append((square[0] - sx, square[1] - sy, square[2] - sx, square[3] - sy))
        tooLargePlates = {placements[index].plate for index in tooLarge}
        noRoomPlates = {placements[index].plate for index in noRoom}
        taken = (near | noRoomPlates) - tooLargePlates
        # what blocking more may help: the plates whose parts all had room beside the square
        helps = any(plate not in tooLargePlates | noRoomPlates for plate in near)
        return ((len(taken), plateCount), placements, tooLarge, sorted(taken), shifts, plateCount, moreBlocked if helps else [])

    blocked: list = []
    best = None
    for _ in range(PURGE_ATTEMPTS):
        result = attempt(blocked)
        if best is None or result[0] < best[0]:
            best = result
        if not result[6]:
            break
        blocked = blocked + result[6]
    (_, placements, tooLarge, takenPlates, shifts, plateCount, _) = best

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
    return (laid, plateCount, tooLarge, takenPlates)


def layOutKinds(groups: list[list], kinds: list, bed: tuple[float, float], spacing: float, purge: float,
                purgeAnchor: tuple[float, float] = (1.0, 1.0)) -> tuple[list[tuple[int, object]], int, list[int], list[int]]:
    """
    As layOut, the groups of one kind on plates of their own, the kinds in the order they first come, their plates
    numbered on. A box set's box, lid and small parts are three kinds (Nutzer 17.11.2026: „Das Zubehör der Box sollte auf
    eine separate Platte. Eine Box müsste je nach Größe 3 Platten gesamt ergeben.“), see exportParts.plateKind
    """
    order: list = []
    for kind in kinds:
        if kind not in order:
            order.append(kind)
    laid = []
    plates = 0
    tooLarge = []
    taken = []
    for kind in order:
        indices = [index for (index, k) in enumerate(kinds) if k == kind]
        (kindLaid, kindPlates, kindTooLarge, kindTaken) = layOut([groups[index] for index in indices], bed, spacing, purge, purgeAnchor)
        laid += [(plates + plate, meshObject) for (plate, meshObject) in kindLaid]
        tooLarge += [indices[index] for index in kindTooLarge]
        taken += [plates + plate for plate in kindTaken]
        plates += kindPlates
    return (laid, plates, sorted(tooLarge), sorted(taken))
