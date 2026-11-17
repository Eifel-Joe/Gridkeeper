"""
buildBox returns the native bodies of box and lid, as binBuilder does (round 27). The bodies moveToComponent gives back
are seen through the Box and Lid occurrences: the snapshot tests found neither among the design's bodies ("loose body
Base, not part of what was built") nor their box tag on them ("Base isn't in the Text component of its part"),
fusion-auftraege r27_snap step 1, 17.11.2026. boxBuilder needs Fusion to load, so the test reads its source.
"""

import ast
import os

SOURCE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "commands", "commandCreateBox", "boxBuilder.py")


def _function(name):
    tree = ast.parse(open(SOURCE, encoding="utf-8").read())
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def test_build_box_returns_the_native_bodies():
    returns = [node for node in ast.walk(_function("_buildBox")) if isinstance(node, ast.Return)]
    assert len(returns) == 1
    value = returns[0].value
    if isinstance(value, ast.BinOp):
        value = value.left
    assert isinstance(value, ast.List) and len(value.elts) == 2
    for element in value.elts:
        assert isinstance(element, ast.Call) and ast.unparse(element.func) == "rebuildUtils.nativeBody", ast.unparse(element)


def test_build_box_puts_joint_origins_at_the_small_parts_seats():
    """Round 28, plan task 5: the seats of latches, handle and pins become joint origins in the box component"""
    source = ast.unparse(_function("_buildBox"))
    assert "createPointJointOrigins(predBoxSeats.seatJointOriginPoints(dims), boxComponent" in source


def test_build_box_inserts_the_small_parts_and_returns_their_bodies_after_box_and_lid():
    """Round 28, plan task 6 and decision 5: the parts come into the set, buildBox gives box and lid first"""
    source = ast.unparse(_function("_buildBox"))
    assert "predBoxInsert.insertParts(des, setOccurrence, boxOccurrence, dims, name, assembly.inContext)" in source
    returns = [node for node in ast.walk(_function("_buildBox")) if isinstance(node, ast.Return)]
    assert len(returns) == 1
    assert ast.unparse(returns[0].value) == "[rebuildUtils.nativeBody(base), rebuildUtils.nativeBody(lid)] + partBodies"


def test_a_rebuild_pairs_box_and_lid_only():
    """rebuildUtils.bodyMap pairs old and new bodies only when there are as many; the old set's tagged bodies are box
    and lid, the small parts (round 28) aren't tagged, so the rebuild's build gives the tagged bodies only"""
    rebuild = _function("rebuildBox")
    build = next(node for node in ast.walk(rebuild) if isinstance(node, ast.FunctionDef) and node.name == "build")
    assert "tagUtils.readBodyTag" in ast.unparse(build)
