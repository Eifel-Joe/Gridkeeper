"""
Round 58: after a build or rebuild from a dialog the component that was active before is active again, as
GridfinityGenerator a45c6b4 does for bins and baseplates. Gridkeeper's box, box label and label insert dialogs build the
same way. Checked on the source: each dialog's build and rebuild run inside commonUtils.keepActiveComponent.
"""

import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIALOGS = {
    "commandCreateBin": ("binBuilder.buildBin", "binBuilder.rebuildBin"),
    "commandCreateBaseplate": ("buildBaseplate", "rebuildBaseplate"),
    "commandCreateBox": ("buildBox", "rebuildBox"),
    "commandCreateBoxLabel": ("buildBoxLabel", "rebuildBoxLabel"),
    "commandCreateLabel": ("buildLabel", "rebuildLabel"),
}


def _guarded_calls(path):
    """Names of the calls inside a with commonUtils.keepActiveComponent(...) block, and of all calls"""
    with open(path, encoding="utf-8") as file:
        tree = ast.parse(file.read())
    guarded = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.With) and any(
            isinstance(item.context_expr, ast.Call) and ast.unparse(item.context_expr.func) == "commonUtils.keepActiveComponent"
            for item in node.items
        ):
            guarded |= {ast.unparse(call.func) for call in ast.walk(node) if isinstance(call, ast.Call)}
    called = {ast.unparse(call.func) for call in ast.walk(tree) if isinstance(call, ast.Call)}
    return (guarded, called)


def test_every_dialog_builds_and_rebuilds_keeping_the_active_component():
    for (folder, names) in DIALOGS.items():
        (guarded, called) = _guarded_calls(os.path.join(ROOT, "commands", folder, "entry.py"))
        for name in names:
            assert name in called, f"{folder}: {name} isn't called"
            assert name in guarded, f"{folder}: {name} runs without keepActiveComponent"
