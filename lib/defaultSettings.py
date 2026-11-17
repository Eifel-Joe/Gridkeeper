# The settings the generator dialogs start with before any saved defaults, in the config format of lib/configJson.py:
# every field of a generator's InputState by its name, lengths in mm and angles in degrees. Shape test cases only list
# the settings they change from these, so they're built the way a new bin is, see commandSnapshotTests/testCases.py.
# Kept free of Fusion imports so it can be unit tested

BIN = {
    'baseWidth': 42.0,
    'baseLength': 42.0,
    'heightUnit': 7.0,
    'xyClearance': 0.25,
    'binWidth': 2,
    'binLength': 3,
    'binHeight': 5,
    'isHalfGrid': False,
    'wallThickness': 1.2,
    'binType': 'Hollow',
    'isShellRounded': True,
    'generateBase': True,
    'generateBody': True,
    'hasJointOrigins': False,
    'hasScrewHoles': False,
    'screwHoleDiameter': 3.0,
    'hasMagnetCutouts': False,
    'hasMagnetCutoutsTabs': False,
    'magnetCutoutDiameter': 6.5,
    'magnetCutoutDepth': 2.4,
    'hasLip': True,
    'hasLipNotches': False,
    # dividers on grid lines go up into the lip, see raisedDividers
    'hasDividersToTop': False,
    'lipType': 'Light',
    'isLipTopTrimmed': True,
    'hasScoop': False,
    'scoopMaxRadius': 25.0,
    'hasTab': False,
    'tabLength': 1,
    'tabWidth': 13.0,
    'tabPosition': 0,
    'tabOverhangAngle': 45.0,
    # follows the bin type when it changes, shelled bins get hollow tabs
    'isTabHollow': False,
    'isTabOpenThroughSides': False,
    'tabTopAngle': 0.0,
    'labelText': '',
    'labelIcon': 'None',
    'labelStyle': 'Outline',
    'isLabelBold': True,
    # '#RRGGBB', empty for none, see labelColors
    'labelColor': '',
    # play of a Cullenect insert in its socket, like Cullenect, see cullenect
    'cullenectSocketOffset': 0.3,
    'compartmentsX': 1,
    'compartmentsY': 1,
    'showCompartmentsLayout': False,
    'compartmentPockets': [],
    'hasCustomShape': False,
    'shapeCells': [],
    # walls folded in for stiffness, see wallCreases
    'hasCreases': True,
    'creaseDepth': 2.0,
    # in base units, about 120 mm and 200 mm with 42 mm feet
    'creaseMinLength': 2.85,
    'creaseMaxPanelLength': 4.75,
    # in height units, 70 mm with 7 mm units
    'creaseMinHeight': 10,
}

BASEPLATE = {
    'baseWidth': 42.0,
    'baseLength': 42.0,
    'xyClearance': 0.25,
    'plateWidth': 2,
    'plateLength': 3,
    'plateType': 'Light',
    'hasMagnetSockets': True,
    'magnetSocketSize': 6.5,
    'magnetSocketDepth': 2.4,
    'hasScrewHoles': True,
    'screwHoleSize': 3.2,
    'screwHeadSize': 6.0,
    'hasPadding': False,
    'paddingLeft': 0.0,
    'paddingTop': 0.0,
    'paddingRight': 0.0,
    'paddingBottom': 0.0,
    'extraBottomThickness': 6.4,
    'verticalClearance': 0.5,
    'hasConnectionHoles': False,
    'connectionHoleSize': 3.2,
    'sizingMode': 'Fill area',
    'areaWidth': 400.0,
    'areaLength': 300.0,
    # how far a plate's edge stops short of the grid line, plates glued side by side leave twice it between them.
    # Closer than bins are to each other
    'plateEdgeClearance': 0.05,
    # a common bed size, of the Bambu Lab A1, P1 and X1, the bed dropdown starts on custom
    'bedWidth': 256.0,
    'bedLength': 256.0,
    'bedMargin': 5.0,
    'alignmentX': 'Center',
    'alignmentY': 'Center',
    'useHalfCells': True,
    'hasJointOrigins': False,
}

# a Cullenect insert of the label command, see commandCreateLabel/inputState.py
LABEL = {
    'baseWidth': 42.0,
    'useUnits': True,
    'widthUnits': 1,
    'freeWidth': 25.0,
    'offsetX': 0.0,
    'offsetY': 0.0,
    'line1': 'M3x10',
    'line2': '',
    # one of textStyles.STYLES, Heavy prints at 0.4 mm nozzles (round 11, p130)
    'textStyle': 'Heavy',
    'showScrew': True,
    'head': 'socket',
    'shaft': 'machine',
    'threads': 'full',
    'driver': 'hex',
    'flange': False,
    'security': False,
    'hardware': 'none',
    'surface': 'Embossed',
    'textColor': '',
}

# by generator, see configJson.GENERATOR_BIN
SETTINGS = {
    'bin': BIN,
    'baseplate': BASEPLATE,
    'label': LABEL,
}
