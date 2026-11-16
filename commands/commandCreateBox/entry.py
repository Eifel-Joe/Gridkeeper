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
from ...lib.gridfinityUtils import commonUtils
from ...lib.gridfinityUtils import magnetSizes
from ...lib.gridfinityUtils import predBoxConfig
from .inputState import InputState
from .boxBuilder import buildBox, rebuildBox, boxName, boxProblem
from ...lib import configJson
from ...lib import defaultSettings
from ...lib import rebuildUtils
from ...lib.ui.commandUiState import CommandUiState
from ...lib.ui.defaultsButtons import addDefaultsButtonRow, defaultsButtonsHandlers, DEFAULTS_SAVE, DEFAULTS_FACTORY_RESET
from ...lib.ui.buttonRow import addButtonRow
from ...lib.ui import configButtons
from ...lib.ui import browserPages
from ...lib.ui.unsupportedDesignTypeException import UnsupportedDesignTypeException

# Dialog of the box command: a storage box after Pred's parametric Gridfinity Storage Box v1.1
# (https://www.printables.com/model/543553, CC BY-NC), rebuilt in code for Gridkeeper (round 27, p260)

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdBox'
CMD_NAME = 'Gridkeeper box'
# the first section of a part's settings names the part, as the settings window does (review round 23)
SETTINGS_TITLE = 'Gridfinity box'
CMD_Description = ("Creates a storage box with lid after Pred's parametric Gridfinity Storage Box v1.1.\n\n"
    'Set its width and length in grid cells and its height in units. Box and lid stack and latch with boxes printed '
    "from Pred's file; latches, hinges, handle and label holder seats are built in.")

uiState = CommandUiState(CMD_NAME)
IS_PROMOTED = False

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')
CONFIG_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'commandConfig')
UI_INPUT_DEFAULTS_CONFIG_PATH = os.path.join(CONFIG_FOLDER_PATH, "ui_input_defaults.json")

local_handlers = []

INFO_GROUP = 'info_group'
SIZE_GROUP = 'size_group'
MAGNET_GROUP = 'magnet_group'
JOINT_GROUP = 'joint_group'
INPUT_CHANGES_GROUP = 'input_changes_group'
PREVIEW_GROUP = 'preview_group'
GRID_X_INPUT = 'grid_x'
GRID_Y_INPUT = 'grid_y'
HEIGHT_U_INPUT = 'height_u'
SIZE_TEXT = 'size_text'
MAGNETS_INPUT = 'with_magnets'
MAGNET_SIZE_DROPDOWN = 'magnet_size'
MAGNET_DEPTH_INPUT = 'magnet_height'
MAGNET_DIAMETER_INPUT = 'magnet_diameter'
JOINT_ORIGINS_INPUT = 'joint_origins'
INPUT_CHANGES_BUTTONS_BROWSER = 'input_changes_buttons'
CONFIG_BUTTONS_BROWSER = 'config_buttons'
SHOW_PREVIEW_INPUT = 'show_preview'
PREVIEW_TIME_INPUT = 'preview_time'

INFO_TEXT = ("<b>Help:</b> every input is explained "
             "<a href=\"https://eifel-joe.github.io/Gridkeeper/boxes/\">in the Gridkeeper documentation</a>. "
             "Based on Pred's Gridfinity Storage Box v1.1, "
             "<a href=\"https://www.printables.com/model/543553\">Printables 543553</a> (CC BY-NC), "
             "rebuilt in code for Gridkeeper.")

INPUTS_VALID = True

pendingConfig: dict | None = None
pendingRebuildBody: adsk.fusion.BRepBody | None = None
rebuildBodyToken: str | None = None
rebuildNotes: list[str] = []
DEFAULT_STATE = configJson.stateFromJson(configJson.GENERATOR_BOX, InputState, defaultSettings.SETTINGS[configJson.GENERATOR_BOX])


def infoText():
    version = tagUtils.getGeneratorVersion()
    return f"{INFO_TEXT}<br><span style=\"color:#808080; font-size:small\">Version {version}</span>" if version else INFO_TEXT


