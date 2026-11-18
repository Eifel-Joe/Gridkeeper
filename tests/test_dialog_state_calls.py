"""
The dialogs' getInputsState must not reach itself through the module's own helpers. Round 10 had the bin dialog's
label color ask isShaped(), which asks getInputsState() again: endless recursion, the bin dialog never opened and its
label inputs stayed greyed out (15.11.2026). entry.py needs Fusion to load, so the calls are read from the source.
"""

import ast
import os

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRIES = [
    os.path.join("commands", "commandCreateBin", "entry.py"),
    os.path.join("commands", "commandCreateLabel", "entry.py"),
    os.path.join("commands", "commandCreateBaseplate", "entry.py"),
]


def _callGraph(path: str) -> dict[str, set[str]]:
    """Module-level function -> names of module-level functions it calls by plain name"""
    with open(os.path.join(PROJECT_ROOT, path), encoding="utf-8") as file:
        tree = ast.parse(file.read())
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    return {
        name: {call.func.id for call in ast.walk(node) if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id in functions}
        for (name, node) in functions.items()
    }


def _reaches(graph: dict[str, set[str]], start: str, target: str) -> list[str] | None:
    """A call path from start's callees to target, None without one"""
    stack = [(callee, [start, callee]) for callee in graph.get(start, ())]
    seen = set()
    while stack:
        (name, path) = stack.pop()
        if name == target:
            return path
        if name in seen:
            continue
        seen.add(name)
        stack.extend((callee, path + [callee]) for callee in graph.get(name, ()))
    return None


@pytest.mark.parametrize("path", ENTRIES)
def test_get_inputs_state_does_not_call_itself(path):
    graph = _callGraph(path)
    assert "getInputsState" in graph
    assert _reaches(graph, "getInputsState", "getInputsState") is None
