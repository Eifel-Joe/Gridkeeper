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
