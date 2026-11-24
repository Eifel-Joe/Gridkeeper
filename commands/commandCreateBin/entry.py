import adsk.core, adsk.fusion, traceback
import html
import os
import pathlib
import time
import math
import dataclasses


from ...lib.gridfinityUtils import designIntent
from ...lib import configUtils
from ...lib import tagUtils
from ...lib import settingsUtils
from ...lib import fusion360utils as futil
from ... import config
from ...lib.gridfinityUtils import commonUtils
from ...lib.gridfinityUtils import const
from ...lib.gridfinityUtils import labelGenerator
from ...lib.gridfinityUtils import labelColors
from ...lib.gridfinityUtils import scoopSides
from ...lib.gridfinityUtils import textStyles
from ...lib.gridfinityUtils import cullenect
from ...lib.gridfinityUtils import binCell
from ...lib.gridfinityUtils.binBodyTabGenerator import tabFilletAllowance
from ...lib.gridfinityUtils.binBodyLipGeneratorInput import LIP_TYPES, lipHeight
from ...lib.gridfinityUtils import compartmentLayout
from ...lib.gridfinityUtils import binShape
from ...lib.gridfinityUtils import binGrid
from ...lib.gridfinityUtils import magnetSizes
from ...lib.ui import magnetSizeInput
from ...lib.gridfinityUtils import wallCreases
from ...lib.gridfinityUtils import raisedDividers
from .inputState import InputState
from . import binBuilder
from .binBuilder import BIN_TYPE_HOLLOW, BIN_TYPE_SHELLED, BIN_TYPE_SOLID
from ...lib.ui.commandUiState import CommandUiState
from ...lib.ui.defaultsButtons import addDefaultsButtonRow, defaultsButtonsHandlers, DEFAULTS_SAVE, DEFAULTS_FACTORY_RESET
from ...lib.ui.buttonRow import addButtonRow
from ...lib.ui import configButtons
from ...lib.ui import selection
from ...lib.ui import browserPages
from ...lib.ui.infoPage import addInfoPage, infoPageHandlers, warningLine
from ...lib.ui.unsupportedDesignTypeException import UnsupportedDesignTypeException
from ...lib.ui import errorPalette
from ...lib import errorReport
from ...lib import rebuildUtils
from ...lib import configJson
from ...lib import defaultSettings

# what the dialog starts with before saved defaults, see lib/defaultSettings.py
DEFAULT_STATE = configJson.stateFromJson(configJson.GENERATOR_BIN, InputState, defaultSettings.BIN)

app = adsk.core.Application.get()
ui = app.userInterface


# *** The command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdBin'
CMD_NAME = 'Gridkeeper bin'
# the first section of a part's settings names the part, as the settings window does (review round 23)
SETTINGS_TITLE = 'Gridfinity bin'
# shown on hover over the button, the first paragraph says what it makes, the second how
CMD_Description = ('Creates a gridfinity bin that drops into a baseplate.\n\n'
    'Set its size in base and height units, then pick a hollow, shelled or solid body with a stacking lip, '
    'compartments, a scoop, a label tab and magnet or screw holes in its feet. '
    'A custom shape fills odd spots like a tetris piece.')

commandUIState = CommandUiState(CMD_NAME)
actualDimensionsTableUiState = CommandUiState(CMD_NAME)
# pockets drawn in the compartments drawing, see compartmentLayout
compartmentPockets: list[dict] = []
# cells of a custom shaped bin, see binShape, empty while the bin is a plain rectangle
binShapeCells: list[tuple[int, int]] = []
# config the dialog opens with next, see startWithConfig
pendingConfig: dict | None = None
# a body of the bin the dialog opens to rebuild next, see startRebuild, and the entity token of the one the open
# dialog rebuilds, every preview is undone, the token finds the body again after. None while it makes a new bin
pendingRebuildBody: adsk.fusion.BRepBody | None = None
rebuildBodyToken: str | None = None
# features after the rebuilt bin that need a look, shown once the dialog closes
rebuildNotes: list[str] = []
# the info text of the open dialog, the page asks for it once loaded
dialogInfo = ''
# how the open dialog came to be, for the log and the report of a failed build, see buildWorkflow
WORKFLOW_NEW = 'New bin'
WORKFLOW_CLONE = 'Clone from the settings window'
WORKFLOW_REBUILD = 'Rebuild in place from the settings window'
dialogWorkflow = WORKFLOW_NEW
# configs loaded from a file into the open dialog
loadedConfigs: list[str] = []
# bodies of the last build, selected and centered in the view when the dialog closes on OK, see command_destroy
builtBodies: list[adsk.fusion.BRepBody] = []

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')
# picture under the description on hover, like Fusion's own commands
TOOL_CLIP_PATH = os.path.join(ICON_FOLDER, 'toolclip.png')
# the lip profile of each lip type in its dropdown, drawn by tools/lipTypeIcons.py
LIP_TYPE_ICON_FOLDER = os.path.join(ICON_FOLDER, 'lipTypes')

CONFIG_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'commandConfig')
UI_INPUT_DEFAULTS_CONFIG_PATH = os.path.join(CONFIG_FOLDER_PATH, "ui_input_defaults.json")
COMPARTMENTS_HTML_URL = browserPages.pageUrl(__file__, 'compartments.html')
SHAPE_HTML_URL = browserPages.pageUrl(__file__, 'shape.html')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

# Constants
BIN_BASIC_SIZES_GROUP = "bin_basic_sizes_group"
BIN_DIMENSIONS_GROUP = "bin_dimensions_group"
BIN_FEATURES_GROUP = "bin_features_group"
BIN_COMPARTMENTS_GROUP_ID = 'compartments_group'
BIN_SCOOP_GROUP_ID = 'bin_scoop_group'
BIN_TAB_FEATURES_GROUP_ID = 'bin_tab_features_group'
BIN_BASE_FEATURES_GROUP_ID = 'bin_base_features_group'
USER_CHANGES_GROUP_ID = 'user_changes_group'
PREVIEW_GROUP_ID = 'preview_group'
INFO_GROUP = 'info_group'
# where a new bin goes, a cell of a baseplate or box (round 31, p312), not kept with the settings
BIN_PLACEMENT_GROUP_ID = 'bin_placement_group'
BIN_CELL_INPUT_ID = 'bin_cell'

BIN_BASE_WIDTH_UNIT_INPUT_ID = 'base_width_unit'
BIN_BASE_LENGTH_UNIT_INPUT_ID = 'base_length_unit'
BIN_HEIGHT_UNIT_INPUT_ID = 'height_unit'
BIN_XY_CLEARANCE_INPUT_ID = 'bin_xy_tolerance'
BIN_WIDTH_INPUT_ID = 'bin_width'
BIN_LENGTH_INPUT_ID = 'bin_length'
# half size feet all over, otherwise sizes ending in a half get a row of half feet, see binGrid
BIN_HALF_GRID_INPUT_ID = 'half_grid'
BIN_HEIGHT_INPUT_ID = 'bin_height'
BIN_REAL_DIMENSIONS_TABLE = "real_dimensions"
BIN_REAL_DIMENSIONS_TABLE_TOTAL_WIDTH = "total_real_width"
BIN_REAL_DIMENSIONS_TABLE_TOTAL_LENGTH = "total_real_length"
BIN_REAL_DIMENSIONS_TABLE_TOTAL_HEIGHT = "total_real_height"
BIN_REAL_DIMENSIONS_TABLE_CULLENECT = "cullenect_sockets"
BIN_REAL_DIMENSIONS_TABLE_TOTAL_WIDTH_INCHES = "total_real_width_inches"
BIN_REAL_DIMENSIONS_TABLE_TOTAL_LENGTH_INCHES = "total_real_length_inches"
BIN_REAL_DIMENSIONS_TABLE_TOTAL_HEIGHT_INCHES = "total_real_height_inches"
BIN_WALL_THICKNESS_INPUT_ID = 'bin_wall_thickness'
BIN_SHELL_ROUNDED_INPUT_ID = 'bin_shell_rounded'
BIN_GENERATE_BASE_INPUT_ID = 'bin_generate_base'
BIN_GENERATE_BODY_INPUT_ID = 'bin_generate_body'
BIN_JOINT_ORIGINS_INPUT_ID = 'bin_joint_origins'
BIN_PLACEMENT_INPUT_ID = 'bin_placement'
BIN_SCREW_HOLES_INPUT_ID = 'bin_screw_holes'
BIN_MAGNET_CUTOUTS_INPUT_ID = 'bin_magnet_cutouts'
BIN_MAGNET_CUTOUTS_TABS_INPUT_ID = 'bin_magnet_cutouts_tabs'
BIN_SCREW_DIAMETER_INPUT = 'screw_diameter'
BIN_MAGNET_DIAMETER_INPUT = 'magnet_diameter'
BIN_MAGNET_HEIGHT_INPUT = 'magnet_height'
# the magnet size choice before the depth (round 27, p263)
BIN_MAGNET_SIZE_INPUT = 'magnet_size'
# the front wall's, the only scoop before round 48, keeps its ID
BIN_HAS_SCOOP_INPUT_ID = 'bin_has_scoop'
BIN_HAS_SCOOP_BACK_INPUT_ID = 'bin_has_scoop_back'
BIN_HAS_SCOOP_LEFT_INPUT_ID = 'bin_has_scoop_left'
BIN_HAS_SCOOP_RIGHT_INPUT_ID = 'bin_has_scoop_right'
BIN_SCOOP_WALL_INPUT_IDS = [BIN_HAS_SCOOP_INPUT_ID, BIN_HAS_SCOOP_BACK_INPUT_ID, BIN_HAS_SCOOP_LEFT_INPUT_ID, BIN_HAS_SCOOP_RIGHT_INPUT_ID]
BIN_SCOOP_MAX_RADIUS_INPUT_ID = 'bin_scoop_max_radius'
BIN_HAS_TAB_INPUT_ID = 'bin_has_tab'
BIN_TAB_LENGTH_INPUT_ID = 'bin_tab_length'
BIN_TAB_WIDTH_INPUT_ID = 'bin_tab_width'
BIN_TAB_POSITION_INPUT_ID = 'bin_tab_position'
BIN_TAB_ANGLE_INPUT_ID = 'bin_tab_angle'
BIN_TAB_HOLLOW_INPUT_ID = 'bin_tab_hollow'
BIN_TAB_HOLLOW_SIDES_INPUT_ID = 'bin_tab_hollow_sides'
BIN_TAB_TOP_ANGLE_INPUT_ID = 'bin_tab_top_angle'
BIN_TAB_TOP_OFFSET_INPUT_ID = 'bin_tab_top_offset'
BIN_TAB_LABEL_TEXT_INPUT_ID = 'bin_tab_label_text'
BIN_TAB_LABEL_ICON_INPUT_ID = 'bin_tab_label_icon'
BIN_TAB_LABEL_STYLE_INPUT_ID = 'bin_tab_label_style'
BIN_TAB_LABEL_BOLD_INPUT_ID = 'bin_tab_label_bold'
BIN_TAB_LABEL_COLOR_INPUT_ID = 'bin_tab_label_color'
BIN_TAB_LABEL_CUSTOM_COLOR_INPUT_ID = 'bin_tab_label_color_custom'
BIN_TAB_CULLENECT_OFFSET_INPUT_ID = 'bin_tab_cullenect_offset'
BIN_WITH_LIP_INPUT_ID = 'with_lip'
BIN_WITH_LIP_NOTCHES_INPUT_ID = 'with_lip_notches'
BIN_DIVIDERS_TO_TOP_INPUT_ID = 'dividers_to_top'
BIN_LIP_TYPE_INPUT_ID = 'lip_type'
BIN_LIP_TOP_TRIMMED_INPUT_ID = 'lip_top_trimmed'
# long walls folded in to stiffen them, see wallCreases
BIN_CREASES_INPUT_ID = 'wall_creases'
BIN_CREASE_DEPTH_INPUT_ID = 'wall_crease_depth'
BIN_CREASE_MIN_LENGTH_INPUT_ID = 'wall_crease_min_length'
BIN_CREASE_MAX_PANEL_LENGTH_INPUT_ID = 'wall_crease_max_panel_length'
BIN_CREASE_MIN_HEIGHT_INPUT_ID = 'wall_crease_min_height'
# replaced by the drawing, still read from defaults saved before it
LEGACY_COMPARTMENTS_GRID_TYPE_ID = 'compartments_grid_type'
LEGACY_COMPARTMENTS_GRID_TYPE_CUSTOM = 'Custom grid'
BIN_COMPARTMENTS_GRID_BASE_WIDTH_ID = 'compartments_grid_w'
BIN_COMPARTMENTS_GRID_BASE_LENGTH_ID = 'compartments_grid_l'
GRID_CELLS_MAX = 100
# the same page twice, a row with the grid size and a drawing to pick compartment shapes, labels and depths,
# the drawing shown on request as it takes space. Fusion doesn't resize a browser input once it's shown
BIN_COMPARTMENTS_SHOW_LAYOUT_ID = 'compartments_show_layout'
BIN_COMPARTMENTS_GRID_BROWSER_ID = 'compartments_grid_browser'
BIN_COMPARTMENTS_BROWSER_ID = 'compartments_browser'
COMPARTMENTS_PAGE_GRID = 'grid'
COMPARTMENTS_PAGE_LAYOUT = 'layout'
BIN_TYPE_DROPDOWN_ID = 'bin_type'
# a drawing of the bin's cells to leave some out, like a tetris piece, shown with the checkbox
BIN_SHAPE_CUSTOM_ID = 'custom_shape'
BIN_SHAPE_BROWSER_ID = 'shape_browser'
SHAPE_NOTE = 'Compartments, scoop and label tab are not built for custom shapes yet'

