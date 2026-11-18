"""
The frame around an outline that the trim cuts take their region from (round 35, p282 and p290). It was drawn with a bare
addTwoPointRectangle: Fusion only sets horizontal and vertical, position and size stayed free and the sketches
"Outer clearance trim sketch" and "Plate outline trim sketch" were never fully constrained.
"""

import os
import sys

import pytest

from tests.test_joint_origin_layout import _load

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FakePoint3D:
    def __init__(self, x, y, z=0):
        (self.x, self.y, self.z) = (x, y, z)

    @staticmethod
    def create(x, y, z=0):
        return FakePoint3D(x, y, z)

    def isEqualTo(self, other):
        return (self.x, self.y, self.z) == (other.x, other.y, other.z)


class FakeOrientations:
    HorizontalDimensionOrientation = "horizontal"
    VerticalDimensionOrientation = "vertical"


class SketchPoint:
    def __init__(self, x, y):
        self.geometry = FakePoint3D(x, y)


class Line:
    def __init__(self, start, end):
        (self.startSketchPoint, self.endSketchPoint) = (start, end)


class LineList(list):
    def item(self, index):
        return self[index]


class FakeSketch:
    """Records what a sketch gets: Fusion's addTwoPointRectangle starts at the first point, runs along x first and
    shares the corner points between its lines"""

    def __init__(self):
        self.isComputeDeferred = False
        self.originPoint = SketchPoint(0, 0)
        self.points = []
        self.lines = []
        self.constraints = []
        self.dimensions = []
        sketch = self

        class Lines:
            def addTwoPointRectangle(self, first, second):
                corners = [SketchPoint(first.x, first.y), SketchPoint(second.x, first.y), SketchPoint(second.x, second.y), SketchPoint(first.x, second.y)]
                sketch.points.extend(corners)
                rectangle = LineList(Line(corners[i], corners[(i + 1) % 4]) for i in range(4))
                sketch.lines.extend(rectangle)
                return rectangle

        class Curves:
            sketchLines = Lines()

        class Constraints:
            def addHorizontal(self, line):
                sketch.constraints.append(("horizontal", line))

            def addVertical(self, line):
                sketch.constraints.append(("vertical", line))

            def addCoincident(self, point, entity):
                sketch.constraints.append(("coincident", point, entity))

        class Parameter:
            expression = None

        class Dimension:
            def __init__(self):
                self.parameter = Parameter()

        class Dimensions:
            def addDistanceDimension(self, first, second, orientation, textPoint, isDriving=True):
                sketch.dimensions.append((first, second, orientation))
                return Dimension()

        self.sketchCurves = Curves()
        self.geometricConstraints = Constraints()
        self.sketchDimensions = Dimensions()

    def modelToSketchSpace(self, point):
        return FakePoint3D(point.x, point.y, point.z)

    def determinedPoints(self):
        """Points whose x and y follow from the origin through the constraints and dimensions, by propagation"""
        known = {id(self.originPoint): [True, True]}
        for point in self.points:
            known.setdefault(id(point), [False, False])
        changed = True
        while changed:
            changed = False
            def tie(a, b, axis):
                nonlocal changed
                if known[id(a)][axis] != known[id(b)][axis]:
                    known[id(a)][axis] = known[id(b)][axis] = True
                    changed = True
            for constraint in self.constraints:
                if constraint[0] == "horizontal":
                    tie(constraint[1].startSketchPoint, constraint[1].endSketchPoint, 1)
                elif constraint[0] == "vertical":
                    tie(constraint[1].startSketchPoint, constraint[1].endSketchPoint, 0)
            for (first, second, orientation) in self.dimensions:
                tie(first, second, 0 if orientation == "horizontal" else 1)
        return [point for point in self.points if known[id(point)] == [True, True]]


@pytest.fixture
def sketchUtils(monkeypatch):
    monkeypatch.setattr(sys.modules["adsk.core"], "Point3D", FakePoint3D)
    monkeypatch.setattr(sys.modules["adsk.fusion"], "DimensionOrientations", FakeOrientations, raising=False)
    # type annotations name Fusion classes the stubs don't have, as in test_pred_sketch_arcs
    for module in (sys.modules["adsk.core"], sys.modules["adsk.fusion"]):
        monkeypatch.setattr(module, "__getattr__", lambda name: type(name, (), {}), raising=False)
    return _load("sketchUtils")


@pytest.mark.parametrize("outline", [(-0.025, -0.025, 8.375, 4.175), (-0.025, -0.025, 12.575, 12.575), (0.5, -2.0, 3.0, 1.0)])
def test_the_frame_is_fully_determined(sketchUtils, outline):
    sketch = FakeSketch()
    sketchUtils.addFrame(sketch, *outline)
    assert len(sketch.points) == 4
    assert len(sketch.determinedPoints()) == 4
    # exactly determined: four corners have 8 coordinates, the rectangle ties 4, the dimensions fix the other 4
    assert len(sketch.dimensions) == 4


def test_the_frame_keeps_the_outline_size_clear_on_every_side(sketchUtils):
    sketch = FakeSketch()
    (minX, minY, maxX, maxY) = (-0.025, -0.025, 8.375, 4.175)
    sketchUtils.addFrame(sketch, minX, minY, maxX, maxY)
    margin = max(maxX - minX, maxY - minY)
    xs = [point.geometry.x for point in sketch.points]
    ys = [point.geometry.y for point in sketch.points]
    assert min(xs) == pytest.approx(minX - margin) and max(xs) == pytest.approx(maxX + margin)
    assert min(ys) == pytest.approx(minY - margin) and max(ys) == pytest.approx(maxY + margin)


def test_the_trim_cuts_draw_their_frame_dimensioned():
    with open(os.path.join(PROJECT_ROOT, "lib", "gridfinityUtils", "baseGenerator.py"), encoding="utf-8") as file:
        source = file.read()
    assert "addTwoPointRectangle" not in source
    assert source.count("sketchUtils.addFrame(") == 2
