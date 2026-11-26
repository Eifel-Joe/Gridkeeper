"""
The box label command (round 29, p262, dev-notes/r29/boxlabel-plan.md): a menu command of its own (17.11.2026: so a label can be swapped), the label jointed into the holder
of a chosen box, or beside the parts there are without one. entry.py and boxLabelBuilder.py need Fusion to load, so
their source is read; the plain parts are loaded.
"""

import ast
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(ROOT, "commands", "commandCreateBoxLabel")
ENTRY = os.path.join(FOLDER, "entry.py")
BUILDER = os.path.join(FOLDER, "boxLabelBuilder.py")


def _function(path, name):
    tree = ast.parse(open(path, encoding="utf-8").read())
    return ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name))


def _state_module():
    spec = importlib.util.spec_from_file_location("boxLabelInputState", os.path.join(FOLDER, "inputState.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_the_command_is_registered_in_the_menu():
    source = open(os.path.join(ROOT, "commands", "__init__.py"), encoding="utf-8").read()
    assert "from .commandCreateBoxLabel import entry as commandCreateBoxLabel" in source
    tree = ast.parse(source)
    commands = next(node for node in tree.body if isinstance(node, ast.Assign) and ast.unparse(node.targets[0]) == "commands")
    names = [ast.unparse(element) for element in commands.value.elts]
    assert names.index("commandCreateBoxLabel") == names.index("commandCreateBox") + 1


def test_the_command_has_its_own_id_name_and_icons():
    source = open(ENTRY, encoding="utf-8").read()
    assert "CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdBoxLabel'" in source
    assert "CMD_NAME = 'Gridkeeper box label'" in source
    for size in ("16x16.png", "32x32.png", "64x64.png"):
        assert os.path.isfile(os.path.join(FOLDER, "resources", size))


def test_the_state_holds_text_symbols_and_look():
    state = _state_module().InputState(cells=5, bigText="M3", line1="Socket", line2="DIN 912", symbols=["None"] * 5,
                                       textStyle="Heavy", surface="Embossed", textColor="")
    assert state.symbols == ["None"] * 5


def test_five_symbol_dropdowns_from_the_symbol_choices():
    source = _function(ENTRY, "command_created")
    assert "for index, inputId in enumerate(SYMBOL_DROPDOWNS)" in source
    assert "symbolNames()" in source
    assert "len(SYMBOL_DROPDOWNS) == predBoxLabelLayout.MAX_SYMBOLS" in open(ENTRY, encoding="utf-8").read()


def test_only_a_box_label_joint_origin_can_be_picked():
    source = _function(ENTRY, "command_select")
    assert "isBoxLabelJointOrigin" in source


def test_the_width_is_a_choice_of_preds_fixed_widths():
    """17.11.2026: the label has fixed widths, so the width is a choice menu, not a free setting.
    It works without a box in the document (a reprint)"""
    source = _function(ENTRY, "command_created")
    assert "widthDropdown = addDropdown(boxGroup.children, WIDTH_DROPDOWN, tr('Label width'), [name for name, _ in predBoxLabelLayout.widthChoices()])" in source
    assert "addIntegerSpinnerCommandInput" not in open(ENTRY, encoding="utf-8").read()
    assert "cells=predBoxLabelLayout.cellsOfChoice(uiState.getState(WIDTH_DROPDOWN))" in _function(ENTRY, "getInputsState")


def test_a_picked_box_preselects_its_width():
    """A width can also be taken over when a joint is picked to position the label"""
    source = _function(ENTRY, "command_input_changed")
    assert "if changed_input.id == BOX_INPUT:" in source
    assert "predBoxLabelLayout.widthChoiceFor(cells)" in source
    assert "uiState.setValue(WIDTH_DROPDOWN" in source


def test_the_cells_come_from_the_boxs_outer_width():
    source = _function(BUILDER, "boxCells")
    # cells x 42 mm + 20 mm, the rule is shared with the box rebuild's width note, see test_box_label_rebuild
    assert "predBoxLabelLayout.cellsOfBoxWidth(" in source


def test_the_builder_joints_the_label_into_the_holder():
    source = _function(BUILDER, "_buildBoxLabel")
    assert "predBoxLabel.createBoxLabel(" in source
    assert "root.joints.createInput(assembly.inContext(jointOrigin, occurrence), box)" in source
    assert "setAsRigidJointMotion()" in source


def test_without_a_box_the_label_lies_beside_the_parts():
    source = _function(BUILDER, "_buildBoxLabel")
    assert "placementUtils.findPlacement(" in source
    assert "tagUtils.TAG_BOX" in source


def test_text_parameters_drive_the_texts():
    source = _function(BUILDER, "_buildBoxLabel")
    assert "parameterUtils.addTextParameter(" in source
    assert "labelInput.bigTextParameter" in source and "labelInput.lineParameters" in source


def test_the_marking_gets_the_color_and_its_own_component():
    source = _function(BUILDER, "_buildBoxLabel")
    assert "assembly.TEXT_COMPONENT_NAME" in source
    assert "appearanceUtils.colorPart(marking, textOccurrence, state.textColor)" in source


def test_a_timeline_group_per_label():
    source = _function(BUILDER, "_buildBoxLabel")
    assert "timelineGroups.add(" in source


def test_execute_and_preview_share_the_build():
    assert "generateBoxLabel(args)" in _function(ENTRY, "command_execute")
    assert "generateBoxLabel(args, mayChangeDocument=False)" in _function(ENTRY, "command_preview")


def test_free_labels_count_as_taken_room_by_their_body_names():
    """Review: the bodies aren't tagged, placementUtils finds them by name: 'Box label', 'Box label text 1', ..."""
    source = _function(BUILDER, "_buildBoxLabel")
    assert "predBoxLabel.PLATE_BODY_NAME," in source


def test_bodies_in_the_root_are_moved_to_the_free_spot():
    """Review: a preview in a part design builds into the root, without an occurrence to carry the spot or a joint"""
    source = _function(BUILDER, "_buildBoxLabel")
    assert "elif occurrenceTransform is None and (box is None or not place.isComponent):" in source
    assert "placementUtils.moveBodies(" in source


def test_the_plate_is_tagged_so_the_export_takes_it_with_its_surface():
    # p380 (round r29-export): untagged, the export didn't take the label as a part, and a Flush one lay wrong side up
    source = _function(BUILDER, "_buildBoxLabel")
    # its config holds the surface among the rest since the box label is rebuilt and cloned (1.1.0)
    assert "tagUtils.tagBody(plate, tagUtils.TAG_BOX_LABEL, settings, labelParameters, configJson.stateToJson(configJson.GENERATOR_BOX_LABEL, state), prefix," in source
