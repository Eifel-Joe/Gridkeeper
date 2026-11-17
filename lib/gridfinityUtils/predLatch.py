"""
Pred's latch (Latch_Experimental) of the storage box after Pred's parametric Gridfinity Storage Box v1.1
(https://www.printables.com/model/543553, CC BY-NC, by Pred), drawn in code for Gridkeeper (round 29, Jörg 17.11.2026:
"Wir zeichnen die Teile im Code."). Plan: dev-notes/r29/latch-plan.md.

The part frame is Pred's component frame, as the former resources/predBox/latch.f3d: the latch lies flat in its print position,
x -11.8..11.8, y -36.5..0, z 0..7 mm. Pred's steps and measures are from fusion-auftraege/r29_walk/Latch_Experimental.json.

Pred builds the left half, patterns the slot features once 10 mm along -y (R-Pattern2, with Chamfer5 and Chamfer7) and
mirrors the finished half with its fillets and chamfers (Mirror1). Gridkeeper builds both halves and both slots directly
(round 29 README: no mirroring of fillets or chamfers, Pred's #42 Mirror6 lost its edges in round 27):
- Sketch1 is Pred's sketch and its mirror image across x = 0 in one sketch; Pred's lines on x = 0 lie inside the whole
  body and are left out, lines ending on x = 0 run through.
- Each side face gets its own sketch (Sketch2, Sketch2 right) with both slots; the face's outline as lines of its own.
- Fillets and chamfers take Pred's edges and their mirror images in one feature each.
Every sketch is fully constrained (Jörg: "Denk nur dran, dass alle Zeichnungen vollständig bestimmt sein müssen.").
Tested in tests/test_pred_latch.py.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import adsk.core, adsk.fusion

from .dim import Dim, valueInput, applyTo
from .predSketch import WorldSketch, collection
from .predBoxEdges import EdgeNotFound, mirrorItem

# Pred's side face lies at x = +-9.8 mm
SIDE_X = 9.8
# where an edge is looked up: Pred's coordinates are rounded to 4 places in mm (cm)
TOLERANCE = 2e-4

_EPS = 1e-6


def mm(value: float) -> Dim:
    return Dim.length(round(value / 10, 9))


# -- sketch geometry (mm) -----------------------------------------------------------------------------------------------

# Pred's Sketch1, left half (walk curves 0..33), without the lines on x = 0 (curves 12, 21) and the doubled curve 20
_HALF_SKETCH1 = [
    # three pockets 5.2 x 5.2
    ((-7.15, -4.9), (-1.95, -4.9)), ((-1.95, -4.9), (-1.95, -10.1)), ((-1.95, -10.1), (-7.15, -10.1)), ((-7.15, -10.1), (-7.15, -4.9)),
    ((-1.95, -14.9), (-1.95, -20.1)), ((-1.95, -20.1), (-7.15, -20.1)), ((-7.15, -14.9), (-1.95, -14.9)), ((-7.15, -20.1), (-7.15, -14.9)),
    ((-1.95, -24.9), (-1.95, -30.1)), ((-1.95, -30.1), (-7.15, -30.1)), ((-7.15, -24.9), (-1.95, -24.9)), ((-7.15, -30.1), (-7.15, -24.9)),
    # the outline
    ((-9.8, -32.5), (-9.8, -2.5)), ((-9.8, -32.5), (0.0, -32.5)), ((-9.8, -2.5), (0.0, -2.5)),
    # the tab
    ((-9.8, -32.5), (-7.8, -32.5)), ((-7.8, -32.5), (-7.8, -36.5)), ((-7.8, -36.5), (-9.8, -36.5)), ((-9.8, -36.5), (-9.8, -32.5)),
    # the end
    ((0.0, 0.0), (-9.8, 0.0)), ((-9.8, 0.0), (-9.8, -2.5)), ((-8.6, 0.0), (-8.6, -2.5)),
    # the spring strip and its links to the pockets
    ((-1.2, -2.5), (-1.2, -32.5)),
    ((-1.95, -6.5), (-1.2, -6.5)), ((-1.95, -8.5), (-1.2, -8.5)), ((-1.95, -18.5), (-1.2, -18.5)),
    ((-1.95, -16.5), (-1.2, -16.5)), ((-1.95, -28.5), (-1.2, -28.5)), ((-1.95, -26.5), (-1.2, -26.5)),
    ((-1.2, -4.9), (0.0, -4.9)), ((-1.2, -30.1), (0.0, -30.1)),
]


def _clean(p):
    return tuple(round(v, 9) + 0.0 for v in p)


def _key(a, b):
    return tuple(sorted([_clean(a), _clean(b)]))


def _between(p, a, b):
    """p lies strictly inside the axis-parallel segment a-b"""
    for axis in (0, 1):
        other = 1 - axis
        if abs(a[axis] - b[axis]) < _EPS and abs(p[axis] - a[axis]) < _EPS:
            low, high = sorted((a[other], b[other]))
            return low + _EPS < p[other] < high - _EPS
    return False


def _planar(segments, extraPoints=()):
    """Split the axis-parallel segments at every end (and extra point) lying inside them, drop doubles"""
    points = {_clean(p) for s in segments for p in s} | {_clean(p) for p in extraPoints}
    out = []
    seen = set()
    for a, b in segments:
        a, b = _clean(a), _clean(b)
        axis = 0 if abs(a[1] - b[1]) < _EPS else 1
        cuts = sorted([a, b] + [p for p in points if _between(p, a, b)], key=lambda p: p[axis])
        for c, d in zip(cuts, cuts[1:]):
            if _key(c, d) not in seen:
                seen.add(_key(c, d))
                out.append((c, d))
    return out


def _mergeAt(segments, onPlane):
    """Join two collinear segments meeting only each other at a point where onPlane holds"""
    segments = list(segments)
    changed = True
    while changed:
        changed = False
        ends = {}
        for index, segment in enumerate(segments):
            for p in segment:
                ends.setdefault(p, []).append(index)
        for p, indices in ends.items():
            if not onPlane(p) or len(indices) != 2:
                continue
            (a, b), (c, d) = segments[indices[0]], segments[indices[1]]
            first = a if b == p else b
            second = c if d == p else d
            if abs((first[0] - p[0]) * (second[1] - p[1]) - (first[1] - p[1]) * (second[0] - p[0])) > _EPS:
                continue
            segments = [s for i, s in enumerate(segments) if i not in indices] + [(first, second)]
            changed = True
            break
    return segments


def sketch1Lines():
    """Sketch1 over the whole width (x, y mm): Pred's half and its mirror image, split at every meeting point"""
    mirrored = [((-a[0], a[1]), (-b[0], b[1])) for a, b in _HALF_SKETCH1]
    return _mergeAt(_planar(_HALF_SKETCH1 + mirrored), lambda p: abs(p[0]) < _EPS)


