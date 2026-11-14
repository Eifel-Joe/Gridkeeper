"""
Layout of a Cullenect insert made by the label command: its size from grid units or a free width, where the text lines
and the symbol go. Plain math, no Fusion, lengths in cm.

Layout after cullenect_label_generate in Cullenect.scad by CullenJWebb (MIT), https://github.com/CullenJWebb/Cullenect-Labels:
text at the left, a screw at the right edge, a hardware symbol at the right with the margin it has to top and bottom.
"""

from dataclasses import dataclass, field

from . import const

MIN_WIDTH = 1.0
MAX_WIDTH = 30.0
MAX_LINES = 2


@dataclass
class LabelLayout:
    width: float
    height: float
    textMinX: float
    textMaxX: float
    # right edge of the symbol, None without one
    iconMaxX: float | None
    iconCenterY: float
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
        lineHeights=lineHeights,
        lineCenters=lineCenters,
    )


def fittedLineHeight(lineHeight: float, measuredWidth: float, availableWidth: float) -> float:
    """Text height for a line measured `measuredWidth` wide at `lineHeight` to fit the available width"""
    if measuredWidth <= 0 or availableWidth <= 0:
        return lineHeight
    return lineHeight * min(1, availableWidth / measuredWidth)
