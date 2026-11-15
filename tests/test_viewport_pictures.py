"""
Tests for the appearance the snapshot previews and model pictures are colored with (round 16, p31): a library named
in another language has no 'Plastic', the one the label colors are copied from is taken then, see
appearanceUtils.baseAppearance.
"""

import os
import sys
import types
import importlib.util

import pytest

PACKAGE = "viewportPicturesTestPackage"


class _AppearanceError(Exception):
    pass


def _load():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # the module annotates with Fusion types, they only need to exist while it loads
    stubs = [(sys.modules["adsk.core"], ("Appearances", "Appearance", "Viewport", "ColorProperty")), (sys.modules["adsk.fusion"], ("Design",))]
    added = [(module, name) for (module, names) in stubs for name in names if not hasattr(module, name)]
    for (module, name) in added:
        setattr(module, name, type(name, (), {}))
    try:
        for (name, path) in ((PACKAGE, []), (f"{PACKAGE}.ui", [os.path.join(project_root, "lib", "ui")]), (f"{PACKAGE}.gridfinityUtils", [])):
            package = types.ModuleType(name)
            package.__path__ = path
            sys.modules[name] = package
        # the real one needs Fusion's material libraries, this one stands in for it
        fake = types.ModuleType(f"{PACKAGE}.gridfinityUtils.appearanceUtils")
        fake.AppearanceError = _AppearanceError
        fake.baseAppearance = lambda: "base appearance"
        sys.modules[fake.__name__] = fake
        sys.modules[f"{PACKAGE}.gridfinityUtils"].appearanceUtils = fake
        spec = importlib.util.spec_from_file_location(f"{PACKAGE}.ui.viewportPictures", os.path.join(project_root, "lib", "ui", "viewportPictures.py"))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return (mod, fake)
    finally:
        for (module, name) in added:
            delattr(module, name)


(pictures, appearanceUtils) = _load()


class _Named:
    def __init__(self, name):
        self.name = name


class _Appearances:
    def __init__(self, names):
        self.items = [_Named(name) for name in names]
        self.count = len(self.items)

    def item(self, index):
        return self.items[index]


def _libraries(*names):
    return [types.SimpleNamespace(appearances=_Appearances(names))]


@pytest.fixture
def app(monkeypatch):
    fake = types.SimpleNamespace(materialLibraries=[])
    monkeypatch.setattr(pictures, "app", fake)
    return fake


def test_a_plastic_appearance_is_taken_first(app):
    app.materialLibraries = _libraries("Glas", "Plastic - Matte (Blue)", "Plastic - Glossy")
    assert pictures.firstLibraryAppearance(pictures.COLOR_BASE_PREFIXES).name == "Plastic - Matte (Blue)"


def test_a_german_library_falls_back_to_the_label_color_base(app):
    app.materialLibraries = _libraries("Kunststoff - matt (Blau)", "Stahl - satiniert")
    assert pictures.firstLibraryAppearance(pictures.COLOR_BASE_PREFIXES) == "base appearance"


def test_without_any_base_it_is_a_picture_error(app, monkeypatch):
    app.materialLibraries = _libraries("Kunststoff - matt (Blau)")
    def none():
        raise _AppearanceError("no appearance with a color in the material libraries")
    monkeypatch.setattr(appearanceUtils, "baseAppearance", none)
    with pytest.raises(pictures.PictureError):
        pictures.firstLibraryAppearance(pictures.COLOR_BASE_PREFIXES)