def _slot(shift):
    """Pred's T-slot in Sketch2 (walk curves 4..7, 13..32) at y shifted by shift, as (y, z) segments"""
    a, b, c, d = -7.1 + shift, -9.1 + shift, -11.1 + shift, -13.1 + shift
    lines = [((a, z), (d, z)) for z in (1.2, 1.6, 1.8, 5.2, 5.4, 5.8)]
    lines += [((y, 1.2), (y, 5.8)) for y in (a, d)]
    lines += [((y, 1.8), (y, 5.2)) for y in (b, c)]
    return lines


def sketch2Shape():
    """The side sketch in (y, z) mm, the same on both sides: Pred's Sketch2 with the slot R-Pattern2 adds 10 mm along -y.
    lines: the face outline (Pred's 4 reference curves, drawn) and both slots; construction: Pred's lines to the mid
    height and to the nose's centre (curve 8 hangs on a projected point and is left out); circle: the nose; chord: its
    flat side, drawn after the chain with its ends on the circle"""
    outline = [((0.0, 0.0), (-36.5, 0.0)), ((-36.5, 0.0), (-36.5, 7.0)), ((-36.5, 7.0), (0.0, 7.0)), ((0.0, 7.0), (0.0, 0.0))]
    construction = [((0.0, 3.5), (-9.1, 3.5)), ((-36.5, 3.5), (-33.7, 3.5))]
    lines = _planar(outline + _slot(0.0) + _slot(-10.0), [p for s in construction for p in s])
    center, diameter, offset = (-33.7, 3.5), 3.8, 1.4
    half = math.sqrt((diameter / 2) ** 2 - offset ** 2)
    chord = ((center[0] + half, center[1] - offset), (center[0] - half, center[1] - offset))
    return {'lines': lines, 'construction': construction, 'circle': (center, diameter), 'chord': chord}


