"""
Tests for coloring label text and symbols (round 14, p120): the color goes to the Text component's occurrence, so the
letters a longer text adds show it too, and stays on the bodies as before when the 3MF export needs it there.
"""

import os
import sys
import types
import importlib.util

import pytest


def _load():
    # the module annotates with Fusion types, they only need to exist while it loads, other tests check for them
    stubs = [(sys.modules["adsk.core"], ("Appearance", "ColorProperty")), (sys.modules["adsk.fusion"], ("Design", "BRepBody", "Occurrence"))]
    added = [(module, name) for (module, names) in stubs for name in names if not hasattr(module, name)]
    for (module, name) in added:
        setattr(module, name, type(name, (), {}))
    try:
        return _loadModule()
    finally:
        for (module, name) in added:
            delattr(module, name)


def _loadModule():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(project_root, "lib", "gridfinityUtils")
    package = "appearanceUtilsTestPackage"
    if package not in sys.modules:
        packageSpec = importlib.util.spec_from_loader(package, loader=None, is_package=True)
        packageModule = importlib.util.module_from_spec(packageSpec)
        packageModule.__path__ = [folder]
        sys.modules[package] = packageModule
        # commonUtils pulls in the add-in's config and Fusion's log, only debugLog is used here
        commonUtils = types.ModuleType(f"{package}.commonUtils")
        commonUtils.debugLog = lambda *args, **kwargs: None
        sys.modules[commonUtils.__name__] = commonUtils
    spec = importlib.util.spec_from_file_location(f"{package}.appearanceUtils", os.path.join(folder, "appearanceUtils.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


appearanceUtils = _load()

RED = "#FF0000"


class _Colorable:
    def __init__(self):
        self.appearance = None
        self.parentComponent = types.SimpleNamespace(parentDesign="design")


@pytest.fixture
def appearances(monkeypatch):
    """The appearances asked for, by design and color"""
    asked = []
    def labelAppearance(design, color):
        asked.append((design, color))
        return f"appearance {color}"
    monkeypatch.setattr(appearanceUtils, "labelAppearance", labelAppearance)
    return asked


def test_color_goes_to_the_text_occurrence(appearances):
    occurrence = _Colorable()
    bodies = [_Colorable(), _Colorable()]
    appearanceUtils.colorPart(bodies, occurrence, RED, colorBodiesToo=False)
    assert occurrence.appearance == f"appearance {RED}"
    assert [body.appearance for body in bodies] == [None, None]
    assert appearances == [("design", RED)]


def test_bodies_keep_the_color_when_asked(appearances):
    occurrence = _Colorable()
    bodies = [_Colorable(), _Colorable()]
    appearanceUtils.colorPart(bodies, occurrence, RED, colorBodiesToo=True)
    assert occurrence.appearance == f"appearance {RED}"
    assert [body.appearance for body in bodies] == [f"appearance {RED}"] * 2
    assert len(appearances) == 1


def test_no_color_touches_nothing(appearances):
    occurrence = _Colorable()
    bodies = [_Colorable()]
    appearanceUtils.colorPart(bodies, occurrence, "", colorBodiesToo=True)
    assert occurrence.appearance is None and bodies[0].appearance is None
    assert appearances == []


def test_without_occurrence_only_bodies_are_colored(appearances):
    bodies = [_Colorable()]
    appearanceUtils.colorPart(bodies, None, RED, colorBodiesToo=False)
    # bodies in the root have no Text component to carry the color, they keep it themselves
    assert bodies[0].appearance == f"appearance {RED}"


def test_nothing_to_color_asks_for_no_appearance(appearances):
    appearanceUtils.colorPart([], None, RED, colorBodiesToo=True)
    assert appearances == []


def test_by_default_only_the_occurrence_is_colored(appearances):
    # Fusion 15.11.2026 (round 14 probe): with the color on the Text occurrence alone the letters a longer text adds
    # show it and the 3MF export carries it, so the bodies don't need it themselves (spec, decision 2)
    occurrence = _Colorable()
    bodies = [_Colorable()]
    appearanceUtils.colorPart(bodies, occurrence, RED)
    assert occurrence.appearance == f"appearance {RED}"
    assert bodies[0].appearance is None


# Nutzer 17.11.2026: "Im Übrigen brauchen Latches, Hinge, Handle und Pin eine andere Farbe als die Box und der Deckel."
# Orange like the latch in Pred's file (the main session's choice, Nutzer may change it), one appearance per document

def test_the_small_parts_have_an_appearance_of_their_own():
    appearanceUtils = _load()
    assert appearanceUtils.BOX_PARTS_APPEARANCE == "Gridkeeper box parts"
    assert appearanceUtils.BOX_PARTS_COLOR == "#F07800"


def test_the_box_parts_appearance_is_made_once_by_name(monkeypatch):
    appearanceUtils = _load()
    calls = []
    monkeypatch.setattr(appearanceUtils, "namedAppearance", lambda design, name, color: calls.append((design, name, color)) or "appearance")
    assert appearanceUtils.boxPartsAppearance("design") == "appearance"
    assert calls == [("design", "Gridkeeper box parts", "#F07800")]
