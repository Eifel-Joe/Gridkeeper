r"""
Stroke widths of letter outlines, to find the least text height a 0.4 mm nozzle still prints (round 17).

    python tools/fontStroke.py D:/Entwicklung/Gridfinity/fusion-auftraege/r17_font.json

The json comes from the Fusion job r17_font: per text style the outlines of A-Z a-z 0-9 at 10 mm text height as
segments (x1, y1, x2, y2) in mm. From points along the outline a ray runs across the stroke, at right angles to the
outline, to where it leaves the letter again: that length is the stroke there. Points close to a sharp corner don't
count, the ray runs out at once there (the tip of an A is a corner, not a stroke). The thinnest stroke is the 1 %
quantile of all of them, so single points don't decide it.
"""

import bisect
import json
import math
import sys

SHARP_TURN = math.radians(30)
QUANTILE = 0.01
# largest stroke looked for, longer rays aren't followed
MAX_STROKE = 3.0
_CELL = 0.25
_EPS = 1e-7


def _key(x: float, y: float) -> tuple[int, int]:
    return (round(x * 1e4), round(y * 1e4))


def _sharpCorners(segments) -> list[tuple[float, float]]:
    """Ends where two segments meet at a turn of more than SHARP_TURN"""
    ends: dict[tuple[int, int], list[tuple[float, float, float, float]]] = {}
    for segment in segments:
        (x1, y1, x2, y2) = segment
        ends.setdefault(_key(x1, y1), []).append((x1, y1, x2 - x1, y2 - y1))
        ends.setdefault(_key(x2, y2), []).append((x2, y2, x1 - x2, y1 - y2))
    corners = []
    for touching in ends.values():
        if len(touching) != 2:
            continue
        ((x, y, ax, ay), (_, _, bx, by)) = touching
        # both point away from the end: straight on they are opposite
        angle = math.atan2(ax * by - ay * bx, ax * bx + ay * by)
        if math.pi - abs(angle) > SHARP_TURN:
            corners.append((x, y))
    return corners


class _Outline:
    def __init__(self, segments):
        self.segments = [s for s in segments if (s[2] - s[0]) ** 2 + (s[3] - s[1]) ** 2 > _EPS ** 2]
        self.cells: dict[tuple[int, int], list[int]] = {}
        for (index, (x1, y1, x2, y2)) in enumerate(self.segments):
            for cx in range(math.floor(min(x1, x2) / _CELL), math.floor(max(x1, x2) / _CELL) + 1):
                for cy in range(math.floor(min(y1, y2) / _CELL), math.floor(max(y1, y2) / _CELL) + 1):
                    self.cells.setdefault((cx, cy), []).append(index)

    def near(self, x0: float, y0: float, x1: float, y1: float) -> set[int]:
        found = set()
        for cx in range(math.floor(min(x0, x1) / _CELL), math.floor(max(x0, x1) / _CELL) + 1):
            for cy in range(math.floor(min(y0, y1) / _CELL), math.floor(max(y0, y1) / _CELL) + 1):
                found.update(self.cells.get((cx, cy), ()))
        return found

    def inside(self, x: float, y: float) -> bool:
        """Even-odd: crossings of a ray to the right"""
        crossings = 0
        cy = math.floor(y / _CELL)
        candidates = set()
        for (cell, indices) in self.cells.items():
            if cell[1] == cy and cell[0] >= math.floor(x / _CELL):
                candidates.update(indices)
        for index in candidates:
            (x1, y1, x2, y2) = self.segments[index]
            if (y1 > y) != (y2 > y):
                crossX = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if crossX > x:
                    crossings += 1
        return crossings % 2 == 1

    def hit(self, x: float, y: float, dx: float, dy: float, own: int) -> float | None:
        """Distance along the ray to the first segment it crosses, none within MAX_STROKE"""
        best = None
        for index in self.near(x, y, x + dx * MAX_STROKE, y + dy * MAX_STROKE):
            if index == own:
                continue
            (x1, y1, x2, y2) = self.segments[index]
            (ex, ey) = (x2 - x1, y2 - y1)
            denominator = dx * ey - dy * ex
            if abs(denominator) < 1e-12:
                continue
            t = ((x1 - x) * ey - (y1 - y) * ex) / denominator
            u = ((x1 - x) * dy - (y1 - y) * dx) / denominator
            if t > _EPS and -1e-9 <= u <= 1 + 1e-9 and (best is None or t < best):
                best = t
        return best


def strokeWidths(segments, step: float, cornerSkip: float = 0.5) -> list[float]:
    """Stroke width across the letter from points every `step` along the outline, none within `cornerSkip` of a
    sharp corner"""
    outline = _Outline(segments)
    corners = _sharpCorners(outline.segments)
    widths = []
    for (index, (x1, y1, x2, y2)) in enumerate(outline.segments):
        length = math.hypot(x2 - x1, y2 - y1)
        (tx, ty) = ((x2 - x1) / length, (y2 - y1) / length)
        count = max(1, round(length / step))
        for k in range(count):
            t = (k + 0.5) / count * length
            (px, py) = (x1 + tx * t, y1 + ty * t)
            if any(math.hypot(px - cx, py - cy) < cornerSkip for (cx, cy) in corners):
                continue
            # the normal pointing into the letter
            (nx, ny) = (-ty, tx)
            probe = min(step, 1e-3)
            if not outline.inside(px + nx * probe, py + ny * probe):
                (nx, ny) = (-nx, -ny)
            distance = outline.hit(px, py, nx, ny, index)
            if distance is not None:
                widths.append(distance)
    return widths


def thinnestStroke(segments, step: float, cornerSkip: float = 0.5) -> float:
    widths = sorted(strokeWidths(segments, step, cornerSkip))
    return widths[min(len(widths) - 1, int(len(widths) * QUANTILE))]


def main() -> int:
    with open(sys.argv[1], encoding='utf-8') as file:
        data = json.load(file)
    height = data['height_mm']
    for (style, entry) in data['styles'].items():
        thinnest = thinnestStroke([tuple(s) for s in entry['segments']], 0.05)
        print(f'{style}: thinnest stroke {thinnest:.3f} mm at {height:g} mm, {thinnest / height:.4f} per height, '
              f'0.4 mm from {0.4 / (thinnest / height):.2f} mm text height')
    return 0


if __name__ == '__main__':
    sys.exit(main())
