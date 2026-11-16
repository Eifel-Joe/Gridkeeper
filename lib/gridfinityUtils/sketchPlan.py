"""
Which conditions and dimensions bind a sketch completely, without one too many (round 27, task 3b).

Fusion rejected box sketches whose points were each dimensioned to the origin as over constrained
(fusion-auftraege/r27_probe*.out). Nutzer chose the way of the existing generators ("Ja, Formen-Weg"): lines horizontal
or vertical, arcs tangent, each shape one anchor, then lengths. This module picks those from candidates in a fixed
order and keeps a candidate only when it raises the rank of the linearised system, until every degree of freedom is
bound. Rules from the probes: never two dimensions between the same two points, never both origin dimensions on one
point, never a dimension of zero.

Fusion-free. Points are (x, y) in sketch coordinates; curves are dicts:
  {'kind': 'line', 'a': i, 'b': j}, {'kind': 'arc', 'center': c, 'start': i, 'end': j}, {'kind': 'circle', 'center': c}
Arc ends and centers are points of the list; a circle adds its radius as one more unknown.
Result: tuples ('horizontal'|'vertical'|'originOnLine'|'radius'|'diameter', curve), ('tangent', arc, curve),
('hdim'|'vdim', point, otherPoint or None for the origin).
"""

import math

_EPS = 1e-7
_RANK_EPS = 1e-9


def variableCount(points, curves):
    return 2 * len(points) + sum(1 for c in curves if c['kind'] == 'circle')


def inherentCount(curves):
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
    if kind == 'originOnLine':
        # a horizontal line through the origin has y = 0, a vertical one x = 0
        c = curves[constraint[1]]
        get = Y if constraint[2] == 'horizontal' else X
        return lambda v: get(v, c['a'])
    if kind == 'tangent':
        arc, other = curves[constraint[1]], curves[constraint[2]]
        p = constraint[3]
        c = arc['center']
        if other['kind'] == 'line':
            q = other['b'] if other['a'] == p else other['a']
            return lambda v: (X(v, c) - X(v, p)) * (X(v, q) - X(v, p)) + (Y(v, c) - Y(v, p)) * (Y(v, q) - Y(v, p))
        d = other['center']
        return lambda v: (X(v, c) - X(v, p)) * (Y(v, d) - Y(v, p)) - (Y(v, c) - Y(v, p)) * (X(v, d) - X(v, p))
    if kind == 'radius':
        a = curves[constraint[1]]
        return lambda v: math.hypot(X(v, a['center']) - X(v, a['start']), Y(v, a['center']) - Y(v, a['start']))
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
    """The unknowns a constraint touches, so its gradient stays sparse"""
    kind = constraint[0]
    pointIndices = []
    if kind in ('horizontal', 'vertical', 'originOnLine'):
        c = curves[constraint[1]]
        pointIndices = [c['a'], c['b']]
    elif kind == 'tangent':
        arc, other = curves[constraint[1]], curves[constraint[2]]
        pointIndices = [arc['center'], constraint[3]] + [other[k] for k in ('a', 'b', 'center') if k in other]
    elif kind in ('radius', 'arcEnds'):
        a = curves[constraint[1]]
        pointIndices = [a['center'], a['start'], a['end']]
    elif kind == 'diameter':
        return [radiusIndex[constraint[1]]]
    else:
        pointIndices = [constraint[1]] + ([] if constraint[2] is None else [constraint[2]])
    return sorted({2 * i + k for i in pointIndices for k in (0, 1)})


def _gradient(function, values, variables):
    row = {}
    h = 1e-6
    for k in variables:
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
        self.rows = {}  # pivot -> row (dict), pivot entry 1, zero in every other pivot column

    def reduce(self, row):
        row = dict(row)
        for pivot in [k for k in row if k in self.rows]:
            factor = row.get(pivot, 0.0)
            if factor:
                for k, x in self.rows[pivot].items():
                    row[k] = row.get(k, 0.0) - factor * x
        return {k: x for k, x in row.items() if abs(x) > 1e-13}

    def add(self, row):
        row = self.reduce(row)
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


def _row(constraint, curves, radiusIndex, values):
    return _gradient(_function(constraint, curves, radiusIndex), values, _variables(constraint, curves, radiusIndex))


def rank(points, curves, constraints):
    values, radiusIndex = _layout(points, curves)
    basis = _Basis()
    count = 0
    for index, curve in enumerate(curves):
        if curve['kind'] == 'arc':
            count += basis.add(_row(('arcEnds', index), curves, radiusIndex, values))
    for constraint in constraints:
        count += basis.add(_row(_full(constraint, curves), curves, radiusIndex, values))
    return count


def _full(constraint, curves):
    """Tangent constraints carry the shared point internally"""
    if constraint[0] == 'tangent' and len(constraint) == 3:
        arc, other = curves[constraint[1]], curves[constraint[2]]
        ends = {arc['start'], arc['end']}
        otherEnds = {other.get('a'), other.get('b')} if other['kind'] == 'line' else {other['start'], other['end']}
        shared = (ends & otherEnds).pop()
        return constraint + (shared,)
    return constraint


