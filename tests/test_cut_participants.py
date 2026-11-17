"""
Every cut of the storage box generators names the bodies it cuts (p400). Fusion's cut without participantBodies cuts
every body in its way, also bodies of other components: a bin standing where a hinge was being drawn got the hinge's
clearance rings and screw hole cut into it (the user's test for 1.1.0, fusion-auftraege/p400_cut_participants.log).

Checked in the source (ast), as the generators need Fusion:
- every call of a module's extrude helper with a cut operation passes the bodies to cut;
- every function that makes a feature input for a cut, or for an operation passed in, sets participantBodies.
predLatch's helper takes its body from the builder (set by the first, new-body extrude), predBoxGenerator.along
defaults to the box body; both are covered by the second rule.
"""

import ast
import os

import pytest

LIB = os.path.join(os.path.dirname(__file__), '..', 'lib', 'gridfinityUtils')
MODULES = ['predBoxGenerator', 'predHandle', 'predHandlePin', 'predHinge', 'predLatch']
# the module's extrude helpers: (called name, index of the operation among the positional arguments)
HELPERS = {
    'predBoxGenerator': [('extrude', 1)],
    'predHandlePin': [('_extrude', 2)],
    'predHinge': [('_extrude', 2)],
}
CUTTING = {'CutFeatureOperation', 'IntersectFeatureOperation'}
# local names the modules give the cut operation
CUT_NAMES = {'cut'}


def _tree(module):
    with open(os.path.join(LIB, module + '.py'), encoding='utf-8') as f:
        return ast.parse(f.read())


def _calledName(call: ast.Call):
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _isCut(node) -> bool:
    return ((isinstance(node, ast.Attribute) and node.attr in CUTTING)
            or (isinstance(node, ast.Name) and node.id in CUT_NAMES))


@pytest.mark.parametrize('module', sorted(HELPERS))
def test_cuts_through_helpers_name_their_bodies(module):
    missing = []
    for node in ast.walk(_tree(module)):
        if not isinstance(node, ast.Call):
            continue
        for name, index in HELPERS[module]:
            if _calledName(node) == name and len(node.args) > index and _isCut(node.args[index]):
                if not any(k.arg in ('bodies', 'body') for k in node.keywords):
                    missing.append(f'{module}.py:{node.lineno}')
    assert missing == []


@pytest.mark.parametrize('module', MODULES)
def test_feature_inputs_for_cuts_set_participants(module):
    """A function making an extrude, sweep or revolve input for a cut (or for an operation it is given) sets
    participantBodies; inputs for a new body need none"""
    missing = []
    for function in ast.walk(_tree(module)):
        if not isinstance(function, ast.FunctionDef):
            continue
        calls = [node for node in ast.walk(function) if isinstance(node, ast.Call) and _calledName(node) == 'createInput'
                 and any(_isCut(arg) or (isinstance(arg, ast.Name) and arg.id == 'operation') for arg in node.args)]
        sets = any(isinstance(node, ast.Attribute) and node.attr == 'participantBodies' and isinstance(node.ctx, ast.Store)
                   for node in ast.walk(function))
        if calls and not sets:
            missing.append(f'{module}.{function.name}')
    assert missing == []