# InputState fields kept as they are in the dialog state, see getInputsState
STATE_INPUT_IDS = {
    'baseWidth': BIN_BASE_WIDTH_UNIT_INPUT_ID,
    'baseLength': BIN_BASE_LENGTH_UNIT_INPUT_ID,
    'heightUnit': BIN_HEIGHT_UNIT_INPUT_ID,
    'xyClearance': BIN_XY_CLEARANCE_INPUT_ID,
    'binWidth': BIN_WIDTH_INPUT_ID,
    'binLength': BIN_LENGTH_INPUT_ID,
    'binHeight': BIN_HEIGHT_INPUT_ID,
    'isHalfGrid': BIN_HALF_GRID_INPUT_ID,
    'wallThickness': BIN_WALL_THICKNESS_INPUT_ID,
    'binType': BIN_TYPE_DROPDOWN_ID,
    'isShellRounded': BIN_SHELL_ROUNDED_INPUT_ID,
    'generateBase': BIN_GENERATE_BASE_INPUT_ID,
    'generateBody': BIN_GENERATE_BODY_INPUT_ID,
    'hasJointOrigins': BIN_JOINT_ORIGINS_INPUT_ID,
    'placement': BIN_PLACEMENT_INPUT_ID,
    'hasScrewHoles': BIN_SCREW_HOLES_INPUT_ID,
    'screwHoleDiameter': BIN_SCREW_DIAMETER_INPUT,
    'hasMagnetCutouts': BIN_MAGNET_CUTOUTS_INPUT_ID,
    'hasMagnetCutoutsTabs': BIN_MAGNET_CUTOUTS_TABS_INPUT_ID,
    'magnetCutoutDiameter': BIN_MAGNET_DIAMETER_INPUT,
    'magnetCutoutDepth': BIN_MAGNET_HEIGHT_INPUT,
    'hasLip': BIN_WITH_LIP_INPUT_ID,
    'hasLipNotches': BIN_WITH_LIP_NOTCHES_INPUT_ID,
    'hasDividersToTop': BIN_DIVIDERS_TO_TOP_INPUT_ID,
    'lipType': BIN_LIP_TYPE_INPUT_ID,
    'isLipTopTrimmed': BIN_LIP_TOP_TRIMMED_INPUT_ID,
    'hasScoop': BIN_HAS_SCOOP_INPUT_ID,
    'hasScoopBack': BIN_HAS_SCOOP_BACK_INPUT_ID,
    'hasScoopLeft': BIN_HAS_SCOOP_LEFT_INPUT_ID,
    'hasScoopRight': BIN_HAS_SCOOP_RIGHT_INPUT_ID,
    'scoopMaxRadius': BIN_SCOOP_MAX_RADIUS_INPUT_ID,
    'hasTab': BIN_HAS_TAB_INPUT_ID,
    'tabLength': BIN_TAB_LENGTH_INPUT_ID,
    'tabWidth': BIN_TAB_WIDTH_INPUT_ID,
    'tabPosition': BIN_TAB_POSITION_INPUT_ID,
    'tabTopOffset': BIN_TAB_TOP_OFFSET_INPUT_ID,
    'isTabHollow': BIN_TAB_HOLLOW_INPUT_ID,
    'isTabOpenThroughSides': BIN_TAB_HOLLOW_SIDES_INPUT_ID,
    'labelText': BIN_TAB_LABEL_TEXT_INPUT_ID,
    'labelIcon': BIN_TAB_LABEL_ICON_INPUT_ID,
    'labelStyle': BIN_TAB_LABEL_STYLE_INPUT_ID,
    'isLabelBold': BIN_TAB_LABEL_BOLD_INPUT_ID,
    'cullenectSocketOffset': BIN_TAB_CULLENECT_OFFSET_INPUT_ID,
    'hasCreases': BIN_CREASES_INPUT_ID,
    'creaseDepth': BIN_CREASE_DEPTH_INPUT_ID,
    'creaseMinLength': BIN_CREASE_MIN_LENGTH_INPUT_ID,
    'creaseMaxPanelLength': BIN_CREASE_MAX_PANEL_LENGTH_INPUT_ID,
    'creaseMinHeight': BIN_CREASE_MIN_HEIGHT_INPUT_ID,
}
# angles are kept as the expression typed in, see CommandUiState.onInputUpdate
STATE_ANGLE_INPUT_IDS = {
    'tabOverhangAngle': BIN_TAB_ANGLE_INPUT_ID,
    'tabTopAngle': BIN_TAB_TOP_ANGLE_INPUT_ID,
}

INFO_BROWSER = 'info_page'
INPUT_CHANGES_BUTTONS_BROWSER = 'input_changes_buttons'
CONFIG_BUTTONS_BROWSER = 'config_buttons'
PRESERVE_CHAGES_RADIO_GROUP = 'preserve_changes'
PRESERVE_CHAGES_RADIO_GROUP_PRESERVE = 'Preserve inputs'
PRESERVE_CHAGES_RADIO_GROUP_RESET = 'Reset inputs after creation'
RESET_CHAGES_INPUT = 'reset_changes'
SHOW_PREVIEW_INPUT = 'show_preview'
SHOW_PREVIEW_MANUAL_INPUT = 'show_preview_manual'
PREVIEW_TIME_INPUT = 'preview_time'

INFO_TEXT = ("<b>Help:</b> every input is explained "
             "<a href=\"https://eifel-joe.github.io/Gridkeeper/bins/\">"
             "in the Gridkeeper documentation</a>.")

def infoText():
    version = tagUtils.getGeneratorVersion()
    return f"{INFO_TEXT}<br><span style=\"color:#808080; font-size:small\">Version {version}</span>" if version else INFO_TEXT

def refreshUi():
    global commandUIState
    commandUIState.forceUIRefresh()
    update_actual_bin_dimensions()
    # before the inputs that depend on the shape
    normalizeShapeCells()
    onChangeValidate()
    normalizeCompartmentPockets()
    updateCullenectSockets()
    refreshCompartmentsDrawing()
    refreshShapeDrawing()

