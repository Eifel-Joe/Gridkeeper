"""
Which edges and faces the box's chamfers and fillets take, carried over from Pred's file to any box size.

Pred's edges were read at 5 x 4 x 6 (predBoxEdges.json, mm, made by dev-notes/tools/pred_from_log.py from
fusion-auftraege/r27_pred_walk.log). For another size every coordinate keeps its distance to what it hangs on in
Pred's sketches, chosen per step in RULES: the near side wall, the box middle, the label width, the bottom, the top or
the middle height. The generator then looks the carried-over items up among the body's real edges (matchItems).
Fusion-free, values in cm.
"""

import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))


def _toCm(item):
    out = {}
    for key, value in item.items():
        if key in ('start', 'end', 'center', 'min', 'max'):
            out[key] = [v / 10 for v in value]
        elif key == 'radius':
            out[key] = value / 10
        else:
            out[key] = value
    return out


def _load():
    raw = json.load(open(os.path.join(_HERE, 'predBoxEdges.json'), encoding='utf-8'))
    steps = {}
    for step, edgeSets in raw.items():
        steps[step] = []
        for edgeSet in edgeSets:
            converted = {key: (value / 10 if key in ('distance', 'radius') else value)
                         for key, value in edgeSet.items() if key != 'items'}
            converted['items'] = [_toCm(item) for item in edgeSet['items']]
            steps[step].append(converted)
    return steps


PRED_EDGES = _load()

# Pred's own size, cm (5 x 4 x 6)
PRED_VALUES = {
    'outerWidth': 23.0, 'outerLength': 18.8, 'midX': 11.5, 'midY': 9.4,
    'bodyTop': 5.22, 'midZ': 2.47, 'labelWidth': 7.05, 'catchSlideDepth': 4.3,
}
# z up to the top of the lower groove belongs to the bottom, everything above hangs on the top
_BOTTOM_ZONE = 0.82
# label features reach 2.5 mm past the label edge (the opening tab's rounding)
_LABEL_ZONE = 0.25
# the end of the catch slide at 5 x 4 x 6 (Extrude14: top - 6 mm - 43 mm)
_SLIDE_END = 0.32
_EPS = 1e-6

# x rule, y rule, z rule per step (see _carry). The handle and label holders hang on the label edge, measured in
# Pred's file at 6 x 5 x 8 (fusion-auftraege/r27_pred_size_6x5x8.txt: +13.75 mm with the label edge, not +21 mm
# with the middle).
RULES = {
    '#22 Chamfer7': ('label', 'sides', 'auto'),
    '#23 Fillet4': ('label', 'sides', 'auto'),
    '#24 Chamfer10': ('label', 'sides', 'auto'),
    '#32 Chamfer26': ('label', 'sides', 'midZ'),
    '#33 Fillet10': ('label', 'sides', 'midZ'),
    '#40 Chamfer29': ('label', 'sides', 'midZ'),
    '#41 Chamfer30': ('label', 'sides', 'midZ'),
    '#43 Fillet11': ('sides', 'sides', 'auto'),
    '#46 Chamfer1': ('sides', 'sides', 'auto'),
    '#49 Chamfer2': ('sides', 'sides', 'auto'),
    '#54 Fillet2': ('sides', 'sides', 'slide'),
    '#56 Chamfer3': ('sides', 'sides', 'auto'),
    '#59 Chamfer9': ('sides', 'sides', 'auto'),
    '#67 Chamfer13': ('sides', 'sides', 'auto'),
    '#68 Chamfer14': ('sides', 'sides', 'auto'),
    '#69 Fillet5': ('sides', 'sides', 'auto'),
    '#70 Chamfer18': ('sides', 'sides', 'auto'),
    '#77 Chamfer20': ('sides', 'sides', 'auto'),
    '#79 Chamfer19': ('sides', 'sides', 'auto'),
    '#82 Chamfer21': ('sides', 'sides', 'auto'),
    '#83 Chamfer11': ('sides', 'sides', 'auto'),
    '#84 Chamfer12': ('sides+label', 'sides', 'auto'),
    '#85 Chamfer16': ('sides', 'sides', 'auto'),
}


