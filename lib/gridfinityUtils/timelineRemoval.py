from typing import Callable

# Deletes the items of an old part one by one in a rebuild, see rebuildUtils.removeOldGroup. Kept free of Fusion types
# so pytest can check the order of the timeline calls.


def deleteOneByOne(items: list, timeline, log: Callable[[str], None]) -> list[str]:
    """
    Deletes the items, the last first so none is still used by what's left, suppresses those Fusion won't delete and
    returns their names. The marker goes right after the items first: with it at the end every delete recomputed all
    that comes after them, a stacked second box once per item of the old one, hours in all (r27_cmd run 2,
    17.11.2026). Rolled back, the later items are computed once, by the move to the end
    """
    left = [item for item in items if item.isValid]
    if left:
        left[-1].rollTo(False)
    kept = []
    try:
        for item in reversed(left):
            if not item.isValid:
                continue
            name = item.name
            try:
                if item.isDeletable and item.deleteObject():
                    continue
                log(f'{name} wasn\'t deleted, deletable: {item.isDeletable}')
            except RuntimeError as err:
                log(f'{name} wasn\'t deleted, {err}')
            try:
                item.isSuppressed = True
            except RuntimeError as err:
                log(f'{name} wasn\'t suppressed either, {err}')
            kept.append(name)
    finally:
        # also when something breaks, the marker before the new part would leave the design looking broken
        timeline.moveToEnd()
    return kept


def deleteMovedFirst(items: list, isMoved: Callable[[object], bool], timeline, log: Callable[[str], None], expectMoved: bool = False) -> list[str]:
    """
    Deletes the items of an old part whose group header is gone already, for a rebuild with joints moved over to the
    new part (round 43, p533). The items isMoved picks, the old joint origins the moved joints used, go one by one
    first; the rest is grouped anew and that group deleted as a whole. Returns the names of those kept, suppressed.

    Root: a moved joint still hangs on the old joint origin it used. Deleting the old group as a whole, or the old
    occurrence, took the joint along as a dependent (the bin fell out of its cell, the insert to the origin); item by
    item it stayed but took 0.85-0.92 s per item, 252-274 s of a box rebuild. With those joint origins deleted on
    their own first, the whole delete keeps the joint (fusion-auftraege/r43_probe.py, 18.11.2026: baseplate with a
    bin in a cell 2.7 -> 0.7 s, bin with an insert 5.4 -> 0.9 s, joint kept, timeline healthy).
    Falls back to item by item for the rest, said in the log, when a moved one is kept (the whole delete would take its
    joint), joints were moved (expectMoved) but isMoved picked none of their joint origins, the rest has a gap in the timeline (a group spans a range) or the whole delete fails or leaves items.
    Rejected: deleting the group with the marker right after it, deleting the old occurrence (both took the joint);
    Design.deleteEntities (round 39: said true, removed 4 of 54 items)
    """
    moved = [item for item in items if item.isValid and isMoved(item)]
    kept = deleteOneByOne(moved, timeline, log) if moved else []
    rest = [item for item in items if item.isValid and not any(item is one for one in moved)]
    if not rest:
        return kept
    if expectMoved and not moved:
        # the whole delete would take the moved joints along (review round 43)
        log('deleting the rest item by item: joints were moved, but none of the joint origins they used was found')
        return deleteOneByOne(rest, timeline, log)
    if kept:
        log(f'deleting the rest item by item: {", ".join(kept)} wasn\'t deleted, the whole delete would take its joint along')
        return kept + deleteOneByOne(rest, timeline, log)
    indices = sorted(item.index for item in rest)
    if indices[-1] - indices[0] + 1 != len(rest):
        log(f'deleting the rest item by item: its {len(rest)} items aren\'t contiguous in the timeline ({indices[0]}..{indices[-1]})')
        return kept + deleteOneByOne(rest, timeline, log)
    if not moved:
        # deleteOneByOne leaves the marker at the end, the whole delete was measured there
        timeline.moveToEnd()
    group = None
    try:
        group = timeline.timelineGroups.add(indices[0], indices[-1])
        deleted = group.deleteMe(True)
    except RuntimeError as err:
        deleted = False
        log(f'the rest wasn\'t deleted as a whole, {err}')
    left = [item for item in rest if item.isValid]
    if deleted and not left:
        return kept
    log(f'deleting the rest item by item: the whole delete left {len(left)} of {len(rest)} items')
    try:
        # its items stay in the timeline without it
        if group is not None and group.isValid:
            group.deleteMe(False)
    except RuntimeError as err:
        log(f'the group made for the rest wasn\'t taken off, {err}')
    return kept + deleteOneByOne(left, timeline, log)
