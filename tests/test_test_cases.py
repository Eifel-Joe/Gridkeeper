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


def test_a_missing_setting_is_an_error(tmp_path):
    settings = sample_settings()
    del settings["hasLip"]
    with pytest.raises(cases.TestCaseError, match="hasLip"):
        cases.loadCase(write_case(tmp_path, settings), STATE_CLASSES)


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
    case = cases.loadCase(os.path.join(CASES_FOLDER, "bin_2x3x5_features.json"), STATE_CLASSES)
    settings = json.loads(cases.caseJson(case))["settings"]
    assert settings["wallThickness"] == 1.2
    assert settings["tabOverhangAngle"] == 45


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
    data = {"description": "a case", "generator": "bin", "settings": sample_settings(), "parameters": {"gfBaseWidth": 40, "gfHeightUnit": 5}}
    case = cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)
    assert case.parameters == {"gfBaseWidth": pytest.approx(4.0), "gfHeightUnit": pytest.approx(0.5)}
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
    data["parameters"] = {"gfHeightUnit": 7}
    with pytest.raises(cases.TestCaseError, match="gfHeightUnit"):
        cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)


@pytest.mark.parametrize("value", [0, -1, "40", True])
def test_a_parameter_has_to_be_a_positive_length(tmp_path, value):
    data = {"description": "a case", "generator": "bin", "settings": sample_settings(), "parameters": {"gfBaseWidth": value}}
    with pytest.raises(cases.TestCaseError, match="gfBaseWidth"):
        cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)


def test_written_parameters_read_back_and_are_listed_in_the_settings(tmp_path):
    data = {"description": "a case", "generator": "bin", "settings": sample_settings(), "parameters": {"gfBaseLength": 50.5}}
    case = cases.loadCase(write_case_data(tmp_path, data), STATE_CLASSES)
    assert json.loads(cases.caseJson(case))["parameters"] == {"gfBaseLength": 50.5}
    settings = cases.caseSettings(case)
    assert dict(settings[2]["items"]) == {"gfBaseLength": "50.5"}


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
    assert cases.PARAMETER_FIELDS[cases.GENERATOR_LABEL] == {'gfBaseWidth': 'baseWidth'}


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


# A raised divider corner carries on from the compartment corner below without a ledge (p83, the user's hand test): small
# upward faces left where the two meet are reported. Faces as (area mm2, width mm, length mm), from Fusion
def test_ledges_reports_the_sickles_of_bin():
    faces = [(0.3635, 2.24, 1.33), (0.0542, 2.55, 2.55), (484.99, 125.5, 83.5)]
    notes = cases.raisedCornerLedges(faces)
    assert len(notes) == 2
    assert notes[0].startswith('ledge of 0.36 mm2')


def test_ledges_ignore_slivers_of_tangent_seams_and_big_faces():
    assert cases.raisedCornerLedges([(0.0001, 2.55, 2.55), (0.0, 0.0, 1.2), (12.0, 4.0, 3.0)]) == []
