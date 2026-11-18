"""
Rebuilds the polygons of the label symbol svgs as lines, circular arcs and cubic splines (round 40, p371).

OpenSCAD writes every rounding as a polygon: the Torx drive of a countersunk screw is 1670 points 0.01 mm apart, and
Fusion took 40 s to build a box label with it. This tool turns each closed polygon of a symbol file into as few
segments as fit within a tolerance (0.01 mm by default) and checks the result before it writes anything:

- a polygon on one circle becomes a whole circle, two half arcs (as Fusion imports a circle anyway),
- otherwise, from the sharpest corner on, each run of points becomes the longest line or circular arc that stays
  within the tolerance (points and chord midpoints, turning one way, under a full turn),
- two or more arcs in a row that join smoothly and turn the same way, which a freeform like an ellipse gives, become
  cubic splines where one fits within the tolerance,
- paths that already hold arcs or splines are left as they are, so a second run changes nothing.

Checks per file, the file is not written when one fails (SymbolCheckError): the new outline is within the tolerance
of the polygon both ways (points of either to the other), the area of each closed path is within 0.5 % or 0.01 square
units, the number of closed paths is the same. The svg header, title and style stay, only the path data changes.
Each folder gets symbol-check.json with the area of every closed path and the outline of the polygons, so the tests
can check the files without the polygons.

The tolerance is in svg units, millimetres in the files OpenSCAD writes. Run after rendering symbols:

    python dev-notes/tools/arcSymbols.py [--tolerance 0.01] [--check] <folder or svg> ...
"""

import argparse
import importlib.util
import json
import math
import os
import re
import sys
from dataclasses import dataclass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHECK_FILE = 'symbol-check.json'
DEFAULT_TOLERANCE = 0.01
# an arc of a larger radius is no rounding but a line drawn slightly bent
MAX_RADIUS = 60.0
# smooth joint between arcs that may become one spline, degrees
SMOOTH_JOINT = 10.0
# how many more points a run is tried after the last fit before it gives up
LOOKAHEAD = 8
# shapes are fitted within this share of the tolerance: the check samples the whole outline, the fit only the points
# and chord midpoints, an arc off centre to its chord strays a little further between them
FIT_MARGIN = 0.9


def _loadSvgSymbol():
    path = os.path.join(PROJECT_ROOT, 'lib', 'gridfinityUtils', 'svgSymbol.py')
    spec = importlib.util.spec_from_file_location('svgSymbol', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


svgSymbol = _loadSvgSymbol()


class SymbolCheckError(Exception):
    pass


@dataclass
class Report:
    name: str
    pointsBefore: int
    lines: int
    arcs: int
    cubics: int
    deviation: float
    areaChange: float
    changed: bool
    # why the file was left as it is, empty when it passed
    error: str = ''


# --- geometry -----------------------------------------------------------------------------------------------------

def _segmentDistance(p, a, b) -> float:
    (dx, dy) = (b[0] - a[0], b[1] - a[1])
    lengthSquared = dx * dx + dy * dy
    t = 0.0 if lengthSquared == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / lengthSquared))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _fitCircle(points):
    """(cx, cy, r) of the least squares circle (Kåsa) through the points, None when they are on a line"""
    count = len(points)
    mx = sum(p[0] for p in points) / count
    my = sum(p[1] for p in points) / count
    suu = svv = suv = suuu = svvv = suvv = svuu = 0.0
    for (x, y) in points:
        (u, v) = (x - mx, y - my)
        suu += u * u
        svv += v * v
        suv += u * v
        suuu += u * u * u
        svvv += v * v * v
        suvv += u * v * v
        svuu += v * u * u
    determinant = suu * svv - suv * suv
    if abs(determinant) < 1e-18:
        return None
    uc = (0.5 * (suuu + suvv) * svv - 0.5 * (svvv + svuu) * suv) / determinant
    vc = (0.5 * (svvv + svuu) * suu - 0.5 * (suuu + suvv) * suv) / determinant
    (cx, cy) = (uc + mx, vc + my)
    return (cx, cy, sum(math.hypot(p[0] - cx, p[1] - cy) for p in points) / count)


def _fitsLine(points, tolerance) -> bool:
    return all(_segmentDistance(p, points[0], points[-1]) <= tolerance for p in points[1:-1])


