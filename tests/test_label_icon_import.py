"""
How labelGenerator puts a symbol into a sketch (round 40, p371): one importSVG, placed from the symbol's own outline
(svgSymbol), no probe imports into throwaway sketches, no import just to measure it. labelGenerator needs Fusion to
load, so the two functions are read from its source and run against a recording sketch.
"""

import ast
import importlib.util
import os
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, 'lib', 'gridfinityUtils', 'labelGenerator.py')
HEX_NUT = os.path.join(ROOT, 'lib', 'gridfinityUtils', 'labelIcons', 'nuts', 'hex-nut.svg')


def _svgSymbol():
    spec = importlib.util.spec_from_file_location('svgSymbol', os.path.join(ROOT, 'lib', 'gridfinityUtils', 'svgSymbol.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


svgSymbol = _svgSymbol()


class Point:
    def __init__(self, x, y, z=0):
        (self.x, self.y, self.z) = (x, y, z)


class Box:
    def __init__(self, minX, minY, maxX, maxY):
        (self.minPoint, self.maxPoint) = (Point(minX, minY), Point(maxX, maxY))


class Curve:
    """An imported curve is fixed, as Fusion leaves it; Sketch.move doesn't move fixed geometry (Fusion 18.11.2026)"""
    def __init__(self, box):
        self.boundingBox = box
        self.isFixed = True


class SketchPoint:
    def __init__(self):
        self.isFixed = True


class Curves(list):
    @property
    def count(self):
        return len(self)

    def item(self, index):
        return self[index]


class Matrix:
    def __init__(self):
        self.translation = None
        self.cells = {}

    def setCell(self, row, column, value):
        self.cells[(row, column)] = value
        return True

    @staticmethod
    def create():
        return Matrix()


class Vector:
    @staticmethod
    def create(x, y, z):
        return (x, y, z)


class RecordingSketch:
    """Imports put one curve with the bounds svgSymbol says (shifted by `off`), or `handBounds` for a file svgSymbol
    can't read; moves are recorded. `throwaways` collects the sketches added beside it, none unless allowed"""
    def __init__(self, off=(0.0, 0.0), handBounds=None, allowThrowaway=False):
        self.imports = []
        self.moves = []
        self.sketchCurves = Curves()
        self.sketchPoints = Curves()
        self.originPoint = SketchPoint()
        self.off = off
        self.handBounds = handBounds
        self.allowThrowaway = allowThrowaway
        self.throwaways = []
        self.deleted = False
        self.parentComponent = types.SimpleNamespace(sketches=types.SimpleNamespace(add=self._throwaway))
        self.referencePlane = None

    def _throwaway(self, plane):
        if not self.allowThrowaway:
            raise AssertionError('no throwaway sketch for a probe import')
        sketch = RecordingSketch(handBounds=self.handBounds)
        self.throwaways.append(sketch)
        return sketch

    def deleteMe(self):
        self.deleted = True
        return True

    def importSVG(self, path, x, y, scale):
        self.imports.append((path, x, y, scale))
        if self.handBounds is not None:
            unit = svgSymbol.SVG_UNIT_CM * scale
            (b0, b1, b2, b3) = self.handBounds
            self.sketchCurves.append(Curve(Box(b0 * unit + x, -b3 * unit + y, b2 * unit + x, -b1 * unit + y)))
            self.sketchPoints += [SketchPoint() for _ in range(4)]
            return True
        bounds = svgSymbol.readSymbol(path).bounds
        unit = svgSymbol.SVG_UNIT_CM * scale
        self.sketchCurves.append(Curve(Box(bounds[0] * unit + x + self.off[0], -bounds[3] * unit + y + self.off[1],
                                           bounds[2] * unit + x + self.off[0], -bounds[1] * unit + y + self.off[1])))
        self.sketchPoints.append(SketchPoint())
        return True

    def move(self, entities, matrix):
        assert not any(curve.isFixed for curve in self.sketchCurves), 'fixed curves are not moved'
        assert not any(point.isFixed for point in self.sketchPoints), 'fixed points are not moved'
        self.moves.append((list(entities), matrix.translation))
        return True


def _functions(*names):
    tree = ast.parse(open(SOURCE, encoding='utf-8').read())
    source = '\n\n'.join(ast.unparse(node) for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names)
    logs = []
    namespace = {
        'os': os,
        'svgSymbol': svgSymbol,
        'adsk': types.SimpleNamespace(core=types.SimpleNamespace(Matrix3D=Matrix, Vector3D=Vector), fusion=types.SimpleNamespace(Sketch=object)),
        'commonUtils': types.SimpleNamespace(debugLog=logs.append, objectCollectionFromList=lambda items: list(items)),
    }
    exec(compile(source, SOURCE, 'exec'), namespace)
    return (namespace, logs)


def test_import_icon_imports_once_where_svg_symbol_says():
    (namespace, logs) = _functions('_importIcon', '_iconCurvesBounds')
    sketch = RecordingSketch()
    namespace['_importIcon'](sketch, HEX_NUT, 2.0, 1.0, 0.8)
    assert len(sketch.imports) == 1
    assert sketch.imports[0] == (HEX_NUT, *svgSymbol.importArguments(svgSymbol.readSymbol(HEX_NUT).bounds, 2.0, 1.0, 0.8))
    assert sketch.moves == []
    assert any('placed at 2.000, 1.000' in log for log in logs)


def test_import_icon_moves_when_fusion_puts_it_elsewhere():
    (namespace, _) = _functions('_importIcon', '_iconCurvesBounds')
    sketch = RecordingSketch(off=(0.01, -0.02))
    namespace['_importIcon'](sketch, HEX_NUT, 2.0, 1.0, 0.8)
    assert len(sketch.imports) == 1
    [(curves, translation)] = sketch.moves
    assert len(curves) == 1
    assert translation == pytest.approx((-0.01, 0.02, 0))
    # fixed again afterwards, as the import left them
    assert all(curve.isFixed for curve in sketch.sketchCurves) and all(point.isFixed for point in sketch.sketchPoints)


def test_icon_measure_reads_the_file():
    (namespace, _) = _functions('_iconMeasure')
    sketch = RecordingSketch()
    (aspect, points) = namespace['_iconMeasure'](sketch, HEX_NUT)
    assert sketch.imports == []
    symbol = svgSymbol.readSymbol(HEX_NUT)
    assert (aspect, points) == (pytest.approx(symbol.aspect), symbol.pointCount)


def test_no_probe_imports_left():
    source = open(SOURCE, encoding='utf-8').read()
    assert '_importMeasured' not in source
    # one in _importIcon, one in _iconMeasure for a hand drawn file svgSymbol can't read
    assert source.count('importSVG(') == 2


HAND_DRAWN = '<svg viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg"><path d="m 1,2 l 4,0 l 0,2 z"/></svg>'


def test_hand_drawn_svg_imports_once_and_is_scaled_by_a_move(tmp_path):
    # a file svgSymbol can't read (relative commands, circles, transforms): imported as it is, then scaled and moved
    # by one uniform scaling move, still a single import
    path = tmp_path / 'hand.svg'
    path.write_text(HAND_DRAWN)
    (namespace, _) = _functions('_importIcon', '_iconCurvesBounds')
    sketch = RecordingSketch(handBounds=(1, 2, 5, 4))
    namespace['_importIcon'](sketch, str(path), 2.0, 1.0, 0.8)
    assert sketch.imports == [(str(path), 0, 0, 1)]
    [(curves, translation)] = sketch.moves
    unit = svgSymbol.SVG_UNIT_CM
    scale = 0.8 / (2 * unit)
    assert translation == pytest.approx((2.0 - 1 * unit * scale, 1.0 - (-4 * unit) * scale, 0))


def test_hand_drawn_svg_measured_by_one_throwaway_import(tmp_path):
    path = tmp_path / 'hand.svg'
    path.write_text(HAND_DRAWN)
    (namespace, _) = _functions('_iconMeasure', '_iconCurvesBounds')
    sketch = RecordingSketch(handBounds=(1, 2, 5, 4), allowThrowaway=True)
    (aspect, points) = namespace['_iconMeasure'](sketch, str(path))
    [throwaway] = sketch.throwaways
    assert len(throwaway.imports) == 1 and throwaway.deleted
    assert aspect == pytest.approx(2.0)
    assert points == 3
