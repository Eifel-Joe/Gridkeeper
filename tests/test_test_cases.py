"""
Tests for shape test cases: reading the JSON case files into generator states and writing them back.
"""

import os
import json
import math
import importlib.util
import pytest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_FOLDER = os.path.join(PROJECT_ROOT, "tests", "e2e", "cases")


def _load(name, *path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PROJECT_ROOT, *path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cases = _load("testCases", "commands", "commandSnapshotTests", "testCases.py")
binState = _load("binInputState", "commands", "commandCreateBin", "inputState.py")
baseplateState = _load("baseplateInputState", "commands", "commandCreateBaseplate", "inputState.py")
labelState = _load("labelInputState", "commands", "commandCreateLabel", "inputState.py")

STATE_CLASSES = {
    cases.GENERATOR_BIN: binState.InputState,
    cases.GENERATOR_BASEPLATE: baseplateState.InputState,
    cases.GENERATOR_LABEL: labelState.InputState,
}


def write_case(tmp_path, settings, generator="bin", name="case"):
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps({"description": "a case", "generator": generator, "settings": settings}))
    return str(path)


def sample_settings():
    with open(os.path.join(CASES_FOLDER, "bin_2x3x5_features.json")) as file:
        return json.load(file)["settings"]


def test_every_case_in_the_repo_loads():
    loaded = cases.loadCases(CASES_FOLDER, STATE_CLASSES)
    assert len(loaded) > 0
    for case in loaded:
        assert case.generator in STATE_CLASSES


def test_lengths_come_in_mm_and_angles_in_degrees():
    case = cases.loadCase(os.path.join(CASES_FOLDER, "bin_2x3x5_features.json"), STATE_CLASSES)
    assert case.name == "bin_2x3x5_features"
    assert case.state.baseWidth == pytest.approx(4.2)
    assert case.state.wallThickness == pytest.approx(0.12)
    assert case.state.tabOverhangAngle == pytest.approx(math.radians(45))
    assert case.state.cullenectSocketOffset == pytest.approx(0.03)
    # units of the grid stay as they are
    assert case.state.binWidth == 2
    assert case.state.creaseMinHeight == 10


def test_shape_cells_become_tuples(tmp_path):
    settings = {**sample_settings(), "hasCustomShape": True, "shapeCells": [[0, 0], [1, 0]]}
    case = cases.loadCase(write_case(tmp_path, settings), STATE_CLASSES)
    assert case.state.shapeCells == [(0, 0), (1, 0)]


def test_settings_a_case_has_not_are_the_defaults(tmp_path):
    case = cases.loadCase(write_case(tmp_path, {"binHeight": 3, "hasScoop": True}), STATE_CLASSES)
    assert case.state.binHeight == 3
    assert case.state.hasScoop is True
    defaults = cases.stateFromJson(cases.GENERATOR_BIN, binState.InputState, cases.DEFAULT_SETTINGS[cases.GENERATOR_BIN])
    assert case.state.wallThickness == pytest.approx(defaults.wallThickness)
    assert case.state.isShellRounded == defaults.isShellRounded


def test_a_case_of_no_settings_is_the_defaults(tmp_path):
    case = cases.loadCase(write_case(tmp_path, {}, generator="baseplate"), STATE_CLASSES)
    assert cases.snapshotSettings(case) == cases.DEFAULT_SETTINGS[cases.GENERATOR_BASEPLATE]


@pytest.mark.parametrize("generator", [cases.GENERATOR_BIN, cases.GENERATOR_BASEPLATE])
def test_defaults_have_every_setting_of_the_state(generator):
    state = cases.stateFromJson(generator, STATE_CLASSES[generator], cases.DEFAULT_SETTINGS[generator])
    assert cases.stateToJson(generator, state) == cases.DEFAULT_SETTINGS[generator]


def test_cases_list_only_settings_that_differ_from_the_defaults():
    for fileName in sorted(os.listdir(CASES_FOLDER)):
        with open(os.path.join(CASES_FOLDER, fileName)) as file:
            data = json.load(file)
        defaults = cases.DEFAULT_SETTINGS[data["generator"]]
        same = [name for (name, value) in data["settings"].items() if defaults.get(name) == value]
        assert same == [], f"{fileName} sets {same} to the defaults, leave them out so the case follows the defaults"


