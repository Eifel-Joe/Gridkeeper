"""
Walls of a bin that get a scoop (round 48, idea of upstream issue #140): one checkbox per wall, the back wall carries
the label tab and is locked while the tab is on.
"""

import os
import importlib.util


def _load_scoop_sides():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(project_root, "lib", "gridfinityUtils", "scoopSides.py")
    spec = importlib.util.spec_from_file_location("scoopSides", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scoops = _load_scoop_sides()
FRONT, BACK, LEFT, RIGHT = scoops.FRONT, scoops.BACK, scoops.LEFT, scoops.RIGHT


def test_no_wall_checked_no_scoop():
    assert scoops.scoopSides(False, False, False, False, hasTab=False) == frozenset()


def test_todays_single_scoop_is_the_front():
    assert scoops.scoopSides(True, False, False, False, hasTab=True) == frozenset({FRONT})


def test_every_wall_on_its_own():
    assert scoops.scoopSides(False, True, False, False, hasTab=False) == frozenset({BACK})
    assert scoops.scoopSides(False, False, True, False, hasTab=False) == frozenset({LEFT})
    assert scoops.scoopSides(False, False, False, True, hasTab=False) == frozenset({RIGHT})


def test_four_scoops_without_tab():
    assert scoops.scoopSides(True, True, True, True, hasTab=False) == frozenset({FRONT, BACK, LEFT, RIGHT})


def test_the_tab_locks_the_back_wall():
    assert scoops.scoopSides(True, True, True, True, hasTab=True) == frozenset({FRONT, LEFT, RIGHT})


def test_back_is_the_tab_wall():
    assert scoops.TAB_SIDE == BACK


def test_order_puts_the_back_first_for_the_bottom_fillet():
    # the bottom fillet of the cavity starts at the first wall without a scoop, the back one as before round 48
    assert scoops.SIDES_ORDER == (BACK, LEFT, RIGHT, FRONT)
    assert scoops.firstPlainSide(frozenset({FRONT})) == BACK
    assert scoops.firstPlainSide(frozenset({FRONT, BACK})) == LEFT
    assert scoops.firstPlainSide(frozenset({FRONT, BACK, LEFT, RIGHT})) is None


def _state(**flags):
    from types import SimpleNamespace
    values = dict(hasScoop=False, hasScoopBack=False, hasScoopLeft=False, hasScoopRight=False, hasTab=False)
    values.update(flags)
    return SimpleNamespace(**values)


def test_sides_of_a_dialog_state():
    state = _state(hasScoop=True, hasScoopBack=True, hasScoopRight=True, hasTab=True)
    assert scoops.stateScoopSides(state, buildsScoop=True) == frozenset({FRONT, RIGHT})


def test_shelled_solid_or_shaped_bins_build_none():
    state = _state(hasScoop=True, hasScoopLeft=True)
    assert scoops.stateScoopSides(state, buildsScoop=False) == frozenset()


def test_wall_insets_take_the_scoop_inset_on_scoop_walls():
    # the scoop runs up into the lip, its wall reaches to the lip's inner edge (as the front did before round 48)
    insets = scoops.wallInsets(frozenset({FRONT, LEFT}), 1.2, 2.6)
    assert insets == {FRONT: 2.6, BACK: 1.2, LEFT: 2.6, RIGHT: 1.2}


def test_wall_insets_without_scoops_are_the_wall():
    assert set(scoops.wallInsets(frozenset(), 1.2, 2.6).values()) == {1.2}


BOX_MIN, BOX_MAX = (0.0, 0.0), (10.0, 6.0)


def touches(edgeMin, edgeMax, sides):
    return scoops.touchesScoopWall(edgeMin, edgeMax, BOX_MIN, BOX_MAX, sides)


def test_front_line_and_its_corner_arcs_touch_the_front_scoop():
    sides = frozenset({FRONT})
    assert touches((0.5, 0.0), (9.5, 0.0), sides)          # front line
    assert touches((0.0, 0.0), (0.5, 0.5), sides)          # front left arc
    assert touches((9.5, 0.0), (10.0, 0.5), sides)         # front right arc
    assert not touches((0.0, 0.5), (0.0, 5.5), sides)     # left line
    assert not touches((0.0, 5.5), (0.5, 6.0), sides)     # back left arc
    assert not touches((0.5, 6.0), (9.5, 6.0), sides)     # back line


def test_every_scoop_wall_is_touched():
    sides = frozenset({BACK, LEFT, RIGHT})
    assert touches((0.5, 6.0), (9.5, 6.0), sides)
    assert touches((0.0, 0.5), (0.0, 5.5), sides)
    assert touches((10.0, 0.5), (10.0, 5.5), sides)
    assert touches((0.0, 0.0), (0.5, 0.5), sides)          # front left arc meets the left scoop
    assert not touches((0.5, 0.0), (9.5, 0.0), sides)     # front line


def test_generators_take_the_scoop_walls_not_a_single_flag():
    # round 48: a single hasScoop read anywhere in the generators would build the front scoop only
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(project_root, "lib", "gridfinityUtils")
    readers = []
    for name in sorted(os.listdir(folder)):
        # scoopSides reads the dialog's flags into the walls
        if name.endswith(".py") and name != "scoopSides.py":
            with open(os.path.join(folder, name), encoding="utf-8") as file:
                if "hasScoop" in file.read():
                    readers.append(name)
    assert readers == []


def test_bin_builder_passes_the_scoop_walls():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(project_root, "commands", "commandCreateBin", "binBuilder.py"), encoding="utf-8") as file:
        source = file.read()
    # the bin's walls reach each compartment, the outer walls follow them (addendum: per compartment)
    assert "binScoopSides(state), hasTab=state.hasTab)" in source
    assert "binBodyInput.hasScoop" not in source


