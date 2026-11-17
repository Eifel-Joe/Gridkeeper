import adsk.core, adsk.fusion, traceback
import html
import os
import time

from ...lib.gridfinityUtils import designIntent
from ...lib import configUtils
from ...lib import tagUtils
from ...lib import fusion360utils as futil
from ... import config
from ...lib.gridfinityUtils import commonUtils
from ...lib.gridfinityUtils import labelColors
from ...lib.gridfinityUtils import predBoxLabel
from ...lib.gridfinityUtils import predBoxLabelLayout
from ...lib.gridfinityUtils import predBoxSeats
from ...lib.gridfinityUtils import textStyles
from .inputState import InputState
from .boxLabelBuilder import buildBoxLabel, boxCells, isBoxLabelJointOrigin, labelLayout, labelName, labelProblem, ICONS_FOLDER
from ...lib.ui.commandUiState import CommandUiState
from ...lib.ui.defaultsButtons import addDefaultsButtonRow, defaultsButtonsHandlers, DEFAULTS_SAVE, DEFAULTS_FACTORY_RESET
from ...lib.ui import browserPages
from ...lib.ui.unsupportedDesignTypeException import UnsupportedDesignTypeException

# Dialog of the box label command (round 29, p262, dev-notes/r29/boxlabel-plan.md): the label of the storage box after
# Pred's parametric Gridfinity Storage Box v1.1 (https://www.printables.com/model/543553, CC BY-NC, by Pred), Gridkeeper
# text and Cullenect symbols (https://github.com/CullenJWebb/Cullenect-Labels, MIT, by CullenJWebb). A command of its
# own (Jörg 17.11.2026: "Letzteres wäre mir gut recht, weil man es so besser auch mal austauschen könnte.")

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdBoxLabel'
CMD_NAME = 'Gridkeeper box label'
CMD_Description = ("Creates the label for the label holder of a Gridkeeper box after Pred's storage box.\n\n"
    'A large text at the left, two lines and up to five Cullenect symbols at the right, raised, set in or flush. Pick '
    'the label joint origin of a box and the label is jointed into its holder.')

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
BOX_GROUP = 'box_group'
TEXT_GROUP = 'text_group'
SYMBOL_GROUP = 'symbol_group'
INPUT_CHANGES_GROUP = 'input_changes_group'
PREVIEW_GROUP = 'preview_group'
BOX_INPUT = 'box'
WIDTH_DROPDOWN = 'label_width'
SIZE_TEXT = 'size_text'
BIG_TEXT_INPUT = 'big_text'
LINE_1_INPUT = 'text_line_1'
LINE_2_INPUT = 'text_line_2'
TEXT_STYLE_DROPDOWN = 'text_style'
SURFACE_DROPDOWN = 'surface_dropdown'
TEXT_COLOR_DROPDOWN = 'text_color'
CUSTOM_COLOR_INPUT = 'text_color_custom'
SYMBOL_DROPDOWNS = [f'symbol_{index + 1}' for index in range(predBoxLabelLayout.MAX_SYMBOLS)]
SYMBOL_TEXT = 'symbol_text'
INPUT_CHANGES_BUTTONS_BROWSER = 'input_changes_buttons'
SHOW_PREVIEW_INPUT = 'show_preview'
PREVIEW_TIME_INPUT = 'preview_time'

assert len(SYMBOL_DROPDOWNS) == predBoxLabelLayout.MAX_SYMBOLS

SURFACE_NAMES = {
    predBoxLabel.SURFACE_EMBOSSED: 'Raised',
    predBoxLabel.SURFACE_DEBOSSED: 'Set in',
    predBoxLabel.SURFACE_FLUSH: 'Flush',
}

INFO_TEXT = ("<b>Help:</b> every input is explained "
             "<a href=\"https://eifel-joe.github.io/Gridkeeper/boxes/\">in the Gridkeeper documentation</a>. "
             "The label slides into the holder of a box after Pred's Gridfinity Storage Box v1.1, "
             "<a href=\"https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric\">Printables 543553</a> (CC BY-NC). "
             "Symbols from Cullenect labels by CullenJWebb, "
             "<a href=\"https://github.com/CullenJWebb/Cullenect-Labels\">Cullenect-Labels</a> (MIT).")

INPUTS_VALID = True


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


def symbolNames() -> list[str]:
    return [name for (name, _) in predBoxLabelLayout.symbolChoices(ICONS_FOLDER)]


def addGroup(inputs, groupId, label):
    group = inputs.addGroupCommandInput(groupId, label)
    group.isExpanded = uiState.getState(groupId)
    uiState.registerCommandInput(group)
    return group


