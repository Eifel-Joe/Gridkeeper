from dataclasses import dataclass

from . import const, textStyles
from .dim import Dim

# Where the text and icon of a bin label go (round 14, p72). They are drawn at the finished spot, on planes that follow
# the bin's parameters, rather than laid out at the current spot and moved there: a move takes the letter bodies there
# are, and letters a longer text adds stayed behind at the origin. Across the label it is model x as dims, so it follows
# the parameters; along the label it is the distance from the back edge, the hinge a tilted label turns down about,
# measured along its face. Sizes of the letters and icon are measured in Fusion and fixed at build time.


# An icon's imported curves come fixed where they are, so they don't follow the label's x. Let go and held by dims
# from one anchor they do, but every dim costs more the more there are: in Fusion 15.11.2026 the hex nut's 10 points
# took 20 dims in 0.3 s, the 263 points of cullenect-crimp-ring-closed hadn't all of their dims after a minute. Up to
# this many points an icon is held by dims, more and its bodies are moved into place, the text never is (Hauptsitzung
# 15.11.2026, proposal A). Counted when building, so coarser symbols (p51) fall under it by themselves.
# Round 17, p180: measured again on the coarser Cullenect symbols (job r17_dims): tnut-2 26 points 1.3 s, tnut-1 32,
# nut-square 34, nut 36 points 1.9 s, magnet 50 points already 3.0 s, crimp-ring-closed 120 points 15 s. The spec holds
# a symbol by dims when that takes under 2 s, so the limit stays between 36 and 50, see tests/test_bin_label_layout.py
ICON_POINTS_HELD_BY_DIMS = 40


def isIconHeldByDims(pointCount: int) -> bool:
    return pointCount <= ICON_POINTS_HELD_BY_DIMS


def labelSpan(tabOriginX: Dim, tabLength: Dim, compartmentX: Dim, compartmentWidth: Dim) -> tuple[Dim, Dim]:
    """From where to where across a compartment its label or Cullenect socket goes: the overlap of the tab and the
    compartment, a tab is trimmed to its compartment. As Fusion's max() and min() of both (round 15, p60): picked by
    their values when building, a base width changed afterwards could turn which ends first, and the socket of a
    compartment beside the grid stayed off its middle"""
    return (Dim.max(tabOriginX, compartmentX), Dim.min(tabOriginX + tabLength, compartmentX + compartmentWidth))


@dataclass
class BinLabelPlacement:
    # height of the label plane
    planeZ: Dim
    # the back edge, a tilted label turns down about it
    hingeY: Dim
    # radians, 0 is flat
    tiltAngle: float
    # model x of the ends of the line the text stands on
    baselineStartX: Dim
    baselineEndX: Dim
    # text alone is centered, after an icon it starts at the left
    isCentered: bool
    # distance of the text's baseline from the back edge, along the label face
    baselineFromBack: float
    # model x of the icon's left side, none without an icon
    iconMinX: Dim | None
    # distance of the icon's bottom from the back edge, along the label face
    iconMinFromBack: float


def binLabelPlacement(
    originX: Dim,
    originY: Dim,
    originZ: Dim,
    width: Dim,
    length: float,
    tiltAngle: float,
    textHeight: float,
    iconWidth: float,
    iconHeight: float,
    hasIcon: bool,
    hasText: bool,
) -> BinLabelPlacement:
    """Text height is of its capitals, it stands on a line below the middle of the label by half of it, as the middle
    alignment of a text box did, and an icon stands on that line too. Icon alone sits in the middle. An icon taller than
    the letters, it keeps its full size since round 22 (upstream f1cb49b), sits in the middle and the letters stand on
    its bottom"""
    side = Dim.length(const.BIN_LABEL_SIDE_MARGIN)
    iconMinX = originX + side if hasIcon else None
    baselineStartX = iconMinX + Dim.length(iconWidth + const.BIN_LABEL_ICON_GAP) if hasIcon else originX + side
    baselineEndX = originX + width - side
    baselineFromBack = length / 2 + (max(textHeight, iconHeight) if hasIcon else textHeight) / 2
    return BinLabelPlacement(
        planeZ=originZ,
        hingeY=originY + Dim.length(length),
        tiltAngle=tiltAngle,
        baselineStartX=baselineStartX,
        baselineEndX=baselineEndX,
        isCentered=not hasIcon,
        baselineFromBack=baselineFromBack,
        iconMinX=iconMinX,
        iconMinFromBack=baselineFromBack if hasText else length / 2 + iconHeight / 2,
    )


def _labelTexts(config: dict) -> tuple[str, dict]:
    """The bin label and the compartment labels that are set, by their cell: a tag without pockets and the empty ones
    the dialog fills the grid with say the same (review round 19)"""
    labels = {}
    for (index, pocket) in enumerate(config.get('compartmentPockets') or []):
        if isinstance(pocket, dict) and pocket.get('label'):
            labels[(pocket.get('x', index), pocket.get('y', 0))] = pocket['label']
    return (config.get('labelText', ''), labels)


def textChangedSinceBuild(builtConfig: dict, newConfig: dict) -> bool:
    """Whether a label text differs from the one the bin was built with, the config of its tag without its parameters
    (round 19, p181). Set by its parameter alone, a longer text keeps the height of its letters and runs past the tab, a
    rebuild fits it anew instead. The bin's own label and those of its compartments"""
    return _labelTexts(builtConfig) != _labelTexts(newConfig)


def sharedText(built: str, values: list[str]) -> str:
    """The text of a label several parameters hold, compartments showing the bin's label each have one: the first that
    differs from the built text, edited in Fusion, else the built one. Taken in turn, an unchanged parameter after the
    edited one undid the edit (review round 19)"""
    return next((value for value in values if value != built), built)


@dataclass
class BinLabelFit:
    # text height given to Fusion, the height of the letters as measured, the icon's height
    textHeight: float
    lettersHeight: float
    iconSize: float
    # the text doesn't fit even at the least height that prints, see textStyles.fittedHeight
    overflows: bool


def fitBinLabel(contentWidth: float, contentHeight: float, iconAspect: float | None, measuredWidth: float, measuredHeight: float, style: str) -> BinLabelFit:
    """Sizes of the text and icon of a bin label, the text measured at a text height of contentHeight (round 22, p13,
    as the original, upstream f1cb49b by Le0Michine). The icon keeps its full size, as tall as the letters can
    be at most, only limited by the label width; the text shrinks to the width left after the icon and gap, not below
    the least height that prints (round 19). Before, icon and letters shrank together"""
    tallest = contentHeight * const.BIN_LABEL_TEXT_HEIGHT_RATIO
    iconSize = min(tallest, contentWidth / iconAspect) if iconAspect is not None else tallest
    room = contentWidth - (iconSize * iconAspect + const.BIN_LABEL_ICON_GAP if iconAspect is not None else 0)
    heightScale = tallest / measuredHeight
    widthScale = max(room, 0) / measuredWidth
    (fitted, overflows) = textStyles.fittedHeight(contentHeight * heightScale, contentHeight * widthScale, style)
    return BinLabelFit(fitted, measuredHeight * fitted / contentHeight, iconSize, overflows)
