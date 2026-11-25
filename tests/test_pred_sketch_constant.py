"""
Round 45 (p480): WorldSketch leaves a dimension at the value it was drawn with when its dim does not depend on any
parameter (Dim.dependsOnParameters): two points that hang on the same measure keep their distance whatever the
parameter, the expression would only cost a Parameter.expression call (195 ms each in a second box,
fusion-auftraege/r45_profil.log) and a dependency in the document. Dimensions that follow a parameter get their
expression as before. Runs _apply on stand-ins for the sketch.
"""

import types

import pytest

from tests.test_pred_sketch_fixed import predSketch

Dim = predSketch.Dim


class _Parameter:
    def __init__(self):
        self.expression = None


class _Dimension:
    def __init__(self):
        self.parameter = _Parameter()


class _Dimensions:
    def __init__(self):
        self.made = []

    def addDistanceDimension(self, first, second, orientation, text, isDriving):
        self.made.append(_Dimension())
        return self.made[-1]

    def addDiameterDimension(self, circle, text, isDriving):
        self.made.append(_Dimension())
        return self.made[-1]


class _Point:
    def __init__(self, x, y):
        self.x, self.y, self.z = x, y, 0.0
        self.isFixed = False


class _Circle:
    def __init__(self, x, y):
        self.centerSketchPoint = types.SimpleNamespace(geometry=_Point(x, y))


@pytest.fixture
def sketch(monkeypatch):
    monkeypatch.setattr(predSketch.adsk.fusion, "DimensionOrientations",
                        types.SimpleNamespace(HorizontalDimensionOrientation=0, VerticalDimensionOrientation=1), raising=False)
    monkeypatch.setattr(predSketch.adsk.core, "Point3D", types.SimpleNamespace(create=lambda x, y, z: _Point(x, y)), raising=False)
    world = predSketch.WorldSketch.__new__(predSketch.WorldSketch)
    world.sketch = types.SimpleNamespace(sketchDimensions=_Dimensions(), geometricConstraints=None, originPoint=_Point(0, 0))
    world.xAxis, world.yAxis = (0, 1), (1, 1)
    return world


def _width():
    parameter = types.SimpleNamespace(name="gfBox1_baseWidth", value=5)
    return Dim.parameter(parameter) * Dim.length(4.2) + Dim.length(2.0)


def test_a_distance_between_points_on_the_same_measure_gets_no_expression(sketch):
    outer = _width()
    sketch.worldPoints = [(outer - Dim.length(2.1), Dim.length(1.0), 0.0), (outer - Dim.length(4.1), Dim.length(1.0), 0.0)]
    sketch.curves = []
    points = {0: _Point(19.9, 1.0), 1: _Point(17.9, 1.0)}
    sketch._apply([("hdim", 0, 1)], [], points, [points[0], points[1]])
    (dimension,) = sketch.sketch.sketchDimensions.made
    assert dimension.parameter.expression is None


def test_a_distance_that_follows_a_parameter_keeps_its_expression(sketch):
    outer = _width()
    sketch.worldPoints = [(outer - Dim.length(2.1), Dim.length(1.0), 0.0), (Dim.length(3.0), Dim.length(1.0), 0.0)]
    sketch.curves = []
    points = {0: _Point(19.9, 1.0), 1: _Point(3.0, 1.0)}
    sketch._apply([("hdim", 0, 1), ("hdim", 0, None)], [], points, [points[0], points[1]])
    (between, fromOrigin) = sketch.sketch.sketchDimensions.made
    assert "gfBox1_baseWidth" in between.parameter.expression
    assert between.parameter.expression.startswith("abs(")
    assert "gfBox1_baseWidth" in fromOrigin.parameter.expression


