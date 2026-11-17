"""
Tests for grid placement: snapping extents to cells and greedily picking the free spot closest to the origin.
"""

import sys
import os
import types
import importlib.util
import pytest


def _load_placement_utils():
    # The modules annotate with adsk types, so they only need to exist
    fusion = sys.modules.get("adsk.fusion") or types.ModuleType("adsk.fusion")
    for name in ("BRepBody", "Design", "Component", "MoveFeature"):
        if not hasattr(fusion, name):
            setattr(fusion, name, type(name, (), {}))
    sys.modules["adsk.fusion"] = fusion
    sys.modules["adsk"].fusion = fusion

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    package = types.ModuleType("placementpkg")
    package.__path__ = []
    sys.modules["placementpkg"] = package

    def load(name):
        path = os.path.join(project_root, "lib", f"{name}.py")
        spec = importlib.util.spec_from_file_location(f"placementpkg.{name}", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[f"placementpkg.{name}"] = mod
        setattr(package, name, mod)
        spec.loader.exec_module(mod)
        return mod

    load("tagUtils")
    return load("placementUtils")


placementUtils = _load_placement_utils()

BASE = 4.2  # cm
CLEARANCE = 0.025  # cm


def binExtent(x, y, width, length):
    """Extent of a bin placed with its grid corner at cell (x, y)"""
    return (x * BASE, y * BASE, (x + width) * BASE - CLEARANCE * 2, (y + length) * BASE - CLEARANCE * 2)


def place(footprintCells, occupied):
    return placementUtils.findFreeGridOffset(footprintCells, occupied)


# ---------------------------------------------------------------------------
# extentToCells
# ---------------------------------------------------------------------------

def test_bin_extent_covers_exactly_its_cells():
    assert placementUtils.extentToCells(binExtent(0, 0, 2, 3), BASE, BASE) == (0, 0, 2, 3)


def test_moved_bin_extent_covers_exactly_its_cells():
    assert placementUtils.extentToCells(binExtent(3, 1, 1, 1), BASE, BASE) == (3, 1, 4, 2)


def test_extent_on_cell_border_does_not_spill_into_neighbour():
    assert placementUtils.extentToCells((0, 0, BASE * 2 + 1e-7, BASE), BASE, BASE) == (0, 0, 2, 1)


def test_off_grid_extent_snaps_outward():
    assert placementUtils.extentToCells((1.0, -0.5, 5.0, 2.0), BASE, BASE) == (0, -1, 2, 1)


def test_padding_reserves_whole_cells():
    padded = (-0.5, 0, BASE * 2 - CLEARANCE * 2 + 0.5, BASE)
    assert placementUtils.extentToCells(padded, BASE, BASE) == (-1, 0, 3, 1)


# ---------------------------------------------------------------------------
# findFreeGridOffset
# ---------------------------------------------------------------------------

def test_first_item_stays_at_origin():
    assert place((0, 0, 2, 2), []) == (0, 0)


def test_second_item_goes_next_to_first_along_x():
    assert place((0, 0, 1, 1), [(0, 0, 1, 1)]) == (1, 0)


def test_equal_items_gather_into_a_square():
    occupied = []
    for _ in range(4):
        (x, y) = place((0, 0, 1, 1), occupied)
        occupied.append((x, y, x + 1, y + 1))
    assert sorted(cells[:2] for cells in occupied) == [(0, 0), (0, 1), (1, 0), (1, 1)]


def test_gap_left_by_deleted_item_is_reused():
    occupied = [(1, 0, 2, 1), (0, 1, 1, 2), (1, 1, 2, 2)]
    assert place((0, 0, 1, 1), occupied) == (0, 0)


def test_large_item_fits_in_gap_only_when_it_is_big_enough():
    # 1x1 hole at (1, 0) surrounded by items, a 2x1 item can't use it
    occupied = [(0, 0, 1, 1), (2, 0, 3, 1), (0, 1, 3, 2)]
    (x, y) = place((0, 0, 2, 1), occupied)
    shifted = (x, y, x + 2, y + 1)
    assert not any(placementUtils.cellsOverlap(shifted, cells) for cells in occupied)
    assert place((0, 0, 1, 1), occupied) == (1, 0)


def test_long_item_settles_with_its_center_closest_to_origin():
    # a 1x1 at origin; a 3x1 item fits above (center 1.5, 1.5) closer than beside it (center 2.5, 0.5)
    assert place((0, 0, 3, 1), [(0, 0, 1, 1)]) == (0, 1)


def test_negative_footprint_start_from_padding():
    # padded footprint starts one cell left of its origin, stacking above beats shifting 3 cells right
    assert place((-1, 0, 2, 1), [(-1, 0, 2, 1)]) == (0, 1)


def test_items_away_from_origin_leave_origin_free():
    assert place((0, 0, 1, 1), [(5, 5, 6, 6)]) == (0, 0)


def test_non_square_cells_scale_distance():
    # wide cells make a step along y cheaper than along x
    assert placementUtils.findFreeGridOffset((0, 0, 1, 1), [(0, 0, 1, 1)], cellWidth=10, cellLength=1) == (0, 1)


def test_result_never_overlaps():
    occupied = [(0, 0, 3, 2), (3, 0, 4, 4), (0, 2, 2, 3), (5, 1, 7, 2)]
    for footprint in [(0, 0, 1, 1), (0, 0, 2, 2), (0, 0, 4, 1), (0, 0, 1, 5)]:
        (x, y) = place(footprint, occupied)
        assert x >= 0 and y >= 0
        shifted = (footprint[0] + x, footprint[1] + y, footprint[2] + x, footprint[3] + y)
        assert not any(placementUtils.cellsOverlap(shifted, cells) for cells in occupied)


# --- round 13 (p100): a new insert goes beside bins and baseplates too, not into the first bin at the origin

def test_placement_avoids_bins_and_baseplates(monkeypatch):
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class Box:
        def __init__(self, minX, minY, maxX, maxY):
            self.minPoint = Point(minX, minY)
            self.maxPoint = Point(maxX, maxY)

    root = object()

    class Body:
        def __init__(self, box):
            self.parentComponent = root
            self.boundingBox = box

    design = types.SimpleNamespace(rootComponent=root, allComponents=[])
    tagged = {"bin": [Body(Box(0, 0, 4.2, 4.2))], "baseplate": [], "label": []}
    monkeypatch.setattr(placementUtils.tagUtils, "findTaggedBodies", lambda d, tag: [(body, {}) for body in tagged[tag]])
    (x, y) = placementUtils.findPlacement(design, ["label", "bin", "baseplate"], "Gridfinity label", (0, 0, 3.6, 1.1), 4.2, 1.5)
    assert x >= 4.2 - 1e-9 or y >= 4.2 - 1e-9


def test_placement_with_a_single_tag_still_works(monkeypatch):
    root = object()
    design = types.SimpleNamespace(rootComponent=root, allComponents=[])
    monkeypatch.setattr(placementUtils.tagUtils, "findTaggedBodies", lambda d, tag: [])
    assert placementUtils.findPlacement(design, "bin", "Gridfinity bin ", (0, 0, 4.1, 4.1), 4.2, 4.2) == (0, 0)


# --- a box label taken out of the holder of a box rebuilt too narrow for it goes in front of the box (Nutzer
# 17.11.2026: "Schild vor die Front wäre besser. Sonst übersieht man es schnell."). cm, as in the code

LABEL = (7.05, 2.45)  # a 5 cells label lying flat: width along its x, height along its y
GAP = 1.0  # cm, placementUtils.FRONT_GAP
SET = [(0.0, 0.0, 14.0, 12.0), (2.5, -1.2, 11.5, 0.0)]  # box, handle sticking out in front (-y)


def test_the_front_gap_is_10_mm():
    assert placementUtils.FRONT_GAP == pytest.approx(GAP)


def test_a_label_goes_in_front_of_the_box_centred_on_its_middle():
    (x, y, turns) = placementUtils.frontPlacement((0, -1), (7.0, 0.73), SET, LABEL, GAP, [])
    assert x == pytest.approx(7.0)
    # in front of the handle, the part of the set furthest out, by the gap
    assert y == pytest.approx(-1.2 - GAP - 2.45 / 2)
    assert turns == 0


def test_the_box_itself_in_the_occupied_list_doesnt_block_the_spot():
    assert placementUtils.frontPlacement((0, -1), (7.0, 0.73), SET, LABEL, GAP, SET) is not None


def test_a_turned_box_gets_its_label_turned_along_its_front():
    # front towards +x: the box is turned a quarter to the left, the label lies along the wall, its height across
    (x, y, turns) = placementUtils.frontPlacement((1, 0), (13.27, 6.0), SET, LABEL, GAP, [])
    assert (x, y, turns) == (pytest.approx(14.0 + GAP + 2.45 / 2), pytest.approx(6.0), 1)
    (x, y, turns) = placementUtils.frontPlacement((0, 1), (7.0, 11.27), SET, LABEL, GAP, [])
    assert (x, y, turns) == (pytest.approx(7.0), pytest.approx(12.0 + GAP + 2.45 / 2), 2)
    (x, y, turns) = placementUtils.frontPlacement((-1, 0), (0.73, 6.0), SET, LABEL, GAP, [])
    assert (x, y, turns) == (pytest.approx(0.0 - GAP - 2.45 / 2), pytest.approx(6.0), 3)


def test_a_front_with_something_in_the_way_gives_no_spot():
    bin_in_front = (5.0, -6.0, 9.2, -1.8)
    assert placementUtils.frontPlacement((0, -1), (7.0, 0.73), SET, LABEL, GAP, [bin_in_front]) is None


def test_something_closer_than_the_gap_blocks_too():
    # the label would end at y = -2.2 - 2.45, a part 5 mm below that is within the gap
    just_below = (6.0, -6.0, 8.0, -2.2 - 2.45 - 0.5)
    assert placementUtils.frontPlacement((0, -1), (7.0, 0.73), SET, LABEL, GAP, [just_below]) is None


def test_something_beside_the_spot_doesnt_block_it():
    far_left = (-10.0, -6.0, -5.0, -1.8)
    assert placementUtils.frontPlacement((0, -1), (7.0, 0.73), SET, LABEL, GAP, [far_left]) is not None


def test_a_box_turned_off_the_grid_axes_gives_no_spot():
    assert placementUtils.frontPlacement((0.6, -0.8), (7.0, 0.73), SET, LABEL, GAP, []) is None


def test_no_box_extents_give_no_spot():
    assert placementUtils.frontPlacement((0, -1), (7.0, 0.73), [], LABEL, GAP, []) is None


def test_occupied_extents_can_leave_out_the_label_itself(monkeypatch):
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class Box:
        def __init__(self, minX, minY, maxX, maxY):
            self.minPoint = Point(minX, minY)
            self.maxPoint = Point(maxX, maxY)

    root = object()
    labelComponent = object()

    class Body:
        def __init__(self, box, component):
            self.parentComponent = component
            self.boundingBox = box
            self.name = "Box label"
            self.attributes = types.SimpleNamespace(itemByName=lambda group, name: None)

        def createForAssemblyContext(self, occurrence):
            return self

    class Occurrences(list):
        pass

    root = types.SimpleNamespace(allOccurrencesByComponent=lambda component: Occurrences([object()]))
    labelBody = Body(Box(0, 0, 7, 2.45), labelComponent)
    otherBody = Body(Box(20, 0, 27, 2.45), object())
    design = types.SimpleNamespace(rootComponent=root, allComponents=[types.SimpleNamespace(bRepBodies=[labelBody]), types.SimpleNamespace(bRepBodies=[otherBody])])
    monkeypatch.setattr(placementUtils.tagUtils, "findTaggedBodies", lambda d, tag: [])
    every = placementUtils.getOccupiedExtents(design, ["box"], "Box label")
    assert len(every) == 2
    skipped = placementUtils.getOccupiedExtents(design, ["box"], "Box label", skipComponents=[labelComponent])
    assert skipped == [(20, 0, 27, 2.45)]
