import adsk.core, adsk.fusion
import dataclasses
import math
import os
import re

from ...lib import tagUtils
from ...lib import labelFaces
from ...lib import threeMf
from ...lib import stlFile
from ...lib import exportParts
from ...lib import printLayout
from ...lib import configUtils
from ...lib import fusion360utils as futil
from ...lib.ui import expressionFormat
from ...lib.gridfinityUtils import labelGenerator
from ...lib.gridfinityUtils import labelColors
from ... import config
from ..commandCreateBaseplate import printBeds

# Upstream's export of bins and baseplates (Le0Michine, 4b2f167, round 17.11.2026), for every part our generators make
# (p300): which tags are parts is exportParts.EXPORT_TAGS, and the colored text and symbol bodies in a part's Text
# component (p86, p90) go into the part's mesh and file, painted for the slicer in the 3MF

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdExport'
CMD_NAME = 'Gridkeeper export'
CMD_Description = 'Export bins, baseplates, Cullenect inserts and boxes for printing, 3MF with the label text in a color of its own, or STL and STEP files'
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')
# in the context menu after Fusion's Save As Mesh
SAVE_AS_MESH_COMMAND_ID = 'FusionSaveAsSTLCommand'

ALL_INPUT_ID = 'export_all'
SELECTION_INPUT_ID = 'export_bodies'
FORMAT_INPUT_ID = 'export_format'
PAINT_INPUT_ID = 'export_paint_labels'
# round 37 (p301): a filament input for each label color of the parts, its id ends in the color or 'none'
FILAMENTS_GROUP_ID = 'export_filaments_group'
FILAMENT_INPUT_PREFIX = 'export_filament_'
FOLDER_INPUT_ID = 'export_folder'
BROWSE_INPUT_ID = 'export_browse'
FILE_NAME_INPUT_ID = 'export_file_name'
SUMMARY_INPUT_ID = 'export_summary'
# round r29-export: the bed the 3MF's parts are laid out on, their spacing and the purge tower's corner
BED_GROUP_ID = 'export_bed_group'
BED_INPUT_ID = 'export_bed'
BED_WIDTH_INPUT_ID = 'export_bed_width'
BED_LENGTH_INPUT_ID = 'export_bed_length'
SPACING_INPUT_ID = 'export_spacing'
PURGE_INPUT_ID = 'export_purge'

FORMAT_3MF = '3MF'
FORMAT_STL = 'STL'
FORMAT_STEP = 'STEP'
FORMATS = [FORMAT_3MF, FORMAT_STL, FORMAT_STEP]
FORMAT_EXTENSIONS = {FORMAT_3MF: '3mf', FORMAT_STL: 'stl', FORMAT_STEP: 'step'}
# files named in the question whether to replace them, the rest counted
MAX_LISTED_FILES = 8
# the 3MF file of more than one body
DEFAULT_FILE_NAME = 'Gridkeeper parts'
# the 3MF and STL meshes, finer than the STL export's high refinement, which the calculator can't be set to
MESH_QUALITY = adsk.fusion.TriangleMeshQualityOptions.VeryHighQualityTriangleMesh
# cm, a mesh triangle this close to the plane of a letter face can lie on it
PAINT_TOLERANCE = 1e-4

# the dialog's last choices, kept for the next time Fusion runs
CONFIG_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'commandConfig')
CONFIG_SECTION = 'Export'

# the folder chosen in the dialog open now, and whether its file name was typed or still follows the bodies
dialogFolder = ''
isFileNameTyped = False
# a preset setting the bed size, so the size inputs' change doesn't turn the dropdown to Custom
isApplyingBedPreset = False
# the filaments of the label colors, saved ones and those changed in the dialog open now, kept when the selection
# changes; a color's input shows these or one assigned anew, see exportParts.assignFilaments (round 37, p301)
dialogFilaments: dict[str, int] = {}
# the filament each input was made with, to tell a number typed in from one assigned (round 37)
dialogAssigned: dict[str, int] = {}

local_handlers = []
markingMenuHandler = None
# starting a command can clear the selection, so what was selected when the menu opened is kept
menuEntities = []

@dataclasses.dataclass
class ExportItem:
    # native, the occurrence places it
    body: adsk.fusion.BRepBody
    occurrence: adsk.fusion.Occurrence | None
    # the colored text and symbol bodies of the part, in its Text component, each placed by its occurrence (p300)
    markings: list['ExportItem'] = dataclasses.field(default_factory=list)

    @property
    def hasOutlineLabels(self) -> bool:
        """
        Bins built before the label styles had outline labels only. A colored outline label has letter bodies of its
        own, they're the markings, see labelColors.paintsOutlineLetterFaces
        """
        tag = tagUtils.readBodyTag(self.body)
        if tag is None or tag[0] != tagUtils.TAG_BIN:
            return False
        settings = tag[1].get('config')
        style = settings.get('labelStyle', labelGenerator.LABEL_STYLE_OUTLINE) if isinstance(settings, dict) else labelGenerator.LABEL_STYLE_OUTLINE
        color = settings.get('labelColor', '') if isinstance(settings, dict) else ''
        return labelColors.paintsOutlineLetterFaces(True, style == labelGenerator.LABEL_STYLE_OUTLINE, color)

    @property
    def labelColor(self) -> str:
        """
        A text or symbol body's color, by the appearance the generators give its Text occurrence, or the body in the
        root (appearanceUtils.colorPart), '' for none, see labelColors.colorOfAppearanceName (round 37, p301)
        """
        for holder in (self.occurrence, self.body):
            appearance = holder.appearance if holder is not None else None
            color = labelColors.colorOfAppearanceName(appearance.name if appearance is not None else None)
            if color:
                return color
        return ''

def labelColorsOf(items: list[ExportItem]) -> list[str]:
    """The label colors of the parts, each once in the order found, '' for outline letters and text without a color"""
    return exportParts.distinctLabelColors(
        [([''] if item.hasOutlineLabels else []) + [marking.labelColor for marking in item.markings] for item in items])

def start():
    global markingMenuHandler
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    futil.add_handler(cmd_def.commandCreated, command_created)
    markingMenuHandler = futil.add_handler(ui.markingMenuDisplaying, marking_menu_displaying, local_handlers=local_handlers)

def stop():
    global markingMenuHandler
    if markingMenuHandler is not None:
        ui.markingMenuDisplaying.remove(markingMenuHandler)
        markingMenuHandler = None
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    if command_definition:
        command_definition.deleteMe()