# Sketch1's profiles per extrude, boxes ((x0, y0), (x1, y1)) in mm
SKETCH1_PROFILES = {
    # 7 mm: tabs, end posts, the two main regions, the strip ends
    'Extrude1': [((-9.8, -36.5), (-7.8, -32.5)), ((7.8, -36.5), (9.8, -32.5)),
                 ((-9.8, -2.5), (-8.6, 0.0)), ((8.6, -2.5), (9.8, 0.0)),
                 ((-9.8, -32.5), (-1.2, -2.5)), ((1.2, -32.5), (9.8, -2.5)),
                 ((-1.2, -4.9), (1.2, -2.5)), ((-1.2, -32.5), (1.2, -30.1))],
    # 2.5 mm: pocket floors, their links, the spring strip (Pred's 10 and 8 here too add nothing and are left out)
    'Extrude2': [((x0, y - 5.2), (x0 + 5.2, y)) for x0 in (-7.15, 1.95) for y in (-4.9, -14.9, -24.9)]
              + [((x0, y - 2.0), (x0 + 0.75, y)) for x0 in (-1.95, 1.2) for y in (-6.5, -16.5, -26.5)]
              + [((-1.2, -30.1), (1.2, -4.9))],
    # 2 mm: the end's floor
    'Extrude5': [((-8.6, -2.5), (8.6, 0.0))],
}


def _slotBoxes(shift):
    a, b, c, d = -7.1 + shift, -9.1 + shift, -11.1 + shift, -13.1 + shift
    return {
        3: ((d, 5.4), (a, 5.8)), 4: ((d, 1.2), (a, 1.6)), 5: ((d, 1.8), (c, 5.2)), 6: ((d, 1.6), (a, 1.8)),
        7: ((b, 1.8), (a, 5.2)), 8: ((d, 5.2), (a, 5.4)), 9: ((c, 1.8), (b, 5.2)),
    }


def _slotProfiles(numbers):
    return [_slotBoxes(shift)[n] for shift in (0.0, -10.0) for n in numbers]


# Sketch2's profiles per extrude and side, boxes ((y0, z0), (y1, z1)) in mm, Pred's profile numbers, both slots
SLOT_PROFILES = {
    'Extrude6': _slotProfiles([4, 8, 5, 3, 6, 7, 9]),
    'Extrude7': _slotProfiles([8, 5, 6, 7, 9]),
    'Extrude3': _slotProfiles([9]),
}


# -- edges (mm) ---------------------------------------------------------------------------------------------------------

def _line(a, b):
    return {'kind': 'line', 'start': list(a), 'end': list(b)}


def _arc(center, radius, start, end):
    return {'kind': 'arc', 'center': list(center), 'radius': radius, 'start': list(start), 'end': list(end)}


def _nurbs(low, high):
    return {'kind': 'NurbsCurve3D', 'min': list(low), 'max': list(high)}


