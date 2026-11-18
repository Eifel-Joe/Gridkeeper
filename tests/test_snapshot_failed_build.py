"""
Round 39, p531: a case whose build broke left its document open: buildCase raised before handing the document back,
runCase never recorded it, closeCaseDocument didn't find it (twelve half-built box documents after one run,
the first snapshot run of round 39). buildCase closes its document, unsaved, when the build breaks, and raises on.
"""

import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRY = os.path.join(ROOT, "commands", "commandSnapshotTests", "entry.py")


def _function(name):
    source = open(ENTRY, encoding="utf-8").read()
    return next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)


def test_a_broken_build_closes_its_document_and_raises_on():
    function = _function("buildCase")
    tries = [n for n in ast.walk(function) if isinstance(n, ast.Try)]
    assert tries, "no try around the build"
    handlers = [h for t in tries for h in t.handlers]
    assert any("document.close(False)" in ast.unparse(h) and any(isinstance(n, ast.Raise) for n in ast.walk(h)) for h in handlers)
    # the document is made before the try, the build inside it
    assert "_buildCaseIn(" in ast.unparse(tries[0].body[0])
    assert "buildBodies(" in ast.unparse(_function("_buildCaseIn"))


def test_with_parameters_closes_its_document_too():
    assert "document.close(False)" in ast.unparse(next(t for t in ast.walk(_function("buildWithParameters")) if isinstance(t, ast.Try)).finalbody[0])