def selectionEntities(selected: list) -> list:
    """A face stands for its body"""
    entities = []
    for entity in selected:
        face = adsk.fusion.BRepFace.cast(entity)
        entity = face.body if face is not None else entity
        if entity not in entities:
            entities.append(entity)
    return entities

def occurrenceOf(component: adsk.fusion.Component) -> adsk.fusion.Occurrence | None:
    """The first place of a component, for a native body, as the settings menu finds it (commandShowSettings)"""
    design = adsk.fusion.Design.cast(app.activeProduct)
    occurrences = design.rootComponent.allOccurrencesByComponent(component) if design is not None else None
    return occurrences.item(0) if occurrences is not None and occurrences.count > 0 else None

def isRootComponent(component: adsk.fusion.Component) -> bool:
    design = adsk.fusion.Design.cast(app.activeProduct)
    return design is not None and component == design.rootComponent

def isTextComponent(component: adsk.fusion.Component) -> bool:
    """A part's Text component, never the root, which is named after the document, see exportParts.isTextComponentName"""
    return exportParts.isTextComponentName(component.name, isRootComponent(component))

def partRoleOf(component: adsk.fusion.Component) -> str | None:
    """The role a component has in a box set (Box, Lid, Latch, ...), None outside one"""
    attribute = component.attributes.itemByName(tagUtils.TAG_GROUP, tagUtils.TAG_PART_ROLE)
    return attribute.value if attribute is not None else None

def isPartBody(body: adsk.fusion.BRepBody) -> bool:
    """A part the export takes, see exportParts.isPartBody, the body where it's placed or its native one"""
    native = body.nativeObject if body.assemblyContext is not None else body
    tag = tagUtils.readExportTag(native)
    component = native.parentComponent
    return exportParts.isPartBody(tag[0] if tag is not None else None, component.name, isRootComponent(component), partRoleOf(component))

def placedPart(body: adsk.fusion.BRepBody) -> adsk.fusion.BRepBody | None:
    """
    The part a body belongs to, where it's placed: itself, or for a letter or symbol in a Text component the part one
    level up, as tagUtils.partTag finds it (the letters of an insert are tagged too, they still aren't a part). None for
    any other body
    """
    native = body.nativeObject if body.assemblyContext is not None else body
    if not isTextComponent(native.parentComponent):
        return body if isPartBody(body) else None
    textOccurrence = body.assemblyContext if body.assemblyContext is not None else occurrenceOf(native.parentComponent)
    partOccurrence = textOccurrence.assemblyContext if textOccurrence is not None else None
    if partOccurrence is None:
        return None
    return next((partBody for partBody in partOccurrence.bRepBodies if isPartBody(partBody)), None)

def markingsOf(part: adsk.fusion.BRepBody) -> list[ExportItem]:
    """
    The visible bodies of the part's Text components, where they're placed. A part in the root, built without a
    component, has no Text component to find them in
    """
    occurrence = part.assemblyContext
    if occurrence is None:
        return []
    markings = []
    for child in occurrence.childOccurrences:
        if not isTextComponent(child.component):
            continue
        markings += [ExportItem(body.nativeObject, child) for body in child.bRepBodies if body.isVisible]
    return markings

def isTagged(entity) -> bool:
    """
    A part or a letter of one, or an occurrence or component with a part among its bodies or those of the occurrences
    in it, our containers Grid, Bins and Label too. The browser's root is a component, the others are occurrences
    """
    body = adsk.fusion.BRepBody.cast(entity)
    if body is not None:
        return placedPart(body) is not None
    occurrence = adsk.fusion.Occurrence.cast(entity)
    if occurrence is not None:
        return isTagged(occurrence.component)
    component = adsk.fusion.Component.cast(entity)
    if component is None:
        return False
    return any(placedPart(body) is not None for body in component.bRepBodies) \
        or any(isTagged(child.component) for child in component.occurrences)

def isGridfinityBody(body: adsk.fusion.BRepBody) -> bool:
    """A visible part, the body where it's placed or its native one, its letters come with it"""
    return body.isVisible and isPartBody(body)

def occurrenceBodies(occurrence: adsk.fusion.Occurrence) -> list[adsk.fusion.BRepBody]:
    """Its visible parts and those of the occurrences in it, where they're placed. A Text occurrence stands for its part"""
    return exportParts.partBodiesUnder(
        occurrence,
        isText=lambda current: isTextComponent(current.component),
        parentOf=lambda current: current.assemblyContext,
        childrenOf=lambda current: list(current.childOccurrences),
        bodiesOf=lambda current: list(current.bRepBodies),
        isPart=isGridfinityBody,
    )

def menuSelection(design: adsk.fusion.Design) -> list[adsk.fusion.BRepBody]:
    """
    The bodies the dialog starts with selected, the visible parts of a component or occurrence in its
    place, so the selection counts bodies only. Bodies picked themselves stay, whatever they are
    """
    bodies = []
    for entity in menuEntities:
        if not entity.isValid:
            continue
        body = adsk.fusion.BRepBody.cast(entity)
        occurrence = adsk.fusion.Occurrence.cast(entity)
        component = adsk.fusion.Component.cast(entity)
        if body is not None:
            bodies.append(body)
        elif occurrence is not None:
            bodies += occurrenceBodies(occurrence)
        elif component is not None and design is not None:
            for placed in design.rootComponent.allOccurrencesByComponent(component):
                bodies += occurrenceBodies(placed)
    return bodies

def isRootSelected(design: adsk.fusion.Design) -> bool:
    return design is not None and any(entity.isValid and entity == design.rootComponent for entity in menuEntities)

def marking_menu_displaying(args: adsk.core.MarkingMenuEventArgs):
    """After Save As Mesh, or last, when anything selected is a bin or baseplate or holds one"""
    global menuEntities
    try:
        menuEntities = selectionEntities(args.selectedEntities or [])
        if not any(isTagged(entity) for entity in menuEntities):
            return
        controls = args.linearMarkingMenu.controls
        commandDefinition = ui.commandDefinitions.itemById(CMD_ID)
        saveAsMesh = controls.itemById(SAVE_AS_MESH_COMMAND_ID)
        if saveAsMesh is None:
            # a menu without Save As Mesh
            controls.addCommand(commandDefinition)
            return
        control = controls.addCommand(commandDefinition, SAVE_AS_MESH_COMMAND_ID, False)
        if not saveAsMesh.isVisible:
            # the menu of a face keeps Save As Mesh hidden and the separator before it too, which would join the export
            # to Properties above
            controls.addSeparator('', control.id, True)
    except Exception as err:
        futil.log(f'{CMD_NAME} context menu failed, {err}')

