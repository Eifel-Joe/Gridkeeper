"""
Tests for the Cullenect label system: insert and socket sizes, how wide a socket fits a tab, and the tab it needs.
Dimensions follow Cullenect.scad by CullenJWebb (MIT), https://github.com/CullenJWebb/Cullenect-Labels
"""

import math
import os
import sys
import importlib.util

import pytest
from pytest import approx


def _load_cullenect():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(project_root, "lib", "gridfinityUtils")
    # cullenect imports const as a sibling module, load both under a throwaway package
    package = "cullenectTestPackage"
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


def test_label_width_follows_cullenect():
    assert cullenect.labelWidth(1) == approx(3.6)
    assert cullenect.labelWidth(2) == approx(7.8)
    assert cullenect.labelWidth(1, 4.0, 0.01) == approx(3.41)


def test_socket_is_label_plus_offset():
    assert cullenect.socketWidth(1, 4.2, 0.03) == approx(3.63)
    assert cullenect.socketHeight(0.03) == approx(1.13)


@pytest.mark.parametrize("available, units", [
    (3.91, 1.0),     # 1x1 bin, 1.2 mm walls
    (4.0375, 1.0),   # 1x1 compartment of a 4x2 bin
    (8.195, 2.0),    # compartment over 2 cells of a 4x2 bin
    (16.51, 4.0),    # compartment over 4 cells
    (3.55, 0.5),     # 1x1 bin with 3 mm walls
    (1.5, None),     # not even half a unit
])
def test_socket_units_take_the_widest_standard_label_that_fits(available, units):
    assert cullenect.socketUnits(available, 4.2, 0.03) == units


def test_front_inset_keeps_the_margin_at_45_degrees():
    allowance = 0.06 / math.tan(math.radians(45) / 2)
    assert cullenect.socketFrontInset(math.radians(45), allowance) == approx(0.1)


def test_steep_overhang_pushes_the_socket_back_and_widens_the_tab():
    allowance = 0.06 / math.tan(math.radians(10) / 2)
    inset = cullenect.socketFrontInset(math.radians(80), allowance)
    assert inset == approx(0.16 * math.tan(math.radians(80)) - allowance)
    assert cullenect.effectiveTabWidth(1.3, math.radians(80), allowance, 0.03) == approx(1.13 + 2 * inset)


def test_tab_width_is_raised_to_14_mm_but_wider_user_tabs_stay():
    a = math.radians(45)
    allowance = 0.06 / math.tan(a / 2)
    assert cullenect.effectiveTabWidth(1.3, a, allowance, 0.03) == approx(1.4)
    assert cullenect.effectiveTabWidth(1.8, a, allowance, 0.03) == approx(1.8)


def test_tab_span_is_trimmed_to_the_compartment():
    assert cullenect.tabSpanInCompartment(4.0375, 0, 16.8) == approx(4.0375)
    assert cullenect.tabSpanInCompartment(8.195, 4.2, 4.2) == approx(3.995)


def test_describe_socket():
    assert cullenect.describeSocket(1.0, 4.2, 0.03) == "1U: pocket 36.3 mm, insert 36 mm"
    assert cullenect.describeSocket(0.5, 4.2, 0.03) == "0.5U: pocket 15.3 mm, insert 15 mm"
    assert cullenect.describeSocket(None, 4.2, 0.03) == "too short for a Cullenect pocket"


def _labelGeneratorConstants():
    # labelGenerator needs Fusion to load, its module constants are read from the source instead
    import ast
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(project_root, "lib", "gridfinityUtils", "labelGenerator.py")
    with open(path, encoding="utf-8") as file:
        tree = ast.parse(file.read())
    names = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            value = node.value
            if isinstance(value, ast.Constant):
                names[node.targets[0].id] = value.value
            elif isinstance(value, ast.List) and all(isinstance(item, ast.Name) for item in value.elts):
                names[node.targets[0].id] = [names[item.id] for item in value.elts]
    return names


def test_cullenect_is_a_label_style():
    names = _labelGeneratorConstants()
    assert names["LABEL_STYLE_CULLENECT"] == "Cullenect"
    assert names["LABEL_STYLES"] == ["Outline", "Engraved", "Embossed", "Cullenect"]


def test_hollow_cullenect_tab_keeps_a_skin_under_the_socket():
    assert cullenect.hollowTabWallThickness(0.12) == approx(0.16)
    assert cullenect.hollowTabWallThickness(0.2) == approx(0.2)
