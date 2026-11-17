"""
The config of the box label (round 29, p262) for its settings, rebuild and clone (Hauptsitzung for 1.1.0, Jörg after his
test: "Die Box-Labels haben die Punkte [Gridkeeper settings / rebuild / clone im Rechtsklick] nicht. Warum? Die
Cullenect-Label haben es."), as labelConfig is the Cullenect insert's. Plain, no Fusion.

Settings are by field name as configJson.stateToJson has them, the symbols by their names in the dialog
(predBoxLabelLayout.symbolChoices).
"""

import re

from .predBoxLabelLayout import MAX_SYMBOLS, NO_SYMBOL

# the label's text parameters by their field, with the label the tag gives them; a rebuild takes their values back into
# the settings, see rebuildUtils.configWithParameters
PARAMETER_LABELS = {'bigText': 'Large text', 'line1': 'Line 1', 'line2': 'Line 2'}
PARAMETER_FIELDS = {label: field for (field, label) in PARAMETER_LABELS.items()}

# the joint the box label command makes into a box's holder, "<label> in holder"; Fusion numbers a name still taken, a
# rebuild with the same name gives "<label> in holder (1)" while the old joint is there yet
HOLDER_JOINT_SUFFIX = ' in holder'
_HOLDER_JOINT = re.compile(r' in holder( \(\d+\))?$')


def isHolderJointName(name: str) -> bool:
    """Whether the joint is one the box label command made into a holder"""
    return _HOLDER_JOINT.search(name) is not None


def knownSymbols(symbols: list[str], names: list[str]) -> tuple[list[str], list[str]]:
    """
    The symbols of a config for the dialog's five places: names this install has no svg for become empty places, said
    by the second list, a short list is filled with empty places, a long one cut
    """
    unknown = [symbol for symbol in symbols if symbol not in names]
    known = [symbol if symbol in names else NO_SYMBOL for symbol in symbols][:MAX_SYMBOLS]
    return (known + [NO_SYMBOL] * (MAX_SYMBOLS - len(known)), unknown)
