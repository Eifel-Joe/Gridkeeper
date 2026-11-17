import adsk.core, adsk.fusion, traceback

# smallest units the dialogs accept
HEIGHT_UNIT_MIN = 0.5
BASE_UNIT_MIN = 1

BIN_XY_CLEARANCE = 0.025
BIN_CORNER_FILLET_RADIUS = 0.4

BIN_BASE_TOP_SECTION_HEIGH = 0.24
BIN_BASE_MID_SECTION_HEIGH = 0.18
BIN_BASE_BOTTOM_SECTION_HEIGH = 0.08
BIN_BASE_HEIGHT = BIN_BASE_TOP_SECTION_HEIGH + BIN_BASE_MID_SECTION_HEIGH + BIN_BASE_BOTTOM_SECTION_HEIGH
BIN_MAGNET_HOLE_GROOVE_DEPTH = 0.06

BIN_LIP_EXTRA_HEIGHT = 0.44
BIN_LIP_WALL_THICKNESS = BIN_BASE_TOP_SECTION_HEIGH - BIN_XY_CLEARANCE
BIN_LIP_TOP_RECESS_HEIGHT = 0.06
# straight part of the support under a full lip, from its inner tip down, see binBodyLipGenerator.createLipSupport
BIN_LIP_SUPPORT_WALL_HEIGHT = 0.12
BIN_WALL_THICKNESS = 0.12
BIN_CONNECTION_RECESS_DEPTH = 0.44
BIN_COMPARTMENT_BOTTOM_THICKNESS = 0.1
# compartment corners shrink with the wall thickness to stay concentric with the bin's down to this, the inside radius
# of the lip, so where the walls line up the corners run up into the lip without a step
BIN_BODY_CUTOUT_BOTTOM_FILLET_RADIUS = BIN_CORNER_FILLET_RADIUS - BIN_LIP_WALL_THICKNESS

BIN_TAB_WIDTH = 1.3
BIN_TAB_OVERHANG_ANGLE = 45
BIN_TAB_LABEL_ANGLE = 0
BIN_TAB_EDGE_FILLET_RADIUS = 0.06
BIN_TAB_TOP_CLEARANCE = 0.05
BIN_LABEL_DEPTH = 0.05
# what an engraved label leaves of a hollow tab's top
BIN_TAB_HOLLOW_MIN_SKIN = 0.04
# outline walls are only there to split the tab face into regions a slicer can color
BIN_LABEL_OUTLINE_THICKNESS = 0.0001
BIN_LABEL_MARGIN = 0.1
# from the compartment walls or the tab ends
BIN_LABEL_SIDE_MARGIN = 0.18
BIN_LABEL_ICON_GAP = 0.18
# tallest letters and icon, as a share of the label height inside its margins, 7.9mm on a default tab
BIN_LABEL_TEXT_HEIGHT_RATIO = 0.79 / (BIN_TAB_WIDTH - BIN_LABEL_MARGIN * 2)

BIN_SCOOP_MAX_RADIUS = 2.5
# the scoop stops this far below the top of its compartment, so the corners above it keep their vertical edges at any
# depth. A scoop as deep as the compartment would take them, the corner fillets would lose their edges once a height
# change takes the scoop past the depth or back
BIN_SCOOP_TOP_MARGIN = 0.01

BASEPLATE_EXTRA_HEIGHT = 0.64
BASEPLATE_BIN_Z_CLEARANCE = 0.05
# how far a baseplate's edge stops short of the grid line, plates glued side by side leave twice it between them.
# Closer than bins are to each other
BASEPLATE_PLATE_EDGE_CLEARANCE = 0.005

DIMENSION_DEFAULT_WIDTH_UNIT = 4.2
DIMENSION_DEFAULT_HEIGHT_UNIT = 0.7
DIMENSION_SCREW_HOLES_OFFSET = 0.8
DIMENSION_SCREW_HOLE_DIAMETER = 0.3
DIMENSION_PLATE_CONNECTION_SCREW_HOLE_DIAMETER = 0.32
DIMENSION_PLATE_SCREW_HOLE_DIAMETER = 0.32
DIMENSION_SCREW_HEAD_CUTOUT_DIAMETER = 0.6
DIMENSION_SCREW_HEAD_CUTOUT_OFFSET_HEIGHT = 0.05
DIMENSION_MAGNET_CUTOUT_DIAMETER = 0.65
DIMENSION_MAGNET_CUTOUT_DEPTH = 0.24
DIMENSION_PRINT_HELPER_GROOVE_DEPTH = 0.03


DEFAULT_FILTER_TOLERANCE = 0.00001
# walls folded in for stiffness, see wallCreases
BIN_CREASE_DEPTH = 0.2
# in base units, about 120 mm and 200 mm with 42 mm feet
BIN_CREASE_MIN_LENGTH = 2.85
BIN_CREASE_MAX_PANEL_LENGTH = 4.75
# in height units, 70 mm with 7 mm units
BIN_CREASE_MIN_HEIGHT = 10

# Cullenect labels by CullenJWebb (MIT), https://github.com/CullenJWebb/Cullenect-Labels, Cullenect.scad d6dc0bb
# insert: 42 mm x units - 6 mm wide, 11 mm high, 1.2 mm thick
CULLENECT_LABEL_HEIGHT = 1.1
CULLENECT_LABEL_THICKNESS = 0.12
CULLENECT_WIDTH_REDUCTION = 0.6
# play of the insert in its socket, in X and Y
CULLENECT_SOCKET_OFFSET = 0.03
# latch around the insert, set in 0.2 mm from 0.2 mm to 0.8 mm height
CULLENECT_LATCH_INSET = 0.02
CULLENECT_LATCH_BOTTOM = 0.02
CULLENECT_LATCH_HEIGHT = 0.06
# ribs along both long sides of the socket, 0.2 mm above its floor
CULLENECT_RIB_WIDTH = 0.02
CULLENECT_RIB_HEIGHT = 0.04
CULLENECT_RIB_BOTTOM = 0.02
CULLENECT_CORNER_RADIUS = 0.05
# text and icons are two 0.2 mm layers, raised above or set into the insert: one layer printed incomplete with a
# 0.4 mm nozzle (Nutzer 15.11.2026, p130)
CULLENECT_MARKING_DEPTH = 0.04
# least material left around the socket on the tab top
CULLENECT_POCKET_MARGIN = 0.1
CULLENECT_MIN_TAB_WIDTH = 1.4
# the thinnest bin wall a Cullenect socket goes into, Nutzer 15.11.2026 (p35): "Standard fuer Cullenect ist 1,2mm. Dicker
# geht, duenner nicht."
CULLENECT_MIN_WALL_THICKNESS = 0.12
# sockets come in standard label widths, in steps of half a unit
CULLENECT_UNIT_STEP = 0.5
# insert of the label command: text from the left margin to a gap before the symbol. Fusion's text height is the
# height of the capitals, one line as tall as Cullenect's text(size = 5) in Open Sans, two lines stacked
CULLENECT_TEXT_MARGIN = 0.1
CULLENECT_ICON_GAP = 0.1
CULLENECT_TEXT_HEIGHT = 0.5
CULLENECT_TWO_LINE_TEXT_HEIGHT = 0.35
CULLENECT_LINE_GAP = 0.15