def getErrorMessage(text="An unknown error occurred, please validate your inputs and try again"):
    return f"{text}:<br>{traceback.format_exc()}"


def showErrorInMessageBox(text="An unknown error occurred, please validate your inputs and try again"):
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


def addSpinner(inputs, inputId, label, minimum, maximum, tooltip):
    spinner = inputs.addIntegerSpinnerCommandInput(inputId, label, minimum, maximum, 1, uiState.getState(inputId))
    spinner.tooltip = tooltip
    uiState.registerCommandInput(spinner)
    return spinner


def addLength(inputs, inputId, label, tooltip=''):
    valueInput = inputs.addValueInput(inputId, label, app.activeProduct.unitsManager.defaultLengthUnits,
                                      adsk.core.ValueInput.createByReal(uiState.getState(inputId)))
    valueInput.tooltip = tooltip
    uiState.registerCommandInput(valueInput)
    return valueInput


def addBool(inputs, inputId, label, tooltip=''):
    boolInput = inputs.addBoolValueInput(inputId, label, True, '', uiState.getState(inputId))
    boolInput.tooltip = tooltip
    uiState.registerCommandInput(boolInput)
    return boolInput


def addGroup(inputs, groupId, label):
    group = inputs.addGroupCommandInput(groupId, label)
    group.isExpanded = uiState.getState(groupId)
    uiState.registerCommandInput(group)
    return group


def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')
    args.command.setDialogInitialSize(400, 500)
    inputs = args.command.commandInputs
    global rebuildBodyToken
    global pendingRebuildBody
    rebuildBodyToken = pendingRebuildBody.entityToken if pendingRebuildBody is not None else None
    rebuildName = pendingRebuildBody.name if pendingRebuildBody is not None else None
    pendingRebuildBody = None
    applyPendingConfig()

    infoGroup = addGroup(inputs, INFO_GROUP, 'Info')
    info = infoText()
    if rebuildName is not None:
        info = f'<b>Rebuilding {html.escape(rebuildName)}</b> in place, features after it in the timeline are kept.<br>' + info
    infoGroup.children.addTextBoxCommandInput("info_text", "Info", info, info.count('<br>') + 4, True)

    sizeGroup = addGroup(inputs, SIZE_GROUP, 'Size')
    addSpinner(sizeGroup.children, GRID_X_INPUT, 'Width (u)', predBoxConfig.MIN_GRID_X, 20, 'Grid cells of 42 mm across, at least 4 like Pred')
    addSpinner(sizeGroup.children, GRID_Y_INPUT, 'Length (u)', predBoxConfig.MIN_GRID_Y, 20, 'Grid cells of 42 mm front to back, at least 3')
    addSpinner(sizeGroup.children, HEIGHT_U_INPUT, 'Height (u)', predBoxConfig.MIN_HEIGHT_U, 30, 'Height units of 7 mm, at least 5; the lid adds 10 mm')
    sizeGroup.children.addTextBoxCommandInput(SIZE_TEXT, 'Box', '', 2, True)

    magnetGroup = addGroup(inputs, MAGNET_GROUP, 'Magnet holes')
    addBool(magnetGroup.children, MAGNETS_INPUT, 'Add magnet holes', 'Holes in the floor pads of every cell, to hold bins with magnets')
    sizeDropdown = magnetGroup.children.addDropDownCommandInput(MAGNET_SIZE_DROPDOWN, 'Magnet size', adsk.core.DropDownStyles.TextListDropDownStyle)
    for name in magnetSizes.BOX_CHOICES:
        sizeDropdown.listItems.add(name, name == uiState.getState(MAGNET_SIZE_DROPDOWN))
    sizeDropdown.tooltip = '6×2 mm magnets need 2.4 mm. 6×3 mm magnets would break through the floor of the box'
    uiState.registerCommandInput(sizeDropdown)
    addLength(magnetGroup.children, MAGNET_DEPTH_INPUT, 'Magnet cutout depth', 'At most 2.6 mm, 0.2 mm of floor stays under the magnet')
    addLength(magnetGroup.children, MAGNET_DIAMETER_INPUT, 'Magnet cutout diameter', '3 to 8.5 mm, the pad around the hole grows with it')

    jointGroup = addGroup(inputs, JOINT_GROUP, 'Joint origins')
    addBool(jointGroup.children, JOINT_ORIGINS_INPUT, 'Add joint origins', 'A joint origin in every cell of the floor, to joint bins into the box')

    inputChangesGroup = addGroup(inputs, INPUT_CHANGES_GROUP, 'Inputs')
    addDefaultsButtonRow(inputChangesGroup.children, INPUT_CHANGES_BUTTONS_BROWSER)
    addButtonRow(inputChangesGroup.children, CONFIG_BUTTONS_BROWSER)

    previewGroup = addGroup(inputs, PREVIEW_GROUP, 'Preview')
    addBool(previewGroup.children, SHOW_PREVIEW_INPUT, 'Show preview (slow)')
    previewGroup.children.addTextBoxCommandInput(PREVIEW_TIME_INPUT, 'Last preview', 'None yet', 1, True)

    updateInputs(inputs)

    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)
    futil.add_handler(args.command.incomingFromHTML, command_incoming_from_html, local_handlers=local_handlers)


