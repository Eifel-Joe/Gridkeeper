import adsk.core, adsk.fusion, traceback
import os
import time

from ...lib import configUtils
from ...lib import tagUtils
from ...lib import settingsUtils
from ...lib import fusion360utils as futil
from ... import config
from ...lib.gridfinityUtils.const import DIMENSION_DEFAULT_WIDTH_UNIT
from ...lib.gridfinityUtils import commonUtils
from ...lib.gridfinityUtils import cullenectCatalog
from ...lib.gridfinityUtils import cullenectLabelGenerator
from ...lib.gridfinityUtils import cullenectLabelLayout
from ...lib.gridfinityUtils import sharedParameters
from ...lib.gridfinityUtils import labelColors
from ...lib.gridfinityUtils import textStyles
from .inputState import InputState
from .labelBuilder import buildLabel, labelName, labelProblem, labelSize, labelSymbol, ICONS_FOLDER, NO_HARDWARE
from ...lib.ui.commandUiState import CommandUiState
from ...lib.ui.defaultsButtons import addDefaultsButtonRow, defaultsButtonsHandlers, DEFAULTS_SAVE, DEFAULTS_FACTORY_RESET
from ...lib.ui import browserPages
from ...lib.ui.unsupportedDesignTypeException import UnsupportedDesignTypeException

# Dialog of the label command, Cullenect inserts by CullenJWebb (MIT), https://github.com/CullenJWebb/Cullenect-Labels

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdLabel'
CMD_NAME = 'Gridfinity label'
# shown on hover over the button, the first paragraph says what it makes, the second how
CMD_Description = ('Creates a Cullenect label insert for the label sockets of bins.\n\n'
    'Set its width in base units or in mm, up to two lines of text and a screw or hardware symbol. The text and symbol '
    'are bodies of their own, raised, set in or flush, to print them in another colour.')

uiState = CommandUiState(CMD_NAME)
IS_PROMOTED = False

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')
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
PREVIEW_TIME_INPUT = 'preview_time'

SIZING_MODE_UNITS = 'Base units'
SIZING_MODE_FREE = 'Width in mm'
SURFACE_NAMES = {
    cullenectLabelGenerator.SURFACE_EMBOSSED: 'Raised',
    cullenectLabelGenerator.SURFACE_DEBOSSED: 'Set in',
    cullenectLabelGenerator.SURFACE_FLUSH: 'Flush',
}
SCREW_DROPDOWNS = {HEAD_DROPDOWN: 'head', SHAFT_DROPDOWN: 'shaft', THREADS_DROPDOWN: 'threads', DRIVER_DROPDOWN: 'driver'}
SCREW_INPUTS = list(SCREW_DROPDOWNS.keys()) + [FLANGE_INPUT, SECURITY_INPUT]

INFO_TEXT = ("<b>Help:</b> The insert clicks into the Cullenect pockets of bin label tabs, label style Cullenect. "
             "Cullenect labels by CullenJWebb, "
             "<a href=\"https://github.com/CullenJWebb/Cullenect-Labels\">Cullenect-Labels</a> (MIT).")

INPUTS_VALID = True

def infoText():
    version = tagUtils.getGeneratorVersion()
    return f"{INFO_TEXT}<br><span style=\"color:#808080; font-size:small\">Version {version}</span>" if version else INFO_TEXT

def getErrorMessage(text = "An unknown error occurred, please validate your inputs and try again"):
    return f"{text}:<br>{traceback.format_exc()}"

def showErrorInMessageBox(text = "An unknown error occurred, please validate your inputs and try again"):
    if ui:
        ui.messageBox(getErrorMessage(text), f"{CMD_NAME} Error")

def start():
    futil.log(f'{CMD_NAME} Command Start Event')
    try:
        addinConfig = configUtils.readConfig(CONFIG_FOLDER_PATH)
        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
        if not cmd_def:
            cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
            futil.add_handler(cmd_def.commandCreated, command_created)
            workspace = ui.workspaces.itemById(WORKSPACE_ID)
            panel = workspace.toolbarPanels.itemById(PANEL_ID)
            control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
            control.isPromoted = addinConfig['UI'].getboolean('is_promoted', fallback=IS_PROMOTED)
        initUiState()
    except Exception as err:
        futil.log(f'{CMD_NAME} Error occurred at the start, {err}, {getErrorMessage()}')
        showErrorInMessageBox(f"{CMD_NAME} Critical error occurred at the start, the command will be unavailable")

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

