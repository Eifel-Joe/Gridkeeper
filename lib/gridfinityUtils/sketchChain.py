"""
Which conditions and dimensions bind a sketch completely, in the way of sketchUtils.createRectangle (round 27, task 3b,
Nutzer: "Ja, Formen-Weg").

A rank picking plan with tangencies was rejected by Fusion (fusion-auftraege/r27_sketches2/3.out). The chain fixes the
points of each shape one after another: the shape's first point from the origin, every further point with dimensions to
points already fixed (a new line end two, a new arc centre two, an arc end on a fixed centre one), real horizontal and
vertical lines with that condition in place of a dimension. Never a dimension of zero, never an alignment to the origin,
never a tangency. rank() checks a chain numerically (pytest).

Fusion-free. Points are (x, y) in sketch coordinates; curves are dicts:
  {'kind': 'line', 'a': i, 'b': j}, {'kind': 'arc', 'center': c, 'start': i, 'end': j}, {'kind': 'circle', 'center': c}
Result: ('horizontal'|'vertical'|'diameter', curve), ('hdim'|'vdim', point, otherPoint or None for the origin),
('originAt', point) for a shape that starts on the origin.
"""

import math

_EPS = 1e-7
_RANK_EPS = 1e-9


# -- checking (pytest): rank of the linearised system ----------------------------------------------------------------

def variableCount(points, curves):
    return 2 * len(points) + sum(1 for c in curves if c['kind'] == 'circle')


def inherentCount(curves):
    """An arc's ends lie at the same distance from its centre"""
    return sum(1 for c in curves if c['kind'] == 'arc')


def _layout(points, curves):
    values = [v for p in points for v in p]
    radiusIndex = {}
    for index, curve in enumerate(curves):
        if curve['kind'] == 'circle':
            radiusIndex[index] = len(values)
            values.append(1.0)
    return values, radiusIndex


def _function(constraint, curves, radiusIndex):
    kind = constraint[0]

    def X(v, i):
        return v[2 * i]

    def Y(v, i):
        return v[2 * i + 1]

    if kind in ('horizontal', 'vertical'):
        c = curves[constraint[1]]
        get = Y if kind == 'horizontal' else X
        return lambda v: get(v, c['a']) - get(v, c['b'])
    if kind == 'originAt':
        get = X if constraint[2] == 'x' else Y
        return lambda v: get(v, constraint[1])
    if kind == 'diameter':
        index = radiusIndex[constraint[1]]
        return lambda v: v[index]
    if kind in ('hdim', 'vdim'):
        get = X if kind == 'hdim' else Y
        i, j = constraint[1], constraint[2]
        if j is None:
            return lambda v: get(v, i)
        return lambda v: get(v, i) - get(v, j)
    if kind == 'arcEnds':
        a = curves[constraint[1]]

        def equal(v):
            c, s, e = a['center'], a['start'], a['end']
            return ((X(v, c) - X(v, s)) ** 2 + (Y(v, c) - Y(v, s)) ** 2
                    - (X(v, c) - X(v, e)) ** 2 - (Y(v, c) - Y(v, e)) ** 2)
        return equal
    raise ValueError(kind)


def _variables(constraint, curves, radiusIndex):
    kind = constraint[0]
    if kind in ('horizontal', 'vertical'):
        c = curves[constraint[1]]
        pointIndices = [c['a'], c['b']]
    elif kind == 'arcEnds':
        a = curves[constraint[1]]
        pointIndices = [a['center'], a['start'], a['end']]
    elif kind == 'diameter':
        return [radiusIndex[constraint[1]]]
    elif kind == 'originAt':
        pointIndices = [constraint[1]]
    else:
        pointIndices = [constraint[1]] + ([] if constraint[2] is None else [constraint[2]])
    return sorted({2 * i + k for i in pointIndices for k in (0, 1)})


def _row(constraint, curves, radiusIndex, values):
    function = _function(constraint, curves, radiusIndex)
    row = {}
    h = 1e-6
    for k in _variables(constraint, curves, radiusIndex):
        saved = values[k]
        values[k] = saved + h
        up = function(values)
        values[k] = saved - h
        down = function(values)
        values[k] = saved
        derivative = (up - down) / (2 * h)
        if abs(derivative) > 1e-12:
            row[k] = derivative
    norm = math.sqrt(sum(x * x for x in row.values()))
    return {k: x / norm for k, x in row.items()} if norm > 0 else row


class _Basis:
    """Fully reduced sparse row echelon form: add() keeps a row only if it is independent of the rows so far"""

    def __init__(self):
        self.rows = {}

    def add(self, row):
        row = dict(row)
        for pivot in [k for k in row if k in self.rows]:
            factor = row.get(pivot, 0.0)
            if factor:
                for k, x in self.rows[pivot].items():
                    row[k] = row.get(k, 0.0) - factor * x
        row = {k: x for k, x in row.items() if abs(x) > 1e-13}
        if not row:
            return False
        pivot = max(row, key=lambda k: abs(row[k]))
        if abs(row[pivot]) < _RANK_EPS * 1e3:
            return False
        scale = row[pivot]
        row = {k: x / scale for k, x in row.items()}
        for other in self.rows.values():
            factor = other.get(pivot, 0.0)
            if factor:
                for k, x in row.items():
                    other[k] = other.get(k, 0.0) - factor * x
                other.pop(pivot, None)
        self.rows[pivot] = row
        return True


def rank(points, curves, constraints):
    values, radiusIndex = _layout(points, curves)
    basis = _Basis()
    count = 0
    for index, curve in enumerate(curves):
        if curve['kind'] == 'arc':
            count += basis.add(_row(('arcEnds', index), curves, radiusIndex, values))
    for constraint in constraints:
        rows = [('originAt', constraint[1], 'x'), ('originAt', constraint[1], 'y')] if constraint[0] == 'originAt' else [constraint]
        for item in rows:
            count += basis.add(_row(item, curves, radiusIndex, values))
    return count


