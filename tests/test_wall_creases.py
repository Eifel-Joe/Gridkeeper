"""
Tests for laying out the creases stiffening long bin walls.
"""

import os
import sys
import types
import importlib.util

import pytest


def _load_wall_creases():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(project_root, "lib", "gridfinityUtils")
    # a package of its own, so the relative import of binShape resolves without the Fusion modules
    package = types.ModuleType("creasesPackage")
    package.__path__ = [folder]
    sys.modules["creasesPackage"] = package
    for name in ["binShape", "scoopSides", "wallCreases"]:
        spec = importlib.util.spec_from_file_location(f"creasesPackage.{name}", os.path.join(folder, f"{name}.py"))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[f"creasesPackage.{name}"] = mod
        spec.loader.exec_module(mod)
    return sys.modules["creasesPackage.wallCreases"]


creases = _load_wall_creases()
WallSide = creases.WallSide


def test_rectangle_sides_point_inwards():
    cells = [(x, y) for x in range(3) for y in range(2)]
    assert creases.wallSides(cells) == [
        WallSide('x', 0, 1, 0, 3),
        WallSide('y', 3, -1, 0, 2),
        WallSide('x', 2, -1, 0, 3),
        WallSide('y', 0, 1, 0, 2),
    ]


def test_l_sides_include_the_notch():
    sides = creases.wallSides([(0, 0), (1, 0), (0, 1), (0, 2)])
    assert WallSide('x', 1, -1, 1, 2) in sides
    assert WallSide('y', 1, -1, 1, 3) in sides
    assert len(sides) == 6


scoops = sys.modules["creasesPackage.scoopSides"]


def test_walls_of_a_plain_bin_are_named_for_their_scoop():
    sides = creases.wallSides([(x, y) for x in range(2) for y in range(2)])
    assert [creases.scoopWall(side) for side in sides] == [scoops.FRONT, scoops.RIGHT, scoops.BACK, scoops.LEFT]


def test_straight_length_leaves_the_corner_arcs():
    assert creases.straightLength(WallSide('x', 0, 1, 0, 3), 4.2, 0.4) == pytest.approx(11.8)


def layout(columns, rows, scoopSides=frozenset()):
    # creases from about 120 mm, panels up to about 200 mm, both in feet
    cells = [(x, y) for x in range(columns) for y in range(rows)]
    return creases.creaseLayout(cells, 4.2, 4.2, 2.85, 4.75, scoopSides)


def test_short_bins_get_no_creases():
    assert layout(2, 2) == []


def test_three_feet_are_enough():
    assert [count for (_, count) in layout(3, 1)] == [1, 1]


def test_walls_shorter_than_a_panel_of_the_longest_stay_flat():
    # 210 mm split in two panels of 105 mm, the 84 mm ends are too short for one
    assert layout(5, 2) == [(WallSide('x', 0, 1, 0, 5), 2), (WallSide('x', 2, -1, 0, 5), 2)]


def test_walls_as_long_as_a_panel_stretch_theirs():
    # 252 mm split in two panels of 126 mm, the ends are as long, corners included
    assert [count for (_, count) in layout(6, 3)] == [2, 1, 2, 1]
    # the 294 mm long walls get two panels, the 252 mm ends two as well
    assert [count for (_, count) in layout(7, 6)] == [2, 2, 2, 2]


def test_scoop_side_is_left_out():
    assert layout(5, 2, frozenset({scoops.FRONT})) == [(WallSide('x', 2, -1, 0, 5), 2)]


def test_every_scoop_wall_is_left_out():
    # round 48: a scoop braces its wall, whichever it is
    assert layout(5, 2, frozenset({scoops.BACK})) == [(WallSide('x', 0, 1, 0, 5), 2)]
    assert layout(5, 2, frozenset({scoops.FRONT, scoops.BACK})) == []
    assert [side for (side, _) in layout(6, 3, frozenset({scoops.LEFT, scoops.RIGHT}))] == [
        WallSide('x', 0, 1, 0, 6), WallSide('x', 3, -1, 0, 6)]
