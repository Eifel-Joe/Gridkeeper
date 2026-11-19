"""
Round 47 (p591): how a kept part comes about (drawn into a scratch component that is deleted again) and how a box set
gets its copy (one base feature in the part's component, the bodies named as drawn). Spec
dev-notes/specs/2026-11-19-r47-box-small-parts.md, requirements 1, 2 and 4; Fusion stand-ins below.
"""

import sys

import pytest

from tests.test_joint_origin_layout import _load

copies = _load("predPartCopies")


class FakeTbm:
    def __init__(self):
        self.copied = []

    def copy(self, body):
        self.copied.append(body)
        return ('copy', body)


@pytest.fixture
def tbm(monkeypatch):
    fake = FakeTbm()
    fusion = sys.modules["adsk.fusion"]
    manager = type("TemporaryBRepManager", (), {"get": staticmethod(lambda: fake)})
    monkeypatch.setattr(fusion, "TemporaryBRepManager", manager, raising=False)
    return fake


class Body:
    def __init__(self, name, source=None, renameFails=False):
        self._name = name
        self.source = source
        self.renameFails = renameFails

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if self.renameFails:
            raise RuntimeError("rename refused")
        self._name = value


class Bodies(list):
    def __init__(self, failAt=None, renameFails=False):
        super().__init__()
        self.failAt = failAt
        self.renameFails = renameFails

    def add(self, body, base):
        if self.failAt is not None and len(self) == self.failAt:
            raise RuntimeError("add refused")
        base.log.append("add")
        added = Body(f"Body{len(self) + 1}", body, self.renameFails)
        base.bodies.append(added)
        self.append(added)
        return added


class Base:
    def __init__(self, component, deletes=True):
        self.log = []
        self.deleted = False
        self.bodies = []
        self.component = component
        self.deletes = deletes

    def startEdit(self):
        self.log.append("start")

    def finishEdit(self):
        self.log.append("finish")

    def deleteMe(self):
        if not self.deletes:
            return False
        self.deleted = True
        for body in self.bodies:
            self.component.bRepBodies.remove(body)
        return True


class Component:
    def __init__(self, failAt=None, renameFails=False, baseDeletes=True):
        self.bRepBodies = Bodies(failAt, renameFails)
        self.bases = []
        component = self

        class BaseFeatures:
            def add(self):
                base = Base(component, baseDeletes)
                component.bases.append(base)
                return base

        self.features = type("Features", (), {"baseFeatures": BaseFeatures()})()
        self.occurrences = Occurrences()


class Occurrence:
    def __init__(self, deletes):
        self.component = type("Scratch", (), {})()
        self.component.bRepBodies = []
        self.deleted = False
        self.deletes = deletes

    def deleteMe(self):
        if self.deletes == "raise":
            raise RuntimeError("delete refused")
        self.deleted = self.deletes
        return self.deletes


class Occurrences:
    def __init__(self, deletes=True):
        self.made = []
        self.deletes = deletes

    def addNewComponent(self, transform):
        occurrence = Occurrence(self.deletes)
        self.made.append(occurrence)
        return occurrence


@pytest.fixture
def identity(monkeypatch):
    core = sys.modules["adsk.core"]
    matrix = type("Matrix3D", (), {"create": staticmethod(lambda: "identity")})
    monkeypatch.setattr(core, "Matrix3D", matrix, raising=False)


def test_a_copy_is_one_base_feature_with_the_bodies_named_as_drawn(tbm):
    component = Component()
    bodies = copies.addCopies(component, [("BottomHingePart_M3x30", "b"), ("TopHingePart_M3x30", "t")])
    assert [b.name for b in bodies] == ["BottomHingePart_M3x30", "TopHingePart_M3x30"]
    assert len(component.bases) == 1 and component.bases[0].log == ["start", "add", "add", "finish"]
    # each box gets copies of its own, the kept bodies stay as they are for the next box
    assert tbm.copied == ["b", "t"]
    assert [b.source for b in bodies] == [("copy", "b"), ("copy", "t")]


def test_a_failed_copy_leaves_no_base_feature_behind(tbm):
    component = Component(failAt=1)
    with pytest.raises(RuntimeError, match="add refused"):
        copies.addCopies(component, [("a", "a"), ("b", "b")])
    assert component.bases[0].deleted and len(component.bRepBodies) == 0
    assert component.bases[0].log[-1] == "finish"


def test_a_failed_naming_leaves_no_base_feature_behind(tbm):
    """Review round 47: the bodies stayed when naming failed, the part was then drawn on top of them"""
    component = Component(renameFails=True)
    with pytest.raises(RuntimeError, match="rename refused"):
        copies.addCopies(component, [("Latch", "l")])
    assert component.bases[0].deleted and len(component.bRepBodies) == 0


def test_a_copy_fusion_does_not_remove_is_left_behind_not_drawn_over(tbm):
    component = Component(failAt=1, baseDeletes=False)
    with pytest.raises(copies.LeftBehind):
        copies.addCopies(component, [("a", "a"), ("b", "b")])


def test_a_kept_part_is_drawn_into_a_scratch_component_that_is_deleted(tbm, identity):
    parent = Component()
    drawnInto = []

    def draw(component):
        drawnInto.append(component)
        component.bRepBodies.append(Body("Latch"))
        return []

    # every body the generator leaves in the scratch component, as insertParts took all of a part's bodies (review)
    kept = copies.keepDrawn(parent, draw)
    assert kept == [("Latch", ("copy", tbm.copied[0]))]
    (scratch,) = parent.occurrences.made
    assert drawnInto == [scratch.component] and scratch.deleted


def test_the_scratch_component_goes_also_when_drawing_fails(tbm, identity):
    parent = Component()

    def draw(component):
        raise RuntimeError("edge not found")

    with pytest.raises(RuntimeError):
        copies.keepDrawn(parent, draw)
    assert parent.occurrences.made[0].deleted


def test_a_failed_drawing_is_not_hidden_by_a_failed_clean_up(tbm, identity):
    parent = Component()
    parent.occurrences = Occurrences(deletes="raise")

    def draw(component):
        raise RuntimeError("edge not found")

    with pytest.raises(RuntimeError, match="edge not found"):
        copies.keepDrawn(parent, draw)


def test_a_scratch_component_fusion_keeps_is_an_error(tbm, identity):
    parent = Component()
    parent.occurrences = Occurrences(deletes=False)
    with pytest.raises(RuntimeError, match="not deleted"):
        copies.keepDrawn(parent, lambda component: component.bRepBodies.append(Body("Latch")))