def test_settings_are_an_object(tmp_path):
    with pytest.raises(cases.TestCaseError, match="case"):
        cases.loadCase(write_case(tmp_path, [["hasLip", True]]), STATE_CLASSES)


def test_an_unknown_setting_is_an_error(tmp_path):
    settings = {**sample_settings(), "hasLid": True}
    with pytest.raises(cases.TestCaseError, match="hasLid"):
        cases.loadCase(write_case(tmp_path, settings), STATE_CLASSES)


def test_an_unknown_generator_is_an_error(tmp_path):
    with pytest.raises(cases.TestCaseError, match="drawer"):
        cases.loadCase(write_case(tmp_path, sample_settings(), generator="drawer"), STATE_CLASSES)


def test_broken_json_names_the_case(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{")
    with pytest.raises(cases.TestCaseError, match="broken"):
        cases.loadCase(str(path), STATE_CLASSES)


def test_written_case_reads_back_the_same(tmp_path):
    case = cases.loadCase(os.path.join(CASES_FOLDER, "bin_2x3x5_features.json"), STATE_CLASSES)
    path = tmp_path / "copy.json"
    path.write_text(cases.caseJson(case))
    copy = cases.loadCase(str(path), STATE_CLASSES)
    assert copy.description == case.description
    for field in binState.InputState.__dataclass_fields__:
        assert getattr(copy.state, field) == pytest.approx(getattr(case.state, field)), field


def test_written_case_has_no_float_noise():
    case = cases.loadCase(os.path.join(CASES_FOLDER, "bin_3x2x6_tab_steep_tilted.json"), STATE_CLASSES)
    settings = json.loads(cases.caseJson(case))["settings"]
    assert settings["tabWidth"] == 20
    assert settings["tabOverhangAngle"] == 30


def test_written_case_lists_only_settings_that_differ_from_the_defaults():
    path = os.path.join(CASES_FOLDER, "bin_2x3x5_features.json")
    with open(path) as file:
        data = json.load(file)
    case = cases.loadCase(path, STATE_CLASSES)
    assert json.loads(cases.caseJson(case))["settings"] == data["settings"]


def test_snapshot_settings_have_every_setting():
    case = cases.loadCase(os.path.join(CASES_FOLDER, "bin_2x3x5_features.json"), STATE_CLASSES)
    settings = cases.snapshotSettings(case)
    assert list(settings) == list(binState.InputState.__dataclass_fields__)
    assert settings["labelText"] == "Test"
    assert settings["wallThickness"] == 1.2
    assert json.loads(cases.settingsText(settings)) == settings


def test_every_snapshot_has_its_settings():
    snapshots = os.path.join(PROJECT_ROOT, "tests", "e2e", "snapshots")
    for case in cases.loadCases(CASES_FOLDER, STATE_CLASSES):
        path = os.path.join(snapshots, case.name, cases.SETTINGS_FILE)
        assert os.path.isfile(path), f"{case.name} has no {cases.SETTINGS_FILE}, update its snapshot"
        with open(path) as file:
            assert set(json.load(file)) <= set(STATE_CLASSES[case.generator].__dataclass_fields__) | set(cases.snapshotSettings(case)), case.name


def test_unchanged_settings_have_no_changes():
    settings = {"wallThickness": 1.2, "hasLip": True, "shapeCells": [[0, 0]], "labelText": ""}
    assert cases.settingChanges(settings, dict(settings)) == []


def test_numbers_are_the_same_through_float_noise():
    assert cases.settingChanges({"wallThickness": 1.2, "binWidth": 2}, {"wallThickness": 1.2000000000001, "binWidth": 2.0}) == []


def test_changed_settings_are_listed_in_order():
    expected = {"binWidth": 2, "isShellRounded": False, "wallThickness": 1.2}
    actual = {"binWidth": 2, "isShellRounded": True, "wallThickness": 1.5}
    assert cases.settingChanges(expected, actual) == [
        {"key": "isShellRounded", "expected": False, "actual": True},
        {"key": "wallThickness", "expected": 1.2, "actual": 1.5},
    ]


def test_a_flag_is_not_a_number_of_the_same_value():
    assert cases.settingChanges({"binHeight": 1}, {"binHeight": True}) == [{"key": "binHeight", "expected": 1, "actual": True}]


def test_settings_on_one_side_only_are_changes():
    assert cases.settingChanges({"seamClearance": 0.5}, {"plateClearance": 0.1}) == [
        {"key": "seamClearance", "expected": 0.5, "actual": None},
        {"key": "plateClearance", "expected": None, "actual": 0.1},
    ]


def test_lists_and_objects_are_shown_as_json():
    changes = cases.settingChanges({"shapeCells": [[0, 0]]}, {"shapeCells": [[0, 0], [1, 0]]})
    assert changes == [{"key": "shapeCells", "expected": "[[0, 0]]", "actual": "[[0, 0], [1, 0]]"}]


def test_case_settings_name_the_case_and_list_every_setting():
    case = cases.loadCase(os.path.join(CASES_FOLDER, "bin_2x3x5_features.json"), STATE_CLASSES)
    settings = cases.caseSettings(case)
    assert settings[0]["title"] == "Test case"
    assert ["Case", "bin_2x3x5_features"] in settings[0]["items"]
    items = dict(settings[1]["items"])
    assert items["wallThickness"] == "1.2"
    assert items["labelText"] == '"Test"'
    assert len(items) == len(binState.InputState.__dataclass_fields__)


def test_readme_lists_the_cases_as_they_are():
    readme = os.path.join(PROJECT_ROOT, "tests", "e2e", "README.md")
    with open(readme, encoding="utf-8") as file:
        written = file.read()
    assert written == cases.casesMarkdown(CASES_FOLDER), "tests/e2e/README.md is out of date, run python3 tests/e2e/write_readme.py"


def write_case_data(tmp_path, data, name="case"):
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(data))
    return str(path)


def test_parameters_come_in_mm_and_edit_the_state(tmp_path):
    data = {"description": "a case", "generator": "bin", "settings": sample_settings(), "parameters": {"gfBin1_baseWidth": 40, "gfBin1_heightUnit": 5}}
    case = cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)
    assert case.parameters == {"gfBin1_baseWidth": pytest.approx(4.0), "gfBin1_heightUnit": pytest.approx(0.5)}
    edited = cases.editedState(case)
    assert edited.baseWidth == pytest.approx(4.0)
    assert edited.heightUnit == pytest.approx(0.5)
    assert edited.baseLength == case.state.baseLength
    assert case.state.baseWidth == pytest.approx(4.2)


