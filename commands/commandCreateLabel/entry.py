import adsk.core, adsk.fusion, traceback
import html
import os
import time

from ...lib.gridfinityUtils import designIntent
from ...lib import configUtils
from ...lib import tagUtils
from ...lib import settingsUtils
from ...lib import fusion360utils as futil
from ... import config
from ...lib.gridfinityUtils.const import DIMENSION_DEFAULT_WIDTH_UNIT, BASE_UNIT_MIN
from ...lib.gridfinityUtils import commonUtils
from ...lib.gridfinityUtils import cullenectCatalog
from ...lib.gridfinityUtils import cullenectLabelGenerator
from ...lib.gridfinityUtils import cullenectLabelLayout
from ...lib.gridfinityUtils import labelColors
from ...lib.gridfinityUtils import textStyles
from .inputState import InputState
from .labelBuilder import buildLabel, rebuildLabel, insertPocket, labelName, labelProblem, labelSize, labelSymbol, pocketProblem, pocketSizeMm, ICONS_FOLDER, NO_HARDWARE
from ...lib import configJson
from ...lib import defaultSettings
from ...lib import rebuildUtils
from ...lib.gridfinityUtils import labelConfig
from ...lib.ui.commandUiState import CommandUiState
from ...lib.ui.defaultsButtons import addDefaultsButtonRow, defaultsButtonsHandlers, DEFAULTS_SAVE, DEFAULTS_FACTORY_RESET
from ...lib.ui.buttonRow import addButtonRow
from ...lib.ui import configButtons
from ...lib.ui import selectionPrefill
from ...lib.ui import browserPages
from ...lib.ui.unsupportedDesignTypeException import UnsupportedDesignTypeException
from ...lib.ui import dropdowns
from ...lib.i18n import tr, trValue, number

# Dialog of the label command, Cullenect inserts by CullenJWebb (MIT), https://github.com/CullenJWebb/Cullenect-Labels

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdLabel'
CMD_NAME = 'Gridkeeper label'
# the name the user reads, CMD_NAME stays for the log
CMD_TITLE = tr('Gridkeeper label')
# the first section of a part's settings names the part, as the settings window does (review round 23)
SETTINGS_TITLE = 'Gridfinity label'
# shown on hover over the button, the first paragraph says what it makes, the second how
CMD_Description = tr('Creates a Cullenect label insert for the label sockets of bins.\n\n'
    'Set its width in base units or in mm, up to two lines of text and a screw or hardware symbol. The text and symbol '
    'are bodies of their own, raised, set in or flush, to print them in another colour.')

uiState = CommandUiState(CMD_NAME)
IS_PROMOTED = False

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')
# picture under the description on hover, as the bin and baseplate commands, see tools/screenshots/toolclips
TOOL_CLIP_PATH = os.path.join(ICON_FOLDER, 'toolclip.png')
CONFIG_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'commandConfig')
UI_INPUT_DEFAULTS_CONFIG_PATH = os.path.join(CONFIG_FOLDER_PATH, "ui_input_defaults.json")

local_handlers = []

# Input groups
INFO_GROUP = 'info_group'
SIZE_GROUP = 'size_group'
TEXT_GROUP = 'text_group'
SYMBOL_GROUP = 'symbol_group'
INPUT_CHANGES_GROUP = 'input_changes_group'
PREVIEW_GROUP = 'preview_group'
# Input ids
BASE_WIDTH_INPUT = 'base_width_unit'
SIZING_MODE_DROPDOWN = 'sizing_mode_dropdown'
WIDTH_UNITS_INPUT = 'width_units'
FREE_WIDTH_INPUT = 'free_width'
OFFSET_X_INPUT = 'offset_x'
OFFSET_Y_INPUT = 'offset_y'
SIZE_TEXT = 'size_text'
LINE_1_INPUT = 'text_line_1'
LINE_2_INPUT = 'text_line_2'
TEXT_STYLE_DROPDOWN = 'text_style'
SURFACE_DROPDOWN = 'surface_dropdown'
TEXT_COLOR_DROPDOWN = 'text_color'
CUSTOM_COLOR_INPUT = 'text_color_custom'
SHOW_SCREW_INPUT = 'show_screw'
HEAD_DROPDOWN = 'screw_head'
SHAFT_DROPDOWN = 'screw_shaft'
THREADS_DROPDOWN = 'screw_threads'
DRIVER_DROPDOWN = 'screw_driver'
FLANGE_INPUT = 'screw_flange'
SECURITY_INPUT = 'screw_security'
HARDWARE_DROPDOWN = 'hardware'
SYMBOL_TEXT = 'symbol_text'
INPUT_CHANGES_BUTTONS_BROWSER = 'input_changes_buttons'
SHOW_PREVIEW_INPUT = 'show_preview'
# a Cullenect pocket of a bin to joint the insert into (round 13, p100), its joint origin
POCKET_GROUP = 'pocket_group'
POCKET_INPUT = 'pocket'
# why the pocket of a rebuilt insert isn't picked (round 20, p220)
POCKET_NOTE = 'pocket_note'
PREVIEW_TIME_INPUT = 'preview_time'

