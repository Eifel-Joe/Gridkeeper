"""
Dropdowns show a value in the add-in's language and keep the English value: the state, saved defaults, configs and
tags stay language-neutral (lib/ui/dropdowns.py, dev-notes/specs/2026-11-26-r60-german.md).
"""

import sys

import adsk.core
import pytest

i18n = sys.modules["FusionGridfinityGenerator.lib.i18n"]
dropdowns = sys.modules["FusionGridfinityGenerator.lib.ui.dropdowns"]
from commandUiState import CommandUiState

GERMAN = {"Hollow": "Hohl", "Shelled": "Schale", "Solid": "Voll"}


@pytest.fixture
def german():
    i18n.setLanguage("de", dict(GERMAN))
    yield
    i18n.setLanguage("en")


def _dropdown(selected="Shelled"):
    dropdown = adsk.core.DropDownCommandInput("bin_type", [])
    for value in ("Hollow", "Shelled", "Solid"):
        dropdowns.addItem(dropdown, value, value == selected)
    return dropdown


def test_trValue_marks_a_value_and_returns_it():
    assert i18n.trValue("Hollow") == "Hollow"


def test_items_show_the_translation(german):
    dropdown = _dropdown()
    assert [dropdown.listItems.item(i).name for i in range(dropdown.listItems.count)] == ["Hohl", "Schale", "Voll"]
    assert dropdown.selectedItem.name == "Schale"


def test_the_value_is_the_english_one(german):
    assert dropdowns.value(_dropdown("Solid")) == "Solid"


def test_english_shows_and_keeps_the_value():
    dropdown = _dropdown("Hollow")
    assert dropdown.selectedItem.name == "Hollow"
    assert dropdowns.value(dropdown) == "Hollow"


def test_names_from_data_come_back_unchanged(german):
    dropdown = adsk.core.DropDownCommandInput("bed", [])
    dropdowns.addItem(dropdown, "Bambu Lab A1", True, translate=False)
    assert dropdown.selectedItem.name == "Bambu Lab A1"
    assert dropdowns.value(dropdown) == "Bambu Lab A1"


def test_an_item_shown_by_its_value_is_found(german):
    """Items a dropdown got without the helper keep their name as the value"""
    dropdown = adsk.core.DropDownCommandInput("other", ["Plain"], "Plain")
    assert dropdowns.value(dropdown) == "Plain"


def test_no_selection_gives_none():
    dropdown = adsk.core.DropDownCommandInput("empty", [])
    dropdown.listItems._items = []
    assert dropdowns.value(_NoSelection()) is None


class _NoSelection:
    id = "none"
    selectedItem = None


def test_two_values_with_the_same_label_in_one_dropdown_are_an_error():
    i18n.setLanguage("de", {"Light": "Leicht", "Lite": "Leicht"})
    try:
        dropdown = adsk.core.DropDownCommandInput("clash", [])
        dropdowns.addItem(dropdown, "Light", True)
        with pytest.raises(ValueError):
            dropdowns.addItem(dropdown, "Lite", False)
    finally:
        i18n.setLanguage("en")


def test_the_same_label_in_two_dropdowns_is_fine():
    i18n.setLanguage("de", {"Light": "Leicht", "Lite": "Leicht"})
    try:
        first = adsk.core.DropDownCommandInput("first", [])
        second = adsk.core.DropDownCommandInput("second", [])
        dropdowns.addItem(first, "Light", True)
        dropdowns.addItem(second, "Lite", True)
        assert (dropdowns.value(first), dropdowns.value(second)) == ("Light", "Lite")
    finally:
        i18n.setLanguage("en")


def test_two_commands_may_use_the_same_dropdown_id():
    """The baseplate's Grid units and the insert's Base units are both German Rastereinheiten in a dropdown with the
    id sizing_mode_dropdown: opening one dialog after the other failed, and a value could come from the other
    command. Fusion has one command dialog open at a time and each fills its dropdowns from empty"""
    i18n.setLanguage("de", {"Grid units": "Rastereinheiten", "Base units": "Rastereinheiten", "Millimeters": "Millimeter"})
    try:
        values = []
        for value in ("Grid units", "Base units", "Grid units"):
            dropdown = adsk.core.DropDownCommandInput("sizing_mode_dropdown", [])
            dropdown.listItems._items = []
            dropdowns.addItem(dropdown, value, True)
            dropdowns.addItem(dropdown, "Millimeters", False)
            values.append(dropdowns.value(dropdown))
        assert values == ["Grid units", "Base units", "Grid units"]
    finally:
        i18n.setLanguage("en")


def test_a_dropdown_filled_again_keeps_its_values(german):
    """The insert dialog fills a hardware dropdown again when the hardware changes"""
    dropdown = _dropdown("Solid")
    dropdown.listItems.clear()
    for value in ("Hollow", "Shelled"):
        dropdowns.addItem(dropdown, value, value == "Shelled")
    assert dropdowns.value(dropdown) == "Shelled"
    assert dropdowns.valueOf(dropdown, "Voll") == "Voll"


def test_the_state_keeps_the_value(german):
    dropdown = _dropdown("Solid")
    state = CommandUiState("bin")
    state.onInputUpdate(dropdown)
    assert state.getState("bin_type") == "Solid"


def test_the_state_selects_the_item_of_its_value(german):
    dropdown = _dropdown("Hollow")
    state = CommandUiState("bin")
    state.onInputUpdate(dropdown)
    state.updateValue("bin_type", "Shelled")
    state.registerCommandInput(dropdown)
    state.updateInputFromState(dropdown)
    assert dropdown.selectedItem.name == "Schale"
    assert dropdowns.value(dropdown) == "Shelled"