def test_a_case_without_parameters_has_none():
    case = cases.loadCase(os.path.join(CASES_FOLDER, "bin_2x3x5_features.json"), STATE_CLASSES)
    assert case.parameters == {}
    assert cases.editedState(case) == case.state
    assert "parameters" not in json.loads(cases.caseJson(case))


def test_a_parameter_the_generator_has_not_is_an_error(tmp_path):
    with open(os.path.join(CASES_FOLDER, "baseplate_2x2_light.json")) as file:
        data = json.load(file)
    data["parameters"] = {"gfBin1_heightUnit": 7}
    with pytest.raises(cases.TestCaseError, match="gfBin1_heightUnit"):
        cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)


@pytest.mark.parametrize("value", [0, -1, "40", True])
def test_a_parameter_has_to_be_a_positive_length(tmp_path, value):
    data = {"description": "a case", "generator": "bin", "settings": sample_settings(), "parameters": {"gfBin1_baseWidth": value}}
    with pytest.raises(cases.TestCaseError, match="gfBin1_baseWidth"):
        cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)


def test_written_parameters_read_back_and_are_listed_in_the_settings(tmp_path):
    data = {"description": "a case", "generator": "bin", "settings": sample_settings(), "parameters": {"gfBin1_baseLength": 50.5}}
    case = cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)
    assert json.loads(cases.caseJson(case))["parameters"] == {"gfBin1_baseLength": 50.5}
    settings = cases.caseSettings(case)
    assert dict(settings[2]["items"]) == {"gfBin1_baseLength": "50.5"}


def test_label_cases_are_there_and_load():
    loaded = {case.name: case for case in cases.loadCases(CASES_FOLDER, STATE_CLASSES)}
    for name in ("label_1u_screw_text", "label_2u_hardware", "label_25mm_free", "label_6u_text"):
        assert loaded[name].generator == cases.GENERATOR_LABEL


