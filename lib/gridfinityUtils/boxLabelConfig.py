"""
The config of the box label (round 29, p262) for its settings, rebuild and clone (1.1.0: box labels lacked the
settings / rebuild / clone right-click entries that the Cullenect labels have), as labelConfig is the Cullenect insert's. Plain, no Fusion.

Settings are by field name as configJson.stateToJson has them, the symbols by their names in the dialog
(predBoxLabelLayout.symbolChoices).
"""

import re

from .predBoxLabelLayout import MAX_SYMBOLS, NO_SYMBOL, labelWidth, widthChoiceFor, widthChoiceShown

try:
    from ..i18n import tr, number
except ImportError:
    # loaded on its own by a test or a tool, outside the add-in package: English
    def tr(text, context=None, /, **values):
        return text.format(**values) if values else text

    def number(value):
        return value if isinstance(value, str) else f'{value:g}'

# the label's text parameters: the end of their name in the document (gfBoxLabel1_text1, kept as built in round 29),
# the config field each holds and the label the tag gives it; a rebuild takes their values back into the settings, see
# rebuildUtils.configWithParameters. One table: the names and the fields differ, a lookup of a name among the fields
# failed every build (click test 17.11.2026, KeyError 'text1')
TEXT_PARAMETERS = [('bigText', 'bigText', 'Large text'), ('text1', 'line1', 'Line 1'), ('text2', 'line2', 'Line 2')]
TEXT_PARAMETER_NAMES = [name for (name, _, _) in TEXT_PARAMETERS]
PARAMETER_FIELDS = {label: field for (_, field, label) in TEXT_PARAMETERS}


def parameterLabels(parameterNames: list[str | None]) -> list[list[str]]:
    """The label and name pairs of the tag, the parameter names in the order of TEXT_PARAMETERS, None for a text left
    empty, which has none"""
    return [[label, name] for ((_, _, label), name) in zip(TEXT_PARAMETERS, parameterNames) if name is not None]


# the joint the box label command makes into a box's holder, "<label> in holder"; Fusion numbers a name still taken, a
# rebuild with the same name gives "<label> in holder (1)" while the old joint is there yet
HOLDER_JOINT_SUFFIX = ' in holder'
_HOLDER_JOINT = re.compile(r' in holder( \(\d+\))?$')


def isHolderJointName(name: str) -> bool:
    """Whether the joint is one the box label command made into a holder"""
    return _HOLDER_JOINT.search(name) is not None


# how a label in the holder fits a rebuilt box, see labelFit
FIT_SAME = 'same'
FIT_NARROWER = 'narrower'
FIT_TOO_WIDE = 'tooWide'


def labelFit(labelCells: int | None, boxCells: int | None) -> str:
    """
    How a label built for labelCells fits the holder of a box boxCells wide. Decided 17.11.2026: when a box rebuild makes
    the label too wide, the label is laid beside it. Too wide goes beside,
    narrower stays in; a width that isn't known leaves it as it is
    """
    if labelCells is None or boxCells is None or widthChoiceFor(labelCells) == widthChoiceFor(boxCells):
        return FIT_SAME
    return FIT_TOO_WIDE if labelWidth(labelCells) > labelWidth(boxCells) else FIT_NARROWER


def widthNote(jointName: str, labelCells: int | None, boxCells: int | None, place: str = 'beside') -> str | None:
    """
    What the note after a box rebuild says of its label of another label width, none when it fits. place: where a too
    wide one was laid, 'in front of' the box or 'beside' it at a free spot
    """
    fit = labelFit(labelCells, boxCells)
    if fit == FIT_SAME:
        return None
    widths = tr('{label} against {box} the box takes now', label=widthChoiceShown(labelCells), box=widthChoiceShown(boxCells))
    if fit == FIT_TOO_WIDE:
        if place == 'in front of':
            return tr('{joint}: the label is too wide for the box now ({widths}), it was laid in front of the box; rebuild the label with that width', joint=jointName, widths=widths)
        return tr('{joint}: the label is too wide for the box now ({widths}), it was laid beside the box; rebuild the label with that width', joint=jointName, widths=widths)
    return tr('{joint}: the label is narrower than the holder now ({widths}), it stays in the holder; rebuild the label with that width', joint=jointName, widths=widths)


def knownSymbols(symbols: list[str], names: list[str]) -> tuple[list[str], list[str]]:
    """
    The symbols of a config for the dialog's five places: names this install has no svg for become empty places, said
    by the second list, a short list is filled with empty places, a long one cut
    """
    unknown = [symbol for symbol in symbols if symbol not in names]
    known = [symbol if symbol in names else NO_SYMBOL for symbol in symbols][:MAX_SYMBOLS]
    return (known + [NO_SYMBOL] * (MAX_SYMBOLS - len(known)), unknown)