def test_a_diameter_only_with_a_parameter_in_it(sketch):
    width = Dim.parameter(types.SimpleNamespace(name="gfBox1_baseWidth", value=5))
    sketch.worldPoints = [(Dim.length(1.0), Dim.length(1.0), 0.0)]
    sketch.curves = [{"kind": "circle", "center": 0, "diameter": Dim.length(0.6)},
                     {"kind": "circle", "center": 0, "diameter": (width - width) + Dim.length(0.4)},
                     {"kind": "circle", "center": 0, "diameter": width * Dim.length(0.1)}]
    drawn = [_Circle(1.0, 1.0), _Circle(1.0, 1.0), _Circle(1.0, 1.0)]
    sketch._apply([("diameter", 0), ("diameter", 1), ("diameter", 2)], drawn, {0: _Point(1.0, 1.0)}, [_Point(1.0, 1.0)])
    expressions = [d.parameter.expression for d in sketch.sketch.sketchDimensions.made]
    assert expressions[:2] == [None, None]
    assert "gfBox1_baseWidth" in expressions[2]


# Round 59: in a document that isn't in mm, Fusion keeps a dimension left as drawn as a rounded text in its units,
# '0.0787401575 in' for 2 mm, and evaluates it again when a parameter change recomputes the sketch: 1e-10 cm off, the
# two 2 mm roundings of a 4 mm catch slide no longer meet in one face, nor the mirrored halves of the handle
# (fusion-auftraege/r59_paramfaces.log, the same with every dimension in mm: r59_paramfaces2.log). There every
# dimension gets its expression, in mm; documents in mm stay as they are.
def test_in_inches_a_distance_on_the_same_measure_gets_its_length_in_mm(sketch):
    sketch.isDocumentInMm = False
    outer = _width()
    sketch.worldPoints = [(outer - Dim.length(2.1), Dim.length(1.0), 0.0), (outer - Dim.length(4.1), Dim.length(1.0), 0.0)]
    sketch.curves = []
    points = {0: _Point(19.9, 1.0), 1: _Point(17.9, 1.0)}
    sketch._apply([("hdim", 0, 1)], [], points, [points[0], points[1]])
    (dimension,) = sketch.sketch.sketchDimensions.made
    assert dimension.parameter.expression == "20 mm"


def test_in_inches_a_constant_diameter_gets_its_length_in_mm(sketch):
    sketch.isDocumentInMm = False
    sketch.worldPoints = [(Dim.length(1.0), Dim.length(1.0), 0.0)]
    sketch.curves = [{"kind": "circle", "center": 0, "diameter": Dim.length(0.6)}]
    sketch._apply([("diameter", 0)], [_Circle(1.0, 1.0)], {0: _Point(1.0, 1.0)}, [_Point(1.0, 1.0)])
    (dimension,) = sketch.sketch.sketchDimensions.made
    assert dimension.parameter.expression == "6 mm"


def test_in_inches_a_distance_that_follows_a_parameter_keeps_its_expression(sketch):
    sketch.isDocumentInMm = False
    outer = _width()
    sketch.worldPoints = [(outer - Dim.length(2.1), Dim.length(1.0), 0.0), (Dim.length(3.0), Dim.length(1.0), 0.0)]
    sketch.curves = []
    points = {0: _Point(19.9, 1.0), 1: _Point(3.0, 1.0)}
    sketch._apply([("hdim", 0, 1)], [], points, [points[0], points[1]])
    (dimension,) = sketch.sketch.sketchDimensions.made
    assert "gfBox1_baseWidth" in dimension.parameter.expression


def test_a_document_is_in_mm_unless_its_units_say_otherwise():
    units = types.SimpleNamespace(MillimeterDistanceUnits=2, InchDistanceUnits=3, CentimeterDistanceUnits=1)
    design = lambda unit: types.SimpleNamespace(fusionUnitsManager=types.SimpleNamespace(distanceDisplayUnits=unit))
    assert predSketch.isInMm(design(2), units)
    assert not predSketch.isInMm(design(3), units)
    assert not predSketch.isInMm(design(1), units)
    assert predSketch.isInMm(None, units)
