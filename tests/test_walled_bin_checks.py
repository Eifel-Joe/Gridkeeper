"""
Tests for which bins the checks on walls and dividers look at: a bin built without its body is feet only, cutting a
section through a foot made Fusion fail the divider gap check of the case "bin_2x1_base_only".
"""

import os
import importlib.util
from types import SimpleNamespace


def _load(name, *path):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location(name, os.path.join(project_root, *path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


testCases = _load("testCases", "commands", "commandSnapshotTests", "testCases.py")


def test_a_bin_with_its_body_has_walls():
    assert testCases.hasWalls(testCases.GENERATOR_BIN, SimpleNamespace(generateBody=True))


def test_a_bin_of_feet_only_has_no_walls():
    assert not testCases.hasWalls(testCases.GENERATOR_BIN, SimpleNamespace(generateBody=False))


def test_a_state_without_the_setting_is_a_whole_bin():
    assert testCases.hasWalls(testCases.GENERATOR_BIN, SimpleNamespace())


def test_other_generators_have_no_bin_walls_to_check():
    for generator in (testCases.GENERATOR_BASEPLATE, testCases.GENERATOR_LABEL, testCases.GENERATOR_BOX):
        assert not testCases.hasWalls(generator, SimpleNamespace(generateBody=True))


# A bin of one compartment has no divider: the gap check took the engraved icon in the top of its label tab, a thin
# stretch on a level section, for one, and the recess of the icon for a 3 mm gap to the wall
# (bin_2x1x4_hollow_tab_open_sides; the same with the sides closed)
def test_a_bin_of_one_compartment_has_no_dividers():
    assert not testCases.hasDividers(SimpleNamespace(compartmentsX=1, compartmentsY=1))
    assert not testCases.hasDividers(SimpleNamespace())


def test_a_bin_of_more_compartments_has_dividers():
    assert testCases.hasDividers(SimpleNamespace(compartmentsX=2, compartmentsY=1))
    assert testCases.hasDividers(SimpleNamespace(compartmentsX=1, compartmentsY=3))
