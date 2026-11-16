"""
An entity put into a selection input when a dialog opens, the pocket of an insert rebuilt in place (round 20, p220).
Fusion may refuse it ("3 : invalid argument selection"), the dialog stopped half built then and OK built nothing. A
refused entity leaves the input empty, the dialog goes on and tells why. No Fusion import, so it can be unit tested.
"""


def prefillSelection(selectionInput, entity) -> str | None:
    """Puts the entity into the selection input, a note when Fusion refused it, none when it took it or there's none"""
    if entity is None:
        return None
    try:
        selectionInput.addSelection(entity)
        return None
    except Exception as err:
        return f'{err}'
