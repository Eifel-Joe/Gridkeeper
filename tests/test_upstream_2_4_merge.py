"""
Round 12 (p13): the inputs of this fork in upstream's config, rebuild and per bin parameter mechanism of v2.4.0.0.
See dev-notes/specs/2026-11-15-upstream-2-4-merge.md
"""

import os
import sys
import json
import math
import types
import importlib.util
import pytest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_FOLDER = os.path.join(PROJECT_ROOT, "tests", "e2e", "cases")


def _load(name, *path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PROJECT_ROOT, *path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_tag_utils():
    # The module annotates with adsk.fusion types, so they only need to exist
    fusion = sys.modules.get("adsk.fusion") or types.ModuleType("adsk.fusion")
    for name in ("BRepBody", "Design", "UserParameter"):
        if not hasattr(fusion, name):
            setattr(fusion, name, type(name, (), {}))
    sys.modules["adsk.fusion"] = fusion
    sys.modules["adsk"].fusion = fusion
    return _load("tagUtils", "lib", "tagUtils.py")


configJson = _load("configJson", "lib", "configJson.py")
defaultSettings = _load("defaultSettings", "lib", "defaultSettings.py")
labelColors = _load("labelColors", "lib", "gridfinityUtils", "labelColors.py")
binState = _load("binInputState", "commands", "commandCreateBin", "inputState.py")
labelState = _load("labelInputState", "commands", "commandCreateLabel", "inputState.py")
tagUtils = _load_tag_utils()
BIN = configJson.GENERATOR_BIN
LABEL = configJson.GENERATOR_LABEL


def bin_defaults():
    return configJson.stateFromJson(BIN, binState.InputState, defaultSettings.BIN)


# --- our bin inputs have defaults and come in mm ---

def test_bin_defaults_have_our_inputs():
    state = bin_defaults()
    assert state.hasDividersToTop is False
    assert state.labelColor == ""
    # the play of a Cullenect insert in its socket, 0.3 mm like Cullenect, kept in cm
    assert state.cullenectSocketOffset == pytest.approx(0.03)


def test_socket_play_is_written_in_mm():
    state = bin_defaults()
    assert configJson.stateToJson(BIN, state)["cullenectSocketOffset"] == pytest.approx(0.3)


def test_cullenect_bin_with_color_and_dividers_round_trips():
    settings = {**defaultSettings.BIN, "labelStyle": "Cullenect", "cullenectSocketOffset": 0.45,
                "labelColor": "#D02020", "hasDividersToTop": True, "hasTab": True}
    state = configJson.stateFromJson(BIN, binState.InputState, settings)
    assert state.cullenectSocketOffset == pytest.approx(0.045)
    back = configJson.stateToJson(BIN, state)
    assert back == settings


def test_config_saved_by_upstream_keeps_our_inputs_from_the_dialog():
    current = configJson.stateFromJson(BIN, binState.InputState, {
        **defaultSettings.BIN, "labelColor": "#2060D0", "hasDividersToTop": True, "cullenectSocketOffset": 0.5,
    })
    upstream = {name: value for (name, value) in defaultSettings.BIN.items()
                if name not in ("labelColor", "hasDividersToTop", "cullenectSocketOffset")}
    (state, notes) = configJson.readConfig(json.dumps({"generator": BIN, "settings": upstream}), BIN, binState.InputState, current)
    assert state.labelColor == "#2060D0"
    assert state.hasDividersToTop is True
    assert state.cullenectSocketOffset == pytest.approx(0.05)
    missing = [name for (name, _) in notes.missing]
    assert sorted(missing) == ["cullenectSocketOffset", "hasDividersToTop", "labelColor"]


# --- the color of a config goes back into the dialog's dropdown and custom text ---

@pytest.mark.parametrize("color", ["", "#D02020", "#2060D0", "#A0B1C2"])
def test_label_color_goes_back_to_the_dialog_and_round_trips(color):
    (choice, custom) = labelColors.choiceOf(color)
    assert choice in labelColors.CHOICES
    assert labelColors.dialogColor(choice, custom) == color.upper()


# --- a text edit of a colored label rebuilds, a parameter edit would leave new letters uncolored (p120) ---

def test_text_of_an_uncolored_label_is_a_parameter_edit():
    assert labelColors.textEditByParameter("") is True


def test_text_of_a_colored_label_is_rebuilt():
    assert labelColors.textEditByParameter("#D02020") is False


# --- a rebuilt bin maps its tagged bodies, colored labels beside it aren't bins ---

class FakeAttributes:
    def __init__(self, tags):
        self.tags = tags

    def itemByName(self, group, name):
        value = self.tags.get(name)
        return types.SimpleNamespace(value=value) if value is not None else None


class FakeBody:
    def __init__(self, name, tags=None):
        self.name = name
        self.attributes = FakeAttributes(tags or {})


def test_only_the_bin_bodies_take_the_place_of_the_old_ones():
    tag = tagUtils.createTagValue("2.4.0.0")
    built = [FakeBody("Bin", {tagUtils.TAG_BIN: tag}), FakeBody("Label text 1"), FakeBody("Label text 2")]
    assert [body.name for body in tagUtils.taggedBodies(built, tagUtils.TAG_BIN)] == ["Bin"]


# --- inserts: config format for the shape test cases, a base width parameter of their own ---

def test_label_defaults_load():
    state = configJson.stateFromJson(LABEL, labelState.InputState, defaultSettings.LABEL)
    assert state.baseWidth == pytest.approx(4.2)
    assert configJson.stateToJson(LABEL, state) == defaultSettings.LABEL
    assert defaultSettings.SETTINGS[LABEL] is defaultSettings.LABEL


def test_label_lengths_are_in_mm():
    assert configJson.MM_FIELDS[LABEL] == {"baseWidth", "freeWidth", "offsetX", "offsetY"}


def test_label_builder_has_no_shared_parameters():
    path = os.path.join(PROJECT_ROOT, "commands", "commandCreateLabel", "labelBuilder.py")
    with open(path, encoding="utf-8") as file:
        source = file.read()
    assert "sharedParameters" not in source
    assert "LABEL_BASE_WIDTH_PARAMETER = 'baseWidth'" in source


def test_nothing_uses_the_removed_shared_parameters():
    for folder in ("commands", "lib"):
        for (root, _, files) in os.walk(os.path.join(PROJECT_ROOT, folder)):
            for fileName in files:
                if fileName.endswith(".py"):
                    with open(os.path.join(root, fileName), encoding="utf-8") as file:
                        assert "sharedParameters" not in file.read(), os.path.join(root, fileName)


# --- review round 12: a dialog rebuild of a Cullenect bin works the sockets out anew when the grid changes ---

def _load_cullenect():
    folder = os.path.join(PROJECT_ROOT, "lib", "gridfinityUtils")
    package = "cullenectMergePackage"
    if package not in sys.modules:
        packageSpec = importlib.util.spec_from_loader(package, loader=None, is_package=True)
        packageModule = importlib.util.module_from_spec(packageSpec)
        packageModule.__path__ = [folder]
        sys.modules[package] = packageModule
    spec = importlib.util.spec_from_file_location(package + ".cullenect", os.path.join(folder, "cullenect.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


cullenect = _load_cullenect()


@pytest.mark.parametrize("changed", [["baseWidth"], ["baseLength"], ["binHeight", "baseWidth"]])
def test_grid_change_of_a_cullenect_tab_is_rebuilt(changed):
    # the socket units and whether a compartment is deep enough for a socket are worked out when building
    assert cullenect.parameterEditKeepsSockets(True, True, changed) is False


@pytest.mark.parametrize("isCullenect, hasTab, changed", [
    (True, True, ["binHeight"]),
    (True, True, ["heightUnit"]),
    (False, True, ["baseWidth"]),
    (True, False, ["baseLength"]),
])
def test_other_parameter_edits_keep_the_sockets(isCullenect, hasTab, changed):
    assert cullenect.parameterEditKeepsSockets(isCullenect, hasTab, changed) is True


# --- review round 12: a bin without a label to color keeps the dialog's color choice ---

def test_a_bin_with_a_label_brings_its_color_back():
    assert labelColors.restoresColor("#D02020", True, False) is True
    # a label without a color clears the dialog's
    assert labelColors.restoresColor("", True, False) is True


@pytest.mark.parametrize("hasLabel, isCullenect", [(False, False), (True, True), (False, True)])
def test_a_bin_without_a_label_to_color_leaves_the_choice(hasLabel, isCullenect):
    assert labelColors.restoresColor("", hasLabel, isCullenect) is False


# --- round 11 merged in: the text style of an insert is a setting of its config, Heavy by default ---

def test_label_defaults_have_the_text_style_of_round_11():
    textStyles = _load("textStyles", "lib", "gridfinityUtils", "textStyles.py")
    assert defaultSettings.LABEL["textStyle"] == textStyles.DEFAULT_INSERT_STYLE
    assert "isBold" not in defaultSettings.LABEL


# --- master's 6c2743c (root component active after building) merged into upstream's rebuild-in-place builders: the
# wrapper that activates the root afterwards has to hand every argument of a rebuild on to the builder ---

import ast


def _function(path, name):
    with open(os.path.join(PROJECT_ROOT, *path), encoding="utf-8") as file:
        tree = ast.parse(file.read())
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def _parameters(function):
    return [argument.arg for argument in function.args.args]


@pytest.mark.parametrize("path, outer, inner", [
    (("commands", "commandCreateBin", "binBuilder.py"), "buildBin", "_buildBin"),
    (("commands", "commandCreateBaseplate", "baseplateBuilder.py"), "buildBaseplate", "_buildBaseplate"),
])
def test_builder_wrapper_hands_every_argument_on(path, outer, inner):
    # round 13: the wrapper works out the structure plan and builds through assembly.buildWithStructure, which leaves
    # the root active. Every argument of a rebuild still has to reach the builder, the plan comes on top
    wrapper = _function(path, outer)
    builder = _function(path, inner)
    calls = [node for node in ast.walk(wrapper) if isinstance(node, ast.Call) and getattr(node.func, "id", None) == inner]
    assert len(calls) == 1
    # a keyword argument has to go to the parameter of its own name
    assert all(keyword.arg == keyword.value.id for keyword in calls[0].keywords)
    passed = [argument.id for argument in calls[0].args] + [keyword.value.id for keyword in calls[0].keywords]
    assert passed == _parameters(builder)
    # only the plan is new, only whether the document may change is used up by the wrapper
    assert [name for name in passed if name not in _parameters(wrapper)] == ["plan"]
    assert [name for name in _parameters(wrapper) if name not in passed] in ([], ["mayChangeDocument"])
    # and the root is active again after it, also after a failed build
    assert "assembly.buildWithStructure" in ast.unparse(wrapper)


# --- review of the recursion fix: the label color of a state comes from that state, not from the dialog, so a
# config, clone or rebuild state that differs from the inputs gets its own (only the color choice is the dialog's) ---

def test_state_label_color_reads_the_state_not_the_dialog():
    function = _function(("commands", "commandCreateBin", "entry.py"), "stateLabelColor")
    read = {node.id for node in ast.walk(function) if isinstance(node, ast.Name)}
    for inputId in ("BIN_GENERATE_BODY_INPUT_ID", "BIN_HAS_TAB_INPUT_ID", "BIN_TYPE_DROPDOWN_ID", "BIN_TAB_LABEL_STYLE_INPUT_ID"):
        assert inputId not in read, inputId
