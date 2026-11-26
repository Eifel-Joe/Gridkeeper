import adsk.core, adsk.fusion
import os
import traceback

from ...lib import tagUtils
from ...lib import settingsUtils
from ...lib import configJson
from ...lib import fusion360utils as futil
from ...lib.ui import browserPages
from ...lib.ui import configButtons
from ...lib.ui.buttonRow import Button
from ...lib.i18n import tr
from ... import config
from ..commandCreateBin import entry as binEntry
from ..commandCreateBaseplate import entry as baseplateEntry
from ..commandCreateLabel import entry as labelEntry
from ..commandCreateBox import entry as boxEntry
from ..commandCreateBoxLabel import entry as boxLabelEntry

app = adsk.core.Application.get()
ui = app.userInterface


def showFailure(englishName: str, shownName: str, err: Exception):
    """The log in English, the message box in the add-in's language (review round 60, as the export's)"""
    futil.handle_error(f'{englishName} failed, {err}')
    ui.messageBox(tr('{command} failed, {error}', command=shownName, error=err) + '\n' + traceback.format_exc())

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdShowSettings'
CMD_NAME = tr('Gridkeeper settings')
CMD_Description = tr('Show the settings this bin, baseplate or label was generated with')
# a bin with a cog, shown beside the context menu item
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')
# the context menu item opening the generator's dialog to rebuild the body, as the Rebuild button of the window does
REBUILD_CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdRebuild'
REBUILD_CMD_NAME = tr('Gridkeeper rebuild')
# a bin with a wrench
REBUILD_ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'rebuild', '')
REBUILD_CMD_DESCRIPTION = tr('Open the generator dialog with the settings of this bin, baseplate or label to build it again in its place, keeping the features after it')
# the context menu item opening the generator's dialog with these settings for a new body, as the Clone button of the window does
CLONE_CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdClone'
CLONE_CMD_NAME = tr('Gridkeeper clone')
# a bin with two sheets, a copy
CLONE_ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'clone', '')
CLONE_CMD_DESCRIPTION = tr('Open the generator dialog with the settings of this bin, baseplate, label or box to build a new one')

SETTINGS_TEXT_INPUT = 'settings_text'
SETTINGS_BROWSER = 'settings'
SETTINGS_HTML_URL = browserPages.pageUrl(__file__, 'settings.html')
# English: the name of a saved file starts with one when the generator can't tell, the window shows tagTitle
TAG_TITLES = {
    tagUtils.TAG_BIN: 'Gridfinity bin',
    tagUtils.TAG_BASEPLATE: 'Gridfinity baseplate',
    tagUtils.TAG_LABEL: 'Gridfinity label',
    tagUtils.TAG_BOX: 'Gridfinity box',
    tagUtils.TAG_BOX_LABEL: 'Box label',
}
def tagTitle(tagName: str) -> str:
    """The window's title for a kind of generated part, in the add-in's language"""
    titles = {
        tagUtils.TAG_BIN: tr('Gridfinity bin'),
        tagUtils.TAG_BASEPLATE: tr('Gridfinity baseplate'),
        tagUtils.TAG_LABEL: tr('Gridfinity label'),
        tagUtils.TAG_BOX: tr('Gridfinity box'),
        tagUtils.TAG_BOX_LABEL: tr('Box label'),
    }
    return titles.get(tagName, CMD_NAME)

# the dialog each generator opens with a cloned config, see startWithConfig
CLONE_COMMANDS = {
    tagUtils.TAG_BIN: binEntry,
    tagUtils.TAG_BASEPLATE: baseplateEntry,
    # inserts since round 18 (p150)
    tagUtils.TAG_LABEL: labelEntry,
    # storage boxes after Pred (round 27)
    tagUtils.TAG_BOX: boxEntry,
    # the label of a box (1.1.0: box labels lacked these entries that the Cullenect labels have)
    tagUtils.TAG_BOX_LABEL: boxLabelEntry,
}
# generators that rebuild a body in place, see binEntry.startRebuild, baseplateEntry.startRebuild, labelEntry.startRebuild,
# boxEntry.startRebuild and boxLabelEntry.startRebuild
REBUILD_COMMANDS = {
    tagUtils.TAG_BIN: binEntry,
    tagUtils.TAG_BASEPLATE: baseplateEntry,
    tagUtils.TAG_LABEL: labelEntry,
    tagUtils.TAG_BOX: boxEntry,
    tagUtils.TAG_BOX_LABEL: boxLabelEntry,
}
REBUILD_ACTION = 'rebuild'
# the page's height, what the dialog has room for at its initial size. Fusion makes a page as tall as its content up
# to its maximum height and scrolls the dialog then, the page scrolls the settings itself, see html/settings.html
PAGE_HEIGHT = 340

local_handlers = []
markingMenuHandler = None
# starting a command can clear the selection, so the body and its tag are kept from when the menu opened
menuTag = None

