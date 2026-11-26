"""
Settings checks, names and joint origin places of the storage box after Pred (round 27, p260). Fusion-free, cm.
"""

from typing import NamedTuple

from . import const
from .predBox import PRED
from . import predBoxParts

MIN_GRID_X = 4
MIN_GRID_Y = 3
# Decided 16.11.2026: minimum height 6 for now. At 5 the holders reach the lid joint and Pred's chamfer there fails
# (dev-notes/plans/2026-11-16-runde-27.md, p264)
MIN_HEIGHT_U = 6
# Pred's magnet hole sits in a 2.8 mm pad, 0.2 mm of floor stays under it (decided 16.11.2026: 6x2 mm magnets only, custom up
# to 2.6 mm); the pad's radius is the magnet's plus 0.75 mm and fits into the cell corner up to 8.5 mm
MAGNET_DEPTH_MAX = 0.26
MAGNET_DIAMETER_MIN = 0.3
MAGNET_DIAMETER_MAX = 0.85
# Pred's magnet holes, the floor pads around them are this plus 1.5 mm wide
PRED_MAGNET_DIAMETER = 0.65


# the lid's top (round 30, p311, 18.11.2026): Pred's Gridfinity grid, or closed and flat, sturdier, the stacking
# tabs in its corners kept so boxes still stack ("Standard bleibt Raster")
LID_TOP_GRID = 'Grid'  # tr-value
LID_TOP_CLOSED = 'Closed'  # tr-value
LID_TOPS = (LID_TOP_GRID, LID_TOP_CLOSED)
DEFAULT_LID_TOP = LID_TOP_GRID


class BoxOptions(NamedTuple):
    hasMagnets: bool
    magnetDepth: float
    magnetDiameter: float
    lidTop: str


class LidTopFeatures(NamedTuple):
    """The steps of the cell grid that build the grid on top of the lid (predBoxGenerator.floorGrid)"""
    # Sweep1 cuts the sockets into the top of the lid as well as into the floor of the box
    socketsInTop: bool
    # Sweep4 hollows out the bin seats under the lid, they open up into the sockets
    hollowSeats: bool
    # #17 Extrude5 lowers the area inside the rim to the top of the cell ridges
    cellRidges: bool
    # #85 Chamfer16 on the edge of that lowered area
    ridgeChamfer: bool

# user parameter names after the numbered prefix, stored in user documents, keep them literal
PARAMETERS = ['baseWidth', 'baseLength', 'heightU']
# the label each parameter has in the settings window, the config field it is, see rebuildUtils.configWithParameters
PARAMETER_FIELDS = {'Width (units)': 'gridX', 'Length (units)': 'gridY', 'Height (units)': 'heightU'}

# the top of Pred's socket profile over the floor plane (z = 0), a bin's base reaches that far down from it, as the
# baseplate's sockets, see baseplateBuilder
CELL_JOINT_Z = 0.465 - const.BIN_BASE_HEIGHT

_EPS = 1e-9


def boxProblem(state) -> str | None:
    """Why the box can't be built with these settings, none if it can"""
    if state.gridX < MIN_GRID_X:
        return f'Width must be at least {MIN_GRID_X} units'
    if state.gridY < MIN_GRID_Y:
        return f'Length must be at least {MIN_GRID_Y} units'
    if state.heightU < MIN_HEIGHT_U:
        return f'Height must be at least {MIN_HEIGHT_U} units'
    # a defaults file or test case may hold a hinge no longer known, it broke the build halfway (review R28)
    if state.hinge not in predBoxParts.HINGES:
        return f"Unknown hinge {state.hinge}, pick one of {', '.join(predBoxParts.HINGES)}"
    if state.lidTop not in LID_TOPS:
        return f"Unknown lid top {state.lidTop}, pick one of {', '.join(LID_TOPS)}"
    if state.hasMagnets:
        if state.magnetDepth <= _EPS:
            return 'The magnet holes need a depth'
        if state.magnetDepth > MAGNET_DEPTH_MAX + _EPS:
            return f'Magnet holes deeper than {MAGNET_DEPTH_MAX * 10:g} mm would break through the floor'
        if not MAGNET_DIAMETER_MIN - _EPS <= state.magnetDiameter <= MAGNET_DIAMETER_MAX + _EPS:
            return f'The magnet diameter is {MAGNET_DIAMETER_MIN * 10:g} to {MAGNET_DIAMETER_MAX * 10:g} mm'
    return None



def boxOptions(state) -> BoxOptions:
    """
    The magnet settings the generator builds with. The floor pads grow with the magnet diameter, without magnets they
    keep Pred's size: a diameter left typed in (0 or 15 mm, not checked with the magnets off) broke the build or made
    the pads of a box without magnets other than Pred's (review R27)
    """
    diameter = state.magnetDiameter if state.hasMagnets else PRED_MAGNET_DIAMETER
    return BoxOptions(state.hasMagnets, state.magnetDepth, diameter, state.lidTop)


def lidTopFeatures(lidTop: str) -> LidTopFeatures:
    """
    Which steps of the grid on top the lid gets (spec 2026-11-18-r30-lid-closed, way A). A closed lid leaves all four
    out: its top stays one flat face on the body's top from rim to rim. Sweep2, the bin seats under the lid, stays for
    both, so the lid holds the bins as before. Sweep4 goes with the sockets: without them above it would leave a void
    closed on every side in each cell
    """
    grid = lidTop == LID_TOP_GRID
    return LidTopFeatures(socketsInTop=grid, hollowSeats=grid, cellRidges=grid, ridgeChamfer=grid)



def spinnerLimits(minimum: int, maximum: int, value: int) -> tuple[int, int]:
    """
    The limits of a size spinner that opens with this value: a rebuild takes the size parameters, which may have been
    set beyond the limits in Change Parameters; shown as they are, boxProblem names what's wrong (review R27)
    """
    return (max(1, min(minimum, value)), max(maximum, value))


def boxName(state) -> str:
    return f'Box {state.gridX}×{state.gridY}×{state.heightU}'


def cellCenters(gridX: int, gridY: int) -> list[tuple[int, int, float, float]]:
    """Column, row and the centre of each cell (cm), row by row from the front left"""
    first = PRED['margin'] + PRED['grid'] / 2
    return [(column, row, first + column * PRED['grid'], first + row * PRED['grid'])
            for row in range(gridY) for column in range(gridX)]