def test_label_lengths_come_in_mm():
    case = cases.loadCase(os.path.join(CASES_FOLDER, "label_25mm_free.json"), STATE_CLASSES)
    assert case.state.freeWidth == pytest.approx(2.5)
    assert case.state.baseWidth == pytest.approx(4.2)
    assert case.state.offsetX == pytest.approx(-0.01)
    assert case.state.offsetY == pytest.approx(0)
    # units of the grid stay as they are
    case = cases.loadCase(os.path.join(CASES_FOLDER, "label_2u_hardware.json"), STATE_CLASSES)
    assert case.state.widthUnits == 2


def test_label_cases_may_change_the_base_width():
    assert cases.PARAMETER_FIELDS[cases.GENERATOR_LABEL] == {'gfLabel1_baseWidth': 'baseWidth'}


def test_dividers_to_top_defaults_off_in_every_bin_case():
    loaded = cases.loadCases(CASES_FOLDER, STATE_CLASSES)
    for case in loaded:
        if case.generator == cases.GENERATOR_BIN and "dividers_to_top" not in case.name:
            assert case.state.hasDividersToTop is False, case.name


def test_a_case_is_built_in_a_hybrid_design_unless_it_says_part(tmp_path):
    hybrid = cases.loadCase(write_case_data(tmp_path, {"description": "a case", "generator": "bin", "settings": sample_settings()}), STATE_CLASSES)
    assert hybrid.designIntent == cases.DESIGN_INTENT_HYBRID
    assert "designIntent" not in json.loads(cases.caseJson(hybrid))
    data = {"description": "a case", "generator": "bin", "designIntent": "part", "settings": sample_settings()}
    part = cases.loadCase(write_case_data(tmp_path, data, name="part"), STATE_CLASSES)
    assert part.designIntent == cases.DESIGN_INTENT_PART
    assert json.loads(cases.caseJson(part))["designIntent"] == "part"


def test_an_unknown_design_intent_is_an_error(tmp_path):
    data = {"description": "a case", "generator": "bin", "designIntent": "assembly-ish", "settings": sample_settings()}
    with pytest.raises(cases.TestCaseError, match="design intent"):
        cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)


def test_bodies_the_generator_did_not_return_are_loose():
    # (key, name) of every body in the case document, the keys of those the generator returned
    design = [("a", "Bin 3x2x3"), ("b", "Raised dividers (1)"), ("c", "Bin 3x2x3 (1)")]
    assert cases.looseBodyNames(design, {"a", "c"}) == ["Raised dividers (1)"]
    assert cases.looseBodyNames(design, {"a", "b", "c"}) == []


def test_a_case_may_name_the_design_intent_it_leaves(tmp_path):
    data = {"description": "a case", "generator": "label", "designIntent": "part", "designIntentAfter": "hybrid",
            "settings": json.load(open(os.path.join(CASES_FOLDER, "label_1u_screw_text.json")))["settings"]}
    case = cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)
    assert case.designIntentAfter == cases.DESIGN_INTENT_HYBRID
    assert json.loads(cases.caseJson(case))["designIntentAfter"] == "hybrid"
    plain = cases.loadCase(os.path.join(CASES_FOLDER, "label_1u_screw_text.json"), STATE_CLASSES)
    assert plain.designIntentAfter is None
    assert "designIntentAfter" not in json.loads(cases.caseJson(plain))


def test_an_unknown_design_intent_after_is_an_error(tmp_path):
    data = {"description": "a case", "generator": "bin", "designIntentAfter": "assembly-ish", "settings": sample_settings()}
    with pytest.raises(cases.TestCaseError, match="design intent"):
        cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)


# A raised divider corner carries on from the compartment corner below without a ledge (p83, Joerg's hand test): small
# upward faces left where the two meet are reported. Faces as (area mm2, width mm, length mm), from Fusion
def test_ledges_reports_the_sickles_of_joergs_bin():
    faces = [(0.3635, 2.24, 1.33), (0.0542, 2.55, 2.55), (484.99, 125.5, 83.5)]
    notes = cases.raisedCornerLedges(faces)
    assert len(notes) == 2
    assert notes[0].startswith('ledge of 0.36 mm2')


