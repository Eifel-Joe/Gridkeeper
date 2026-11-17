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
