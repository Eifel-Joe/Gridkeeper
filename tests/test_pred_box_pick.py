"""
Round 45 (p296, p480): the box's chamfers and fillets find their edges and faces where they are expected instead of
turning every edge of the body into its item form (34 294 edges.item per build, 11-16 s,
fusion-auftraege/r45_profil.log). A point on the expected item asks Fusion for what lies there (findBRepUsingPoint,
0.25 ms, exactly that edge in r45_probe.log); the candidates are matched by the same signature as today, so the same
edge is taken. Anything not found that way: None, the generator walks the whole body as today.
"""

import ast
import os

import pytest

from tests.test_joint_origin_layout import _load

edges = _load("predBoxEdges")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LINE = {"kind": "line", "start": [1.0, 2.0, 3.0], "end": [5.0, 2.0, 3.0]}
ARC = {"kind": "arc", "center": [0.0, 0.0, 1.0], "radius": 0.5, "start": [0.5, 0.0, 1.0], "end": [0.0, 0.5, 1.0]}
FACE = {"kind": "face", "min": [0.0, 0.0, 0.0], "max": [2.0, 4.0, 0.0]}


def test_the_probe_point_lies_on_the_item():
    assert edges.probePoint(LINE) == pytest.approx([3.0, 2.0, 3.0])
    assert edges.probePoint(ARC) == pytest.approx([0.5, 0.0, 1.0])
    assert edges.probePoint(FACE) == pytest.approx([1.0, 2.0, 0.0])


class _Edge:
    """A body's edge as its item form, with the body it belongs to"""
    def __init__(self, item, body="base"):
        self.item = item
        self.body = body


def _key(edge):
    return edge.item


def _finder(candidates):
    calls = []

    def find(item):
        calls.append(item)
        point = edges.probePoint(item)
        return [c for c in candidates if any(c.item.get(k) == point for k in ("start", "end"))
                or edges.probePoint(c.item) == point]
    return find, calls


def test_each_item_is_picked_by_its_signature_in_the_expected_order():
    other = _Edge({"kind": "line", "start": [3.0, 2.0, 3.0], "end": [3.0, 9.0, 3.0]})
    line = _Edge(dict(LINE, start=LINE["end"], end=LINE["start"]))   # drawn the other way round: same signature
    arc = _Edge(dict(ARC))
    neighbour = _Edge({"kind": "line", "start": [0.5, 0.0, 1.0], "end": [0.5, 0.0, 4.0]})
    find, calls = _finder([other, line, arc, neighbour])
    assert edges.pickByPoint([ARC, LINE], find, _key) == [arc, line]
    assert calls == [ARC, LINE]


def test_the_same_edges_as_the_walk_over_the_whole_body():
    body = [_Edge(dict(LINE)), _Edge(dict(ARC)), _Edge(dict(FACE)), _Edge({"kind": "line", "start": [9, 9, 9], "end": [9, 9, 8]})]
    find, _ = _finder(body)
    expected = [LINE, ARC, FACE]
    assert edges.pickByPoint(expected, find, _key) == edges.matchItems(expected, body, _key)


def test_one_item_not_found_gives_none_for_the_walk():
    find, _ = _finder([_Edge(dict(LINE))])
    assert edges.pickByPoint([LINE, ARC], find, _key) is None


def _source(*parts):
    return open(os.path.join(ROOT, *parts), encoding="utf-8").read()


def _method(source, cls, name):
    tree = ast.parse(source)
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
    return ast.unparse(next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == name))


GENERATOR = ("lib", "gridfinityUtils", "predBoxGenerator.py")


def test_the_generator_looks_up_by_point_and_walks_only_as_a_fallback():
    pick = _method(_source(*GENERATOR), "_Builder", "_pick")
    assert "self._lookup(" in pick and "fusionLists.items" not in pick
    lookup = _method(_source(*GENERATOR), "_Builder", "_lookup")
    assert "predBoxEdges.pickByPoint(" in lookup
    assert "predBoxEdges.matchItems(" in lookup and "fusionLists.items(" in lookup
    assert "debugLog(" in lookup
    near = _method(_source(*GENERATOR), "_Builder", "_near")
    assert "findBRepUsingPoint(" in near and ".body == body" in near


def test_the_floor_pad_blends_too():
    floorGrid = _method(_source(*GENERATOR), "_Builder", "floorGrid")
    assert "self._near(" in floorGrid
    assert "fusionLists.items(self.base.edges)" in floorGrid  # the fallback