def addDropdown(inputs, inputId, label, names):
    """The remembered choice, or the first one when it isn't offered any more (saved defaults of an older version)"""
    selected = uiState.getState(inputId)
    if selected not in names and len(names) > 0:
        selected = names[0]
        uiState.updateValue(inputId, selected)
    dropdown = inputs.addDropDownCommandInput(inputId, label, adsk.core.DropDownStyles.TextListDropDownStyle)
    for name in names:
        dropdown.listItems.add(name, name == selected)
    uiState.registerCommandInput(dropdown)
    return dropdown


def addString(inputs, inputId, label, tooltip=''):
    stringInput = inputs.addStringValueInput(inputId, label, uiState.getState(inputId))
    stringInput.tooltip = tooltip
    uiState.registerCommandInput(stringInput)
    return stringInput


def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')
    args.command.setDialogInitialSize(400, 500)
    inputs = args.command.commandInputs

    infoGroup = addGroup(inputs, INFO_GROUP, 'Info')
    info = infoText()
    infoGroup.children.addTextBoxCommandInput("info_text", "Info", info, info.count('<br>') + 4, True)

    boxGroup = addGroup(inputs, BOX_GROUP, 'Box')
    boxInput = boxGroup.children.addSelectionInput(BOX_INPUT, 'Box', f'The {predBoxSeats.LABEL_JOINT_ORIGIN} of a box, the label is jointed into its holder')
    boxInput.addSelectionFilter(adsk.core.SelectionCommandInput.JointOrigins)
    boxInput.setSelectionLimits(0, 1)
    boxInput.tooltip = (f'Optional: pick the {predBoxSeats.LABEL_JOINT_ORIGIN} at the front of a box, the label takes '
                        "the box's width and goes into the holder. Without, it lies beside the parts there are")
    # Jörg 17.11.2026: "Da das Schild ja feste Breiten hat, sollte es nur ein Auswahlmenü dafür geben. Nicht frei
    # einstellbar." Works without a box in the document, for a reprint
    addDropdown(boxGroup.children, WIDTH_DROPDOWN, 'Label width', [name for name, _ in predBoxLabelLayout.widthChoices()]).tooltip =         "Pred's label widths by the width of the box; a picked box sets its own"
    boxGroup.children.addTextBoxCommandInput(SIZE_TEXT, 'Label', '', 2, True)

    textGroup = addGroup(inputs, TEXT_GROUP, 'Text')
    addString(textGroup.children, BIG_TEXT_INPUT, 'Large text', 'In large letters at the left, e.g. M3; empty leaves the room to the lines')
    addString(textGroup.children, LINE_1_INPUT, 'Line 1')
    addString(textGroup.children, LINE_2_INPUT, 'Line 2')
    addDropdown(textGroup.children, TEXT_STYLE_DROPDOWN, 'Text style', textStyles.STYLES).tooltip = \
        'Heavy is Arial Black, its strokes print with a 0.4 mm nozzle. Regular and Bold are Arial, thin when small'
    addDropdown(textGroup.children, SURFACE_DROPDOWN, 'Text and symbols', list(SURFACE_NAMES.values())).tooltip = \
        "Raised 0.4 mm like Pred's labels, or set 0.4 mm in, as bodies of their own to print in another colour. Set in keeps them hidden, flush shows them"
    addDropdown(textGroup.children, TEXT_COLOR_DROPDOWN, 'Text color', labelColors.CHOICES).tooltip = \
        'Gives the text and symbol bodies this color, for printing them in another filament'
    addString(textGroup.children, CUSTOM_COLOR_INPUT, 'Custom color', '#rrggbb, e.g. #D02020')

    symbolGroup = addGroup(inputs, SYMBOL_GROUP, 'Symbols')
    names = symbolNames()
    for (index, inputId) in enumerate(SYMBOL_DROPDOWNS):
        addDropdown(symbolGroup.children, inputId, f'Symbol {index + 1}', names).tooltip = \
            'Under the lines, from the left; the ones the width has no room for are left out from the right'
    symbolGroup.children.addTextBoxCommandInput(SYMBOL_TEXT, 'Symbols', '', 1, True)

    inputChangesGroup = addGroup(inputs, INPUT_CHANGES_GROUP, 'Inputs')
    addDefaultsButtonRow(inputChangesGroup.children, INPUT_CHANGES_BUTTONS_BROWSER)

    previewGroup = addGroup(inputs, PREVIEW_GROUP, 'Preview')
    showPreview = previewGroup.children.addBoolValueInput(SHOW_PREVIEW_INPUT, 'Show preview (slow)', True, '', uiState.getState(SHOW_PREVIEW_INPUT))
    uiState.registerCommandInput(showPreview)
    previewGroup.children.addTextBoxCommandInput(PREVIEW_TIME_INPUT, 'Last preview', 'None yet', 1, True)

    updateInputs(inputs)

    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)
    futil.add_handler(args.command.select, command_select, local_handlers=local_handlers)
    futil.add_handler(args.command.incomingFromHTML, command_incoming_from_html, local_handlers=local_handlers)


