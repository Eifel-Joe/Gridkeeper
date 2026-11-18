"""
Round 43: deleting the old part of a rebuild (p533) and the name of a joint the rebuild made (p430). A joint moved over
to the new part still hangs on the old joint origin it used: the group as a whole took it along. The repointing notes
those joint origins on the target, removeOldGroup deletes them first (timelineRemoval.deleteMovedFirst). Once the old
part is gone, a joint the build made named with Fusion's counter gets the lowest free name. Run on stand-ins, the
functions loaded from rebuildUtils' source as in test_rebuild_joint_ends.
"""

import ast
import os
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REBUILD_UTILS = os.path.join(ROOT, "lib", "rebuildUtils.py")
SOURCE = open(REBUILD_UTILS, encoding="utf-8").read()


def _function(name):
    return next(n for n in ast.parse(SOURCE).body if isinstance(n, ast.FunctionDef) and n.name == name)


def _load(name, **namespace):
    # annotations left unevaluated: the stand-ins have no Fusion types
    future = ast.parse("from __future__ import annotations").body
    exec(compile(ast.Module(body=future + [_function(name)], type_ignores=[]), REBUILD_UTILS, "exec"), namespace)
    return namespace[name]


class _Log:
    def __init__(self):
        self.messages = []

    def fileLog(self, message):
        self.messages.append(message)

    debugLog = fileLog


def _adsk():
    return types.SimpleNamespace(fusion=types.SimpleNamespace(JointOrigin=types.SimpleNamespace(
        cast=lambda entity: entity if isinstance(entity, _JointOrigin) else None)))


class _JointOrigin:
    def __init__(self, name):
        self.name = name


class _Item:
    def __init__(self, entity):
        self.entity = entity
        self.isValid = True


class _Group:
    def __init__(self, items):
        self.name = "Gridfinity baseplate 2x2"
        self.count = len(items)
        self.isCollapsed = False
        self.isValid = True
        self.parentTimeline = "timeline"
        self.calls = []

    def deleteMe(self, deleteGroupAndContents):
        self.calls.append(deleteGroupAndContents)
        self.isValid = False
        return True


def test_the_target_notes_the_joint_origins_joints_were_moved_away_from():
    assert "movedFrom" in ast.unparse(next(n for n in ast.parse(SOURCE).body if isinstance(n, ast.ClassDef) and n.name == "RebuildTarget"))
    for name in ("repointJoints", "repointJointsByName"):
        tries = [n for n in ast.walk(_function(name)) if isinstance(n, ast.Try)]
        body = [ast.unparse(statement) for statement in tries[0].body]
        moved = next(i for (i, line) in enumerate(body) if line.startswith("setattr(joint, side,"))
        noted = [i for (i, line) in enumerate(body) if line.startswith("target.movedFrom.append(")]
        # the native one, as a timeline item's entity is, and only once the joint took the new side
        assert noted and noted[0] > moved, (name, body)
        assert "nativeObject" in body[noted[0]], (name, body[noted[0]])


def test_with_joints_moved_the_noted_joint_origins_go_first_then_the_rest_as_a_whole():
    pocket = _JointOrigin("Pocket joint origin")
    other = _JointOrigin("Pocket joint origin 2")
    items = [_Item("Occurrence"), _Item(pocket), _Item(other), _Item("Extrude1")]
    group = _Group(items)
    # two joints moved away from the same joint origin: it counts once
    target = types.SimpleNamespace(group=group, groupItems=items, movedFrom=[pocket, pocket])
    calls = []

    def deleteMovedFirst(groupItems, isMoved, timeline, log, expectedMoved=0):
        calls.append((groupItems, [item for item in groupItems if isMoved(item)], timeline, expectedMoved))
        return []
    removal = types.SimpleNamespace(deleteMovedFirst=deleteMovedFirst,
                                    deleteOneByOne=lambda *args: (_ for _ in ()).throw(AssertionError("item by item")))
    removeOldGroup = _load("removeOldGroup", adsk=_adsk(), commonUtils=_Log(), timelineRemoval=removal, LOG_PREFIX="test")
    assert removeOldGroup(target, jointsMoved=True) == []
    # the header goes, its items stay in the timeline for deleteMovedFirst
    assert group.calls == [False]
    assert calls == [(items, [items[1]], "timeline", 1)]


