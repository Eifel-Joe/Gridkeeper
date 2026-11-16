"""
Layout of a Cullenect insert made by the label command: its size from grid units or a free width, where the text lines
and the symbol go. Plain math, no Fusion, lengths in cm.

Layout after cullenect_label_generate in Cullenect.scad by CullenJWebb (MIT), https://github.com/CullenJWebb/Cullenect-Labels:
text at the left, a screw at the right edge, a hardware symbol at the right with the margin it has to top and bottom.
"""

import os
from dataclasses import dataclass, field, replace

from . import const, cullenectCatalog, textStyles

MIN_WIDTH = 1.0
MAX_WIDTH = 30.0
MAX_LINES = 2
# least height, the latch and the rounded corners need it, and least room left for text beside a symbol
MIN_HEIGHT = 0.5
MIN_TEXT_SPACE = 0.3
# largest correction of width and height, like a printer is off
MAX_OFFSET = 0.1
# Round 17, p140: debossed text and symbol are cut 0.4 mm deep, the whole top layer. Reaching the edge they cut the
# rim over the latch through, the 0.2 mm the top layer stands over it, and the insert no longer holds. Debossed the
# symbol keeps this far from the edge, one line of a 0.4 mm nozzle in all: the 0.2 mm overhang and 0.2 mm over the
# latch. Flush and embossed
# don't cut the rim and stay as they are. Descenders of a lower line may still reach into it, see labelLayout
DEBOSS_RIM = const.CULLENECT_LATCH_INSET + 0.02


@dataclass
class LabelLayout:
    width: float
    height: float
    textMinX: float
    textMaxX: float
    # right edge of the symbol, None without one
    iconMaxX: float | None
    iconCenterY: float
    iconWidth: float = 0
    # cap heights of the text lines from the top, before they shrink to fit the width
    lineHeights: list[float] = field(default_factory=list)
    lineCenters: list[float] = field(default_factory=list)
    # largest height of the lines that keeps the descenders on the insert, see descenderLineHeight; None for any
    descenderLimit: float | None = None


def labelSize(units: float | None, freeWidth: float | None, baseWidth: float, offsetX: float, offsetY: float) -> tuple[float, float]:
    """Width and height of an insert of `units` grid units or `freeWidth`, the offsets correct for the printer on both"""
    if units is not None:
        width = baseWidth * units - const.CULLENECT_WIDTH_REDUCTION
    elif freeWidth is not None:
        width = freeWidth
    else:
        raise ValueError('An insert needs grid units or a width')
    return (width + offsetX, const.CULLENECT_LABEL_HEIGHT + offsetY)


def validWidth(width: float) -> bool:
    return MIN_WIDTH - 1e-9 <= width <= MAX_WIDTH + 1e-9


def movedLayout(layout: LabelLayout, offsetX: float, offsetY: float) -> LabelLayout:
    """The layout of an insert whose bottom left corner is at the offset instead of the origin"""
    return replace(
        layout,
        textMinX=layout.textMinX + offsetX,
        textMaxX=layout.textMaxX + offsetX,
        iconMaxX=layout.iconMaxX + offsetX if layout.iconMaxX is not None else None,
        iconCenterY=layout.iconCenterY + offsetY,
        lineCenters=[center + offsetY for center in layout.lineCenters],
    )


def descenderLineHeight(lineHeight: float, lowerCenter: float, rim: float, style: str) -> tuple[float, float]:
    """Height of two lines whose lower one stands centered at `lowerCenter` with its descenders (g, j, p, y) at least
    `rim` above the bottom edge (round 17, p110), and that limit. The baseline is under the middle by half the height,
    the descenders go DESCENT_FACTOR of it further down. The lines shrink to the limit, but not below the least height
    of their style (textStyles.minTextHeight): a 0.4 mm nozzle leaves thinner strokes out. Text below that already
    stays as it is. Where the limit is lower, layoutProblem tells. Taken whatever the text, a text parameter can change it later"""
    limit = (lowerCenter - rim) / (0.5 + textStyles.DESCENT_FACTOR)
    if limit >= lineHeight:
        return (lineHeight, limit)
    return (min(lineHeight, max(limit, textStyles.minTextHeight(style))), limit)


