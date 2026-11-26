import adsk.core
import os
from typing import Callable

from ...lib import clipboard
from ...lib import configJson
from ...lib import fusion360utils as futil
from ...lib.i18n import tr
from . import browserPages
from .buttonRow import Button, buttonRowHandlers

# Buttons to save a bin or baseplate config to a file, load or copy it, see configJson for the format
CONFIG_SAVE = 'saveConfig'
CONFIG_LOAD = 'loadConfig'
CONFIG_COPY = 'copyConfig'
CONFIG_CLONE = 'cloneConfig'

app = adsk.core.Application.get()
ui = app.userInterface

# the folder last saved to or opened from, so the next file dialog starts there
_lastFolder = ''

def fileFilter() -> str:
    return tr('Gridkeeper config (*.json);;All files (*.*)')

def configButtons(generatorTitle: str, canLoad: bool, canClone: bool) -> list[Button]:
    # callers pass the English title, configJson.GENERATOR_TITLES, the buttons show it in the add-in's language
    generatorTitle = configJson.translatedTitle(generatorTitle)
    buttons = [Button(CONFIG_SAVE, tr('Save to file'), tr('Save these {generatorTitle} settings to a JSON file', generatorTitle=generatorTitle))]
    if canLoad:
        buttons.append(Button(CONFIG_LOAD, tr('Load from file'), tr('Set the inputs from {generatorTitle} settings saved to a file', generatorTitle=generatorTitle)))
    buttons.append(Button(CONFIG_COPY, tr('Copy'), tr('Copy these {generatorTitle} settings to the clipboard as JSON', generatorTitle=generatorTitle)))
    if canClone:
        buttons.append(Button(CONFIG_CLONE, tr('Clone into new {generatorTitle}', generatorTitle=generatorTitle), tr('Open the {generatorTitle} dialog with these settings', generatorTitle=generatorTitle)))
    return buttons

def configButtonsHandlers(
    generatorTitle: str,
    configText: Callable[[], str],
    fileName: Callable[[], str],
    onLoad: Callable[[str, str], None] = None,
    onClone: Callable[[], None] = None,
    moreButtons: list[tuple[Button, Callable[[], None]]] = [],
) -> dict[str, browserPages.Handler]:
    """
    Messages of a button row, see buttonRow.addButtonRow. configText is the config to save or copy, fileName the
    name a saved file starts with, onLoad gets the text and name of a file opened, onClone opens the dialog with the
    config. More buttons come after with what their click does.
    Load and clone have their buttons only when they're given
    """
    def onClick(action: str) -> str | None:
        if action == CONFIG_SAVE:
            saveConfigFile(configText(), fileName())
        elif action == CONFIG_LOAD:
            opened = openConfigFile()
            if opened is not None:
                onLoad(*opened)
        elif action == CONFIG_COPY:
            return copyConfig(configText())
        elif action == CONFIG_CLONE:
            onClone()
        else:
            for (button, onMoreClick) in moreButtons:
                if action == button.action:
                    onMoreClick()
        return None
    buttons = configButtons(generatorTitle, onLoad is not None, onClone is not None) + [button for (button, _) in moreButtons]
    return buttonRowHandlers(buttons, onClick)

def saveConfigFile(text: str, fileName: str) -> None:
    global _lastFolder
    dialog = ui.createFileDialog()
    dialog.title = tr('Save Gridkeeper config')
    dialog.filter = fileFilter()
    dialog.initialFilename = f'{fileName}.json'
    if _lastFolder:
        dialog.initialDirectory = _lastFolder
    if dialog.showSave() != adsk.core.DialogResults.DialogOK:
        return
    _lastFolder = os.path.dirname(dialog.filename)
    try:
        with open(dialog.filename, 'w', encoding='utf-8') as file:
            file.write(text)
        futil.log(f'Saved config to {dialog.filename}')
    except OSError as err:
        ui.messageBox(tr('Couldn\'t save the config to {fileName}:\n{err}', fileName=dialog.filename, err=err), tr('Gridkeeper config'))

def openConfigFile() -> tuple[str, str] | None:
    """Text and name of the file picked, none when the dialog was cancelled or the file can't be read"""
    global _lastFolder
    dialog = ui.createFileDialog()
    dialog.title = tr('Load Gridkeeper config')
    dialog.filter = fileFilter()
    dialog.isMultiSelectEnabled = False
    if _lastFolder:
        dialog.initialDirectory = _lastFolder
    if dialog.showOpen() != adsk.core.DialogResults.DialogOK:
        return None
    _lastFolder = os.path.dirname(dialog.filename)
    try:
        with open(dialog.filename, encoding='utf-8') as file:
            return (file.read(), os.path.basename(dialog.filename))
    except (OSError, UnicodeDecodeError) as err:
        ui.messageBox(tr('Couldn\'t read {fileName}:\n{err}', fileName=dialog.filename, err=err), tr('Gridkeeper config'))
        return None

def copyConfig(text: str) -> str | None:
    """What the button shows once it's copied"""
    try:
        clipboard.copyText(text)
        return tr('Copied')
    except Exception as err:
        futil.log(f'Couldn\'t copy the config, {err}')
        ui.messageBox(tr('Couldn\'t copy to the clipboard:\n{err}', err=err), tr('Gridkeeper config'))
        return None

def readConfig(
    text: str,
    source: str,
    generator: str,
    stateClass: type,
    current: object,
    choices: dict[str, configJson.Choice],
    isFromTag: bool = False,
) -> object | None:
    """
    The state of a config for a dialog, see configJson.readConfig, none when it can't be read. Shows why, or what
    reading it changed when it did. source names it in the message, like Loaded "bin.json" or Cloned
    """
    try:
        (state, notes) = configJson.readConfig(text, generator, stateClass, current, choices, isFromTag)
    except configJson.ConfigError as err:
        ui.messageBox(tr('Couldn\'t read the config. {err}', err=err), tr('Gridkeeper config'))
        return None
    if not notes.isEmpty():
        details = configJson.notesText(generator, notes)
        futil.log(f'{source} config with changes:\n{details}')
        ui.messageBox(tr('{source} with changes:\n\n{details}', source=source, details=details), tr('Gridkeeper config'), adsk.core.MessageBoxButtonTypes.OKButtonType, adsk.core.MessageBoxIconTypes.WarningIconType)
    return state
