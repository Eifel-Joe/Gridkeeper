"""
Tests for the sketch constraint check of the shape tests: which sketches aren't fully constrained and when that fails a case.
"""

import os
import importlib.util
from dataclasses import dataclass


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