class EdgeNotFound(Exception):
    pass


def _sides(value, middle, size, newSize):
    return value if value < middle else newSize - (size - value)


def _label(value, values):
    mid, newMid = PRED_VALUES['midX'], values['midX']
    offset = value - mid
    if abs(offset) < _EPS:
        return newMid
    half, newHalf = PRED_VALUES['labelWidth'] / 2, values['labelWidth'] / 2
    side = 1 if offset > 0 else -1
    return newMid + side * (newHalf - (half - abs(offset)))


def _carryX(rule, x, values):
    if rule == 'sides+label':
        rule = 'label' if abs(x - PRED_VALUES['midX']) <= PRED_VALUES['labelWidth'] / 2 + _LABEL_ZONE + _EPS else 'sides'
    if rule == 'sides':
        return _sides(x, PRED_VALUES['midX'], PRED_VALUES['outerWidth'], values['outerWidth'])
    if rule == 'label':
        return _label(x, values)
    raise ValueError(rule)


def _carryY(rule, y, values):
    if rule == 'sides':
        return _sides(y, PRED_VALUES['midY'], PRED_VALUES['outerLength'], values['outerLength'])
    raise ValueError(rule)


def _carryZ(rule, z, values):
    if rule == 'midZ':
        return values['midZ'] + (z - PRED_VALUES['midZ'])
    if rule == 'slide' and abs(z - _SLIDE_END) < _EPS:
        return values['bodyTop'] - (PRED_VALUES['bodyTop'] - PRED_VALUES['catchSlideDepth'] - _SLIDE_END) - values['catchSlideDepth']
    if rule in ('auto', 'slide'):
        return z if z <= _BOTTOM_ZONE + _EPS else values['bodyTop'] + (z - PRED_VALUES['bodyTop'])
    raise ValueError(rule)


def carryItem(item, rules, values):
    """Pred's edge or face (cm) at the place it has in a box of the given measures (PredBoxDims.values())"""
    xRule, yRule, zRule = rules
    out = dict(item)
    for key in ('start', 'end', 'center', 'min', 'max'):
        if key in item:
            x, y, z = item[key]
            out[key] = [_carryX(xRule, x, values), _carryY(yRule, y, values), _carryZ(zRule, z, values)]
    return out


def mirrorItem(item, midX):
    """The item mirrored across the plane x = midX (cm), a face's box keeping min below max"""
    out = dict(item)
    for key in ('start', 'end', 'center'):
        if key in item:
            x, y, z = item[key]
            out[key] = [2 * midX - x, y, z]
    if 'min' in item and 'max' in item:
        out['min'] = [2 * midX - item['max'][0]] + list(item['min'][1:])
        out['max'] = [2 * midX - item['min'][0]] + list(item['max'][1:])
    return out


def expectedItems(step, values, mirrored=False):
    """Pred's items of the step at the box's size; mirrored, those of the right half's counterpart: the generator
    builds the right handle and label holders itself instead of Pred's #42 Mirror6, see predBoxGenerator.holders"""
    rules = RULES[step]
    items = [carryItem(item, rules, values) for edgeSet in PRED_EDGES[step] for item in edgeSet['items']]
    return [mirrorItem(item, values['midX']) for item in items] if mirrored else items


def _key(point):
    # 0.001 mm grid, the coordinates are exact sums of Pred's dimensions
    return tuple(round(v * 10000) for v in point)


def _signature(item):
    kind = item['kind']
    if kind in ('line', 'arc'):
        ends = tuple(sorted([_key(item['start']), _key(item['end'])]))
        extra = (_key(item['center']), round(item['radius'] * 10000)) if kind == 'arc' else ()
        return (kind, ends) + extra
    if kind == 'circle':
        return (kind, _key(item['center']), round(item['radius'] * 10000))
    if kind == 'face':
        return (kind, _key(item['min']), _key(item['max']))
    return (kind, _key(item.get('min', (0, 0, 0))), _key(item.get('max', (0, 0, 0))))


