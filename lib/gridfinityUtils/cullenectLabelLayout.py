"""
Layout of a Cullenect insert made by the label command: its size from grid units or a free width, where the text lines
and the symbol go. Plain math, no Fusion, lengths in cm.

Layout after cullenect_label_generate in Cullenect.scad by CullenJWebb (MIT), https://github.com/CullenJWebb/Cullenect-Labels:
text at the left, a screw at the right edge, a hardware symbol at the right with the margin it has to top and bottom.
"""

import os
from dataclasses import dataclass, field, replace

from . import const, cullenectCatalog

MIN_WIDTH = 1.0
MAX_WIDTH = 30.0
MAX_LINES = 2
# least height, the latch and the rounded corners need it, and least room left for text beside a symbol
MIN_HEIGHT = 0.5
MIN_TEXT_SPACE = 0.3
# largest correction of width and height, like a printer is off
MAX_OFFSET = 0.1


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


def labelLayout(width: float, height: float, iconSize: tuple[float, float] | None, isScrew: bool, lineCount: int) -> LabelLayout:
    """Where text and symbol go on an insert. A screw ends at the right edge like in Cullenect, other symbols keep the
    margin to the right they have to top and bottom. The text runs from the left margin to a gap before the symbol"""
    if lineCount < 0 or lineCount > MAX_LINES:
        raise ValueError(f'An insert takes up to {MAX_LINES} text lines')
    iconMaxX = None
    textMaxX = width - const.CULLENECT_TEXT_MARGIN
    if iconSize is not None:
        (iconWidth, iconHeight) = iconSize
        iconMaxX = width if isScrew else width - max(0, (height - iconHeight) / 2)
        textMaxX = iconMaxX - iconWidth - const.CULLENECT_ICON_GAP
    middle = height / 2
    if lineCount == 1:
        lineHeights = [const.CULLENECT_TEXT_HEIGHT]
        lineCenters = [middle]
    elif lineCount == 2:
        lineHeights = [const.CULLENECT_TWO_LINE_TEXT_HEIGHT] * 2
        pitch = const.CULLENECT_TWO_LINE_TEXT_HEIGHT + const.CULLENECT_LINE_GAP
        lineCenters = [middle + pitch / 2, middle - pitch / 2]
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
    )


def iconSize(iconPath: str, width: float, height: float, isScrew: bool = True) -> tuple[float, float]:
    """Size of the symbol on the insert, as large as its svg says like in Cullenect, scaled down to fit the height of
    the insert and its width. A screw ends at the right edge and keeps the margin at the left, other symbols keep the
    right margin of their gap to top and bottom too, which grows as they get smaller, see labelLayout"""
    (widthMm, heightMm) = cullenectCatalog.svgSize(iconPath)
    (iconWidth, iconHeight) = (widthMm / 10, heightMm / 10)
    margin = const.CULLENECT_TEXT_MARGIN
    scale = min(1, height / iconHeight, (width - margin) / iconWidth)
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
    return None


# share of the room for a line that stays free when its text is fitted (p84). The width is measured on the outlines of
# the letters, Fusion lays a text out by their advance, wider by the side bearings: Joerg's "Welle 6mm" was fitted to
# exactly 34 mm of outline and Fusion took it for longer than its box
TEXT_WIDTH_RESERVE = 0.05


def fittedLineHeight(lineHeight: float, measuredWidth: float, availableWidth: float) -> float:
    """Text height for a line measured `measuredWidth` wide at `lineHeight` to fit the available width, keeping
    TEXT_WIDTH_RESERVE of it free"""
    if measuredWidth <= 0 or availableWidth <= 0:
        return lineHeight
    return lineHeight * min(1, availableWidth * (1 - TEXT_WIDTH_RESERVE) / measuredWidth)


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
) -> str | None:
    """Why the dialog can't build the insert, none if it can. `isSymbolMissing`: a symbol was chosen but has no svg"""
    if abs(offsetX) > MAX_OFFSET + 1e-9 or abs(offsetY) > MAX_OFFSET + 1e-9:
        return f'Corrections are at most {MAX_OFFSET * 10:g} mm either way'
    if not validWidth(width):
        return f'An insert is {MIN_WIDTH * 10:g} to {MAX_WIDTH * 10:g} mm wide'
    if isSymbolMissing:
        return 'No svg for this symbol, see tools/cullenectIcons.py and tools/setScrewIcons.py'
    size = iconSize(iconPath, width, height, isScrew) if iconPath is not None else None
    return layoutProblem(labelLayout(width, height, size, isScrew, lineCount))
