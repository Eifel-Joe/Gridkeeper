"""
Tests for the config of a Cullenect insert (round 18, p150): saved, loaded and cloned like the bins' and baseplates',
the dialog's values of a state and back, and where a rebuilt insert goes.
"""

import os
import sys
import json
import dataclasses
import importlib.util

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS_FOLDER = os.path.join(PROJECT_ROOT, "lib", "gridfinityUtils", "cullenectIcons")
CASES_FOLDER = os.path.join(PROJECT_ROOT, "tests", "e2e", "cases")


def _load(name, *path, package=None):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PROJECT_ROOT, *path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _loadPackageModule(module):
    # labelConfig imports cullenectCatalog and labelColors as siblings, loaded under a throwaway package
    package = "labelConfigTestPackage"
    if package not in sys.modules:
        packageSpec = importlib.util.spec_from_loader(package, loader=None, is_package=True)
        packageModule = importlib.util.module_from_spec(packageSpec)
        packageModule.__path__ = [os.path.join(PROJECT_ROOT, "lib", "gridfinityUtils")]
        sys.modules[package] = packageModule
    return _load(f"{package}.{module}", "lib", "gridfinityUtils", f"{module}.py")


labelConfig = _loadPackageModule("labelConfig")
catalog = _loadPackageModule("cullenectCatalog")
configJson = _load("configJsonForLabels", "lib", "configJson.py")
defaultSettings = _load("defaultSettingsForLabels", "lib", "defaultSettings.py")
labelState = _load("labelInputState", "commands", "commandCreateLabel", "inputState.py")

LABEL = configJson.GENERATOR_LABEL
SURFACE_NAMES = {"Embossed": "Raised", "Debossed": "Set in", "Flush": "Flush"}


def _case(name):
    with open(os.path.join(CASES_FOLDER, name + ".json")) as file:
        return configJson.stateFromJson(LABEL, labelState.InputState, {**defaultSettings.SETTINGS[LABEL], **json.load(file)["settings"]})


CASES = ["label_1u_screw_text", "label_25mm_free", "label_2u_hardware", "label_1u_screw_text_colored", "label_1u_set_screw_hex"]


@pytest.mark.parametrize("name", CASES)
def test_config_round_trip(name):
    state = _case(name)
    text = configJson.configText(LABEL, configJson.stateToJson(LABEL, state), "2.2.0.0")
    (read, notes) = configJson.readConfig(text, LABEL, labelState.InputState, _case("label_1u_screw_text"))
    assert notes.isEmpty()
    assert configJson.stateToJson(LABEL, read) == configJson.stateToJson(LABEL, state)


def _dialog_round_trip(settings):
    values = labelConfig.dialogValues(settings, SURFACE_NAMES)
    hardwareKeys = [os.path.splitext(os.path.basename(path))[0] for (_, path) in catalog.listHardwareIcons(ICONS_FOLDER)]
    return labelConfig.settingsOfDialog(values, SURFACE_NAMES, catalog.screwOptions(ICONS_FOLDER), hardwareKeys)


@pytest.mark.parametrize("name", CASES)
def test_dialog_values_round_trip(name):
    settings = configJson.stateToJson(LABEL, _case(name))
    assert _dialog_round_trip(settings) == settings


def test_every_screw_block_and_hardware_round_trips():
    settings = configJson.stateToJson(LABEL, _case("label_1u_screw_text"))
    for (field, keys) in catalog.screwOptions(ICONS_FOLDER).items():
        for key in keys:
            changed = {**settings, field: key}
            assert _dialog_round_trip(changed)[field] == key, (field, key)
    for (_, path) in catalog.listHardwareIcons(ICONS_FOLDER):
        key = os.path.splitext(os.path.basename(path))[0]
        changed = {**settings, "showScrew": False, "hardware": key}
        assert _dialog_round_trip(changed)["hardware"] == key
    assert _dialog_round_trip({**settings, "hardware": "none"})["hardware"] == "none"


def test_dialog_shows_the_color_as_choice_and_custom_text():
    settings = configJson.stateToJson(LABEL, _case("label_1u_screw_text"))
    assert labelConfig.dialogValues({**settings, "textColor": "#D02020"}, SURFACE_NAMES)["colorChoice"] == "Red"
    values = labelConfig.dialogValues({**settings, "textColor": "#123456"}, SURFACE_NAMES)
    assert (values["colorChoice"], values["customColor"]) == ("Custom", "#123456")


def test_old_label_config_keeps_missing_fields():
    current = dataclasses.replace(_case("label_1u_screw_text"), textColor="#D02020")
    settings = configJson.stateToJson(LABEL, _case("label_25mm_free"))
    del settings["textColor"]
    (read, notes) = configJson.readConfig(configJson.configText(LABEL, settings), LABEL, labelState.InputState, current)
    assert read.textColor == "#D02020"
    assert ("textColor", "#D02020") in notes.missing


def test_rebuild_keeps_the_corner():
    # the old insert's box in cm, the new one is drawn from its bottom left corner
    assert labelConfig.rebuildCorner((1.2, 3.0, 4.8, 4.1)) == pytest.approx((1.2, 3.0))


def test_parameter_fields_are_settings_of_an_insert():
    # rebuildUtils.configWithParameters puts a parameter's value into the field of its label, see labelBuilder
    fields = {field.name for field in dataclasses.fields(labelState.InputState)}
    assert set(labelConfig.PARAMETER_FIELDS.values()) <= fields
    assert set(labelConfig.PARAMETER_FIELDS) == {"Base width unit", "Text line 1", "Text line 2"}
    assert "baseWidth" in configJson.MM_FIELDS[LABEL]


def test_a_text_only_in_line_2_is_labelled_line_2():
    # review round 18 (I4): labelled by its place, a second line alone went back into line 1 on a rebuild and the
    # insert got its text twice. Labelled by the line it was typed in, it goes back there
    assert labelConfig.textLines("", "DIN 912") == [("DIN 912", "Text line 2")]
    assert labelConfig.PARAMETER_FIELDS["Text line 2"] == "line2"


def test_both_lines_keep_their_labels():
    assert labelConfig.textLines("M3x10", "DIN 912") == [("M3x10", "Text line 1"), ("DIN 912", "Text line 2")]
    assert labelConfig.textLines("M3x10", "  ") == [("M3x10", "Text line 1")]


def test_a_numbered_pocket_joint_is_the_commands():
    # round 20: a rebuild with the same name made "... in pocket (1)", the old joint was still there; insertPocket
    # looked for the name ending in " in pocket" and lost the pocket on the next rebuild
    assert labelConfig.isPocketJointName("Gridfinity label 1U M3x10 in pocket")
    assert labelConfig.isPocketJointName("Gridfinity label 1U M3x10 in pocket (1)")
    assert labelConfig.isPocketJointName("Gridfinity label 1U M3x10 in pocket (12)")
    assert not labelConfig.isPocketJointName("Starr1")
    assert not labelConfig.isPocketJointName("in pocket of mine (x)")