# Pred's fillet and chamfer edges of the left half, as the walk gives them: step -> [(kind, size, items)]
_PRED_EDGES = {
    'Fillet1': [('fillet', 4.0, [_line((-7.8, -32.5, 0.0), (-7.8, -32.5, 7.0))])],
    'Fillet2': [('fillet', 2.0, [_line((-8.6, -2.5, 2.0), (-8.6, 0.0, 2.0))])],
    'Chamfer1': [('chamfer', 1.5, [
        _line((-7.15, -4.9, 7.0), (-1.95, -4.9, 7.0)), _line((-1.95, -10.1, 7.0), (-7.15, -10.1, 7.0)),
        _line((-7.15, -14.9, 7.0), (-1.95, -14.9, 7.0)), _line((-1.95, -20.1, 7.0), (-7.15, -20.1, 7.0)),
        _line((-7.15, -24.9, 7.0), (-1.95, -24.9, 7.0)), _line((-1.95, -30.1, 7.0), (-7.15, -30.1, 7.0)),
        _line((-1.95, -6.5, 7.0), (-1.2, -6.5, 7.0)), _line((-1.2, -8.5, 7.0), (-1.95, -8.5, 7.0)),
        _line((-1.95, -16.5, 7.0), (-1.2, -16.5, 7.0)), _line((-1.2, -18.5, 7.0), (-1.95, -18.5, 7.0)),
        _line((-1.95, -26.5, 7.0), (-1.2, -26.5, 7.0)), _line((-1.2, -28.5, 7.0), (-1.95, -28.5, 7.0))])],
    'Fillet3': [('fillet', 1.0, [
        _line((-8.6, -2.5, 4.0), (-8.6, -2.5, 7.0)),
        _arc((-6.6, -2.5, 4.0), 2.0, (-6.6, -2.5, 2.0), (-8.6, -2.5, 4.0)),
        _line((0.0, -2.5, 2.0), (-6.6, -2.5, 2.0))])],
    'Chamfer5': [('chamfer', 0.375, [
        _line((-10.55, -9.1, 1.8), (-10.55, -11.1, 1.8)), _line((-10.55, -11.1, 5.2), (-10.55, -9.1, 5.2)),
        _line((-10.55, -9.1, 5.2), (-10.55, -9.1, 1.8)), _line((-10.55, -11.1, 1.8), (-10.55, -11.1, 5.2))])],
    'Chamfer7': [('chamfer', 0.2, [
        _line((-9.8, -7.1, 1.2), (-9.8, -7.1, 1.6)), _line((-9.8, -7.1, 5.4), (-9.8, -7.1, 5.8)),
        _line((-9.8, -13.1, 5.8), (-9.8, -13.1, 5.4)), _line((-9.8, -13.1, 1.6), (-9.8, -13.1, 1.2)),
        _line((-8.35, -7.1, 1.2), (-8.35, -7.1, 5.8)), _line((-8.35, -13.1, 5.8), (-8.35, -13.1, 1.2)),
        _line((-9.8, -13.1, 1.2), (-9.8, -7.1, 1.2)), _line((-9.8, -7.1, 5.8), (-9.8, -13.1, 5.8)),
        _line((-9.8, -7.1, 5.4), (-9.8, -13.1, 5.4)), _line((-9.8, -7.1, 1.6), (-9.8, -13.1, 1.6))])],
    'Chamfer6': [('chamfer', 0.5, [_arc((-11.8, -33.7, 3.5), 1.9, (-11.8, -34.9845, 2.1), (-11.8, -32.4155, 2.1))])],
    'Fillet4': [('fillet', 3.5, [_line((-9.8, -36.5, 7.0), (-7.8, -36.5, 7.0)), _line((-7.8, -36.5, 0.0), (-9.8, -36.5, 0.0))])],
    'Chamfer2': [
        ('chamfer', 1.0, [_line((-8.6, 0.0, 7.0), (-9.8, 0.0, 7.0)), _line((0.0, 0.0, 0.0), (-9.8, 0.0, 0.0))]),
        ('chamfer', 0.25, [
            _line((-9.8, 0.0, 0.0), (-9.8, 0.0, 7.0)), _line((-8.6, 0.0, 4.0), (-8.6, 0.0, 7.0)),
            _arc((-6.6, 0.0, 4.0), 2.0, (-6.6, 0.0, 2.0), (-8.6, 0.0, 4.0)), _line((0.0, 0.0, 2.0), (-6.6, 0.0, 2.0)),
            _line((-9.8, 0.0, 7.0), (-9.8, -33.0, 7.0)), _arc((-9.8, -33.0, 3.5), 3.5, (-9.8, -33.0, 7.0), (-9.8, -33.0, 0.0)),
            _line((-9.8, 0.0, 0.0), (-9.8, -33.0, 0.0)), _arc((-3.8, -36.5, 7.0), 4.0, (-3.8, -32.5, 7.0), (-5.7365, -33.0, 7.0)),
            _line((-3.8, -32.5, 7.0), (0.0, -32.5, 7.0)), _line((-3.8, -32.5, 0.0), (0.0, -32.5, 0.0)),
            _arc((-3.8, -36.5, 0.0), 4.0, (-5.7365, -33.0, 0.0), (-3.8, -32.5, 0.0)),
            _nurbs((-7.8, -36.5, 0.0), (-5.7365, -33.0, 3.5)), _nurbs((-7.8, -36.5, 3.5), (-5.7365, -33.0, 7.0)),
            _arc((-7.6, -1.5, 7.0), 1.0, (-8.6, -1.5, 7.0), (-7.6, -2.5, 7.0)), _line((-8.6, -1.5, 7.0), (-8.6, 0.0, 7.0)),
            _line((0.0, -2.5, 7.0), (-7.6, -2.5, 7.0))])],
    'Chamfer3': [('chamfer', 0.2, [
        _line((-1.2, -30.0, 7.0), (-1.2, -28.5, 5.5)), _line((-1.2, -26.5, 5.5), (-1.2, -25.0, 7.0)),
        _line((-1.2, -25.0, 7.0), (-1.2, -20.0, 7.0)), _line((-1.2, -20.0, 7.0), (-1.2, -18.5, 5.5)),
        _line((-1.2, -16.5, 5.5), (-1.2, -15.0, 7.0)), _line((-1.2, -15.0, 7.0), (-1.2, -10.0, 7.0)),
        _line((-1.2, -10.0, 7.0), (-1.2, -8.5, 5.5)), _line((-1.2, -6.5, 5.5), (-1.2, -5.0, 7.0)),
        _line((-1.95, -26.5, 2.5), (-1.95, -26.5, 5.5)), _line((-1.95, -25.0, 7.0), (-1.95, -26.5, 5.5)),
        _line((-1.95, -23.4, 7.0), (-1.95, -25.0, 7.0)), _line((-1.95, -20.0, 7.0), (-1.95, -21.6, 7.0)),
        _line((-1.95, -18.5, 5.5), (-1.95, -20.0, 7.0)), _line((-1.95, -18.5, 2.5), (-1.95, -18.5, 5.5)),
        _line((-1.95, -16.5, 2.5), (-1.95, -16.5, 5.5)), _line((-1.95, -15.0, 7.0), (-1.95, -16.5, 5.5)),
        _line((-1.95, -8.5, 5.5), (-1.95, -10.0, 7.0)), _line((-1.95, -8.5, 2.5), (-1.95, -8.5, 5.5)),
        _line((-1.95, -6.5, 2.5), (-1.95, -6.5, 5.5)), _line((-1.95, -5.0, 7.0), (-1.95, -6.5, 5.5)),
        _line((-1.2, -16.5, 2.5), (-1.2, -16.5, 5.5)), _line((-1.2, -8.5, 2.5), (-1.2, -8.5, 5.5)),
        _line((-1.2, -6.5, 2.5), (-1.2, -6.5, 5.5)), _line((-1.2, -18.5, 2.5), (-1.2, -18.5, 5.5)),
        _line((-1.2, -26.5, 2.5), (-1.2, -26.5, 5.5)), _line((-1.95, -28.5, 5.5), (-1.95, -30.0, 7.0)),
        _line((-1.2, -28.5, 2.5), (-1.2, -28.5, 5.5)), _line((-1.95, -28.5, 2.5), (-1.95, -28.5, 5.5)),
        _line((-7.15, -31.6, 7.0), (-7.15, -23.4, 7.0)), _line((-7.15, -21.6, 7.0), (-7.15, -13.4, 7.0)),
        _line((-7.15, -11.6, 7.0), (-7.15, -3.4, 7.0)), _line((-1.95, -13.4, 7.0), (-1.95, -15.0, 7.0)),
        _line((-1.95, -10.0, 7.0), (-1.95, -11.6, 7.0)), _line((-1.95, -3.4, 7.0), (-1.95, -5.0, 7.0)),
        _line((-1.95, -30.0, 7.0), (-1.95, -31.6, 7.0))])],
}

