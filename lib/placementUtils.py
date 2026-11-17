import adsk.core, adsk.fusion
import math

from . import tagUtils

# fraction of a grid cell, keeps bodies sitting exactly on cell borders from spilling into neighbours
GRID_SNAP_TOLERANCE = 0.001

def extentToCells(
    extent: tuple[float, float, float, float],
    cellWidth: float,
    cellLength: float,
) -> tuple[int, int, int, int]:
    """Grid cells covered by an XY extent (minX, minY, maxX, maxY), end exclusive"""
    (minX, minY, maxX, maxY) = extent
    return (
        math.floor(minX / cellWidth + GRID_SNAP_TOLERANCE),
        math.floor(minY / cellLength + GRID_SNAP_TOLERANCE),
        math.ceil(maxX / cellWidth - GRID_SNAP_TOLERANCE),
        math.ceil(maxY / cellLength - GRID_SNAP_TOLERANCE),
    )

def cellsOverlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

def findFreeGridOffset(
    footprint: tuple[int, int, int, int],
    occupied: list[tuple[int, int, int, int]],
    cellWidth: float = 1,
    cellLength: float = 1,
) -> tuple[int, int]:
    """Non-negative grid offset moving footprint clear of occupied cells, greedily picking the spot
    whose footprint center is closest to the origin. Ties go to lower rows, then lower columns."""
    # past these offsets the footprint clears every occupied cell, so the closest free spot is within them
    limitX = max([0] + [cells[2] - footprint[0] for cells in occupied])
    limitY = max([0] + [cells[3] - footprint[1] for cells in occupied])
    centerX = (footprint[0] + footprint[2]) / 2
    centerY = (footprint[1] + footprint[3]) / 2
    def distanceToOrigin(offset: tuple[int, int]):
        return ((offset[0] + centerX) * cellWidth) ** 2 + ((offset[1] + centerY) * cellLength) ** 2
    candidates = sorted(
        ((x, y) for x in range(limitX + 1) for y in range(limitY + 1)),
        key=lambda offset: (distanceToOrigin(offset), offset[1], offset[0]),
    )
    for (x, y) in candidates:
        shifted = (footprint[0] + x, footprint[1] + y, footprint[2] + x, footprint[3] + y)
        if not any(cellsOverlap(shifted, cells) for cells in occupied):
            return (x, y)
    return (limitX, 0)

def getOccupiedExtents(
    design: adsk.fusion.Design,
    tagName: str | list[str],
    legacyNamePrefix: str,
    skipComponents: list | None = None,
) -> list[tuple[float, float, float, float]]:
    """World XY extents of every placed instance of bodies with the tag or one of the tags, plus untagged ones from
    before tagging. Several tags: a new insert goes beside bins and baseplates too, not into the first bin (round 13,
    p100). Bodies of skipComponents are left out: a box label being laid elsewhere isn't in its own way"""
    tagNames = [tagName] if isinstance(tagName, str) else list(tagName)
    bodies = [body for name in tagNames for (body, _) in tagUtils.findTaggedBodies(design, name)]
    for component in design.allComponents:
        for body in component.bRepBodies:
            if body.name.startswith(legacyNamePrefix) and all(body.attributes.itemByName(tagUtils.TAG_GROUP, name) is None for name in tagNames):
                bodies.append(body)

    skip = skipComponents or []
    bodies = [body for body in bodies if not any(body.parentComponent == component for component in skip)]

    root = design.rootComponent
    extents = []
    for body in bodies:
        if body.parentComponent == root:
            instances = [body]
        else:
            instances = [body.createForAssemblyContext(occurrence) for occurrence in root.allOccurrencesByComponent(body.parentComponent)]
        for instance in instances:
            box = instance.boundingBox
            extents.append((box.minPoint.x, box.minPoint.y, box.maxPoint.x, box.maxPoint.y))
    return extents