def test_an_item_whose_entity_fusion_wont_give_isnt_taken_for_a_moved_one():
    # review round 43: the header is gone already, an exception there would leave the old part ungrouped
    class Broken:
        isValid = True

        @property
        def entity(self):
            raise RuntimeError("3 : Associated feature is invalid")
    pocket = _JointOrigin("Pocket joint origin")
    items = [Broken(), _Item(pocket)]
    target = types.SimpleNamespace(group=_Group(items), groupItems=items, movedFrom=[pocket])
    picked = []
    removal = types.SimpleNamespace(deleteMovedFirst=lambda groupItems, isMoved, timeline, log, expectedMoved=0: picked.extend(
        [item for item in groupItems if isMoved(item)]) or [])
    removeOldGroup = _load("removeOldGroup", adsk=_adsk(), commonUtils=_Log(), timelineRemoval=removal, LOG_PREFIX="test")
    removeOldGroup(target, jointsMoved=True)
    assert picked == [items[1]]


def test_without_joints_moved_the_group_goes_as_a_whole_as_before():
    items = [_Item("Occurrence"), _Item("Extrude1")]
    group = _Group(items)
    target = types.SimpleNamespace(group=group, groupItems=items, movedFrom=[])
    removal = types.SimpleNamespace(deleteMovedFirst=None, deleteOneByOne=None)
    removeOldGroup = _load("removeOldGroup", adsk=_adsk(), commonUtils=_Log(), timelineRemoval=removal, LOG_PREFIX="test")
    assert removeOldGroup(target, jointsMoved=False) == []
    assert group.calls == [True]


class _Joint:
    def __init__(self, name, token, component):
        self.name = name
        # a token string may differ between fetches (Fusion's docs): the joints are compared as objects
        self.entityToken = token + "-fetched-anew"
        self.parentComponent = component
        component.joints.append(self)


class _Component:
    def __init__(self):
        self.joints = []


def test_a_joint_the_build_made_drops_fusions_counter_once_the_old_one_is_gone():
    root = _Component()
    old = _Joint("A in cell", "a", root)
    new = _Joint("B in cell (1)", "b2", root)
    sameName = _Joint("A in cell (1)", "a2", root)
    user = _Joint("Rigid (1)", "u", root)
    design = types.SimpleNamespace(rootComponent=types.SimpleNamespace(allJoints=root.joints))
    jointNames = types.SimpleNamespace(freedName=lambda name, taken: _freedName(name, taken))
    dropJointCounters = _load("dropJointCounters", jointNames=jointNames, commonUtils=_Log(), LOG_PREFIX="test")
    dropJointCounters(design, [old, user])
    # new joints only: the user's own keeps its name
    assert new.name == "B in cell"
    assert user.name == "Rigid (1)"
    assert old.name == "A in cell"
    # another bin of the same name still holds the base: Fusion's counter stays
    assert sameName.name == "A in cell (1)"


def _freedName(name, taken):
    base = name.rsplit(" (", 1)[0]
    return base if name != base and base not in taken else None


def test_rebuild_drops_the_counters_after_the_old_group_is_gone_and_not_on_a_preview():
    body = [ast.unparse(statement) for statement in _function("rebuild").body]
    before = next(i for (i, line) in enumerate(body) if "existingJoints(design)" in line)
    build = next(i for (i, line) in enumerate(body) if "newBodies = build(" in line)
    remove = next(i for (i, line) in enumerate(body) if "removeOldGroup(" in line)
    # whether joints were moved from what was noted, not the count of the notes (review round 43)
    assert "jointsMoved=len(target.movedFrom) > 0" in body[remove]
    drop = next(i for (i, line) in enumerate(body) if line.startswith("dropJointCounters(design,"))
    preview = next(i for (i, line) in enumerate(body) if line.startswith("if isPreview"))
    assert preview < before < build < remove < drop