def test_ledges_ignore_slivers_of_tangent_seams_and_big_faces():
    assert cases.raisedCornerLedges([(0.0001, 2.55, 2.55), (0.0, 0.0, 1.2), (12.0, 4.0, 3.0)]) == []


# Text of an insert stays one line per text line on the insert (p84, p70): letter bodies as (min x, min y, max x,
# max y) in mm, the insert 36 x 11 mm at the origin, the middle of each text line
INSERT_BOX = (0.0, 0.0, 36.0, 11.0)
ONE_LINE = [5.5]
TWO_LINES = [8.0, 3.0]


def test_text_on_one_line_inside_the_insert_passes():
    letters = [(1.0, 3.0, 4.5, 8.0), (5.0, 3.0, 8.0, 8.0), (9.0, 2.0, 12.0, 8.0)]
    assert cases.insertTextProblems(INSERT_BOX, letters, ONE_LINE) == []


def test_joergs_wrapped_welle_6mm_fails():
    # p84, measured in Joerg's document: "Welle" y 6.8 to 11.9 mm, "6mm" y -0.9 to 4.1 mm
    letters = [(1.0, 6.8, 6.0, 11.9), (6.5, 6.8, 18.1, 11.9), (1.0, -0.9, 13.0, 4.1)]
    notes = cases.insertTextProblems(INSERT_BOX, letters, ONE_LINE)
    assert any('line 1 in 2 bands' in note for note in notes)
    assert any('off the insert' in note for note in notes)


def test_text_past_the_right_edge_fails_unless_it_may_run_on():
    letters = [(1.0, 3.0, 20.0, 8.0), (21.0, 3.0, 37.5, 8.0)]
    assert any('off the insert' in note for note in cases.insertTextProblems(INSERT_BOX, letters, ONE_LINE))
    # a text made longer after building runs on to the right, still one line on the insert's height
    assert cases.insertTextProblems(INSERT_BOX, letters, ONE_LINE, mayRunOnRight=True) == []


def test_two_lines_are_two_bands():
    letters = [(1.0, 6.0, 10.0, 9.5), (1.0, 1.5, 8.0, 5.0)]
    assert cases.insertTextProblems(INSERT_BOX, letters, TWO_LINES) == []
    assert any('line 2 has no text' in note for note in cases.insertTextProblems(INSERT_BOX, letters[:1], TWO_LINES))


def test_text_parameters_are_set_after_building_and_listed(tmp_path):
    data = {"description": "a case", "generator": "label", "settings": label_settings(),
            "texts": {"gfLabel1_text1": "Welle 6mm h6 geschliffen"}}
    case = cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)
    assert case.texts == {"gfLabel1_text1": "Welle 6mm h6 geschliffen"}
    assert json.loads(cases.caseJson(case))["texts"] == {"gfLabel1_text1": "Welle 6mm h6 geschliffen"}
    assert any(section["title"] == "Texts set after building" for section in cases.caseSettings(case))


def test_a_case_without_texts_has_none():
    case = cases.loadCase(os.path.join(CASES_FOLDER, "label_1u_screw_text.json"), STATE_CLASSES)
    assert case.texts == {}
    assert "texts" not in json.loads(cases.caseJson(case))


@pytest.mark.parametrize("texts", [{"gfLabel1_width": "x"}, {"gfLabel1_text1": 3}, {"gfLabel1_baseWidth": "x"}])
def test_texts_have_to_be_text_parameters_of_an_insert(tmp_path, texts):
    data = {"description": "a case", "generator": "label", "settings": label_settings(), "texts": texts}
    with pytest.raises(cases.TestCaseError, match="text"):
        cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)


def test_only_label_cases_set_texts(tmp_path):
    data = {"description": "a case", "generator": "bin", "settings": sample_settings(), "texts": {"gfLabel1_text1": "x"}}
    with pytest.raises(cases.TestCaseError, match="text"):
        cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)