def matchItems(expected, candidates, key):
    """The candidates (body edges or faces) that are the expected items, in their order.
    key turns a candidate into the item form (kind, start/end/center/radius or min/max, cm)."""
    index = {}
    for candidate in candidates:
        index.setdefault(_signature(key(candidate)), candidate)
    picked = []
    for item in expected:
        found = index.get(_signature(item))
        if found is None:
            raise EdgeNotFound(f"{item['kind']} not found: {item}; near it: {_near(item, candidates, key)}")
        picked.append(found)
    return picked


# a face is asked for at a grid of points over its box, the middle first: Pred's flat faces are rectangles, rounded
# corners and L shapes, the middle of a corner's box lies off it (r45_mess.log: #56, #77, #82 found nothing there)
_FACE_GRID = [0.5, 0.0, 1.0, 0.25, 0.75]


def probePoints(item):
    """
    Points (cm) on or around the expected item to ask Fusion what lies there, in order (round 45, p296): a line's
    midpoint, an arc's start (the edges meeting there, the arc among them), a grid over a face's box
    """
    if item['kind'] == 'line':
        return [[(a + b) / 2 for a, b in zip(item['start'], item['end'])]]
    if item['kind'] == 'arc':
        return [list(item['start'])]
    if item['kind'] == 'face':
        low, high = item['min'], item['max']
        # the face is flat across one axis (Pred's faces are planes along the box axes), the grid spans the other two
        span = [axis for axis in range(3) if abs(high[axis] - low[axis]) > _EPS]
        points = []
        for u in _FACE_GRID:
            for v in (_FACE_GRID if len(span) > 1 else [0.0]):
                point = [(a + b) / 2 for a, b in zip(low, high)]
                for (axis, t) in zip(span, (u, v)):
                    point[axis] = low[axis] + t * (high[axis] - low[axis])
                points.append(point)
        return points
    raise ValueError(f"no probe point for a {item['kind']}")


def pickByPoint(expected, find, key):
    """
    The expected items looked up where they are (round 45, p296): find(point) gives the body's edges or faces there,
    at the item's probePoints in turn; the one whose item form (key) has the item's signature is taken, as matchItems
    does over the whole body. None as soon as one isn't found that way, or two different ones have its signature at a
    point (the walk takes the first in the body's order, a lookup might take another; review round 45): the caller
    walks the whole body then. Reading every edge took 11-16 s per box (34 294 edges.item,
    fusion-auftraege/r45_profil.log), a lookup 0.25 ms (r45_probe.log). Tested in tests/test_pred_box_pick.py
    """
    picked = []
    for item in expected:
        signature = _signature(item)
        found = None
        for point in probePoints(item):
            matches = []
            for candidate in find(point):
                if _signature(key(candidate)) == signature and not any(candidate == match for match in matches):
                    matches.append(candidate)
            if len(matches) > 1:
                return None
            if matches:
                found = matches[0]
                break
        if found is None:
            return None
        picked.append(found)
    return picked


def _near(item, candidates, key, distance=0.3):
    """Candidates of the same kind with a point within distance (cm) of one of the item's, for the error message"""
    points = [item[k] for k in ('start', 'end', 'center', 'min', 'max') if k in item]
    near = []
    for candidate in candidates:
        other = key(candidate)
        if other['kind'] != item['kind']:
            continue
        otherPoints = [other[k] for k in ('start', 'end', 'center', 'min', 'max') if k in other]
        if any(sum((a - b) ** 2 for a, b in zip(p, q)) ** 0.5 < distance for p in points for q in otherPoints):
            near.append({k: ([round(v * 10, 3) for v in other[k]] if isinstance(other[k], list) else other[k]) for k in other})
    return near[:8]