def readChoices() -> dict:
    """The dialog's last choices, the Downloads folder the first time"""
    addinConfig = configUtils.readConfig(CONFIG_FOLDER_PATH)
    section = addinConfig[CONFIG_SECTION] if addinConfig.has_section(CONFIG_SECTION) else {}
    folder = section.get('folder', '')
    if not os.path.isdir(folder):
        downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
        folder = downloads if os.path.isdir(downloads) else os.path.expanduser('~')
    format = section.get('format', FORMAT_3MF)
    return {
        'folder': folder,
        'format': format if format in FORMATS else FORMAT_3MF,
        'paint': section.get('paint', 'yes') != 'no',
        # the filaments of the label colors (round 37), an older export's one label filament for text without a color
        'filaments': exportParts.labelFilamentChoices(dict(section)),
        # the bed, its size, spacing and purge square in mm (r29-export)
        'layout': exportParts.layoutChoices(dict(section), bedNames()),
    }

def bedNames() -> list[str]:
    """The bed dropdown's entries, the baseplate dialog's presets after Custom"""
    return [printBeds.PRINT_BED_CUSTOM] + list(printBeds.PRINT_BED_PRESETS.keys())

def saveChoices(folder: str, format: str, paint: bool, filaments: dict[str, int], layout: dict):
    """The filaments of the label colors shown, with the saved ones of other colors (round 37)"""
    addinConfig = configUtils.readConfig(CONFIG_FOLDER_PATH)
    saved = exportParts.labelFilamentChoices(dict(addinConfig[CONFIG_SECTION])) if addinConfig.has_section(CONFIG_SECTION) else {}
    addinConfig[CONFIG_SECTION] = {
        'folder': folder,
        'format': format,
        'paint': 'yes' if paint else 'no',
        'labelFilaments': exportParts.formatLabelFilaments(exportParts.mergeLabelFilaments(saved, filaments)),
        'bed': layout['bed'],
        'bedWidth': f'{layout["bedWidth"]:g}',
        'bedLength': f'{layout["bedLength"]:g}',
        'spacing': f'{layout["spacing"]:g}',
        'purge': f'{layout["purge"]:g}',
    }
    if not configUtils.writeConfig(addinConfig, CONFIG_FOLDER_PATH):
        futil.log(f'{CMD_NAME} choices not saved to {CONFIG_FOLDER_PATH}')