def initDefaultUiState():
    global commandUIState
    global actualDimensionsTableUiState
    global compartmentPockets
    global binShapeCells
    commandUIState.initValue(INFO_GROUP, True, adsk.core.GroupCommandInput.classType())
    commandUIState.initValue(BIN_BASIC_SIZES_GROUP, True, adsk.core.GroupCommandInput.classType())
    commandUIState.initValue(BIN_DIMENSIONS_GROUP, True, adsk.core.GroupCommandInput.classType())
    commandUIState.initValue(BIN_FEATURES_GROUP, True, adsk.core.GroupCommandInput.classType())
    commandUIState.initValue(BIN_COMPARTMENTS_GROUP_ID, True, adsk.core.GroupCommandInput.classType())
    commandUIState.initValue(BIN_COMPARTMENTS_SHOW_LAYOUT_ID, DEFAULT_STATE.showCompartmentsLayout, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_SCOOP_GROUP_ID, True, adsk.core.GroupCommandInput.classType())
    commandUIState.initValue(BIN_TAB_FEATURES_GROUP_ID, True, adsk.core.GroupCommandInput.classType())
    commandUIState.initValue(BIN_BASE_FEATURES_GROUP_ID, True, adsk.core.GroupCommandInput.classType())
    commandUIState.initValue(USER_CHANGES_GROUP_ID, True, adsk.core.GroupCommandInput.classType())
    commandUIState.initValue(PREVIEW_GROUP_ID, True, adsk.core.GroupCommandInput.classType())

    commandUIState.initValue(BIN_BASE_WIDTH_UNIT_INPUT_ID, DEFAULT_STATE.baseWidth, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_BASE_LENGTH_UNIT_INPUT_ID, DEFAULT_STATE.baseLength, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_HEIGHT_UNIT_INPUT_ID, DEFAULT_STATE.heightUnit, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_XY_CLEARANCE_INPUT_ID, DEFAULT_STATE.xyClearance, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_WIDTH_INPUT_ID, DEFAULT_STATE.binWidth, adsk.core.FloatSpinnerCommandInput.classType())
    commandUIState.initValue(BIN_LENGTH_INPUT_ID, DEFAULT_STATE.binLength, adsk.core.FloatSpinnerCommandInput.classType())
    commandUIState.initValue(BIN_HALF_GRID_INPUT_ID, DEFAULT_STATE.isHalfGrid, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_SHAPE_CUSTOM_ID, DEFAULT_STATE.hasCustomShape, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_PLACEMENT_INPUT_ID, DEFAULT_STATE.placement, adsk.core.DropDownCommandInput.classType())
    commandUIState.initValue(BIN_HEIGHT_INPUT_ID, DEFAULT_STATE.binHeight, adsk.core.ValueCommandInput.classType())

    commandUIState.initValue(BIN_GENERATE_BODY_INPUT_ID, DEFAULT_STATE.generateBody, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_TYPE_DROPDOWN_ID, DEFAULT_STATE.binType, adsk.core.DropDownCommandInput.classType())
    commandUIState.initValue(BIN_SHELL_ROUNDED_INPUT_ID, DEFAULT_STATE.isShellRounded, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_WALL_THICKNESS_INPUT_ID, DEFAULT_STATE.wallThickness, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_WITH_LIP_INPUT_ID, DEFAULT_STATE.hasLip, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_WITH_LIP_NOTCHES_INPUT_ID, DEFAULT_STATE.hasLipNotches, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_DIVIDERS_TO_TOP_INPUT_ID, DEFAULT_STATE.hasDividersToTop, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_LIP_TYPE_INPUT_ID, DEFAULT_STATE.lipType, adsk.core.DropDownCommandInput.classType())
    commandUIState.initValue(BIN_LIP_TOP_TRIMMED_INPUT_ID, DEFAULT_STATE.isLipTopTrimmed, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_CREASES_INPUT_ID, DEFAULT_STATE.hasCreases, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_CREASE_DEPTH_INPUT_ID, DEFAULT_STATE.creaseDepth, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_CREASE_MIN_LENGTH_INPUT_ID, DEFAULT_STATE.creaseMinLength, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_CREASE_MAX_PANEL_LENGTH_INPUT_ID, DEFAULT_STATE.creaseMaxPanelLength, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_CREASE_MIN_HEIGHT_INPUT_ID, DEFAULT_STATE.creaseMinHeight, adsk.core.ValueCommandInput.classType())

    commandUIState.initValue(BIN_COMPARTMENTS_GRID_BASE_WIDTH_ID, DEFAULT_STATE.compartmentsX, adsk.core.IntegerSpinnerCommandInput.classType())
    commandUIState.initValue(BIN_COMPARTMENTS_GRID_BASE_LENGTH_ID, DEFAULT_STATE.compartmentsY, adsk.core.IntegerSpinnerCommandInput.classType())

    commandUIState.initValue(BIN_HAS_SCOOP_INPUT_ID, DEFAULT_STATE.hasScoop, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_HAS_SCOOP_BACK_INPUT_ID, DEFAULT_STATE.hasScoopBack, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_HAS_SCOOP_LEFT_INPUT_ID, DEFAULT_STATE.hasScoopLeft, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_HAS_SCOOP_RIGHT_INPUT_ID, DEFAULT_STATE.hasScoopRight, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_SCOOP_MAX_RADIUS_INPUT_ID, DEFAULT_STATE.scoopMaxRadius, adsk.core.ValueCommandInput.classType())

    commandUIState.initValue(BIN_HAS_TAB_INPUT_ID, DEFAULT_STATE.hasTab, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_TAB_LENGTH_INPUT_ID, DEFAULT_STATE.tabLength, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_TAB_WIDTH_INPUT_ID, DEFAULT_STATE.tabWidth, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_TAB_POSITION_INPUT_ID, DEFAULT_STATE.tabPosition, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_TAB_ANGLE_INPUT_ID, angleExpression(DEFAULT_STATE.tabOverhangAngle), adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_TAB_HOLLOW_INPUT_ID, DEFAULT_STATE.isTabHollow, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_TAB_HOLLOW_SIDES_INPUT_ID, DEFAULT_STATE.isTabOpenThroughSides, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_TAB_TOP_ANGLE_INPUT_ID, angleExpression(DEFAULT_STATE.tabTopAngle), adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_TAB_TOP_OFFSET_INPUT_ID, DEFAULT_STATE.tabTopOffset, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_TAB_LABEL_TEXT_INPUT_ID, DEFAULT_STATE.labelText, adsk.core.StringValueCommandInput.classType())
    commandUIState.initValue(BIN_TAB_LABEL_ICON_INPUT_ID, DEFAULT_STATE.labelIcon, adsk.core.DropDownCommandInput.classType())
    commandUIState.initValue(BIN_TAB_LABEL_STYLE_INPUT_ID, DEFAULT_STATE.labelStyle, adsk.core.DropDownCommandInput.classType())
    commandUIState.initValue(BIN_TAB_LABEL_BOLD_INPUT_ID, DEFAULT_STATE.isLabelBold, adsk.core.BoolValueCommandInput.classType())
    (defaultColorChoice, defaultCustomColor) = labelColors.choiceOf(DEFAULT_STATE.labelColor)
    commandUIState.initValue(BIN_TAB_LABEL_COLOR_INPUT_ID, defaultColorChoice, adsk.core.DropDownCommandInput.classType())
    commandUIState.initValue(BIN_TAB_LABEL_CUSTOM_COLOR_INPUT_ID, defaultCustomColor, adsk.core.StringValueCommandInput.classType())
    commandUIState.initValue(BIN_TAB_CULLENECT_OFFSET_INPUT_ID, DEFAULT_STATE.cullenectSocketOffset, adsk.core.ValueCommandInput.classType())

    commandUIState.initValue(BIN_GENERATE_BASE_INPUT_ID, DEFAULT_STATE.generateBase, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_JOINT_ORIGINS_INPUT_ID, DEFAULT_STATE.hasJointOrigins, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_SCREW_HOLES_INPUT_ID, DEFAULT_STATE.hasScrewHoles, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_SCREW_DIAMETER_INPUT, DEFAULT_STATE.screwHoleDiameter, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_MAGNET_CUTOUTS_INPUT_ID, DEFAULT_STATE.hasMagnetCutouts, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_MAGNET_CUTOUTS_TABS_INPUT_ID, DEFAULT_STATE.hasMagnetCutoutsTabs, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(BIN_MAGNET_DIAMETER_INPUT, DEFAULT_STATE.magnetCutoutDiameter, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_MAGNET_HEIGHT_INPUT, DEFAULT_STATE.magnetCutoutDepth, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(BIN_MAGNET_SIZE_INPUT, magnetSizes.choiceForDepth(DEFAULT_STATE.magnetCutoutDepth, magnetSizes.ALL_CHOICES), adsk.core.DropDownCommandInput.classType())

    compartmentPockets = list(DEFAULT_STATE.compartmentPockets)
    binShapeCells = list(DEFAULT_STATE.shapeCells)
    recordedDefaults = configUtils.readJsonConfig(UI_INPUT_DEFAULTS_CONFIG_PATH)
    if recordedDefaults is not None and recordedDefaults.get('static_ui') is not None:
        staticUiState = recordedDefaults['static_ui']
        futil.log(f'{CMD_NAME} Found previously saved default values, restoring {staticUiState}')
        try:
            commandUIState.initValues(staticUiState)
            futil.log(f'{CMD_NAME} Successfully restored default values')
        except Exception as err:
            futil.log(f'{CMD_NAME} Failed to restore default values, err: {err}')
        try:
            if isinstance(recordedDefaults.get('compartments'), list):
                # pockets only count with the layout shown, the grid is uniform otherwise
                if commandUIState.getState(BIN_COMPARTMENTS_SHOW_LAYOUT_ID):
                    compartmentPockets = recordedDefaults['compartments']
            elif staticUiState.get(LEGACY_COMPARTMENTS_GRID_TYPE_ID, {}).get('value') == LEGACY_COMPARTMENTS_GRID_TYPE_CUSTOM:
                # the custom grid table saved before the drawing, its rows become pockets
                compartmentPockets = compartmentLayout.fromTableRows(recordedDefaults.get('compartments_table'), fullCompartmentDepth() / 10)
                commandUIState.initValue(BIN_COMPARTMENTS_SHOW_LAYOUT_ID, True, adsk.core.BoolValueCommandInput.classType())
                futil.log(f'{CMD_NAME} Restored compartments from the saved custom grid table')
        except Exception as err:
            futil.log(f'{CMD_NAME} Failed to restore compartments, err: {err}')
        commandUIState.removeValue(LEGACY_COMPARTMENTS_GRID_TYPE_ID)
        if commandUIState.getState(BIN_SHAPE_CUSTOM_ID) and isinstance(recordedDefaults.get('shape'), list):
            binShapeCells = recordedDefaults['shape']
        # saved defaults of an older version have the depth only, the choice is read back from it
        magnetSizeInput.syncMagnetSize(commandUIState, BIN_MAGNET_SIZE_INPUT, BIN_MAGNET_HEIGHT_INPUT, magnetSizes.ALL_CHOICES)
    futil.log(f'{CMD_NAME} UI state initialized')

def getErrorMessage(text = "An unknown error occurred, please validate your inputs and try again"):
    stackTrace = traceback.format_exc()
    return f"{text}:<br>{stackTrace}"

def showErrorInMessageBox(text = "An unknown error occurred, please validate your inputs and try again"):
    if ui:
        ui.messageBox(getErrorMessage(text), f"{CMD_NAME} Error")

# Executed when add-in is run.
def start():
    try:
        futil.log(f'{CMD_NAME} Command Start Event')
        addinConfig = configUtils.readConfig(CONFIG_FOLDER_PATH)

        # Create a command Definition.
        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
        if not cmd_def:
            cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
            if os.path.isfile(TOOL_CLIP_PATH):
                cmd_def.toolClipFilename = TOOL_CLIP_PATH

            # Define an event handler for the command created event. It will be called when the button is clicked.
            futil.add_handler(cmd_def.commandCreated, command_created)

            # ******** Add a button into the UI so the user can run the command. ********
            # Get the target workspace the button will be created in.
            workspace = ui.workspaces.itemById(WORKSPACE_ID)

            # Get the panel the button will be created in.
            panel = workspace.toolbarPanels.itemById(PANEL_ID)

            # Create the button command control in the UI after the specified existing command.
            control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

            # Specify if the command is promoted to the main toolbar.
            control.isPromoted = addinConfig['UI'].getboolean('is_promoted')
        initDefaultUiState()
        ui.statusMessage = ""
    except Exception as err:
        futil.log(f'{CMD_NAME} Error occurred at the start, {err}, {getErrorMessage()}')
        ui.statusMessage = f"{CMD_NAME} failed to initialize"
        showErrorInMessageBox(f"{CMD_NAME} Critical error occurred at the start, the command will be unavailable, if the issue persists use <a href=\"{errorReport.ISSUES_URL}\">this link</a> to report it")

# Executed when add-in is stopped.
def stop():
    futil.log(f'{CMD_NAME} Command Stop Event')
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control: adsk.core.CommandControl = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    addinConfig = configUtils.readConfig(CONFIG_FOLDER_PATH)
    addinConfig['UI']['is_promoted'] = 'yes' if command_control.isPromoted else 'no'
    configUtils.writeConfig(addinConfig, CONFIG_FOLDER_PATH)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()

def render_actual_bin_dimensions_table(inputs: adsk.core.CommandInputs):
    global actualDimensionsTableUiState
    actualDimensionsTable = inputs.addTableCommandInput(BIN_REAL_DIMENSIONS_TABLE, "Actual dimensions", 3, "1:1:1")
    rows = [[
        (BIN_REAL_DIMENSIONS_TABLE_TOTAL_WIDTH, "Width"),
        (BIN_REAL_DIMENSIONS_TABLE_TOTAL_LENGTH, "Length"),
        (BIN_REAL_DIMENSIONS_TABLE_TOTAL_HEIGHT, "Height"),
    ]]
    # a document in inches shows them in inches too, on a line of their own
    if isDocumentInInches():
        rows.append([
            (BIN_REAL_DIMENSIONS_TABLE_TOTAL_WIDTH_INCHES, "Width in inches"),
            (BIN_REAL_DIMENSIONS_TABLE_TOTAL_LENGTH_INCHES, "Length in inches"),
            (BIN_REAL_DIMENSIONS_TABLE_TOTAL_HEIGHT_INCHES, "Height in inches"),
        ])
    for (row, cells) in enumerate(rows):
        for (column, (inputId, name)) in enumerate(cells):
            cell = actualDimensionsTable.commandInputs.addStringValueInput(inputId, "", name)
            cell.isReadOnly = True
            actualDimensionsTableUiState.registerCommandInput(cell)
            actualDimensionsTableUiState.initValue(cell.id, "", cell.objectType)
            actualDimensionsTable.addCommandInput(cell, row, column)
    cullenectSockets = actualDimensionsTable.commandInputs.addStringValueInput(BIN_REAL_DIMENSIONS_TABLE_CULLENECT, "", "")
    cullenectSockets.isReadOnly = True
    actualDimensionsTableUiState.registerCommandInput(cullenectSockets)
    actualDimensionsTableUiState.initValue(cullenectSockets.id, "", cullenectSockets.objectType)
    # the Cullenect sockets of the bin across the whole row below the sizes, see updateCullenectSockets
    actualDimensionsTable.addCommandInput(cullenectSockets, len(rows), 0, 0, 2)
    actualDimensionsTable.tooltip = 'Actual bin dimensions'
    actualDimensionsTable.tablePresentationStyle = adsk.core.TablePresentationStyles.transparentBackgroundTablePresentationStyle
    actualDimensionsTable.hasGrid = False
    actualDimensionsTable.minimumVisibleRows = len(rows)
    actualDimensionsTable.maximumVisibleRows = cullenect.dimensionsTableRows(isDocumentInInches(), False)
    return actualDimensionsTable

def compartmentCellSize() -> tuple[float, float, float]:
    """Width and length of a compartment grid cell in mm, and the smallest one that still fits the corner fillets"""
    wallThickness: float = commandUIState.getState(BIN_WALL_THICKNESS_INPUT_ID)
    xyClearance: float = commandUIState.getState(BIN_XY_CLEARANCE_INPUT_ID)
    def cell(baseUnit: float, binSize: int, cells: int) -> float:
        return round((baseUnit * binSize - wallThickness * 2 - xyClearance * 2 - wallThickness * (cells - 1)) / cells * 10, 2)
    return (
        cell(commandUIState.getState(BIN_BASE_WIDTH_UNIT_INPUT_ID), commandUIState.getState(BIN_WIDTH_INPUT_ID), commandUIState.getState(BIN_COMPARTMENTS_GRID_BASE_WIDTH_ID)),
        cell(commandUIState.getState(BIN_BASE_LENGTH_UNIT_INPUT_ID), commandUIState.getState(BIN_LENGTH_INPUT_ID), commandUIState.getState(BIN_COMPARTMENTS_GRID_BASE_LENGTH_ID)),
        round((const.BIN_CORNER_FILLET_RADIUS - wallThickness) * 2 * 10, 2),
    )

def millimeters(value: float) -> str:
    """A length in cm as mm, to the micron an untrimmed lip needs, without trailing zeros"""
    return f'{value * 10:.3f}'.rstrip('0').rstrip('.')

def isDocumentInInches() -> bool:
    return app.activeProduct.unitsManager.defaultLengthUnits == 'in'

def inches(value: float) -> str:
    """A length in cm in inches, as Fusion shows them"""
    return app.activeProduct.unitsManager.formatInternalValue(value, 'in', True)

def update_actual_bin_dimensions():
    global actualDimensionsTableUiState
    try:
        clearance = commandUIState.getState(BIN_XY_CLEARANCE_INPUT_ID)
        actualWidth = commandUIState.getState(BIN_BASE_WIDTH_UNIT_INPUT_ID) * commandUIState.getState(BIN_WIDTH_INPUT_ID) - clearance * 2
        actualLength = commandUIState.getState(BIN_BASE_LENGTH_UNIT_INPUT_ID) * commandUIState.getState(BIN_LENGTH_INPUT_ID) - clearance * 2
        lip = lipHeight(commandUIState.getState(BIN_LIP_TOP_TRIMMED_INPUT_ID), clearance) if commandUIState.getState(BIN_WITH_LIP_INPUT_ID) else 0
        actualHeight = commandUIState.getState(BIN_HEIGHT_UNIT_INPUT_ID) * commandUIState.getState(BIN_HEIGHT_INPUT_ID) + lip
        for (inputId, inchesId, name, value) in [
            (BIN_REAL_DIMENSIONS_TABLE_TOTAL_WIDTH, BIN_REAL_DIMENSIONS_TABLE_TOTAL_WIDTH_INCHES, 'width', actualWidth),
            (BIN_REAL_DIMENSIONS_TABLE_TOTAL_LENGTH, BIN_REAL_DIMENSIONS_TABLE_TOTAL_LENGTH_INCHES, 'length', actualLength),
            (BIN_REAL_DIMENSIONS_TABLE_TOTAL_HEIGHT, BIN_REAL_DIMENSIONS_TABLE_TOTAL_HEIGHT_INCHES, 'height', actualHeight),
        ]:
            actualDimensionsTableUiState.updateValue(inputId, f'{name.capitalize()}: {millimeters(value)}mm')
            actualDimensionsTableUiState.getInput(inputId).tooltip = f'Total bin {name}: {millimeters(value)}mm'
            if isDocumentInInches():
                actualDimensionsTableUiState.updateValue(inchesId, inches(value))
                actualDimensionsTableUiState.getInput(inchesId).tooltip = f'Total bin {name}: {inches(value)}'
    except:
        showErrorInMessageBox()

def cullenectSockets() -> list[str]:
    """Socket and insert width of each Cullenect socket the bin gets, the same way binBuilder lays out the tabs"""
    return cullenect.socketSummary(*cullenectSocketLayout())

def cullenectTabWidth() -> float:
    """The width of the tab a Cullenect socket gets, widened from the one entered as binBuilder does (p32)"""
    overhangAngle = app.activeProduct.unitsManager.evaluateExpression(str(commandUIState.getState(BIN_TAB_ANGLE_INPUT_ID)), 'deg')
    return cullenect.effectiveTabWidth(
        commandUIState.getState(BIN_TAB_WIDTH_INPUT_ID),
        overhangAngle,
        tabFilletAllowance(overhangAngle, 0),
        commandUIState.getState(BIN_TAB_CULLENECT_OFFSET_INPUT_ID),
    )

def cullenectSocketLayout() -> tuple[list[float], float, float, float, float]:
    """The compartment widths that get a socket (0 for one too short), where the tab starts in them, its length, the
    base width and the socket play, as cullenect.socketSummary and socketCounts take them"""
    baseWidth: float = commandUIState.getState(BIN_BASE_WIDTH_UNIT_INPUT_ID)
    binWidth: float = commandUIState.getState(BIN_WIDTH_INPUT_ID)
    wallThickness: float = commandUIState.getState(BIN_WALL_THICKNESS_INPUT_ID)
    xyClearance: float = commandUIState.getState(BIN_XY_CLEARANCE_INPUT_ID)
    tabLengthUnits: float = commandUIState.getState(BIN_TAB_LENGTH_INPUT_ID)
    socketOffset: float = commandUIState.getState(BIN_TAB_CULLENECT_OFFSET_INPUT_ID)
    tabLength = baseWidth * max(0, min(tabLengthUnits, binWidth))
    if commandUIState.getState(BIN_TYPE_DROPDOWN_ID) == BIN_TYPE_SHELLED:
        # one tab along the back wall inside the shell
        interiorWidth = baseWidth * binWidth - (wallThickness + xyClearance) * 2
        return ([interiorWidth], 0, tabLength - (wallThickness + xyClearance) * 2, baseWidth, socketOffset)
    # creased bins are built with a single cavity whatever grid the dialog keeps, see binBuilder.buildBin
    creased = len(creaseLayout()) > 0
    columns = 1 if creased else commandUIState.getState(BIN_COMPARTMENTS_GRID_BASE_WIDTH_ID)
    rows = 1 if creased else commandUIState.getState(BIN_COMPARTMENTS_GRID_BASE_LENGTH_ID)
    pockets = compartmentLayout.normalizePockets(
        compartmentPockets if commandUIState.getState(BIN_COMPARTMENTS_SHOW_LAYOUT_ID) and not creased else [],
        columns,
        rows,
    )
    interiorWidth = baseWidth * binWidth - (wallThickness + xyClearance) * 2
    interiorLength = commandUIState.getState(BIN_BASE_LENGTH_UNIT_INPUT_ID) * commandUIState.getState(BIN_LENGTH_INPUT_ID) - (wallThickness + xyClearance) * 2
    widths = cullenect.compartmentWidths(interiorWidth, columns, [item['width'] for item in pockets], wallThickness)
    lengths = cullenect.compartmentWidths(interiorLength, rows, [item['length'] for item in pockets], wallThickness)
    tabWidth = cullenectTabWidth()
    # a compartment too short from front to back gets no socket, like one too narrow
    widths = [width if cullenect.socketFitsDepth(length, tabWidth, socketOffset) else 0 for (width, length) in zip(widths, lengths)]
    tabStart = baseWidth * max(0, min(commandUIState.getState(BIN_TAB_POSITION_INPUT_ID), binWidth - tabLengthUnits))
    return (widths, tabStart, tabLength, baseWidth, socketOffset)

def hasCullenectSockets() -> bool:
    return (
        commandUIState.getState(BIN_TAB_LABEL_STYLE_INPUT_ID) == labelGenerator.LABEL_STYLE_CULLENECT
        and commandUIState.getState(BIN_HAS_TAB_INPUT_ID)
        and commandUIState.getState(BIN_GENERATE_BODY_INPUT_ID)
        and commandUIState.getState(BIN_TYPE_DROPDOWN_ID) != BIN_TYPE_SOLID
        and not isShaped()
    )

def updateCullenectSockets():
    """Last row of the dimensions table, which inserts fit the sockets"""
    try:
        problem = cullenect.wallProblem(commandUIState.getState(BIN_WALL_THICKNESS_INPUT_ID)) if hasCullenectSockets() else None
        # the reason OK is locked, in place of the sockets (p35)
        text = f'Cullenect: {problem}' if problem is not None else f'Cullenect: {"; ".join(cullenectSockets())}' if hasCullenectSockets() else ''
        socketsInput = actualDimensionsTableUiState.getInput(BIN_REAL_DIMENSIONS_TABLE_CULLENECT)
        actualDimensionsTableUiState.updateValue(BIN_REAL_DIMENSIONS_TABLE_CULLENECT, text)
        socketsInput.tooltip = 'Socket width of the label tabs and the width of the Cullenect insert that fits them'
        socketsInput.isVisible = len(text) > 0
        table = socketsInput.parentCommandInput
        if isinstance(table, adsk.core.TableCommandInput):
            table.maximumVisibleRows = cullenect.dimensionsTableRows(isDocumentInInches(), len(text) > 0)
    except:
        showErrorInMessageBox()

def addIconItems(dropdown: adsk.core.DropDownCommandInput, firstItems: list[str], selected: str):
    """Icons show their preview, separated by type"""
    for name in firstItems:
        dropdown.listItems.add(name, name == selected)
    for group in labelGenerator.listIconGroups():
        dropdown.listItems.addSeparator(-1)
        for icon in group:
            dropdown.listItems.add(icon.name, icon.name == selected, icon.previewFolder)
    if dropdown.selectedItem is None:
        dropdown.listItems.item(0).isSelected = True

def fullCompartmentDepth() -> float:
    """Depth of a full depth compartment from the bin top in mm, as the generator builds it"""
    heightUnit: float = commandUIState.getState(BIN_HEIGHT_UNIT_INPUT_ID)
    binHeight: float = commandUIState.getState(BIN_HEIGHT_INPUT_ID)
    # see binBodyTopHeight
    bodyHeight = binHeight * heightUnit - const.BIN_BASE_HEIGHT if heightUnit >= const.BIN_BASE_HEIGHT else (binHeight - 1) * heightUnit
    return round((bodyHeight - const.BIN_COMPARTMENT_BOTTOM_THICKNESS) * 10, 2)

def normalizeCompartmentPockets():
    """Pockets fitted to the compartment grid, after it changes size"""
    global compartmentPockets
    compartmentPockets = compartmentLayout.normalizePockets(
        compartmentPockets,
        commandUIState.getState(BIN_COMPARTMENTS_GRID_BASE_WIDTH_ID),
        commandUIState.getState(BIN_COMPARTMENTS_GRID_BASE_LENGTH_ID),
    )

def compartmentCount() -> int:
    """Merged cells of a custom grid count as one compartment, as built: only while the layout is shown"""
    return len(compartmentLayout.normalizePockets(
        compartmentPockets if commandUIState.getState(BIN_COMPARTMENTS_SHOW_LAYOUT_ID) else [],
        commandUIState.getState(BIN_COMPARTMENTS_GRID_BASE_WIDTH_ID),
        commandUIState.getState(BIN_COMPARTMENTS_GRID_BASE_LENGTH_ID),
    ))

def hasSingleCompartment() -> bool:
    return compartmentCount() == 1

def updateTabHollowSidesInput(isTabEnabled: bool):
    """Side walls are only opened for a hollow tab of a single compartment, the option is cleared when it can't apply"""
    isEnabled = isTabEnabled and commandUIState.getState(BIN_TAB_HOLLOW_INPUT_ID) and hasSingleCompartment()
    commandUIState.getInput(BIN_TAB_HOLLOW_SIDES_INPUT_ID).isEnabled = isEnabled
    if not isEnabled:
        commandUIState.updateValue(BIN_TAB_HOLLOW_SIDES_INPUT_ID, False)

def compartmentIconOptions() -> list[dict]:
    """Label icons for the drawing, with the preview images the icon dropdowns show"""
    def option(name: str, group: str = '', previewFolder: str = '') -> dict:
        def image(fileName: str) -> str:
            path = os.path.join(previewFolder, fileName)
            return pathlib.Path(path).as_uri() if previewFolder and os.path.isfile(path) else ''
        return {'name': name, 'group': group, 'image': image('32x32.png'), 'imageDark': image('32x32-dark.png')}
    options = [option(compartmentLayout.DEFAULT_ICON), option(labelGenerator.LABEL_ICON_NONE)]
    for group in labelGenerator.listIconGroups():
        for icon in group:
            folder = os.path.dirname(icon.path)
            groupName = 'Other' if os.path.samefile(folder, labelGenerator.LABEL_ICONS_FOLDER) else os.path.basename(folder).capitalize()
            options.append(option(icon.name, groupName, icon.previewFolder))
    return options

def compartmentsDrawingData(browserId: str) -> dict:
    """Everything the compartments drawing shows, sizes in mm"""
    xyClearance: float = commandUIState.getState(BIN_XY_CLEARANCE_INPUT_ID)
    (cellWidth, cellLength, minCellSize) = compartmentCellSize()
    hasTab = commandUIState.getState(BIN_HAS_TAB_INPUT_ID) and commandUIState.getState(BIN_GENERATE_BODY_INPUT_ID) and commandUIState.getState(BIN_TYPE_DROPDOWN_ID) == BIN_TYPE_HOLLOW
    return {
        'page': COMPARTMENTS_PAGE_GRID if browserId == BIN_COMPARTMENTS_GRID_BROWSER_ID else COMPARTMENTS_PAGE_LAYOUT,
        'columns': commandUIState.getState(BIN_COMPARTMENTS_GRID_BASE_WIDTH_ID),
        'rows': commandUIState.getState(BIN_COMPARTMENTS_GRID_BASE_LENGTH_ID),
        'binWidth': round((commandUIState.getState(BIN_BASE_WIDTH_UNIT_INPUT_ID) * commandUIState.getState(BIN_WIDTH_INPUT_ID) - xyClearance * 2) * 10, 2),
        'binLength': round((commandUIState.getState(BIN_BASE_LENGTH_UNIT_INPUT_ID) * commandUIState.getState(BIN_LENGTH_INPUT_ID) - xyClearance * 2) * 10, 2),
        'cellWidth': cellWidth,
        'cellLength': cellLength,
        'minCellSize': minCellSize,
        'maxCells': GRID_CELLS_MAX,
        'fullDepth': fullCompartmentDepth(),
        'pockets': compartmentPockets,
        # the walls a compartment without its own scoops takes (round 48), without the tab's lock: the page locks
        # the back itself, a compartment's own copy keeps it for when the tab goes off (review round 48)
        'binScoops': sorted(binBuilder.binScoopSides(dataclasses.replace(getInputsState(), hasTab=False))),
        'hasTab': hasTab,
        'defaultLabel': commandUIState.getState(BIN_TAB_LABEL_TEXT_INPUT_ID),
        'defaultIcon': commandUIState.getState(BIN_TAB_LABEL_ICON_INPUT_ID),
        'icons': compartmentIconOptions(),
    }

def refreshCompartmentsDrawing(skipBrowserId: str = None):
    """Both compartment pages, but the one that is getting its answer already"""
    for browserId in [BIN_COMPARTMENTS_GRID_BROWSER_ID, BIN_COMPARTMENTS_BROWSER_ID]:
        if browserId != skipBrowserId:
            browserPages.sendUpdate(commandUIState.commandInputs.get(browserId), compartmentsDrawingData(browserId))

def isHalfGrid() -> bool:
    return commandUIState.getState(BIN_HALF_GRID_INPUT_ID)

def gridDivisions() -> int:
    return binBuilder.gridDivisions(getInputsState())

def feetSize() -> tuple[float, float]:
    return binBuilder.feetSize(getInputsState())

def feetGridSize() -> tuple[int, int]:
    return binBuilder.feetGridSize(getInputsState())

def outlineCellsPerFoot() -> int:
    return binBuilder.outlineCellsPerFoot(getInputsState())

def normalizeShapeCells():
    """Shape cells within the bin, every cell when the shape is first shown"""
    global binShapeCells
    (columns, rows) = feetGridSize()
    if not commandUIState.getState(BIN_SHAPE_CUSTOM_ID):
        binShapeCells = []
        return
    binShapeCells = binShape.normalizeShape(binShapeCells, columns, rows)
    if len(binShapeCells) == 0:
        binShapeCells = binShape.rectangle(columns, rows)

def shapeCells() -> list[tuple[int, int]]:
    return binBuilder.shapeCells(getInputsState())

def outlineCells() -> list[tuple[int, int]]:
    return binBuilder.outlineCells(getInputsState())

def isShaped() -> bool:
    return binBuilder.isShaped(getInputsState())

def shapeError() -> str | None:
    return binBuilder.shapeError(getInputsState())

def creaseLayout() -> list[tuple[wallCreases.WallSide, int]]:
    return binBuilder.creaseLayout(getInputsState())

def shapeDrawingData() -> dict:
    (columns, rows) = feetGridSize()
    return {
        'columns': columns,
        'rows': rows,
        # a half foot is drawn half as wide
        'columnSizes': [size for (_, size) in binGrid.footSpans(feetSize()[0])],
        'rowSizes': [size for (_, size) in binGrid.footSpans(feetSize()[1])],
        'cells': shapeCells(),
        'error': shapeError(),
        'note': SHAPE_NOTE if isShaped() else '',
    }

def refreshShapeDrawing():
    browserPages.sendUpdate(commandUIState.commandInputs.get(BIN_SHAPE_BROWSER_ID), shapeDrawingData())

def binLabelColor() -> str:
    """The label color of the dialog's state, see stateLabelColor"""
    return getInputsState().labelColor

def stateLabelColor(state: InputState) -> str:
    """The label color of a bin state built without one, '' where there is no label to color, a custom text that is no
    color as it is (see labelColors.dialogColor). Hollow and shelled bins both have labels on their tab (review round
    10: a shelled bin let an invalid color through). It takes the state rather than asking isShaped(): that builds the
    state again, which asked for this color, endless recursion that kept the bin dialog from opening (15.11.2026,
    see tests/test_dialog_state_calls.py)"""
    # whether there is a label comes from the state, only the color choice is the dialog's (review round 12: a state
    # of a config or rebuild differing from the inputs got the inputs' answer)
    color = labelColors.dialogColor(commandUIState.getState(BIN_TAB_LABEL_COLOR_INPUT_ID), commandUIState.getState(BIN_TAB_LABEL_CUSTOM_COLOR_INPUT_ID))
    return labelColors.labelColorFor(color, stateHasLabel(state), isCullenectState(state))

def stateHasLabel(state: InputState) -> bool:
    """Whether the bin of the state gets a tab label to color, see labelColors.binHasLabel"""
    return labelColors.binHasLabel(state.generateBody, state.hasTab, binBuilder.isShaped(state), state.binType == BIN_TYPE_SOLID)

def isCullenectState(state: InputState) -> bool:
    return state.labelStyle == labelGenerator.LABEL_STYLE_CULLENECT

def is_all_input_valid(inputs: adsk.core.CommandInputs):
    result = True
    base_width_unit: adsk.core.ValueCommandInput = inputs.itemById(BIN_BASE_WIDTH_UNIT_INPUT_ID)
    base_length_unit: adsk.core.ValueCommandInput = inputs.itemById(BIN_BASE_LENGTH_UNIT_INPUT_ID)

    height_unit: adsk.core.ValueCommandInput = inputs.itemById(BIN_HEIGHT_UNIT_INPUT_ID)
    xy_tolerance: adsk.core.ValueCommandInput = inputs.itemById(BIN_XY_CLEARANCE_INPUT_ID)
    bin_width: adsk.core.ValueCommandInput = inputs.itemById(BIN_WIDTH_INPUT_ID)
    bin_length: adsk.core.ValueCommandInput = inputs.itemById(BIN_LENGTH_INPUT_ID)
    bin_height: adsk.core.ValueCommandInput = inputs.itemById(BIN_HEIGHT_INPUT_ID)
    bin_wall_thickness: adsk.core.ValueCommandInput = inputs.itemById(BIN_WALL_THICKNESS_INPUT_ID)
    bin_screw_holes: adsk.core.BoolValueCommandInput = inputs.itemById(BIN_SCREW_HOLES_INPUT_ID)
    bin_magnet_cutouts: adsk.core.BoolValueCommandInput = inputs.itemById(BIN_MAGNET_CUTOUTS_INPUT_ID)
    bin_generate_base: adsk.core.BoolValueCommandInput = inputs.itemById(BIN_GENERATE_BASE_INPUT_ID)
    bin_generate_body: adsk.core.BoolValueCommandInput = inputs.itemById(BIN_GENERATE_BODY_INPUT_ID)
    bin_screw_hole_diameter: adsk.core.ValueCommandInput = inputs.itemById(BIN_SCREW_DIAMETER_INPUT)
    bin_magnet_cutout_diameter: adsk.core.ValueCommandInput = inputs.itemById(BIN_MAGNET_DIAMETER_INPUT)
    bin_magnet_cutout_depth: adsk.core.ValueCommandInput = inputs.itemById(BIN_MAGNET_HEIGHT_INPUT)
    with_lip: adsk.core.BoolValueCommandInput = inputs.itemById(BIN_WITH_LIP_INPUT_ID)
    with_lip_notches: adsk.core.BoolValueCommandInput = inputs.itemById(BIN_WITH_LIP_NOTCHES_INPUT_ID)
    binScoopMaxRadius: adsk.core.ValueCommandInput = inputs.itemById(BIN_SCOOP_MAX_RADIUS_INPUT_ID)
    hasTabInput: adsk.core.BoolValueCommandInput = inputs.itemById(BIN_HAS_TAB_INPUT_ID)
    binTabLength: adsk.core.ValueCommandInput = inputs.itemById(BIN_TAB_LENGTH_INPUT_ID)
    binTabWidth: adsk.core.ValueCommandInput = inputs.itemById(BIN_TAB_WIDTH_INPUT_ID)
    binTabPosition: adsk.core.ValueCommandInput = inputs.itemById(BIN_TAB_POSITION_INPUT_ID)
    binTabAngle: adsk.core.ValueCommandInput = inputs.itemById(BIN_TAB_ANGLE_INPUT_ID)
    binTypeDropdownInput: adsk.core.DropDownCommandInput = inputs.itemById(BIN_TYPE_DROPDOWN_ID)

    result = result and base_width_unit.value > 1
    result = result and base_length_unit.value > 1
    result = result and height_unit.value > 0.5
    result = result and xy_tolerance.value >= 0.01 and xy_tolerance.value <= 0.05
    result = result and bin_width.value > 0 and binGrid.isHalfStep(bin_width.value)
    result = result and bin_length.value > 0 and binGrid.isHalfStep(bin_length.value)
    result = result and bin_height.value >= 1
    result = result and bin_wall_thickness.value >= 0.04 and bin_wall_thickness.value <= 0.2
    if bin_generate_base.value:
        result = result and (not bin_screw_holes.value or bin_screw_hole_diameter.value > 0.1) and (not bin_magnet_cutouts.value or bin_screw_hole_diameter.value < bin_magnet_cutout_diameter.value)
        result = result and bin_magnet_cutout_depth.value > 0

    result = result and shapeError() is None
    # Cullenect only from 1.2 mm walls (p35), a loaded config and a rebuild open this dialog too
    if hasCullenectSockets():
        result = result and cullenect.wallProblem(bin_wall_thickness.value) is None
    result = result and labelColors.isColor(binLabelColor())
    if inputs.itemById(BIN_CREASES_INPUT_ID).value:
        result = result and inputs.itemById(BIN_CREASE_DEPTH_INPUT_ID).value > 0
        result = result and inputs.itemById(BIN_CREASE_MAX_PANEL_LENGTH_INPUT_ID).value > 0

    if bin_generate_body.value and binTypeDropdownInput.selectedItem.name == BIN_TYPE_HOLLOW:
        if anyScoopWall():
            result = result and binScoopMaxRadius.value > 0
        if hasTabInput.value:
            result = result and binTabLength.value > 0
            result = result and binTabWidth.value > 0
            result = result and binTabPosition.value >= 0
            result = result and binTabAngle.value >= math.radians(30) and binTabAngle.value <= math.radians(65)
            binTabTopAngle: adsk.core.ValueCommandInput = inputs.itemById(BIN_TAB_TOP_ANGLE_INPUT_ID)
            result = result and binTabTopAngle.value >= 0 and binTabTopAngle.value <= math.radians(45)
            socketOffset: adsk.core.ValueCommandInput = inputs.itemById(BIN_TAB_CULLENECT_OFFSET_INPUT_ID)
            result = result and socketOffset.value >= 0 and socketOffset.value <= 0.1

    return result

# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')
    global commandUIState
    global actualDimensionsTableUiState

    args.command.setDialogInitialSize(450, 500)
    global rebuildBodyToken
    global pendingRebuildBody
    global dialogInfo
    global dialogWorkflow
    dialogWorkflow = WORKFLOW_REBUILD if pendingRebuildBody is not None else WORKFLOW_CLONE if pendingConfig is not None else WORKFLOW_NEW
    loadedConfigs.clear()
    rebuildBodyToken = pendingRebuildBody.entityToken if pendingRebuildBody is not None else None
    rebuildName = pendingRebuildBody.name if pendingRebuildBody is not None else None
    pendingRebuildBody = None
    applyPendingConfig()

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs
    # Create a value input field and set the default using 1 unit of the default length unit.
    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits

    infoGroup = inputs.addGroupCommandInput(INFO_GROUP, 'Info')
    dialogInfo = infoText()
    if rebuildName is not None:
        dialogInfo = warningLine(f'<b>Rebuilding {html.escape(rebuildName)}</b> in place, features after it in the timeline are kept. '
            'Changing only what its parameters hold, like its height or label, sets them instead.') + dialogInfo
    addInfoPage(infoGroup.children, INFO_BROWSER)
    infoGroup.isExpanded = commandUIState.getState(INFO_GROUP)
    commandUIState.registerCommandInput(infoGroup)

    # Where the bin goes (round 38): upstream's snap or center (d37c166) as Position, always, and a cell of a baseplate
    # or box (round 31, p312), only offered when there's one and not for a rebuilt bin, it keeps its joint. The cell is
    # neither remembered nor in the settings, a picked one wins, see binCell.placementSource
    placementGroup = inputs.addGroupCommandInput(BIN_PLACEMENT_GROUP_ID, 'Placement')
    placementGroup.isExpanded = True
    if binCell.offersCellPick(dialogWorkflow != WORKFLOW_REBUILD, binBuilder.hasCellParts(adsk.fusion.Design.cast(app.activeProduct))):
        cellInput = placementGroup.children.addSelectionInput(BIN_CELL_INPUT_ID, 'Cell', 'A cell joint origin of a baseplate or of the floor of a box')
        cellInput.addSelectionFilter(adsk.core.SelectionCommandInput.JointOrigins)
        cellInput.setSelectionLimits(0, 1)
        cellInput.tooltip = ('Optional: pick a cell joint origin of a baseplate or of the floor of a box, the bin is jointed there '
            'with its front left cell. Without, it goes beside the other bins. Baseplates offer their cells with Add joint '
            'origins, a box without cell joint origins gets them when it is rebuilt.')
    placementInput = placementGroup.children.addDropDownCommandInput(BIN_PLACEMENT_INPUT_ID, 'Position', adsk.core.DropDownStyles.TextListDropDownStyle)
    placementInput.tooltip = ('Snaps the bin to the free grid spot closest to the origin, next to bins already there, or centers '
        'it on the origin. A centered bin is centered again when rebuilt. A picked cell wins, this is greyed out then')
    for option in binBuilder.PLACEMENT_OPTIONS:
        placementInput.listItems.add(option, option == commandUIState.getState(BIN_PLACEMENT_INPUT_ID))
    commandUIState.registerCommandInput(placementInput)

    basicSizesGroup = inputs.addGroupCommandInput(BIN_BASIC_SIZES_GROUP, 'Basic sizes')
    basicSizesGroup.isExpanded = commandUIState.getState(BIN_BASIC_SIZES_GROUP)
    commandUIState.registerCommandInput(basicSizesGroup)
    baseWidthUnitInput = basicSizesGroup.children.addValueInput(BIN_BASE_WIDTH_UNIT_INPUT_ID, 'Base width unit (mm)', defaultLengthUnits, adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_BASE_WIDTH_UNIT_INPUT_ID)))
    baseWidthUnitInput.minimumValue = const.BASE_UNIT_MIN
    baseWidthUnitInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(baseWidthUnitInput)
    baseLengthUnitInput = basicSizesGroup.children.addValueInput(BIN_BASE_LENGTH_UNIT_INPUT_ID, 'Base length unit (mm)', defaultLengthUnits, adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_BASE_LENGTH_UNIT_INPUT_ID)))
    baseLengthUnitInput.minimumValue = const.BASE_UNIT_MIN
    baseLengthUnitInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(baseLengthUnitInput)
    binHeightUnitInput = basicSizesGroup.children.addValueInput(BIN_HEIGHT_UNIT_INPUT_ID, 'Bin height unit (mm)', defaultLengthUnits, adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_HEIGHT_UNIT_INPUT_ID)))
    binHeightUnitInput.minimumValue = const.HEIGHT_UNIT_MIN
    binHeightUnitInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(binHeightUnitInput)
    xyClearanceInput = basicSizesGroup.children.addValueInput(BIN_XY_CLEARANCE_INPUT_ID, 'Bin xy clearance (mm)', defaultLengthUnits, adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_XY_CLEARANCE_INPUT_ID)))
    xyClearanceInput.minimumValue = 0.01
    xyClearanceInput.isMinimumInclusive = True
    xyClearanceInput.maximumValue = 0.05
    xyClearanceInput.isMaximumInclusive = True
    commandUIState.registerCommandInput(xyClearanceInput)

    binDimensionsGroup = inputs.addGroupCommandInput(BIN_DIMENSIONS_GROUP, 'Main dimensions')
    binDimensionsGroup.tooltipDescription = 'Set in base units'
    binDimensionsGroup.isExpanded = commandUIState.getState(BIN_DIMENSIONS_GROUP)
    commandUIState.registerCommandInput(binDimensionsGroup)
    binWidthInput = binDimensionsGroup.children.addFloatSpinnerCommandInput(BIN_WIDTH_INPUT_ID, 'Bin width, X (u)', '', 0.5, 100, 0.5, commandUIState.getState(BIN_WIDTH_INPUT_ID))
    binWidthInput.tooltip = 'In whole or half base units'
    commandUIState.registerCommandInput(binWidthInput)
    binLengthInput = binDimensionsGroup.children.addFloatSpinnerCommandInput(BIN_LENGTH_INPUT_ID, 'Bin length, Y (u)', '', 0.5, 100, 0.5, commandUIState.getState(BIN_LENGTH_INPUT_ID))
    binLengthInput.tooltip = 'In whole or half base units'
    commandUIState.registerCommandInput(binLengthInput)
    halfGridInput = binDimensionsGroup.children.addBoolValueInput(BIN_HALF_GRID_INPUT_ID, 'Half grid', True, '', commandUIState.getState(BIN_HALF_GRID_INPUT_ID))
    halfGridInput.tooltip = ('Puts the bin on half size feet, for a half grid baseplate, the bin keeps its size in base units. '
        'Without it a size ending in a half gets whole feet and a row of half feet along the back or right side, halved across the row only. '
        'Half feet have no magnet or screw holes, there is no room for them')
    commandUIState.registerCommandInput(halfGridInput)
    binHeightInput = binDimensionsGroup.children.addValueInput(BIN_HEIGHT_INPUT_ID, 'Bin height, Z (u)', '', adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_HEIGHT_INPUT_ID)))
    binHeightInput.minimumValue = 1
    binHeightInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(binHeightInput)
    customShapeInput = binDimensionsGroup.children.addBoolValueInput(BIN_SHAPE_CUSTOM_ID, 'Custom shape', True, '', commandUIState.getState(BIN_SHAPE_CUSTOM_ID))
    customShapeInput.tooltip = 'Shows a drawing of the bin cells to leave some of them out, so the bin fills an L or another tetris like spot. Unticking it fills every cell again'
    commandUIState.registerCommandInput(customShapeInput)
    shapeBrowser = binDimensionsGroup.children.addBrowserCommandInput(BIN_SHAPE_BROWSER_ID, '', SHAPE_HTML_URL, 200, 200)
    shapeBrowser.isFullWidth = True
    shapeBrowser.isVisible = commandUIState.getState(BIN_SHAPE_CUSTOM_ID)
    commandUIState.registerCommandInput(shapeBrowser)
    render_actual_bin_dimensions_table(binDimensionsGroup.children)

    binFeaturesGroup = inputs.addGroupCommandInput(BIN_FEATURES_GROUP, 'Bin features')
    binFeaturesGroup.isExpanded = commandUIState.getState(BIN_FEATURES_GROUP)
    commandUIState.registerCommandInput(binFeaturesGroup)
    generateBodyCheckboxInput = binFeaturesGroup.children.addBoolValueInput(BIN_GENERATE_BODY_INPUT_ID, 'Generate body', True, '', commandUIState.getState(BIN_GENERATE_BODY_INPUT_ID))
    commandUIState.registerCommandInput(generateBodyCheckboxInput)
    binTypeDropdown = binFeaturesGroup.children.addDropDownCommandInput(BIN_TYPE_DROPDOWN_ID, 'Bin type', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
    binTypeDropdownDefaultValue = commandUIState.getState(BIN_TYPE_DROPDOWN_ID)
    binTypeDropdown.listItems.add(BIN_TYPE_HOLLOW, binTypeDropdownDefaultValue == BIN_TYPE_HOLLOW)
    binTypeDropdown.listItems.add(BIN_TYPE_SHELLED, binTypeDropdownDefaultValue == BIN_TYPE_SHELLED)
    binTypeDropdown.listItems.add(BIN_TYPE_SOLID, binTypeDropdownDefaultValue == BIN_TYPE_SOLID)
    commandUIState.registerCommandInput(binTypeDropdown)

    binWallThicknessInput = binFeaturesGroup.children.addValueInput(BIN_WALL_THICKNESS_INPUT_ID, 'Bin wall thickness', defaultLengthUnits, adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_WALL_THICKNESS_INPUT_ID)))
    binWallThicknessInput.minimumValue = 0.04
    binWallThicknessInput.isMinimumInclusive = True
    binWallThicknessInput.maximumValue = 0.2
    binWallThicknessInput.isMaximumInclusive = True
    commandUIState.registerCommandInput(binWallThicknessInput)
    generateLipCheckboxInput = binFeaturesGroup.children.addBoolValueInput(BIN_WITH_LIP_INPUT_ID, 'Generate lip for stackability', True, '', commandUIState.getState(BIN_WITH_LIP_INPUT_ID))
    commandUIState.registerCommandInput(generateLipCheckboxInput)
    hasLipNotches = binFeaturesGroup.children.addBoolValueInput(BIN_WITH_LIP_NOTCHES_INPUT_ID, 'Generate lip notches', True, '', commandUIState.getState(BIN_WITH_LIP_NOTCHES_INPUT_ID))
    hasLipNotches.isEnabled = commandUIState.getState(BIN_WITH_LIP_INPUT_ID)
    commandUIState.registerCommandInput(hasLipNotches)
    lipTypeInput = binFeaturesGroup.children.addDropDownCommandInput(BIN_LIP_TYPE_INPUT_ID, 'Lip type', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
    lipTypeInput.tooltip = ('Light keeps the inside of the lip straight down to the bin top. '
        'Full follows the original Gridfinity profile, narrowing to an inner tip with a support under it, and a scoop wall as thick as the tip')
    for lipType in LIP_TYPES:
        lipTypeInput.listItems.add(lipType, lipType == commandUIState.getState(BIN_LIP_TYPE_INPUT_ID), os.path.join(LIP_TYPE_ICON_FOLDER, lipType))
    commandUIState.registerCommandInput(lipTypeInput)
    lipTopTrimmedInput = binFeaturesGroup.children.addBoolValueInput(BIN_LIP_TOP_TRIMMED_INPUT_ID, 'Trim lip top', True, '', commandUIState.getState(BIN_LIP_TOP_TRIMMED_INPUT_ID))
    lipTopTrimmedInput.tooltip = 'Cuts the top of the lip flat, 0.6mm lower, instead of the sharp edge of the original profile'
    commandUIState.registerCommandInput(lipTopTrimmedInput)
    creasesInput = binFeaturesGroup.children.addBoolValueInput(BIN_CREASES_INPUT_ID, 'Fold long walls for stiffness', True, '', commandUIState.getState(BIN_CREASES_INPUT_ID))
    creasesInput.tooltip = ('Folds walls of hollow and shelled bins in along shallow creases, origami style, so tall long walls bow less. '
        'Bins from the min height with a wall from the min length get them. Walls are split into even panels up to the max panel length, '
        'walls shorter than a panel of the longest one stay flat. '
        'The scoop wall stays flat, the scoop braces it. A creased bin has a single compartment and a solid label tab')
    commandUIState.registerCommandInput(creasesInput)
    for (inputId, label, units, minimum) in [
        (BIN_CREASE_DEPTH_INPUT_ID, 'Crease depth', defaultLengthUnits, 0.05),
        (BIN_CREASE_MIN_LENGTH_INPUT_ID, 'Creased wall min length (u)', '', 1),
        (BIN_CREASE_MAX_PANEL_LENGTH_INPUT_ID, 'Crease panel max length (u)', '', 1),
        (BIN_CREASE_MIN_HEIGHT_INPUT_ID, 'Creased bin min height (u)', '', 1),
    ]:
        creaseValueInput = binFeaturesGroup.children.addValueInput(inputId, label, units, adsk.core.ValueInput.createByReal(commandUIState.getState(inputId)))
        creaseValueInput.minimumValue = minimum
        creaseValueInput.isMinimumInclusive = True
        commandUIState.registerCommandInput(creaseValueInput)

    compartmentsGroup: adsk.core.GroupCommandInput = inputs.addGroupCommandInput(BIN_COMPARTMENTS_GROUP_ID, 'Bin compartments')
    compartmentsGroup.isExpanded = commandUIState.getState(BIN_COMPARTMENTS_GROUP_ID)
    commandUIState.registerCommandInput(compartmentsGroup)
    compartmentsGridBrowser = compartmentsGroup.children.addBrowserCommandInput(BIN_COMPARTMENTS_GRID_BROWSER_ID, '', COMPARTMENTS_HTML_URL, 30, 30)
    compartmentsGridBrowser.isFullWidth = True
    commandUIState.registerCommandInput(compartmentsGridBrowser)
    showLayoutInput = compartmentsGroup.children.addBoolValueInput(BIN_COMPARTMENTS_SHOW_LAYOUT_ID, 'Edit compartment layout', True, '', commandUIState.getState(BIN_COMPARTMENTS_SHOW_LAYOUT_ID))
    showLayoutInput.tooltip = 'Shows a drawing of the compartment grid to merge cells into larger compartments and give each its own label and depth. Unticking it resets the compartments to the uniform grid'
    commandUIState.registerCommandInput(showLayoutInput)
    compartmentsBrowser = compartmentsGroup.children.addBrowserCommandInput(BIN_COMPARTMENTS_BROWSER_ID, '', COMPARTMENTS_HTML_URL, 270, 270)
    compartmentsBrowser.isFullWidth = True
    compartmentsBrowser.isVisible = commandUIState.getState(BIN_COMPARTMENTS_SHOW_LAYOUT_ID)
    commandUIState.registerCommandInput(compartmentsBrowser)
    # with the compartments it divides, the id stays so saved defaults keep the setting
    dividersToTopInput = compartmentsGroup.children.addBoolValueInput(BIN_DIVIDERS_TO_TOP_INPUT_ID, 'Dividers up to the top on grid lines', True, '', commandUIState.getState(BIN_DIVIDERS_TO_TOP_INPUT_ID))
    dividersToTopInput.tooltip = ('Compartment dividers lying on a grid line go up to the top of the lip and run out in its profile, '
        'the feet of a bin stacked on top have a groove there. Dividers between grid lines stay below the lip. '
        'Hollow bins with a lip and more than one compartment only')
    commandUIState.registerCommandInput(dividersToTopInput)

    binScoopGroup = compartmentsGroup.children.addGroupCommandInput(BIN_SCOOP_GROUP_ID, 'Scoop')
    binScoopGroup.isExpanded = commandUIState.getState(BIN_SCOOP_GROUP_ID)
    commandUIState.registerCommandInput(binScoopGroup)
    # one per wall (round 48, idea of upstream issue #140 by teateatea), every compartment gets a scoop at each
    for (inputId, title, tooltip) in [
        (BIN_HAS_SCOOP_INPUT_ID, 'Front (along bin width)', 'A scoop along the front wall of every compartment'),
        (BIN_HAS_SCOOP_BACK_INPUT_ID, 'Back (along bin width)', 'A scoop along the back wall of every compartment. Locked while the label tab is on, the tab sits on the back wall'),
        (BIN_HAS_SCOOP_LEFT_INPUT_ID, 'Left (along bin length)', 'A scoop along the left wall of every compartment'),
        (BIN_HAS_SCOOP_RIGHT_INPUT_ID, 'Right (along bin length)', 'A scoop along the right wall of every compartment'),
    ]:
        scoopWallInput = binScoopGroup.children.addBoolValueInput(inputId, title, True, '', commandUIState.getState(inputId))
        scoopWallInput.tooltip = tooltip
        commandUIState.registerCommandInput(scoopWallInput)
    binScoopMaxRadiusInput = binScoopGroup.children.addValueInput(BIN_SCOOP_MAX_RADIUS_INPUT_ID, 'Scoop max radius (mm)', defaultLengthUnits, adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_SCOOP_MAX_RADIUS_INPUT_ID)))
    commandUIState.registerCommandInput(binScoopMaxRadiusInput)
    binScoopMaxRadiusInput.isEnabled = anyScoopWall()

    binTabFeaturesGroup = compartmentsGroup.children.addGroupCommandInput(BIN_TAB_FEATURES_GROUP_ID, 'Label tab')
    binTabFeaturesGroup.isExpanded = commandUIState.getState(BIN_TAB_FEATURES_GROUP_ID)
    commandUIState.registerCommandInput(binTabFeaturesGroup)
    generateTabCheckboxinput = binTabFeaturesGroup.children.addBoolValueInput(BIN_HAS_TAB_INPUT_ID, 'Add label tab (along bin width)', True, '', commandUIState.getState(BIN_HAS_TAB_INPUT_ID))
    commandUIState.registerCommandInput(generateTabCheckboxinput)
    binTabLengthInput = binTabFeaturesGroup.children.addValueInput(BIN_TAB_LENGTH_INPUT_ID, 'Tab length (u)', '', adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_TAB_LENGTH_INPUT_ID)))
    commandUIState.registerCommandInput(binTabLengthInput)
    binTabWidthInput = binTabFeaturesGroup.children.addValueInput(BIN_TAB_WIDTH_INPUT_ID, 'Tab width (mm)', defaultLengthUnits, adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_TAB_WIDTH_INPUT_ID)))
    commandUIState.registerCommandInput(binTabWidthInput)
    binTabPostionInput = binTabFeaturesGroup.children.addValueInput(BIN_TAB_POSITION_INPUT_ID, 'Tab offset (u)', '', adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_TAB_POSITION_INPUT_ID)))
    commandUIState.registerCommandInput(binTabPostionInput)
    tabObverhangAngleInput = binTabFeaturesGroup.children.addValueInput(BIN_TAB_ANGLE_INPUT_ID, 'Tab overhang angle', 'deg', adsk.core.ValueInput.createByString(str(commandUIState.getState(BIN_TAB_ANGLE_INPUT_ID))))
    tabObverhangAngleInput.minimumValue = math.radians(30)
    tabObverhangAngleInput.isMinimumInclusive = True
    tabObverhangAngleInput.maximumValue = math.radians(65)
    tabObverhangAngleInput.isMaximumInclusive = True
    commandUIState.registerCommandInput(tabObverhangAngleInput)
    tabTopAngleInput = binTabFeaturesGroup.children.addValueInput(BIN_TAB_TOP_ANGLE_INPUT_ID, 'Tab top angle', 'deg', adsk.core.ValueInput.createByString(str(commandUIState.getState(BIN_TAB_TOP_ANGLE_INPUT_ID))))
    tabTopAngleInput.tooltip = 'Tilts the tab top down towards the front, so the label faces the front of the bin'
    tabTopAngleInput.minimumValue = 0
    tabTopAngleInput.isMinimumInclusive = True
    tabTopAngleInput.maximumValue = math.radians(45)
    tabTopAngleInput.isMaximumInclusive = True
    commandUIState.registerCommandInput(tabTopAngleInput)
    tabTopOffsetInput = binTabFeaturesGroup.children.addValueInput(BIN_TAB_TOP_OFFSET_INPUT_ID, 'Tab top offset (mm)', defaultLengthUnits, adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_TAB_TOP_OFFSET_INPUT_ID)))
    tabTopOffsetInput.tooltip = 'How far the tab is below the top of the bin, up to 2mm, the label goes down with it. Dividers between compartments are lowered as much'
    tabTopOffsetInput.minimumValue = 0
    tabTopOffsetInput.isMinimumInclusive = True
    tabTopOffsetInput.maximumValue = 0.2
    tabTopOffsetInput.isMaximumInclusive = True
    commandUIState.registerCommandInput(tabTopOffsetInput)
    tabHollowInput = binTabFeaturesGroup.children.addBoolValueInput(BIN_TAB_HOLLOW_INPUT_ID, 'Hollow tab', True, '', commandUIState.getState(BIN_TAB_HOLLOW_INPUT_ID))
    tabHollowInput.tooltip = 'Shells the tab with the wall thickness. With a single compartment it is opened through the back wall of the bin, with more compartments it is left closed. On by default for shelled bins'
    commandUIState.registerCommandInput(tabHollowInput)
    tabHollowSidesInput = binTabFeaturesGroup.children.addBoolValueInput(BIN_TAB_HOLLOW_SIDES_INPUT_ID, 'Open through side walls', True, '', commandUIState.getState(BIN_TAB_HOLLOW_SIDES_INPUT_ID))
    tabHollowSidesInput.tooltip = 'Also opens a hollow tab through the side walls of the bin where it runs into them, not only through the back wall. Only for a single compartment'
    commandUIState.registerCommandInput(tabHollowSidesInput)
    labelTextInput = binTabFeaturesGroup.children.addStringValueInput(BIN_TAB_LABEL_TEXT_INPUT_ID, 'Label text', commandUIState.getState(BIN_TAB_LABEL_TEXT_INPUT_ID))
    labelTextInput.tooltip = 'Text on every compartment label, compartments in the drawing above can have their own. Each label gets a text parameter to edit it later'
    commandUIState.registerCommandInput(labelTextInput)
    labelIconInput = binTabFeaturesGroup.children.addDropDownCommandInput(BIN_TAB_LABEL_ICON_INPUT_ID, 'Label icon', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
    addIconItems(labelIconInput, [labelGenerator.LABEL_ICON_NONE], commandUIState.getState(BIN_TAB_LABEL_ICON_INPUT_ID))
    commandUIState.registerCommandInput(labelIconInput)
    labelStyleInput = binTabFeaturesGroup.children.addDropDownCommandInput(BIN_TAB_LABEL_STYLE_INPUT_ID, 'Label style', adsk.core.DropDownStyles.TextListDropDownStyle)
    labelStyleInput.tooltip = 'Outline splits the tab face along the label so a slicer can color it, engraved cuts it in, embossed raises it from a lowered tab. Cullenect cuts a socket for exchangeable Cullenect label inserts (CullenJWebb) instead, the tab is widened to at least 14 mm and kept flat'
    for style in labelGenerator.LABEL_STYLES:
        labelStyleInput.listItems.add(style, style == commandUIState.getState(BIN_TAB_LABEL_STYLE_INPUT_ID))
    commandUIState.registerCommandInput(labelStyleInput)
    labelBoldInput = binTabFeaturesGroup.children.addBoolValueInput(BIN_TAB_LABEL_BOLD_INPUT_ID, 'Bold label text', True, '', commandUIState.getState(BIN_TAB_LABEL_BOLD_INPUT_ID))
    commandUIState.registerCommandInput(labelBoldInput)
    labelColorInput = binTabFeaturesGroup.children.addDropDownCommandInput(BIN_TAB_LABEL_COLOR_INPUT_ID, 'Label color', adsk.core.DropDownStyles.TextListDropDownStyle)
    labelColorInput.tooltip = 'Keeps the label as bodies of its own in this color, for printing it in another filament: raised letters are not joined to the bin, engraved and outline ones fill their cut flush. None joins or cuts them as before'
    labelColorChoice = commandUIState.getState(BIN_TAB_LABEL_COLOR_INPUT_ID)
    if labelColorChoice not in labelColors.CHOICES:
        labelColorChoice = labelColors.NO_COLOR_CHOICE
        commandUIState.updateValue(BIN_TAB_LABEL_COLOR_INPUT_ID, labelColorChoice)
    for choice in labelColors.CHOICES:
        labelColorInput.listItems.add(choice, choice == labelColorChoice)
    commandUIState.registerCommandInput(labelColorInput)
    labelCustomColorInput = binTabFeaturesGroup.children.addStringValueInput(BIN_TAB_LABEL_CUSTOM_COLOR_INPUT_ID, 'Custom label color', commandUIState.getState(BIN_TAB_LABEL_CUSTOM_COLOR_INPUT_ID))
    labelCustomColorInput.tooltip = '#rrggbb, e.g. #D02020'
    commandUIState.registerCommandInput(labelCustomColorInput)
    cullenectOffsetInput = binTabFeaturesGroup.children.addValueInput(BIN_TAB_CULLENECT_OFFSET_INPUT_ID, 'Socket play (mm)', defaultLengthUnits, adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_TAB_CULLENECT_OFFSET_INPUT_ID)))
    cullenectOffsetInput.tooltip = 'How much larger the Cullenect socket is than the insert, in width and height. 0.3 mm like Cullenect, the inserts themselves are made to size'
    cullenectOffsetInput.minimumValue = 0
    cullenectOffsetInput.isMinimumInclusive = True
    cullenectOffsetInput.maximumValue = 0.1
    cullenectOffsetInput.isMaximumInclusive = True
    commandUIState.registerCommandInput(cullenectOffsetInput)
    for input in binTabFeaturesGroup.children:
        if not input.id == BIN_HAS_TAB_INPUT_ID:
            input.isEnabled = commandUIState.getState(BIN_HAS_TAB_INPUT_ID)
    updateTabHollowSidesInput(commandUIState.getState(BIN_HAS_TAB_INPUT_ID))

    baseFeaturesGroup = inputs.addGroupCommandInput(BIN_BASE_FEATURES_GROUP_ID, 'Base interface features')
    baseFeaturesGroup.isExpanded = commandUIState.getState(BIN_BASE_FEATURES_GROUP_ID)
    commandUIState.registerCommandInput(baseFeaturesGroup)
    generateBaseCheckboxInput = baseFeaturesGroup.children.addBoolValueInput(BIN_GENERATE_BASE_INPUT_ID, 'Generate base', True, '', commandUIState.getState(BIN_GENERATE_BASE_INPUT_ID))
    commandUIState.registerCommandInput(generateBaseCheckboxInput)
    jointOriginsCheckboxInput = baseFeaturesGroup.children.addBoolValueInput(BIN_JOINT_ORIGINS_INPUT_ID, 'Add joint origins', True, '', commandUIState.getState(BIN_JOINT_ORIGINS_INPUT_ID))
    jointOriginsCheckboxInput.tooltip = 'A joint origin at the bottom center of every foot, to joint the bin into baseplate sockets'
    commandUIState.registerCommandInput(jointOriginsCheckboxInput)
    generateScrewHolesCheckboxInput = baseFeaturesGroup.children.addBoolValueInput(BIN_SCREW_HOLES_INPUT_ID, 'Add screw holes', True, '', commandUIState.getState(BIN_SCREW_HOLES_INPUT_ID))
    commandUIState.registerCommandInput(generateScrewHolesCheckboxInput)
    screwSizeInput = baseFeaturesGroup.children.addValueInput(BIN_SCREW_DIAMETER_INPUT, 'Screw hole diameter', defaultLengthUnits, adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_SCREW_DIAMETER_INPUT)))
    screwSizeInput.minimumValue = 0.1
    screwSizeInput.isMinimumInclusive = True
    screwSizeInput.maximumValue = 1
    screwSizeInput.isMaximumInclusive = True
    commandUIState.registerCommandInput(screwSizeInput)
    generateMagnetSocketCheckboxInput = baseFeaturesGroup.children.addBoolValueInput(BIN_MAGNET_CUTOUTS_INPUT_ID, 'Add magnet sockets', True, '', commandUIState.getState(BIN_MAGNET_CUTOUTS_INPUT_ID))
    commandUIState.registerCommandInput(generateMagnetSocketCheckboxInput)
    generateMagnetsTabCheckboxInput = baseFeaturesGroup.children.addBoolValueInput(BIN_MAGNET_CUTOUTS_TABS_INPUT_ID, 'Add tabs to magnet sockets', True, '', commandUIState.getState(BIN_MAGNET_CUTOUTS_TABS_INPUT_ID))
    commandUIState.registerCommandInput(generateMagnetsTabCheckboxInput)
    magnetDiameterInput = baseFeaturesGroup.children.addValueInput(BIN_MAGNET_DIAMETER_INPUT, 'Magnet cutout diameter', defaultLengthUnits, adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_MAGNET_DIAMETER_INPUT)))
    magnetDiameterInput.minimumValue = 0.1
    magnetDiameterInput.isMinimumInclusive = True
    magnetDiameterInput.maximumValue = 1
    magnetDiameterInput.isMaximumInclusive = True
    commandUIState.registerCommandInput(magnetDiameterInput)
    magnetSizeInput.addMagnetSizeInput(baseFeaturesGroup.children, BIN_MAGNET_SIZE_INPUT, commandUIState, magnetSizes.ALL_CHOICES)
    magnetHeightInput = baseFeaturesGroup.children.addValueInput(BIN_MAGNET_HEIGHT_INPUT, 'Magnet cutout depth', defaultLengthUnits, adsk.core.ValueInput.createByReal(commandUIState.getState(BIN_MAGNET_HEIGHT_INPUT)))
    magnetHeightInput.minimumValue = 0.1
    magnetHeightInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(magnetHeightInput)

    userChangesGroup = inputs.addGroupCommandInput(USER_CHANGES_GROUP_ID, 'Changes')
    userChangesGroup.isExpanded = commandUIState.getState(USER_CHANGES_GROUP_ID)
    commandUIState.registerCommandInput(userChangesGroup)
    addDefaultsButtonRow(userChangesGroup.children, INPUT_CHANGES_BUTTONS_BROWSER)
    addButtonRow(userChangesGroup.children, CONFIG_BUTTONS_BROWSER)

    previewGroup = inputs.addGroupCommandInput(PREVIEW_GROUP_ID, 'Preview')
    previewGroup.isExpanded = commandUIState.getState(PREVIEW_GROUP_ID)
    commandUIState.registerCommandInput(userChangesGroup)
    showPreviewCheckboxInput =  previewGroup.children.addBoolValueInput(SHOW_PREVIEW_INPUT, 'Show auto update preview (slow)', True, '', False)
    commandUIState.registerCommandInput(showPreviewCheckboxInput)
    showPreviewManual = previewGroup.children.addBoolValueInput(SHOW_PREVIEW_MANUAL_INPUT, 'Update preview once', False, '', False)
    showPreviewManual.isFullWidth = True
    commandUIState.registerCommandInput(showPreviewManual)
    # not registered with the dialog state, it's neither remembered nor part of the generated settings
    previewGroup.children.addTextBoxCommandInput(PREVIEW_TIME_INPUT, 'Last preview', 'None yet', 1, True)

    refreshUi()

    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)
    futil.add_handler(args.command.incomingFromHTML, command_incoming_from_html, local_handlers=local_handlers)
    futil.add_handler(args.command.select, command_select, local_handlers=local_handlers)

