"""
Round 38: upstream's Placement dropdown (snap or center, d37c166) sits in the fork's Placement group with the cell
(round 31). The group is always there, the cell only where binCell.offersCellPick says, the dropdown is called
Position and greyed out while a cell is picked. entry.py needs Fusion to load, so the tests read its source.
"""

import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRY = os.path.join(ROOT, "commands", "commandCreateBin", "entry.py")


def _function(name):
    tree = ast.parse(open(ENTRY, encoding="utf-8").read())
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def _source(name):
    return ast.unparse(_function(name))


def test_the_placement_group_is_always_there_with_the_position_in_it():
    source = _source("command_created")
    group = source.index("placementGroup = inputs.addGroupCommandInput(BIN_PLACEMENT_GROUP_ID, 'Placement')")
    offer = source.index("if binCell.offersCellPick(")
    position = source.index("placementGroup.children.addDropDownCommandInput(BIN_PLACEMENT_INPUT_ID, 'Position'")
    assert group < offer
    assert "binDimensionsGroup.children.addDropDownCommandInput(BIN_PLACEMENT_INPUT_ID" not in source
    # the cell stays under the offer, the position isn't
    assert "placementGroup.children.addSelectionInput(BIN_CELL_INPUT_ID" in source[offer:position]


def test_the_settings_leave_out_the_cell_but_show_the_position():
    source = _source("snapshotSettings")
    assert "BIN_CELL_INPUT_ID" in source
    assert "BIN_PLACEMENT_GROUP_ID" not in source


def test_picking_a_cell_greys_the_position_out():
    source = _source("updatePositionInput")
    assert "binCell.positionEnabled(selectedCell(inputs) is not None)" in source
    changed = _source("command_input_changed")
    assert "updatePositionInput(" in changed