def command_created(args: adsk.core.CommandCreatedEventArgs):
    global dialogFolder, isFileNameTyped, dialogFilaments, dialogAssigned
    command = args.command
    inputs = command.commandInputs
    choices = readChoices()
    dialogFolder = choices['folder']
    isFileNameTyped = False
    dialogFilaments = dict(choices['filaments'])
    dialogAssigned = {}
    design = adsk.fusion.Design.cast(app.activeProduct)
    # the whole design when its root was picked
    allInput = inputs.addBoolValueInput(ALL_INPUT_ID, 'All Gridkeeper parts', True, '', isRootSelected(design))
    allInput.tooltip = 'Selects every visible bin, baseplate, Cullenect insert and box of the design, with their colored text, off goes back to what was selected'
    selectionInput = inputs.addSelectionInput(SELECTION_INPUT_ID, 'Bodies', 'Bins, baseplates, Cullenect inserts, boxes or any other bodies to export, a letter stands for its part')
    # bodies only, Fusion puts a selected component in too as the command starts, beside its bodies
    selectionInput.addSelectionFilter(adsk.core.SelectionCommandInput.SolidBodies)
    selectionInput.setSelectionLimits(0, 0)
    selectAll(inputs, allInput.value)
    formatInput = inputs.addDropDownCommandInput(FORMAT_INPUT_ID, 'Format', adsk.core.DropDownStyles.TextListDropDownStyle)
    for name in FORMATS:
        formatInput.listItems.add(name, name == choices['format'])
    formatInput.tooltip = '3MF lays the bodies out in print orientation on the print bed, a file per plate, STL and STEP give each body a file of its own in the folder'
    folderInput = inputs.addTextBoxCommandInput(FOLDER_INPUT_ID, 'Folder', dialogFolder, 2, True)
    folderInput.tooltip = 'Where the files go, the last folder chosen is kept'
    browseInput = inputs.addBoolValueInput(BROWSE_INPUT_ID, '', False, '', False)
    browseInput.text = 'Choose folder...'
    fileNameInput = inputs.addStringValueInput(FILE_NAME_INPUT_ID, 'File name', '')
    fileNameInput.tooltip = 'The 3MF file\'s name, the body\'s name for one body'
    paintInput = inputs.addBoolValueInput(PAINT_INPUT_ID, 'Color label text', True, '', choices['paint'])
    paintInput.tooltip = 'Assigns each label color a filament so the slicer paints it automatically: the letters of outline labels, and the colored text and symbols of bins, Cullenect inserts and box labels. The parts print on filament 1'
    filamentsGroup = inputs.addGroupCommandInput(FILAMENTS_GROUP_ID, 'Label filaments')
    filamentsGroup.isExpanded = True
    filamentsGroup.tooltip = 'The slicer\'s filament of each label color of the parts, counting from 1 as the slicer lists them, 1 is the filament the parts print on. Each color starts on a filament of its own, a change is kept for the next export'
    addLayoutInputs(inputs, choices['layout'])
    inputs.addTextBoxCommandInput(SUMMARY_INPUT_ID, '', '', 2, True)
    # as wide as the bin dialog, the minimum widens one Fusion kept narrower from before
    command.setDialogInitialSize(450, 400)
    command.setDialogMinimumSize(450, 300)
    updateInputs(inputs)
    futil.add_handler(command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(command.destroy, command_destroy, local_handlers=local_handlers)

def addLayoutInputs(inputs: adsk.core.CommandInputs, layout: dict):
    """
    The bed the 3MF's parts are laid out on, the baseplate dialog's presets or a size of its own, the spacing between
    the parts and the purge tower's square, in Fusion's units, cm (round r29-export)
    """
    product = adsk.fusion.Design.cast(app.activeProduct)
    units = product.unitsManager.defaultLengthUnits if product is not None else 'mm'
    group = inputs.addGroupCommandInput(BED_GROUP_ID, 'Print bed')
    group.isExpanded = True
    bedInput = group.children.addDropDownCommandInput(BED_INPUT_ID, 'Printer', adsk.core.DropDownStyles.TextListDropDownStyle)
    for name in bedNames():
        bedInput.listItems.add(name, name == layout['bed'])
    bedInput.tooltip = "The 3MF lays the parts out on this bed in print orientation, what doesn't fit goes on further plates"
    for (inputId, name, value, tooltip) in (
        (BED_WIDTH_INPUT_ID, 'Bed width, X', layout['bedWidth'], 'The usable width of the bed'),
        (BED_LENGTH_INPUT_ID, 'Bed length, Y', layout['bedLength'], 'The usable depth of the bed'),
        (SPACING_INPUT_ID, 'Spacing', layout['spacing'], 'Space between the parts and to the edge of the bed'),
        (PURGE_INPUT_ID, 'Purge tower area', layout['purge'], 'A square kept free on each plate for the purge tower when label text is colored: where Bambu Studio puts the tower for a Bambu Lab printer, the back right corner for others, 0 for none'),
    ):
        valueInput = group.children.addValueInput(inputId, name, units, adsk.core.ValueInput.createByReal(value / 10))
        valueInput.minimumValue = 0
        valueInput.isMinimumInclusive = inputId in (SPACING_INPUT_ID, PURGE_INPUT_ID)
        valueInput.tooltip = tooltip

def layoutOf(inputs: adsk.core.CommandInputs) -> dict:
    """The dialog's bed, spacing and purge square, mm"""
    def value(inputId: str) -> float:
        return adsk.core.ValueCommandInput.cast(inputs.itemById(inputId)).value * 10
    return {
        'bed': adsk.core.DropDownCommandInput.cast(inputs.itemById(BED_INPUT_ID)).selectedItem.name,
        'bedWidth': value(BED_WIDTH_INPUT_ID),
        'bedLength': value(BED_LENGTH_INPUT_ID),
        'spacing': value(SPACING_INPUT_ID),
        'purge': value(PURGE_INPUT_ID),
    }

def bedInputChanged(inputs: adsk.core.CommandInputs, changed: adsk.core.CommandInput):
    """A preset sets the bed size, typing a size turns the dropdown to Custom, as in the baseplate dialog"""
    global isApplyingBedPreset
    bedInput = adsk.core.DropDownCommandInput.cast(inputs.itemById(BED_INPUT_ID))
    if changed.id == BED_INPUT_ID:
        size = printBeds.presetBedSize(bedInput.selectedItem.name)
        if size is None:
            return
        isApplyingBedPreset = True
        try:
            adsk.core.ValueCommandInput.cast(inputs.itemById(BED_WIDTH_INPUT_ID)).value = size[0]
            adsk.core.ValueCommandInput.cast(inputs.itemById(BED_LENGTH_INPUT_ID)).value = size[1]
        finally:
            isApplyingBedPreset = False
    elif changed.id in (BED_WIDTH_INPUT_ID, BED_LENGTH_INPUT_ID) and not isApplyingBedPreset:
        # only a size that is no longer the preset's, should Fusion report the preset's own setting late
        size = printBeds.presetBedSize(bedInput.selectedItem.name) if bedInput.selectedItem is not None else None
        typed = tuple(adsk.core.ValueCommandInput.cast(inputs.itemById(inputId)).value for inputId in (BED_WIDTH_INPUT_ID, BED_LENGTH_INPUT_ID))
        if size is not None and not all(math.isclose(a, b, abs_tol=1e-6) for (a, b) in zip(size, typed)):
            bedInput.listItems.item(0).isSelected = True

def command_input_changed(args: adsk.core.InputChangedEventArgs):
    global dialogFolder, isFileNameTyped
    # a filament set by hand stays when the selection changes, those assigned anew don't: they could take a number
    # another color gets then (round 37)
    color = colorOfFilamentInput(args.input.id)
    if color is not None:
        filament = selectedFilament(adsk.core.DropDownCommandInput.cast(args.input))
        if filament is not None:
            dialogFilaments[color] = filament
        return
    # args.inputs only holds the siblings of the changed input, those of the Print bed group in it, the dialog's
    # inputs are on the command (as the baseplate dialog notes; review r29-export)
    inputs = args.input.parentCommand.commandInputs
    if args.input.id in (BED_WIDTH_INPUT_ID, BED_LENGTH_INPUT_ID, SPACING_INPUT_ID, PURGE_INPUT_ID):
        # "2.9" typed stays so in the field, it's shown as "2.90 mm" like in the other dialogs (p291)
        expressionFormat.request(adsk.core.ValueCommandInput.cast(args.input))
    if args.input.id in (BED_INPUT_ID, BED_WIDTH_INPUT_ID, BED_LENGTH_INPUT_ID):
        bedInputChanged(inputs, args.input)
    if args.input.id == ALL_INPUT_ID:
        selectAll(inputs, adsk.core.BoolValueCommandInput.cast(args.input).value)
    elif args.input.id == BROWSE_INPUT_ID:
        folder = askFolder(dialogFolder)
        if folder is not None:
            dialogFolder = folder
            adsk.core.TextBoxCommandInput.cast(inputs.itemById(FOLDER_INPUT_ID)).text = folder
    elif args.input.id == FILE_NAME_INPUT_ID:
        isFileNameTyped = True
    updateInputs(inputs)

def selectAll(inputs: adsk.core.CommandInputs, isAll: bool):
    """Every visible part in the selection, or what was selected as the dialog opened"""
    selectionInput = adsk.core.SelectionCommandInput.cast(inputs.itemById(SELECTION_INPUT_ID))
    selectionInput.clearSelection()
    design = adsk.fusion.Design.cast(app.activeProduct)
    entities = gridfinityBodies(design) if isAll and design is not None else menuSelection(design)
    for entity in entities:
        selectionInput.addSelection(entity)

def gridfinityBodies(design: adsk.fusion.Design) -> list[adsk.fusion.BRepBody]:
    """
    The visible parts where they're placed, those of a component in each of its occurrences. The tagged letters of a
    Cullenect insert come with the insert, see exportParts.isPartBody
    """
    root = design.rootComponent
    bodies = []
    for tagName in exportParts.EXPORT_TAGS:
        for (body, _) in tagUtils.findTaggedBodies(design, tagName):
            component = body.parentComponent
            if not exportParts.isPartBody(tagName, component.name, component == root):
                continue
            if component == root:
                placed = [body]
            else:
                placed = [body.createForAssemblyContext(occurrence) for occurrence in root.allOccurrencesByComponent(component)]
            bodies += [placedBody for placedBody in placed if placedBody.isVisible]
    # the small parts of box sets, untagged, by their component's role (review round 28)
    for component in design.allComponents:
        if partRoleOf(component) not in exportParts.SMALL_PART_ROLES:
            continue
        for body in component.bRepBodies:
            placed = [body.createForAssemblyContext(occurrence) for occurrence in root.allOccurrencesByComponent(component)]
            bodies += [placedBody for placedBody in placed if placedBody.isVisible]
    return bodies

def selectedFormat(inputs: adsk.core.CommandInputs) -> str:
    return adsk.core.DropDownCommandInput.cast(inputs.itemById(FORMAT_INPUT_ID)).selectedItem.name

def updateInputs(inputs: adsk.core.CommandInputs):
    """Painting is for 3MF only, the summary says what goes out"""
    format = selectedFormat(inputs)
    paintInput = adsk.core.BoolValueCommandInput.cast(inputs.itemById(PAINT_INPUT_ID))
    paintInput.isVisible = format == FORMAT_3MF
    fileNameInput = adsk.core.StringValueCommandInput.cast(inputs.itemById(FILE_NAME_INPUT_ID))
    fileNameInput.isVisible = format == FORMAT_3MF
    inputs.itemById(BED_GROUP_ID).isVisible = format == FORMAT_3MF
    inputs.itemById(PURGE_INPUT_ID).isVisible = format == FORMAT_3MF and paintInput.value
    try:
        items = exportItems(inputs)
        updateFilamentInputs(inputs, labelColorsOf(items), format == FORMAT_3MF and paintInput.value)
        if not isFileNameTyped:
            fileNameInput.value = defaultFileName(items)
        files = 'a 3MF file per plate' if format == FORMAT_3MF else 'a file each'
        summary = f'{len(items)} part{"" if len(items) == 1 else "s"}, {files}' if items else 'Select bodies to export'
    except Exception as err:
        summary = f'Bodies not found, {err}'
    adsk.core.TextBoxCommandInput.cast(inputs.itemById(SUMMARY_INPUT_ID)).text = summary

def filamentInputId(color: str) -> str:
    return FILAMENT_INPUT_PREFIX + (color.lstrip('#') or exportParts.NO_COLOR_KEY)

def colorOfFilamentInput(inputId: str) -> str | None:
    """The label color of a filament input by its id, none for another input, see filamentInputId"""
    if not inputId.startswith(FILAMENT_INPUT_PREFIX):
        return None
    name = inputId[len(FILAMENT_INPUT_PREFIX):]
    return '' if name == exportParts.NO_COLOR_KEY else f'#{name}'

def filamentInputs(inputs: adsk.core.CommandInputs) -> list[adsk.core.DropDownCommandInput]:
    """
    A list of filaments per label color, not a spinner: Fusion drops a number typed into a spinner when OK is clicked
    straight from the field, without a change event (click test round 37), a list item counts as soon as it's picked
    """
    group = adsk.core.GroupCommandInput.cast(inputs.itemById(FILAMENTS_GROUP_ID))
    return [adsk.core.DropDownCommandInput.cast(group.children.item(index)) for index in range(group.children.count)]

def selectedFilament(filamentInput: adsk.core.DropDownCommandInput) -> int | None:
    item = filamentInput.selectedItem
    return exportParts.filamentOfChoice(item.name if item is not None else None)

def shownFilaments(inputs: adsk.core.CommandInputs) -> dict[str, int]:
    """The filament of each label color in the dialog"""
    shown = {colorOfFilamentInput(filamentInput.id): selectedFilament(filamentInput) for filamentInput in filamentInputs(inputs)}
    return {color: filament for (color, filament) in shown.items() if filament is not None}

def updateFilamentInputs(inputs: adsk.core.CommandInputs, colors: list[str], isShown: bool):
    """
    An input for each label color of the parts, made anew only when the colors change, so a filament input never goes
    while its own change is handled. A color's filament is the one changed in the dialog or saved, else assigned anew
    """
    global dialogFilaments, dialogAssigned
    group = adsk.core.GroupCommandInput.cast(inputs.itemById(FILAMENTS_GROUP_ID))
    if [filamentInput.id for filamentInput in filamentInputs(inputs)] != [filamentInputId(color) for color in colors]:
        # a number changed without its change event reaching us would go with its input (click test round 37)
        dialogFilaments = exportParts.keepTypedFilaments(dialogFilaments, shownFilaments(inputs), dialogAssigned)
        for filamentInput in filamentInputs(inputs):
            filamentInput.deleteMe()
        dialogAssigned = exportParts.assignFilaments(colors, dialogFilaments)
        for (color, filament) in dialogAssigned.items():
            name = labelColors.textName(color)
            filamentInput = group.children.addDropDownCommandInput(filamentInputId(color), name, adsk.core.DropDownStyles.TextListDropDownStyle)
            for choice in exportParts.filamentChoices():
                filamentInput.listItems.add(choice, choice == str(filament))
            filamentInput.tooltip = f'{name}: the slicer\'s filament it prints in, 1 is the filament of the parts'
    group.isVisible = isShown and len(colors) > 0

def selectedEntities(inputs: adsk.core.CommandInputs) -> list:
    selectionInput = adsk.core.SelectionCommandInput.cast(inputs.itemById(SELECTION_INPUT_ID))
    return [selectionInput.selection(index).entity for index in range(selectionInput.selectionCount)]

def exportItems(inputs: adsk.core.CommandInputs) -> list[ExportItem]:
    return exportItemsOf(selectedEntities(inputs))

def exportItemsOf(entities: list) -> list[ExportItem]:
    """
    The parts of the bodies and occurrences, each once with its colored text and symbol bodies: a letter stands for its
    part. Other bodies picked themselves go out as they are
    """
    bodies: list[adsk.fusion.BRepBody] = []
    def addOccurrence(occurrence: adsk.fusion.Occurrence):
        # visible ones, as the dialog's selection takes them, see occurrenceBodies
        bodies.extend(body for body in occurrence.bRepBodies if body.isVisible)
        for child in occurrence.childOccurrences:
            addOccurrence(child)

    for entity in entities:
        body = adsk.fusion.BRepBody.cast(entity)
        if body is not None:
            bodies.append(body)
            continue
        occurrence = adsk.fusion.Occurrence.cast(entity)
        if occurrence is not None:
            addOccurrence(occurrence)
    def partOf(body: adsk.fusion.BRepBody) -> adsk.fusion.BRepBody:
        return placedPart(body) or body
    def key(body: adsk.fusion.BRepBody) -> tuple:
        # a placed body by its native one and the occurrence placing it, as the 3MF and STEP export take it
        return (body.nativeObject, body.assemblyContext) if body.assemblyContext is not None else (body, None)
    items = []
    for body in exportParts.exportTargets(bodies, partOf, key):
        (native, occurrence) = key(body)
        items.append(ExportItem(native, occurrence, markingsOf(body) if isPartBody(body) else []))
    return items

def command_execute(args: adsk.core.CommandEventArgs):
    inputs = args.command.commandInputs
    try:
        format = selectedFormat(inputs)
        paint = adsk.core.BoolValueCommandInput.cast(inputs.itemById(PAINT_INPUT_ID)).value
        shown = shownFilaments(inputs)
        folder = dialogFolder
        if not os.path.isdir(folder):
            folder = askFolder(folder)
            if folder is None:
                return
        layout = layoutOf(inputs)
        items = exportItems(inputs)
        # the dialog shows every color of the parts, one missing is assigned anew; each is kept as it goes out (review
        # round 37: a color only assigned here wasn't saved)
        filaments = exportParts.assignFilaments(labelColorsOf(items), {**dialogFilaments, **shown})
        saveChoices(folder, format, paint, {**shown, **filaments}, layout)
        if len(items) == 0:
            ui.messageBox('Nothing to export, select bodies or turn on All Gridkeeper parts.', CMD_NAME)
            return
        names = fileNames(items)
        if format == FORMAT_3MF:
            fileName = safeFileName(adsk.core.StringValueCommandInput.cast(inputs.itemById(FILE_NAME_INPUT_ID)).value) or defaultFileName(items)
            fileName = fileName[:-4] if fileName.lower().endswith('.3mf') else fileName
            result = export3mf(items, names, folder, fileName, filaments if paint else None, layout)
            if result is None:
                return
            (painted, paths, tooLarge, noPurge, nearExcluded) = result
            where = paths[0] if len(paths) == 1 else f'{len(paths)} files, a file per plate, in {folder}'
            ui.messageBox(f'Exported {len(items)} part{"" if len(items) == 1 else "s"} to {where}.{plateNote(tooLarge, noPurge, nearExcluded, paint)}{paintNote(paint, painted, filaments)}', CMD_NAME)
        else:
            if not mayReplace([os.path.join(folder, f'{name}.{FORMAT_EXTENSIONS[format]}') for name in names]):
                return
            exportEach(items, names, folder, format)
            ui.messageBox(f'Exported {len(items)} {format} file{"" if len(items) == 1 else "s"} to {folder}.', CMD_NAME)
    except Exception as err:
        futil.handle_error(f'{CMD_NAME} failed, {err}', show_message_box=True)

def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    # the context menu handler stays for the next menu
    local_handlers = [handler for handler in local_handlers if handler is markingMenuHandler]

def paintNote(paint: bool, painted: int, filaments: dict[str, int] | None) -> str:
    """What of the labels was colored, after the export's message: each color with its filament (round 37)"""
    if not paint:
        return ''
    if painted == 0 or not filaments:
        return '\n\nNo label text to color.'
    bodies = 'the part' if painted == 1 else f'{painted} parts'
    colors = ', '.join(f'{labelColors.textName(color)} on filament {filament}' for (color, filament) in filaments.items())
    return f'\n\nLabel text of {bodies}: {colors}.'

def plateNote(tooLarge: list[str], noPurge: list[int], nearExcluded: list[int], paint: bool) -> str:
    """Which parts don't fit the bed, and which plates have no free corner for the purge tower"""
    note = ''
    if tooLarge:
        note += '\n\nLarger than the bed, on a plate of its own: ' + ', '.join(tooLarge) + '.'
    if paint and noPurge:
        note += '\n\nNo room kept free for the purge tower on plate ' + ', '.join(str(plate + 1) for plate in noPurge) + ', move the tower or a part in the slicer.'
    if nearExcluded:
        note += '\n\nA part comes near the area the printer keeps free on plate ' + ', '.join(str(plate + 1) for plate in nearExcluded) + ', the slicer may warn of collisions.'
    return note

def mayReplace(paths: list[str], removed: list[str] = None) -> bool:
    """
    Whether the files there already may be replaced, and the removed ones removed, asked once for all of them, see
    exportParts.replaceQuestion
    """
    existing = [path for path in paths if os.path.exists(path)]
    removed = removed or []
    if len(existing) == 0 and len(removed) == 0:
        return True
    folder = os.path.dirname((existing + removed)[0])
    question = exportParts.replaceQuestion([os.path.basename(path) for path in existing], [os.path.basename(path) for path in removed], folder, MAX_LISTED_FILES)
    answer = ui.messageBox(question, CMD_NAME, adsk.core.MessageBoxButtonTypes.YesNoButtonType, adsk.core.MessageBoxIconTypes.WarningIconType)
    return answer == adsk.core.DialogResults.DialogYes

def safeFileName(name: str) -> str:
    """Without the characters file systems refuse"""
    return re.sub(r'[\\/:*?"<>|]+', '_', name).strip()

def defaultFileName(items: list[ExportItem]) -> str:
    return fileNames(items)[0] if len(items) == 1 else DEFAULT_FILE_NAME

def setNameOf(item: ExportItem) -> str | None:
    """
    The name of the set a box's body is in: Base and Lid lie in the components Box and Lid of the set "Box 5×4×6"
    (round 27), the small parts in components of their own there (round 28). None for every other body and for a box
    built as bodies in the root
    """
    tag = tagUtils.readBodyTag(item.body)
    isSmallPart = partRoleOf(item.body.parentComponent) in exportParts.SMALL_PART_ROLES
    if not isSmallPart and (tag is None or tag[0] != tagUtils.TAG_BOX):
        return None
    partOccurrence = item.occurrence or occurrenceOf(item.body.parentComponent)
    setOccurrence = partOccurrence.assemblyContext if partOccurrence is not None else None
    return setOccurrence.component.name if setOccurrence is not None else None

def fileNames(items: list[ExportItem]) -> list[str]:
    """By body name, a box's with its set's name in front (exportParts.partFileName), numbered when the same"""
    names = []
    for item in items:
        name = safeFileName(exportParts.partFileName(item.body.name, setNameOf(item))) or 'Body'
        unique = name
        number = 2
        while unique.lower() in (other.lower() for other in names):
            unique = f'{name} ({number})'
            number += 1
        names.append(unique)
    return names

def askFolder(folder: str) -> str | None:
    dialog = ui.createFolderDialog()
    dialog.title = f'{CMD_NAME}, a folder for the files'
    if os.path.isdir(folder):
        dialog.initialDirectory = folder
    return dialog.folder if dialog.showDialog() == adsk.core.DialogResults.DialogOK else None

def progressDialog(count: int) -> adsk.core.ProgressDialog:
    progress = ui.createProgressDialog()
    progress.isCancelButtonShown = False
    progress.show(CMD_NAME, 'Exporting %v of %m', 0, count)
    return progress

def exportEach(items: list[ExportItem], names: list[str], folder: str, format: str):
    """
    A file of each body in the folder, files of the same name are replaced. Each body at the origin, centered on x and
    y with its bottom at z 0, as made on its own, whatever its place in the design
    """
    progress = progressDialog(len(items))
    # Fusion's STEP export writes a whole component where it is, and Fusion can't open a design hidden, so each body
    # goes alone into a design opened for a moment, which is closed without saving
    previous = app.activeDocument
    scratch = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType) if format == FORMAT_STEP else None
    try:
        for (index, (item, name)) in enumerate(zip(items, names)):
            path = os.path.join(folder, f'{name}.{FORMAT_EXTENSIONS[format]}')
            if format == FORMAT_STL:
                # the mesh the 3MF takes, Fusion's STL export writes a body where it is
                # in print orientation (17.11.2026, D4)
                meshObject = printMesh(item, name, None)
                stlFile.write(path, name, stlFile.atOrigin(meshObject.vertices), meshObject.triangles)
            else:
                exportStep(scratch, item, name, path)
            progress.progressValue = index + 1
    finally:
        progress.hide()
        if scratch is not None:
            scratch.close(False)
            if previous is not None and previous.isValid:
                previous.activate()

