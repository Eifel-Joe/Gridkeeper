from dataclasses import dataclass

from . import const
from .dim import Dim

# Where the text and icon of a bin label go (round 14, p72). They are drawn at the finished spot, on planes that follow
# the bin's parameters, rather than laid out at the current spot and moved there: a move takes the letter bodies there
# are, and letters a longer text adds stayed behind at the origin. Across the label it is model x as dims, so it follows
# the parameters; along the label it is the distance from the back edge, the hinge a tilted label turns down about,
# measured along its face. Sizes of the letters and icon are measured in Fusion and fixed at build time.


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
    alignment of a text box did, and an icon stands on that line too. Icon alone sits in the middle"""
    side = Dim.length(const.BIN_LABEL_SIDE_MARGIN)
    iconMinX = originX + side if hasIcon else None
    baselineStartX = iconMinX + Dim.length(iconWidth + const.BIN_LABEL_ICON_GAP) if hasIcon else originX + side
    baselineEndX = originX + width - side
    baselineFromBack = length / 2 + textHeight / 2
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
