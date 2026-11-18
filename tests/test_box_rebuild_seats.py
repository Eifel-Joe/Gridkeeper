"""
Round 36, p293: a joint of the user on one of the four latches (or a handle pin or hinge) jumped to the last latch when
the box was rebuilt. The four latches are four occurrences of one component, keyed by role and joint origin name alone
the last overwrote the others. A rebuild now tells them apart by their seat, the box joint origin the set joints each
to. Run on stand-ins instead of Fusion, the functions loaded from rebuildUtils' source as in test_bin_cell_rebuild.
"""

import ast
import os
import types

from tests.test_joint_origin_layout import _load as _loadModule

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REBUILD_UTILS = os.path.join(ROOT, "lib", "rebuildUtils.py")
predBoxParts = _loadModule("predBoxParts")
_ADSK = types.SimpleNamespace(fusion=types.SimpleNamespace(
    JointOrigin=types.SimpleNamespace(cast=lambda entity: entity), Component=object, Occurrence=object, Joint=object))


def _function(name):
    tree = ast.parse(open(REBUILD_UTILS, encoding="utf-8").read())
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def _load(*names):
    namespace = {"adsk": _ADSK, "predBoxParts": predBoxParts, "tagUtils": types.SimpleNamespace(TAG_GROUP="g", TAG_PART_ROLE="role")}
    for name in ("partRole",) + names:
        exec(compile(ast.Module(body=[_function(name)], type_ignores=[]), REBUILD_UTILS, "exec"), namespace)
    return [namespace[name] for name in names]


class _Attributes:
    def __init__(self, role=None):
        self.role = role

    def itemByName(self, group, name):
        return types.SimpleNamespace(value=self.role) if self.role is not None else None


class _Component:
    def __init__(self, name, jointOrigins=(), role=None):
        self.name = name
        self.attributes = _Attributes(role)
        self.jointOrigins = [_JointOrigin(jointOrigin, self) for jointOrigin in jointOrigins]


class _JointOrigin:
    def __init__(self, name, component, context=None):
        self.name = name
        self.parentComponent = component
        self.nativeObject = None
        self.assemblyContext = context

    def createForAssemblyContext(self, occurrence):
        proxy = _JointOrigin(self.name, self.parentComponent, occurrence)
        proxy.nativeObject = self
        return proxy


class _Occurrence:
    def __init__(self, path, component, children=()):
        self.fullPathName = path
        self.component = component
        self.childOccurrences = list(children)


def _joint(one, two, occurrenceOne=None, occurrenceTwo=None):
    return types.SimpleNamespace(geometryOrOriginOne=one, geometryOrOriginTwo=two, occurrenceOne=occurrenceOne, occurrenceTwo=occurrenceTwo)


LATCH_SEATS = ["Latch front left", "Latch front right", "Latch left", "Latch right"]


def _set(name):
    """A box set like boxBuilder builds it: Box, Lid, four occurrences of one Latch component, each jointed at its seat"""
    box = _Component("Box", [predBoxParts.seatJointOriginName(seat) for seat in predBoxParts.SEAT_NAMES] + ["Stack bottom joint origin"], role="Box")
    lid = _Component("Lid", ["Stack top joint origin"], role="Lid")
    latch = _Component("Latch", ["Latch joint origin"], role="Latch")
    boxOccurrence = _Occurrence(f"{name}+Box:1", box)
    latches = [_Occurrence(f"{name}+Latch:{index + 1}", latch) for index in range(4)]
    setOccurrence = _Occurrence(name, _Component(name), [boxOccurrence, _Occurrence(f"{name}+Lid:1", lid)] + latches)
    # the set's own joints, latch side first as predBoxInsert adds them, the box's seat second
    joints = []
    for (occurrence, seat) in zip(latches, LATCH_SEATS):
        latchSide = latch.jointOrigins[0].createForAssemblyContext(occurrence)
        seatSide = next(j for j in box.jointOrigins if j.name == predBoxParts.seatJointOriginName(seat)).createForAssemblyContext(boxOccurrence)
        joints.append(_joint(latchSide, seatSide, occurrence, boxOccurrence))
    return setOccurrence, latches, joints


def test_each_latch_occurrence_has_its_seat():
    (seatsByOccurrence,) = _load("seatsByOccurrence")
    (_, latches, joints) = _set("Boxes:1+Box 5x4x6:1")
    seats = seatsByOccurrence(joints)
    assert [seats[occurrence.fullPathName] for occurrence in latches] == LATCH_SEATS


def test_the_seat_is_found_on_either_side_and_without_the_joints_occurrences():
    (seatsByOccurrence,) = _load("seatsByOccurrence")
    (_, latches, joints) = _set("S")
    swapped = _joint(joints[0].geometryOrOriginTwo, joints[0].geometryOrOriginOne, joints[0].occurrenceTwo, joints[0].occurrenceOne)
    # a joint's sides may come without an occurrence (round 20, p220), the joint origin's context is the part then
    bare = _joint(joints[1].geometryOrOriginOne, joints[1].geometryOrOriginTwo)
    assert seatsByOccurrence([swapped, bare]) == {latches[0].fullPathName: "Latch front left", latches[1].fullPathName: "Latch front right"}


