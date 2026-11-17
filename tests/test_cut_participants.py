"""
Every cut of the storage box generators names the bodies it cuts (p400). Fusion's cut without participantBodies cuts
every body in its way, also bodies of other components: a bin standing where a hinge was being drawn got the hinge's
clearance rings and screw hole cut into it (Jörg's test for 1.1.0, fusion-auftraege/p400_cut_participants.log).

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


def _operations(call: ast.Call):
    """The arguments that can be the operation: positional ones and an 'operation' keyword"""
    return list(call.args) + [k.value for k in call.keywords if k.arg == 'operation']


def _ownNodes(function):
    """The nodes of the function without those of functions nested in it (each is checked on its own)"""
    stack = list(function.body)
    while stack:
        node = stack.pop()
        yield node
        stack.extend(child for child in ast.iter_child_nodes(node)
                     if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)))


@pytest.mark.parametrize('module', sorted(HELPERS))
def test_cuts_through_helpers_name_their_bodies(module):
    missing = []
    for node in ast.walk(_tree(module)):
        if not isinstance(node, ast.Call):
            continue
        for name, index in HELPERS[module]:
            operation = node.args[index] if len(node.args) > index else next(
                (k.value for k in node.keywords if k.arg == 'operation'), None)
            if _calledName(node) == name and operation is not None and _isCut(operation):
                given = [k.value for k in node.keywords if k.arg in ('bodies', 'body')]
                if not given or (isinstance(given[0], ast.Constant) and given[0].value is None):
                    missing.append(f'{module}.py:{node.lineno}')
    assert missing == []


@pytest.mark.parametrize('module', MODULES)
def test_feature_inputs_for_cuts_set_participants(module):
    """Each extrude, sweep or revolve input for a cut (or for an operation passed in) gets participantBodies set on that
    very input, in the function that makes it (nested functions are checked on their own); inputs for a new body need
    none. A helper may set them only when it is given bodies: its cut calls are held to pass them by the test above"""
    missing = []
    for function in ast.walk(_tree(module)):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        nodes = list(_ownNodes(function))
        stored = {node.value.id for node in nodes if isinstance(node, ast.Attribute) and node.attr == 'participantBodies'
                  and isinstance(node.ctx, ast.Store) and isinstance(node.value, ast.Name)}
        for node in nodes:
            if not (isinstance(node, ast.Call) and _calledName(node) == 'createInput' and any(
                    _isCut(arg) or (isinstance(arg, ast.Name) and arg.id == 'operation') for arg in _operations(node))):
                continue
            targets = [n.targets[0].id for n in nodes if isinstance(n, ast.Assign) and n.value is node
                       and isinstance(n.targets[0], ast.Name)]
            if not targets or targets[0] not in stored:
                missing.append(f'{module}.{function.name}:{node.lineno}')
    assert missing == []
