"""
Tests for the settings of the storage box after Pred (round 27, p260): the smallest box, the magnet holes the box can
take (Nutzer 16.11.2026: "Box nur 6×2", custom up to 2.6 mm, diameter like the baseplate), the name, the joint origins in
the floor and the config the dialog saves.
"""

import os
import sys
import importlib.util

import pytest

from tests.test_joint_origin_layout import _load

boxConfig = _load("predBoxConfig")
configJson = importlib.import_module("lib.configJson")
defaultSettings = importlib.import_module("lib.defaultSettings")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _inputState():
    spec = importlib.util.spec_from_file_location("boxInputState", os.path.join(ROOT, "commands", "commandCreateBox", "inputState.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.InputState


InputState = _inputState()


def state(**changes):
    defaults = configJson.stateFromJson(configJson.GENERATOR_BOX, InputState, defaultSettings.SETTINGS["box"])
    for name, value in changes.items():
        setattr(defaults, name, value)
    return defaults


def test_defaults_are_preds_box():
    s = state()
    assert (s.gridX, s.gridY, s.heightU) == (5, 4, 6)
    assert s.hasMagnets is False and s.hasJointOrigins is True
    assert (round(s.magnetDepth * 10, 6), round(s.magnetDiameter * 10, 6)) == (2.4, 6.5)
    assert boxConfig.boxProblem(s) is None


def test_config_round_trip_in_mm():
    s = state(magnetDepth=0.26, magnetDiameter=0.8)
    saved = configJson.stateToJson(configJson.GENERATOR_BOX, s)
    assert (saved["magnetDepth"], saved["magnetDiameter"]) == (2.6, 8.0)
    assert configJson.stateFromJson(configJson.GENERATOR_BOX, InputState, saved) == s


@pytest.mark.parametrize("changes, message", [
    ({"gridX": 3}, "Width must be at least 4 units"),
    ({"gridY": 2}, "Length must be at least 3 units"),
    # Nutzer 16.11.2026: "Mindesthöhe 6. vorerst." (height 5 is p264)
    ({"heightU": 5}, "Height must be at least 6 units"),
    ({"hasMagnets": True, "magnetDepth": 0.27}, "Magnet holes deeper than 2.6 mm would break through the floor"),
    ({"hasMagnets": True, "magnetDepth": 0}, "The magnet holes need a depth"),
    ({"hasMagnets": True, "magnetDiameter": 0.29}, "The magnet diameter is 3 to 8.5 mm"),
    ({"hasMagnets": True, "magnetDiameter": 0.86}, "The magnet diameter is 3 to 8.5 mm"),
])
def test_problems(changes, message):
    assert boxConfig.boxProblem(state(**changes)) == message


def test_magnets_off_ignore_their_size():
    assert boxConfig.boxProblem(state(hasMagnets=False, magnetDepth=0.34)) is None


def test_smallest_box_and_deepest_magnets_build():
    assert boxConfig.boxProblem(state(gridX=4, gridY=3, heightU=6, hasMagnets=True, magnetDepth=0.26, magnetDiameter=0.85)) is None


def test_name():
    assert boxConfig.boxName(state(gridX=7, gridY=5, heightU=10)) == "Box 7×5×10"


def test_cell_joint_origins_sit_in_the_sockets():
    centers = boxConfig.cellCenters(2, 3)
    assert [(c, r) for (c, r, _, _) in centers] == [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)]
    # 10 mm rim, cell centre 21 mm in, 42 mm apart
    assert [(round(x * 10, 6), round(y * 10, 6)) for (_, _, x, y) in centers[:2]] == [(31, 31), (73, 31)]
    # like the baseplate's sockets: the socket top (4.65 mm over the floor plane) less a bin base
    assert round(boxConfig.CELL_JOINT_Z * 10, 6) == round(4.65 - 5.0, 6)


def test_parameter_fields():
    assert boxConfig.PARAMETERS == ["baseWidth", "baseLength", "heightU"]
    assert boxConfig.PARAMETER_FIELDS == {"Width (units)": "gridX", "Length (units)": "gridY", "Height (units)": "heightU"}


def test_floor_pads_keep_preds_size_without_magnets():
    """Review R27: the pads around the magnet holes grow with the diameter; without magnets a diameter left typed in
    (0 or 15 mm) must neither break the build nor change Pred's 8 mm pads"""
    for diameter in (0.0, 1.5, 0.8):
        options = boxConfig.boxOptions(state(hasMagnets=False, magnetDiameter=diameter))
        assert (options.hasMagnets, round(options.magnetDiameter * 10, 6)) == (False, 6.5)
    options = boxConfig.boxOptions(state(hasMagnets=True, magnetDepth=0.26, magnetDiameter=0.8))
    assert (options.hasMagnets, round(options.magnetDepth * 10, 6), round(options.magnetDiameter * 10, 6)) == (True, 2.6, 8.0)


@pytest.mark.parametrize("value, limits", [(6, (6, 30)), (5, (5, 30)), (35, (6, 35)), (0, (1, 30))])
def test_spinner_takes_a_parameter_beyond_its_limits(value, limits):
    """Review R27: a rebuild opens the dialog with the size parameters, which may have been set to 5 or 35 in Change
    Parameters; the spinner widens to show it, boxProblem names what's wrong instead of the dialog not opening"""
    assert boxConfig.spinnerLimits(6, 30, value) == limits
