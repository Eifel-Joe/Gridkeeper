"""
The symbol svgs of the labels (lib/gridfinityUtils/cullenectIcons, labelIcons) read without Fusion: their closed paths
of lines, circular arcs and cubic splines, the outline of what they draw, how many sketch points an import makes and
where Sketch.importSVG puts them. Round 40 (p371): one import per symbol, placed from these numbers, instead of probe
imports to measure it (four imports and walking every sketch curve took 40 s for a Torx symbol)
"""

import math
import re
from dataclasses import dataclass

# Sketch.importSVG maps an svg point (x, y) to the sketch point (x, -y) * SVG_UNIT_CM * scale + (posX, posY), whatever
# the viewBox and the unit of width and height say, on every sketch plane: measured in Fusion 18.11.2026 (XY, XZ, YZ,
# a triangle and a half circle as probe). An svg unit is a CSS pixel, 1/96 inch
SVG_UNIT_CM = 2.54 / 96

Point = tuple[float, float]
# ('line', p0, p1), ('arc', p0, p1, rx, ry, rotation, largeArc, sweep) as the svg A command, ('cubic', p0, c1, c2, p1)
Segment = tuple

_TOKEN = re.compile(r'[MLACZmlacz]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')
_ARGUMENTS = {'M': 2, 'L': 2, 'A': 7, 'C': 6}


def parsePath(d: str) -> list[list[Segment]]:
    """The closed paths of an svg path's data, each a list of segments ending where it starts. Absolute M, L, A, C and
    Z, as the symbol files are written; a line of no length is left out, Fusion draws none"""
    tokens = _TOKEN.findall(d)
    loops: list[list[Segment]] = []
    loop: list[Segment] = []
    start: Point | None = None
    current: Point | None = None
    command = None
    index = 0

    def close():
        nonlocal loop, current
        if start is not None and current is not None and current != start:
            loop.append(('line', current, start))
        if len(loop) > 0:
            loops.append(loop)
        loop = []
        current = start

    while index < len(tokens):
        token = tokens[index]
        if token.isalpha():
            if token.islower() and token not in 'z':
                raise ValueError(f'relative path command {token} is not supported')
            command = token.upper()
            index += 1
            if command == 'Z':
                close()
            continue
        if command not in _ARGUMENTS:
            raise ValueError(f'number without a path command: {token}')
        values = [float(value) for value in tokens[index:index + _ARGUMENTS[command]]]
        if len(values) < _ARGUMENTS[command]:
            raise ValueError(f'path command {command} is missing numbers')
        index += _ARGUMENTS[command]
        if command == 'M':
            if len(loop) > 0:
                close()
            start = current = (values[0], values[1])
            # numbers after a moveto are lines, as in svg
            command = 'L'
        elif command == 'L':
            end = (values[0], values[1])
            if end != current:
                loop.append(('line', current, end))
            current = end
        elif command == 'A':
            end = (values[5], values[6])
            loop.append(('arc', current, end, values[0], values[1], values[2], values[3] != 0, values[4] != 0))
            current = end
        elif command == 'C':
            end = (values[4], values[5])
            loop.append(('cubic', current, (values[0], values[1]), (values[2], values[3]), end))
            current = end
    if len(loop) > 0:
        close()
    return loops


def arcCenter(segment: Segment) -> tuple[float, float, float, float, float, float, float]:
    """(cx, cy, rx, ry, rotation in radians, start angle, sweep angle) of an arc segment, after svg 1.1 F.6.5, the
    radii scaled up when too small for the endpoints"""
    (_, (x1, y1), (x2, y2), rx, ry, rotation, largeArc, sweep) = segment
    phi = math.radians(rotation)
    (cos, sin) = (math.cos(phi), math.sin(phi))
    (dx, dy) = ((x1 - x2) / 2, (y1 - y2) / 2)
    x1p = cos * dx + sin * dy
    y1p = -sin * dx + cos * dy
    (rx, ry) = (abs(rx), abs(ry))
    scale = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if scale > 1:
        (rx, ry) = (rx * math.sqrt(scale), ry * math.sqrt(scale))
    numerator = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    denominator = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    factor = math.sqrt(max(0.0, numerator / denominator)) if denominator > 0 else 0.0
    if largeArc == sweep:
        factor = -factor
    cxp = factor * rx * y1p / ry
    cyp = -factor * ry * x1p / rx
    cx = cos * cxp - sin * cyp + (x1 + x2) / 2
    cy = sin * cxp + cos * cyp + (y1 + y2) / 2
    start = math.atan2((y1p - cyp) / ry, (x1p - cxp) / rx)
    end = math.atan2((-y1p - cyp) / ry, (-x1p - cxp) / rx)
    delta = end - start
    if sweep and delta <= 0:
        delta += 2 * math.pi
    elif not sweep and delta >= 0:
        delta -= 2 * math.pi
    return (cx, cy, rx, ry, phi, start, delta)