# Pred's order of the fillets and chamfers
EDGE_STEPS = list(_PRED_EDGES)
# the steps R-Pattern2 repeats 10 mm along -y
_PATTERNED = ('Chamfer5', 'Chamfer7')


def _shifted(item, dy):
    out = dict(item)
    for key in ('start', 'end', 'center', 'min', 'max'):
        if key in item:
            x, y, z = item[key]
            out[key] = [x, y + dy, z]
    return out


def _onPlane(point):
    return abs(point[0]) < _EPS


def _bothSides(items):
    """Each item and its mirror image across x = 0; a line along x ending on x = 0 and its image are one edge of the
    whole body"""
    out = []
    for item in items:
        mirrored = mirrorItem(item, 0.0)
        if item['kind'] == 'line':
            start, end = item['start'], item['end']
            alongX = abs(start[1] - end[1]) < _EPS and abs(start[2] - end[2]) < _EPS
            ends = [p for p in (start, end) if _onPlane(p)]
            if alongX and len(ends) == 1:
                far = end if _onPlane(start) else start
                out.append(_line(far, [-far[0], far[1], far[2]]))
                continue
        out += [item, mirrored]
    return out


def edgeSets(step):
    """The edge sets of a fillet or chamfer on the whole latch: [(kind, size mm, items mm)]"""
    sets = []
    for kind, size, items in _PRED_EDGES[step]:
        if step in _PATTERNED:
            items = items + [_shifted(item, -10.0) for item in items]
        sets.append((kind, size, _bothSides(items)))
    return sets


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


