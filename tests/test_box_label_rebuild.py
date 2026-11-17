"""
Settings, rebuild and clone of the box label (Hauptsitzung for 1.1.0, Jörg after his test: "Die Box-Labels haben die
Punkte [Gridkeeper settings / rebuild / clone im Rechtsklick] nicht. Warum? Die Cullenect-Label haben es."). As the
Cullenect insert (round 18, p150): the plate's tag keeps the whole config, the right-click menu offers settings, rebuild
and clone, a rebuild builds the label anew in place and jointed into its holder again, a clone opens the dialog with the
settings and no box. The Fusion parts are read as source, the plain parts are loaded.
"""

import ast
import json
import os

import pytest

from tests.test_box_label_command import BUILDER, ENTRY, ROOT, _function, _state_module
from tests.test_config_json import _load
from tests.test_joint_origin_layout import _load as _loadUtils
from tests.test_tag_utils import _Body, _Component, _Occurrence, _load_tag_utils

configJson = _load("configJson", "lib", "configJson.py")
boxLabelConfig = _loadUtils("boxLabelConfig")
tagUtils = _load_tag_utils()
State = _state_module().InputState

SETTINGS_ENTRY = os.path.join(ROOT, "commands", "commandShowSettings", "entry.py")
REBUILD_UTILS = os.path.join(ROOT, "lib", "rebuildUtils.py")
BOX_LABEL = "boxLabel"


def _state(**changes):
    values = dict(cells=5, bigText="M3", line1="Socket head", line2="DIN 912", symbols=["Socket Hex", "Nut", "None", "None", "None"],
                  textStyle="Heavy", surface="Debossed", textColor="#D02020")
    values.update(changes)
    return State(**values)


def _source(path):
    return open(path, encoding="utf-8").read()


class TestConfig:
    def test_the_box_label_is_a_generator_of_the_config_files(self):
        assert configJson.GENERATOR_BOX_LABEL == BOX_LABEL
        assert configJson.GENERATOR_TITLES[BOX_LABEL] == "box label"

    def test_the_tag_name_is_the_generator_name(self):
        # the settings page takes the tag name as configJson's generator, see commandShowSettings.pageHandlers
        assert tagUtils.TAG_BOX_LABEL == configJson.GENERATOR_BOX_LABEL

    def test_the_state_round_trips(self):
        state = _state()
        settings = configJson.stateToJson(BOX_LABEL, state)
        assert settings["cells"] == 5 and settings["symbols"] == ["Socket Hex", "Nut", "None", "None", "None"]
        assert configJson.stateFromJson(BOX_LABEL, State, json.loads(json.dumps(settings))) == state

    def test_a_config_file_is_read_with_its_symbols(self):
        text = configJson.configText(BOX_LABEL, configJson.stateToJson(BOX_LABEL, _state(symbols=["Nut"] * 5)))
        (state, notes) = configJson.readConfig(text, BOX_LABEL, State, _state())
        assert state.symbols == ["Nut"] * 5 and notes.isEmpty()

    def test_symbols_have_to_be_a_list_of_names(self):
        settings = configJson.stateToJson(BOX_LABEL, _state())
        settings["symbols"] = "Nut"
        with pytest.raises(configJson.ConfigError, match="symbols has to be a list of names"):
            configJson.readConfig(configJson.configText(BOX_LABEL, settings), BOX_LABEL, State, _state())


class TestPlainParts:
    def test_the_text_parameters_go_back_to_their_fields(self):
        assert boxLabelConfig.PARAMETER_FIELDS == {"Large text": "bigText", "Line 1": "line1", "Line 2": "line2"}

    @pytest.mark.parametrize("name, isHolder", [
        ("Gridkeeper box label 5 cells M3 in holder", True),
        # Fusion numbers a name still taken: a rebuild with the old joint still there
        ("Gridkeeper box label 5 cells M3 in holder (1)", True),
        ("Gridkeeper box label 5 cells M3 in holder of mine", False),
        ("Rigid1", False),
    ])
    def test_the_joint_into_the_holder_is_known_by_its_name(self, name, isHolder):
        assert boxLabelConfig.isHolderJointName(name) is isHolder

    def test_symbols_the_install_has_no_svg_for_become_empty_places(self):
        (symbols, unknown) = boxLabelConfig.knownSymbols(["Nut", "Gone", "None"], ["None", "Nut", "Washer"])
        assert symbols == ["Nut", "None", "None", "None", "None"]
        assert unknown == ["Gone"]

    def test_more_than_five_symbols_are_cut(self):
        (symbols, _) = boxLabelConfig.knownSymbols(["Nut"] * 7, ["None", "Nut"])
        assert symbols == ["Nut"] * 5


