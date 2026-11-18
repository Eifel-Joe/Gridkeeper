import re

# The name a joint made by a rebuild gets once the old part is gone (round 43, p430). Fusion counts a name still taken
# up: the new joint of a bin rebuilt in its cell was "... in cell (1)" while the old joint was there yet, the next
# rebuild "(2)". No Fusion import, so it can be unit tested.

_COUNTED = re.compile(r'^(?P<base>.+) \((?P<count>\d+)\)$')


def countedBase(name: str) -> str | None:
    """
    The name without the counter at its end, none for a name without one. A component's name ending in "(n)" may be the
    generator's own (from a label text), the rebuild tells Fusion's counter by the base having been taken (round 44)
    """
    match = _COUNTED.match(name)
    return match.group('base') if match is not None else None


def freedName(name: str, taken: list[str]) -> str | None:
    """
    The lowest free name below the joint's own, the base first, then "base (1)" and on; none when the name has no
    counter or none below it is free (another joint of the same base name keeps it, as Fusion counted)
    """
    match = _COUNTED.match(name)
    if match is None:
        return None
    base = match.group('base')
    count = int(match.group('count'))
    for candidate in [base] + [f'{base} ({index})' for index in range(1, count)]:
        if candidate not in taken:
            return candidate
    return None