def selectedTag() -> tuple[adsk.fusion.BRepBody, str, dict] | None:
    """
    The single selected generated body, native, with its tag, also when one of its faces is selected, or the component
    of a hybrid design it was generated in
    """
    if ui.activeSelections.count != 1:
        return None
    entity = ui.activeSelections.item(0).entity
    occurrence = adsk.fusion.Occurrence.cast(entity)
    component = occurrence.component if occurrence is not None else adsk.fusion.Component.cast(entity)
    if component is not None:
        return componentTag(component)
    body = adsk.fusion.BRepBody.cast(entity)
    if body is None:
        face = adsk.fusion.BRepFace.cast(entity)
        body = face.body if face is not None else None
    if body is None:
        return None
    # bins in their own component are selected through an occurrence, the tag sits on the body itself. A letter a
    # longer text added has none, the bin or insert it's in answers for it (p71)
    design = adsk.fusion.Design.cast(app.activeProduct)
    def occurrenceOf(component: adsk.fusion.Component) -> adsk.fusion.Occurrence | None:
        occurrences = design.rootComponent.allOccurrencesByComponent(component) if design is not None else None
        return occurrences.item(0) if occurrences is not None and occurrences.count > 0 else None
    return tagUtils.partTag(body, occurrenceOf)

def componentTag(component: adsk.fusion.Component) -> tuple[adsk.fusion.BRepBody, str, dict] | None:
    """
    The generated body of a component with its tag, none unless it holds exactly one, its bodies are native. A box set
    holds none, its Box component's body stands for it, see tagUtils.menuTagOf
    """
    def tagsOf(owner: adsk.fusion.Component) -> list:
        return [(body, *tag) for body in owner.bRepBodies if (tag := tagUtils.readPartTag(body)) is not None]
    def roleOf(child: adsk.fusion.Component) -> str | None:
        # the tag only, not the name: a user's own component named Box doesn't answer for its parent
        attribute = child.attributes.itemByName(tagUtils.TAG_GROUP, tagUtils.TAG_PART_ROLE)
        return attribute.value if attribute is not None else None
    children = [(roleOf(occurrence.component), tagsOf(occurrence.component)) for occurrence in component.occurrences]
    return tagUtils.menuTagOf(tagsOf(component), children)

def canRebuild(tag: tuple[adsk.fusion.BRepBody, str, dict] | None) -> bool:
    """Bodies generated before the generator kept the config can't be rebuilt"""
    return tag is not None and tag[1] in REBUILD_COMMANDS and tagUtils.buildConfig(tag[1], tag[2]) is not None

def canClone(tag: tuple[adsk.fusion.BRepBody, str, dict] | None) -> bool:
    """Bodies generated before the generator kept the config can't be cloned"""
    return tag is not None and tag[1] in CLONE_COMMANDS and tagUtils.buildConfig(tag[1], tag[2]) is not None

def startRebuild(tag: tuple[adsk.fusion.BRepBody, str, dict]):
    (body, tagName, value) = tag
    REBUILD_COMMANDS[tagName].startRebuild(body, value)

def parameterExpression(name: str) -> str | None:
    design = adsk.fusion.Design.cast(app.activeProduct)
    parameter = design.userParameters.itemByName(name) if design is not None else None
    return parameter.expression if parameter is not None else None

def start():
    global markingMenuHandler
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    futil.add_handler(cmd_def.commandCreated, command_created)
    rebuild_def = ui.commandDefinitions.itemById(REBUILD_CMD_ID)
    if not rebuild_def:
        rebuild_def = ui.commandDefinitions.addButtonDefinition(REBUILD_CMD_ID, REBUILD_CMD_NAME, REBUILD_CMD_DESCRIPTION, REBUILD_ICON_FOLDER)
    futil.add_handler(rebuild_def.commandCreated, rebuild_command_created)
    clone_def = ui.commandDefinitions.itemById(CLONE_CMD_ID)
    if not clone_def:
        clone_def = ui.commandDefinitions.addButtonDefinition(CLONE_CMD_ID, CLONE_CMD_NAME, CLONE_CMD_DESCRIPTION, CLONE_ICON_FOLDER)
    futil.add_handler(clone_def.commandCreated, clone_command_created)
    markingMenuHandler = futil.add_handler(ui.markingMenuDisplaying, marking_menu_displaying, local_handlers=local_handlers)

def stop():
    global markingMenuHandler
    if markingMenuHandler is not None:
        ui.markingMenuDisplaying.remove(markingMenuHandler)
        markingMenuHandler = None
    for cmdId in [CMD_ID, REBUILD_CMD_ID, CLONE_CMD_ID]:
        command_definition = ui.commandDefinitions.itemById(cmdId)
        if command_definition:
            command_definition.deleteMe()