# -- the chain -------------------------------------------------------------------------------------------------------

class _Chain:
    def __init__(self, points):
        self.points = points
        self.known = set()
        self.out = []

    def _differs(self, p, reference, axis):
        other = 0.0 if reference is None else self.points[reference][axis]
        return abs(self.points[p][axis] - other) > _EPS

    def fixAxis(self, p, axis, references):
        for reference in references:
            if reference != p and (reference is None or reference in self.known) and self._differs(p, reference, axis):
                self.out.append(('hdim' if axis == 0 else 'vdim', p, reference))
                return
        raise ValueError(f'sketch chain: no reference for point {p} on axis {axis}')

    def references(self, p, first=()):
        """Where a new point may hang: the given points, the nearest fixed points, then the origin"""
        others = sorted(self.known, key=lambda q: math.dist(self.points[p], self.points[q]))
        return list(first) + others + [None]

    def anchor(self, candidates):
        candidates = sorted(candidates)
        for p in candidates:
            x, y = self.points[p]
            if abs(x) < _EPS and abs(y) < _EPS:
                self.out.append(('originAt', p))
                self.known.add(p)
                return
        chosen = next((p for p in candidates if abs(self.points[p][0]) > _EPS and abs(self.points[p][1]) > _EPS),
                      candidates[0])
        for axis in (0, 1):
            self.fixAxis(chosen, axis, [None] + self.references(chosen))
        self.known.add(chosen)

    def line(self, index, curve):
        a, b = curve['a'], curve['b']
        if a in self.known and b in self.known:
            return
        known, new = (a, b) if a in self.known else (b, a)
        (kx, ky), (nx, ny) = self.points[known], self.points[new]
        if abs(ky - ny) < _EPS:
            self.out.append(('horizontal', index))
            self.fixAxis(new, 0, self.references(new, [known]))
        elif abs(kx - nx) < _EPS:
            self.out.append(('vertical', index))
            self.fixAxis(new, 1, self.references(new, [known]))
        else:
            self.fixAxis(new, 0, self.references(new, [known]))
            self.fixAxis(new, 1, self.references(new, [known]))
        self.known.add(new)

    def onCircle(self, p, center):
        """An arc end on a fixed centre needs one dimension: on the axis it lies off the centre least. An end straight
        below the centre fixed by its height would touch the circle there (a double root), fixed by x it crosses it"""
        (px, py), (cx, cy) = self.points[p], self.points[center]
        axis = 0 if abs(px - cx) <= abs(py - cy) else 1
        self.fixAxis(p, axis, self.references(p, [center]))
        self.known.add(p)

    def arc(self, index, curve):
        c, s, e = curve['center'], curve['start'], curve['end']
        if c not in self.known:
            if s in self.known and e in self.known:
                # the centre lies on the chord's bisector: one dimension along it
                (sx, sy), (ex, ey) = self.points[s], self.points[e]
                axis = 0 if abs(ey - sy) >= abs(ex - sx) else 1
                self.fixAxis(c, axis, self.references(c, [s, e]))
                self.known.add(c)
                return
            # the other end first, by two dimensions, then the centre on the chord's bisector as above. Fixed on the
            # circle by one dimension, the end had a second solution across the centre: the label rail's end level with
            # its centre flipped there after a width change (fusion-auftraege/r27_diag4.log, Chamfer30 lost its edge)
            known = s if s in self.known else e
            other = e if known == s else s
            self.fixAxis(other, 0, self.references(other, [known]))
            self.fixAxis(other, 1, self.references(other, [known]))
            self.known.add(other)
            self.arc(index, curve)
            return
        new = [p for p in (s, e) if p not in self.known]
        if not new:
            raise ValueError('sketch chain: arc with its centre and both ends fixed elsewhere')
        if len(new) == 2:
            first = new.pop(0)
            self.fixAxis(first, 0, self.references(first, [c]))
            self.fixAxis(first, 1, self.references(first, [c]))
            self.known.add(first)
        self.onCircle(new[0], c)

    def circle(self, index, curve):
        c = curve['center']
        if c not in self.known:
            for axis in (0, 1):
                self.fixAxis(c, axis, [None] + self.references(c))
            self.known.add(c)
        self.out.append(('diameter', index))


def _ends(curve):
    return [curve[k] for k in ('a', 'b', 'start', 'end', 'center') if k in curve]


def chain(points, curves):
    parent = list(range(len(points)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for curve in curves:
        ends = _ends(curve)
        for m in ends[1:]:
            parent[find(m)] = find(ends[0])
    state = _Chain(points)
    roots = []
    for curve in curves:
        root = find(_ends(curve)[0])
        if root not in roots:
            roots.append(root)
    for root in roots:
        members = [(i, c) for i, c in enumerate(curves) if find(_ends(c)[0]) == root]
        if not all(c['kind'] == 'circle' for _, c in members):
            # a shape starts on a point of its outline, not on an arc centre
            outline = {p for _, c in members for k in ('a', 'b', 'start', 'end') if k in c for p in [c[k]]}
            state.anchor(outline)
        remaining = list(members)
        while remaining:
            for position, (index, curve) in enumerate(remaining):
                if curve['kind'] == 'circle' or any(p in state.known for p in _ends(curve)):
                    break
            else:
                raise ValueError('sketch chain: a curve hangs on nothing fixed')
            remaining.pop(position)
            getattr(state, curve['kind'])(index, curve)
    return state.out
