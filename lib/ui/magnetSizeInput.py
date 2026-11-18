import adsk.core

from ..gridfinityUtils import magnetSizes

# The magnet size choice before the free "Magnet cutout depth" field (round 27, p263; decided 16.11.2026: adjustable
# magnet holes, 2.4 mm for 2 mm magnets and 3.4 mm for 3 mm magnets, also for baseplates and bins). The choice only
# writes the depth field; settings keep the depth, the choice is read back from it, see magnetSizes.

LABEL = 'Magnet size'
TOOLTIP = '6×2 mm magnets need a 2.4 mm deep cutout, 6×3 mm ones 3.4 mm. Custom keeps the depth below to type'


def addMagnetSizeInput(inputs: adsk.core.CommandInputs, inputId: str, uiState, choices: list[str]) -> adsk.core.DropDownCommandInput:
    dropdown = inputs.addDropDownCommandInput(inputId, LABEL, adsk.core.DropDownStyles.TextListDropDownStyle)
    selected = uiState.getState(inputId)
    for name in choices:
        dropdown.listItems.add(name, name == selected)
    dropdown.tooltip = TOOLTIP
    uiState.registerCommandInput(dropdown)
    return dropdown


def onMagnetSizeChanged(uiState, sizeId: str, depthId: str) -> bool:
    """A size sets the depth field, Custom leaves it. True when the depth changed"""
    depth = magnetSizes.depthForChoice(uiState.getState(sizeId))
    if depth is None:
        return False
    uiState.setValue(depthId, depth)
    return True


def syncMagnetSize(uiState, sizeId: str, depthId: str, choices: list[str]):
    """The choice read back from the depth, after settings were loaded or applied"""
    uiState.setValue(sizeId, magnetSizes.choiceForDepth(uiState.getState(depthId), choices))


def isDepthTyped(uiState, sizeId: str) -> bool:
    """The depth field is typed in only with Custom"""
    return uiState.getState(sizeId) == magnetSizes.CUSTOM