def exportStep(document: adsk.core.Document, item: ExportItem, name: str, path: str):
    """The body alone in the document with its text and symbol bodies (p300), together at the origin"""
    brepManager = adsk.fusion.TemporaryBRepManager.get()
    copies = []
    for placed in [item] + item.markings:
        copy = brepManager.copy(placed.body)
        if placed.occurrence is not None:
            brepManager.transform(copy, placed.occurrence.transform2)
        copies.append(copy)
    box = copies[0].boundingBox
    for copy in copies[1:]:
        box.combine(copy.boundingBox)
    move = toOrigin(box)
    design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
    # a body is added as it is without a base feature
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
    bodies = []
    try:
        for (index, copy) in enumerate(copies):
            brepManager.transform(copy, move)
            body = design.rootComponent.bRepBodies.add(copy)
            body.name = name if index == 0 else f'{name} text {index}'
            bodies.append(body)
        exportManager = design.exportManager
        if not exportManager.execute(exportManager.createSTEPExportOptions(path, design.rootComponent)):
            raise RuntimeError(f'{name} not written to {path}')
    finally:
        for body in bodies:
            body.deleteMe()

def toOrigin(box: adsk.core.BoundingBox3D) -> adsk.core.Matrix3D:
    """The move putting the box centered on x and y at 0 with its bottom at z 0, see stlFile.atOrigin"""
    move = adsk.core.Matrix3D.create()
    move.translation = adsk.core.Vector3D.create(
        -(box.minPoint.x + box.maxPoint.x) / 2,
        -(box.minPoint.y + box.maxPoint.y) / 2,
        -box.minPoint.z,
    )
    return move

