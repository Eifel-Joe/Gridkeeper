"""
Tests for the sketch constraint check of the shape tests: which sketches aren't fully constrained and when that fails a case.
"""

import os
import importlib.util
from dataclasses import dataclass, field


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, *path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PROJECT_ROOT, *path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


constraints = _load("constraints", "commands", "commandSnapshotTests", "constraints.py")


@dataclass
class FakeSketch:
    name: str
    isFullyConstrained: bool
    sketchTexts: list = field(default_factory=list)


def test_lists_the_sketches_not_fully_constrained():
    sketches = [FakeSketch("Label socket sketch", True), FakeSketch("Label text sketch", False)]
    assert constraints.unconstrainedSketches(sketches) == ["Label text sketch"]


def test_fully_constrained_sketches_list_nothing():
    assert constraints.unconstrainedSketches([FakeSketch("Body sketch", True)]) == []


def test_cullenect_cases_fail_on_loose_sketches():
    failure = constraints.constraintFailure("bin", "bin_1x1x3_cullenect", ["x"])
    assert isinstance(failure, str) and "x" in failure


def test_label_cases_fail_on_loose_sketches():
    assert isinstance(constraints.constraintFailure("label", "label_1u_screw_text", ["x"]), str)


def test_other_cases_only_report_loose_sketches():
    assert constraints.constraintFailure("bin", "bin_1x1x3_plain", ["x"]) is None


def test_nothing_loose_never_fails():
    assert constraints.constraintFailure("bin", "bin_1x1x3_cullenect", []) is None


@dataclass
class FakeEntity:
    isFullyConstrained: bool = True
    isFixed: bool = False


@dataclass
class FakeTextSketch:
    name: str
    sketchTexts: list
    sketchCurves: list
    sketchPoints: list
    isFullyConstrained: bool = False


def test_live_text_sketch_with_everything_else_bound_counts_as_constrained():
    sketch = FakeTextSketch("Label text sketch", ["text"], [FakeEntity(False, True)] * 4, [FakeEntity(True), FakeEntity(False, True)])
    assert constraints.unconstrainedSketches([sketch]) == []


def test_live_text_sketch_with_a_loose_point_is_listed():
    sketch = FakeTextSketch("Label text sketch", ["text"], [FakeEntity(False, True)], [FakeEntity(False, False)])
    assert constraints.unconstrainedSketches([sketch]) == ["Label text sketch"]


def test_live_text_sketch_with_a_loose_curve_is_listed():
    sketch = FakeTextSketch("Label text sketch", ["text"], [FakeEntity(False, False)], [])
    assert constraints.unconstrainedSketches([sketch]) == ["Label text sketch"]


def test_loose_sketch_without_text_is_listed_even_with_bound_entities():
    sketch = FakeTextSketch("Label icon sketch", [], [FakeEntity(False, True)], [])
    assert constraints.unconstrainedSketches([sketch]) == ["Label icon sketch"]
