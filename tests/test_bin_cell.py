"""
A new bin jointed into a cell of a baseplate or of the floor of a box (round 31, p312): which joint origins are cells,
the joint's name, where the bin's own placement joint origin sits and when the dialog offers the pick.
binCell has no Fusion import, so it is loaded as a plain file.
"""

import os
import importlib.util

import pytest

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "gridfinityUtils", "binCell.py")
spec = importlib.util.spec_from_file_location("binCellUnderTest", PATH)
binCell = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binCell)


@pytest.mark.parametrize("name, cell", [
    ("Socket joint origin 2-3", (2, 3)),
    ("Cell joint origin 1-1", (1, 1)),
    ("Socket joint origin 12-10", (12, 10)),
])
def test_cells_of_baseplates_and_boxes(name, cell):
    assert binCell.cellOf(name) == cell


@pytest.mark.parametrize("name", [
    "Foot joint origin 1-1",
    "Pocket joint origin 1",
    "Cell placement joint origin",
    "Cell joint origin plane 1",
    "Stack top joint origin",
    "Socket joint origin 1-1 (1)",
    "",
])
def test_other_joint_origins_are_no_cells(name):
    assert binCell.cellOf(name) is None


def test_the_placement_joint_origin_is_no_cell():
    assert binCell.cellOf(binCell.PLACEMENT_JOINT_ORIGIN) is None


def test_joint_name():
    assert binCell.cellJointName("Bin 2x1x3") == "Bin 2x1x3 in cell"


@pytest.mark.parametrize("name, isCell", [
    ("Bin 2x1x3 in cell", True),
    ("Bin 2x1x3 in cell (2)", True),
    ("Insert 1u in pocket", False),
    ("Bin in cell holder", False),
])
def test_cell_joint_names(name, isCell):
    assert binCell.isCellJointName(name) is isCell


@pytest.mark.parametrize("isNewBin, hasParts, offered", [
    (True, True, True),
    (True, False, False),
    (False, True, False),
    (False, False, False),
])
def test_the_pick_is_offered_for_new_bins_with_a_baseplate_or_box(isNewBin, hasParts, offered):
    assert binCell.offersCellPick(isNewBin, hasParts) is offered


# --- round 38: upstream's Placement (snap or center, d37c166) joined with the cell in one group ---

@pytest.mark.parametrize("isCentered, hasCell, hasKeptPlacement, source", [
    (False, True, False, "cell"),
    # a picked cell wins over Center on origin, also when a bin in a cell is rebuilt with it
    (True, True, True, "cell"),
    # a centered bin is centered again when rebuilt, its size may have changed (upstream)
    (True, False, True, "center"),
    (True, False, False, "center"),
    (False, False, True, "kept"),
    (False, False, False, "snap"),
])
def test_where_a_bin_goes(isCentered, hasCell, hasKeptPlacement, source):
    assert binCell.placementSource(isCentered, hasCell, hasKeptPlacement) == source


@pytest.mark.parametrize("hasCell, enabled", [(False, True), (True, False)])
def test_the_position_is_greyed_out_while_a_cell_is_picked(hasCell, enabled):
    assert binCell.positionEnabled(hasCell) is enabled


@pytest.mark.parametrize("position, hasCell, stored", [
    ("Center on origin", False, "Center on origin"),
    ("Snap to free spot", False, "Snap to free spot"),
    # a bin in a cell keeps no centering: should its cell go, it stays where it was instead of jumping (review round 38)
    ("Center on origin", True, "Snap to free spot"),
])
def test_a_bin_in_a_cell_is_stored_as_snapped(position, hasCell, stored):
    assert binCell.storedPosition(position, hasCell, "Snap to free spot") == stored