def export3mf(items: list[ExportItem], names: list[str], folder: str, fileName: str, filaments: dict[str, int] | None, layout: dict) -> tuple[int, list[str], list[str], list[int], list[int]] | None:
    """
    The bodies in print orientation laid out on the bed, a 3MF per plate (round r29-export; 17.11.2026: sorting
    only works properly with one 3MF per plate), the purge tower's square free when
    the text is painted, a chosen Bambu Lab printer's excluded area free. Returns how many have painted letters, the
    files, the names of the parts too large for the bed, the plates without a free purge square and the plates near an
    excluded area; none when the files there may not be replaced
    """
    objects = []
    keys = []
    kinds = []
    paintedCount = 0
    progress = progressDialog(len(items))
    try:
        for (index, (item, name)) in enumerate(zip(items, names)):
            rotation = printRotationOf(item)
            meshObject = printMesh(item, name, filaments, rotation)
            paintedCount += 1 if meshObject.painted else 0
            objects.append(meshObject)
            occurrencePath = item.occurrence.fullPathName if item.occurrence is not None else None
            role = partRoleOf(item.body.parentComponent)
            keys.append(exportParts.printGroupKey(role, occurrencePath, rotation))
            tag = tagUtils.readExportTag(item.body)
            kinds.append(exportParts.plateKind(role, tag[0] if tag is not None else None, item.body.name, setNameOf(item)))
            progress.progressValue = index + 1
    finally:
        progress.hide()
    groups = exportParts.printGroups(keys)
    bed = (layout['bedWidth'], layout['bedLength'])
    # a purge tower only for painted text, where the printer's slicer puts it, the excluded areas of a Bambu Lab printer
    # chosen kept free (click test 17.11.2026: F2 the tower wasn't in the corner kept free, F1 Bambu warned of a box too
    # close to the X1's excluded area). A box set's box, lid and small parts on plates of their own (17.11.2026)
    purge = layout['purge'] if filaments is not None and paintedCount > 0 else 0.0
    (laid, plates, tooLarge, noPurge, nearExcluded) = printLayout.layOutKinds(
        [[objects[index] for index in group] for group in groups], [kinds[group[0]] for group in groups], bed,
        layout['spacing'], purge, printBeds.purgeAnchor(layout['bed']), printBeds.excludedAreas(layout['bed']))
    titles = [printLayout.plateFileName(fileName, plate, plates) for plate in range(plates)]
    paths = [os.path.join(folder, f'{title}.3mf') for title in titles]
    # the plate files of an earlier export of the name the new one doesn't write, they'd be printed with the new ones
    written = {os.path.normcase(path) for path in paths}
    stale = [os.path.join(folder, name) for name in os.listdir(folder)
             if printLayout.isPlateFileOf(name, fileName) and os.path.normcase(os.path.join(folder, name)) not in written]
    if not mayReplace(paths, stale):
        return None
    for (plate, (title, path)) in enumerate(zip(titles, paths)):
        onPlate = [meshObject for (index, meshObject) in laid if index == plate]
        threeMf.write(path, onPlate, title, tagUtils.getGeneratorVersion(), isLaidOut=True)
    for path in stale:
        # one held open by a slicer stays, the export itself is done (review r29-export)
        try:
            os.remove(path)
        except OSError as err:
            futil.log(f'{CMD_NAME} older plate file {path} not removed, {err}')
    return (paintedCount, paths, [names[groups[index][0]] for index in tooLarge], noPurge, nearExcluded)