SIZING_MODE_UNITS = trValue('Base units')
SIZING_MODE_FREE = trValue('Width in mm')
SURFACE_NAMES = {
    cullenectLabelGenerator.SURFACE_EMBOSSED: trValue('Raised'),
    cullenectLabelGenerator.SURFACE_DEBOSSED: trValue('Set in'),
    cullenectLabelGenerator.SURFACE_FLUSH: trValue('Flush'),
}
# the hardware choice for no hardware, NO_HARDWARE is the config's value
HARDWARE_NONE = trValue('None', 'hardware')
SCREW_DROPDOWNS = {HEAD_DROPDOWN: 'head', SHAFT_DROPDOWN: 'shaft', THREADS_DROPDOWN: 'threads', DRIVER_DROPDOWN: 'driver'}
# the screw blocks and hardware names of cullenectCatalog.CULLENECT_NAMES are translated in their own context: 'Full'
# is a thread there and 'None' no hardware, the lip type Full and a label without icon read otherwise
HARDWARE_CONTEXT = 'hardware'
SCREW_INPUTS = list(SCREW_DROPDOWNS.keys()) + [FLANGE_INPUT, SECURITY_INPUT]

INFO_TEXT = tr("<b>Help:</b> every input is explained "
             "<a href=\"https://eifel-joe.github.io/Gridkeeper/cullenect/inserts/\">in the Gridkeeper documentation</a>. "
             "The insert clicks into the Cullenect pockets of bin label tabs, label style Cullenect. "
             "Cullenect labels by CullenJWebb, "
             "<a href=\"https://github.com/CullenJWebb/Cullenect-Labels\">Cullenect-Labels</a> (MIT).")

INPUTS_VALID = True

# Saving, loading, cloning and rebuilding an insert like a bin (round 18, p150), the workflow of upstream v2.4 by
# Le0Michine, see commandCreateBaseplate.entry
CONFIG_BUTTONS_BROWSER = 'config_buttons'
# config the dialog opens with next, see startWithConfig
pendingConfig: dict | None = None
# the insert the dialog opens to rebuild next and the pocket it is jointed into, see startRebuild; the entity token of
# the one the open dialog rebuilds, every preview is undone, the token finds the body again. None for a new insert
pendingRebuildBody: adsk.fusion.BRepBody | None = None
pendingRebuildPocket: adsk.fusion.JointOrigin | None = None
rebuildBodyToken: str | None = None
# what of the features after a rebuilt insert needs a look, shown when the dialog closes
rebuildNotes: list[str] = []
DEFAULT_STATE = configJson.stateFromJson(configJson.GENERATOR_LABEL, InputState, defaultSettings.SETTINGS[configJson.GENERATOR_LABEL])

def infoText():
    version = tagUtils.getGeneratorVersion()
    return f"{INFO_TEXT}<br><span style=\"color:#808080; font-size:small\">{tr('Version {version}', version=version)}</span>" if version else INFO_TEXT

def getErrorMessage(text = None):
    return f"{text or tr('An unknown error occurred, please validate your inputs and try again')}:<br>{traceback.format_exc()}"

def showErrorInMessageBox(text = None):
    if ui:
        ui.messageBox(getErrorMessage(text), tr('{command} Error', command=CMD_TITLE))

def start():
    futil.log(f'{CMD_NAME} Command Start Event')
    try:
        addinConfig = configUtils.readConfig(CONFIG_FOLDER_PATH)
        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
        if not cmd_def:
            cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_TITLE, CMD_Description, ICON_FOLDER)
            if os.path.isfile(TOOL_CLIP_PATH):
                cmd_def.toolClipFilename = TOOL_CLIP_PATH
            futil.add_handler(cmd_def.commandCreated, command_created)
            workspace = ui.workspaces.itemById(WORKSPACE_ID)
            panel = workspace.toolbarPanels.itemById(PANEL_ID)
            control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
            control.isPromoted = addinConfig['UI'].getboolean('is_promoted', fallback=IS_PROMOTED)
        initUiState()
    except Exception as err:
        futil.log(f'{CMD_NAME} Error occurred at the start, {err}, {getErrorMessage()}')
        showErrorInMessageBox(tr('{command} Critical error occurred at the start, the command will be unavailable', command=CMD_TITLE))

def stop():
    futil.log(f'{CMD_NAME} Command Stop Event')
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control: adsk.core.CommandControl = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    if command_control:
        addinConfig = configUtils.readConfig(CONFIG_FOLDER_PATH)
        addinConfig['UI']['is_promoted'] = 'yes' if command_control.isPromoted else 'no'
        configUtils.writeConfig(addinConfig, CONFIG_FOLDER_PATH)
        command_control.deleteMe()
    if command_definition:
        command_definition.deleteMe()

def screwOptions() -> dict[str, list]:
    return cullenectCatalog.screwOptions(ICONS_FOLDER)

def dropdownNames() -> dict[str, list[str]]:
    """The names each dropdown offers, the screw building blocks and hardware read from the symbol folders"""
    options = screwOptions()
    names = {inputId: [cullenectCatalog.displayName(key) for key in options[field]] for (inputId, field) in SCREW_DROPDOWNS.items()}
    names[HARDWARE_DROPDOWN] = [HARDWARE_NONE] + [name for (name, _) in cullenectCatalog.listHardwareIcons(ICONS_FOLDER)]
    names[SIZING_MODE_DROPDOWN] = [SIZING_MODE_UNITS, SIZING_MODE_FREE]
    names[SURFACE_DROPDOWN] = list(SURFACE_NAMES.values())
    names[TEXT_COLOR_DROPDOWN] = labelColors.CHOICES
    names[TEXT_STYLE_DROPDOWN] = textStyles.STYLES
    return names