def findPlacement(
    design: adsk.fusion.Design,
    tagName: str | list[str],
    legacyNamePrefix: str,
    extent: tuple[float, float, float, float],
    cellWidth: float,
    cellLength: float,
) -> tuple[float, float]:
    """XY offset placing an item with the given extent at the origin into a free grid spot"""
    occupied = [extentToCells(occupiedExtent, cellWidth, cellLength) for occupiedExtent in getOccupiedExtents(design, tagName, legacyNamePrefix)]
    (x, y) = findFreeGridOffset(extentToCells(extent, cellWidth, cellLength), occupied, cellWidth, cellLength)
    return (x * cellWidth, y * cellLength)

# what is kept clear around a box label laid in front of its box, cm; the grid search keeps whole cells instead
FRONT_GAP = 1.0
# how far off a grid axis a box's front may point and still count as along it
FRONT_AXIS_TOLERANCE = 1e-6

def frontPlacement(
    front: tuple[float, float],
    centre: tuple[float, float],
    boxExtents: list[tuple[float, float, float, float]],
    size: tuple[float, float],
    gap: float,
    occupied: list[tuple[float, float, float, float]],
) -> tuple[float, float, int] | None:
    """
    Where a part lying flat goes in front of a box (Nutzer 17.11.2026 of a box label taken out of its holder: "Schild vor
    die Front wäre besser. Sonst übersieht man es schnell."): front is the world XY direction the box's front faces,
    centre a world point on the box's middle (its Label joint origin), boxExtents the world XY extents of the box's
    parts (box, handle, ...), size the part's width and height lying unturned. It goes gap past the part of the box
    furthest out to the front, its middle on the box's middle, turned with the box: quarter turns about z from a box
    whose front faces -y. Returns its middle and the quarter turns, none for a box turned off the grid axes, without
    extents, or when anything of occupied is closer to the spot than gap (the box's own extents are fine)
    """
    if len(boxExtents) == 0:
        return None
    (dx, dy) = front
    turnsByFront = {(0, -1): 0, (1, 0): 1, (0, 1): 2, (-1, 0): 3}
    axis = next((key for key in turnsByFront if abs(dx - key[0]) < FRONT_AXIS_TOLERANCE and abs(dy - key[1]) < FRONT_AXIS_TOLERANCE), None)
    if axis is None:
        return None
    turns = turnsByFront[axis]
    (width, height) = size if turns % 2 == 0 else (size[1], size[0])
    reach = gap + (size[1] / 2)
    if axis == (0, -1):
        (x, y) = (centre[0], min(extent[1] for extent in boxExtents) - reach)
    elif axis == (0, 1):
        (x, y) = (centre[0], max(extent[3] for extent in boxExtents) + reach)
    elif axis == (1, 0):
        (x, y) = (max(extent[2] for extent in boxExtents) + reach, centre[1])
    else:
        (x, y) = (min(extent[0] for extent in boxExtents) - reach, centre[1])
    # kept clear by gap on every side; touching (the box at exactly gap) isn't in the way
    clear = (x - width / 2 - gap, y - height / 2 - gap, x + width / 2 + gap, y + height / 2 + gap)
    tolerance = FRONT_AXIS_TOLERANCE
    for extent in occupied:
        if clear[0] < extent[2] - tolerance and extent[0] < clear[2] - tolerance and clear[1] < extent[3] - tolerance and extent[1] < clear[3] - tolerance:
            return None
    return (x, y, turns)

def moveBodies(
    bodies: list[adsk.fusion.BRepBody],
    offsetX: float,
    offsetY: float,
    targetComponent: adsk.fusion.Component,
    *,
    name: str,
) -> adsk.fusion.MoveFeature:
    moveFeatures = targetComponent.features.moveFeatures
    bodiesToMove = adsk.core.ObjectCollection.create()
    for body in bodies:
        bodiesToMove.add(body)
    moveInput = moveFeatures.createInput2(bodiesToMove)
    moveInput.defineAsTranslateXYZ(
        adsk.core.ValueInput.createByReal(offsetX),
        adsk.core.ValueInput.createByReal(offsetY),
        adsk.core.ValueInput.createByReal(0),
        True,
    )
    moveFeature = moveFeatures.add(moveInput)
    moveFeature.name = name
    return moveFeature
