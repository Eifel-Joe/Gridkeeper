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
    build = next(i for (i, line) in enumerate(body) if line.startswith("newBodies = build("))
    remove = next(i for (i, line) in enumerate(body) if "removeOldGroup(" in line)
    # whether joints were moved from what was noted, not the count of the notes (review round 43)
    assert "jointsMoved=len(target.movedFrom) > 0" in body[remove]
    drop = next(i for (i, line) in enumerate(body) if line.startswith("dropJointCounters(design,"))
    preview = next(i for (i, line) in enumerate(body) if line.startswith("if isPreview"))
    assert preview < before < build < remove < drop
