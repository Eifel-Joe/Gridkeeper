"""
The box dialog's hinge choice (round 28, Jörg 17.11.2026: "alle drei zum auswählen ist besser"): a dropdown with the
three variants of predBoxParts.HINGES, read into and back from the state, and a config's unknown hinge becomes the
default. entry.py needs Fusion to load, so its source is read.
"""

import ast
import os

ENTRY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "commands", "commandCreateBox", "entry.py")


def _function(name):
    tree = ast.parse(open(ENTRY, encoding="utf-8").read())
    return ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name))


def test_the_dialog_lists_every_hinge_variant():
    source = _function("command_created")
    assert "HINGE_DROPDOWN" in source and "predBoxParts.HINGES" in source


def test_the_hinge_goes_into_the_state_and_back():
    assert "hinge=uiState.getState(HINGE_DROPDOWN)" in _function("getInputsState")
    assert "uiState.setValue(HINGE_DROPDOWN, state.hinge)" in _function("applyInputsState")
    assert "uiState.initValue(HINGE_DROPDOWN, DEFAULT_STATE.hinge" in _function("initUiState")


def test_a_config_with_an_unknown_hinge_gets_the_default():
    source = _function("readConfig")
    assert "'hinge': configJson.Choice(list(predBoxParts.HINGES), predBoxParts.DEFAULT_HINGE)" in source


def test_the_dialog_has_no_joint_origins_checkbox_any_more():
    """Round 31: the floor cells always get joint origins, the field stays in the state for older configs"""
    assert "JOINT_ORIGINS_INPUT" not in _function("command_created")
    assert "hasJointOrigins=True" in _function("getInputsState")
    assert "JOINT_ORIGINS_INPUT" not in _function("applyInputsState")


# Round 30, p311 (Jörg 18.11.2026: "Lid top: Grid / Closed", "Standard bleibt Raster")

def test_the_dialog_has_a_lid_group_with_the_lid_tops():
    source = _function("command_created")
    assert "LID_TOP_DROPDOWN" in source and "predBoxConfig.LID_TOPS" in source
    assert "addGroup(inputs, LID_GROUP, 'Lid')" in source
    # between the magnet holes and the small parts (the joint origins group went in round 31)
    assert source.index("MAGNET_GROUP") < source.index("LID_GROUP") < source.index("PARTS_GROUP")
    assert "LID_GROUP" in _function("initUiState")


def test_the_lid_top_goes_into_the_state_and_back():
    assert "lidTop=uiState.getState(LID_TOP_DROPDOWN)" in _function("getInputsState")
    assert "uiState.setValue(LID_TOP_DROPDOWN, state.lidTop)" in _function("applyInputsState")
    assert "uiState.initValue(LID_TOP_DROPDOWN, DEFAULT_STATE.lidTop" in _function("initUiState")


def test_a_config_with_an_unknown_lid_top_gets_the_default():
    source = _function("readConfig")
    assert "'lidTop': configJson.Choice(list(predBoxConfig.LID_TOPS), predBoxConfig.DEFAULT_LID_TOP)" in source
