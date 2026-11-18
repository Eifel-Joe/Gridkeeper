"""
Tests for bin and baseplate config files: writing them and reading them back into a dialog's state.
"""

import os
import re
import json
import math
import dataclasses
import importlib.util
import pytest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_FOLDER = os.path.join(PROJECT_ROOT, "tests", "e2e", "cases")


def _load(name, *path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PROJECT_ROOT, *path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


configJson = _load("configJson", "lib", "configJson.py")
defaultSettings = _load("defaultSettings", "lib", "defaultSettings.py")
binState = _load("binInputState", "commands", "commandCreateBin", "inputState.py")
baseplateState = _load("baseplateInputState", "commands", "commandCreateBaseplate", "inputState.py")
BIN = configJson.GENERATOR_BIN
BASEPLATE = configJson.GENERATOR_BASEPLATE


def case_state(name, generator, stateClass):
    """A test case, its settings over the defaults"""
    with open(os.path.join(CASES_FOLDER, name)) as file:
        return configJson.stateFromJson(generator, stateClass, {**defaultSettings.SETTINGS[generator], **json.load(file)["settings"]})


@pytest.fixture
def current():
    """A bin as the dialog has it"""
    return case_state("bin_2x3x5_features.json", BIN, binState.InputState)


BIN_CHOICES = {
    "binType": configJson.Choice(["Hollow", "Shelled", "Solid"], "Hollow"),
    "labelIcon": configJson.Choice(["None", "screw"], "None"),
}


def read(text, current, generator=BIN, stateClass=None, choices=None):
    return configJson.readConfig(text, generator, stateClass or binState.InputState, current, choices)


def settings_text(**settings):
    return json.dumps({"generator": BIN, "settings": settings})


def test_saved_config_reads_back_to_the_same_state(current):
    text = configJson.configText(BIN, configJson.stateToJson(BIN, current), "1.7.0.0")
    (state, notes) = read(text, current)
    assert notes.isEmpty()
    for field in dataclasses.fields(state):
        expected = getattr(current, field.name)
        if isinstance(expected, float):
            assert math.isclose(getattr(state, field.name), expected, abs_tol=1e-9), field.name
        else:
            assert getattr(state, field.name) == expected, field.name


def test_config_names_its_generator_and_version(current):
    data = json.loads(configJson.configText(BIN, configJson.stateToJson(BIN, current), "1.7.0.0"))
    assert data["generator"] == BIN
    assert data["generatorVersion"] == "1.7.0.0"
    assert data["settings"]["baseWidth"] == pytest.approx(current.baseWidth * 10)


def test_version_is_left_out_when_unknown(current):
    assert "generatorVersion" not in json.loads(configJson.configText(BIN, configJson.stateToJson(BIN, current)))


def test_lengths_and_angles_are_read_in_mm_and_degrees(current):
    (state, _) = read(json.dumps({"generator": BIN, "settings": {"wallThickness": 1.6, "tabOverhangAngle": 30}}), current)
    assert state.wallThickness == pytest.approx(0.16)
    assert state.tabOverhangAngle == pytest.approx(math.pi / 6)


def test_missing_settings_keep_the_current_ones(current):
    (state, notes) = read(json.dumps({"generator": BIN, "settings": {"binWidth": 4}}), current)
    assert state.binWidth == 4
    assert state.binLength == current.binLength
    assert state.wallThickness == pytest.approx(current.wallThickness)
    assert ("binLength", current.binLength) in notes.missing
    assert "binWidth" not in [name for (name, _) in notes.missing]


def test_unknown_settings_are_skipped(current):
    (state, notes) = read(json.dumps({"generator": BIN, "settings": {"binWidth": 4, "hasLid": True}}), current)
    assert state.binWidth == 4
    assert not hasattr(state, "hasLid")
    assert notes.unknown == ["hasLid"]


def test_the_old_gap_between_plates_reads_as_half_on_each_plate_edge():
    plate = case_state("baseplate_2x2_light.json", BASEPLATE, baseplateState.InputState)
    text = json.dumps({"generator": BASEPLATE, "settings": {"plateClearance": 0.3}})
    (state, notes) = read(text, plate, BASEPLATE, baseplateState.InputState)
    assert state.plateEdgeClearance == pytest.approx(0.015)
    assert "plateClearance" not in notes.unknown
    assert "plateEdgeClearance" not in [name for (name, _) in notes.missing]


def test_a_new_setting_wins_over_its_old_name():
    settings = configJson.renamedSettings(BASEPLATE, {"plateClearance": 0.3, "plateEdgeClearance": 0.1})
    assert settings == {"plateEdgeClearance": 0.1}


def test_shape_cells_become_tuples(current):
    (state, _) = read(json.dumps({"generator": BIN, "settings": {"shapeCells": [[0, 0], [1, 0]]}}), current)
    assert state.shapeCells == [(0, 0), (1, 0)]


def test_test_case_files_load_as_configs(current):
    """A case has only the settings it changes, the others keep the current values"""
    with open(os.path.join(CASES_FOLDER, "bin_2x3x5_features.json")) as file:
        (state, notes) = read(file.read(), current)
    assert notes.unknown == [] and notes.replaced == []
    assert "hasScoop" not in [name for (name, _) in notes.missing]
    assert "wallThickness" in [name for (name, _) in notes.missing]
    # settings added after the oldest configs get the value of the older bins instead (round 32, p280)
    with open(os.path.join(CASES_FOLDER, "bin_2x3x5_features.json")) as file:
        saved = json.load(file)["settings"]
    older = {name: value for (name, value) in OLDER_BIN.items() if name not in saved}
    assert configJson.stateToJson(BIN, state) == {**configJson.stateToJson(BIN, current), **older}


@pytest.mark.parametrize("settings, name", [
    ({"hasLip": 1}, "hasLip"),
    ({"binWidth": "2"}, "binWidth"),
    ({"binWidth": True}, "binWidth"),
    ({"labelText": 5}, "labelText"),
    ({"shapeCells": "all"}, "shapeCells"),
    ({"shapeCells": [[0, 0, 1]]}, "shapeCells"),
    ({"shapeCells": [[0, 0.5]]}, "shapeCells"),
    ({"compartmentPockets": [1]}, "compartmentPockets"),
    ({"compartmentsX": 2.5}, "compartmentsX"),
    ({"compartmentsX": True}, "compartmentsX"),
])
def test_settings_of_the_wrong_kind_are_refused(current, settings, name):
    with pytest.raises(configJson.ConfigError, match=name):
        read(json.dumps({"generator": BIN, "settings": settings}), current)


def test_whole_numbers_count_as_lengths(current):
    (state, _) = read(json.dumps({"generator": BIN, "settings": {"baseWidth": 42}}), current)
    assert state.baseWidth == pytest.approx(4.2)


def test_baseplate_config_is_refused_by_the_bin(current):
    with pytest.raises(configJson.ConfigError, match="baseplate, not of a bin"):
        read(json.dumps({"generator": BASEPLATE, "settings": {}}), current)


@pytest.mark.parametrize("text", ["{not json", "[]", json.dumps({"generator": BIN}), json.dumps({"settings": {}})])
def test_files_that_arent_configs_are_refused(current, text):
    with pytest.raises(configJson.ConfigError):
        read(text, current)


def test_baseplate_config_reads_back():
    current = case_state("baseplate_fill_area_pieces.json", BASEPLATE, baseplateState.InputState)
    text = configJson.configText(BASEPLATE, configJson.stateToJson(BASEPLATE, current))
    (state, notes) = read(text, current, BASEPLATE, baseplateState.InputState)
    assert notes.isEmpty()
    assert state.areaWidth == pytest.approx(current.areaWidth)
    assert state.sizingMode == current.sizingMode


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_numbers_have_to_be_finite(current, value):
    with pytest.raises(configJson.ConfigError, match="binHeight"):
        read('{"generator": "bin", "settings": {"binHeight": %s}}' % value, current)


def test_every_wrong_setting_is_named(current):
    with pytest.raises(configJson.ConfigError) as err:
        read(settings_text(hasLip=1, binWidth="2"), current)
    assert "hasLip has to be yes or no" in str(err.value)
    assert "binWidth has to be a number" in str(err.value)


def test_whole_numbers_written_with_a_fraction_are_read(current):
    (state, _) = read(settings_text(compartmentsX=3.0, shapeCells=[[1.0, 0]]), current)
    assert state.compartmentsX == 3 and isinstance(state.compartmentsX, int)
    assert state.shapeCells == [(1, 0)]


def test_values_out_of_range_are_left_to_the_dialog(current):
    (state, notes) = read(settings_text(wallThickness=-5, compartmentsX=0), current)
    assert state.wallThickness == pytest.approx(-0.5)
    assert state.compartmentsX == 0
    assert notes.replaced == []


def test_unknown_options_become_the_default(current):
    (state, notes) = read(settings_text(binType="Bucket", labelIcon="screw-m3"), current, choices=BIN_CHOICES)
    assert state.binType == "Hollow"
    assert state.labelIcon == "None"
    assert notes.replaced == [("binType", "Bucket", "Hollow"), ("labelIcon", "screw-m3", "None")]


def test_known_options_are_kept(current):
    (state, notes) = read(settings_text(binType="Solid", labelIcon="screw"), current, choices=BIN_CHOICES)
    assert (state.binType, state.labelIcon) == ("Solid", "screw")
    assert notes.replaced == []


def test_options_arent_checked_without_choices(current):
    (state, _) = read(settings_text(binType="Bucket"), current)
    assert state.binType == "Bucket"


def test_notes_list_every_change_by_kind(current):
    (_, notes) = read(settings_text(binType="Bucket", hasLid=True), current, choices=BIN_CHOICES)
    notes.missing = [("creaseDepth", 0.6), ("hasLip", True), ("shapeCells", [[0, 0]]), ("labelText", "M3"), ("binHeight", 5)]
    text = configJson.notesText(BIN, notes)
    assert text == "\n\n".join([
        "Not recognised, skipped:\n  • hasLid",
        "Not in the file, kept the current value:\n  • creaseDepth (0.6 mm)\n  • hasLip (yes)\n  • shapeCells (1 items)"
        "\n  • labelText (\"M3\")\n  • binHeight (5)",
        "Unknown option, used the default:\n  • binType \"Bucket\" → Hollow",
    ])


def test_no_notes_without_changes(current):
    assert configJson.notesText(BIN, configJson.ConfigNotes()) == ""


# --- round 18, p151: an old bin config without a label color kept the dialog's color choice. Round 32 (p280) reverses it
# for settings a config couldn't have had, see test_old_bin_with_a_label_gets_no_color_even_with_one_in_the_dialog

labelColors = _load("labelColorsForConfig", "lib", "gridfinityUtils", "labelColors.py")


# --- round 20, p221: the note after "Load from file" named the wall thickness ten times too large (12 mm for 1.2 mm)

def test_hand_test_10_file_keeps_lengths_in_mm_in_the_note(current):
    # the dialog with a wall of 1.2 mm typed in (0.12 cm, as Fusion's inputs keep lengths), then the file of hand test
    # 10 loaded, which has only the bin size: every kept length shows in mm as the dialog does. Not reproduced: this
    # path shows 1.2 mm, see dev-notes/specs/runde-20-uebergabe.md
    path = os.path.join(PROJECT_ROOT, "dev-notes", "specs", "testdateien", "handtest-10-alte-bin-ohne-farbe.json")
    with open(path, encoding="utf-8") as file:
        text = file.read()
    dialog = dataclasses.replace(current, wallThickness=0.12, xyClearance=0.025, baseWidth=4.2)
    (state, notes) = read(text, dialog)
    kept = dict(notes.missing)
    assert kept["wallThickness"] == pytest.approx(1.2)
    note = configJson.notesText(BIN, notes)
    assert "wallThickness (1.2 mm)" in note
    assert "xyClearance (0.25 mm)" in note
    assert "baseWidth (42 mm)" in note
    assert state.wallThickness == pytest.approx(0.12)


# --- upstream round 17.11. (p13): a bin saved before the lip types had the light lip trimmed flat ---

def _lip_changed(current):
    return dataclasses.replace(current, lipType="Full", isLipTopTrimmed=False)


def test_older_bin_settings_get_the_lip_they_were_built_with():
    assert configJson.withOlderValues(BIN, {"binWidth": 4}) == {**OLDER_BIN, "binWidth": 4}
    filled = configJson.withOlderValues(BIN, {"lipType": "Full", "isLipTopTrimmed": False})
    assert (filled["lipType"], filled["isLipTopTrimmed"]) == ("Full", False)
    assert configJson.withOlderValues(configJson.GENERATOR_BASEPLATE, {"baseWidth": 42}) == {"baseWidth": 42}


def test_older_config_reads_with_the_light_trimmed_lip_whatever_the_dialog_has(current):
    # a rebuild or clone of a bin tagged before the merge reads its config over the dialog's state (p151)
    (state, notes) = read(settings_text(binWidth=4), _lip_changed(current))
    assert state.lipType == "Light"
    assert state.isLipTopTrimmed is True
    missing = [name for (name, _) in notes.missing]
    assert "lipType" not in missing and "isLipTopTrimmed" not in missing


def test_config_with_a_lip_type_keeps_it(current):
    (state, _) = read(settings_text(lipType="Full", isLipTopTrimmed=False), current)
    assert state.lipType == "Full"
    assert state.isLipTopTrimmed is False


def test_rebuild_fills_the_older_values_into_a_tagged_config():
    # parameterEdits compares the tagged config with the dialog's, a bin tagged before the merge would otherwise count
    # its lip as changed and be rebuilt instead of having its parameters set
    path = os.path.join(PROJECT_ROOT, "lib", "rebuildUtils.py")
    with open(path, encoding="utf-8") as file:
        source = file.read()
    body = source[source.index("def configWithParameters("):]
    body = body[:body.index("\ndef ", 1)]
    assert "config = configJson.withOlderValues(generator, " in body


# --- upstream round 17.11. (p13, 3452e56): the plate clearance per edge, renamed on every way settings are read ---

def test_renamed_settings_leave_label_and_unknown_generators_alone():
    # Cullenect inserts have no renamed settings, a generator a later round adds (the box of round 27) neither
    assert configJson.renamedSettings(configJson.GENERATOR_LABEL, {"baseWidth": 25}) == {"baseWidth": 25}
    assert configJson.renamedSettings("box", {"width": 3}) == {"width": 3}


def test_old_baseplate_config_reads_the_clearance_per_edge():
    settings = configJson.withOlderValues(configJson.GENERATOR_BASEPLATE, configJson.renamedSettings(configJson.GENERATOR_BASEPLATE, {"plateClearance": 0.6}))
    assert settings == {"plateEdgeClearance": 0.3}


def test_rebuild_renames_the_settings_of_a_tagged_config():
    # a baseplate tagged before the rename keeps plateClearance in its tag, its settings and a rebuild read the new name
    path = os.path.join(PROJECT_ROOT, "lib", "rebuildUtils.py")
    with open(path, encoding="utf-8") as file:
        source = file.read()
    body = source[source.index("def configWithParameters("):]
    body = body[:body.index("\ndef ", 1)]
    assert "config = configJson.withOlderValues(generator, configJson.renamedSettings(generator, config))" in body


def test_rebuild_log_compares_under_the_new_names():
    # the log of an old baseplate's rebuild showed plateEdgeClearance None -> 0.05 instead of its old value halved
    path = os.path.join(PROJECT_ROOT, "lib", "rebuildUtils.py")
    with open(path, encoding="utf-8") as file:
        source = file.read()
    body = source[source.index("def configChanges("):]
    body = body[:body.index("\ndef ", 1)] if "\ndef " in body[1:] else body
    assert "configJson.renamedSettings(generator, " in body


# --- round 32, p280: a config saved before a setting existed builds as it was saved, not with the dialog's value.
# Joerg: "Aeltere Bins werden erstellt, wie sie gespeichert wurden. Es werden keine Einstellungen aktiviert, welche die
# Config nicht her gibt." See dev-notes/specs/2026-11-18-r32-old-bin-defaults.md

# the fields of each generator's oldest config, read from git (bin and baseplate 2fea2a1, label 8a5ce68, box c5a24e8,
# box label bd75733). A field added since needs the value that built the older models in configJson.OLDER_VALUES
FIRST_CONFIG_FIELDS = {
    BIN: [
        "baseWidth", "baseLength", "heightUnit", "xyClearance", "binWidth", "binLength", "binHeight", "isHalfGrid",
        "wallThickness", "binType", "generateBase", "generateBody", "hasJointOrigins", "hasScrewHoles",
        "screwHoleDiameter", "hasMagnetCutouts", "hasMagnetCutoutsTabs", "magnetCutoutDiameter", "magnetCutoutDepth",
        "hasLip", "hasLipNotches", "hasScoop", "scoopMaxRadius", "hasTab", "tabLength", "tabWidth", "tabPosition",
        "tabOverhangAngle", "isTabHollow", "isTabOpenThroughSides", "tabTopAngle", "labelText", "labelIcon",
        "labelStyle", "isLabelBold", "compartmentsX", "compartmentsY", "showCompartmentsLayout", "compartmentPockets",
        "hasCustomShape", "shapeCells", "hasCreases", "creaseDepth", "creaseMinLength", "creaseMaxPanelLength",
        "creaseMinHeight",
    ],
    BASEPLATE: [
        "baseWidth", "baseLength", "xyClearance", "plateWidth", "plateLength", "plateType", "hasMagnetSockets",
        "magnetSocketSize", "magnetSocketDepth", "hasScrewHoles", "screwHoleSize", "screwHeadSize", "hasPadding",
        "paddingLeft", "paddingTop", "paddingRight", "paddingBottom", "extraBottomThickness", "verticalClearance",
        "hasConnectionHoles", "connectionHoleSize", "sizingMode", "areaWidth", "areaLength", "fitTolerance", "bedWidth",
        "bedLength", "bedMargin", "alignmentX", "alignmentY", "useHalfCells", "hasJointOrigins",
    ],
    configJson.GENERATOR_LABEL: [
        "baseWidth", "useUnits", "widthUnits", "freeWidth", "offsetX", "offsetY", "line1", "line2", "textStyle",
        "showScrew", "head", "shaft", "threads", "driver", "flange", "security", "hardware", "surface", "textColor",
    ],
    configJson.GENERATOR_BOX: ["gridX", "gridY", "heightU", "hasMagnets", "magnetDepth", "magnetDiameter", "hasJointOrigins"],
    configJson.GENERATOR_BOX_LABEL: ["cells", "bigText", "line1", "line2", "symbols", "textStyle", "surface", "textColor"],
}
STATE_FOLDERS = {
    BIN: "commandCreateBin", BASEPLATE: "commandCreateBaseplate", configJson.GENERATOR_LABEL: "commandCreateLabel",
    configJson.GENERATOR_BOX: "commandCreateBox", configJson.GENERATOR_BOX_LABEL: "commandCreateBoxLabel",
}


def _state_fields(generator):
    # read from the source like the inventory was, the box states import from their package
    path = os.path.join(PROJECT_ROOT, "commands", STATE_FOLDERS[generator], "inputState.py")
    with open(path, encoding="utf-8") as file:
        return re.findall(r"^    (\w+)\s*:", file.read(), re.M)


@pytest.mark.parametrize("generator", list(FIRST_CONFIG_FIELDS))
def test_every_setting_added_since_the_oldest_config_has_its_older_value(generator):
    added = [name for name in _state_fields(generator) if name not in FIRST_CONFIG_FIELDS[generator]]
    assert [name for name in added if name not in configJson.OLDER_VALUES.get(generator, {})] == []


def _opposite(current):
    # the dialog with each later setting the other way round from the older bins
    return dataclasses.replace(
        current, lipType="Full", isLipTopTrimmed=False, isShellRounded=True, hasDividersToTop=True,
        labelColor="#FF0000", cullenectSocketOffset=0.05,
    )


def _oldest_bin_config(current):
    settings = configJson.stateToJson(BIN, dataclasses.replace(current, hasTab=True, labelText="Bolts"))
    return {name: value for (name, value) in settings.items() if name in FIRST_CONFIG_FIELDS[BIN]}


OLDER_BIN = {
    "lipType": "Light", "isLipTopTrimmed": True, "isShellRounded": False, "hasDividersToTop": False,
    "labelColor": "", "cullenectSocketOffset": 0.3,
}


def test_oldest_bin_config_reads_as_it_was_built_whatever_the_dialog_has(current):
    text = configJson.configText(BIN, _oldest_bin_config(current))
    (state, notes) = read(text, _opposite(current))
    built = configJson.stateToJson(BIN, state)
    assert {name: built[name] for name in OLDER_BIN} == OLDER_BIN
    assert [name for (name, _) in notes.missing if name in OLDER_BIN] == []


def test_older_values_never_replace_a_saved_setting(current):
    saved = configJson.stateToJson(BIN, _opposite(current))
    filled = configJson.withOlderValues(BIN, saved)
    assert {name: filled[name] for name in OLDER_BIN} == {name: saved[name] for name in OLDER_BIN}


def test_old_bin_with_a_label_gets_no_color_even_with_one_in_the_dialog(current):
    # p151 (round 18) kept the dialog's color here; p280 reverses it for settings the config couldn't have had
    text = configJson.configText(BIN, _oldest_bin_config(current))
    (state, _) = read(text, dataclasses.replace(current, labelColor=labelColors.configCurrentColor("Red", "")))
    assert state.labelColor == ""
    assert labelColors.restoresColor(state.labelColor, True, False)
    assert labelColors.choiceOf(state.labelColor) == (labelColors.NO_COLOR_CHOICE, "")


# a baseplate saved before plates had a clearance of their own (8cc5089) took the bin xy clearance at every edge
# where plates meet

def test_old_baseplate_gets_its_xy_clearance_at_the_plate_edges():
    assert configJson.withOlderValues(BASEPLATE, {"xyClearance": 0.2})["plateEdgeClearance"] == 0.2
    assert configJson.withOlderValues(BASEPLATE, {"xyClearance": 0.5})["plateEdgeClearance"] == 0.5


def test_partial_baseplate_config_without_xy_clearance_keeps_the_dialogs_edge_clearance():
    assert "plateEdgeClearance" not in configJson.withOlderValues(BASEPLATE, {"baseWidth": 42})


def test_saved_plate_clearance_wins_over_the_xy_clearance():
    settings = configJson.withOlderValues(BASEPLATE, configJson.renamedSettings(BASEPLATE, {"plateClearance": 0.6, "xyClearance": 0.25}))
    assert settings["plateEdgeClearance"] == 0.3


def test_old_baseplate_config_reads_its_edge_clearance_over_the_dialog():
    current = case_state("baseplate_3x2_full.json", BASEPLATE, baseplateState.InputState)
    settings = configJson.stateToJson(BASEPLATE, dataclasses.replace(current, xyClearance=0.04))
    old = {name: value for (name, value) in settings.items() if name in FIRST_CONFIG_FIELDS[BASEPLATE] and name != "fitTolerance"}
    (state, _) = read(json.dumps({"generator": BASEPLATE, "settings": old}), current, BASEPLATE, baseplateState.InputState)
    assert state.plateEdgeClearance == pytest.approx(0.04)


def test_baseplate_dialog_takes_the_edge_clearance_up_to_the_largest_xy_clearance():
    # nothing in the geometry limits it to 0.25 mm, that was half upstream's 0.5 mm whole gap; the edges took the xy
    # clearance up to 0.5 mm before 8cc5089, and the outer edges of a fill area still do
    const = _load("constForConfig", "lib", "gridfinityUtils", "const.py")
    assert const.BASEPLATE_PLATE_EDGE_CLEARANCE_MAX == 0.05
    with open(os.path.join(PROJECT_ROOT, "commands", "commandCreateBaseplate", "entry.py"), encoding="utf-8") as file:
        source = file.read()
    assert "plateEdgeClearanceInput.maximumValue = const.BASEPLATE_PLATE_EDGE_CLEARANCE_MAX" in source
    assert "inputsState.plateEdgeClearance <= const.BASEPLATE_PLATE_EDGE_CLEARANCE_MAX" in source
    assert "0.025, 0.5]mm" in source


def test_rebuild_log_compares_with_the_older_values():
    # an old bin's rebuild logged lipType None -> 'Light' and the like for settings it never had
    path = os.path.join(PROJECT_ROOT, "lib", "rebuildUtils.py")
    with open(path, encoding="utf-8") as file:
        source = file.read()
    body = source[source.index("def configChanges("):]
    body = body[:body.index("\ndef ", 1)] if "\ndef " in body[1:] else body
    assert "configJson.withOlderValues(generator, configJson.renamedSettings(generator, " in body


def test_xy_clearance_of_the_wrong_type_is_refused_once():
    # review round 32: a text xyClearance in a file was named a second time as plateEdgeClearance
    current = case_state("baseplate_3x2_full.json", BASEPLATE, baseplateState.InputState)
    with pytest.raises(configJson.ConfigError) as err:
        read(json.dumps({"generator": BASEPLATE, "settings": {"xyClearance": "0.4"}}), current, BASEPLATE, baseplateState.InputState)
    assert "xyClearance" in str(err.value) and "plateEdgeClearance" not in str(err.value)
