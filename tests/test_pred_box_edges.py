"""
Tests for carrying the edges of Pred's chamfers and fillets (read at 5 x 4 x 6, lib/gridfinityUtils/predBoxEdges.json)
over to other box sizes (round 27, p260). Every coordinate keeps its distance to what it hangs on in Pred's sketches:
the near side wall, the box middle, the label width, the bottom, the top or the middle height.
"""

import pytest

from tests.test_joint_origin_layout import _load

predBox = _load("predBox")
edges = _load("predBoxEdges")
DimKind = predBox.DimKind
Dim = predBox.Dim


def _values(gridX=5, gridY=4, heightU=6):
    return predBox.PredBoxDims(
        Dim(gridX, "gfBox1_baseWidth", DimKind.EXPRESSION),
        Dim(gridY, "gfBox1_baseLength", DimKind.EXPRESSION),
        Dim(heightU, "gfBox1_heightU", DimKind.EXPRESSION),
    ).values()


def _points(item):
    return [tuple(round(v * 10, 4) for v in item[key]) for key in ("start", "end", "center", "min", "max") if key in item]


def test_every_step_has_rules():
    assert set(edges.RULES) == set(edges.PRED_EDGES)


@pytest.mark.parametrize("step", sorted(edges.RULES))
def test_pred_size_keeps_pred_edges(step):
    expected = edges.expectedItems(step, _values())
    pred = [item for edgeSet in edges.PRED_EDGES[step] for item in edgeSet["items"]]
    assert [_points(item) for item in expected] == [_points(item) for item in pred]


def _find(step, values, predPoint):
    """The carried-over item whose Pred original has a point at predPoint (mm)"""
    pred = [item for edgeSet in edges.PRED_EDGES[step] for item in edgeSet["items"]]
    carried = edges.expectedItems(step, values)
    for original, item in zip(pred, carried):
        if predPoint in _points(original):
            return _points(item)
    raise AssertionError(f"{predPoint} not in {step}")


def test_side_cutout_edges_follow_the_walls_4x3x5():
    points = _find("#43 Fillet11", _values(4, 3, 5), (174, 0, 52.2))
    assert points == [(132, 0, 45.2), (132, 0, -2.8)]
    points = _find("#43 Fillet11", _values(4, 3, 5), (0, 132, -2.8))
    assert points == [(0, 90, -2.8), (0, 90, 45.2)]


def test_opening_tab_follows_the_label_width_6x3():
    assert _find("#22 Chamfer7", _values(6, 3, 6), (150.25, 2.5, 51.2)) == [(178.5, 2.5, 51.2), (93.5, 2.5, 51.2)]


def test_handle_holder_keeps_its_distance_to_the_label_edge():
    """Pred at 6 x 5 x 8 (r27_pred_size_6x5x8.txt): the handle holders move with the label edge (+13.75 mm), not
    with the middle (+21 mm)"""
    points = _find("#32 Chamfer26", _values(6, 5, 8), (60.25, 0, 34.7))
    assert points == [(74, 0, 41.7), (79, 0, 41.7)]
    points = _find("#32 Chamfer26", _values(7, 4, 5), (60.25, 0, 34.7))
    assert points == [(95, 0, 31.2), (100, 0, 31.2)]


def test_label_holder_line_ends_in_the_middle():
    # 6 wide: middle 136 mm, label 85 mm, the line starts 5 mm inside the label edge
    points = _find("#41 Chamfer30", _values(6, 3, 6), (115, 5, 10.95))
    assert points == [(136 - 42.5 + 5, 5, 10.95), (136, 5, 10.95)]


@pytest.mark.parametrize("heightU, slotEnd", [(5, 3.2), (6, 3.2), (8, 17.2)])
def test_catch_slide_end_follows_the_slot(heightU, slotEnd):
    top = _values(heightU=heightU)["bodyTop"] * 10
    points = _find("#54 Fillet2", _values(heightU=heightU), (1.75, 145.0, 3.2))
    assert points == [(1.75, 145.0, slotEnd), (1.75, 147.0, slotEnd)]
    points = _find("#54 Fillet2", _values(heightU=heightU), (1.75, 145.0, 48.2))
    assert points == [(1.75, 145.0, round(top - 4, 4)), (1.75, 147.0, round(top - 4, 4))]
    assert _find("#54 Fillet2", _values(heightU=heightU), (1.75, 147.0, 1.2))[0] == (1.75, 147.0, 1.2)


def test_lower_catch_tabs_stay_at_the_bottom():
    assert _find("#46 Chamfer1", _values(heightU=8), (38, 4, 2.2)) == [(38, 4, 2.2), (36, 4, 2.2)]
    assert _find("#46 Chamfer1", _values(heightU=8), (24, 4, 42.2)) == [(24, 4, 56.2), (26, 4, 56.2)]


def test_matching_picks_exactly_the_expected_edges():
    expected = edges.expectedItems("#24 Chamfer10", _values())
    shifted = [dict(item, center=[v + 0.1 for v in item["center"]]) if "center" in item
               else dict(item, start=[v + 0.1 for v in item["start"]], end=[v + 0.1 for v in item["end"]])
               for item in expected]
    candidates = list(reversed(expected)) + shifted
    picked = edges.matchItems(expected, candidates, key=lambda candidate: candidate)
    assert [_points(item) for item in picked] == [_points(item) for item in expected]


def test_matching_reports_a_missing_edge():
    expected = edges.expectedItems("#22 Chamfer7", _values())
    with pytest.raises(edges.EdgeNotFound, match="#22 Chamfer7|Chamfer7|line"):
        edges.matchItems(expected, [], key=lambda candidate: candidate)


def test_reversed_line_matches():
    [line] = edges.expectedItems("#22 Chamfer7", _values())
    reversed_ = dict(line, start=line["end"], end=line["start"])
    assert edges.matchItems([line], [reversed_], key=lambda candidate: candidate) == [reversed_]


def test_a_line_shortened_at_one_end_still_matches():
    """At height 5 the holders' top rounding is square (Jörg: "Rundung weglassen (2)"), the slanted line of the chamfer
    beside it reaches further: same start, same direction, other end"""
    [line] = edges.expectedItems("#22 Chamfer7", _values())
    longer = dict(line, end=[line["end"][0] - 0.05, line["end"][1], line["end"][2]])
    other = dict(line, start=[v + 0.01 for v in line["start"]])
    assert edges.matchItems([line], [other, longer], key=lambda candidate: candidate) == [longer]


def test_a_line_off_its_direction_does_not_match():
    [line] = edges.expectedItems("#22 Chamfer7", _values())
    bent = dict(line, end=[line["end"][0], line["end"][1] + 0.05, line["end"][2]])
    with pytest.raises(edges.EdgeNotFound):
        edges.matchItems([line], [bent], key=lambda candidate: candidate)