def command_select(args: adsk.core.SelectionEventArgs):
    """Only the cells of baseplates and box floors can be picked as the cell, see binBuilder.isCellJointOrigin"""
    if args.activeInput is None or args.activeInput.id != BIN_CELL_INPUT_ID:
        return
    args.isSelectable = binBuilder.isCellJointOrigin(adsk.fusion.JointOrigin.cast(args.selection.entity))

def updatePositionInput(inputs: adsk.core.CommandInputs):
    """Snap or center is greyed out while a cell is picked, the cell wins (round 38)"""
    positionInput = inputs.itemById(BIN_PLACEMENT_INPUT_ID)
    if positionInput is not None:
        positionInput.isEnabled = binCell.positionEnabled(selectedCell(inputs) is not None)

def selectedCell(inputs: adsk.core.CommandInputs) -> adsk.fusion.JointOrigin | None:
    """The cell picked for a new bin, none without the input (no baseplate or box, a rebuild) or a pick"""
    cellInput = adsk.core.SelectionCommandInput.cast(inputs.itemById(BIN_CELL_INPUT_ID))
    if cellInput is None or cellInput.selectionCount == 0:
        return None
    return adsk.fusion.JointOrigin.cast(cellInput.selection(0).entity)


# This event handler is called when the user clicks the OK button in the command dialog or
# is immediately called after the created event not command inputs were created for the dialog.
# the small notice after a part design was switched to hybrid, see designIntent.structurePlan
HYBRID_SWITCH_MESSAGE = designIntent.hybridSwitchMessage('bin')

