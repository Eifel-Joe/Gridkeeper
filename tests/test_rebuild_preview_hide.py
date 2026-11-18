"""
Round 39, p481: the box's rebuild preview tried to suppress the old set's timeline group; Fusion always refuses a box
set's group ("Some group features are not suppression-configurable"), then all 298 items were suppressed one by one,
which is why the old set was hidden all the same (fusion-auftraege/r39_probe.log, step p481). The box hides the old
set by its occurrence's light bulb instead (all 13 bodies hidden at once). The light bulb is turned back on when the
command ends, whatever way it ends (cancel, OK, failure), should Fusion's undo of the preview not do it.
Run on stand-ins, the functions loaded from rebuildUtils' source as in test_box_rebuild_seats.
"""

import ast
import os
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REBUILD_UTILS = os.path.join(ROOT, "lib", "rebuildUtils.py")
BOX_ENTRY = os.path.join(ROOT, "commands", "commandCreateBox", "entry.py")
BOX_BUILDER = os.path.join(ROOT, "commands", "commandCreateBox", "boxBuilder.py")


def _load(*names):
    source = open(REBUILD_UTILS, encoding="utf-8").read()
    tree = ast.parse(source)
    log = []
    namespace = {"commonUtils": types.SimpleNamespace(debugLog=log.append, fileLog=log.append), "LOG_PREFIX": "test", "RebuildTarget": object}
    body = [node for node in tree.body
            if (isinstance(node, ast.FunctionDef) and node.name in names)
            or (isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "_hiddenForPreview" for t in node.targets))]
    exec(compile(ast.Module(body=body, type_ignores=[]), REBUILD_UTILS, "exec"), namespace)
    return namespace, log


class _Item:
    def __init__(self, name, refuses=False):
        self.name = name
        self.refuses = refuses
        self.suppressed = False

    @property
    def isSuppressed(self):
        return self.suppressed

    @isSuppressed.setter
    def isSuppressed(self, value):
        if self.refuses:
            raise RuntimeError("3 : Cannot suppress/unsuppress group. Some group features are not suppression-configurable.")
        self.suppressed = value


class _Occurrence:
    def __init__(self):
        self.isLightBulbOn = True
        self.isValid = True


def _target(occurrence, groupRefuses=True):
    return types.SimpleNamespace(group=_Item("Box 5×4×6", refuses=groupRefuses), groupItems=[_Item("Sketch1"), _Item("Extrude1")],
                                 occurrence=occurrence)


def test_a_set_with_an_occurrence_is_hidden_by_its_light_bulb():
    namespace, log = _load("hideOldBody", "restoreHiddenForPreview")
    occurrence = _Occurrence()
    target = _target(occurrence)
    namespace["hideOldBody"](target, byLightBulb=True)
    assert occurrence.isLightBulbOn is False
    assert not target.group.suppressed and not any(item.suppressed for item in target.groupItems)
    assert log == []


def test_without_the_light_bulb_way_the_group_and_items_go_as_before():
    namespace, log = _load("hideOldBody", "restoreHiddenForPreview")
    target = _target(_Occurrence(), groupRefuses=False)
    namespace["hideOldBody"](target)
    assert target.group.suppressed
    target = _target(_Occurrence(), groupRefuses=True)
    namespace["hideOldBody"](target)
    assert all(item.suppressed for item in target.groupItems)
    # a part of bodies in the root has no occurrence: the light bulb way falls back to suppressing
    target = _target(None, groupRefuses=False)
    namespace["hideOldBody"](target, byLightBulb=True)
    assert target.group.suppressed


def test_the_light_bulb_comes_back_when_the_command_ends():
    namespace, _ = _load("hideOldBody", "restoreHiddenForPreview")
    occurrence = _Occurrence()
    namespace["hideOldBody"](_target(occurrence), byLightBulb=True)
    namespace["restoreHiddenForPreview"]()
    assert occurrence.isLightBulbOn is True
    # once only: a later end restores nothing more
    occurrence.isLightBulbOn = False
    namespace["restoreHiddenForPreview"]()
    assert occurrence.isLightBulbOn is False


def test_a_set_gone_with_ok_isnt_touched():
    namespace, log = _load("hideOldBody", "restoreHiddenForPreview")
    occurrence = _Occurrence()
    namespace["hideOldBody"](_target(occurrence), byLightBulb=True)
    occurrence.isValid = False
    namespace["restoreHiddenForPreview"]()
    assert occurrence.isLightBulbOn is False


def test_a_refused_restore_is_logged_and_the_rest_still_restored():
    namespace, log = _load("hideOldBody", "restoreHiddenForPreview")

    class Refusing(_Occurrence):
        def __setattr__(self, name, value):
            if name == "isLightBulbOn" and value is True and "isLightBulbOn" in self.__dict__:
                raise RuntimeError("refused")
            super().__setattr__(name, value)

    first, second = Refusing(), _Occurrence()
    namespace["hideOldBody"](_target(first), byLightBulb=True)
    namespace["hideOldBody"](_target(second), byLightBulb=True)
    namespace["restoreHiddenForPreview"]()
    assert second.isLightBulbOn is True
    assert any("refused" in line for line in log)


def _functionSource(path, name):
    source = open(path, encoding="utf-8").read()
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(source, node)


def test_the_box_command_restores_on_every_end():
    destroy = _functionSource(BOX_ENTRY, "command_destroy")
    # first thing, before anything that may raise, and not under a termination reason
    first = ast.parse(destroy).body[0].body
    calls = [ast.unparse(statement) for statement in first[:3]]
    assert "rebuildUtils.restoreHiddenForPreview()" in calls


def test_the_box_rebuild_hides_by_light_bulb():
    rebuild = _functionSource(BOX_BUILDER, "rebuildBox")
    assert "hideByLightBulb=True" in rebuild
    utilsRebuild = _functionSource(REBUILD_UTILS, "rebuild")
    assert "hideOldBody(target, byLightBulb=hideByLightBulb)" in utilsRebuild