def selectedBox(inputs: adsk.core.CommandInputs) -> adsk.fusion.JointOrigin | None:
    boxInput = adsk.core.SelectionCommandInput.cast(inputs.itemById(BOX_INPUT))
    if boxInput is None or boxInput.selectionCount == 0:
        return None
    return adsk.fusion.JointOrigin.cast(boxInput.selection(0).entity)


def boxProblem(inputs: adsk.core.CommandInputs, state: InputState) -> str | None:
    """A picked box whose width isn't the chosen one, the label wouldn't fit its holder"""
    box = selectedBox(inputs) if inputs is not None else None
    cells = boxCells(box) if box is not None else None
    if cells is not None and predBoxLabelLayout.widthChoiceFor(cells) != predBoxLabelLayout.widthChoiceFor(state.cells):
        return f'The picked box takes the label width {predBoxLabelLayout.widthChoiceFor(cells)}'
    return None


def updateInputs(inputs: adsk.core.CommandInputs):
    """Shows the inputs that apply and what the label comes out as"""
    state = getInputsState(inputs)
    inputs.itemById(CUSTOM_COLOR_INPUT).isVisible = uiState.getState(TEXT_COLOR_DROPDOWN) == labelColors.CUSTOM_CHOICE
    width = predBoxLabelLayout.plateWidth(state.cells) * 10
    text = f'Plate {width:g} x {predBoxLabelLayout.PLATE_HEIGHT * 10:g} mm'
    problem = labelProblem(state) or boxProblem(inputs, state)
    inputs.itemById(SIZE_TEXT).formattedText = text if problem is None else f'{text}<br><span style="color:#d04030">{html.escape(problem)}</span>'
    layout = labelLayout(state)
    chosen = sum(1 for name in state.symbols if name != predBoxLabelLayout.NO_SYMBOL)
    symbolText = f'{chosen} chosen'
    if layout is not None and layout.dropped > 0:
        symbolText += f', {layout.dropped} left out for want of room'
    inputs.itemById(SYMBOL_TEXT).text = symbolText


def command_select(args: adsk.core.SelectionEventArgs):
    """Only the label joint origin of a box can be picked"""
    if args.activeInput is None or args.activeInput.id != BOX_INPUT:
        return
    args.isSelectable = isBoxLabelJointOrigin(adsk.fusion.JointOrigin.cast(args.selection.entity))


def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    des = adsk.fusion.Design.cast(app.activeProduct)
    wasPart = des is not None and des.designIntent == adsk.fusion.DesignIntentTypes.PartDesignIntentType
    if generateBoxLabel(args) is False:
        return
    if wasPart and des.designIntent == adsk.fusion.DesignIntentTypes.HybridDesignIntentType:
        ui.messageBox(designIntent.hybridSwitchMessage('box label'), CMD_NAME)
    # text fitted so small that a 0.4 mm nozzle leaves parts out (p130), as the inserts
    hint = textStyles.hintText(textStyles.notes(), suggestHeavy=getInputsState(args.command.commandInputs).textStyle != textStyles.STYLE_HEAVY)
    if hint is not None:
        ui.messageBox(hint, CMD_NAME)


def command_preview(args: adsk.core.CommandEventArgs):
    inputs = args.command.commandInputs
    if inputs.itemById(SHOW_PREVIEW_INPUT).value:
        if INPUTS_VALID:
            startTime = time.perf_counter()
            isGenerated = generateBoxLabel(args, mayChangeDocument=False) is not False
            seconds = time.perf_counter() - startTime
            inputs.itemById(PREVIEW_TIME_INPUT).text = f'{seconds:.2f} s{textStyles.previewNote(textStyles.notes())}' if isGenerated else f'failed after {seconds:.2f} s'
        else:
            args.executeFailed = True
            args.executeFailedMessage = "Some inputs are invalid, unable to generate preview"