def selectableName(inputId: str, names: list[str]) -> str:
    """The remembered choice, or the first one when it isn't offered any more, e.g. a name from saved defaults of an
    older version or a symbol whose svg is gone"""
    selected = uiState.getState(inputId)
    if selected not in names and len(names) > 0:
        selected = textStyles.DEFAULT_INSERT_STYLE if inputId == TEXT_STYLE_DROPDOWN else names[0]
        uiState.updateValue(inputId, selected)
    return selected

def fixDropdownStates():
    for (inputId, names) in dropdownNames().items():
        selectableName(inputId, names)

def addDropdown(inputs: adsk.core.CommandInputs, inputId: str, label: str, names: list[str]) -> adsk.core.DropDownCommandInput:
    """A dropdown of the names, the remembered one selected, else the first"""
    dropdown = inputs.addDropDownCommandInput(inputId, label, adsk.core.DropDownStyles.TextListDropDownStyle)
    selected = selectableName(inputId, names)
    for name in names:
        # the values are English, the items show them translated; names the catalog doesn't know show as they are
        dropdowns.addItem(dropdown, name, name == selected, context=HARDWARE_CONTEXT if inputId in SCREW_DROPDOWNS or inputId == HARDWARE_DROPDOWN else None)
    uiState.registerCommandInput(dropdown)
    return dropdown

def addLength(inputs: adsk.core.CommandInputs, inputId: str, label: str, tooltip: str = '') -> adsk.core.ValueCommandInput:
    valueInput = inputs.addValueInput(inputId, label, app.activeProduct.unitsManager.defaultLengthUnits, adsk.core.ValueInput.createByReal(uiState.getState(inputId)))
    valueInput.tooltip = tooltip
    uiState.registerCommandInput(valueInput)
    return valueInput

def addBool(inputs: adsk.core.CommandInputs, inputId: str, label: str, tooltip: str = '') -> adsk.core.BoolValueCommandInput:
    boolInput = inputs.addBoolValueInput(inputId, label, True, '', uiState.getState(inputId))
    boolInput.tooltip = tooltip
    uiState.registerCommandInput(boolInput)
    return boolInput