class TestTags:
    def test_the_menu_reads_the_box_label_tag(self):
        plate = _Body(_Component(name="Gridkeeper box label 5 cells M3"), {BOX_LABEL: json.dumps({"config": {"cells": 5}})})
        assert tagUtils.readPartTag(plate) == (BOX_LABEL, {"config": {"cells": 5}})

    def test_generator_tags_come_first(self):
        body = _Body(_Component(name="Gridfinity bin"), {"bin": json.dumps({"id": "gfBin1"})})
        assert tagUtils.readPartTag(body) == ("bin", {"id": "gfBin1"})

    def test_a_letter_of_the_box_label_finds_the_plate(self):
        labelComponent = _Component(name="Gridkeeper box label 5 cells M3")
        plate = _Body(labelComponent, {BOX_LABEL: json.dumps({"id": "gfBoxLabel1"})})
        labelOccurrence = _Occurrence(labelComponent)
        textComponent = _Component()
        letter = _Body(textComponent)
        proxy = _Body(textComponent, native=letter, occurrence=_Occurrence(textComponent, labelOccurrence))
        assert tagUtils.partTag(proxy, lambda component: None) == (plate, BOX_LABEL, {"id": "gfBoxLabel1"})

    def test_the_generator_tag_reader_still_leaves_it_out(self):
        # the export and the bin, baseplate and box builders know the generators' tags by readBodyTag (p380)
        plate = _Body(_Component(name="Gridkeeper box label"), {BOX_LABEL: "{}"})
        assert tagUtils.readBodyTag(plate) is None

    def test_rebuild_reads_the_parameters_and_id_of_any_part(self):
        tree = ast.parse(_source(REBUILD_UTILS))
        for name in ("tagParameterNames", "bodyId", "configChanges"):
            function = ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name))
            assert "tagUtils.readPartTag(body)" in function, name


class TestRightClickMenu:
    def test_settings_rebuild_and_clone_know_the_box_label(self):
        source = _source(SETTINGS_ENTRY)
        assert "from ..commandCreateBoxLabel import entry as boxLabelEntry" in source
        tree = ast.parse(source)
        tables = {ast.unparse(node.targets[0]): ast.unparse(node.value) for node in tree.body if isinstance(node, ast.Assign)}
        assert "tagUtils.TAG_BOX_LABEL: 'Box label'" in tables["TAG_TITLES"]
        assert "tagUtils.TAG_BOX_LABEL: boxLabelEntry" in tables["CLONE_COMMANDS"]
        assert "tagUtils.TAG_BOX_LABEL: boxLabelEntry" in tables["REBUILD_COMMANDS"]

    def test_a_selected_box_label_component_answers_with_its_plate(self):
        assert "tagUtils.readPartTag(body)" in _function(SETTINGS_ENTRY, "componentTag")


class TestBuilder:
    def test_the_plate_keeps_the_whole_config_its_settings_parameters_and_id(self):
        source = _function(BUILDER, "_buildBoxLabel")
        assert ("tagUtils.tagBody(plate, tagUtils.TAG_BOX_LABEL, settings, labelParameters, "
                "configJson.stateToJson(configJson.GENERATOR_BOX_LABEL, state), prefix)") in source

    def test_the_text_parameters_are_labelled_for_the_rebuild(self):
        source = _function(BUILDER, "_buildBoxLabel")
        assert "boxLabelConfig.parameterLabels(" in source
        assert "parameterUtils.addTextParameter(des, parameterUtils.parameterName(prefix, field), text.strip(), f'{name} {field}', reuse)" in source

    def test_the_bodies_in_the_root_are_moved_by_a_named_placement(self):
        assert "name=PLACEMENT_FEATURE" in _function(BUILDER, "_buildBoxLabel")

    def test_a_rebuild_is_built_in_place_of_the_old_label(self):
        source = _function(BUILDER, "rebuildBoxLabel")
        assert "rebuildUtils.findTarget(des, body, tagUtils.TAG_BOX_LABEL, PLACEMENT_FEATURE)" in source
        assert "rebuildUtils.rebuild(des, target, prefix, PARAMETER_BASE_NAME, isPreview, build, 'box label', jointsByName=True)" in source
        # a jointed label is placed by its joint, a free one keeps its old transform or the move of its bodies
        assert "None if box is not None else transform" in source

    def test_a_rebuild_refuses_a_box_after_the_label(self):
        assert "_isAfter(target, box)" in _function(BUILDER, "rebuildBoxLabel")

    def test_the_holder_of_a_label_is_found_by_its_joint(self):
        source = _function(BUILDER, "labelHolder")
        assert "boxLabelConfig.isHolderJointName(joint.name)" in source
        assert "isBoxLabelJointOrigin(" in source