def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    if changed_input.id in (PREVIEW_TIME_INPUT, SIZE_TEXT, SYMBOL_TEXT):
        return
    uiState.onInputUpdate(changed_input)
    if changed_input.id == BOX_INPUT:
        # Jörg: "Aber es kann natürlich auch eine Breite übernommen werden, wenn man einen Joint auswählt zum positionieren."
        box = selectedBox(changed_input.parentCommand.commandInputs)
        cells = boxCells(box) if box is not None else None
        if cells is not None:
            uiState.setValue(WIDTH_DROPDOWN, predBoxLabelLayout.widthChoiceFor(cells))
            uiState.forceUIRefresh()
    if isinstance(changed_input, adsk.core.GroupCommandInput) and changed_input.isExpanded == True:
        for input in changed_input.children:
            uiState.registerCommandInput(input)
        uiState.forceUIRefresh()
    updateInputs(changed_input.parentCommand.commandInputs)


def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    global INPUTS_VALID
    state = getInputsState(args.inputs)
    INPUTS_VALID = labelProblem(state) is None and boxProblem(args.inputs, state) is None
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

    if args.browserCommandInput.id == INPUT_CHANGES_BUTTONS_BROWSER:
        browserPages.handleMessage(args, defaultsButtonsHandlers(onDefaults))


def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []


def generateBoxLabel(args: adsk.core.CommandEventArgs, mayChangeDocument: bool = True):
    startTime = time.perf_counter()
    inputs = args.command.commandInputs
    state = getInputsState(inputs)
    commonUtils.fileLog(f'{CMD_NAME} Generating box label {state}')
    # notes of an earlier build, a preview or a failed one, are not this one's
    textStyles.clearNotes()
    try:
        des = adsk.fusion.Design.cast(app.activeProduct)
        buildBoxLabel(des, state, mayChangeDocument, selectedBox(inputs))
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
    for group in (INFO_GROUP, BOX_GROUP, TEXT_GROUP, SYMBOL_GROUP, INPUT_CHANGES_GROUP, PREVIEW_GROUP):
        uiState.initValue(group, True, adsk.core.GroupCommandInput.classType())
    dropdown = adsk.core.DropDownCommandInput.classType()
    string = adsk.core.StringValueCommandInput.classType()
    uiState.initValue(WIDTH_DROPDOWN, predBoxLabelLayout.widthChoiceFor(predBoxLabelLayout.DEFAULT_CELLS), dropdown)
    uiState.initValue(BIG_TEXT_INPUT, 'M3', string)
    uiState.initValue(LINE_1_INPUT, 'Socket head', string)
    uiState.initValue(LINE_2_INPUT, 'DIN 912', string)
    uiState.initValue(TEXT_STYLE_DROPDOWN, textStyles.DEFAULT_INSERT_STYLE, dropdown)
    uiState.initValue(SURFACE_DROPDOWN, SURFACE_NAMES[predBoxLabel.SURFACE_EMBOSSED], dropdown)
    uiState.initValue(TEXT_COLOR_DROPDOWN, labelColors.NO_COLOR_CHOICE, dropdown)
    uiState.initValue(CUSTOM_COLOR_INPUT, '', string)
    for (index, inputId) in enumerate(SYMBOL_DROPDOWNS):
        uiState.initValue(inputId, 'Socket Hex' if index == 0 else predBoxLabelLayout.NO_SYMBOL, dropdown)
    uiState.initValue(SHOW_PREVIEW_INPUT, False, adsk.core.BoolValueCommandInput.classType())
    recordedDefaults = configUtils.readJsonConfig(UI_INPUT_DEFAULTS_CONFIG_PATH)
    if recordedDefaults:
        try:
            uiState.initValues(recordedDefaults)
        except Exception as err:
            futil.log(f'{CMD_NAME} Failed to restore default values, err: {err}')


def saveUIInputsAsDefaults():
    configUtils.dumpJsonConfig(UI_INPUT_DEFAULTS_CONFIG_PATH, uiState.toDict())


def getInputsState(inputs: adsk.core.CommandInputs | None = None) -> InputState:
    surfaceName = uiState.getState(SURFACE_DROPDOWN)
    return InputState(
        cells=predBoxLabelLayout.cellsOfChoice(uiState.getState(WIDTH_DROPDOWN)),
        bigText=uiState.getState(BIG_TEXT_INPUT),
        line1=uiState.getState(LINE_1_INPUT),
        line2=uiState.getState(LINE_2_INPUT),
        symbols=[uiState.getState(inputId) for inputId in SYMBOL_DROPDOWNS],
        textStyle=uiState.getState(TEXT_STYLE_DROPDOWN),
        surface=next((key for (key, name) in SURFACE_NAMES.items() if name == surfaceName), predBoxLabel.SURFACE_EMBOSSED),
        textColor=labelColors.dialogColor(uiState.getState(TEXT_COLOR_DROPDOWN), uiState.getState(CUSTOM_COLOR_INPUT)),
    )
