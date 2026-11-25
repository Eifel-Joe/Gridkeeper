"""
Tests for the names after a rebuild: the new component is made while the old one still has the name, so Fusion counts
it up ("Gridfinity bin 1x1x3 (1)"), once the old one is gone it gets the old name back. A name the user gave the
component, timeline group or body stays, a generated one follows the new settings.
"""

import ast
import os
import re
import types

REBUILD_UTILS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "rebuildUtils.py")
NAME_FUNCTIONS = ("withoutCounter", "isGeneratedName", "keptName", "keepName")


def _load_rebuild_utils():
    # the name functions alone, loaded from rebuildUtils' source as in test_rebuild_delete: the module imports most of
    # the generator, these only need re and a log
    logged = []
    commonUtils = types.SimpleNamespace(fileLog=logged.append, debugLog=logged.append)
    namespace = {"re": re, "commonUtils": commonUtils, "LOG_PREFIX": "Gridfinity rebuild"}
    source = open(REBUILD_UTILS, encoding="utf-8").read()
    functions = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name in NAME_FUNCTIONS]
    # annotations left unevaluated: the stand-ins have no Fusion types
    future = ast.parse("from __future__ import annotations").body
    exec(compile(ast.Module(body=future + functions, type_ignores=[]), REBUILD_UTILS, "exec"), namespace)
    return (types.SimpleNamespace(**{name: namespace[name] for name in NAME_FUNCTIONS}), logged)


(rebuildUtils, logged) = _load_rebuild_utils()


BIN = "Gridfinity bin "


def test_counter_dropped_once_the_old_component_is_gone():
    assert rebuildUtils.keptName("Gridfinity bin 1x1x3 (1)", "Gridfinity bin 1x1x3", "Gridfinity bin 1x1x3", BIN) == "Gridfinity bin 1x1x3"


def test_counted_old_name_kept():
    # the second of two bins of a size was counted already, its rebuild got the next count
    assert rebuildUtils.keptName("Gridfinity bin 1x1x3 (2)", "Gridfinity bin 1x1x3 (1)", "Gridfinity bin 1x1x3", BIN) == "Gridfinity bin 1x1x3 (1)"


def test_new_size_keeps_its_name():
    assert rebuildUtils.keptName("Gridfinity bin 2x1x3", "Gridfinity bin 1x1x3", "Gridfinity bin 1x1x3", BIN) is None


def test_name_not_counted_stays():
    assert rebuildUtils.keptName("Gridfinity bin 1x1x3", "Gridfinity bin 1x1x3", "Gridfinity bin 1x1x3", BIN) is None


def test_users_name_kept():
    assert rebuildUtils.keptName("Gridfinity bin 2x1x3", "Cutlery bin", "Gridfinity bin 1x1x3", BIN) == "Cutlery bin"


def test_users_name_like_a_generated_one_kept():
    # the user named a 1x1x3 bin after another size, it isn't the name the generator gave
    assert rebuildUtils.keptName("Gridfinity bin 1x1x3", "Gridfinity bin 2x2x6", "Gridfinity bin 1x1x3", BIN) == "Gridfinity bin 2x2x6"


def test_users_name_ending_in_a_count_kept():
    assert rebuildUtils.keptName("Gridfinity bin 1x1x3", "Drawer (2)", "Gridfinity bin 1x1x3", BIN) == "Drawer (2)"


def test_body_named_by_fusion_follows_the_new_one():
    # the feet of a bin without a body keep the names Fusion gave them
    assert rebuildUtils.keptName("Body7", "Body3", "Body3", BIN) is None


def test_tag_without_a_name_goes_by_the_prefix():
    assert rebuildUtils.keptName("Gridfinity bin 2x1x3", "Gridfinity bin 1x1x3", None, BIN) is None
    assert rebuildUtils.keptName("Gridfinity bin 2x1x3", "Cutlery bin", None, BIN) == "Cutlery bin"


class FakeItem:
    def __init__(self, name):
        self.name = name


def test_new_item_renamed():
    item = FakeItem("Gridfinity baseplate 3x2 (1)")
    rebuildUtils.keepName(item, "Gridfinity baseplate 3x2", "Gridfinity baseplate 3x2", "Gridfinity baseplate ")
    assert item.name == "Gridfinity baseplate 3x2"


def test_refused_name_logged_and_rebuild_goes_on():
    class Refusing(FakeItem):
        def __setattr__(self, key, value):
            if key == "name" and hasattr(self, "name"):
                raise RuntimeError("name in use")
            super().__setattr__(key, value)
    item = Refusing("Gridfinity bin 1x1x3 (1)")
    logged.clear()
    rebuildUtils.keepName(item, "Cutlery bin", "Gridfinity bin 1x1x3", BIN)
    assert item.name == "Gridfinity bin 1x1x3 (1)"
    assert len(logged) == 1