def _near(p, q, tolerance):
    return all(abs(a - b) < tolerance for a, b in zip(p, q))


def _same(item, other, tolerance):
    if item['kind'] != other['kind']:
        return False
    if item['kind'] in ('line', 'arc'):
        ends = (_near(item['start'], other['start'], tolerance) and _near(item['end'], other['end'], tolerance)) or \
               (_near(item['start'], other['end'], tolerance) and _near(item['end'], other['start'], tolerance))
        if item['kind'] == 'line':
            return ends
        return ends and _near(item['center'], other['center'], tolerance) and abs(item['radius'] - other['radius']) < tolerance
    if item['kind'] == 'circle':
        return _near(item['center'], other['center'], tolerance) and abs(item['radius'] - other['radius']) < tolerance
    return _near(item['min'], other['min'], tolerance) and _near(item['max'], other['max'], tolerance)


def matchEdges(expected, candidates, key, tolerance=TOLERANCE):
    """The candidates that are the expected items (cm), in their order, each found exactly once within the tolerance.
    predBoxEdges.matchItems compares on a 0.001 mm grid; Pred's walk rounds to 4 places, -5.7365 for -5.73654"""
    keyed = [(candidate, key(candidate)) for candidate in candidates]
    picked = []
    for item in expected:
        found = [candidate for candidate, other in keyed if _same(item, other, tolerance)]
        if len(found) != 1:
            raise EdgeNotFound(f"{len(found)} edges for {item['kind']} {item}")
        picked.append(found[0])
    return picked


# -- Fusion ------------------------------------------------------------------------------------------------------------

def _point(p):
    return [p.x, p.y, p.z]


def _edgeItem(edge):
    """An edge in the item form of predBoxEdges (as predBoxGenerator._edgeItem)"""
    geometry = edge.geometry
    kind = geometry.objectType.split('::')[-1]
    if kind == 'Line3D':
        return {'kind': 'line', 'start': _point(geometry.startPoint), 'end': _point(geometry.endPoint)}
    if kind == 'Arc3D':
        return {'kind': 'arc', 'center': _point(geometry.center), 'radius': geometry.radius,
                'start': _point(edge.startVertex.geometry), 'end': _point(edge.endVertex.geometry)}
    if kind == 'Circle3D':
        return {'kind': 'circle', 'center': _point(geometry.center), 'radius': geometry.radius}
    box = edge.boundingBox
    return {'kind': kind, 'min': _point(box.minPoint), 'max': _point(box.maxPoint)}


def _faceSketch(component, face, name) -> WorldSketch:
    """A WorldSketch on a body face without its edges (round 29 README; sketches.add projects them, and in round 28 the
    hole sketch's first profile was then the whole face, fusion-auftraege/r28_handle_build.l3.out)"""
    sketch = WorldSketch(SimpleNamespace(sketches=SimpleNamespace(add=component.sketches.addWithoutEdges)), face, name)
    sketch.component = component
    return sketch


