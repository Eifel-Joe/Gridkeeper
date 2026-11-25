"""
Round 59: the menu's create commands show a picture under their description on hover, as Fusion's own commands do;
bin and baseplate have the original's, label insert, box and box label get their own in the same look.
"""

import ast
import os

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMANDS = ["commandCreateBin", "commandCreateBaseplate", "commandCreateLabel", "commandCreateBox", "commandCreateBoxLabel"]


def _start(command):
    tree = ast.parse(open(os.path.join(PROJECT_ROOT, "commands", command, "entry.py"), encoding="utf-8").read())
    return tree, ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "start"))


@pytest.mark.parametrize("command", COMMANDS)
def test_the_command_sets_its_picture_when_it_is_there(command):
    (tree, start) = _start(command)
    assert "TOOL_CLIP_PATH = os.path.join(ICON_FOLDER, 'toolclip.png')" in ast.unparse(tree)
    assert "if os.path.isfile(TOOL_CLIP_PATH):\n                cmd_def.toolClipFilename = TOOL_CLIP_PATH" in start
