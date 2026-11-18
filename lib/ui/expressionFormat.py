import re

import adsk.core

from ...lib import fusion360utils as futil

app = adsk.core.Application.get()

# The expression is set once inputChanged is over: set within inputChanged or validateInputs, Fusion has it in the API
# but the field keeps showing what was typed; set from a custom event fired there, the field shows it and no further
# inputChanged follows (measured in round 41, Fusion 2706.1.17)
NORMALIZE_EVENT_ID = 'Gridkeeper_normalizeLengthExpression'
handlers = []
pendingInputs: list[adsk.core.ValueCommandInput] = []

# A plain number, as typed into a length input, with or without the input's unit
_PLAIN_NUMBER = r'\s*[-+]?(?:\d+(?:\.\d*)?|\.\d+)\s*'


def start():
    # left over when the add-in wasn't stopped
    app.unregisterCustomEvent(NORMALIZE_EVENT_ID)
    futil.add_handler(app.registerCustomEvent(NORMALIZE_EVENT_ID), normalize_custom_event, local_handlers=handlers)


def stop():
    global handlers
    app.unregisterCustomEvent(NORMALIZE_EVENT_ID)
    handlers = []
    pendingInputs.clear()


def request(valueInput: adsk.core.ValueCommandInput) -> None:
    """Shows the input's value formatted once the inputChanged that called this is over, see normalizedExpression"""
    if not any(pending is valueInput for pending in pendingInputs):
        pendingInputs.append(valueInput)
    app.fireCustomEvent(NORMALIZE_EVENT_ID)


def normalize_custom_event(args: adsk.core.CustomEventArgs):
    inputs = list(pendingInputs)
    pendingInputs.clear()
    for valueInput in inputs:
        try:
            # the dialog may have closed in between
            if not valueInput.isValid or not valueInput.isValidExpression:
                continue
            formatted = app.activeProduct.unitsManager.formatInternalValue(valueInput.value, valueInput.unitType, True)
            expression = normalizedExpression(valueInput.expression, valueInput.unitType, formatted)
            if expression is not None:
                valueInput.expression = expression
        except Exception as err:
            futil.log(f'Length input not formatted, {err}')


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