def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    des = adsk.fusion.Design.cast(app.activeProduct)
    wasPart = des is not None and des.designIntent == adsk.fusion.DesignIntentTypes.PartDesignIntentType
    generateBin(args, False)
    # a new bin or baseplate switches a part design to hybrid for its component of its own, that can't be undone (round 13)
    if wasPart and des.designIntent == adsk.fusion.DesignIntentTypes.HybridDesignIntentType:
        ui.messageBox(HYBRID_SWITCH_MESSAGE, CMD_NAME)

# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs
    if is_all_input_valid(inputs):
        showPreview: adsk.core.BoolValueCommandInput = inputs.itemById(SHOW_PREVIEW_INPUT)
        showPreviewManual: adsk.core.BoolValueCommandInput = inputs.itemById(SHOW_PREVIEW_MANUAL_INPUT)
        if showPreview.value or showPreviewManual.value:
            startTime = time.perf_counter()
            isBuilt = generateBin(args, True)
            # OK keeps a valid preview instead of building again, a rebuild's preview is only a look at the new bin
            args.isValidResult = isBuilt and rebuildBodyToken is None
            showPreviewTime(inputs, time.perf_counter() - startTime, isBuilt)
            showPreviewManual.value = False
            commandUIState.onInputUpdate(showPreviewManual)
    else:
        args.executeFailed = True
        args.executeFailedMessage = "Some inputs are invalid, unable to generate preview"

