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


def expectedItems(step, values):
    rules = RULES[step]
    return [carryItem(item, rules, values) for edgeSet in PRED_EDGES[step] for item in edgeSet['items']]


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
            raise EdgeNotFound(f"{item['kind']} not found: {item}")
        picked.append(found)
    return picked