def printRotationOf(item: ExportItem) -> str:
    """How the part turns into its print orientation, by its role in a box set or its label surface, see printLayout"""
    return printLayout.printRotation(partRoleOf(item.body.parentComponent), item.body.name, exportParts.labelSurface(tagUtils.readExportTag(item.body)))

def printMesh(item: ExportItem, name: str, filaments: dict[str, int] | None, rotation: str | None = None) -> threeMf.MeshObject:
    """
    The part's mesh in its own frame, its component's, turned into print orientation (round r29-export): the box set's
    joints and a box label's holder place a part upright, its own frame lies as Pred printed it, see
    printLayout.printRotation. Its text and symbol bodies come along, they're placed in its frame too
    """
    frame = None
    if item.occurrence is not None:
        frame = item.occurrence.transform2.copy()
        frame.invert()
    meshObject = partMesh(item, name, filaments, frame)
    rotation = printRotationOf(item) if rotation is None else rotation
    return dataclasses.replace(meshObject, vertices=printLayout.rotated(meshObject.vertices, rotation))

def partMesh(item: ExportItem, name: str, filaments: dict[str, int] | None, frame: adsk.core.Matrix3D | None = None) -> threeMf.MeshObject:
    """
    The part's mesh with its text and symbol bodies (p300). With the filaments of the label colors the letters of its
    outline labels get the one of text without a color, each text and symbol body the one of its color (round 37,
    p301), see exportParts.withMarkings
    """
    def filamentOf(color: str) -> int | None:
        return filaments.get(color) if filaments is not None else None
    meshObject = meshOf(item, name, filamentOf('') if item.hasOutlineLabels else None, frame)
    return exportParts.withMarkings(meshObject, [(meshOf(marking, name, None, frame), filamentOf(marking.labelColor)) for marking in item.markings])