def test_joergs_welle_6mm_cases_are_there():
    loaded = {case.name: case for case in cases.loadCases(CASES_FOLDER, STATE_CLASSES)}
    joerg = loaded["label_1u_welle_6mm"]
    assert (joerg.state.line1, joerg.state.line2, joerg.state.showScrew, joerg.state.hardware, joerg.state.surface, joerg.state.isBold) ==         ("Welle 6mm", "", False, "none", "Flush", False)
    assert loaded["label_1u_welle_6mm_text_edited"].texts["gfLabel1_text1"].startswith("Welle 6mm")


def label_settings():
    with open(os.path.join(CASES_FOLDER, "label_1u_screw_text.json")) as file:
        return json.load(file)["settings"]


def test_a_descender_over_an_umlaut_of_the_next_line_is_still_two_lines():
    # review of round 9: "y" of line 1 reaches down to 5.2 mm, the dots of a capital U umlaut of line 2 up to 5.6 mm,
    # they overlap in height and are still two lines
    letters = [(1.0, 6.25, 3.0, 9.75), (3.2, 5.22, 5.0, 8.8), (1.0, 1.25, 3.0, 4.75), (1.3, 5.0, 2.7, 5.55)]
    assert cases.insertTextProblems(INSERT_BOX, letters, TWO_LINES) == []


def test_a_wrapped_line_is_found_among_others_close_to_it():
    # one line broken in two, its second row overlaps a letter hanging down from the first
    letters = [(1.0, 6.25, 10.0, 9.75), (1.0, 0.5, 8.0, 3.9), (1.0, 1.25, 8.0, 4.75)]
    notes = cases.insertTextProblems(INSERT_BOX, letters, ONE_LINE)
    assert any('in 2 bands' in note for note in notes)


def test_texts_and_parameters_in_one_case_are_an_error(tmp_path):
    # a build with the parameters from the start can't have the edited text, see editedState
    data = {"description": "a case", "generator": "label", "settings": label_settings(),
            "parameters": {"gfLabel1_baseWidth": 40.0}, "texts": {"gfLabel1_text1": "x"}}
    with pytest.raises(cases.TestCaseError, match="texts"):
        cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)


def test_letters_added_by_a_text_edit_get_names_in_reading_order():
    # Fusion names them after the user's language and its body count ("Körper12"), the snapshot pairs bodies by name
    names = cases.addedLetterNames("Gridfinity label 1U Welle 6mm", [(46.6, 3.1), (36.2, 3.1), (45.3, 3.1)])
    assert names == ["Gridfinity label 1U Welle 6mm text +3", "Gridfinity label 1U Welle 6mm text +1", "Gridfinity label 1U Welle 6mm text +2"]


def test_dots_above_their_letter_stay_in_its_band():
    # the dots of an i or an umlaut are bodies of their own, a little above the letter
    letters = [(1.0, 3.25, 2.0, 6.85), (2.2, 3.25, 2.7, 5.9), (2.2, 6.2, 2.7, 6.7), (3.0, 3.25, 6.0, 7.75)]
    assert cases.insertTextProblems(INSERT_BOX, letters, ONE_LINE) == []


def test_colored_cases_want_their_parts_in_the_color():
    # p86: the text and symbol bodies of a colored case carry the label appearance, the insert or bin itself doesn't
    wanted = 'Gridfinity label D02020'
    assert cases.colorProblems(wanted, ('Bin', None), [('Label text 1', wanted), ('Label text 2', wanted)]) == []
    assert cases.colorProblems(wanted, ('Bin', None), []) == ['no colored label bodies']
    assert cases.colorProblems(wanted, ('Bin', wanted), [('Label text 1', wanted)]) == ['Bin has the label color']
    assert cases.colorProblems(wanted, ('Bin', None), [('Label text 1', 'Steel')]) == [f'Label text 1 is Steel, not {wanted}']


def test_cases_of_round_10_are_there():
    loaded = {case.name: case for case in cases.loadCases(CASES_FOLDER, STATE_CLASSES)}
    assert loaded['label_1u_set_screw_hex'].state.head == 'none'
    assert loaded['label_1u_set_screw_hex'].state.driver == 'hex'
    assert loaded['label_1u_screw_text_colored'].state.textColor == '#D02020'
    assert loaded['bin_2x1x3_label_text_engraved_colored'].state.labelColor == '#2060D0'
    assert loaded['bin_2x1x3_label_icon_text_embossed_colored'].state.labelColor == '#D02020'
