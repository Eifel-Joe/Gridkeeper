"""
The catch slides of the storage box on both halves (round 59). Mirrored across the box middle (Pred's #73 Mirror2), the
round ends of the right and front right slides came out each split in two in a document in inches, where the left
ones and every slide built in mm are whole (fusion-auftraege/r59_rollback.log: the split appears in Mirror2, with
Fusion's Identical and Adjust compute alike, r59_boxinch2.log). The right slides are drawn and rounded where they are,
as the right handle holders are (Mirror6), and Mirror2 leaves them out.
"""

import ast
import os

from tests.test_pred_box_mirror import generator

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# a box 5 x 4: outer width and length in mm
WIDTH, LENGTH = 230.0, 188.0


def rectangles():
    return [tuple(round(value, 6) for value in rect) for rect in generator.catchSlideRectangles(WIDTH, LENGTH)]


def test_the_left_slides_are_preds():
    rects = rectangles()
    # front, at the latch edges of the front left latch
    assert (19, 21, 1.75, 5.75) in rects and (41, 43, 1.75, 5.75) in rects
    # left side, both latches
    for (ya, yb) in ((19, 21), (41, 43), (LENGTH - 43, LENGTH - 41), (LENGTH - 21, LENGTH - 19)):
        assert (1.75, 5.75, ya, yb) in rects


def test_the_right_slides_are_the_left_ones_across_the_middle():
    rects = rectangles()
    assert (WIDTH - 21, WIDTH - 19, 1.75, 5.75) in rects and (WIDTH - 43, WIDTH - 41, 1.75, 5.75) in rects
    for (ya, yb) in ((19, 21), (41, 43), (LENGTH - 43, LENGTH - 41), (LENGTH - 21, LENGTH - 19)):
        assert (WIDTH - 5.75, WIDTH - 1.75, ya, yb) in rects
    assert len(rects) == 12 and len(set(rects)) == 12


def test_each_rectangle_runs_from_low_to_high():
    for (xa, xb, ya, yb) in rectangles():
        assert xa < xb and ya < yb


def _function(name, className="_Builder"):
    tree = ast.parse(open(os.path.join(PROJECT_ROOT, "lib", "gridfinityUtils", "predBoxGenerator.py"), encoding="utf-8").read())
    builder = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == className)
    return ast.unparse(next(node for node in builder.body if isinstance(node, ast.FunctionDef) and node.name == name))


def test_the_right_slides_are_rounded_where_they_are():
    source = _function("catches")
    assert "catchSlideRectangles(" in source
    assert "self.fillet('#54 Fillet2', name='Fillet2 right', mirrored=True)" in source


def test_mirror2_leaves_the_slides_out():
    source = _function("lidAndHinge")
    mirror2 = source[source.index("self.mirror([self.frontTabs"):source.index("'#73 Mirror2')")]
    for feature in ("self.slideTop", "self.slide,", "self.slideBottom", "self.slideFillet"):
        assert feature not in mirror2


def test_the_right_fillet_finds_the_left_ones_edges_across_the_middle():
    import sys
    edges = sys.modules[generator.__name__.rsplit(".", 1)[0] + ".predBoxEdges"]
    values = {"outerWidth": 23.0, "outerLength": 18.8, "midX": 11.5, "midY": 9.4, "bodyTop": 5.22, "midZ": 2.47,
              "labelWidth": 7.05, "catchSlideDepth": 4.3}
    left = edges.expectedItems("#54 Fillet2", values)
    right = edges.expectedItems("#54 Fillet2", values, mirrored=True)
    assert len(left) == len(right) > 0
    xs = lambda items: [point[0] for item in items for point in edges.probePoints(item)]
    assert max(xs(left)) < values["midX"] < min(xs(right))