def _fitCircleThroughEnds(points):
    """(cx, cy, r) of the circle through the first and the last point that fits the others best (algebraic least
    squares along the perpendicular bisector of the chord): the arc as the svg writes it, by its ends and radius"""
    ((x0, y0), (x1, y1)) = (points[0], points[-1])
    (mx, my) = ((x0 + x1) / 2, (y0 + y1) / 2)
    chord = math.hypot(x1 - x0, y1 - y0)
    if chord == 0:
        return None
    (nx, ny) = (-(y1 - y0) / chord, (x1 - x0) / chord)
    half = chord / 2
    numerator = denominator = 0.0
    for (x, y) in points[1:-1]:
        (u, v) = (x - mx, y - my)
        along = nx * u + ny * v
        numerator += (u * u + v * v - half * half) * along
        denominator += along * along
    if denominator < 1e-18:
        return None
    offset = numerator / (2 * denominator)
    (cx, cy) = (mx + offset * nx, my + offset * ny)
    return (cx, cy, math.hypot(x0 - cx, y0 - cy))


def _fitsArc(points, tolerance):
    """(cx, cy, r, sweep angle) when the points lie on one circular arc through the first and the last point within
    the tolerance, else None"""
    if len(points) < 4:
        return None
    fitted = _fitCircleThroughEnds(points)
    if fitted is None or fitted[2] > MAX_RADIUS:
        return None
    (cx, cy, r) = fitted
    for p in points:
        if abs(math.hypot(p[0] - cx, p[1] - cy) - r) > tolerance:
            return None
    for (a, b) in zip(points, points[1:]):
        if abs(math.hypot((a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cy) - r) > tolerance:
            return None
    angles = [math.atan2(p[1] - cy, p[0] - cx) for p in points]
    steps = [(b - a + math.pi) % (2 * math.pi) - math.pi for (a, b) in zip(angles, angles[1:])]
    if not (all(step > 0 for step in steps) or all(step < 0 for step in steps)):
        return None
    sweep = sum(steps)
    if abs(sweep) >= 2 * math.pi - 1e-6:
        return None
    return (cx, cy, r, sweep)


def _arcSegment(start, end, fit) -> tuple:
    (_, _, r, sweep) = fit
    return ('arc', start, end, r, r, 0.0, abs(sweep) > math.pi, sweep > 0)


def _signedArea(points) -> float:
    return sum(a[0] * b[1] - b[0] * a[1] for (a, b) in zip(points, points[1:] + points[:1])) / 2


def _turn(points, index) -> float:
    (a, b, c) = (points[index - 1], points[index], points[(index + 1) % len(points)])
    (v1, v2) = ((b[0] - a[0], b[1] - a[1]), (c[0] - b[0], c[1] - b[1]))
    return abs(math.atan2(v1[0] * v2[1] - v1[1] * v2[0], v1[0] * v2[0] + v1[1] * v2[1]))


def _direction(vector):
    length = math.hypot(*vector)
    return (vector[0] / length, vector[1] / length) if length > 0 else (0.0, 0.0)


def _tangents(segment):
    """Unit tangents along the segment at its start and its end"""
    if segment[0] == 'line':
        direction = _direction((segment[2][0] - segment[1][0], segment[2][1] - segment[1][1]))
        return (direction, direction)
    if segment[0] == 'cubic':
        (_, p0, c1, c2, p1) = segment
        return (_direction((c1[0] - p0[0], c1[1] - p0[1])), _direction((p1[0] - c2[0], p1[1] - c2[1])))
    center = svgSymbol.arcCenter(segment)
    (cx, cy, _, _, _, start, delta) = center
    sign = 1 if delta > 0 else -1
    return tuple((-math.sin(angle) * sign, math.cos(angle) * sign) for angle in (start, start + delta))


def _angleBetween(a, b) -> float:
    return math.degrees(abs(math.atan2(a[0] * b[1] - a[1] * b[0], a[0] * b[0] + a[1] * b[1])))


# --- cubic splines ------------------------------------------------------------------------------------------------

def _bezier(p0, c1, c2, p1, t):
    u = 1 - t
    return (u * u * u * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t * t * t * p1[0],
            u * u * u * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t * t * t * p1[1])


def _polylineDistance(p, polyline) -> float:
    return min(_segmentDistance(p, a, b) for (a, b) in zip(polyline, polyline[1:]))


def _fitCubic(points, startTangent, endTangent, tolerance):
    """One cubic spline from the first to the last point, leaving and arriving along the tangents, by least squares
    over chord length parameters, improved by Newton steps on the parameters (Schneider's method), None when it isn't
    within the tolerance both ways"""
    lengths = [0.0]
    for (a, b) in zip(points, points[1:]):
        lengths.append(lengths[-1] + math.dist(a, b))
    if lengths[-1] == 0:
        return None
    parameters = [length / lengths[-1] for length in lengths]
    for _ in range(4):
        controls = _cubicControls(points, parameters, startTangent, endTangent)
        if controls is None:
            return None
        cubic = ('cubic', points[0], controls[0], controls[1], points[-1])
        samples = [_bezier(points[0], controls[0], controls[1], points[-1], i / 200) for i in range(201)]
        if all(_polylineDistance(point, samples) <= tolerance for point in points)                 and all(_polylineDistance(sample, points) <= tolerance for sample in samples):
            return cubic
        parameters = [_newton(cubic, point, t) for (point, t) in zip(points, parameters)]
    return None


def _newton(cubic, point, t):
    """The parameter one Newton step nearer to the point's foot on the spline"""
    (_, p0, c1, c2, p1) = cubic
    u = 1 - t
    position = _bezier(p0, c1, c2, p1, t)
    first = [3 * (u * u * (c1[k] - p0[k]) + 2 * u * t * (c2[k] - c1[k]) + t * t * (p1[k] - c2[k])) for k in (0, 1)]
    second = [6 * (u * (c2[k] - 2 * c1[k] + p0[k]) + t * (p1[k] - 2 * c2[k] + c1[k])) for k in (0, 1)]
    difference = [position[k] - point[k] for k in (0, 1)]
    numerator = sum(difference[k] * first[k] for k in (0, 1))
    denominator = sum(first[k] * first[k] + difference[k] * second[k] for k in (0, 1))
    if denominator == 0:
        return t
    return min(1.0, max(0.0, t - numerator / denominator))


def _cubicControls(points, parameters, startTangent, endTangent):
    """The two inner control points of the least squares spline over the given parameters"""
    (p0, p1) = (points[0], points[-1])
    back = (-endTangent[0], -endTangent[1])
    c = [[0.0, 0.0], [0.0, 0.0]]
    x = [0.0, 0.0]
    for (point, t) in zip(points, parameters):
        u = 1 - t
        a1 = (startTangent[0] * 3 * u * u * t, startTangent[1] * 3 * u * u * t)
        a2 = (back[0] * 3 * u * t * t, back[1] * 3 * u * t * t)
        c[0][0] += a1[0] * a1[0] + a1[1] * a1[1]
        c[0][1] += a1[0] * a2[0] + a1[1] * a2[1]
        c[1][1] += a2[0] * a2[0] + a2[1] * a2[1]
        base = _bezier(p0, p0, p1, p1, t)
        rest = (point[0] - base[0], point[1] - base[1])
        x[0] += a1[0] * rest[0] + a1[1] * rest[1]
        x[1] += a2[0] * rest[0] + a2[1] * rest[1]
    c[1][0] = c[0][1]
    determinant = c[0][0] * c[1][1] - c[0][1] * c[1][0]
    chord = math.dist(p0, p1)
    if abs(determinant) < 1e-18:
        return None
    alpha1 = (x[0] * c[1][1] - x[1] * c[0][1]) / determinant
    alpha2 = (c[0][0] * x[1] - c[1][0] * x[0]) / determinant
    if alpha1 <= 1e-6 * chord or alpha2 <= 1e-6 * chord:
        return None
    return ((p0[0] + startTangent[0] * alpha1, p0[1] + startTangent[1] * alpha1),
            (p1[0] + back[0] * alpha2, p1[1] + back[1] * alpha2))


def _jointTangent(pieces, before, after, ownIsAfter):
    """The tangent where piece before ends and piece after starts (around the closed path): the mean of both where
    they meet smoothly (arcs fitted to a freeform kink slightly there), at a corner the one of the run's own piece"""
    (incoming, outgoing) = (_tangents(pieces[before % len(pieces)][0])[1], _tangents(pieces[after % len(pieces)][0])[0])
    if _angleBetween(incoming, outgoing) > SMOOTH_JOINT:
        return outgoing if ownIsAfter else incoming
    return _direction((incoming[0] + outgoing[0], incoming[1] + outgoing[1]))


def _splines(pieces, tolerance):
    """Runs of two or more arcs that join smoothly and turn the same way, as cubic splines where they fit (a spline
    over three arcs of an ellipse spans more than it can follow within 0.01)"""
    result = []
    index = 0
    while index < len(pieces):
        (segment, _) = pieces[index]
        last = index
        if segment[0] == 'arc':
            while last + 1 < len(pieces):
                (current, following) = (pieces[last][0], pieces[last + 1][0])
                if following[0] != 'arc' or following[7] != current[7] \
                        or _angleBetween(_tangents(current)[1], _tangents(following)[0]) > SMOOTH_JOINT:
                    break
                last += 1
        replaced = False
        # from the longest run down to two arcs
        for end in range(last, index, -1):
            points = pieces[index][1] + [point for (_, run) in pieces[index + 1:end + 1] for point in run[1:]]
            cubic = _fitCubic(points, _jointTangent(pieces, index - 1, index, True), _jointTangent(pieces, end, end + 1, False), tolerance)
            if cubic is not None:
                result.append((cubic, points))
                index = end + 1
                replaced = True
                break
        if not replaced:
            result.append(pieces[index])
            index += 1
    return result


# --- decomposition ------------------------------------------------------------------------------------------------

def _dedupe(points):
    result = []
    for point in points:
        if len(result) == 0 or math.dist(point, result[-1]) > 1e-9:
            result.append(point)
    if len(result) > 1 and math.dist(result[0], result[-1]) <= 1e-9:
        result.pop()
    return result


def _greedy(sequence, tolerance):
    """(segment, its points) along the open sequence, each the longest line or arc from where the last one ended"""
    pieces = []
    index = 0
    last = len(sequence) - 1
    while index < last:
        lineEnd = index + 1
        arc = None
        end = index + 1
        while end <= last:
            run = sequence[index:end + 1]
            if _fitsLine(run, tolerance):
                lineEnd = end
            fit = _fitsArc(run, tolerance)
            if fit is not None:
                arc = (end, fit)
            if end - lineEnd > LOOKAHEAD and (arc is None or end - arc[0] > LOOKAHEAD):
                break
            end += 1
        if arc is not None and arc[0] > lineEnd:
            (end, fit) = arc
            pieces.append((_arcSegment(sequence[index], sequence[end], fit), sequence[index:end + 1]))
        else:
            end = lineEnd
            pieces.append((('line', sequence[index], sequence[end]), sequence[index:end + 1]))
        index = end
    return pieces


def _mergeAcrossStart(pieces, tolerance):
    """The last and the first piece as one line or arc when they fit together: the start fell inside a shape, or the
    piece before it ate a few of its points"""
    if len(pieces) < 3:
        return pieces
    points = pieces[-1][1] + pieces[0][1][1:]
    if _fitsLine(points, tolerance):
        merged = ('line', points[0], points[-1])
    else:
        fit = _fitsArc(points, tolerance)
        if fit is None:
            return pieces
        merged = _arcSegment(points[0], points[-1], fit)
    return [(merged, points)] + pieces[1:-1]


def decomposeLoop(points, tolerance):
    """The closed polygon (its points without the first repeated at the end) as lines, circular arcs and cubic
    splines, segments as svgSymbol.Segment, ending where they start"""
    tolerance *= FIT_MARGIN
    points = _dedupe(points)
    if len(points) >= 8:
        fitted = _fitCircle(points)
        if fitted is not None and fitted[2] <= MAX_RADIUS \
                and all(abs(math.hypot(p[0] - fitted[0], p[1] - fitted[1]) - fitted[2]) <= tolerance for p in points) \
                and all(abs(math.hypot((a[0] + b[0]) / 2 - fitted[0], (a[1] + b[1]) / 2 - fitted[1]) - fitted[2]) <= tolerance
                        for (a, b) in zip(points, points[1:] + points[:1])):
            (cx, cy, _) = fitted
            start = points[0]
            # the half arcs go through the start and its opposite, their radius is the start's distance
            r = math.hypot(start[0] - cx, start[1] - cy)
            opposite = (2 * cx - start[0], 2 * cy - start[1])
            sweep = _signedArea(points) > 0
            return [('arc', start, opposite, r, r, 0.0, False, sweep), ('arc', opposite, start, r, r, 0.0, False, sweep)]
    first = max(range(len(points)), key=lambda index: _turn(points, index))
    sequence = points[first:] + points[:first] + [points[first]]
    pieces = _mergeAcrossStart(_greedy(sequence, tolerance), tolerance)
    pieces = _splines(pieces, tolerance)
    return [segment for (segment, _) in pieces]


# --- path data, area, deviation -----------------------------------------------------------------------------------

def _number(value: float) -> str:
    text = f'{value:.6g}'
    return '0' if text in ('-0', '0') else text


def _point(point) -> str:
    return f'{_number(point[0])},{_number(point[1])}'


def pathData(loops) -> str:
    """Svg path data of closed paths of segments, absolute M, L, A, C and z"""
    parts = []
    for loop in loops:
        words = [f'M {_point(loop[0][1])}']
        for (index, segment) in enumerate(loop):
            if segment[0] == 'line':
                if index == len(loop) - 1 and segment[2] == loop[0][1]:
                    continue  # z closes it
                words.append(f'L {_point(segment[2])}')
            elif segment[0] == 'arc':
                (_, _, end, rx, ry, rotation, largeArc, sweep) = segment
                words.append(f'A {_number(rx)},{_number(ry)} {_number(rotation)} {int(largeArc)} {int(sweep)} {_point(end)}')
            else:
                (_, _, c1, c2, end) = segment
                words.append(f'C {_point(c1)} {_point(c2)} {_point(end)}')
        parts.append(' '.join(words) + ' z')
    return '\n'.join(parts)


_GAUSS = [(-0.9602898564975363, 0.1012285362903763), (-0.7966664774136267, 0.2223810344533745),
          (-0.5255324099163290, 0.3137066458778873), (-0.1834346424956498, 0.3626837833783620),
          (0.1834346424956498, 0.3626837833783620), (0.5255324099163290, 0.3137066458778873),
          (0.7966664774136267, 0.2223810344533745), (0.9602898564975363, 0.1012285362903763)]


def _segmentArea(segment) -> float:
    """The segment's part of the closed path's signed area, half the integral of x dy - y dx along it"""
    start = segment[1]
    end = svgSymbol.segmentEnd(segment)
    chord = (start[0] * end[1] - end[0] * start[1]) / 2
    if segment[0] == 'line':
        return chord
    if segment[0] == 'arc':
        (_, _, rx, ry, phi, _, delta) = svgSymbol.arcCenter(segment)
        if abs(rx - ry) <= 1e-12 * max(rx, 1):
            return chord + rx * rx / 2 * (delta - math.sin(delta))
        return _sampledArea([svgSymbol.arcPoint(svgSymbol.arcCenter(segment), svgSymbol.arcCenter(segment)[5] + delta * i / 256) for i in range(257)])
    (_, p0, c1, c2, p1) = segment
    area = 0.0
    for (node, weight) in _GAUSS:
        t = (node + 1) / 2
        (x, y) = _bezier(p0, c1, c2, p1, t)
        u = 1 - t
        dx = 3 * (u * u * (c1[0] - p0[0]) + 2 * u * t * (c2[0] - c1[0]) + t * t * (p1[0] - c2[0]))
        dy = 3 * (u * u * (c1[1] - p0[1]) + 2 * u * t * (c2[1] - c1[1]) + t * t * (p1[1] - c2[1]))
        area += weight / 2 * (x * dy - y * dx)
    return area / 2


def _sampledArea(points) -> float:
    return sum(a[0] * b[1] - b[0] * a[1] for (a, b) in zip(points, points[1:])) / 2


def loopArea(loop) -> float:
    """Signed area of a closed path of segments, positive when it turns with growing svg angle"""
    return sum(_segmentArea(segment) for segment in loop)


def _samples(segment, step):
    """Points along the segment, at most step apart, start included, end left out"""
    start = segment[1]
    if segment[0] == 'line':
        end = segment[2]
        count = max(1, math.ceil(math.dist(start, end) / step))
        return [(start[0] + (end[0] - start[0]) * i / count, start[1] + (end[1] - start[1]) * i / count) for i in range(count)]
    if segment[0] == 'arc':
        center = svgSymbol.arcCenter(segment)
        (_, _, rx, ry, _, begin, delta) = center
        count = max(2, math.ceil(abs(delta) * max(rx, ry) / step))
        return [svgSymbol.arcPoint(center, begin + delta * i / count) for i in range(count)]
    (_, p0, c1, c2, p1) = segment
    length = math.dist(p0, c1) + math.dist(c1, c2) + math.dist(c2, p1)
    count = max(2, math.ceil(length / step))
    return [_bezier(p0, c1, c2, p1, i / count) for i in range(count)]


class _SegmentIndex:
    """The segments of polylines in a grid, to find the nearest one to a point quickly"""
    def __init__(self, polylines, cell):
        self.cell = cell
        self.grid = {}
        for line in polylines:
            for (a, b) in zip(line, line[1:] + line[:1]):
                for gx in range(math.floor(min(a[0], b[0]) / cell), math.floor(max(a[0], b[0]) / cell) + 1):
                    for gy in range(math.floor(min(a[1], b[1]) / cell), math.floor(max(a[1], b[1]) / cell) + 1):
                        self.grid.setdefault((gx, gy), []).append((a, b))

    def distance(self, point, limit) -> float:
        """Distance to the nearest segment, or something above limit when none is that near"""
        reach = math.ceil(limit / self.cell)
        (gx, gy) = (math.floor(point[0] / self.cell), math.floor(point[1] / self.cell))
        best = math.inf
        for x in range(gx - reach, gx + reach + 1):
            for y in range(gy - reach, gy + reach + 1):
                for (a, b) in self.grid.get((x, y), ()):
                    best = min(best, _segmentDistance(point, a, b))
        return best


def contourDeviation(originals, loops, limit: float = 0.05) -> float:
    """How far the closed paths of segments and the polygons (lists of points) are apart at most, from points of
    either to the other; the new outline is sampled a quarter of a hundredth apart. Only distances up to limit are
    searched (a grid of cells that size), anything farther counts as infinite: a check fails either way"""
    step = 0.0025
    sampled = [[point for segment in loop for point in _samples(segment, step)] for loop in loops]
    worst = 0.0
    toOriginal = _SegmentIndex(originals, limit)
    toNew = _SegmentIndex(sampled, limit)
    for line in sampled:
        for point in line:
            worst = max(worst, toOriginal.distance(point, limit))
    for line in originals:
        for point in line:
            worst = max(worst, toNew.distance(point, limit))
    return worst


# --- files --------------------------------------------------------------------------------------------------------

def _polygon(loop):
    """The points of a closed path of lines only, None when it holds arcs or splines"""
    if any(segment[0] != 'line' for segment in loop):
        return None
    return [segment[1] for segment in loop]


def _counts(loops):
    kinds = [segment[0] for loop in loops for segment in loop]
    return (kinds.count('line'), kinds.count('arc'), kinds.count('cubic'))


def convertFile(path: str, tolerance: float = DEFAULT_TOLERANCE, write: bool = True) -> Report:
    """Rebuilds the polygons of one symbol svg, checks the result and writes it (unless write is off). Raises
    SymbolCheckError when a check fails, nothing is written then"""
    with open(path, encoding='utf-8') as file:
        svg = file.read()
    datas = svgSymbol.pathData(svg)
    if len(datas) != 1:
        raise SymbolCheckError(f'{path}: {len(datas)} paths, the symbols have one')
    loops = svgSymbol.parsePath(datas[0])
    newLoops = []
    originals = []
    for loop in loops:
        polygon = _polygon(loop)
        segments = decomposeLoop(polygon, tolerance) if polygon is not None else loop
        if polygon is not None and (len(segments) < len(loop) or any(segment[0] != 'line' for segment in segments)):
            newLoops.append(segments)
            originals.append(polygon)
        else:
            newLoops.append(loop)
    name = os.path.basename(path)
    pointsBefore = sum(len(loop) for loop in loops)
    if len(originals) == 0:
        return Report(name, pointsBefore, *_counts(loops), 0.0, 0.0, False)
    data = pathData(newLoops)
    written = svgSymbol.parsePath(data)
    if len(written) != len(loops):
        raise SymbolCheckError(f'{name}: {len(written)} closed paths instead of {len(loops)}')
    deviation = contourDeviation([_polygon(loop) or [p for s in loop for p in _samples(s, 0.0025)] for loop in loops], written)
    if deviation > tolerance:
        raise SymbolCheckError(f'{name}: outline {deviation:.4f} off, more than {tolerance}')
    areaChange = 0.0
    for (old, new) in zip(loops, written):
        (before, after) = (abs(loopArea(old)), abs(loopArea(new)))
        areaChange = max(areaChange, abs(after - before))
        # an outline within the tolerance all round can't change the area by more than its length times the
        # tolerance; a fixed share would refuse the coarse hardware polygons, whose arcs bulge out to the circles
        # they stand for
        if abs(after - before) > _perimeter(old) * tolerance:
            raise SymbolCheckError(f'{name}: area of a closed path {before:.4f} -> {after:.4f}')
    if write:
        with open(path, 'w', encoding='utf-8', newline='\n') as file:
            file.write(svg.replace(datas[0], '\n' + data + '\n', 1))
    return Report(name, pointsBefore, *_counts(written), deviation, areaChange, True)


def _perimeter(loop) -> float:
    points = [point for segment in loop for point in _samples(segment, 0.01)]
    return sum(math.dist(a, b) for (a, b) in zip(points, points[1:] + points[:1]))


def _checkEntry(path: str) -> dict:
    symbol = svgSymbol.readSymbol(path)
    return {'areas': [round(loopArea(loop), 6) for loop in symbol.loops], 'bounds': [round(value, 6) for value in symbol.bounds]}


def convertFolder(folder: str, tolerance: float = DEFAULT_TOLERANCE, write: bool = True) -> list[Report]:
    """Every svg directly in the folder, and its symbol-check.json: the entry of a file is taken before the file is
    rebuilt and kept for files a run leaves as they are. A file that fails a check is left as it is, its report says
    why"""
    checkPath = os.path.join(folder, CHECK_FILE)
    check = {}
    if os.path.isfile(checkPath):
        with open(checkPath, encoding='utf-8') as file:
            check = json.load(file)
    reports = []
    names = sorted(name for name in os.listdir(folder) if name.lower().endswith('.svg'))
    for name in names:
        path = os.path.join(folder, name)
        entry = _checkEntry(path)
        try:
            report = convertFile(path, tolerance, write)
        except SymbolCheckError as err:
            # the file stays a polygon, the others go on
            report = Report(name, 0, 0, 0, 0, 0.0, 0.0, False, str(err))
        if report.changed or name not in check:
            check[name] = entry
        reports.append(report)
    check = {name: check[name] for name in names if name in check}
    if write and len(names) > 0:
        with open(checkPath, 'w', encoding='utf-8', newline='\n') as file:
            json.dump(check, file, indent=1, sort_keys=True)
            file.write('\n')
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().split('\n')[0])
    parser.add_argument('paths', nargs='+', help='folders (with their subfolders) or svg files')
    parser.add_argument('--tolerance', type=float, default=DEFAULT_TOLERANCE, help='svg units, mm in the OpenSCAD files')
    parser.add_argument('--check', action='store_true', help='write nothing, only report')
    arguments = parser.parse_args()
    folders = []
    for path in arguments.paths:
        if os.path.isdir(path):
            folders += [root for (root, _, files) in os.walk(path) if any(name.lower().endswith('.svg') for name in files)]
        else:
            folders.append(os.path.dirname(os.path.abspath(path)))
    totals = [0, 0, 0, 0, 0]
    failed = 0
    for folder in sorted(set(folders)):
        reports = convertFolder(folder, arguments.tolerance, not arguments.check)
        for report in reports:
            if report.error:
                print(f'FAILED, left as it is: {report.error}')
                failed += 1
            if report.changed:
                print(f'{report.name}: {report.pointsBefore} -> {report.lines} lines, {report.arcs} arcs, {report.cubics} splines, '
                      f'outline {report.deviation:.4f}, area {report.areaChange:.5f}')
            totals = [a + b for (a, b) in zip(totals, (1 if report.changed else 0, report.pointsBefore if report.changed else 0, report.lines, report.arcs, report.cubics))]
    print(f'{totals[0]} files {"would change" if arguments.check else "rebuilt"}: {totals[1]} polygon points; '
          f'all files now {totals[2]} lines, {totals[3]} arcs, {totals[4]} splines')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
