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
            translate: bool = True):
    """An item showing the value translated, or as it is for names from data (printers, fonts, symbols)"""
    name = trKnown(value) if translate else value
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
