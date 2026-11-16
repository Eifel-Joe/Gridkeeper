"""
Tests for deleting the items of an old part one by one in a rebuild (round 27): with the marker at the end every
deleted item made Fusion recompute everything after it, a second stacked box (about 90 items, 60 s and more) once per
item of the old box, hours in all (r27_cmd run 2, 17.11.2026). The marker goes right after the old items first, the
later ones are computed once at the end.
"""

from tests.test_joint_origin_layout import _load

timelineRemoval = _load("timelineRemoval")


class Timeline:
    def __init__(self):
        self.calls = []

    def moveToEnd(self):
        self.calls.append("moveToEnd")


class Item:
    def __init__(self, timeline, name, deletable=True):
        self.timeline = timeline
        self.name = name
        self.isValid = True
        self.isDeletable = deletable
        self.isSuppressed = False

    def rollTo(self, rollBefore):
        self.timeline.calls.append(("rollTo", self.name, rollBefore))

    def deleteObject(self):
        self.timeline.calls.append(("delete", self.name))
        if self.isDeletable:
            self.isValid = False
        return self.isDeletable


def items(timeline, *names):
    return [Item(timeline, name) for name in names]


def test_marker_goes_after_the_old_items_before_the_first_delete_and_to_the_end_once_after():
    timeline = Timeline()
    old = items(timeline, "Sketch1", "Extrude1", "Chamfer1")
    kept = timelineRemoval.deleteOneByOne(old, timeline, log=lambda message: None)
    assert kept == []
    assert timeline.calls == [
        ("rollTo", "Chamfer1", False),
        ("delete", "Chamfer1"),
        ("delete", "Extrude1"),
        ("delete", "Sketch1"),
        "moveToEnd",
    ]


def test_an_item_fusion_wont_delete_is_suppressed_and_named():
    timeline = Timeline()
    old = items(timeline, "Sketch1", "Joint1")
    old[1].isDeletable = False
    logged = []
    kept = timelineRemoval.deleteOneByOne(old, timeline, log=logged.append)
    assert kept == ["Joint1"]
    assert old[1].isSuppressed is True
    assert timeline.calls[-1] == "moveToEnd"
    assert len(logged) == 1 and "Joint1" in logged[0]


def test_items_gone_already_are_skipped_and_the_marker_goes_after_the_last_one_left():
    timeline = Timeline()
    old = items(timeline, "Sketch1", "Extrude1", "Chamfer1")
    old[2].isValid = False
    timelineRemoval.deleteOneByOne(old, timeline, log=lambda message: None)
    assert timeline.calls[0] == ("rollTo", "Extrude1", False)
    assert ("delete", "Chamfer1") not in timeline.calls


def test_nothing_left_still_ends_at_the_end():
    timeline = Timeline()
    assert timelineRemoval.deleteOneByOne([], timeline, log=lambda message: None) == []
    assert timeline.calls == ["moveToEnd"]
