"""
Tests for deleting the items of an old part one by one in a rebuild (round 27): with the marker at the end every
deleted item made Fusion recompute everything after it, a second stacked box (about 90 items, 60 s and more) once per
item of the old box, hours in all (r27_cmd run 2, 17.11.2026). The marker goes right after the old items first, the
later ones are computed once at the end.
"""

import pytest

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


def test_the_marker_goes_back_to_the_end_when_a_delete_breaks():
    """Review R27: an error other than Fusion's RuntimeError left the marker before the new part"""
    import pytest
    timeline = Timeline()
    old = items(timeline, "Sketch1", "Extrude1")

    def broken():
        raise ValueError("broken")
    old[1].deleteObject = broken
    with pytest.raises(ValueError):
        timelineRemoval.deleteOneByOne(old, timeline, log=lambda message: None)
    assert timeline.calls[-1] == "moveToEnd"


# Round 43 (p533): a rebuild with joints moved over to the new part. Deleting the old group as a whole took a moved
# joint along, it still hangs on the old joint origin it used; with those joint origins deleted first, one by one, the
# rest as a whole keeps the joint and is several times faster than item by item (fusion-auftraege/r43_probe.py).


class Group:
    def __init__(self, timeline, start, end, deletes=True, raises=False):
        self.timeline = timeline
        self.start = start
        self.end = end
        self.isValid = True
        self.deletes = deletes
        self.raises = raises

    def deleteMe(self, deleteGroupAndContents):
        self.timeline.calls.append(("deleteGroup", self.start, self.end, deleteGroupAndContents))
        if self.raises:
            raise RuntimeError("3 : the group can't be deleted")
        self.isValid = False
        if deleteGroupAndContents and self.deletes:
            for item in self.timeline.items:
                if self.start <= item.index <= self.end:
                    item.isValid = False
        return self.deletes or not deleteGroupAndContents


class Groups:
    def __init__(self, timeline):
        self.timeline = timeline
        self.deletes = True
        self.raises = False

    def add(self, start, end):
        self.timeline.calls.append(("group", start, end))
        return Group(self.timeline, start, end, self.deletes, self.raises)


class GroupingTimeline(Timeline):
    def __init__(self):
        super().__init__()
        self.items = []
        self.timelineGroups = Groups(self)


class IndexedItem(Item):
    """Fusion counts the items after a deleted one down, the timeline has no gaps"""
    def deleteObject(self):
        deleted = super().deleteObject()
        if deleted:
            for item in self.timeline.items:
                if item.isValid and item.index > self.index:
                    item.index -= 1
        return deleted


def indexed(timeline, *names, start=5):
    old = [IndexedItem(timeline, name) for name in names]
    for (offset, item) in enumerate(old):
        item.index = start + offset
    timeline.items += old
    return old


def moved(*names):
    return lambda item: item.name in names


def test_the_moved_joint_origins_go_one_by_one_first_then_the_rest_as_a_whole():
    timeline = GroupingTimeline()
    old = indexed(timeline, "Occurrence", "Sketch1", "Pocket joint origin", "Extrude1")
    kept = timelineRemoval.deleteMovedFirst(old, moved("Pocket joint origin"), timeline, log=lambda message: None)
    assert kept == []
    assert all(not item.isValid for item in old)
    assert timeline.calls == [
        ("rollTo", "Pocket joint origin", False),
        ("delete", "Pocket joint origin"),
        "moveToEnd",
        # the rest, contiguous in the timeline once the joint origin is gone: Fusion closes the gap
        ("group", 5, 7),
        ("deleteGroup", 5, 7, True),
    ]


def test_nothing_moved_goes_straight_to_the_whole_delete():
    timeline = GroupingTimeline()
    old = indexed(timeline, "Occurrence", "Sketch1")
    assert timelineRemoval.deleteMovedFirst(old, moved(), timeline, log=lambda message: None) == []
    assert timeline.calls[-2:] == [("group", 5, 6), ("deleteGroup", 5, 6, True)]
    assert ("delete", "Sketch1") not in timeline.calls


def test_a_moved_joint_origin_fusion_wont_delete_leaves_the_rest_item_by_item():
    # the whole delete would take its joint along
    timeline = GroupingTimeline()
    old = indexed(timeline, "Occurrence", "Socket joint origin 2-2", "Extrude1")
    old[1].isDeletable = False
    logged = []
    kept = timelineRemoval.deleteMovedFirst(old, moved("Socket joint origin 2-2"), timeline, log=logged.append)
    assert kept == ["Socket joint origin 2-2"]
    assert not any(call[0] == "group" for call in timeline.calls if isinstance(call, tuple))
    assert ("delete", "Extrude1") in timeline.calls and ("delete", "Occurrence") in timeline.calls
    assert not old[0].isValid and not old[2].isValid
    assert any("item by item" in message for message in logged)


def test_a_rest_with_a_gap_goes_item_by_item():
    timeline = GroupingTimeline()
    old = indexed(timeline, "Occurrence", "Sketch1", "Extrude1")
    old[2].index = 9  # something else between them in the timeline
    logged = []
    timelineRemoval.deleteMovedFirst(old, moved(), timeline, log=logged.append)
    assert not any(call[0] == "group" for call in timeline.calls if isinstance(call, tuple))
    assert all(not item.isValid for item in old)
    assert any("item by item" in message and "contiguous" in message for message in logged)


@pytest.mark.parametrize("failure", ["refuses", "raises"])
def test_a_whole_delete_that_fails_drops_the_new_group_and_goes_item_by_item(failure):
    timeline = GroupingTimeline()
    timeline.timelineGroups.deletes = failure != "refuses"
    timeline.timelineGroups.raises = failure == "raises"
    old = indexed(timeline, "Occurrence", "Sketch1")
    logged = []
    kept = timelineRemoval.deleteMovedFirst(old, moved(), timeline, log=logged.append)
    assert kept == []
    assert all(not item.isValid for item in old)
    assert ("delete", "Sketch1") in timeline.calls and ("delete", "Occurrence") in timeline.calls
    assert timeline.calls[-1] == "moveToEnd"
    assert any("item by item" in message for message in logged)


def test_joints_moved_but_none_of_their_joint_origins_found_goes_item_by_item():
    # review round 43: the whole delete would take the moved joints along, the measured failure
    timeline = GroupingTimeline()
    old = indexed(timeline, "Occurrence", "Sketch1")
    logged = []
    kept = timelineRemoval.deleteMovedFirst(old, moved(), timeline, log=logged.append, expectedMoved=1)
    assert kept == []
    assert not any(call[0] == "group" for call in timeline.calls if isinstance(call, tuple))
    assert all(not item.isValid for item in old)
    assert any("item by item" in message for message in logged)


def test_joints_moved_from_two_joint_origins_but_one_found_goes_item_by_item():
    # second review round 43: the whole delete would take the joint of the one not found along
    timeline = GroupingTimeline()
    old = indexed(timeline, "Occurrence", "Latch joint origin", "Sketch1")
    logged = []
    timelineRemoval.deleteMovedFirst(old, moved("Latch joint origin"), timeline, log=logged.append, expectedMoved=2)
    assert not any(call[0] == "group" for call in timeline.calls if isinstance(call, tuple))
    assert all(not item.isValid for item in old)
    assert any("item by item" in message and "1 of the 2" in message for message in logged)
