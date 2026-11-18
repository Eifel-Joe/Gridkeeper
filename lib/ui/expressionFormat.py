import re

import adsk.core

from ...lib import fusion360utils as futil

# A plain number, as typed into a length input, with or without the input's unit
_PLAIN_NUMBER = r'\s*[-+]?(?:\d+(?:\.\d*)?|\.\d+)\s*'


def normalizedExpression(expression: str, unitType: str, formatted: str) -> str | None:
    """
    The text a length input should show for what was typed in it: Fusion keeps "2.9" as typed (p291), the field shows
    "2.90 mm" like it does when the dialog opens. Only plain numbers in the input's own length unit; formulas and other
    units stay as typed, angles and inputs without a unit aren't formatted. None when nothing is to be set
    """
    if not unitType or unitType == 'deg':
        return None
    if re.fullmatch(_PLAIN_NUMBER + f'(?:{re.escape(unitType)})?\\s*', expression or '') is None:
        return None
    # nothing to set when it's shown so already, a set is what might come round as a change again
    return formatted if formatted != expression else None
