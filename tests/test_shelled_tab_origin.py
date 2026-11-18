"""
The label tab of a shelled bin always sits on the back wall (round 34, p281). A shelled bin builds no scoop
(binBodyInput.hasScoop needs a hollow bin), so a front placement at the light lip's inner edge could never run and
would have been wrong under a full lip. binBuilder needs Fusion to load, so the tests read its source.
"""

import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_BUILDER = os.path.join(ROOT, "commands", "commandCreateBin", "binBuilder.py")


def _tree():
    return ast.parse(open(BIN_BUILDER, encoding="utf-8").read())


def _function(name):
    return next(node for node in _tree().body if isinstance(node, ast.FunctionDef) and node.name == name)


def test_shelled_tab_origin_does_not_depend_on_scoop_or_lip():
    arguments = [argument.arg for argument in _function("shelledTabOriginY").args.args]
    assert arguments == ["baseLength", "binLength", "xyClearance"]
    assert "BIN_LIP_WALL_THICKNESS" not in ast.unparse(_function("shelledTabOriginY"))


def test_shelled_tab_block_has_no_scoop_branch():
    source = ast.unparse(_function("_buildBin"))
    block = source.split("compartmentTabInput = BinBodyTabGeneratorInput()", 1)[1].split("createGridfinityBinBodyTab", 1)[0]
    assert "hasScoop" not in block
    assert "BIN_LIP_WALL_THICKNESS" not in block
    assert "shelledTabOriginY(" in block
