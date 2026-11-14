"""
Cullenect label sockets on bin tabs: insert and socket sizes, the widest standard label a tab takes and the tab width
the socket needs. Plain math, no Fusion, lengths in cm and angles in radians.

Cullenect labels by CullenJWebb (MIT), https://github.com/CullenJWebb/Cullenect-Labels, dimensions from Cullenect.scad:
an insert is `label_width * units - 6` mm wide and 11 mm high, its socket `socket_offset` larger in X and Y.
"""

import math

from . import const


def labelWidth(units: float, baseWidth: float = const.DIMENSION_DEFAULT_WIDTH_UNIT, offsetX: float = 0) -> float:
    """Insert width for a label of `units` grid units, `offsetX` corrects for the printer"""
    return baseWidth * units - const.CULLENECT_WIDTH_REDUCTION + offsetX

def socketWidth(units: float, baseWidth: float, socketOffset: float) -> float:
    return labelWidth(units, baseWidth) + socketOffset

def socketHeight(socketOffset: float) -> float:
    return const.CULLENECT_LABEL_HEIGHT + socketOffset

def socketUnits(
    availableLength: float,
    baseWidth: float,
    socketOffset: float,
    margin: float = const.CULLENECT_POCKET_MARGIN,
) -> float | None:
    """Widest standard label, in steps of half a unit, whose socket fits the tab length with the margin on both ends.
    Standard widths keep original Cullenect inserts fitting compartment tabs too. None if not even half a unit fits"""
    units = None
    candidate = const.CULLENECT_UNIT_STEP
    while socketWidth(candidate, baseWidth, socketOffset) + 2 * margin <= availableLength + 1e-9:
        units = candidate
        candidate += const.CULLENECT_UNIT_STEP
    return units

def socketFrontInset(overhangAngle: float, filletAllowance: float) -> float:
    """How far the socket stays back from the tab front. Under an overhang the tab gets thinner towards its front, the
    socket floor keeps a skin above the overhang. `filletAllowance` is the tab profile widening for the rounded front
    edge, binBodyTabGenerator.tabFilletAllowance(overhangAngle, 0)"""
    depth = const.CULLENECT_LABEL_THICKNESS + const.BIN_TAB_HOLLOW_MIN_SKIN
    return max(const.CULLENECT_POCKET_MARGIN, depth * math.tan(overhangAngle) - filletAllowance)

def effectiveTabWidth(userTabWidth: float, overhangAngle: float, filletAllowance: float, socketOffset: float) -> float:
    """Tab width with a socket: wide enough for the socket and its margins, a wider tab of the user stays"""
    inset = socketFrontInset(overhangAngle, filletAllowance)
    return max(userTabWidth, const.CULLENECT_MIN_TAB_WIDTH, socketHeight(socketOffset) + 2 * inset)

def hollowTabWallThickness(wallThickness: float) -> float:
    """Top of a hollow tab with a socket, thick enough for the socket not to cut through"""
    return max(wallThickness, const.CULLENECT_LABEL_THICKNESS + const.BIN_TAB_HOLLOW_MIN_SKIN)

def tabSpanInCompartment(compartmentWidth: float, tabStart: float, tabLength: float) -> float:
    """Length of a tab inside its compartment, the tab is trimmed to the compartment"""
    return max(0, min(tabLength, compartmentWidth - tabStart))

def _mm(value: float) -> str:
    return f"{round(value * 10, 2):g}"

def describeSocket(units: float | None, baseWidth: float, socketOffset: float) -> str:
    """Socket and matching insert width, to make the insert for a compartment tab without measuring"""
    if units is None:
        return "too short for a Cullenect pocket"
    return f"{units:g}U: pocket {_mm(socketWidth(units, baseWidth, socketOffset))} mm, insert {_mm(labelWidth(units, baseWidth))} mm"