def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')
    args.command.setDialogInitialSize(400, 500)
    inputs = args.command.commandInputs
    global rebuildBodyToken
    global pendingRebuildBody
    global pendingRebuildPocket
    rebuildBodyToken = pendingRebuildBody.entityToken if pendingRebuildBody is not None else None
    rebuildName = pendingRebuildBody.name if pendingRebuildBody is not None else None
    rebuildPocket = pendingRebuildPocket
    pendingRebuildBody = None
    pendingRebuildPocket = None
    # before the inputs, they take the dialog state
    applyPendingConfig()

    infoGroup = inputs.addGroupCommandInput(INFO_GROUP, tr('Info'))
    infoGroup.isExpanded = uiState.getState(INFO_GROUP)
    uiState.registerCommandInput(infoGroup)
    info = infoText()
    if rebuildName is not None:
        # as the bin and baseplate dialogs say it (review round 18)
        info = tr('<b>Rebuilding {name}</b> in place, features after it in the timeline are kept.<br>', name=html.escape(rebuildName)) + info
    infoGroup.children.addTextBoxCommandInput("info_text", tr('Info'), info, info.count('<br>') + 3, True)

    sizeGroup = inputs.addGroupCommandInput(SIZE_GROUP, tr('Size'))
    sizeGroup.isExpanded = uiState.getState(SIZE_GROUP)
    uiState.registerCommandInput(sizeGroup)
    names = dropdownNames()
    addDropdown(sizeGroup.children, SIZING_MODE_DROPDOWN, tr('Width'), names[SIZING_MODE_DROPDOWN])
    unitsInput = sizeGroup.children.addFloatSpinnerCommandInput(WIDTH_UNITS_INPUT, tr('Width (u)'), '', 0.5, 7, 0.5, uiState.getState(WIDTH_UNITS_INPUT))
    unitsInput.tooltip = tr('Width of the bin label pocket it goes into, in base units, 1u = 36 mm with 42 mm units like Cullenect')
    uiState.registerCommandInput(unitsInput)
    addLength(sizeGroup.children, FREE_WIDTH_INPUT, tr('Width'), tr('Free width, e.g. for the pocket of a compartment tab, the bin dialog shows its insert width'))
    baseWidthInput = addLength(sizeGroup.children, BASE_WIDTH_INPUT, tr('Base width unit (mm)'), tr('Grid of the bins, the width in base units is counted in it'))
    baseWidthInput.minimumValue = BASE_UNIT_MIN
    baseWidthInput.isMinimumInclusive = True
    for (inputId, label, tooltip) in [
        (OFFSET_X_INPUT, tr('Correction width'), tr("Added to the width, for printers printing too wide or too narrow, Cullenect's offset_xy, at most 1 mm either way")),
        (OFFSET_Y_INPUT, tr('Correction height'), tr('Added to the height of 11 mm, at most 1 mm either way')),
    ]:
        offsetInput = addLength(sizeGroup.children, inputId, label, tooltip)
        offsetInput.minimumValue = -cullenectLabelLayout.MAX_OFFSET
        offsetInput.maximumValue = cullenectLabelLayout.MAX_OFFSET
        offsetInput.isMinimumInclusive = True
        offsetInput.isMaximumInclusive = True
    sizeGroup.children.addTextBoxCommandInput(SIZE_TEXT, tr('Insert', 'label insert'), '', 2, True)

    textGroup = inputs.addGroupCommandInput(TEXT_GROUP, tr('Text'))
    textGroup.isExpanded = uiState.getState(TEXT_GROUP)
    uiState.registerCommandInput(textGroup)
    for (inputId, label) in [(LINE_1_INPUT, tr('Line 1')), (LINE_2_INPUT, tr('Line 2'))]:
        stringInput = textGroup.children.addStringValueInput(inputId, label, uiState.getState(inputId))
        uiState.registerCommandInput(stringInput)
    addDropdown(textGroup.children, TEXT_STYLE_DROPDOWN, tr('Text style'), names[TEXT_STYLE_DROPDOWN]).tooltip = \
        tr('Heavy is Arial Black, its strokes print with a 0.4 mm nozzle. Regular and Bold are Arial, thin when small')
    addDropdown(textGroup.children, SURFACE_DROPDOWN, tr('Text and symbol'), names[SURFACE_DROPDOWN]).tooltip = \
        tr('Raised 0.4 mm, or set 0.4 mm in, as a body of its own to print in another colour. Set in keeps that body hidden, flush shows it')
    addDropdown(textGroup.children, TEXT_COLOR_DROPDOWN, tr('Text color'), names[TEXT_COLOR_DROPDOWN]).tooltip = \
        tr('Gives the text and symbol bodies this color, for printing them in another filament. None keeps the look of the insert')
    customColorInput = textGroup.children.addStringValueInput(CUSTOM_COLOR_INPUT, tr('Custom color'), uiState.getState(CUSTOM_COLOR_INPUT))
    customColorInput.tooltip = tr('#rrggbb, e.g. #D02020')
    uiState.registerCommandInput(customColorInput)

    symbolGroup = inputs.addGroupCommandInput(SYMBOL_GROUP, tr('Symbol'))
    symbolGroup.isExpanded = uiState.getState(SYMBOL_GROUP)
    uiState.registerCommandInput(symbolGroup)
    addBool(symbolGroup.children, SHOW_SCREW_INPUT, tr('Screw'), tr('A screw put together from head, shaft, threads and driver, at the right edge'))
    for (inputId, label) in [(HEAD_DROPDOWN, tr('Head')), (SHAFT_DROPDOWN, tr('Shaft')), (THREADS_DROPDOWN, tr('Threads')), (DRIVER_DROPDOWN, tr('Driver'))]:
        addDropdown(symbolGroup.children, inputId, label, names[inputId])
    addBool(symbolGroup.children, FLANGE_INPUT, tr('Flange'))
    addBool(symbolGroup.children, SECURITY_INPUT, tr('Security pin'))
    addDropdown(symbolGroup.children, HARDWARE_DROPDOWN, tr('Hardware'), names[HARDWARE_DROPDOWN]).tooltip = tr('Instead of a screw, new svg files in cullenectIcons/hardware show up here')
    symbolGroup.children.addTextBoxCommandInput(SYMBOL_TEXT, tr('Symbol'), '', 1, True)

    pocketGroup = inputs.addGroupCommandInput(POCKET_GROUP, tr('Pocket'))
    pocketGroup.isExpanded = True
    pocketInput = pocketGroup.children.addSelectionInput(POCKET_INPUT, tr('Pocket'), tr('A pocket joint origin of a bin, the insert is jointed into it'))
    pocketInput.addSelectionFilter(adsk.core.SelectionCommandInput.JointOrigins)
    pocketInput.setSelectionLimits(0, 1)
    pocketInput.tooltip = tr('Optional: pick the joint origin of a Cullenect pocket of a bin, the insert goes into it. Without, it goes beside the bins, baseplates and inserts there are')
    # a rebuilt insert goes into its pocket again unless it's picked off (Hauptsitzung 15.11.2026). Fusion may refuse
    # the pocket, the dialog stopped half built then (round 20, p220): the input stays empty and the dialog says so
    note = selectionPrefill.prefillSelection(pocketInput, rebuildPocket)
    if note is not None:
        futil.log(f'{CMD_NAME} pocket {rebuildPocket.name} of the rebuilt insert not picked, {note}')
        pocketGroup.children.addTextBoxCommandInput(
            POCKET_NOTE, '',
            tr("The pocket the insert was in, {name}, couldn't be picked. Pick it again, "
               "otherwise the insert is built where it was without a joint.", name=html.escape(rebuildPocket.name)),
            3, True,
        )

    inputChangesGroup = inputs.addGroupCommandInput(INPUT_CHANGES_GROUP, tr('Inputs'))
    inputChangesGroup.isExpanded = uiState.getState(INPUT_CHANGES_GROUP)
    uiState.registerCommandInput(inputChangesGroup)
    addDefaultsButtonRow(inputChangesGroup.children, INPUT_CHANGES_BUTTONS_BROWSER)
    addButtonRow(inputChangesGroup.children, CONFIG_BUTTONS_BROWSER)

    previewGroup = inputs.addGroupCommandInput(PREVIEW_GROUP, tr('Preview'))
    previewGroup.isExpanded = uiState.getState(PREVIEW_GROUP)
    uiState.registerCommandInput(previewGroup)
    addBool(previewGroup.children, SHOW_PREVIEW_INPUT, tr('Show preview (slow)'))
    previewGroup.children.addTextBoxCommandInput(PREVIEW_TIME_INPUT, tr('Last preview'), tr('None yet'), 1, True)

    updateInputs(inputs)

    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)
    futil.add_handler(args.command.select, command_select, local_handlers=local_handlers)
    futil.add_handler(args.command.incomingFromHTML, command_incoming_from_html, local_handlers=local_handlers)