def updateInputs(inputs: adsk.core.CommandInputs):
    """Shows the inputs that apply and what the box comes out as"""
    state = getInputsState()
    inputs.itemById(MAGNET_SIZE_DROPDOWN).isEnabled = state.hasMagnets
    inputs.itemById(MAGNET_DEPTH_INPUT).isEnabled = state.hasMagnets and uiState.getState(MAGNET_SIZE_DROPDOWN) == magnetSizes.CUSTOM
    inputs.itemById(MAGNET_DIAMETER_INPUT).isEnabled = state.hasMagnets
    (width, length) = (state.gridX * 42 + 20, state.gridY * 42 + 20)
    height = state.heightU * 7 + 13 + 10
    text = f'{width} x {length} x {height:g} mm with lid'
    problem = boxProblem(state)
    inputs.itemById(SIZE_TEXT).formattedText = text if problem is None else f'{text}<br><span style="color:#d04030">{problem}</span>'


def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    des = adsk.fusion.Design.cast(app.activeProduct)
    wasPart = des is not None and des.designIntent == adsk.fusion.DesignIntentTypes.PartDesignIntentType
    if generateBox(args) is False:
        return
    if wasPart and des.designIntent == adsk.fusion.DesignIntentTypes.HybridDesignIntentType:
        ui.messageBox(designIntent.hybridSwitchMessage('box'), CMD_NAME)


def command_preview(args: adsk.core.CommandEventArgs):
    inputs = args.command.commandInputs
    if inputs.itemById(SHOW_PREVIEW_INPUT).value:
        if INPUTS_VALID:
            startTime = time.perf_counter()
            isGenerated = generateBox(args, mayChangeDocument=False) is not False
            seconds = time.perf_counter() - startTime
            inputs.itemById(PREVIEW_TIME_INPUT).text = f'{seconds:.2f} s' if isGenerated else f'failed after {seconds:.2f} s'
        else:
            args.executeFailed = True
            args.executeFailedMessage = "Some inputs are invalid, unable to generate preview"


def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    if changed_input.id in (PREVIEW_TIME_INPUT, SIZE_TEXT):
        return
    uiState.onInputUpdate(changed_input)
    if changed_input.id == MAGNET_SIZE_DROPDOWN:
        # a size sets the depth field, Custom leaves it to be typed
        depth = magnetSizes.depthForChoice(uiState.getState(MAGNET_SIZE_DROPDOWN))
        if depth is not None:
            uiState.setValue(MAGNET_DEPTH_INPUT, depth)
            uiState.forceUIRefresh()
    if isinstance(changed_input, adsk.core.GroupCommandInput) and changed_input.isExpanded == True:
        for input in changed_input.children:
            uiState.registerCommandInput(input)
        uiState.forceUIRefresh()
    updateInputs(changed_input.parentCommand.commandInputs)