def showPreviewTime(inputs: adsk.core.CommandInputs, seconds: float, isValid: bool):
    inputs.itemById(PREVIEW_TIME_INPUT).text = f'{seconds:.2f} s{textStyles.previewNote(textStyles.notes())}' if isValid else f'failed after {seconds:.2f} s'

def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs
    global commandUIState
    global compartmentPockets
    global binShapeCells
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')
    # the preview time is only shown, nothing follows from it
    if changed_input.id == PREVIEW_TIME_INPUT:
        return
    if changed_input.id == BIN_CELL_INPUT_ID:
        # args.inputs only holds the siblings of the changed input, the dialog inputs are on the command
        updatePositionInput(changed_input.parentCommand.commandInputs)
    commandUIState.onInputUpdate(changed_input)
    if changed_input.id == BIN_TYPE_DROPDOWN_ID:
        commandUIState.updateValue(BIN_TAB_HOLLOW_INPUT_ID, commandUIState.getState(BIN_TYPE_DROPDOWN_ID) == BIN_TYPE_SHELLED)
    elif changed_input.id == BIN_COMPARTMENTS_SHOW_LAYOUT_ID and not commandUIState.getState(BIN_COMPARTMENTS_SHOW_LAYOUT_ID):
        # back to the uniform grid, refreshUi fills it with single cells
        compartmentPockets = []
    elif changed_input.id == BIN_MAGNET_SIZE_INPUT:
        # 6x2 or 6x3 mm magnets set the depth, Custom leaves it to be typed (p263)
        magnetSizeInput.onMagnetSizeChanged(commandUIState, BIN_MAGNET_SIZE_INPUT, BIN_MAGNET_HEIGHT_INPUT)
    elif changed_input.id == BIN_HALF_GRID_INPUT_ID:
        # the drawn shape keeps its footprint in the cells of the other grid
        binShapeCells = binShape.splitCells(binShapeCells) if isHalfGrid() else binShape.mergeCells(binShapeCells)
    refreshUi()

    if isinstance(changed_input, adsk.core.GroupCommandInput) and changed_input.isExpanded == True:
        for input in changed_input.children:
            commandUIState.registerCommandInput(input)
        refreshUi()


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs

    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    args.areInputsValid = is_all_input_valid(inputs)
    futil.log(f'{CMD_NAME} Inputs are {"valid" if args.areInputsValid else "invalid"}')