def arcPoint(center: tuple, angle: float) -> Point:
    (cx, cy, rx, ry, phi, _, _) = center
    (cos, sin) = (math.cos(phi), math.sin(phi))
    return (cx + rx * math.cos(angle) * cos - ry * math.sin(angle) * sin,
            cy + rx * math.cos(angle) * sin + ry * math.sin(angle) * cos)


def cubicPoint(segment: Segment, t: float) -> Point:
    (_, p0, c1, c2, p1) = segment
    u = 1 - t
    return tuple(u * u * u * a + 3 * u * u * t * b + 3 * u * t * t * c + t * t * t * e for (a, b, c, e) in zip(p0, c1, c2, p1))


def _withinSweep(angle: float, start: float, delta: float) -> bool:
    offset = (angle - start) % (2 * math.pi) if delta > 0 else (start - angle) % (2 * math.pi)
    return offset <= abs(delta)


def segmentEnd(segment: Segment) -> Point:
    return segment[2] if segment[0] == 'arc' else segment[-1]


def segmentBounds(segment: Segment) -> tuple[float, float, float, float]:
    """(minX, minY, maxX, maxY) of one segment, arcs and splines with their bulge"""
    kind = segment[0]
    points = [segment[1], segmentEnd(segment)]
    if kind == 'arc':
        center = arcCenter(segment)
        (_, _, rx, ry, phi, start, delta) = center
        # where x and y of the ellipse turn, half a turn apart each
        for base in (math.atan2(-ry * math.sin(phi), rx * math.cos(phi)), math.atan2(ry * math.cos(phi), rx * math.sin(phi))):
            for angle in (base, base + math.pi):
                if _withinSweep(angle, start, delta):
                    points.append(arcPoint(center, angle))
    elif kind == 'cubic':
        (_, p0, c1, c2, p1) = segment
        for axis in (0, 1):
            # the derivative a t² + b t + c of the axis' coordinate
            a = 3 * (-p0[axis] + 3 * c1[axis] - 3 * c2[axis] + p1[axis])
            b = 6 * (p0[axis] - 2 * c1[axis] + c2[axis])
            c = 3 * (c1[axis] - p0[axis])
            roots = []
            if abs(a) < 1e-12:
                if abs(b) > 1e-12:
                    roots.append(-c / b)
            else:
                discriminant = b * b - 4 * a * c
                if discriminant >= 0:
                    roots += [(-b + sign * math.sqrt(discriminant)) / (2 * a) for sign in (1, -1)]
            points += [cubicPoint(segment, t) for t in roots if 0 < t < 1]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def loopsBounds(loops: list[list[Segment]]) -> tuple[float, float, float, float]:
    boxes = [segmentBounds(segment) for loop in loops for segment in loop]
    return (min(box[0] for box in boxes), min(box[1] for box in boxes), max(box[2] for box in boxes), max(box[3] for box in boxes))


@dataclass
class Symbol:
    loops: list[list[Segment]]
    bounds: tuple[float, float, float, float]

    @property
    def pointCount(self) -> int:
        """Sketch points an import makes, as Fusion counts them besides the origin: the ends of the segments, which
        neighbours share, and the centre of each arc (measured 18.11.2026)"""
        return sum(len(loop) + sum(1 for segment in loop if segment[0] == 'arc') for loop in self.loops)

    @property
    def aspect(self) -> float:
        """Width of the drawing per unit of its height"""
        return (self.bounds[2] - self.bounds[0]) / (self.bounds[3] - self.bounds[1])


def pathData(svg: str) -> list[str]:
    """The d attributes of the svg's paths"""
    return re.findall(r'\sd="([^"]*)"', svg, re.S)


def readSymbol(path: str) -> Symbol:
    with open(path, encoding='utf-8') as file:
        svg = file.read()
    loops = [loop for d in pathData(svg) for loop in parsePath(d)]
    if len(loops) == 0:
        raise ValueError(f'{path}: no path')
    return Symbol(loops, loopsBounds(loops))


def importArguments(bounds: tuple[float, float, float, float], minX: float, minY: float, height: float) -> tuple[float, float, float]:
    """(x, y, scale) for Sketch.importSVG so the drawing of the given svg bounds is height high with its bottom left
    corner at (minX, minY), all in cm, see SVG_UNIT_CM. Svg y runs down, its largest y lands at the bottom"""
    scale = height / ((bounds[3] - bounds[1]) * SVG_UNIT_CM)
    unit = SVG_UNIT_CM * scale
    return (minX - bounds[0] * unit, minY + bounds[3] * unit, scale)