def labelLayout(
    width: float,
    height: float,
    iconSize: tuple[float, float] | None,
    isScrew: bool,
    lineCount: int,
    textStyle: str = textStyles.DEFAULT_INSERT_STYLE,
    rim: float = 0,
) -> LabelLayout:
    """Where text and symbol go on an insert. A screw ends at the right edge like in Cullenect, other symbols keep the
    margin to the right they have to top and bottom. The text runs from the left margin to a gap before the symbol.
    Two lines shrink to keep their descenders on the insert, see descenderLineHeight. `rim`: debossed the symbol keeps
    off the edges, see DEBOSS_RIM"""
    if lineCount < 0 or lineCount > MAX_LINES:
        raise ValueError(f'An insert takes up to {MAX_LINES} text lines')
    iconMaxX = None
    descenderLimit = None
    textMaxX = width - const.CULLENECT_TEXT_MARGIN
    if iconSize is not None:
        (iconWidth, iconHeight) = iconSize
        # a screw ends at the right edge, debossed at the rim; other symbols keep a margin like their gap to top and
        # bottom, which is at least the rim as they fit between the rims, see iconSize
        iconMaxX = width - rim if isScrew else width - max(0, (height - iconHeight) / 2)
        textMaxX = iconMaxX - iconWidth - const.CULLENECT_ICON_GAP
    middle = height / 2
    if lineCount == 1:
        lineHeights = [const.CULLENECT_TEXT_HEIGHT]
        lineCenters = [middle]
    elif lineCount == 2:
        # the line centers stay where they are, only the letters get smaller
        pitch = const.CULLENECT_TWO_LINE_TEXT_HEIGHT + const.CULLENECT_LINE_GAP
        lineCenters = [middle + pitch / 2, middle - pitch / 2]
        # to the bottom edge also when debossed: the rim is kept by the symbol only, as the spec says. Keeping it for
        # the descenders too was taken back (Hauptsitzung 15.11.2026), two debossed lines would no longer build in
        # Regular and Bold, Nutzer decides (round 17 hand-over)
        (lineHeight, descenderLimit) = descenderLineHeight(const.CULLENECT_TWO_LINE_TEXT_HEIGHT, lineCenters[1], 0, textStyle)
        lineHeights = [lineHeight] * 2
    else:
        lineHeights = []
        lineCenters = []
    return LabelLayout(
        width=width,
        height=height,
        textMinX=const.CULLENECT_TEXT_MARGIN,
        textMaxX=textMaxX,
        iconMaxX=iconMaxX,
        iconCenterY=middle,
        iconWidth=iconSize[0] if iconSize is not None else 0,
        lineHeights=lineHeights,
        lineCenters=lineCenters,
        descenderLimit=descenderLimit,
    )


def iconSize(iconPath: str, width: float, height: float, isScrew: bool = True, rim: float = 0) -> tuple[float, float]:
    """Size of the symbol on the insert, as large as its svg says like in Cullenect, scaled down to fit the height of
    the insert and its width. A screw ends at the right edge and keeps the margin at the left, other symbols keep the
    right margin of their gap to top and bottom too, which grows as they get smaller, see labelLayout. Debossed they stay
    `rim` off the edges, see DEBOSS_RIM"""
    (widthMm, heightMm) = cullenectCatalog.svgSize(iconPath)
    (iconWidth, iconHeight) = (widthMm / 10, heightMm / 10)
    margin = const.CULLENECT_TEXT_MARGIN
    scale = min(1, (height - 2 * rim) / iconHeight, (width - rim - margin) / iconWidth)
    if not isScrew and iconWidth > iconHeight / 2:
        # width - (height - scale * iconHeight) / 2 - scale * iconWidth >= margin
        scale = min(scale, (width - margin - height / 2) / (iconWidth - iconHeight / 2))
    return (iconWidth * scale, iconHeight * scale)


def layoutProblem(layout: LabelLayout) -> str | None:
    """Why the insert can't be built like this, none if it can"""
    if layout.height < MIN_HEIGHT - 1e-9:
        return f'An insert is at least {MIN_HEIGHT * 10:g} mm high'
    if layout.iconMaxX is not None and layout.iconMaxX - layout.iconWidth < const.CULLENECT_TEXT_MARGIN - 1e-9:
        return 'No room for the symbol, make the insert wider'
    if len(layout.lineHeights) > 0 and layout.textMaxX - layout.textMinX < MIN_TEXT_SPACE - 1e-9:
        return 'No room for text beside the symbol, make the insert wider'
    if layout.descenderLimit is not None and len(layout.lineHeights) > 0 and layout.lineHeights[0] > layout.descenderLimit + 1e-9:
        return "Two lines don't fit this height: their descenders would reach over the edge and the letters can't get smaller without getting too thin to print. Make the height correction smaller, use one line or the Heavy style"
    return None


# share of the room for a line that stays free when its text is fitted (p84). The width is measured on the outlines of
# the letters, Fusion lays a text out by their advance, wider by the side bearings: the user's "Welle 6mm" was fitted to
# exactly 34 mm of outline and Fusion took it for longer than its box
TEXT_WIDTH_RESERVE = 0.05


def fittedLineHeight(lineHeight: float, measuredWidth: float, availableWidth: float) -> float:
    """Text height for a line measured `measuredWidth` wide at `lineHeight` to fit the available width, keeping
    TEXT_WIDTH_RESERVE of it free"""
    if measuredWidth <= 0 or availableWidth <= 0:
        return lineHeight
    return lineHeight * min(1, availableWidth * (1 - TEXT_WIDTH_RESERVE) / measuredWidth)


