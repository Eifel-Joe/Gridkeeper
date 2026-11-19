"""
Walls of a bin that get a scoop (round 48, idea of upstream issue #140): one checkbox per wall, the back wall carries
the label tab and is locked while the tab is on.
"""

import os
import pytest
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


def test_bottom_fillet_only_beside_a_single_scoop():
    # Fusion 19.11.: a floor fillet chain whose ends run into two different scoops fails (FILLET_NO_EDGE_FOUND), with
    # or without its tangent chain: front+back, front+left+right, front+left all failed; front only and left only
    # build, their chain ends at the same scoop on both ends. More than one scoop keeps sharp floor edges
    assert scoops.bottomFilletSides(frozenset()) == [BACK, LEFT, RIGHT, FRONT]
    assert scoops.bottomFilletSides(frozenset({FRONT})) == [BACK, LEFT, RIGHT]
    assert scoops.bottomFilletSides(frozenset({LEFT})) == [BACK, RIGHT, FRONT]
    assert scoops.bottomFilletSides(frozenset({FRONT, BACK})) == []
    assert scoops.bottomFilletSides(frozenset({FRONT, LEFT, RIGHT})) == []
    assert scoops.bottomFilletSides(frozenset({FRONT, LEFT})) == []
    assert scoops.bottomFilletSides(frozenset({FRONT, BACK, LEFT, RIGHT})) == []

# Round 50, p650: with dividers up to the top the compartment grid keeps to the grid lines beside a scoop wall, the
# outer row or column takes the scoop wall's inset. In cm: 1.2 mm wall, full lip inner inset 2.6 mm
WALL = 0.12
FULL_INSET = 0.26


def test_without_keeping_the_grid_a_scoop_wall_moves_the_grid_as_in_round_48():
    (gridInsets, trims) = scoops.gridTrims(frozenset({FRONT}), WALL, FULL_INSET, keepGrid=False)
    assert gridInsets == {BACK: WALL, LEFT: WALL, RIGHT: WALL, FRONT: FULL_INSET}
    assert trims == {BACK: 0, LEFT: 0, RIGHT: 0, FRONT: 0}


def test_keeping_the_grid_lays_it_out_from_the_walls_and_trims_the_scoop_wall():
    (gridInsets, trims) = scoops.gridTrims(frozenset({FRONT, RIGHT}), WALL, FULL_INSET, keepGrid=True)
    assert gridInsets == {BACK: WALL, LEFT: WALL, RIGHT: WALL, FRONT: WALL}
    assert trims[FRONT] == pytest.approx(0.14)
    assert trims[RIGHT] == pytest.approx(0.14)
    assert trims[BACK] == 0 and trims[LEFT] == 0


def test_only_the_outer_row_along_a_scoop_wall_is_trimmed():
    trims = {FRONT: 0.14, BACK: 0, LEFT: 0, RIGHT: 0}
    # a 2x3 grid, cells 4 cm by 4 cm, compartment at column 1, row 0 and one at row 1
    (x, y, width, length) = scoops.trimmedCavity(4.2, 0.12, 4.0, 4.0, (1, 0), (1, 1), (2, 3), trims)
    assert (x, y, width, length) == pytest.approx((4.2, 0.26, 4.0, 3.86))
    assert scoops.trimmedCavity(4.2, 4.24, 4.0, 4.0, (1, 1), (1, 1), (2, 3), trims) == pytest.approx((4.2, 4.24, 4.0, 4.0))


def test_a_compartment_over_all_rows_is_trimmed_at_both_ends():
    trims = {FRONT: 0.14, BACK: 0.07, LEFT: 0.1, RIGHT: 0.2}
    (x, y, width, length) = scoops.trimmedCavity(0.12, 0.12, 8.0, 12.0, (0, 0), (2, 3), (2, 3), trims)
    assert (x, y, width, length) == pytest.approx((0.22, 0.26, 7.7, 11.79))


def test_compartments_stay_alike_for_the_pattern_only_when_every_one_touches_the_trimmed_walls():
    none = {FRONT: 0, BACK: 0, LEFT: 0, RIGHT: 0}
    front = {**none, FRONT: 0.14}
    left = {**none, LEFT: 0.14}
    assert scoops.trimsKeepAlike(none, (2, 3))
    # a single row: every compartment touches the front wall
    assert scoops.trimsKeepAlike(front, (3, 1))
    assert not scoops.trimsKeepAlike(front, (2, 3))
    assert scoops.trimsKeepAlike(left, (1, 3))
    assert not scoops.trimsKeepAlike(left, (2, 1))


def test_the_grid_trims_work_on_dims():
    """The generator places cavities with Dims, which take no bare 0 in a sum"""
    from tests.test_dim import Dim
    wall = Dim.length(WALL)
    (gridInsets, trims) = scoops.gridTrims(frozenset({FRONT}), wall, Dim.length(FULL_INSET), keepGrid=True)
    assert gridInsets[FRONT].value == pytest.approx(WALL)
    (x, y, width, length) = scoops.trimmedCavity(wall, wall, Dim.length(4.0), Dim.length(4.0), (0, 0), (1, 1), (2, 3), trims)
    assert (x.value, y.value, width.value, length.value) == pytest.approx((WALL, FULL_INSET, 4.0, 3.86))
    assert not scoops.trimsKeepAlike(trims, (2, 3))


