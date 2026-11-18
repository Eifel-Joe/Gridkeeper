"""
Round 39 (p296): the box code reads a body's edges and faces by index. Iterating a Fusion collection (list(), a for
loop) asks its length before every item, twice the calls: 5270 edges took 6.7 s with list(), 3.1 s with item(i) over
count (fusion-auftraege/r39_probe.log); a box build reads ~34 000 edges.
"""

import pathlib
import re

from tests.test_joint_origin_layout import _load

fusionLists = _load("fusionLists")
LIB = pathlib.Path(__file__).parent.parent / "lib" / "gridfinityUtils"


class Counting:
    def __init__(self, n):
        self.n = n
        self.countReads = 0
        self.itemCalls = 0

    @property
    def count(self):
        self.countReads += 1
        return self.n

    def item(self, i):
        self.itemCalls += 1
        return ("edge", i)

    def __len__(self):
        raise AssertionError("len() asked")

    def __iter__(self):
        raise AssertionError("iterated")

    def __getitem__(self, i):
        raise AssertionError("indexed")


class Collection:
    """A Fusion-like collection for stand-in bodies: count and item(i) only, as the box code reads it"""

    def __init__(self, entries):
        self.entries = list(entries)

    @property
    def count(self):
        return len(self.entries)

    def item(self, i):
        return self.entries[i]


def test_items_reads_count_once_and_each_item_once():
    edges = Counting(5)
    assert fusionLists.items(edges) == [("edge", i) for i in range(5)]
    assert edges.countReads == 1
    assert edges.itemCalls == 5


def test_items_of_several_collections_in_order():
    assert fusionLists.itemsOfAll([Counting(2), Counting(1)]) == [("edge", 0), ("edge", 1), ("edge", 0)]


def test_box_code_doesnt_iterate_edges_or_faces():
    pattern = re.compile(r"(list\(|for \w+ in |in )[\w.]*\.(edges|faces)\b")
    for name in ["predBoxGenerator", "predHandle", "predHandlePin", "predHinge", "predLatch"]:
        source = (LIB / f"{name}.py").read_text(encoding="utf-8")
        offenders = [line.strip() for line in source.splitlines() if pattern.search(line) and not line.strip().startswith("#")]
        assert offenders == [], name
        assert "fusionLists.items" in source, name