# This event handler is called when the compartments drawing asks for its data once loaded or changes the pockets.
def command_incoming_from_html(args: adsk.core.HTMLEventArgs):
    browserPages.handleMessage(args, pageHandlers(args.browserCommandInput.id, args.browserCommandInput.parentCommand))

def pageHandlers(browserId: str, command: adsk.core.Command) -> dict[str, browserPages.Handler]:
    """What the pages of the dialog send, see browserPages.handleMessage"""
    def preview():
        if commandUIState.getInput(SHOW_PREVIEW_INPUT).value:
            command.doExecutePreview()

    def onDefaults(action: str):
        if action == DEFAULTS_SAVE:
            saveUIInputsAsDefaults()
            return
        if action == DEFAULTS_FACTORY_RESET:
            configUtils.deleteConfigFile(UI_INPUT_DEFAULTS_CONFIG_PATH)
        initDefaultUiState()
        refreshUi()
        preview()

    def onShape(cells):
        global binShapeCells
        binShapeCells = cells
        normalizeShapeCells()
        # scoop, tab and compartments inputs depend on the shape
        onChangeValidate()
        updateCullenectSockets()
        preview()
        # the page redraws from the answer, with the error of the shape it sent
        return shapeDrawingData()

    def onPockets(pockets):
        global compartmentPockets
        compartmentPockets = pockets
        normalizeCompartmentPockets()
        # merging cells changes how many compartments there are, which some inputs depend on
        onChangeValidate()
        updateCullenectSockets()
        preview()

    def onGrid(grid):
        try:
            for (inputId, key) in [(BIN_COMPARTMENTS_GRID_BASE_WIDTH_ID, 'columns'), (BIN_COMPARTMENTS_GRID_BASE_LENGTH_ID, 'rows')]:
                commandUIState.updateValue(inputId, max(1, min(GRID_CELLS_MAX, int(grid[key]))))
        except (ValueError, TypeError, KeyError) as err:
            futil.log(f'{CMD_NAME} Ignoring grid size from the drawing, {err}')
        normalizeCompartmentPockets()
        onChangeValidate()
        updateCullenectSockets()
        # the page that changed it redraws from the answer
        refreshCompartmentsDrawing(browserId)
        preview()
        return compartmentsDrawingData(browserId)

    def onLoadConfig(text: str, fileName: str):
        state = readConfig(text, f'Loaded "{fileName}"')
        if state is None:
            return
        loadedConfigs.append(fileName)
        applyInputsState(state)
        refreshUi()
        preview()

    if browserId == INFO_BROWSER:
        return infoPageHandlers(dialogInfo, command.commandInputs.itemById(INFO_BROWSER))
    if browserId == INPUT_CHANGES_BUTTONS_BROWSER:
        return defaultsButtonsHandlers(onDefaults)
    if browserId == CONFIG_BUTTONS_BROWSER:
        return configButtons.configButtonsHandlers(
            'bin',
            lambda: configJson.configText(configJson.GENERATOR_BIN, configJson.stateToJson(configJson.GENERATOR_BIN, getInputsState()), tagUtils.getGeneratorVersion()),
            lambda: binBuilder.binDisplayName(getInputsState()),
            onLoad=onLoadConfig,
        )
    if browserId == BIN_SHAPE_BROWSER_ID:
        return {browserPages.READY: lambda _: shapeDrawingData(), 'shape': onShape}
    return {browserPages.READY: lambda _: compartmentsDrawingData(browserId), 'pockets': onPockets, 'grid': onGrid}

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event "{args.terminationReason}"')
    global local_handlers
    global rebuildBodyToken
    local_handlers = []
    rebuildBodyToken = None
    if args.terminationReason == adsk.core.CommandTerminationReason.CompletedTerminationReason:
        # once the command is over, so the selection stays
        selection.showBuiltBodies(builtBodies)
        if len(rebuildNotes) > 0:
            ui.messageBox(
                'The bin was rebuilt. These features after it need a look, ones using a face or an edge of the old bin '
                'need them picked again:\n\n' + '\n'.join(rebuildNotes),
                CMD_NAME,
                adsk.core.MessageBoxButtonTypes.OKButtonType,
                adsk.core.MessageBoxIconTypes.WarningIconType,
            )
        # A label text fitted so small that a 0.4 mm nozzle leaves parts out (p130). Told here and not on execute: a
        # valid preview is kept on OK (isValidResult) and execute doesn't run then. The notes are those of the last
        # build, the preview kept or the execute. After the warning of a rebuild, which asks for action. A rebuild
        # that only sets parameters builds no label and notes nothing; one with a label text changed since the bin was
        # built builds it anew (round 19, see binBuilder.parameterEdits)
        hint = textStyles.hintText(textStyles.notes(), suggestHeavy=False, isBinLabel=True)
        if hint is not None:
            ui.messageBox(hint, CMD_NAME)

def onChangeValidate():
    global commandUIState

    generateBase: bool = commandUIState.getState(BIN_GENERATE_BASE_INPUT_ID)
    commandUIState.getInput(BIN_JOINT_ORIGINS_INPUT_ID).isEnabled = generateBase
    # half feet have no room for holes
    hasHoles = generateBase and not isHalfGrid()
    for inputId in [BIN_SCREW_HOLES_INPUT_ID, BIN_MAGNET_CUTOUTS_INPUT_ID, BIN_MAGNET_CUTOUTS_TABS_INPUT_ID, BIN_MAGNET_DIAMETER_INPUT, BIN_MAGNET_HEIGHT_INPUT, BIN_SCREW_DIAMETER_INPUT, BIN_MAGNET_SIZE_INPUT]:
        commandUIState.getInput(inputId).isEnabled = hasHoles
    commandUIState.getInput(BIN_MAGNET_HEIGHT_INPUT).isEnabled = hasHoles and magnetSizeInput.isDepthTyped(commandUIState, BIN_MAGNET_SIZE_INPUT)

    generateBody: bool = commandUIState.getState(BIN_GENERATE_BODY_INPUT_ID)
    binType: str = commandUIState.getState(BIN_TYPE_DROPDOWN_ID)
    # scoop and tab only follow a rectangle so far
    shaped = isShaped()
    commandUIState.getInput(BIN_WALL_THICKNESS_INPUT_ID).isEnabled = generateBody and not binType == BIN_TYPE_SOLID
    commandUIState.getInput(BIN_WITH_LIP_INPUT_ID).isEnabled = generateBody
    commandUIState.getInput(BIN_WITH_LIP_NOTCHES_INPUT_ID).isEnabled = generateBody
    commandUIState.getInput(BIN_LIP_TYPE_INPUT_ID).isEnabled = generateBody
    commandUIState.getInput(BIN_LIP_TOP_TRIMMED_INPUT_ID).isEnabled = generateBody
    for inputId in BIN_SCOOP_WALL_INPUT_IDS:
        commandUIState.getInput(inputId).isEnabled = not shaped
    # the label tab sits on the back wall, its scoop is locked while the tab is on, the value stays for later
    commandUIState.getInput(BIN_HAS_SCOOP_BACK_INPUT_ID).isEnabled = not shaped and not commandUIState.getState(BIN_HAS_TAB_INPUT_ID)
    commandUIState.getInput(BIN_HAS_TAB_INPUT_ID).isEnabled = generateBody and not shaped
    generateTab: bool = commandUIState.getState(BIN_HAS_TAB_INPUT_ID)
    for input in commandUIState.getInput(BIN_TAB_FEATURES_GROUP_ID).children:
        if not input.id == BIN_HAS_TAB_INPUT_ID:
            input.isEnabled = generateBody and generateTab and not shaped
    # a Cullenect socket takes no text, icon or tilted top, the values stay for when the style changes back
    labelInputs = cullenect.labelInputsEnabled(commandUIState.getState(BIN_TAB_LABEL_STYLE_INPUT_ID))
    for (key, inputId) in [
        ('text', BIN_TAB_LABEL_TEXT_INPUT_ID),
        ('icon', BIN_TAB_LABEL_ICON_INPUT_ID),
        ('bold', BIN_TAB_LABEL_BOLD_INPUT_ID),
        ('color', BIN_TAB_LABEL_COLOR_INPUT_ID),
        ('color', BIN_TAB_LABEL_CUSTOM_COLOR_INPUT_ID),
        ('topAngle', BIN_TAB_TOP_ANGLE_INPUT_ID),
        ('socketOffset', BIN_TAB_CULLENECT_OFFSET_INPUT_ID),
    ]:
        if not labelInputs[key]:
            commandUIState.getInput(inputId).isEnabled = False
    commandUIState.getInput(BIN_TAB_CULLENECT_OFFSET_INPUT_ID).isVisible = labelInputs['socketOffset']
    commandUIState.getInput(BIN_TAB_LABEL_CUSTOM_COLOR_INPUT_ID).isVisible = commandUIState.getState(BIN_TAB_LABEL_COLOR_INPUT_ID) == labelColors.CUSTOM_CHOICE
    creased = len(creaseLayout()) > 0
    if creased:
        # the folds would run into the hollow of the tab on the back wall
        commandUIState.getInput(BIN_TAB_HOLLOW_INPUT_ID).isEnabled = False
        commandUIState.updateValue(BIN_TAB_HOLLOW_INPUT_ID, False)
    updateTabHollowSidesInput(generateBody and generateTab and not shaped)

    generateLip: bool = commandUIState.getState(BIN_WITH_LIP_INPUT_ID)
    commandUIState.getInput(BIN_DIVIDERS_TO_TOP_INPUT_ID).isEnabled = raisedDividers.optionEnabled(
        generateBody, generateLip, binType == BIN_TYPE_HOLLOW, shaped, creased,
        compartmentCount(),
    )
    for inputId in [BIN_WITH_LIP_NOTCHES_INPUT_ID, BIN_LIP_TYPE_INPUT_ID, BIN_LIP_TOP_TRIMMED_INPUT_ID]:
        commandUIState.getInput(inputId).isEnabled = generateLip

    canCrease = generateBody and not binType == BIN_TYPE_SOLID
    commandUIState.getInput(BIN_CREASES_INPUT_ID).isEnabled = canCrease
    for inputId in [BIN_CREASE_DEPTH_INPUT_ID, BIN_CREASE_MIN_LENGTH_INPUT_ID, BIN_CREASE_MAX_PANEL_LENGTH_INPUT_ID, BIN_CREASE_MIN_HEIGHT_INPUT_ID]:
        commandUIState.getInput(inputId).isEnabled = canCrease and commandUIState.getState(BIN_CREASES_INPUT_ID)

    anyScoop = anyScoopWall()
    commandUIState.getInput(BIN_SCOOP_MAX_RADIUS_INPUT_ID).isEnabled = anyScoop and not shaped

    generateTab: bool = commandUIState.getState(BIN_HAS_TAB_INPUT_ID)
    commandUIState.getInput(BIN_TAB_LENGTH_INPUT_ID).isEnabled = generateTab and not shaped
    commandUIState.getInput(BIN_TAB_WIDTH_INPUT_ID).isEnabled = generateTab and not shaped
    commandUIState.getInput(BIN_TAB_ANGLE_INPUT_ID).isEnabled = generateTab and not shaped
    commandUIState.getInput(BIN_TAB_POSITION_INPUT_ID).isEnabled = generateTab and not shaped

    # shaped and creased bins have a single cavity, the compartments drawing is hidden but keeps its layout for later
    singleCavity = shaped or creased
    commandUIState.getInput(BIN_COMPARTMENTS_SHOW_LAYOUT_ID).isEnabled = not singleCavity
    commandUIState.getInput(BIN_COMPARTMENTS_GRID_BROWSER_ID).isVisible = not singleCavity
    commandUIState.getInput(BIN_COMPARTMENTS_BROWSER_ID).isVisible = commandUIState.getState(BIN_COMPARTMENTS_SHOW_LAYOUT_ID) and not singleCavity
    commandUIState.getInput(BIN_SHAPE_BROWSER_ID).isVisible = commandUIState.getState(BIN_SHAPE_CUSTOM_ID)

    showPreview: bool = commandUIState.getInput(SHOW_PREVIEW_INPUT).value
    commandUIState.getInput(SHOW_PREVIEW_MANUAL_INPUT).isVisible = not showPreview