def meshOf(item: ExportItem, name: str, filament: int | None, frame: adsk.core.Matrix3D | None = None) -> threeMf.MeshObject:
    """
    The body's triangles in mm where it's placed, the nodes Fusion repeats for each face joined into one. With a
    filament, the triangles on the letter faces of its outline labels are painted with it, see labelFaces
    """
    calculator = item.body.meshManager.createMeshCalculator()
    calculator.setQuality(MESH_QUALITY)
    mesh = calculator.calculate()
    coordinates = mesh.nodeCoordinatesAsDouble
    nodeIndices = mesh.nodeIndices
    transform = item.occurrence.transform2 if item.occurrence is not None else None

    nodes: list[tuple[float, float, float]] = []
    vertices: list[tuple[float, float, float]] = []
    joined: dict[tuple, int] = {}
    nodeVertex = []
    for index in range(len(coordinates) // 3):
        node = (coordinates[index * 3], coordinates[index * 3 + 1], coordinates[index * 3 + 2])
        key = tuple(round(value, 7) for value in node)
        if key not in joined:
            joined[key] = len(vertices)
            nodes.append(node)
            point = adsk.core.Point3D.create(*node)
            if transform is not None:
                point.transformBy(transform)
            # back into the part's own frame, see printMesh
            if frame is not None:
                point.transformBy(frame)
            vertices.append((point.x * 10, point.y * 10, point.z * 10))
        nodeVertex.append(joined[key])

    triangles = []
    painted: dict[int, int] = {}
    letters = letterPlanes(item.body) if filament is not None else []
    for index in range(len(nodeIndices) // 3):
        triangle = tuple(nodeVertex[node] for node in nodeIndices[index * 3:index * 3 + 3])
        if len(set(triangle)) < 3:
            continue
        if letters and isOnLetter([nodes[vertex] for vertex in triangle], letters):
            painted[len(triangles)] = filament
        triangles.append(triangle)
    return threeMf.MeshObject(name, vertices, triangles, painted)

@dataclasses.dataclass
class LetterPlane:
    face: adsk.fusion.BRepFace
    normal: tuple[float, float, float]
    offset: float
    # min and max corner
    box: tuple[tuple[float, float, float], tuple[float, float, float]]

def letterPlanes(body: adsk.fusion.BRepBody) -> list[LetterPlane]:
    planes = []
    for face in labelFaces.outlineLetterFaces(body):
        (_, normal) = face.evaluator.getNormalAtPoint(face.pointOnFace)
        normal.normalize()
        point = face.pointOnFace
        box = face.boundingBox
        planes.append(LetterPlane(
            face,
            (normal.x, normal.y, normal.z),
            normal.x * point.x + normal.y * point.y + normal.z * point.z,
            ((box.minPoint.x, box.minPoint.y, box.minPoint.z), (box.maxPoint.x, box.maxPoint.y, box.maxPoint.z)),
        ))
    return planes

def isOnLetter(corners: list[tuple[float, float, float]], letters: list[LetterPlane]) -> bool:
    """A triangle lies on one face only, so its middle tells which"""
    middle = tuple(sum(corner[axis] for corner in corners) / 3 for axis in range(3))
    for letter in letters:
        if abs(sum(n * m for (n, m) in zip(letter.normal, middle)) - letter.offset) > PAINT_TOLERANCE:
            continue
        if any(middle[axis] < letter.box[0][axis] - PAINT_TOLERANCE or middle[axis] > letter.box[1][axis] + PAINT_TOLERANCE for axis in range(3)):
            continue
        evaluator = letter.face.evaluator
        (isOk, parameter) = evaluator.getParameterAtPoint(adsk.core.Point3D.create(*middle))
        if isOk and evaluator.isParameterOnFace(parameter):
            return True
    return False
