"""
Tests for tools/fontStroke.py: the stroke width of letter outlines, measured across the stroke from each point of the
outline (round 17, the least text height a 0.4 mm nozzle prints).
"""

import math
import os
import importlib.util

import pytest

_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools', 'fontStroke.py')
_spec = importlib.util.spec_from_file_location('fontStroke', _PATH)
fontStroke = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fontStroke)


def _polygon(points):
    return [(*a, *b) for (a, b) in zip(points, points[1:] + points[:1])]


def _circle(radius, count):
    return [(radius * math.cos(2 * math.pi * i / count), radius * math.sin(2 * math.pi * i / count)) for i in range(count)]


def test_rectangle_stroke_is_its_width():
    segments = _polygon([(0, 0), (10, 0), (10, 0.8), (0, 0.8)])
    assert fontStroke.thinnestStroke(segments, 0.05) == pytest.approx(0.8, abs=1e-6)


def test_ring_stroke_is_ring_width():
    segments = _polygon(_circle(5, 360)) + _polygon(_circle(4.6, 360))
    assert fontStroke.thinnestStroke(segments, 0.05) == pytest.approx(0.4, abs=0.01)


def test_thinnest_of_two_strokes():
    # an L of a 1.0 wide bar and a 0.5 wide bar
    segments = _polygon([(0, 0), (6, 0), (6, 0.5), (1, 0.5), (1, 6), (0, 6)])
    assert fontStroke.thinnestStroke(segments, 0.05) == pytest.approx(0.5, abs=1e-6)


def test_points_near_sharp_corners_are_skipped():
    # at the tip of a wedge the stroke runs out to nothing, that is the shape of the corner and not a stroke
    segments = _polygon([(0, 0), (2, 0), (1, 5)])
    assert min(fontStroke.strokeWidths(segments, 0.02, cornerSkip=0)) < 0.05
    assert min(fontStroke.strokeWidths(segments, 0.02, cornerSkip=0.5)) > 0.15