def saveUIInputsAsDefaults():
    futil.log(f'{CMD_NAME} Saving UI state to file')
    result = configUtils.dumpJsonConfig(UI_INPUT_DEFAULTS_CONFIG_PATH, {
        'static_ui': commandUIState.toDict(ignoreKeys=[SHOW_PREVIEW_MANUAL_INPUT, SHOW_PREVIEW_INPUT]),
        'compartments': compartmentPockets,
        'shape': binShapeCells,
        })
    if result:
        futil.log(f'{CMD_NAME} Saved successfully')
    else:
        futil.log(f'{CMD_NAME} UI state failed to save')

def snapshotSettings(inputs: adsk.core.CommandInputs) -> list[dict]:
    # the cell isn't kept with the settings, the position is (round 38)
    settings = settingsUtils.snapshotInputs(
        inputs,
        [INFO_GROUP, USER_CHANGES_GROUP_ID, PREVIEW_GROUP_ID, BIN_REAL_DIMENSIONS_TABLE, BIN_CELL_INPUT_ID],
        SETTINGS_TITLE,
    )
    # the drawing isn't an input with a value, it holds the grid size too
    items = [['Grid', f'{commandUIState.getState(BIN_COMPARTMENTS_GRID_BASE_WIDTH_ID)} x {commandUIState.getState(BIN_COMPARTMENTS_GRID_BASE_LENGTH_ID)}']]
    if commandUIState.getState(BIN_COMPARTMENTS_SHOW_LAYOUT_ID) and compartmentLayout.isCustomized(compartmentPockets):
        items.extend([f'Compartment {index}', compartmentLayout.describe(item)] for (index, item) in enumerate(compartmentPockets, 1))
    settings.append({'title': 'Compartments', 'items': items})
    if hasCullenectSockets():
        # the dimensions table isn't kept, the insert widths are needed later to make inserts that fit
        # the tab as built, widened for the socket (p32), and each socket size with how many of it (p33)
        tabWidth = [['Label tab width', f'{round(cullenectTabWidth() * 10, 2):g} mm (built)']]
        settings.append({'title': 'Cullenect', 'items': tabWidth + cullenect.socketCounts(*cullenectSocketLayout())})
    if isShaped():
        # the drawing as text, front row last like it's shown
        cells = set(shapeCells())
        (columnCount, rowCount) = feetGridSize()
        rows = [
            ''.join('#' if (x, y) in cells else '.' for x in range(columnCount))
            for y in reversed(range(rowCount))
        ]
        settings.append({'title': 'Shape', 'items': [[f'Row {index}', row] for (index, row) in zip(reversed(range(1, len(rows) + 1)), rows)]})
    return settings

def reportConfig(state: InputState | None) -> str | None:
    """The settings of a failed build as a config file, to build it again from the report"""
    if state is None:
        return None
    return configJson.configText(configJson.GENERATOR_BIN, configJson.stateToJson(configJson.GENERATOR_BIN, state), tagUtils.getGeneratorVersion())

def buildWorkflow(isPreview: bool) -> str:
    """How the dialog came to build, like a clone's preview or the OK of a rebuild, with configs loaded into it"""
    loaded = f', loaded {", ".join(loadedConfigs)}' if len(loadedConfigs) > 0 else ''
    return f'{dialogWorkflow}{loaded}, {"preview" if isPreview else "OK"}'

def rebuiltConfig() -> str | None:
    """The config the bin being rebuilt was built with, from its tag, for the report of a failed rebuild"""
    if rebuildBodyToken is None:
        return None
    try:
        tag = tagUtils.readBodyTag(findRebuildBody(adsk.fusion.Design.cast(app.activeProduct)))
        if tag is None or not isinstance(tag[1].get('config'), dict):
            return None
        return configJson.configText(configJson.GENERATOR_BIN, tag[1]['config'], str(tag[1].get('generatorVersion') or ''))
    except Exception as err:
        futil.log(f'{CMD_NAME} config of the rebuilt bin not read, {err}')
        return None

def anyScoopWall() -> bool:
    """Whether a scoop wall is checked, the back one only counts without a label tab, see scoopSides"""
    return len(scoopSides.scoopSides(
        *[commandUIState.getState(inputId) for inputId in BIN_SCOOP_WALL_INPUT_IDS],
        hasTab=commandUIState.getState(BIN_HAS_TAB_INPUT_ID),
    )) > 0

def getInputsState() -> InputState:
    def angle(inputId: str) -> float:
        return app.activeProduct.unitsManager.evaluateExpression(str(commandUIState.getState(inputId)), 'deg')
    state = InputState(
        **{field: commandUIState.getState(inputId) for (field, inputId) in STATE_INPUT_IDS.items()},
        **{field: angle(inputId) for (field, inputId) in STATE_ANGLE_INPUT_IDS.items()},
        # filled in below from the finished state, see stateLabelColor; applyInputsState is the way back
        labelColor='',
        compartmentsX=commandUIState.getState(BIN_COMPARTMENTS_GRID_BASE_WIDTH_ID),
        compartmentsY=commandUIState.getState(BIN_COMPARTMENTS_GRID_BASE_LENGTH_ID),
        showCompartmentsLayout=commandUIState.getState(BIN_COMPARTMENTS_SHOW_LAYOUT_ID),
        compartmentPockets=compartmentPockets,
        hasCustomShape=commandUIState.getState(BIN_SHAPE_CUSTOM_ID),
        shapeCells=binShapeCells,
    )
    return dataclasses.replace(state, labelColor=stateLabelColor(state))

def applyInputsState(state: InputState):
    """Sets the dialog state to a state from getInputsState, the inputs follow on refreshUi"""
    global compartmentPockets
    global binShapeCells
    for (field, inputId) in STATE_INPUT_IDS.items():
        commandUIState.setValue(inputId, getattr(state, field))
    for (field, inputId) in STATE_ANGLE_INPUT_IDS.items():
        commandUIState.setValue(inputId, angleExpression(getattr(state, field)))
    commandUIState.setValue(BIN_COMPARTMENTS_GRID_BASE_WIDTH_ID, state.compartmentsX)
    commandUIState.setValue(BIN_COMPARTMENTS_GRID_BASE_LENGTH_ID, state.compartmentsY)
    commandUIState.setValue(BIN_COMPARTMENTS_SHOW_LAYOUT_ID, state.showCompartmentsLayout)
    commandUIState.setValue(BIN_SHAPE_CUSTOM_ID, state.hasCustomShape)
    # the way back of binLabelColor, a color of none of the named ones goes into the custom text
    if labelColors.restoresColor(state.labelColor, stateHasLabel(state), isCullenectState(state)):
        (colorChoice, customColor) = labelColors.choiceOf(state.labelColor)
        commandUIState.setValue(BIN_TAB_LABEL_COLOR_INPUT_ID, colorChoice)
        commandUIState.setValue(BIN_TAB_LABEL_CUSTOM_COLOR_INPUT_ID, customColor)
    compartmentPockets = list(state.compartmentPockets)
    binShapeCells = list(state.shapeCells)
    # only the depth is saved, the magnet size shown is read back from it (p263)
    magnetSizeInput.syncMagnetSize(commandUIState, BIN_MAGNET_SIZE_INPUT, BIN_MAGNET_HEIGHT_INPUT, magnetSizes.ALL_CHOICES)

def angleExpression(angle: float) -> str:
    """An angle in radians as the dialog keeps it, see STATE_ANGLE_INPUT_IDS"""
    return f'{math.degrees(angle):g} deg'

def startWithConfig(settings: dict):
    """Opens the dialog with the config of a body's tag by field name, see configJson.stateToJson and readConfig"""
    global pendingConfig
    pendingConfig = settings
    ui.commandDefinitions.itemById(CMD_ID).execute()

def startRebuild(body: adsk.fusion.BRepBody, tag: dict):
    """
    Opens the dialog with the settings of the bin the body is of, its tag value, to rebuild it in place, see
    binBuilder.rebuildBin. Its parameters may have been changed since, their values replace the settings
    """
    global pendingRebuildBody
    design = adsk.fusion.Design.cast(app.activeProduct)
    settings = binBuilder.configWithParameters(tag['config'], tag.get('parameters'), design.userParameters.itemByName)
    pendingRebuildBody = body
    startWithConfig(settings)

def findRebuildBody(design: adsk.fusion.Design) -> adsk.fusion.BRepBody:
    return rebuildUtils.findBodyByToken(design, rebuildBodyToken)

def configFileName(settings: dict) -> str:
    """The name a saved file of these settings starts with, as the dialog's Save to file names it"""
    defaults = configJson.stateToJson(configJson.GENERATOR_BIN, DEFAULT_STATE)
    known = {name: value for (name, value) in settings.items() if name in defaults}
    return binBuilder.binDisplayName(configJson.stateFromJson(configJson.GENERATOR_BIN, InputState, {**defaults, **known}))

def configChoices() -> dict[str, configJson.Choice]:
    """The options of the dropdowns with the dialog's first defaults, see initDefaultUiState"""
    iconNames = [labelGenerator.LABEL_ICON_NONE] + [icon.name for group in labelGenerator.listIconGroups() for icon in group]
    return {
        'binType': configJson.Choice([BIN_TYPE_HOLLOW, BIN_TYPE_SHELLED, BIN_TYPE_SOLID], DEFAULT_STATE.binType),
        'labelIcon': configJson.Choice(iconNames, DEFAULT_STATE.labelIcon),
        'labelStyle': configJson.Choice(labelGenerator.LABEL_STYLES, DEFAULT_STATE.labelStyle),
        'lipType': configJson.Choice(LIP_TYPES, DEFAULT_STATE.lipType),
        'placement': configJson.Choice(binBuilder.PLACEMENT_OPTIONS, DEFAULT_STATE.placement),
    }

def readConfig(text: str, source: str, isFromTag: bool = False) -> InputState | None:
    """The state of a config, none when it can't be read, see configButtons.readConfig"""
    # a setting the config doesn't have takes the value of the older models from configJson.OLDER_VALUES, the label
    # color '' among them (round 32, p280, which reverses p151 for it); one no older model lacked keeps the dialog's.
    # The label color of the state is derived, the dialog's choice is what a config with all settings is read over
    color = labelColors.configCurrentColor(commandUIState.getState(BIN_TAB_LABEL_COLOR_INPUT_ID), commandUIState.getState(BIN_TAB_LABEL_CUSTOM_COLOR_INPUT_ID))
    current = dataclasses.replace(getInputsState(), labelColor=color)
    return configButtons.readConfig(text, source, configJson.GENERATOR_BIN, InputState, current, configChoices(), isFromTag)

def applyPendingConfig():
    global pendingConfig
    if pendingConfig is None:
        return
    state = readConfig(configJson.configText(configJson.GENERATOR_BIN, pendingConfig), 'Rebuilding' if rebuildBodyToken is not None else 'Cloned', isFromTag=True)
    pendingConfig = None
    if state is not None:
        applyInputsState(state)

def generateBin(args: adsk.core.CommandEventArgs, isPreview: bool):
    startTime = time.perf_counter()
    settings = snapshotSettings(args.command.commandInputs)
    # the settings come first, so a failing build can be reproduced from the log
    commonUtils.fileLog(f'{CMD_NAME} generating, {buildWorkflow(isPreview)}, with settings:\n{settingsUtils.settingsText(settings)}')
    state = None
    global builtBodies
    global rebuildNotes
    builtBodies = []
    rebuildNotes = []
    # notes of an earlier build, a preview or a failed one, are not this one's
    textStyles.clearNotes()

    try:
        state = getInputsState()
        des = adsk.fusion.Design.cast(app.activeProduct)
        # the new bin's component is active while it's built, the one active before is again afterwards
        with commonUtils.keepActiveComponent(des):
            if rebuildBodyToken is not None:
                (builtBodies, rebuildNotes) = binBuilder.rebuildBin(des, findRebuildBody(des), state, settings, isPreview)
            else:
                builtBodies = binBuilder.buildBin(des, state, settings, mayChangeDocument=not isPreview, cell=selectedCell(args.command.commandInputs))
        futil.log(f'{CMD_NAME} {binBuilder.binDisplayName(state)} generated in {time.perf_counter() - startTime:.3f}s')
    except UnsupportedDesignTypeException as err:
        args.executeFailed = True
        args.executeFailedMessage = 'Design type is unsupported. Projects with disabled design history are unsupported, please enable timeline feature to proceed.'
        # a failed build has no label to hint at, like rebuildNotes it only keeps what a build that went through noted
        textStyles.clearNotes()
        return False
    except Exception as err:
        args.executeFailed = True
        textStyles.clearNotes()
        args.executeFailedMessage = f'{html.escape(errorReport.errorMessage(err))}<br>See the {errorPalette.PALETTE_TITLE} panel to copy a report of it'
        commonUtils.fileLog(f'{CMD_NAME} Error occurred, {err}, {getErrorMessage()}')
        errorPalette.show(f'{CMD_NAME} failed', err, reportConfig(state), buildWorkflow(isPreview), rebuiltConfig())
        return False
    return True