def offerScrewChoices(inputs: adsk.core.CommandInputs) -> dict[str, list]:
    """
    Each screw dropdown offers only what makes a symbol with the blocks above it, a choice without one moves to the
    first that has one, see cullenectCatalog.screwChoices. Head None with driver Hex used to be offered with partial
    threads too and had no svg (p85). The values each block offers
    """
    options = screwOptions()
    selection = {field: keyOf(uiState.getState(inputId), options[field]) for (inputId, field) in SCREW_DROPDOWNS.items()}
    selection['flange'] = uiState.getState(FLANGE_INPUT)
    selection['security'] = uiState.getState(SECURITY_INPUT)
    (choices, corrected) = cullenectCatalog.screwChoices(cullenectCatalog.screwCombinationsOnDisk(ICONS_FOLDER), selection)
    for (inputId, field) in SCREW_DROPDOWNS.items():
        names = [cullenectCatalog.displayName(key) for key in choices[field]]
        selected = cullenectCatalog.displayName(corrected[field])
        dropdown = adsk.core.DropDownCommandInput.cast(inputs.itemById(inputId))
        if [dropdowns.valueOf(dropdown, dropdown.listItems.item(index).name) for index in range(dropdown.listItems.count)] != names:
            dropdown.listItems.clear()
            for name in names:
                dropdowns.addItem(dropdown, name, name == selected, context=HARDWARE_CONTEXT)
        uiState.updateValue(inputId, selected)
    uiState.updateValue(FLANGE_INPUT, corrected['flange'])
    uiState.updateValue(SECURITY_INPUT, corrected['security'])
    return choices

def updateInputs(inputs: adsk.core.CommandInputs):
    """Shows the inputs that apply and what the insert comes out as"""
    choices = offerScrewChoices(inputs)
    state = getInputsState()
    inputs.itemById(WIDTH_UNITS_INPUT).isVisible = state.useUnits
    inputs.itemById(BASE_WIDTH_INPUT).isVisible = state.useUnits
    inputs.itemById(FREE_WIDTH_INPUT).isVisible = not state.useUnits
    for inputId in SCREW_INPUTS:
        inputs.itemById(inputId).isEnabled = state.showScrew
    # a flange or security pin no symbol has stays off and locked
    inputs.itemById(FLANGE_INPUT).isEnabled = state.showScrew and len(choices['flange']) > 1
    inputs.itemById(SECURITY_INPUT).isEnabled = state.showScrew and len(choices['security']) > 1
    inputs.itemById(HARDWARE_DROPDOWN).isEnabled = not state.showScrew
    inputs.itemById(CUSTOM_COLOR_INPUT).isVisible = uiState.getState(TEXT_COLOR_DROPDOWN) == labelColors.CUSTOM_CHOICE
    inputs.itemById(SIZE_TEXT).formattedText = sizeText(state, selectedPocket(inputs))
    inputs.itemById(SYMBOL_TEXT).text = symbolText(state)

def selectedPocket(inputs: adsk.core.CommandInputs) -> adsk.fusion.JointOrigin | None:
    pocketInput = adsk.core.SelectionCommandInput.cast(inputs.itemById(POCKET_INPUT))
    if pocketInput is None or pocketInput.selectionCount == 0:
        return None
    return adsk.fusion.JointOrigin.cast(pocketInput.selection(0).entity)

def command_select(args: adsk.core.SelectionEventArgs):
    """Only joint origins of Cullenect pockets can be picked as the pocket"""
    if args.activeInput is None or args.activeInput.id != POCKET_INPUT:
        return
    args.isSelectable = pocketSizeMm(adsk.fusion.JointOrigin.cast(args.selection.entity)) is not None

def sizeText(state: InputState, pocket: adsk.fusion.JointOrigin | None = None) -> str:
    """The size the insert comes out, or why it can't be built"""
    (width, height) = labelSize(state)
    problem = labelProblem(state) or pocketProblem(state, pocket)
    text = tr('{width} x {height} mm', width=number(f'{width * 10:.2f}'), height=number(f'{height * 10:.2f}'))
    return text if problem is None else f'{text}<br><span style="color:#d04030">{problem}</span>'

def symbolText(state: InputState) -> str:
    (path, isScrew) = labelSymbol(state)
    if path is None:
        return tr('None') if not state.showScrew and state.hardware == NO_HARDWARE else tr('No svg for this symbol')
    return os.path.basename(path)

# the small notice after a part design was switched to hybrid for the insert, see designIntent.structurePlan
HYBRID_SWITCH_MESSAGE = designIntent.hybridSwitchMessage('insert')

def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    des = adsk.fusion.Design.cast(app.activeProduct)
    wasPart = des is not None and des.designIntent == adsk.fusion.DesignIntentTypes.PartDesignIntentType
    if generateLabel(args) is False:
        return
    if wasPart and des.designIntent == adsk.fusion.DesignIntentTypes.HybridDesignIntentType:
        ui.messageBox(HYBRID_SWITCH_MESSAGE, CMD_TITLE)
    # text fitted so small that a 0.4 mm nozzle leaves parts out (p130)
    hint = textStyles.hintText(textStyles.notes(), suggestHeavy=getInputsState().textStyle != textStyles.STYLE_HEAVY)
    if hint is not None:
        ui.messageBox(hint, CMD_TITLE)