class _NamedComponent:
    def __init__(self, name, refuse=False):
        self._name = name
        self.refuse = refuse
        self.isValid = True

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if self.refuse:
            raise RuntimeError("3 : rename refused")
        self._name = value


def _dropComponentCounters(components, named):
    log = _Log()
    # the real names module: the counter may go down to one below its own, not only to the base
    from tests.test_joint_origin_layout import _load as _loadUtil
    drop = _load("dropComponentCounters", jointNames=_loadUtil("jointNames"), commonUtils=log, LOG_PREFIX="test")
    design = types.SimpleNamespace(allComponents=components)
    drop(design, named)
    return log


def test_a_component_the_build_named_drops_fusions_counter_once_the_old_one_is_gone():
    # round 44 (p570): the old bin "B" is gone, the new one asked for "B" got "B (1)" while it was there
    new = _NamedComponent("B (1)")
    text = _NamedComponent("Text (3)")
    other = _NamedComponent("Text")
    user = _NamedComponent("Mine (2)")
    _dropComponentCounters([new, text, other, user], [(new, "B"), (text, "Text")])
    assert new.name == "B"
    # another part still holds the base: the counter goes to the lowest free one only
    assert text.name == "Text (1)"
    # not named by the build, the user's own "(n)" included: untouched
    assert other.name == "Text"
    assert user.name == "Mine (2)"


def test_a_name_the_generator_asked_for_with_a_counter_of_its_own_stays():
    # review round 44: a label text "M3 (2)" names the insert "... M3 (2)"; its base was the old insert's name, yet
    # Fusion counted nothing, the name is what was asked for
    new = _NamedComponent("Gridfinity label 1U M3 (2)")
    _dropComponentCounters([new], [(new, "Gridfinity label 1U M3 (2)")])
    assert new.name == "Gridfinity label 1U M3 (2)"


def test_a_name_counted_from_another_base_stays():
    # "Mine (1)" isn't Fusion's count of the asked "B"
    new = _NamedComponent("Mine (1)")
    _dropComponentCounters([new], [(new, "B")])
    assert new.name == "Mine (1)"


def test_a_component_gone_again_is_skipped():
    gone = _NamedComponent("B (1)")
    gone.isValid = False
    _dropComponentCounters([], [(gone, "B")])
    assert gone.name == "B (1)"


def test_a_component_fusion_wont_rename_keeps_its_name_logged():
    new = _NamedComponent("B (1)", refuse=True)
    log = _dropComponentCounters([new], [(new, "B")])
    assert new.name == "B (1)"
    assert any("kept its name" in message for message in log.messages)


def test_rebuild_records_the_names_while_building_and_drops_the_counters_after_the_old_group_is_gone():
    statements = _function("rebuild").body
    body = [ast.unparse(statement) for statement in statements]
    preview = next(i for (i, line) in enumerate(body) if line.startswith("if isPreview"))
    build = next(i for (i, line) in enumerate(body) if "newBodies = build(" in line)
    # the build runs inside the recording, nothing else does
    assert body[build].startswith("with componentNames.recording() as named:")
    assert len(statements[build].body) == 1
    remove = next(i for (i, line) in enumerate(body) if "removeOldGroup(" in line)
    drop = next(i for (i, line) in enumerate(body) if line.startswith("dropComponentCounters(design, named)"))
    assert preview < build < remove < drop


def test_a_name_fusion_doesnt_list_among_the_components_doesnt_stop_the_rebuild():
    # review round 44: a component whose name isn't in allComponents' names raised ValueError past the RuntimeError
    new = _NamedComponent("B (1)")
    _dropComponentCounters([], [(new, "B")])
    assert new.name == "B"
