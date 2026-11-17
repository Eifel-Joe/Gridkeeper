"""
WorldSketch draws every arc counterclockwise (round 27). Fusion's addByCenterStartSweep with a negative sweep gave an
arc whose start and end were swapped against the points passed (fusion-auftraege/r27_diag3.log, LabelRail right: start
at the curve's end point, end at its start), the end tied to the wrong point then over-constrained the sketch
(VCS_SKETCH_OVER_CONSTRAINTS). binBodyGenerator's rounded corners draw counterclockwise for the same reason.
"""

import math
import sys

import pytest

from tests.test_joint_origin_layout import _load


def _loadSketch():
    modules = [sys.modules["adsk.core"], sys.modules["adsk.fusion"]]
    for module in modules:
        module.__getattr__ = lambda name: type(name, (), {})
    try:
        return _load("predSketch")
    finally:
        for module in modules:
            del module.__getattr__


predSketch = _loadSketch()


def test_a_counterclockwise_arc_is_drawn_from_its_start():
    # the left label rail's lower arc (r27_diag3.log): centre (84.75, -15.95), from (84.75, -10.95) to (79.75, -15.95)
    first, second, sweep = predSketch.arcDrawing((84.75, -15.95), (84.75, -10.95), (79.75, -15.95))
    assert (first, second) == ("start", "end")
    assert sweep == pytest.approx(math.pi / 2)


def test_a_clockwise_arc_is_drawn_from_its_end():
    # the same arc on the right half: centre (145.25, -15.95), from (145.25, -10.95) to (150.25, -15.95)
    first, second, sweep = predSketch.arcDrawing((145.25, -15.95), (145.25, -10.95), (150.25, -15.95))
    assert (first, second) == ("end", "start")
    assert sweep == pytest.approx(math.pi / 2)


@pytest.mark.parametrize("start, end", [((1, 0), (0, 1)), ((0, 1), (1, 0)), ((-1, 0), (0, -1)), ((0, -1), (-1, 0)),
                                        ((1, 0), (-1, 0.001)), ((-1, 0.001), (1, 0))])
def test_the_shorter_arc_always_with_a_positive_sweep(start, end):
    first, second, sweep = predSketch.arcDrawing((0, 0), start, end)
    points = {"start": start, "end": end}
    a0 = math.atan2(points[first][1], points[first][0])
    a1 = math.atan2(points[second][1], points[second][0])
    assert 0 < sweep <= math.pi + 1e-9
    assert math.cos(a0 + sweep) == pytest.approx(math.cos(a1)) and math.sin(a0 + sweep) == pytest.approx(math.sin(a1))