def command_preview(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs
    if inputs.itemById(SHOW_PREVIEW_INPUT).value:
        if INPUTS_VALID:
            startTime = time.perf_counter()
            # a preview leaves a part design as it is, only OK switches it to hybrid
            isGenerated = generateLabel(args, mayChangeDocument=False) is not False
            seconds = time.perf_counter() - startTime
            inputs.itemById(PREVIEW_TIME_INPUT).text = f'{number(f"{seconds:.2f}")} s{textStyles.previewNote(textStyles.notes())}' if isGenerated else tr('failed after {seconds} s', seconds=number(f'{seconds:.2f}'))
        else:
            args.executeFailed = True
            args.executeFailedMessage = tr('Some inputs are invalid, unable to generate preview')

def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    if changed_input.id in (PREVIEW_TIME_INPUT, SIZE_TEXT, SYMBOL_TEXT):
        return
    uiState.onInputUpdate(changed_input)
    if changed_input.id == POCKET_INPUT:
        # the note that the old pocket couldn't be picked goes once one is picked (review round 20)
        note = changed_input.parentCommand.commandInputs.itemById(POCKET_NOTE)
        if note is not None:
            note.isVisible = adsk.core.SelectionCommandInput.cast(changed_input).selectionCount == 0
    if isinstance(changed_input, adsk.core.GroupCommandInput) and changed_input.isExpanded == True:
        for input in changed_input.children:
            uiState.registerCommandInput(input)
        uiState.forceUIRefresh()
    updateInputs(changed_input.parentCommand.commandInputs)
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')

def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    global INPUTS_VALID
    state = getInputsState()
    INPUTS_VALID = labelProblem(state) is None and pocketProblem(state, selectedPocket(args.inputs)) is None
    args.areInputsValid = INPUTS_VALID

def command_incoming_from_html(args: adsk.core.HTMLEventArgs):
    command = args.browserCommandInput.parentCommand

    def onDefaults(action: str):
        if action == DEFAULTS_SAVE:
            saveUIInputsAsDefaults()
            return
        if action == DEFAULTS_FACTORY_RESET:
            configUtils.deleteConfigFile(UI_INPUT_DEFAULTS_CONFIG_PATH)
        initUiState()
        fixDropdownStates()
        uiState.forceUIRefresh()
        updateInputs(command.commandInputs)
        if uiState.getInput(SHOW_PREVIEW_INPUT).value:
            command.doExecutePreview()

    def onLoadConfig(text: str, fileName: str):
        state = readConfig(text, tr('Loading "{fileName}"', fileName=fileName))
        if state is None:
            return
        applyInputsState(state)
        fixDropdownStates()
        uiState.forceUIRefresh()
        updateInputs(command.commandInputs)
        if uiState.getInput(SHOW_PREVIEW_INPUT).value:
            command.doExecutePreview()

    if args.browserCommandInput.id == INPUT_CHANGES_BUTTONS_BROWSER:
        browserPages.handleMessage(args, defaultsButtonsHandlers(onDefaults))
    elif args.browserCommandInput.id == CONFIG_BUTTONS_BROWSER:
        browserPages.handleMessage(args, configButtons.configButtonsHandlers(
            'label',
            lambda: configJson.configText(configJson.GENERATOR_LABEL, configJson.stateToJson(configJson.GENERATOR_LABEL, getInputsState()), tagUtils.getGeneratorVersion()),
            lambda: labelName(getInputsState()),
            onLoad=onLoadConfig,
        ))

def command_destroy(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Destroy Event')
    global local_handlers
    global rebuildBodyToken
    local_handlers = []
    rebuildBodyToken = None
    if args.terminationReason == adsk.core.CommandTerminationReason.CompletedTerminationReason and len(rebuildNotes) > 0:
        ui.messageBox(
            tr('The insert was rebuilt. These features after it need a look, ones using a face or an edge of the old '
               'insert need them picked again:') + '\n\n' + '\n'.join(rebuildNotes),
            CMD_TITLE,
            adsk.core.MessageBoxButtonTypes.OKButtonType,
            adsk.core.MessageBoxIconTypes.WarningIconType,
        )

def snapshotSettings(inputs: adsk.core.CommandInputs) -> list[dict]:
    return settingsUtils.snapshotInputs(inputs, [INFO_GROUP, INPUT_CHANGES_GROUP, PREVIEW_GROUP, POCKET_GROUP], SETTINGS_TITLE)

def generateLabel(args: adsk.core.CommandEventArgs, mayChangeDocument: bool = True):
    startTime = time.perf_counter()
    settings = snapshotSettings(args.command.commandInputs)
    commonUtils.fileLog(f'{CMD_NAME} Generating label with settings:\n{settingsUtils.settingsText(settings)}')
    state = getInputsState()
    # notes of an earlier build, a preview or a failed one, are not this one's
    textStyles.clearNotes()
    global rebuildNotes
    rebuildNotes = []
    try:
        des = adsk.fusion.Design.cast(app.activeProduct)
        pocket = selectedPocket(args.command.commandInputs)
        # the component active before is again afterwards, the build activates its own (as the bin dialog)
        with commonUtils.keepActiveComponent(des):
            if rebuildBodyToken is not None:
                body = rebuildUtils.findBodyByToken(des, rebuildBodyToken)
                (_, rebuildNotes) = rebuildLabel(des, body, state, settings, not mayChangeDocument, pocket)
            else:
                buildLabel(des, state, settings, mayChangeDocument, pocket)
        futil.log(f'{CMD_NAME} {labelName(state)} generated in {time.perf_counter() - startTime:.3f}s')
    except UnsupportedDesignTypeException:
        args.executeFailed = True
        args.executeFailedMessage = tr('Design type is unsupported. Projects with disabled design history are unsupported, please enable timeline feature to proceed.')
        return False
    except Exception as err:
        args.executeFailed = True
        args.executeFailedMessage = getErrorMessage()
        futil.log(f'{CMD_NAME} Error occurred, {err}, {getErrorMessage()}')
        return False

def initUiState():
    for group in (INFO_GROUP, SIZE_GROUP, TEXT_GROUP, SYMBOL_GROUP, INPUT_CHANGES_GROUP, PREVIEW_GROUP):
        uiState.initValue(group, True, adsk.core.GroupCommandInput.classType())
    dropdown = adsk.core.DropDownCommandInput.classType()
    value = adsk.core.ValueCommandInput.classType()
    boolean = adsk.core.BoolValueCommandInput.classType()
    string = adsk.core.StringValueCommandInput.classType()
    uiState.initValue(SIZING_MODE_DROPDOWN, SIZING_MODE_UNITS, dropdown)
    uiState.initValue(WIDTH_UNITS_INPUT, 1, adsk.core.FloatSpinnerCommandInput.classType())
    uiState.initValue(FREE_WIDTH_INPUT, 2.5, value)
    uiState.initValue(BASE_WIDTH_INPUT, DIMENSION_DEFAULT_WIDTH_UNIT, value)
    uiState.initValue(OFFSET_X_INPUT, 0, value)
    uiState.initValue(OFFSET_Y_INPUT, 0, value)
    uiState.initValue(LINE_1_INPUT, 'M3x10', string)
    uiState.initValue(LINE_2_INPUT, '', string)
    uiState.initValue(TEXT_STYLE_DROPDOWN, textStyles.DEFAULT_INSERT_STYLE, dropdown)
    uiState.initValue(SURFACE_DROPDOWN, SURFACE_NAMES[cullenectLabelGenerator.SURFACE_EMBOSSED], dropdown)
    uiState.initValue(TEXT_COLOR_DROPDOWN, labelColors.NO_COLOR_CHOICE, dropdown)
    uiState.initValue(CUSTOM_COLOR_INPUT, '', string)
    uiState.initValue(SHOW_SCREW_INPUT, True, boolean)
    uiState.initValue(HEAD_DROPDOWN, cullenectCatalog.displayName('socket'), dropdown)
    uiState.initValue(SHAFT_DROPDOWN, cullenectCatalog.displayName('machine'), dropdown)
    uiState.initValue(THREADS_DROPDOWN, cullenectCatalog.displayName('full'), dropdown)
    uiState.initValue(DRIVER_DROPDOWN, cullenectCatalog.displayName('hex'), dropdown)
    uiState.initValue(FLANGE_INPUT, False, boolean)
    uiState.initValue(SECURITY_INPUT, False, boolean)
    uiState.initValue(HARDWARE_DROPDOWN, HARDWARE_NONE, dropdown)
    uiState.initValue(SHOW_PREVIEW_INPUT, False, boolean)

    recordedDefaults = configUtils.readJsonConfig(UI_INPUT_DEFAULTS_CONFIG_PATH)
    if recordedDefaults:
        try:
            uiState.initValues(recordedDefaults)
            futil.log(f'{CMD_NAME} Successfully restored default values')
        except Exception as err:
            futil.log(f'{CMD_NAME} Failed to restore default values, err: {err}')

def saveUIInputsAsDefaults():
    futil.log(f'{CMD_NAME} Saving UI state to file')
    configUtils.dumpJsonConfig(UI_INPUT_DEFAULTS_CONFIG_PATH, uiState.toDict())

def keyOf(name: str, keys: list[str]) -> str:
    """The Cullenect name of a shown name"""
    return next((key for key in keys if cullenectCatalog.displayName(key) == name), name)

def getInputsState() -> InputState:
    options = screwOptions()
    hardwareName = uiState.getState(HARDWARE_DROPDOWN)
    hardwareKeys = [os.path.splitext(os.path.basename(path))[0] for (_, path) in cullenectCatalog.listHardwareIcons(ICONS_FOLDER)]
    surfaceName = uiState.getState(SURFACE_DROPDOWN)
    return InputState(
        baseWidth=uiState.getState(BASE_WIDTH_INPUT),
        useUnits=uiState.getState(SIZING_MODE_DROPDOWN) == SIZING_MODE_UNITS,
        widthUnits=uiState.getState(WIDTH_UNITS_INPUT),
        freeWidth=uiState.getState(FREE_WIDTH_INPUT),
        offsetX=uiState.getState(OFFSET_X_INPUT),
        offsetY=uiState.getState(OFFSET_Y_INPUT),
        line1=uiState.getState(LINE_1_INPUT),
        line2=uiState.getState(LINE_2_INPUT),
        textStyle=uiState.getState(TEXT_STYLE_DROPDOWN),
        showScrew=uiState.getState(SHOW_SCREW_INPUT),
        head=keyOf(uiState.getState(HEAD_DROPDOWN), options['head']),
        shaft=keyOf(uiState.getState(SHAFT_DROPDOWN), options['shaft']),
        threads=keyOf(uiState.getState(THREADS_DROPDOWN), options['threads']),
        driver=keyOf(uiState.getState(DRIVER_DROPDOWN), options['driver']),
        flange=uiState.getState(FLANGE_INPUT),
        security=uiState.getState(SECURITY_INPUT),
        hardware=NO_HARDWARE if hardwareName == HARDWARE_NONE else keyOf(hardwareName, hardwareKeys),
        surface=next((key for (key, name) in SURFACE_NAMES.items() if name == surfaceName), cullenectLabelGenerator.SURFACE_EMBOSSED),
        textColor=labelColors.dialogColor(uiState.getState(TEXT_COLOR_DROPDOWN), uiState.getState(CUSTOM_COLOR_INPUT)),
    )

# --- saving, loading, cloning and rebuilding (round 18, p150), as commandCreateBaseplate.entry of upstream v2.4

def applyInputsState(state: InputState):
    """Sets the dialog state to a state, the way back of getInputsState, the inputs follow on forceUIRefresh"""
    values = labelConfig.dialogValues(configJson.stateToJson(configJson.GENERATOR_LABEL, state), SURFACE_NAMES)
    uiState.setValue(BASE_WIDTH_INPUT, state.baseWidth)
    uiState.setValue(SIZING_MODE_DROPDOWN, SIZING_MODE_UNITS if state.useUnits else SIZING_MODE_FREE)
    uiState.setValue(WIDTH_UNITS_INPUT, state.widthUnits)
    uiState.setValue(FREE_WIDTH_INPUT, state.freeWidth)
    uiState.setValue(OFFSET_X_INPUT, state.offsetX)
    uiState.setValue(OFFSET_Y_INPUT, state.offsetY)
    uiState.setValue(LINE_1_INPUT, state.line1)
    uiState.setValue(LINE_2_INPUT, state.line2)
    uiState.setValue(TEXT_STYLE_DROPDOWN, state.textStyle)
    uiState.setValue(SHOW_SCREW_INPUT, state.showScrew)
    for (inputId, field) in SCREW_DROPDOWNS.items():
        uiState.setValue(inputId, values[field])
    uiState.setValue(FLANGE_INPUT, state.flange)
    uiState.setValue(SECURITY_INPUT, state.security)
    uiState.setValue(HARDWARE_DROPDOWN, values['hardware'])
    uiState.setValue(SURFACE_DROPDOWN, values['surface'])
    uiState.setValue(TEXT_COLOR_DROPDOWN, values['colorChoice'])
    uiState.setValue(CUSTOM_COLOR_INPUT, values['customColor'])

def configChoices() -> dict[str, configJson.Choice]:
    """The options of the dropdowns a config can't set to anything else, with the dialog's first defaults"""
    options = screwOptions()
    hardwareKeys = [os.path.splitext(os.path.basename(path))[0] for (_, path) in cullenectCatalog.listHardwareIcons(ICONS_FOLDER)]
    defaults = configJson.stateToJson(configJson.GENERATOR_LABEL, DEFAULT_STATE)
    # a screw block or hardware this install has no svg for is said and replaced, not reset without a word (review)
    choices = {field: configJson.Choice(options[field], defaults[field] if defaults[field] in options[field] else options[field][0]) for field in SCREW_DROPDOWNS.values()}
    choices['hardware'] = configJson.Choice([NO_HARDWARE] + hardwareKeys, NO_HARDWARE)
    choices['textStyle'] = configJson.Choice(textStyles.STYLES, textStyles.DEFAULT_INSERT_STYLE)
    choices['surface'] = configJson.Choice(cullenectLabelGenerator.SURFACES, cullenectLabelGenerator.SURFACE_EMBOSSED)
    return choices

def readConfig(text: str, source: str) -> InputState | None:
    """The state of a config, none when it can't be read, see configButtons.readConfig"""
    return configButtons.readConfig(text, source, configJson.GENERATOR_LABEL, InputState, getInputsState(), configChoices())

def configFileName(settings: dict) -> str:
    """The name a saved file of these settings starts with, as the dialog's Save to file names it"""
    defaults = configJson.stateToJson(configJson.GENERATOR_LABEL, DEFAULT_STATE)
    known = {name: value for (name, value) in settings.items() if name in defaults}
    return labelName(configJson.stateFromJson(configJson.GENERATOR_LABEL, InputState, {**defaults, **known}))

def startWithConfig(settings: dict):
    """Opens the dialog with a config by field name, see configJson.stateToJson, settings it doesn't have stay"""
    global pendingConfig
    global pendingRebuildBody
    global pendingRebuildPocket
    pendingConfig = settings
    if not ui.commandDefinitions.itemById(CMD_ID).execute():
        # no dialog took them, the next one opened by hand mustn't rebuild or clone (review)
        pendingConfig = None
        pendingRebuildBody = None
        pendingRebuildPocket = None

def startRebuild(body: adsk.fusion.BRepBody, tag: dict):
    """
    Opens the dialog with the settings of the insert the body is of, its tag value, to rebuild it in place, see
    labelBuilder.rebuildLabel. Its text and base width parameters may have been changed since, their values replace
    the settings. An insert in a pocket has it picked again
    """
    global pendingRebuildBody
    global pendingRebuildPocket
    design = adsk.fusion.Design.cast(app.activeProduct)
    settings = rebuildUtils.configWithParameters(configJson.GENERATOR_LABEL, tag['config'], tag.get('parameters'), design.userParameters.itemByName, labelConfig.PARAMETER_FIELDS)
    pendingRebuildBody = body
    pendingRebuildPocket = insertPocket(design, body)
    startWithConfig(settings)

def applyPendingConfig():
    global pendingConfig
    if pendingConfig is None:
        return
    state = readConfig(configJson.configText(configJson.GENERATOR_LABEL, pendingConfig), tr('Rebuilding') if rebuildBodyToken is not None else tr('Cloned'))
    pendingConfig = None
    if state is not None:
        applyInputsState(state)
        fixDropdownStates()
