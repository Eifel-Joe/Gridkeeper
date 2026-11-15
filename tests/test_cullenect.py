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
    assert cullenect.LABEL_STYLE == names["LABEL_STYLE_CULLENECT"]
    assert names["LABEL_STYLES"] == ["Outline", "Engraved", "Embossed", "Cullenect"]


def test_hollow_cullenect_tab_keeps_a_skin_under_the_socket():
    assert cullenect.hollowTabWallThickness(0.12) == approx(0.16)
    assert cullenect.hollowTabWallThickness(0.2) == approx(0.2)


CELL = 4.0375   # compartment grid cell of a 4x2 bin with four columns, 1.2 mm walls
WALL = 0.12


def test_socket_summary_lists_each_width_once():
    # mixed 4x2 bin: one compartment over 4 cells, one over 2 and two single ones
    widths = [CELL * 4 + WALL * 3, CELL * 2 + WALL, CELL, CELL]
    assert cullenect.socketSummary(widths, 0, 16.8, 4.2, 0.03) == [
        "1U: pocket 36.3 mm, insert 36 mm",
        "2U: pocket 78.3 mm, insert 78 mm",
        "4U: pocket 162.3 mm, insert 162 mm",
    ]
    # tabs one unit long give every compartment a 1U socket
    assert cullenect.socketSummary(widths, 0, 4.2, 4.2, 0.03) == ["1U: pocket 36.3 mm, insert 36 mm"]


def test_socket_summary_names_tabs_too_short():
    assert cullenect.socketSummary([1.5, CELL], 0, 4.2, 4.2, 0.03) == [
        "too short for a Cullenect pocket",
        "1U: pocket 36.3 mm, insert 36 mm",
    ]


@pytest.mark.parametrize("style, enabled", [
    ("Cullenect", {"text": False, "icon": False, "bold": False, "color": False, "topAngle": False, "socketOffset": True}),
    ("Outline", {"text": True, "icon": True, "bold": True, "color": True, "topAngle": True, "socketOffset": False}),
    ("Engraved", {"text": True, "icon": True, "bold": True, "color": True, "topAngle": True, "socketOffset": False}),
])
def test_label_inputs_follow_the_style(style, enabled):
    assert cullenect.labelInputsEnabled(style) == enabled


def test_switching_back_from_cullenect_keeps_user_values():
    # the dialog only enables and disables inputs, the values the user typed stay in the state
    state = {"labelStyle": "Outline", "tabWidth": 1.3, "labelText": "M3", "tabTopAngle": 0.3}
    before = dict(state)
    for style in ("Cullenect", "Outline"):
        state["labelStyle"] = style
        cullenect.labelInputsEnabled(style)
    assert {key: value for key, value in state.items() if key != "labelStyle"} == {key: value for key, value in before.items() if key != "labelStyle"}


def test_compartment_widths_split_the_interior_like_the_bin():
    interior = 4.2 * 4 - 2 * (0.12 + 0.025)
    widths = cullenect.compartmentWidths(interior, 4, [4, 2, 1, 1], WALL)
    assert widths == [approx(CELL * 4 + WALL * 3), approx(CELL * 2 + WALL), approx(CELL), approx(CELL)]


def test_a_single_cavity_is_one_compartment_over_the_interior():
    # creased bins build one cavity whatever compartment grid the dialog keeps
    assert cullenect.compartmentWidths(12.31, 1, [1], WALL) == [approx(12.31)]


@pytest.mark.parametrize("compartmentLength, fits", [
    (3.91, True),     # 1x1 bin
    (2.62, True),     # three rows on a two units long bin
    (1.22, False),    # three rows on a one unit long bin, the 14 mm tab fills it
])
def test_socket_needs_room_in_front_of_it_inside_the_compartment(compartmentLength, fits):
    assert cullenect.socketFitsDepth(compartmentLength, 1.4, 0.03) is fits


# --- round 13 (p160): joint origins on the floor of each pocket, found by the label command by their tag

def test_pocket_joint_origin_name_single_and_compartments():
    assert cullenect.pocketJointOriginName(0, 1) == "Pocket joint origin"
    assert cullenect.pocketJointOriginName(1, 3) == "Compartment 2 pocket joint origin"


def test_pocket_size_mm_matches_socket():
    (width, height) = cullenect.pocketSizeMm(1, 4.2, 0.03)
    assert width == approx(cullenect.socketWidth(1, 4.2, 0.03) * 10)
    assert height == approx(cullenect.socketHeight(0.03) * 10)
    assert (width, height) == (approx(36.3), approx(11.3))


def test_pocket_tag_value_round_trips():
    value = cullenect.pocketTagValue(36.3, 11.3)
    assert cullenect.readPocketTagValue(value) == (approx(36.3), approx(11.3))


def test_pocket_tag_value_unreadable_is_none():
    assert cullenect.readPocketTagValue("not json") is None
    assert cullenect.readPocketTagValue('{"widthMm": "x"}') is None


# --- round 13 (p160): a rebuilt bin keeps the inserts jointed into its pockets, by the pocket's name

def test_pocket_remap_same_name():
    old = ["Compartment 1 pocket joint origin", "Compartment 2 pocket joint origin"]
    assert cullenect.pocketRemap(old, list(reversed(old))) == {name: name for name in old}


def test_pocket_remap_missing_pocket_is_none():
    old = ["Compartment 1 pocket joint origin", "Compartment 2 pocket joint origin"]
    assert cullenect.pocketRemap(old, ["Pocket joint origin"]) == {old[0]: None, old[1]: None}
    assert cullenect.pocketRemap(["Pocket joint origin"], ["Pocket joint origin"]) == {"Pocket joint origin": "Pocket joint origin"}


# --- review of round 13: a rebuild moves over the joints of pockets only, and says when the insert no longer fits

def test_pocket_names_leave_other_joint_origins_out():
    tag = cullenect.pocketTagValue(36.3, 11.3)
    origins = [("Foot joint origin 1-1", None), ("Pocket joint origin", tag), ("Mine", "not a pocket")]
    assert cullenect.pocketNames(origins) == ["Pocket joint origin"]


def test_pocket_fit_note_only_when_the_insert_no_longer_fits():
    assert cullenect.pocketFitNote("Insert in pocket", "Pocket joint origin", (36.0, 11.0), (36.3, 11.3)) is None
    note = cullenect.pocketFitNote("Insert in pocket", "Pocket joint origin", (78.0, 11.0), (36.3, 11.3))
    assert "Insert in pocket" in note and "Pocket joint origin" in note and "doesn't fit" in note


# p35, Joerg 15.11.2026: "Standard fuer Cullenect ist 1,2mm. Dicker geht, duenner nicht."

def test_walls_from_1_2_mm_take_a_socket():
    for wall in (0.12, 0.2, 0.3):
        assert cullenect.wallProblem(wall) is None


def test_thinner_walls_take_none():
    problem = cullenect.wallProblem(0.119)
    assert problem is not None and "1.2 mm" in problem


def test_rounding_noise_counts_as_1_2():
    assert cullenect.wallProblem(0.12 - 1e-9) is None
