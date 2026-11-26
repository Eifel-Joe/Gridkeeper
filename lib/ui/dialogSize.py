"""
The size a command's dialog opens with. German input names are longer: at the English widths Fusion cut them off
(click test round 60), so in German a dialog starts GERMAN_EXTRA_WIDTH wider and can't be made narrower than that; the
minimum also holds when Fusion opens a dialog at a size it remembers. English dialogs stay as they were.
"""

from .. import i18n

GERMAN_EXTRA_WIDTH = 150
# the dialogs can still be made low, only not narrow
GERMAN_MINIMUM_HEIGHT = 200


def setDialogSize(command, width: int, height: int, minimum: tuple[int, int] | None = None):
    """width, height and the minimum as for English, the command's setDialogInitialSize and setDialogMinimumSize"""
    if i18n.language() != 'de':
        command.setDialogInitialSize(width, height)
        if minimum is not None:
            command.setDialogMinimumSize(*minimum)
        return
    germanWidth = width + GERMAN_EXTRA_WIDTH
    command.setDialogInitialSize(germanWidth, height)
    command.setDialogMinimumSize(max(germanWidth, minimum[0] if minimum else 0), minimum[1] if minimum else GERMAN_MINIMUM_HEIGHT)