def applySharedParameterDefaults():
    """The design's shared base width replaces the remembered one, so inserts match the bins of the design"""
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        return
    (baseWidth, _) = sharedParameters.usableSharedBaseUnits(design)
    if baseWidth is not None:
        uiState.initValue(BASE_WIDTH_INPUT, baseWidth, adsk.core.ValueCommandInput.classType())

def screwOptions() -> dict[str, list]:
    return cullenectCatalog.screwOptions(ICONS_FOLDER)

def dropdownNames() -> dict[str, list[str]]:
    """The names each dropdown offers, the screw building blocks and hardware read from the symbol folders"""
    options = screwOptions()
    names = {inputId: [cullenectCatalog.displayName(key) for key in options[field]] for (inputId, field) in SCREW_DROPDOWNS.items()}
    names[HARDWARE_DROPDOWN] = ['None'] + [name for (name, _) in cullenectCatalog.listHardwareIcons(ICONS_FOLDER)]
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
        selected = names[0]
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
        dropdown.listItems.add(name, name == selected)
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
    applySharedParameterDefaults()
    inputs = args.command.commandInputs

    infoGroup = inputs.addGroupCommandInput(INFO_GROUP, 'Info')
    infoGroup.isExpanded = uiState.getState(INFO_GROUP)
    uiState.registerCommandInput(infoGroup)
    info = infoText()
    infoGroup.children.addTextBoxCommandInput("info_text", "Info", info, info.count('<br>') + 3, True)

    sizeGroup = inputs.addGroupCommandInput(SIZE_GROUP, 'Size')
    sizeGroup.isExpanded = uiState.getState(SIZE_GROUP)
    uiState.registerCommandInput(sizeGroup)
    names = dropdownNames()
    addDropdown(sizeGroup.children, SIZING_MODE_DROPDOWN, 'Width', names[SIZING_MODE_DROPDOWN])
    unitsInput = sizeGroup.children.addFloatSpinnerCommandInput(WIDTH_UNITS_INPUT, 'Width (u)', '', 0.5, 7, 0.5, uiState.getState(WIDTH_UNITS_INPUT))
    unitsInput.tooltip = 'Width of the bin label pocket it goes into, in base units, 1u = 36 mm with 42 mm units like Cullenect'
    uiState.registerCommandInput(unitsInput)
    addLength(sizeGroup.children, FREE_WIDTH_INPUT, 'Width', 'Free width, e.g. for the pocket of a compartment tab, the bin dialog shows its insert width')
    baseWidthInput = addLength(sizeGroup.children, BASE_WIDTH_INPUT, 'Base width unit (mm)', 'Grid of the bins, the width in base units is counted in it')
    baseWidthInput.minimumValue = sharedParameters.BASE_UNIT_MIN
    baseWidthInput.isMinimumInclusive = True
    for (inputId, label, tooltip) in [
        (OFFSET_X_INPUT, 'Correction width', "Added to the width, for printers printing too wide or too narrow, Cullenect's offset_xy, at most 1 mm either way"),
        (OFFSET_Y_INPUT, 'Correction height', 'Added to the height of 11 mm, at most 1 mm either way'),
    ]:
        offsetInput = addLength(sizeGroup.children, inputId, label, tooltip)
        offsetInput.minimumValue = -cullenectLabelLayout.MAX_OFFSET
        offsetInput.maximumValue = cullenectLabelLayout.MAX_OFFSET
        offsetInput.isMinimumInclusive = True
        offsetInput.isMaximumInclusive = True
    sizeGroup.children.addTextBoxCommandInput(SIZE_TEXT, 'Insert', '', 2, True)

    textGroup = inputs.addGroupCommandInput(TEXT_GROUP, 'Text')
    textGroup.isExpanded = uiState.getState(TEXT_GROUP)
    uiState.registerCommandInput(textGroup)
    for (inputId, label) in [(LINE_1_INPUT, 'Line 1'), (LINE_2_INPUT, 'Line 2')]:
        stringInput = textGroup.children.addStringValueInput(inputId, label, uiState.getState(inputId))
        uiState.registerCommandInput(stringInput)
    addDropdown(textGroup.children, TEXT_STYLE_DROPDOWN, 'Text style', names[TEXT_STYLE_DROPDOWN]).tooltip =         'Heavy is Arial Black, its strokes print with a 0.4 mm nozzle. Regular and Bold are Arial, thin when small'
    addDropdown(textGroup.children, SURFACE_DROPDOWN, 'Text and symbol', names[SURFACE_DROPDOWN]).tooltip = \
        'Raised 0.4 mm, or set 0.4 mm in, as a body of its own to print in another colour. Set in keeps that body hidden, flush shows it'
    addDropdown(textGroup.children, TEXT_COLOR_DROPDOWN, 'Text color', names[TEXT_COLOR_DROPDOWN]).tooltip = \
        'Gives the text and symbol bodies this color, for printing them in another filament. None keeps the look of the insert'
    customColorInput = textGroup.children.addStringValueInput(CUSTOM_COLOR_INPUT, 'Custom color', uiState.getState(CUSTOM_COLOR_INPUT))
    customColorInput.tooltip = '#rrggbb, e.g. #D02020'
    uiState.registerCommandInput(customColorInput)

    symbolGroup = inputs.addGroupCommandInput(SYMBOL_GROUP, 'Symbol')
    symbolGroup.isExpanded = uiState.getState(SYMBOL_GROUP)
    uiState.registerCommandInput(symbolGroup)
    addBool(symbolGroup.children, SHOW_SCREW_INPUT, 'Screw', 'A screw put together from head, shaft, threads and driver, at the right edge')
    for (inputId, label) in [(HEAD_DROPDOWN, 'Head'), (SHAFT_DROPDOWN, 'Shaft'), (THREADS_DROPDOWN, 'Threads'), (DRIVER_DROPDOWN, 'Driver')]:
        addDropdown(symbolGroup.children, inputId, label, names[inputId])
    addBool(symbolGroup.children, FLANGE_INPUT, 'Flange')
    addBool(symbolGroup.children, SECURITY_INPUT, 'Security pin')
    addDropdown(symbolGroup.children, HARDWARE_DROPDOWN, 'Hardware', names[HARDWARE_DROPDOWN]).tooltip = 'Instead of a screw, new svg files in cullenectIcons/hardware show up here'
    symbolGroup.children.addTextBoxCommandInput(SYMBOL_TEXT, 'Symbol', '', 1, True)

    inputChangesGroup = inputs.addGroupCommandInput(INPUT_CHANGES_GROUP, 'Inputs')
    inputChangesGroup.isExpanded = uiState.getState(INPUT_CHANGES_GROUP)
    uiState.registerCommandInput(inputChangesGroup)
    addDefaultsButtonRow(inputChangesGroup.children, INPUT_CHANGES_BUTTONS_BROWSER)

    previewGroup = inputs.addGroupCommandInput(PREVIEW_GROUP, 'Preview')
    previewGroup.isExpanded = uiState.getState(PREVIEW_GROUP)
    uiState.registerCommandInput(previewGroup)
    addBool(previewGroup.children, SHOW_PREVIEW_INPUT, 'Show preview (slow)')
    previewGroup.children.addTextBoxCommandInput(PREVIEW_TIME_INPUT, 'Last preview', 'None yet', 1, True)

    updateInputs(inputs)

    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)
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
        if [dropdown.listItems.item(index).name for index in range(dropdown.listItems.count)] != names:
            dropdown.listItems.clear()
            for name in names:
                dropdown.listItems.add(name, name == selected)
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
    inputs.itemById(SIZE_TEXT).formattedText = sizeText(state)
    inputs.itemById(SYMBOL_TEXT).text = symbolText(state)

