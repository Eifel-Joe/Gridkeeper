"""
Round 39 (p480): WorldSketch fixes the points whose two sketch coordinates are plain numbers instead of binding them
with two dimensions (sketchChain fixable). A point that hangs on a box parameter (width, length, height, grid) keeps its
dimensions with their expressions, so a parameter change still moves it.
"""

import ast
import pathlib

from tests.test_pred_box import _dims
from tests.test_pred_sketch_arcs import predSketch
from tests.test_joint_origin_layout import _load

predBox = _load("predBox")
Dim = predBox.Dim
SOURCE = (pathlib.Path(__file__).parent.parent / "lib" / "gridfinityUtils" / "predSketch.py").read_text(encoding="utf-8")

XY = ((0, 1), (1, 1))   # a sketch on XY: sketch x is world x, sketch y world y
XZ = ((0, 1), (2, -1))  # a sketch on XZ: sketch y is world z


def test_plain_numbers_and_value_dims_are_fixable():
    points = [(1.0, 2.0, 0.0), (Dim.length(1.5), Dim.length(2.5), Dim.length(0.3))]
    assert predSketch.fixablePoints(points, *XY) == {0, 1}


def test_an_expression_on_a_sketch_axis_is_not_fixable():
    width = Dim(5, "gfBox1_baseWidth", predBox.DimKind.EXPRESSION)
    points = [(width * Dim.length(4.2), 1.0, 0.0), (1.0, width * Dim.length(4.2), 0.0)]
    assert predSketch.fixablePoints(points, *XY) == set()


def test_an_expression_on_the_normal_axis_is_left_aside():
    height = Dim(6, "gfBox1_heightU", predBox.DimKind.EXPRESSION)
    points = [(1.0, 2.0, height * Dim.length(0.7)), (1.0, 2.0, height * Dim.length(0.7))]
    assert predSketch.fixablePoints(points, *XY) == {0, 1}
    # on XZ the height is a sketch coordinate
    assert predSketch.fixablePoints(points, *XZ) == set()


def test_every_size_measure_of_the_box_keeps_its_dimensions():
    """Width, length, height and grid count reach the sketch only through expressions: no point on them is fixed"""
    dims = _dims(5, 4, 6)
    sizeMeasures = ["outerWidth", "outerLength", "bodyTop", "lidCut", "midX", "midY", "midZ", "innerCutDepth",
                    "labelWidth", "catchSlideDepth", "holderBottom"]
    for name in sizeMeasures:
        measure = getattr(dims, name)
        assert measure.isExpression, name
        # also combined with fixed offsets, the way the generator places features (predBoxGenerator.lab/mid)
        shifted = measure + Dim.length(0.5)
        points = [(measure, 1.0, 1.0), (1.0, measure, 1.0), (shifted, Dim.length(0.2), 1.0)]
        assert predSketch.fixablePoints(points, *XY) == set(), name
    # the box's fixed measures are plain numbers, a point on them may be fixed
    assert predSketch.fixablePoints([(dims.bottom, dims.innerCutStart, dims.bodyTop)], *XZ) == set()
    assert predSketch.fixablePoints([(dims.bottom, dims.innerCutStart, dims.bodyTop)], *XY) == {0}


def _function(cls, name):
    tree = ast.parse(SOURCE)
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
    return ast.get_source_segment(SOURCE, next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == name))


def test_the_chain_gets_the_fixable_points():
    chain = _function("WorldSketch", "_chain")
    assert "fixablePoints(self.worldPoints, self.xAxis, self.yAxis)" in chain
    assert "sketchChain.chain(" in chain and "fixable" in chain


def test_a_fixed_point_is_fixed_in_fusion():
    apply = _function("WorldSketch", "_apply")
    assert "kind == 'fixed'" in apply
    assert ".isFixed = True" in apply
