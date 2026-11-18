"""
The bin dialog's scoop inputs (round 48): one checkbox per wall, the back one locked while the label tab is on.
entry.py needs Fusion to load, so its source is read.
"""

import ast
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRY = os.path.join(PROJECT_ROOT, "commands", "commandCreateBin", "entry.py")
STATE = os.path.join(PROJECT_ROOT, "commands", "commandCreateBin", "inputState.py")


def _source(path):
    with open(path, encoding="utf-8") as file:
        return file.read()


def _function(name):
    tree = ast.parse(_source(ENTRY))
    return ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name))


def test_every_scoop_wall_has_its_input():
    source = _source(ENTRY)
    for (field, inputId) in [
        ("hasScoop", "BIN_HAS_SCOOP_INPUT_ID"),
        ("hasScoopBack", "BIN_HAS_SCOOP_BACK_INPUT_ID"),
        ("hasScoopLeft", "BIN_HAS_SCOOP_LEFT_INPUT_ID"),
        ("hasScoopRight", "BIN_HAS_SCOOP_RIGHT_INPUT_ID"),
    ]:
        assert f"'{field}': {inputId}," in source
        assert f"commandUIState.initValue({inputId}, DEFAULT_STATE.{field}," in source
        assert f"({inputId}, '" in source  # its row in the scoop group, see the loop adding the checkboxes


def test_the_front_input_keeps_its_id():
    # saved dialog states and the config field stay the same, the front scoop is the scoop of older bins
    assert "BIN_HAS_SCOOP_INPUT_ID = 'bin_has_scoop'" in _source(ENTRY)


def test_every_state_field_comes_from_the_dialog():
    fields = re.findall(r"^    (\w+)\s*:", _source(STATE), re.M)
    getter = _function("getInputsState")
    source = _source(ENTRY)
    mapped = set(re.findall(r"^    '(\w+)': BIN_\w+,$", source, re.M))
    missing = [field for field in fields if field not in mapped and f"{field}=" not in getter]
    assert missing == []


def test_back_scoop_is_locked_by_the_label_tab():
    refresh = _function("onChangeValidate")
    assert "getInput(BIN_HAS_SCOOP_BACK_INPUT_ID).isEnabled" in refresh


def test_radius_follows_any_scoop_wall():
    source = _source(ENTRY)
    assert "commandUIState.getInput(BIN_SCOOP_MAX_RADIUS_INPUT_ID).isEnabled = anyScoop and not shaped" in source