def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    global INPUTS_VALID
    INPUTS_VALID = boxProblem(getInputsState()) is None
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
        uiState.forceUIRefresh()
        updateInputs(command.commandInputs)
        if uiState.getInput(SHOW_PREVIEW_INPUT).value:
            command.doExecutePreview()

    def onLoadConfig(text: str, fileName: str):
        state = readConfig(text, f'Loaded "{fileName}"')
        if state is None:
            return
        applyInputsState(state)
        uiState.forceUIRefresh()
        updateInputs(command.commandInputs)
        if uiState.getInput(SHOW_PREVIEW_INPUT).value:
            command.doExecutePreview()

    if args.browserCommandInput.id == INPUT_CHANGES_BUTTONS_BROWSER:
        browserPages.handleMessage(args, defaultsButtonsHandlers(onDefaults))
    elif args.browserCommandInput.id == CONFIG_BUTTONS_BROWSER:
        browserPages.handleMessage(args, configButtons.configButtonsHandlers(
            'box',
            lambda: configJson.configText(configJson.GENERATOR_BOX, configJson.stateToJson(configJson.GENERATOR_BOX, getInputsState()), tagUtils.getGeneratorVersion()),
            lambda: boxName(getInputsState()),
            onLoad=onLoadConfig,
        ))


def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    global rebuildBodyToken
    local_handlers = []
    rebuildBodyToken = None
    if args.terminationReason == adsk.core.CommandTerminationReason.CompletedTerminationReason and len(rebuildNotes) > 0:
        ui.messageBox(
            'The box was rebuilt. These features after it need a look, ones using a face or an edge of the old '
            'box need them picked again:\n\n' + '\n'.join(rebuildNotes),
            CMD_NAME,
            adsk.core.MessageBoxButtonTypes.OKButtonType,
            adsk.core.MessageBoxIconTypes.WarningIconType,
        )


def snapshotSettings(inputs: adsk.core.CommandInputs) -> list[dict]:
    return settingsUtils.snapshotInputs(inputs, [INFO_GROUP, INPUT_CHANGES_GROUP, PREVIEW_GROUP], SETTINGS_TITLE)


def generateBox(args: adsk.core.CommandEventArgs, mayChangeDocument: bool = True):
    startTime = time.perf_counter()
    settings = snapshotSettings(args.command.commandInputs)
    commonUtils.fileLog(f'{CMD_NAME} Generating box with settings:\n{settingsUtils.settingsText(settings)}')
    state = getInputsState()
    global rebuildNotes
    rebuildNotes = []
    try:
        des = adsk.fusion.Design.cast(app.activeProduct)
        if rebuildBodyToken is not None:
            body = rebuildUtils.findBodyByToken(des, rebuildBodyToken)
            (_, rebuildNotes) = rebuildBox(des, body, state, settings, not mayChangeDocument)
        else:
            buildBox(des, state, settings, mayChangeDocument)
        futil.log(f'{CMD_NAME} {boxName(state)} generated in {time.perf_counter() - startTime:.3f}s')
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
    for group in (INFO_GROUP, SIZE_GROUP, MAGNET_GROUP, JOINT_GROUP, INPUT_CHANGES_GROUP, PREVIEW_GROUP):
        uiState.initValue(group, True, adsk.core.GroupCommandInput.classType())
    spinner = adsk.core.IntegerSpinnerCommandInput.classType()
    value = adsk.core.ValueCommandInput.classType()
    boolean = adsk.core.BoolValueCommandInput.classType()
    dropdown = adsk.core.DropDownCommandInput.classType()
    uiState.initValue(GRID_X_INPUT, DEFAULT_STATE.gridX, spinner)
    uiState.initValue(GRID_Y_INPUT, DEFAULT_STATE.gridY, spinner)
    uiState.initValue(HEIGHT_U_INPUT, DEFAULT_STATE.heightU, spinner)
    uiState.initValue(MAGNETS_INPUT, DEFAULT_STATE.hasMagnets, boolean)
    uiState.initValue(MAGNET_SIZE_DROPDOWN, magnetSizes.choiceForDepth(DEFAULT_STATE.magnetDepth, magnetSizes.BOX_CHOICES), dropdown)
    uiState.initValue(MAGNET_DEPTH_INPUT, DEFAULT_STATE.magnetDepth, value)
    uiState.initValue(MAGNET_DIAMETER_INPUT, DEFAULT_STATE.magnetDiameter, value)
    uiState.initValue(JOINT_ORIGINS_INPUT, DEFAULT_STATE.hasJointOrigins, boolean)
    uiState.initValue(SHOW_PREVIEW_INPUT, False, boolean)
    recordedDefaults = configUtils.readJsonConfig(UI_INPUT_DEFAULTS_CONFIG_PATH)
    if recordedDefaults:
        try:
            uiState.initValues(recordedDefaults)
        except Exception as err:
            futil.log(f'{CMD_NAME} Failed to restore default values, err: {err}')