# Round 17, p52: room kept free before the symbol when a text is fitted. The text is fitted once, when the insert is
# built; a width made smaller later moves the symbol to the left towards it. Up to this much narrower they don't touch,
# much narrower the insert is to be built anew. Without a symbol the text room stays (Hauptsitzung 15.11.2026: the
# spec names the symbol only, the right edge is collected for Nutzer)
SHRINK_ROOM = 0.1


def textFitWidth(layout: LabelLayout) -> float:
    """Width a text line is fitted to, see fittedLineHeight: its room, less SHRINK_ROOM before a symbol"""
    room = layout.textMaxX - layout.textMinX
    return room - SHRINK_ROOM if layout.iconMaxX is not None else room


def _mm(value: float) -> str:
    return f'{round(value * 10, 4):g} mm'


def _withOffset(expression: str, offset: float) -> str:
    if offset > 0:
        return f'{expression} + {_mm(offset)}'
    if offset < 0:
        return f'{expression} - {_mm(-offset)}'
    return expression


def widthExpression(units: float | None, freeWidth: float | None, baseWidthName: str | None, offsetX: float) -> str:
    """Expression of the width parameter of an insert: grid units follow the base width parameter like the bins do"""
    if units is not None:
        expression = f'{baseWidthName} * {units:g} - {_mm(const.CULLENECT_WIDTH_REDUCTION)}'
    else:
        expression = _mm(freeWidth)
    return _withOffset(expression, offsetX)


TITLE_TEXT_LENGTH = 20


def labelTitle(units: float | None, freeWidth: float | None, lines: list[str]) -> str:
    """Name of the component and timeline group of an insert, with the start of its first line"""
    size = f'{units:g}U' if units is not None else _mm(freeWidth)
    texts = [line.strip() for line in lines if len(line.strip()) > 0]
    text = ''
    if len(texts) > 0:
        text = ' ' + (texts[0] if len(texts[0]) <= TITLE_TEXT_LENGTH else texts[0][:TITLE_TEXT_LENGTH] + '…')
    return f'Gridfinity label {size}{text}'


def symbolChoice(folder: str, showScrew: bool, screw: tuple, hardware: str) -> tuple[str | None, bool]:
    """The svg of the chosen symbol and whether it's a screw. A screw goes first, a combination without a file gives
    no symbol, the hardware is the name of its svg without extension, 'none' for none"""
    if showScrew:
        return (cullenectCatalog.screwIconPath(folder, *screw), True)
    path = os.path.join(folder, cullenectCatalog.HARDWARE_FOLDER, f'{hardware}.svg')
    return (path if hardware != 'none' and os.path.isfile(path) else None, False)


def insertProblem(
    width: float,
    height: float,
    iconPath: str | None,
    isScrew: bool,
    isSymbolMissing: bool,
    lineCount: int,
    offsetX: float,
    offsetY: float,
    textStyle: str = textStyles.DEFAULT_INSERT_STYLE,
    isDebossed: bool = False,
) -> str | None:
    """Why the dialog can't build the insert, none if it can. `isSymbolMissing`: a symbol was chosen but has no svg"""
    if abs(offsetX) > MAX_OFFSET + 1e-9 or abs(offsetY) > MAX_OFFSET + 1e-9:
        return f'Corrections are at most {MAX_OFFSET * 10:g} mm either way'
    if not validWidth(width):
        return f'An insert is {MIN_WIDTH * 10:g} to {MAX_WIDTH * 10:g} mm wide'
    if isSymbolMissing:
        return 'No svg for this symbol, see tools/cullenectIcons.py and tools/setScrewIcons.py'
    rim = DEBOSS_RIM if isDebossed else 0
    size = iconSize(iconPath, width, height, isScrew, rim) if iconPath is not None else None
    return layoutProblem(labelLayout(width, height, size, isScrew, lineCount, textStyle, rim))


# --- an insert jointed into a pocket of a bin (round 13, p100, p160)

# shown in the label dialog, the insert isn't built then (Nutzer 15.11.2026: "Gar nichts. Hinweis, dass diese Tasche
# nicht passt und eine passende gewählt werden soll.")
POCKET_MISFIT = 'This pocket is too small for the insert, pick one that fits'

def insertFitsPocket(insertWidthMm: float, insertHeightMm: float, pocketWidthMm: float, pocketHeightMm: float) -> bool:
    """Whether the insert fits the pocket, in mm: an insert and a bin have base units of their own, and an insert may
    have a free width, so label units don't tell"""
    tolerance = 0.001
    return insertWidthMm <= pocketWidthMm + tolerance and insertHeightMm <= pocketHeightMm + tolerance