def _candidates(points, curves):
    def P(i):
        return points[i]

    out = []
    for index, c in enumerate(curves):
        if c['kind'] == 'line':
            (ax, ay), (bx, by) = P(c['a']), P(c['b'])
            if abs(ay - by) < _EPS:
                out.append(('horizontal', index))
            elif abs(ax - bx) < _EPS:
                out.append(('vertical', index))
    for index, c in enumerate(curves):
        if c['kind'] != 'arc':
            continue
        cx, cy = P(c['center'])
        for otherIndex, other in enumerate(curves):
            if otherIndex == index or other['kind'] == 'circle':
                continue
            ends = [other['a'], other['b']] if other['kind'] == 'line' else [other['start'], other['end']]
            for p in (c['start'], c['end']):
                if p not in ends:
                    continue
                px, py = P(p)
                if other['kind'] == 'line':
                    q = ends[1] if ends[0] == p else ends[0]
                    qx, qy = P(q)
                    length = math.hypot(qx - px, qy - py)
                    if abs((cx - px) * (qx - px) + (cy - py) * (qy - py)) < _EPS * max(length, 1):
                        out.append(('tangent', index, otherIndex))
                else:
                    dx, dy = P(other['center'])
                    if other['center'] != c['center'] and abs((cx - px) * (dy - py) - (cy - py) * (dx - px)) < _EPS:
                        if index < otherIndex:
                            out.append(('tangent', index, otherIndex))
    for index, c in enumerate(curves):
        if c['kind'] == 'line':
            (ax, ay), (bx, by) = P(c['a']), P(c['b'])
            onLine = abs(ax * by - bx * ay) < _EPS
            within = min(ax, bx) - _EPS <= 0 <= max(ax, bx) + _EPS and min(ay, by) - _EPS <= 0 <= max(ay, by) + _EPS
            if onLine and within and abs(ay - by) < _EPS:
                out.append(('originOnLine', index, 'horizontal'))
            elif onLine and within and abs(ax - bx) < _EPS:
                out.append(('originOnLine', index, 'vertical'))
    for index, c in enumerate(curves):
        if c['kind'] == 'arc':
            out.append(('radius', index))
        elif c['kind'] == 'circle':
            out.append(('diameter', index))
    return out


def _components(points, curves):
    parent = list(range(len(points)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for c in curves:
        members = [c[k] for k in ('a', 'b', 'center', 'start', 'end') if k in c]
        for m in members[1:]:
            parent[find(m)] = find(members[0])
    groups = {}
    for i in range(len(points)):
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=lambda g: min(g))


def planConstraints(points, curves):
    values, radiusIndex = _layout(points, curves)
    total = variableCount(points, curves)
    basis = _Basis()
    for index, curve in enumerate(curves):
        if curve['kind'] == 'arc':
            basis.add(_row(('arcEnds', index), curves, radiusIndex, values))
    chosen = []
    pairs = set()
    originUse = {}

    def tryAdd(constraint):
        if len(chosen) + inherentCount(curves) >= total:
            return False
        kind = constraint[0]
        if kind in ('hdim', 'vdim'):
            i, j = constraint[1], constraint[2]
            axis = 0 if kind == 'hdim' else 1
            other = 0.0 if j is None else points[j][axis]
            if j == i or abs(points[i][axis] - other) < _EPS:
                return False
            if j is None:
                if originUse.get(i, kind) != kind:
                    return False
            elif frozenset((i, j)) in pairs:
                return False
        row = _row(_full(constraint, curves), curves, radiusIndex, values)
        if not basis.add(row):
            return False
        chosen.append(constraint)
        if kind in ('hdim', 'vdim'):
            if constraint[2] is None:
                originUse[constraint[1]] = kind
            else:
                pairs.add(frozenset((constraint[1], constraint[2])))
        return True

    for candidate in _candidates(points, curves):
        tryAdd(candidate)

    components = _components(points, curves)
    placed = []
    for group in components:
        if not placed:
            for kind in ('hdim', 'vdim'):
                for i in group:
                    if tryAdd((kind, i, None)):
                        break
        else:
            # anchor on the nearest point of a shape already placed, not on the origin
            for kind in ('hdim', 'vdim'):
                done = False
                for i in group:
                    for j in sorted(placed, key=lambda j: math.dist(points[i], points[j])):
                        if tryAdd((kind, i, j)):
                            done = True
                            break
                    if done:
                        break
        placed += group

    # lengths along the curves, then between any points of a shape, then anything left
    for c in curves:
        ends = [c[k] for k in ('a', 'b', 'start', 'end', 'center') if k in c]
        for i in ends:
            for j in ends:
                if i < j:
                    tryAdd(('hdim', i, j))
                    tryAdd(('vdim', i, j))
    for group in components:
        for i in group:
            for j in sorted(group, key=lambda j: math.dist(points[i], points[j])):
                if i < j:
                    tryAdd(('hdim', i, j))
                    tryAdd(('vdim', i, j))
    for i in range(len(points)):
        tryAdd(('hdim', i, None))
        tryAdd(('vdim', i, None))
    # a shape of one point (concentric circles) has nothing else to hang on: both origin dimensions on it
    for group in components:
        if len(group) == 1:
            originUse.pop(group[0], None)
            tryAdd(('vdim', group[0], None))
            tryAdd(('hdim', group[0], None))
    if len(chosen) + inherentCount(curves) != total:
        raise ValueError(f'sketch plan: {total - len(chosen) - inherentCount(curves)} degrees of freedom left')
    return chosen