class TestDialog:
    def test_the_dialog_takes_a_config_before_its_inputs(self):
        source = _function(ENTRY, "command_created")
        assert source.index("applyPendingConfig()") < source.index("addGroup(inputs, INFO_GROUP")

    def test_a_rebuild_picks_the_box_again(self):
        assert "selectionPrefill.prefillSelection(boxInput, rebuildBox)" in _function(ENTRY, "command_created")

    def test_rebuild_starts_with_the_parameters_values(self):
        source = _function(ENTRY, "startRebuild")
        assert ("rebuildUtils.configWithParameters(configJson.GENERATOR_BOX_LABEL, tag['config'], tag.get('parameters'), "
                "design.userParameters.itemByName, boxLabelConfig.PARAMETER_FIELDS)") in source
        assert "labelHolder(design, body)" in source

    def test_clone_and_rebuild_open_the_dialog(self):
        assert "ui.commandDefinitions.itemById(CMD_ID).execute()" in _function(ENTRY, "startWithConfig")

    def test_the_build_rebuilds_while_the_dialog_rebuilds(self):
        source = _function(ENTRY, "generateBoxLabel")
        assert "rebuildUtils.findBodyByToken(des, rebuildBodyToken)" in source
        assert "rebuildBoxLabel(des, body, state, settings, not mayChangeDocument, selectedBox(inputs))" in source

    def test_the_settings_page_names_a_saved_file(self):
        assert "labelName(" in _function(ENTRY, "configFileName")


class TestOlderLabels:
    """Review: labels built before this change keep {'surface': ...} only, a rebuild filled the rest from the dialog's
    last state and replaced the label with another. They show their settings, without rebuild and clone"""

    def test_a_config_of_the_surface_only_isnt_one_to_build_from(self):
        assert tagUtils.buildConfig(BOX_LABEL, {"config": {"surface": "Flush"}}) is None

    def test_a_whole_config_is(self):
        config = configJson.stateToJson(BOX_LABEL, _state())
        assert tagUtils.buildConfig(BOX_LABEL, {"config": config}) == config

    def test_other_parts_need_a_config(self):
        assert tagUtils.buildConfig("bin", {"config": {"binHeight": 3}}) == {"binHeight": 3}
        assert tagUtils.buildConfig("bin", {}) is None

    def test_the_menu_and_the_page_ask_for_it(self):
        for name in ("canRebuild", "canClone", "pageHandlers"):
            assert "tagUtils.buildConfig(" in _function(SETTINGS_ENTRY, name), name


class TestTextParameters:
    """Click test 17.11.2026: KeyError 'text1' in _buildBoxLabel, the parameters are named text1 and text2 in the
    document while the config fields are line1 and line2. One table holds both, the builder and the rebuild use it"""

    def test_each_parameter_has_its_config_field_and_label(self):
        assert boxLabelConfig.TEXT_PARAMETERS == [("bigText", "bigText", "Large text"), ("text1", "line1", "Line 1"), ("text2", "line2", "Line 2")]

    def test_the_fields_are_the_dialogs(self):
        fields = set(State.__dataclass_fields__)
        assert all(field in fields for (_, field, _) in boxLabelConfig.TEXT_PARAMETERS)

    def test_the_tag_labels_the_parameters_there_are(self):
        # the click test's label: all three texts; and one without a large text
        assert boxLabelConfig.parameterLabels(["gfBoxLabel1_bigText", "gfBoxLabel1_text1", "gfBoxLabel1_text2"]) == [
            ["Large text", "gfBoxLabel1_bigText"], ["Line 1", "gfBoxLabel1_text1"], ["Line 2", "gfBoxLabel1_text2"]]
        assert boxLabelConfig.parameterLabels([None, "gfBoxLabel2_text1", None]) == [["Line 1", "gfBoxLabel2_text1"]]

    def test_the_rebuild_reads_them_back_into_their_fields(self):
        assert boxLabelConfig.PARAMETER_FIELDS == {"Large text": "bigText", "Line 1": "line1", "Line 2": "line2"}

    def test_the_builder_uses_the_table(self):
        source = _function(BUILDER, "_buildBoxLabel")
        assert "boxLabelConfig.parameterLabels([parameter.name if parameter is not None else None for parameter in parameters])" in source
        assert "boxLabelConfig.PARAMETER_LABELS" not in source
        assert "TEXT_PARAMETER_NAMES" in source


class TestWrongJointOrigin:
    """Click test 17.11.2026: another joint origin of the box came through, the build failed with an unknown error"""

    def test_a_picked_joint_origin_that_isnt_a_label_one_blocks_ok_with_a_note(self):
        source = _function(ENTRY, "boxProblem")
        assert "not isBoxLabelJointOrigin(box)" in source
        assert "predBoxSeats.LABEL_JOINT_ORIGIN" in source