def sizeText(state: InputState) -> str:
    """The size the insert comes out, or why it can't be built"""
    (width, height) = labelSize(state)
    problem = labelProblem(state)
    text = f'{width * 10:.2f} x {height * 10:.2f} mm'
    return text if problem is None else f'{text}<br><span style="color:#d04030">{problem}</span>'

def symbolText(state: InputState) -> str:
    (path, isScrew) = labelSymbol(state)
    if path is None:
        return 'None' if not state.showScrew and state.hardware == NO_HARDWARE else 'No svg for this symbol'
    return os.path.basename(path)

# the small notice after a part design was switched to hybrid for the insert, see designIntent.componentPlan
HYBRID_SWITCH_MESSAGE = ('This document was a part design. It has been switched to a hybrid design, so the insert is a '
    'component of its own. A design holding components can no longer be switched back to a part design.')

def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    des = adsk.fusion.Design.cast(app.activeProduct)
    wasPart = des is not None and des.designIntent == adsk.fusion.DesignIntentTypes.PartDesignIntentType
    if generateLabel(args) is not False and wasPart and des.designIntent == adsk.fusion.DesignIntentTypes.HybridDesignIntentType:
        ui.messageBox(HYBRID_SWITCH_MESSAGE, CMD_NAME)

def command_preview(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs
    if inputs.itemById(SHOW_PREVIEW_INPUT).value:
        if INPUTS_VALID:
            startTime = time.perf_counter()
            # a preview leaves a part design as it is, only OK switches it to hybrid
            isGenerated = generateLabel(args, mayChangeDocument=False) is not False
            seconds = time.perf_counter() - startTime
            inputs.itemById(PREVIEW_TIME_INPUT).text = f'{seconds:.2f} s' if isGenerated else f'failed after {seconds:.2f} s'
        else:
            args.executeFailed = True
            args.executeFailedMessage = "Some inputs are invalid, unable to generate preview"

def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    if changed_input.id in (PREVIEW_TIME_INPUT, SIZE_TEXT, SYMBOL_TEXT):
        return
    uiState.onInputUpdate(changed_input)
    if isinstance(changed_input, adsk.core.GroupCommandInput) and changed_input.isExpanded == True:
        for input in changed_input.children:
            uiState.registerCommandInput(input)
        uiState.forceUIRefresh()
    updateInputs(changed_input.parentCommand.commandInputs)
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')

def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    global INPUTS_VALID
    INPUTS_VALID = labelProblem(getInputsState()) is None
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

    if args.browserCommandInput.id == INPUT_CHANGES_BUTTONS_BROWSER:
        browserPages.handleMessage(args, defaultsButtonsHandlers(onDefaults))

def command_destroy(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Destroy Event')
    global local_handlers
    local_handlers = []

def snapshotSettings(inputs: adsk.core.CommandInputs) -> list[dict]:
    return settingsUtils.snapshotInputs(inputs, [INFO_GROUP, INPUT_CHANGES_GROUP, PREVIEW_GROUP], CMD_NAME)

def generateLabel(args: adsk.core.CommandEventArgs, mayChangeDocument: bool = True):
    startTime = time.perf_counter()
    settings = snapshotSettings(args.command.commandInputs)
    commonUtils.fileLog(f'{CMD_NAME} Generating label with settings:\n{settingsUtils.settingsText(settings)}')
    state = getInputsState()
    try:
        des = adsk.fusion.Design.cast(app.activeProduct)
        buildLabel(des, state, settings, mayChangeDocument)
        futil.log(f'{CMD_NAME} {labelName(state)} generated in {time.perf_counter() - startTime:.3f}s')
    except UnsupportedDesignTypeException:
        args.executeFailed = True
        args.executeFailedMessage = 'Design type is unsupported. Projects with disabled design history are unsupported, please enable timeline feature to proceed.'
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
    uiState.initValue(HARDWARE_DROPDOWN, 'None', dropdown)
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
        hardware=NO_HARDWARE if hardwareName == 'None' else keyOf(hardwareName, hardwareKeys),
        surface=next((key for (key, name) in SURFACE_NAMES.items() if name == surfaceName), cullenectLabelGenerator.SURFACE_EMBOSSED),
        textColor=labelColors.dialogColor(uiState.getState(TEXT_COLOR_DROPDOWN), uiState.getState(CUSTOM_COLOR_INPUT)),
    )