class _Builder:
    def __init__(self, component):
        self.component = component
        self.features = component.features
        self.body = None

    def extrude(self, profiles, operation, distance: Dim, name):
        extrudes = self.features.extrudeFeatures
        extrudeInput = extrudes.createInput(collection(profiles), operation)
        extrudeInput.setDistanceExtent(False, valueInput(distance))
        if self.body is not None:
            extrudeInput.participantBodies = [self.body]
        feature = extrudes.add(extrudeInput)
        feature.name = name
        return feature

    def alongX(self, profiles, operation, worldDistance: float, name):
        """Extrude a side sketch's profiles by worldDistance mm along world x (the sketch normal points either way)"""
        sketch = profiles[0].parentSketch
        normal = sketch.xDirection.crossProduct(sketch.yDirection)
        sign = 1 if normal.x > 0 else -1
        return self.extrude(profiles, operation, mm(worldDistance * sign), name)

    def edges(self, step):
        adds = []
        for kind, size, items in edgeSets(step):
            found = matchEdges([_toCm(item) for item in items], list(self.body.edges), _edgeItem)
            adds.append((kind, size, found))
        if adds[0][0] == 'fillet':
            fillets = self.features.filletFeatures
            filletInput = fillets.createInput()
            for _, size, found in adds:
                filletInput.edgeSetInputs.addConstantRadiusEdgeSet(collection(found), valueInput(mm(size)), True)
            feature = fillets.add(filletInput)
        else:
            chamfers = self.features.chamferFeatures
            chamferInput = chamfers.createInput2()
            for _, size, found in adds:
                chamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(collection(found), valueInput(mm(size)), True)
            feature = chamfers.add(chamferInput)
        feature.name = step
        return feature

    # -- Sketch1 and the footprint -------------------------------------------------------------------------------

    def footprint(self):
        c = self.component
        sketch = WorldSketch(c, c.xYConstructionPlane, 'Sketch1')
        for a, b in sketch1Lines():
            sketch.line((mm(a[0]), mm(a[1]), mm(0)), (mm(b[0]), mm(b[1]), mm(0)))
        sketch.close()

        def profiles(step):
            return sketch.profiles([((a[0] / 10, a[1] / 10, 0), (b[0] / 10, b[1] / 10, 0)) for a, b in SKETCH1_PROFILES[step]])
        operations = adsk.fusion.FeatureOperations
        first = self.extrude(profiles('Extrude1'), operations.NewBodyFeatureOperation, mm(7), 'Extrude1')
        self.body = first.bodies.item(0)
        self.body.name = 'Latch'
        self.extrude(profiles('Extrude2'), operations.JoinFeatureOperation, mm(2.5), 'Extrude2')
        self.extrude(profiles('Extrude5'), operations.JoinFeatureOperation, mm(2), 'Extrude5')

    # -- Sketch2 on both side faces ------------------------------------------------------------------------------

    def sideFace(self, side):
        """The planar face at x = side * 9.8 mm (the largest, should Fusion split it)"""
        faces = [face for face in self.body.faces
                 if face.geometry.objectType == adsk.core.Plane.classType()
                 and abs(abs(face.geometry.normal.x) - 1) < _EPS and abs(face.pointOnFace.x - side * SIDE_X / 10) < _EPS]
        if not faces:
            raise ValueError(f'latch: no side face at x = {side * SIDE_X} mm')
        return max(faces, key=lambda face: face.area)

    def sideSketch(self, side, name):
        sketch = _faceSketch(self.component, self.sideFace(side), name)
        shape = sketch2Shape()
        x = mm(side * SIDE_X)

        def world(p):
            return (x, mm(p[0]), mm(p[1]))
        for a, b in shape['lines']:
            sketch.line(world(a), world(b))
        for a, b in shape['construction']:
            sketch.line(world(a), world(b), construction=True)
        center, diameter = shape['circle']
        sketch.circle(world(center), mm(diameter))
        sketch.close()
        self.chord(sketch, world(center), [world(p) for p in shape['chord']], mm(center[1] - shape['chord'][0][1]))
        return sketch

    def chord(self, sketch: WorldSketch, center, ends, offset: Dim):
        """The nose's flat side as Pred's: a line with both ends on the circle, offset from its centre. The chain cannot
        put a point on a circle; ends fixed by dimensions alone could miss the circle by rounding and leave the profile
        open. Four conditions on the line's four coordinates: along the face, the two ends on the circle, the offset"""
        s = sketch.sketch
        [circle] = list(s.sketchCurves.sketchCircles)
        points = []
        for end in ends:
            p = sketch._sketchPoint3D(end)
            p.z = 0
            points.append(p)
        line = s.sketchCurves.sketchLines.addByTwoPoints(points[0], points[1])
        constraints = s.geometricConstraints
        along = sketch.xAxis[0] == 1  # the sketch's x runs along world y
        if along:
            constraints.addHorizontal(line)
        else:
            constraints.addVertical(line)
        constraints.addCoincident(line.startSketchPoint, circle)
        constraints.addCoincident(line.endSketchPoint, circle)
        orientation = (adsk.fusion.DimensionOrientations.VerticalDimensionOrientation if along
                       else adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation)
        c = circle.centerSketchPoint.geometry
        text = adsk.core.Point3D.create(c.x + 0.3, c.y - 0.3, 0)
        dimension = s.sketchDimensions.addDistanceDimension(circle.centerSketchPoint, line.startSketchPoint, orientation, text, True)
        applyTo(dimension.parameter, offset)

    def slots(self):
        """Pred's Extrude6, Extrude7, Extrude3, Chamfer5, Chamfer7 and R-Pattern2's copy of them, on both sides"""
        operations = adsk.fusion.FeatureOperations
        self.sides = {side: self.sideSketch(side, name) for side, name in ((-1, 'Sketch2'), (1, 'Sketch2 right'))}

        def profiles(side, step):
            x = side * SIDE_X / 10
            return self.sides[side].profiles([((x, a[0] / 10, a[1] / 10), (x, b[0] / 10, b[1] / 10)) for a, b in SLOT_PROFILES[step]])
        # Pred: Extrude6 cuts to the pocket wall x = -7.15 offset by -1.2, that is 1.45 mm deep (the edges of Chamfer7
        # lie at x = -8.35); Extrude7 joins 1 mm back from the face, Extrude3 the cam 0.75 mm out of it
        for step, operation, depth in (('Extrude6', operations.CutFeatureOperation, 1.45),
                                       ('Extrude7', operations.JoinFeatureOperation, 1.0),
                                       ('Extrude3', operations.JoinFeatureOperation, -0.75)):
            for side in self.sides:
                self.alongX(profiles(side, step), operation, -side * depth, step if side < 0 else step + ' right')
        self.edges('Chamfer5')
        self.edges('Chamfer7')

    def nose(self):
        """Pred's Extrude4: the nose above its flat side, 2 mm out of the face"""
        (cy, cz), diameter = sketch2Shape()['circle']
        chordZ = sketch2Shape()['chord'][0][1]
        for side, sketch in self.sides.items():
            # by the centroid in world y and z: the profile bounding box is loose around arcs (Pred's profile 2 reads
            # 31.46..35.94 for a circle of 3.8), and profilesWhere hands over the sketch's axes, which differ per side
            top = []
            for profile in sketch.sketch.profiles:
                centroid = sketch.sketch.sketchToModelSpace(profile.areaProperties().centroid)
                if math.hypot(centroid.y * 10 - cy, centroid.z * 10 - cz) < diameter / 2 and centroid.z * 10 > chordZ:
                    top.append(profile)
            if len(top) != 1:
                raise ValueError(f'latch: {len(top)} nose profiles in {sketch.sketch.name}')
            self.alongX(top, adsk.fusion.FeatureOperations.JoinFeatureOperation, side * 2.0,
                        'Extrude4' if side < 0 else 'Extrude4 right')

    def jointOrigin(self):
        """As the former resources/predBox/latch.f3d (fusion-auftraege/r28_extract.py): at the part's origin, Z along the part's
        +y, X along its -x; jointed to the box's upright seat it gives the place of Pred's Latch:1"""
        component = self.component
        originInput = component.jointOrigins.createInput(adsk.fusion.JointGeometry.createByPoint(component.originConstructionPoint))
        originInput.zAxisEntity = component.yConstructionAxis
        originInput.xAxisEntity = component.xConstructionAxis
        originInput.angle = adsk.core.ValueInput.createByString('180 deg')
        jointOrigin = component.jointOrigins.add(originInput)
        jointOrigin.name = 'Latch joint origin'
        return jointOrigin

    def checkSketches(self):
        loose = [sketch.name for sketch in self.component.sketches if not sketch.isFullyConstrained]
        if loose:
            raise ValueError(f'latch: sketches not fully constrained: {", ".join(loose)}')


def createLatch(component: adsk.fusion.Component) -> list[adsk.fusion.BRepBody]:
    """Pred's latch drawn into the empty component; its one body, named Latch"""
    builder = _Builder(component)
    builder.footprint()
    for step in ('Fillet1', 'Fillet2', 'Chamfer1', 'Fillet3'):
        builder.edges(step)
    builder.slots()
    builder.nose()
    for step in ('Chamfer6', 'Fillet4', 'Chamfer2', 'Chamfer3'):
        builder.edges(step)
    builder.jointOrigin()
    builder.checkSketches()
    return [builder.body]