def test_a_corner_of_a_cell_along_a_trimmed_wall_moves_in_by_the_trim():
    trims = {FRONT: 0.14, BACK: 0, LEFT: 0, RIGHT: 0.07}
    # the front corners of the front row
    assert scoops.cornerTrim(0, 0, -1, -1, (2, 3), trims) == (None, 0.14)
    # a back corner of the front row lies on a divider, untrimmed
    assert scoops.cornerTrim(0, 0, -1, 1, (2, 3), trims) == (None, None)
    # the right column's right corner, its front one too
    assert scoops.cornerTrim(1, 1, 1, 1, (2, 3), trims) == (0.07, None)
    assert scoops.cornerTrim(1, 0, 1, -1, (2, 3), trims) == (0.07, 0.14)


def test_a_raised_divider_starts_at_the_trimmed_cavity_of_a_scoop_wall():
    """Its box starts half a wall short of the cavity as before round 50: at a scoop wall that is the trimmed cavity's
    edge, not the grid's, so it doesn't reach out under the lip (near coincident faces with the lip, shown in Fusion)"""
    trims = {FRONT: 0.07, BACK: 0, LEFT: 0, RIGHT: 0.14}
    # a wall across x runs along y, from the front to the back
    assert scoops.runTrims('x', 0, 3, (2, 3), trims) == (0.07, None)
    assert scoops.runTrims('x', 1, 2, (2, 3), trims) == (None, None)
    # a wall across y runs along x, from the left to the right
    assert scoops.runTrims('y', 0, 2, (2, 3), trims) == (None, 0.14)


def test_the_cavities_start_at_the_trimmed_grid_and_never_inside_a_thicker_wall():
    """The compartments top clearance spans the cavities: from the scoop inset where trimmed, from the wall where the
    wall is thicker than the inset (review round 50: a 3 mm wall under a light lip, 1.9 mm inset, got a step cut 1.1 mm
    into the front wall)"""
    (gridInsets, trims) = scoops.gridTrims(frozenset({FRONT}), 0.12, FULL_INSET, keepGrid=True)
    assert scoops.cavityInsets(gridInsets, trims)[FRONT] == pytest.approx(FULL_INSET)
    assert scoops.cavityInsets(gridInsets, trims)[BACK] == pytest.approx(0.12)
    (gridInsets, trims) = scoops.gridTrims(frozenset({FRONT}), 0.3, 0.19, keepGrid=True)
    assert scoops.cavityInsets(gridInsets, trims)[FRONT] == pytest.approx(0.3)
    # without keeping the grid as round 48: the scoop inset, also inside a thicker wall
    (gridInsets, trims) = scoops.gridTrims(frozenset({FRONT}), 0.3, 0.19, keepGrid=False)
    assert scoops.cavityInsets(gridInsets, trims)[FRONT] == pytest.approx(0.19)


def test_the_floor_fillet_is_no_rounder_than_the_tightest_corner():
    """Round 50: a bottom fillet of 2.55 mm running into a corner of 2.25 mm failed in Fusion (FILLET_NO_EDGE_FOUND)"""
    assert scoops.floorFilletRadius(0.255, None) == pytest.approx(0.255)
    assert scoops.floorFilletRadius(0.255, {('right', 'front'): 0.2246, ('left', 'back'): 0.255}) == pytest.approx(0.2246)
    # sharp corners, a sharp floor
    assert scoops.floorFilletRadius(0.255, {('right', 'front'): 0, ('left', 'back'): 0.2}) == 0


# p652 (round 50): a cavity with a scoop shallower than its corner radius, 1 mm in a bin one unit high
def test_the_floor_fillet_beside_a_scoop_fits_the_cavity_depth():
    # 2.55 mm failed in Fusion at 1.0 mm depth (ASM_BL_CAP_COMPLEX), 0.9 mm built
    assert scoops.scoopFloorRadius(0.255, 0.1, frozenset({FRONT}), margin=0.01) == pytest.approx(0.1 - 0.01)
    # deep enough, or without a scoop, the radius stays
    assert scoops.scoopFloorRadius(0.255, 2.9, frozenset({FRONT}), margin=0.01) == pytest.approx(0.255)
    assert scoops.scoopFloorRadius(0.255, 0.1, frozenset(), margin=0.01) == pytest.approx(0.255)


# p653 (round 50): a cavity corner between two scoop walls follows the lip's inner corner there
def test_a_corner_between_two_scoop_walls_is_concentric_with_the_lip():
    # bin corner 4 mm, full lip inset 2.6 mm: 1.4 mm instead of 2.55 mm
    assert scoops.scoopCornerRadius(0.255, 0.4, 0.26) == pytest.approx(0.14)
    # a light lip's 1.9 mm inset leaves 2.1 mm
    assert scoops.scoopCornerRadius(0.255, 0.4, 0.19) == pytest.approx(0.21)
    # never rounder than the compartment's corners
    assert scoops.scoopCornerRadius(0.255, 0.4, 0.1) == pytest.approx(0.255)


def test_only_corners_between_two_trimmed_scoop_walls_follow_the_lip():
    walls = frozenset({FRONT, LEFT})
    assert scoops.scoopWallCorners(walls, (0, 0), (1, 1), (2, 3)) == {(LEFT, FRONT)}
    # a compartment along one of them only, or a bin with one scoop wall
    assert scoops.scoopWallCorners(walls, (1, 0), (1, 1), (2, 3)) == set()
    assert scoops.scoopWallCorners(frozenset({FRONT}), (0, 0), (2, 3), (2, 3)) == set()
    # a compartment over the whole grid has all four corners on the walls
    assert scoops.scoopWallCorners(frozenset({FRONT, BACK, LEFT, RIGHT}), (0, 0), (2, 3), (2, 3)) == {
        (LEFT, FRONT), (LEFT, BACK), (RIGHT, FRONT), (RIGHT, BACK)}
