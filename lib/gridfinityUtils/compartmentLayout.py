"""
Compartment pockets of a bin: rectangles of compartment grid cells tiling the grid, each with its own label and depth.
Pockets are plain dicts, so they go to the dialog drawing and the saved defaults as they are.
"""

# a pocket's label icon taken from the label tab section
DEFAULT_ICON = 'Default'
# the walls a pocket can have a scoop on, in this order, the names of scoopSides (round 48)
SCOOP_WALLS = ('front', 'back', 'left', 'right')

def pocket(x: int, y: int, width: int = 1, length: int = 1, depth: float | None = None, label: str = '', icon: str = DEFAULT_ICON, scoops: list[str] | None = None) -> dict:
    """
    Depth in mm from the bin top, none for the full depth. An empty label takes the label tab section text. Scoops are
    the walls of its own with a scoop, none takes the bin's scoop walls, an empty list has none (round 48)
    """
    item = {'x': x, 'y': y, 'width': width, 'length': length, 'depth': depth, 'label': label, 'icon': icon}
    # left out without a choice of its own, so pockets and their settings stay as saved before round 48
    if scoops is not None:
        item['scoops'] = scoops
    return item

def _sanitizedScoops(scoops) -> list[str] | None:
    """Known walls in wall order, none (the bin's) for anything that isn't a list, e.g. a pocket saved before round 48"""
    if not isinstance(scoops, list):
        return None
    return [wall for wall in SCOOP_WALLS if wall in scoops]

def _cells(item: dict) -> list[tuple[int, int]]:
    return [(x, y) for x in range(item['x'], item['x'] + item['width']) for y in range(item['y'], item['y'] + item['length'])]

def _sanitized(item) -> dict | None:
    """A pocket from untrusted data, e.g. the drawing or an old saved file, none when it isn't one"""
    try:
        (x, y, width, length) = (int(item['x']), int(item['y']), int(item['width']), int(item['length']))
    except (KeyError, TypeError, ValueError):
        return None
    depth = item.get('depth')
    try:
        depth = float(depth) if depth not in (None, '') else None
    except (TypeError, ValueError):
        depth = None
    if depth is not None and depth <= 0:
        depth = None
    label = item.get('label')
    icon = item.get('icon')
    return pocket(x, y, width, length, depth, label if isinstance(label, str) else '', icon if isinstance(icon, str) and icon else DEFAULT_ICON, _sanitizedScoops(item.get('scoops')))

def normalizePockets(pockets: list, columns: int, rows: int) -> list[dict]:
    """
    Pockets tiling a grid of the given size. Pockets reaching past the grid or overlapping an earlier one are dropped,
    cells left over become single cell pockets. Sorted by column, then row, the order the uniform pattern uses.
    """
    taken: set[tuple[int, int]] = set()
    result = []
    for item in pockets or []:
        candidate = _sanitized(item)
        if candidate is None or candidate['width'] < 1 or candidate['length'] < 1:
            continue
        if candidate['x'] < 0 or candidate['y'] < 0 or candidate['x'] + candidate['width'] > columns or candidate['y'] + candidate['length'] > rows:
            continue
        cells = _cells(candidate)
        if any(cell in taken for cell in cells):
            continue
        taken.update(cells)
        result.append(candidate)
    for x in range(columns):
        for y in range(rows):
            if (x, y) not in taken:
                result.append(pocket(x, y))
    result.sort(key=lambda item: (item['x'], item['y']))
    return result

def isUniform(pockets: list[dict]) -> bool:
    """
    Every pocket a single cell of full depth with the bin's scoops, so one can be built and patterned. Labels don't
    matter, they come after
    """
    return all(item['width'] == 1 and item['length'] == 1 and item['depth'] is None and item.get('scoops') is None for item in pockets)

def isCustomized(pockets: list[dict]) -> bool:
    return any(item['width'] != 1 or item['length'] != 1 or item['depth'] is not None or item['label'] or item['icon'] != DEFAULT_ICON or item.get('scoops') is not None for item in pockets)

def fromTableRows(rows: list, fullDepth: float | None = None) -> list[dict]:
    """
    Pockets from the compartments table rows saved with the dialog defaults before the drawing replaced it, each row
    a dict of input states by input id. Depths were lengths in cm, ones reaching the full depth become full depth pockets.
    """
    pockets = []
    for (index, row) in enumerate(rows or [], 1):
        if not isinstance(row, dict):
            continue
        def value(name: str, default=None):
            state = row.get(f'{name}_input_{index}')
            return state.get('value', default) if isinstance(state, dict) else default
        depth = value('d')
        if isinstance(depth, (int, float)) and depth > 0 and (fullDepth is None or depth < fullDepth):
            depth = round(depth * 10, 2)
        else:
            depth = None
        item = _sanitized({
            'x': value('x'),
            'y': value('y'),
            'width': value('w'),
            'length': value('l'),
            'depth': depth,
            'label': value('label', ''),
            'icon': value('icon', DEFAULT_ICON),
        })
        if item is not None:
            pockets.append(item)
    return pockets

def describe(item: dict) -> str:
    """A pocket in the recorded settings"""
    parts = [
        f'cell {item["x"] + 1}, {item["y"] + 1}',
        f'{item["width"]} x {item["length"]} cells',
        f'depth {item["depth"]:g} mm' if item['depth'] is not None else 'full depth',
    ]
    if item['label']:
        parts.append(f'label {item["label"]}')
    if item['icon'] != DEFAULT_ICON:
        parts.append(f'icon {item["icon"]}')
    scoops = item.get('scoops')
    if scoops is not None:
        parts.append(f'scoops {" and ".join(scoops)}' if scoops else 'no scoops')
    return ', '.join(parts)
