"""
Tests for model screenshot presets: presets extending each other, their options and the presets kept in the repo.
"""

import os
import json
import importlib.util
import pytest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRESETS_FOLDER = os.path.join(PROJECT_ROOT, "tools", "screenshots", "models")


def _load(name, *path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PROJECT_ROOT, *path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


presets = _load("modelPresets", "commands", "commandModelScreenshots", "presets.py")
cases = _load("testCases", "commands", "commandSnapshotTests", "testCases.py")
binState = _load("binInputState", "commands", "commandCreateBin", "inputState.py")
baseplateState = _load("baseplateInputState", "commands", "commandCreateBaseplate", "inputState.py")

labelState = _load("labelInputState", "commands", "commandCreateLabel", "inputState.py")
boxState = _load("boxInputState", "commands", "commandCreateBox", "inputState.py")
boxLabelState = _load("boxLabelInputState", "commands", "commandCreateBoxLabel", "inputState.py")
defaults = _load("defaultSettings", "lib", "defaultSettings.py")

STATE_CLASSES = {
    cases.GENERATOR_BIN: binState.InputState,
    cases.GENERATOR_BASEPLATE: baseplateState.InputState,
    cases.GENERATOR_LABEL: labelState.InputState,
    cases.GENERATOR_BOX: boxState.InputState,
    "boxLabel": boxLabelState.InputState,
}


def write(folder, name, data):
    (folder / name).write_text(json.dumps(data))


@pytest.fixture
def folder(tmp_path):
    write(tmp_path, "_base.json", {
        "description": "only to extend",
        "generator": "bin",
        "settings": {"binWidth": 2, "binLength": 3},
        "style": "shadedWithEdges",
    })
    return tmp_path


class TestExtends:
    def test_settings_merge_over_the_base(self, folder):
        write(folder, "wide.json", {"extends": "_base.json", "settings": {"binWidth": 4}})
        preset = presets.loadPreset(str(folder), "wide.json")
        assert preset.settings == {"binWidth": 4, "binLength": 3}
        assert preset.generator == "bin"

    def test_options_come_from_the_base(self, folder):
        write(folder, "wide.json", {"extends": "_base.json"})
        assert presets.loadPreset(str(folder), "wide.json").style == "shadedWithEdges"

    def test_description_is_not_inherited(self, folder):
        write(folder, "wide.json", {"extends": "_base.json"})
        assert presets.loadPreset(str(folder), "wide.json").description == ""

    def test_extends_a_chain(self, folder):
        write(folder, "wide.json", {"extends": "_base.json", "settings": {"binWidth": 4}})
        write(folder, "wide_tall.json", {"extends": "wide.json", "settings": {"binHeight": 8}})
        preset = presets.loadPreset(str(folder), "wide_tall.json")
        assert preset.settings == {"binWidth": 4, "binLength": 3, "binHeight": 8}

    def test_loop_is_an_error(self, folder):
        write(folder, "a.json", {"extends": "b.json"})
        write(folder, "b.json", {"extends": "a.json"})
        with pytest.raises(presets.PresetError, match="loop"):
            presets.loadPreset(str(folder), "a.json")

    def test_missing_base_is_an_error(self, folder):
        write(folder, "a.json", {"extends": "nope.json"})
        with pytest.raises(presets.PresetError, match="preset a"):
            presets.loadPreset(str(folder), "a.json")


class TestOptions:
    def test_defaults(self, folder):
        write(folder, "plain.json", {"extends": "_base.json"})
        preset = presets.loadPreset(str(folder), "plain.json")
        assert (preset.view, preset.camera, preset.width, preset.height, preset.transparent, preset.appearance) == \
            ("isoTopRight", "perspective", 2048, 2048, True, None)
        assert preset.output == presets.DEFAULT_OUTPUT
        assert (preset.margin, preset.supersample, preset.exposure, preset.saturation) == (0.06, 3, 0.85, 1.4)
        assert (preset.style, preset.color) == ("shadedWithEdges", "#4e79a7")

    @pytest.mark.parametrize("options, message", [
        ({"view": "sideways"}, "unknown view"),
        ({"view": {"eye": [1, 2]}}, "eye"),
        ({"view": {"eye": [1, 2, 3], "target": [0, 0, 0], "roll": 3}}, "unknown view keys"),
        ({"camera": "fisheye"}, "unknown camera"),
        ({"style": "sketchy"}, "unknown style"),
        ({"width": 0}, "width"),
        ({"margin": 0.5}, "margin"),
        ({"margin": "wide"}, "margin"),
        ({"supersample": 0}, "supersample"),
        ({"supersample": 2.5}, "supersample"),
        ({"color": "blue"}, "color"),
        ({"exposure": 4}, "exposure"),
        ({"exposure": "bright"}, "exposure"),
        ({"saturation": -1}, "saturation"),
        ({"color": "#4e79a"}, "color"),
        ({"colour": "blue"}, "unknown keys"),
        ({"file": ""}, "file is"),
        ({"file": "sub/toolclip"}, "file is"),
        ({"file": "toolclip.png"}, "file is"),
        ({"file": 3}, "file is"),
        ({"section": "middle"}, "section"),
        ({"section": {"plane": "xx"}}, "section plane"),
        ({"section": {"plane": "xz", "flip": 1}}, "section flip"),
        ({"section": {"plane": "xz", "at": 3}}, "unknown section keys"),
        ({"difference": "notches"}, "difference"),
        ({"difference": {"settings": {}, "color": "#d73a49"}}, "difference settings"),
        ({"difference": {"settings": {"hasLipNotches": False}, "color": "red"}}, "difference color"),
        ({"difference": {"settings": {"hasLipNotches": False}, "color": "#d73a49", "at": 1}}, "unknown difference keys"),
    ])
    def test_bad_options(self, folder, options, message):
        write(folder, "bad.json", {"extends": "_base.json", **options})
        with pytest.raises(presets.PresetError, match=message):
            presets.loadPreset(str(folder), "bad.json")

    def test_custom_view(self, folder):
        view = {"eye": [200, -300, 250], "target": [40, 60, 20]}
        write(folder, "custom.json", {"extends": "_base.json", "view": view})
        assert presets.loadPreset(str(folder), "custom.json").view == view

    def test_section(self, folder):
        write(folder, "cut.json", {"extends": "_base.json", "section": {"plane": "xz"}})
        assert presets.loadPreset(str(folder), "cut.json").section == {"plane": "xz", "flip": False, "offset": None}
        write(folder, "whole.json", {"extends": "_base.json"})
        assert presets.loadPreset(str(folder), "whole.json").section is None

    def test_difference(self, folder):
        difference = {"settings": {"hasLipNotches": False}, "color": "#d73a49"}
        write(folder, "notches.json", {"extends": "_base.json", "difference": difference})
        assert presets.loadPreset(str(folder), "notches.json").difference == difference
        write(folder, "plain.json", {"extends": "_base.json"})
        assert presets.loadPreset(str(folder), "plain.json").difference is None

    def test_color_can_be_turned_off(self, folder):
        write(folder, "own.json", {"extends": "_base.json", "color": None})
        assert presets.loadPreset(str(folder), "own.json").color is None

    def test_needs_a_generator(self, tmp_path):
        write(tmp_path, "bare.json", {"settings": {}})
        with pytest.raises(presets.PresetError, match="generator"):
            presets.loadPreset(str(tmp_path), "bare.json")


class TestLoadPresets:
    def test_skips_presets_only_to_extend(self, folder):
        write(folder, "wide.json", {"extends": "_base.json"})
        assert [preset.name for preset in presets.loadPresets(str(folder))] == ["wide"]

    def test_only(self, folder):
        write(folder, "a.json", {"extends": "_base.json"})
        write(folder, "b.json", {"extends": "_base.json"})
        assert [preset.name for preset in presets.loadPresets(str(folder), ["b"])] == ["b"]


class TestRepoPresets:
    """The presets in the repo build a state with every setting, as test cases do"""

    @pytest.mark.parametrize("preset", presets.loadPresets(PRESETS_FOLDER), ids=lambda preset: preset.name)
    def test_builds_a_state(self, preset):
        # over the dialog's defaults, as a test case and the palette (commandModelScreenshots.entry.presetState)
        settings = {**defaults.SETTINGS.get(preset.generator, {}), **preset.settings}
        cases.stateFromJson(preset.generator, STATE_CLASSES[preset.generator], settings)

    @pytest.mark.parametrize("preset", [preset for preset in presets.loadPresets(PRESETS_FOLDER) if preset.generator == cases.GENERATOR_BIN],
                             ids=lambda preset: preset.name)
    def test_custom_compartments_are_shown(self, preset):
        """The builder uses the pockets only while the compartments drawing is shown, see binBuilder"""
        merged = [pocket for pocket in preset.settings["compartmentPockets"] if pocket["width"] != 1 or pocket["length"] != 1]
        assert not merged or preset.settings["showCompartmentsLayout"]


class TestGridkeeperPresets:
    """Round 58: the palette makes the docs' model pictures, of every generator, from scripts too"""

    def test_pictures_go_into_the_docs(self):
        assert presets.DEFAULT_OUTPUT == os.path.join("docs", "assets", "models")

    def test_every_generator_can_be_pictured(self, tmp_path):
        for generator in ["bin", "baseplate", "label", "box", "boxLabel"]:
            write(tmp_path, f"{generator}.json", {"generator": generator, "settings": {}})
            assert presets.loadPreset(str(tmp_path), f"{generator}.json").generator == generator
        write(tmp_path, "other.json", {"generator": "shelf", "settings": {}})
        with pytest.raises(presets.PresetError, match="generator"):
            presets.loadPreset(str(tmp_path), "other.json")

    def test_a_sidecar_holds_what_the_finisher_needs(self, folder):
        write(folder, "wide.json", {"extends": "_base.json", "width": 1200, "height": 900, "margin": 0.05})
        preset = presets.loadPreset(str(folder), "wide.json")
        data = presets.sidecar(preset, os.path.join("raw", "wide.render.png"), os.path.join("repo"))
        assert data == {
            "name": "wide",
            "render": os.path.join("raw", "wide.render.png"),
            "output": os.path.join("repo", "docs", "assets", "models", "wide.png"),
            "width": 1200,
            "height": 900,
            "margin": 0.05,
            "transparent": True,
            "exposure": preset.exposure,
            "saturation": preset.saturation,
        }

    def test_a_section_can_be_away_from_the_middle(self, folder):
        # a magnet socket of a plate is 8 mm in from its edge, not in its middle
        write(folder, "cut.json", {"extends": "_base.json", "section": {"plane": "xz", "flip": True, "offset": 8}})
        assert presets.loadPreset(str(folder), "cut.json").section == {"plane": "xz", "flip": True, "offset": 8.0}
        write(folder, "middle.json", {"extends": "_base.json", "section": {"plane": "xz"}})
        assert presets.loadPreset(str(folder), "middle.json").section == {"plane": "xz", "flip": False, "offset": None}
        write(folder, "bad.json", {"extends": "_base.json", "section": {"plane": "xz", "offset": "8"}})
        with pytest.raises(presets.PresetError, match="offset"):
            presets.loadPreset(str(folder), "bad.json")


class TestDocsPictures:
    """Round 58: the docs' model pictures all come from the presets, and the presets are the docs' pictures"""

    DOCS = os.path.join(PROJECT_ROOT, "docs")

    def _usedPictures(self):
        import re
        used = set()
        for folder, _, files in os.walk(self.DOCS):
            for name in files:
                if name.endswith(".md"):
                    with open(os.path.join(folder, name), encoding="utf-8") as file:
                        used |= set(re.findall(r"assets/models/([A-Za-z0-9_-]+)\.png", file.read()))
        return used

    def test_every_picture_in_the_docs_has_a_preset(self):
        names = {preset.name for preset in presets.loadPresets(PRESETS_FOLDER)}
        assert self._usedPictures() - names == set()

    def test_every_preset_is_a_picture_of_the_docs(self):
        names = {preset.name for preset in presets.loadPresets(PRESETS_FOLDER)}
        assert names - self._usedPictures() == set()

    def test_every_preset_has_the_docs_look(self):
        for preset in presets.loadPresets(PRESETS_FOLDER):
            assert (preset.camera, preset.color, preset.width, preset.height, preset.output) == (
                "orthographic", "#4A82C8", 1200, 900, presets.DEFAULT_OUTPUT), preset.name



class TestPictureFile:
    """Round 59: a preset may name its picture's file, three hover pictures are each a toolclip.png"""

    def test_the_picture_is_named_after_the_preset_by_default(self, folder):
        write(folder, "wide.json", {"extends": "_base.json"})
        preset = presets.loadPreset(str(folder), "wide.json")
        assert preset.file == "wide"
        assert presets.sidecar(preset, "r.png", "repo")["output"] == os.path.join("repo", "docs", "assets", "models", "wide.png")

    def test_a_preset_names_its_picture(self, folder):
        write(folder, "label.json", {"extends": "_base.json", "file": "toolclip", "output": "commands/commandCreateLabel/resources"})
        preset = presets.loadPreset(str(folder), "label.json")
        data = presets.sidecar(preset, "r.png", "repo")
        assert (data["name"], data["output"]) == ("label", os.path.join("repo", "commands/commandCreateLabel/resources", "toolclip.png"))

    def test_the_file_is_not_passed_on(self, folder):
        write(folder, "_named.json", {"extends": "_base.json", "file": "toolclip"})
        write(folder, "other.json", {"extends": "_named.json"})
        assert presets.loadPreset(str(folder), "other.json").file == "other"


TOOL_CLIPS_FOLDER = os.path.join(PROJECT_ROOT, "tools", "screenshots", "toolclips")


class TestToolClipPresets:
    """Round 59: the hover pictures of the menu in the look of the original's bin and baseplate pictures"""

    def test_each_create_command_without_one_gets_a_picture(self):
        outputs = {preset.output.replace("\\", "/") for preset in presets.loadPresets(TOOL_CLIPS_FOLDER)}
        assert outputs == {f"commands/{command}/resources" for command in ("commandCreateLabel", "commandCreateBox", "commandCreateBoxLabel")}

    def test_each_writes_a_toolclip_beside_the_icons(self):
        for preset in presets.loadPresets(TOOL_CLIPS_FOLDER):
            assert preset.file == "toolclip", preset.name
            assert os.path.isfile(os.path.join(PROJECT_ROOT, preset.output, "32x32.png")), preset.name

    def test_each_has_the_look_of_the_originals(self):
        for preset in presets.loadPresets(TOOL_CLIPS_FOLDER):
            assert (preset.width, preset.height, preset.transparent, preset.style, preset.camera, preset.view) == (
                300, 230, True, "shadedWithEdges", "orthographic", "isoTopRight"), preset.name

    def test_each_builds_a_state(self):
        for preset in presets.loadPresets(TOOL_CLIPS_FOLDER):
            cases.stateFromJson(preset.generator, STATE_CLASSES[preset.generator],
                                {**cases.DEFAULT_SETTINGS.get(preset.generator, {}), **preset.settings})
