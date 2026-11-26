"""
Dropdown items in the add-in's language with an English value (dev-notes/specs/2026-11-26-r60-german.md). A list item
has only its shown name, so the value of each translated name is kept here per dropdown; the command state, saved
defaults, configs and tags keep the value. Values are marked with i18n.trValue where they are defined.
"""

import adsk.core

from ..i18n import trKnown

# (dropdown id, shown name) → value, for the items added translated
_values: dict[tuple[str, str], str] = {}


def addItem(dropdown: adsk.core.DropDownCommandInput, value: str, isSelected: bool, icon: str = '',
            translate: bool = True, context: str | None = None):
    """
    An item showing the value translated, or as it is for names from data (printers, fonts, symbols). A context tells
    apart a value meaning something else in another dropdown, such as the hardware's Full thread and the lip type Full
    """
    name = trKnown(value, context) if translate else value
    # Several commands use the same dropdown id (sizing_mode_dropdown in the baseplate and the insert, text_style in
    # both labels, magnet_size ...), with other values behind the same German name (Grid units, Base units: both
    # Rastereinheiten). Keyed by id alone, the second dialog failed and a value could come from the other command.
    # Fusion has one command dialog open at a time and each fills its dropdowns from empty, so a dropdown's first item
    # starts its values afresh: they are always the open dialog's. Keying by the command instead needs
    # parentCommand.parentCommandDefinition, which isn't there before the dialog is up nor in the test fakes.
    # Test: tests/test_dropdown_values.py, test_two_commands_may_use_the_same_dropdown_id
    if dropdown.listItems.count == 0:
        for key in [key for key in _values if key[0] == dropdown.id]:
            del _values[key]
    known = _values.get((dropdown.id, name))
    if known is not None and known != value:
        raise ValueError(f'{dropdown.id}: {value} and {known} are both shown as {name}')
    _values[(dropdown.id, name)] = value
    return dropdown.listItems.add(name, isSelected, icon)


def valueOf(dropdown: adsk.core.DropDownCommandInput, name: str) -> str:
    """The value of a shown name, the name itself for items added untranslated or without this module"""
    return _values.get((dropdown.id, name), name)


def value(dropdown: adsk.core.DropDownCommandInput) -> str | None:
    """The selected item's value, none without a selection"""
    item = dropdown.selectedItem
    return valueOf(dropdown, item.name) if item is not None else None
