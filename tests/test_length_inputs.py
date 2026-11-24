"""
Round 58: lengths Fusion keeps as parameters of a feature go to it in mm, see dim.lengthInput. Given a real, Fusion
keeps a fillet or chamfer size, a plane offset or a joint origin offset in the document's units to 6 or 7 decimals; in a
document in inches that is up to a nanometre off and faces that should meet are split (GridfinityGenerator 9fff015,
issue #217). Gridkeeper's own generators had the same: checked on the source of every generator module.
"""

import ast
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATORS = sorted(glob.glob(os.path.join(ROOT, "lib", "gridfinityUtils", "*.py")))
# the call and the index of its length argument
LENGTH_ARGUMENTS = {
    "setByOffset": 1,
    "addConstantRadiusEdgeSet": 1,
    "addEqualDistanceChamferEdgeSet": 1,
    "setByDistance": 0,
}
JOINT_ORIGIN_OFFSETS = {"offsetX", "offsetY", "offsetZ"}
# what gives Fusion a real: dim.valueInput and the API itself (predHandle._value already gives mm)
REAL_INPUTS = {"valueInput", "adsk.core.ValueInput.createByReal"}


def _gives_a_real(node) -> bool:
    return isinstance(node, ast.Call) and ast.unparse(node.func) in REAL_INPUTS


def _sites(path):
    with open(path, encoding="utf-8") as file:
        tree = ast.parse(file.read())
    sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in LENGTH_ARGUMENTS:
            index = LENGTH_ARGUMENTS[node.func.attr]
            if len(node.args) > index and _gives_a_real(node.args[index]):
                sites.append(f"{os.path.basename(path)}:{node.lineno} {node.func.attr}")
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Attribute) and target.attr in JOINT_ORIGIN_OFFSETS for target in node.targets
        ) and _gives_a_real(node.value):
            sites.append(f"{os.path.basename(path)}:{node.lineno} joint origin offset")
    return sites


def test_feature_lengths_go_to_fusion_in_mm():
    sites = [site for path in GENERATORS for site in _sites(path)]
    assert sites == []


def test_every_text_gets_its_height_in_mm():
    # Fusion keeps a text height given as a number to 3 decimals in the document's units, a hundredth of a mm off in
    # inches (upstream c5a4bfe/9fff015): each function adding a sketch text sets the height to the micron in mm
    found = []
    for path in GENERATORS:
        with open(path, encoding="utf-8") as file:
            tree = ast.parse(file.read())
        for function in [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]:
            calls = {ast.unparse(node.func) for node in ast.walk(function) if isinstance(node, ast.Call)}
            if "sketch.sketchTexts.add" in calls:
                found.append(function.name)
                assert "holdTextHeight" in {name.split(".")[-1] for name in calls}, f"{os.path.basename(path)} {function.name}"
    assert len(found) >= 3


def test_a_text_height_is_kept_to_the_micron_in_mm():
    import importlib.util
    import sys
    import types
    dim = types.SimpleNamespace(lengthExpression=lambda value: f"{value * 10:g} mm")
    namespace = {"lengthExpression": dim.lengthExpression}
    path = os.path.join(ROOT, "lib", "gridfinityUtils", "labelGenerator.py")
    tree = ast.parse(open(path, encoding="utf-8").read())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "holdTextHeight")
    future = ast.parse("from __future__ import annotations").body
    exec(compile(ast.Module(body=future + [function], type_ignores=[]), path, "exec"), namespace)
    text = types.SimpleNamespace(heightParameter=types.SimpleNamespace(expression=None))
    namespace["holdTextHeight"](text, 0.3214567)
    assert text.heightParameter.expression == "3.215 mm"
