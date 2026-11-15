"""
Cullenect label sockets on bin tabs: insert and socket sizes, the widest standard label a tab takes and the tab width
the socket needs. Plain math, no Fusion, lengths in cm and angles in radians.

Cullenect labels by CullenJWebb (MIT), https://github.com/CullenJWebb/Cullenect-Labels, dimensions from Cullenect.scad:
an insert is `label_width * units - 6` mm wide and 11 mm high, its socket `socket_offset` larger in X and Y.
"""

import json
import math

from . import const, cullenectLabelLayout

# the label style of labelGenerator.LABEL_STYLE_CULLENECT, kept here so this module needs no Fusion
LABEL_STYLE = 'Cullenect'


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

def wallProblem(wallThickness: float) -> str | None:
    """Why a bin with these walls takes no Cullenect socket, none if it does (p35). A wall entered as 1.2 mm may come back
    a hair under it from the units, so the check has a tolerance"""
    if wallThickness < const.CULLENECT_MIN_WALL_THICKNESS - 1e-6:
        return f'Cullenect sockets need walls of at least {const.CULLENECT_MIN_WALL_THICKNESS * 10:g} mm'
    return None

def hollowTabWallThickness(wallThickness: float) -> float:
    """Top of a hollow tab with a socket, thick enough for the socket not to cut through"""
    return max(wallThickness, const.CULLENECT_LABEL_THICKNESS + const.BIN_TAB_HOLLOW_MIN_SKIN)

def tabSpanInCompartment(compartmentWidth: float, tabStart: float, tabLength: float) -> float:
    """Length of a tab inside its compartment, the tab is trimmed to the compartment"""
    return max(0, min(tabLength, compartmentWidth - tabStart))

def compartmentWidths(interiorWidth: float, columns: int, pocketWidths: list[int], wallThickness: float) -> list[float]:
    """Widths of compartments spanning the given numbers of grid columns, the interior split like the bin body does"""
    cell = (interiorWidth - wallThickness * (columns - 1)) / columns
    return [cell * width + wallThickness * (width - 1) for width in pocketWidths]

def socketFitsDepth(
    compartmentLength: float,
    tabWidth: float,
    socketOffset: float,
    margin: float = const.CULLENECT_POCKET_MARGIN,
) -> bool:
    """Whether the socket, in the middle of a tab along the back wall, keeps the margin to the compartment front. A tab
    wider than a short compartment would put the socket into the divider in front"""
    return tabWidth / 2 + socketHeight(socketOffset) / 2 + margin <= compartmentLength + 1e-9

def _mm(value: float) -> str:
    return f"{round(value * 10, 2):g}"

def describeSocket(units: float | None, baseWidth: float, socketOffset: float) -> str:
    """Socket and matching insert width, to make the insert for a compartment tab without measuring"""
    if units is None:
        return "too short for a Cullenect pocket"
    return f"{units:g}U: pocket {_mm(socketWidth(units, baseWidth, socketOffset))} mm, insert {_mm(labelWidth(units, baseWidth))} mm"

def socketSummary(
    compartmentWidths: list[float],
    tabStart: float,
    tabLength: float,
    baseWidth: float,
    socketOffset: float,
) -> list[str]:
    """Each socket size of the bin once, smallest first, for the tabs of compartments of the given widths. The tab starts
    `tabStart` into each compartment and is trimmed to it"""
    units = {
        socketUnits(tabSpanInCompartment(width, tabStart, tabLength), baseWidth, socketOffset)
        for width in compartmentWidths
    }
    return [describeSocket(item, baseWidth, socketOffset) for item in sorted(units, key=lambda item: -1 if item is None else item)]

def labelInputsEnabled(labelStyle: str) -> dict[str, bool]:
    """Which label tab inputs of the bin dialog apply to the style, a socket takes no text, icon or tilted top but its
    play. Inputs are only switched off, the values typed in stay for when the style changes back"""
    isCullenect = labelStyle == LABEL_STYLE
    return {
        'text': not isCullenect,
        'icon': not isCullenect,
        'bold': not isCullenect,
        'color': not isCullenect,
        'topAngle': not isCullenect,
        'socketOffset': isCullenect,
    }


# config fields of the bin grid a socket is fitted to when building, see binBuilder.parameterEdits
_SOCKET_GRID_FIELDS = ('baseWidth', 'baseLength')

def parameterEditKeepsSockets(isCullenect: bool, hasTab: bool, changed: list[str]) -> bool:
    """
    Whether setting the bin's parameters builds the same sockets a rebuild would. The number of socket units and
    whether a compartment is deep enough for a socket are worked out from the base units when building, a change of
    them is built again (review of round 12). Height changes move the socket along its expressions
    """
    if not (isCullenect and hasTab):
        return True
    return not any(name in _SOCKET_GRID_FIELDS for name in changed)


# --- joint origins of the pockets (round 13, p160): one on the floor of each pocket, the label command finds them by
# their tag and checks in mm whether an insert fits, inserts and bins have base units of their own

def pocketJointOriginName(compartmentIndex: int, compartmentCount: int) -> str:
    if compartmentCount == 1:
        return 'Pocket joint origin'
    return f'Compartment {compartmentIndex + 1} pocket joint origin'

def pocketSizeMm(units: float, baseWidth: float, socketOffset: float) -> tuple[float, float]:
    """Width and height of the pocket in mm"""
    return (round(socketWidth(units, baseWidth, socketOffset) * 10, 6), round(socketHeight(socketOffset) * 10, 6))

def pocketTagValue(widthMm: float, heightMm: float) -> str:
    return json.dumps({'widthMm': widthMm, 'heightMm': heightMm})

def readPocketTagValue(value: str) -> tuple[float, float] | None:
    """The pocket size in mm, none for a value that can't be read"""
    try:
        data = json.loads(value)
        width = data['widthMm']
        height = data['heightMm']
    except (ValueError, KeyError, TypeError):
        return None
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in (width, height)):
        return None
    return (float(width), float(height))

def pocketRemap(oldNames: list[str], newNames: list[str]) -> dict[str, str | None]:
    """The pocket of a rebuilt bin each old pocket's joint goes to, by name (they're named by compartment, see
    pocketJointOriginName), none where the new bin has no such pocket"""
    return {name: (name if name in newNames else None) for name in oldNames}

def pocketNames(origins: list[tuple[str, str | None]]) -> list[str]:
    """Names of the joint origins, as (name, value of their pocket tag or None), that are of a pocket. A rebuild moves
    over the joints of those only: a foot's joint onto a baseplate is the user's own, see rebuildUtils.repointJoints"""
    return [name for (name, value) in origins if value is not None and readPocketTagValue(value) is not None]

def pocketFitNote(jointName: str, pocketName: str, insertSizeMm: tuple[float, float], pocketSizeMm: tuple[float, float]) -> str | None:
    """What the rebuild notes when the insert jointed into a pocket no longer fits the rebuilt one, none when it fits"""
    if cullenectLabelLayout.insertFitsPocket(*insertSizeMm, *pocketSizeMm):
        return None
    return f'{jointName}: the insert doesn\'t fit the rebuilt {pocketName} any more, {insertSizeMm[0]:g} x {insertSizeMm[1]:g} mm into {pocketSizeMm[0]:g} x {pocketSizeMm[1]:g} mm'
