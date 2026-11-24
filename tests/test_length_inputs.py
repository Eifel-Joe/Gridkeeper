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