def test_joints_without_a_seat_give_none():
    (seatsByOccurrence,) = _load("seatsByOccurrence")
    lid = _Component("Lid", ["Lid joint origin", "Stack top joint origin"], role="Lid")
    box = _Component("Box", ["Lid joint origin"], role="Box")
    occurrence = _Occurrence("S+Lid:1", lid)
    joint = _joint(lid.jointOrigins[0].createForAssemblyContext(occurrence), box.jointOrigins[0].createForAssemblyContext(_Occurrence("S+Box:1", box)))
    # a joint whose entities aren't joint origins (geometry) is passed over too
    assert seatsByOccurrence([joint, _joint(None, None)]) == {}


def test_the_four_latches_get_four_keys_box_and_lid_none():
    (seatsByOccurrence, newJointOriginKeys) = _load("seatsByOccurrence", "newJointOriginKeys")
    (setOccurrence, latches, joints) = _set("New")
    keys = newJointOriginKeys(setOccurrence, seatsByOccurrence(joints))
    for (occurrence, seat) in zip(latches, LATCH_SEATS):
        assert keys[("Latch", seat, "Latch joint origin")].assemblyContext is occurrence
    assert ("Box", "", "Stack bottom joint origin") in keys and ("Lid", "", "Stack top joint origin") in keys
    assert ("Latch", "", "Latch joint origin") not in keys


def test_a_joint_on_the_front_left_latch_goes_to_the_new_front_left_latch_not_the_last():
    (seatsByOccurrence, newJointOriginKeys, oldJointOriginKey) = _load("seatsByOccurrence", "newJointOriginKeys", "oldJointOriginKey")
    (oldSet, oldLatches, oldJoints) = _set("Old")
    (newSet, newLatches, newJoints) = _set("New")
    seats = seatsByOccurrence(oldJoints + newJoints)
    newKeys = newJointOriginKeys(newSet, seats)
    for (index, seat) in enumerate(LATCH_SEATS):
        # the user's joint holds the old latch's joint origin seen through that latch
        userSide = oldLatches[index].component.jointOrigins[0].createForAssemblyContext(oldLatches[index])
        key = oldJointOriginKey(userSide, oldSet, seats)
        assert key == ("Latch", seat, "Latch joint origin")
        assert newKeys[key].assemblyContext is newLatches[index]


def test_a_joint_on_the_set_itself_or_the_box_keeps_its_key():
    (oldJointOriginKey,) = _load("oldJointOriginKey")
    (oldSet, _, _) = _set("Old")
    box = oldSet.childOccurrences[0]
    stack = next(j for j in box.component.jointOrigins if j.name == "Stack bottom joint origin").createForAssemblyContext(box)
    assert oldJointOriginKey(stack, oldSet, {}) == ("Box", "", "Stack bottom joint origin")
    own = _JointOrigin("Own", oldSet.component)
    assert oldJointOriginKey(own, oldSet, {}) == ("", "", "Own")


def test_the_rebuild_keys_joint_origins_by_seat():
    source = ast.unparse(_function("repointJointsByName"))
    for name in ("seatsByOccurrence(", "newJointOriginKeys(", "oldJointOriginKey("):
        assert name in source


def test_the_part_is_the_joint_origins_context_even_when_the_joint_names_a_higher_occurrence():
    """Review round 36: oldJointOriginKey and newJointOriginKeys go by the part's own occurrence; should a joint name
    the set or the container as its occurrence, the joint origin's context is still the part"""
    (seatsByOccurrence,) = _load("seatsByOccurrence")
    (setOccurrence, latches, joints) = _set("S")
    higher = [_joint(j.geometryOrOriginOne, j.geometryOrOriginTwo, setOccurrence, setOccurrence) for j in joints]
    seats = seatsByOccurrence(higher)
    assert [seats[occurrence.fullPathName] for occurrence in latches] == LATCH_SEATS


def test_a_joint_on_a_seat_joint_origin_of_the_box_keeps_its_key():
    """A joint of the user onto the box's own seat joint origin is on the box, one occurrence, no seat"""
    (seatsByOccurrence, oldJointOriginKey) = _load("seatsByOccurrence", "oldJointOriginKey")
    (oldSet, _, oldJoints) = _set("Old")
    box = oldSet.childOccurrences[0]
    seat = next(j for j in box.component.jointOrigins if j.name == "Latch front left joint origin").createForAssemblyContext(box)
    assert oldJointOriginKey(seat, oldSet, seatsByOccurrence(oldJoints)) == ("Box", "", "Latch front left joint origin")


def test_a_part_of_an_old_set_without_its_seat_joint_finds_no_new_part():
    """Review round 36: a latch not jointed at a seat can't be told apart from the others, its joint isn't moved to
    some latch but stays with the old set, the rebuild says so (repointJointsByName's note)"""
    (seatsByOccurrence, newJointOriginKeys, oldJointOriginKey) = _load("seatsByOccurrence", "newJointOriginKeys", "oldJointOriginKey")
    (oldSet, oldLatches, _) = _set("Old")
    (newSet, _, newJoints) = _set("New")
    seats = seatsByOccurrence(newJoints)
    userSide = oldLatches[0].component.jointOrigins[0].createForAssemblyContext(oldLatches[0])
    assert oldJointOriginKey(userSide, oldSet, seats) not in newJointOriginKeys(newSet, seats)