def saveUIInputsAsDefaults():
    configUtils.dumpJsonConfig(UI_INPUT_DEFAULTS_CONFIG_PATH, uiState.toDict())


def getInputsState() -> InputState:
    return InputState(
        gridX=int(uiState.getState(GRID_X_INPUT)),
        gridY=int(uiState.getState(GRID_Y_INPUT)),
        heightU=int(uiState.getState(HEIGHT_U_INPUT)),
        hasMagnets=uiState.getState(MAGNETS_INPUT),
        magnetDepth=uiState.getState(MAGNET_DEPTH_INPUT),
        magnetDiameter=uiState.getState(MAGNET_DIAMETER_INPUT),
        hasJointOrigins=uiState.getState(JOINT_ORIGINS_INPUT),
    )


def applyInputsState(state: InputState):
    # a size read back from a parameter comes as a float
    uiState.setValue(GRID_X_INPUT, int(round(state.gridX)))
    uiState.setValue(GRID_Y_INPUT, int(round(state.gridY)))
    uiState.setValue(HEIGHT_U_INPUT, int(round(state.heightU)))
    uiState.setValue(MAGNETS_INPUT, state.hasMagnets)
    # only the depth is saved, the size shown is read back from it (p263)
    uiState.setValue(MAGNET_SIZE_DROPDOWN, magnetSizes.choiceForDepth(state.magnetDepth, magnetSizes.BOX_CHOICES))
    uiState.setValue(MAGNET_DEPTH_INPUT, state.magnetDepth)
    uiState.setValue(MAGNET_DIAMETER_INPUT, state.magnetDiameter)
    uiState.setValue(JOINT_ORIGINS_INPUT, state.hasJointOrigins)


def readConfig(text: str, source: str) -> InputState | None:
    return configButtons.readConfig(text, source, configJson.GENERATOR_BOX, InputState, getInputsState(), {})


def configFileName(settings: dict) -> str:
    defaults = configJson.stateToJson(configJson.GENERATOR_BOX, DEFAULT_STATE)
    known = {name: value for (name, value) in settings.items() if name in defaults}
    return boxName(configJson.stateFromJson(configJson.GENERATOR_BOX, InputState, {**defaults, **known}))


def startWithConfig(settings: dict):
    """Opens the dialog with a config by field name, see configJson.stateToJson, settings it doesn't have stay"""
    global pendingConfig
    global pendingRebuildBody
    pendingConfig = settings
    if not ui.commandDefinitions.itemById(CMD_ID).execute():
        pendingConfig = None
        pendingRebuildBody = None


def startRebuild(body: adsk.fusion.BRepBody, tag: dict):
    """Opens the dialog with the settings of the box the body (box or lid) is of, its size parameters may have been
    changed since and replace the settings, see boxBuilder.rebuildBox"""
    global pendingRebuildBody
    design = adsk.fusion.Design.cast(app.activeProduct)
    settings = rebuildUtils.configWithParameters(configJson.GENERATOR_BOX, tag['config'], tag.get('parameters'),
                                                 design.userParameters.itemByName, predBoxConfig.PARAMETER_FIELDS)
    pendingRebuildBody = body
    startWithConfig(settings)


def applyPendingConfig():
    global pendingConfig
    if pendingConfig is None:
        return
    state = readConfig(configJson.configText(configJson.GENERATOR_BOX, pendingConfig), 'Rebuilding' if rebuildBodyToken is not None else 'Cloned')
    pendingConfig = None
    if state is not None:
        applyInputsState(state)