def marking_menu_displaying(args: adsk.core.MarkingMenuEventArgs):
    global menuTag
    try:
        menuTag = selectedTag()
        if menuTag is None:
            return
        controls = args.linearMarkingMenu.controls
        controls.addSeparator()
        controls.addCommand(ui.commandDefinitions.itemById(CMD_ID))
        if canRebuild(menuTag):
            controls.addCommand(ui.commandDefinitions.itemById(REBUILD_CMD_ID))
        if canClone(menuTag):
            controls.addCommand(ui.commandDefinitions.itemById(CLONE_CMD_ID))
    except Exception as err:
        futil.log(f'Gridkeeper settings context menu failed, {err}')

def command_created(args: adsk.core.CommandCreatedEventArgs):
    tag = selectedTag() or menuTag
    command = args.command
    command.isOKButtonVisible = False
    command.cancelButtonText = tr('Close')
    if tag is None:
        command.commandInputs.addTextBoxCommandInput(SETTINGS_TEXT_INPUT, '', tr('Select a generated bin, baseplate or label.'), 1, True)
        return
    (body, tagName, value) = tag
    command.setDialogInitialSize(450, 500)
    # the settings and their buttons in one page, the buttons stay above the settings as they scroll
    browser = command.commandInputs.addBrowserCommandInput(SETTINGS_BROWSER, '', SETTINGS_HTML_URL, PAGE_HEIGHT, PAGE_HEIGHT)
    browser.isFullWidth = True
    futil.add_handler(command.incomingFromHTML, lambda args: command_incoming_from_html(args, body, tagName, value), local_handlers=local_handlers)
    futil.add_handler(command.destroy, command_destroy, local_handlers=local_handlers)

def rebuild_command_created(args: adsk.core.CommandCreatedEventArgs):
    """Opens the generator's dialog in place of this command, which has nothing to show"""
    tag = selectedTag() or menuTag
    try:
        if not canRebuild(tag):
            ui.messageBox(tr('Select a generated bin, baseplate or label to rebuild.'), REBUILD_CMD_NAME)
            return
        startRebuild(tag)
    except Exception as err:
        showFailure('Gridkeeper rebuild', tr('Gridkeeper rebuild'), err)

def clone_command_created(args: adsk.core.CommandCreatedEventArgs):
    """Opens the generator's dialog in place of this command, which has nothing to show"""
    tag = selectedTag() or menuTag
    try:
        if not canClone(tag):
            ui.messageBox(tr('Select a generated bin, baseplate or label to clone.'), CLONE_CMD_NAME)
            return
        (_, tagName, value) = tag
        CLONE_COMMANDS[tagName].startWithConfig(value['config'])
    except Exception as err:
        showFailure('Gridkeeper clone', tr('Gridkeeper clone'), err)

def command_incoming_from_html(args: adsk.core.HTMLEventArgs, body: adsk.fusion.BRepBody, tagName: str, value: dict):
    browserPages.handleMessage(args, pageHandlers(body, tagName, value))

def pageHandlers(body: adsk.fusion.BRepBody, tagName: str, value: dict) -> dict[str, browserPages.Handler]:
    """
    The page gets the settings and the config buttons, bodies generated before the generator kept the config have
    none, see html/settings.html
    """
    page = {
        'title': tagTitle(tagName),
        'settings': settingsUtils.settingsHtml(value, parameterExpression),
        'buttons': [],
    }
    # a box label built before it kept its whole config shows its settings only, see tagUtils.buildConfig
    if tagUtils.buildConfig(tagName, value) is None:
        return {browserPages.READY: lambda _: page}
    # tag names are the generator names of configJson
    generatorTitle = configJson.generatorTitle(tagName)
    moreButtons = []
    if tagName in REBUILD_COMMANDS:
        moreButtons.append((
            Button(REBUILD_ACTION, tr('Rebuild'), tr('Open the {generatorTitle} dialog with these settings to build this {generatorTitle} again in its place, keeping the features after it', generatorTitle=generatorTitle)),
            lambda: startRebuild((body, tagName, value)),
        ))
    configText = configJson.configText(tagName, value['config'], str(value.get('generatorVersion') or ''))
    handlers = configButtons.configButtonsHandlers(
        generatorTitle,
        lambda: configText,
        lambda: configFileName(tagName, value['config']),
        onClone=lambda: CLONE_COMMANDS[tagName].startWithConfig(value['config']),
        moreButtons=moreButtons,
    )
    buttons = handlers[browserPages.READY]
    return {**handlers, browserPages.READY: lambda data: {**page, 'buttons': buttons(data)}}

def configFileName(tagName: str, settings: dict) -> str:
    """The name the generator's dialog gives a saved file of these settings, the tag's title when it can't be read"""
    try:
        return CLONE_COMMANDS[tagName].configFileName(settings)
    except Exception as err:
        futil.log(f'Gridkeeper settings config file name not made, {err}')
        return TAG_TITLES[tagName]

def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    # the context menu handler stays for the next menu
    local_handlers = [handler for handler in local_handlers if handler is markingMenuHandler]
