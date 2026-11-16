"""
Tests for bin tag values: creation, tolerant parsing and the generator version lookup.
"""

import sys
import os
import json
import types
import importlib.util
import pytest


def _load_tag_utils():
    # The module annotates with adsk.fusion types, so they only need to exist
    fusion = sys.modules.get("adsk.fusion") or types.ModuleType("adsk.fusion")
    for name in ("BRepBody", "Design", "UserParameter"):
        if not hasattr(fusion, name):
            setattr(fusion, name, type(name, (), {}))
    sys.modules["adsk.fusion"] = fusion
    sys.modules["adsk"].fusion = fusion

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(project_root, "lib", "tagUtils.py")
    spec = importlib.util.spec_from_file_location("tagUtils", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tagUtils = _load_tag_utils()


def test_created_value_round_trips():
    tag = tagUtils.parseTagValue(tagUtils.createTagValue("1.4.3.0"))
    assert tag == {"schemaVersion": tagUtils.TAG_SCHEMA_VERSION, "generatorVersion": "1.4.3.0"}


def test_unknown_fields_are_kept_for_newer_readers():
    tag = tagUtils.parseTagValue(json.dumps({"schemaVersion": 1, "futureField": [1, 2]}))
    assert tag["schemaVersion"] == 1
    assert tag["futureField"] == [1, 2]


@pytest.mark.parametrize("value", ["", "not json", None, "[1, 2]", "42", '"text"'])
def test_unreadable_value_still_yields_dict(value):
    assert tagUtils.parseTagValue(value) == {}


def test_generator_version_matches_manifest():
    with open(tagUtils.MANIFEST_PATH, "r") as manifest:
        expected = json.load(manifest)["version"]
    tagUtils._generatorVersion = None
    assert tagUtils.getGeneratorVersion() == expected


def test_missing_manifest_gives_empty_version(monkeypatch):
    monkeypatch.setattr(tagUtils, "MANIFEST_PATH", "/nonexistent/Gridkeeper.manifest")
    monkeypatch.setattr(tagUtils, "_generatorVersion", None)
    assert tagUtils.getGeneratorVersion() == ""


def test_settings_are_stored_when_given():
    settings = [{"title": "Basic sizes", "items": [["Bin width (u)", "2"]]}]
    tag = tagUtils.parseTagValue(tagUtils.createTagValue("1.6.0.0", settings))
    assert tag["settings"] == settings


def test_settings_are_left_out_when_not_given():
    assert "settings" not in tagUtils.parseTagValue(tagUtils.createTagValue("1.6.0.0"))


def test_config_is_kept_to_build_the_body_again():
    config = {"binWidth": 2, "shapeCells": [[0, 0]]}
    tag = tagUtils.parseTagValue(tagUtils.createTagValue("1.6.0.0", config=config))
    assert tag["config"] == config


def test_config_is_left_out_when_not_given():
    assert "config" not in tagUtils.parseTagValue(tagUtils.createTagValue("1.6.0.0"))


class _FakeAttribute:
    def __init__(self, parent, value):
        self.parent = parent
        self.value = value


class _FakeAttributes:
    def __init__(self):
        self.byName = {}

    def add(self, group, name, value):
        self.byName[(group, name)] = value

    def itemByName(self, group, name):
        value = self.byName.get((group, name))
        return _FakeAttribute(None, value) if value is not None else None


class _FakeParameter:
    def __init__(self, name):
        self.name = name
        self.attributes = _FakeAttributes()


def test_body_id_and_parameter_field_and_owner_are_kept():
    tag = tagUtils.parseTagValue(tagUtils.createTagValue("2.3.0.0", bodyId="gfBin3"))
    assert tag["id"] == "gfBin3"
    tag = tagUtils.parseTagValue(tagUtils.createTagValue("2.3.0.0", field="binHeight", owner="gfBin3"))
    assert (tag["field"], tag["owner"]) == ("binHeight", "gfBin3")
    assert "id" not in tag


def test_a_parameter_tagged_again_keeps_the_last_field():
    parameter = _FakeParameter("gfBin3_label")
    tagUtils.tagParameterField(parameter, "labelText", "gfBin3")
    tagUtils.tagParameterField(parameter, "compartmentPockets.0.label", "gfBin3")
    assert tagUtils.readParameterField(parameter) == "compartmentPockets.0.label"
    assert tagUtils.readParameterTag(parameter)["owner"] == "gfBin3"


def test_an_untagged_parameter_has_no_field():
    assert tagUtils.readParameterField(_FakeParameter("gfBaseWidth")) is None


def test_owned_parameters_are_found_by_their_owner(monkeypatch):
    parameters = [_FakeParameter("gfBin1_heightU"), _FakeParameter("gfBin2_heightU")]
    tagUtils.tagParameterField(parameters[0], "binHeight", "gfBin1")
    tagUtils.tagParameterField(parameters[1], "binHeight", "gfBin2")

    class _Design:
        def findAttributes(self, group, name):
            return [_FakeAttribute(parameter, parameter.attributes.byName[(group, name)]) for parameter in parameters]

    monkeypatch.setattr(tagUtils.adsk.fusion.UserParameter, "cast", staticmethod(lambda parent: parent), raising=False)
    assert tagUtils.findOwnedParameters(_Design(), "gfBin2") == [(parameters[1], "binHeight")]


def test_container_names_are_literal():
    # stored in user documents and shown in the browser, the user's names (round 13, p90)
    assert tagUtils.TAG_CONTAINER == "container"
    assert tagUtils.CONTAINER_NAMES == {"grid": "Grid", "bins": "Bins", "labels": "Label"}
    assert (tagUtils.KIND_GRID, tagUtils.KIND_BINS, tagUtils.KIND_LABELS) == ("grid", "bins", "labels")


def test_pocket_tag_is_literal():
    assert tagUtils.TAG_POCKET == "pocket"


# ── p71: a letter of a longer text in Text has no tag of its own, the part it's of answers for it ──────────────────


class _Attributes:
    def __init__(self, tags=None):
        self.tags = tags or {}

    def itemByName(self, group, name):
        value = self.tags.get(name) if group == tagUtils.TAG_GROUP else None
        return types.SimpleNamespace(value=value) if value is not None else None


class _Component:
    def __init__(self, bodies=None, name='Text'):
        self.bRepBodies = bodies or []
        self.name = name


class _Body:
    """A native body, or a proxy of one through an occurrence"""
    def __init__(self, component, tags=None, native=None, occurrence=None):
        self.parentComponent = component
        self.attributes = _Attributes(tags)
        self.nativeObject = native
        self.assemblyContext = occurrence
        if native is None:
            component.bRepBodies.append(self)


class _Occurrence:
    def __init__(self, component, parent=None):
        self.component = component
        self.assemblyContext = parent


def _part(tagName):
    """A part with a tagged body, its occurrence, and a Text occurrence in it with an untagged letter"""
    partComponent = _Component(name='Gridfinity bin 1x2x3')
    tagged = _Body(partComponent, {tagName: json.dumps({"id": "gfX"})})
    partOccurrence = _Occurrence(partComponent)
    textComponent = _Component()
    letter = _Body(textComponent)
    textOccurrence = _Occurrence(textComponent, partOccurrence)
    return (tagged, partOccurrence, textComponent, letter, textOccurrence)


def test_tagged_body_is_its_own_part():
    (tagged, partOccurrence, *_) = _part(tagUtils.TAG_BIN)
    proxy = _Body(tagged.parentComponent, native=tagged, occurrence=partOccurrence)
    assert tagUtils.partTag(proxy, lambda component: None) == (tagged, tagUtils.TAG_BIN, {"id": "gfX"})


def test_untagged_letter_in_text_finds_the_insert_base():
    (base, _, _, letter, textOccurrence) = _part(tagUtils.TAG_LABEL)
    proxy = _Body(letter.parentComponent, native=letter, occurrence=textOccurrence)
    assert tagUtils.partTag(proxy, lambda component: None) == (base, tagUtils.TAG_LABEL, {"id": "gfX"})


def test_untagged_letter_of_a_bin_finds_the_bin_body():
    (binBody, _, _, letter, textOccurrence) = _part(tagUtils.TAG_BIN)
    proxy = _Body(letter.parentComponent, native=letter, occurrence=textOccurrence)
    (found, tagName, _) = tagUtils.partTag(proxy, lambda component: None)
    assert found is binBody and tagName == tagUtils.TAG_BIN


def test_native_letter_uses_the_occurrence_of_its_component():
    (base, _, textComponent, letter, textOccurrence) = _part(tagUtils.TAG_LABEL)
    occurrenceOf = lambda component: textOccurrence if component is textComponent else None
    assert tagUtils.partTag(letter, occurrenceOf)[0] is base


def test_root_body_without_tag_has_no_part():
    loose = _Body(_Component())
    assert tagUtils.partTag(loose, lambda component: None) is None


def test_body_in_a_part_without_a_parent_part_has_no_part():
    (_, _, _, letter, textOccurrence) = _part(tagUtils.TAG_BIN)
    # a Text occurrence straight in the root, nothing above it
    textOccurrence.assemblyContext = None
    assert tagUtils.partTag(letter, lambda component: textOccurrence) is None


def test_untagged_body_outside_a_text_component_has_no_part():
    # a bin nested in the user's own assembly: an untagged body of the user's isn't a letter of the part above it
    (_, partOccurrence, _, _, _) = _part(tagUtils.TAG_BIN)
    userComponent = _Component(name='Bracket')
    userBody = _Body(userComponent)
    userOccurrence = _Occurrence(userComponent, partOccurrence)
    proxy = _Body(userComponent, native=userBody, occurrence=userOccurrence)
    assert tagUtils.partTag(proxy, lambda component: None) is None