# --- addendum: scoops per compartment and the radius limit

def test_a_compartment_without_own_scoops_takes_the_bins():
    assert scoops.compartmentScoopSides(None, frozenset({FRONT, LEFT}), hasTab=False) == frozenset({FRONT, LEFT})


def test_own_scoops_replace_the_bins():
    assert scoops.compartmentScoopSides(["right"], frozenset({FRONT}), hasTab=False) == frozenset({RIGHT})
    assert scoops.compartmentScoopSides([], frozenset({FRONT}), hasTab=False) == frozenset()


def test_the_tab_locks_the_back_of_every_compartment():
    # every compartment carries its own tab on its back wall
    assert scoops.compartmentScoopSides(["back", "front"], frozenset(), hasTab=True) == frozenset({FRONT})
    assert scoops.compartmentScoopSides(["back"], frozenset(), hasTab=False) == frozenset({BACK})


def test_outer_walls_where_any_compartment_scoops():
    # 3 columns, 2 rows: (x, y, width, length, sides)
    compartments = [
        (0, 0, 1, 1, frozenset({FRONT, LEFT})),
        (1, 0, 1, 2, frozenset({BACK})),
        (2, 0, 1, 1, frozenset({LEFT})),         # a divider, not the bin's left wall
        (0, 1, 1, 1, frozenset()),
        (2, 1, 1, 1, frozenset({RIGHT})),
    ]
    assert scoops.outerScoopWalls(compartments, 3, 2) == frozenset({FRONT, LEFT, BACK, RIGHT})
    assert scoops.outerScoopWalls(compartments[2:3], 3, 2) == frozenset()


def test_radius_is_limited_only_between_two_scoops_on_an_axis():
    assert scoops.scoopRadiusSpanLimits(frozenset({FRONT}), 30.0, 20.0, 0.5) == []
    assert scoops.scoopRadiusSpanLimits(frozenset({FRONT, LEFT}), 30.0, 20.0, 0.5) == []
    assert scoops.scoopRadiusSpanLimits(frozenset({FRONT, BACK}), 30.0, 20.0, 0.5) == [9.5]
    assert scoops.scoopRadiusSpanLimits(frozenset({FRONT, BACK, LEFT, RIGHT}), 30.0, 20.0, 0.5) == [9.5, 14.5]


def test_generator_scoops_each_compartment_with_its_own_walls():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    def source(*path):
        with open(os.path.join(project_root, *path), encoding="utf-8") as file:
            return file.read()
    generator = source("lib", "gridfinityUtils", "binBodyGenerator.py")
    assert "compartment.scoopSides," in generator
    builder = source("commands", "commandCreateBin", "binBuilder.py")
    assert "compartment.scoopSides = scoopSides.compartmentScoopSides(" in builder
    assert "binBodyInput.scoopSides = scoopSides.outerScoopWalls(" in builder
    cutout = source("lib", "gridfinityUtils", "binBodyCutoutGenerator.py")
    assert "scoopSides.scoopRadiusSpanLimits(" in cutout


def test_tab_openings_reach_through_a_wall_thickened_for_a_scoop():
    # review round 48: a side scoop puts the cavity at the lip's inner edge, the opening must still reach the outside
    assert scoops.tabOpeningDepth({FRONT: 2.6, BACK: 1.2, LEFT: 2.6, RIGHT: 1.2}, 1.2) == 3.8
    # without a scoop on the opened walls as before round 48, twice the wall
    assert scoops.tabOpeningDepth({FRONT: 2.6, BACK: 1.2, LEFT: 1.2, RIGHT: 1.2}, 1.2) == 2.4


def test_chamfer_box_bounds_come_from_its_placement():
    # review round 48: the box's own placement, not a face bounding box Fusion may draw loose
    assert scoops.boxBounds((1.0, 2.0), 10.0, 6.0) == ((1.0, 2.0), (11.0, 8.0))
