import re

# A new bin jointed into a cell of a baseplate or of the floor of a box (round 31, p312): the cell picked takes the
# bin's front left cell. The names of the cells are those of the baseplate's and the box's joint origins
# (jointOriginLayout.cellJointOriginPoints), the lid has none, its stacking grid isn't offered. No Fusion import, so it
# can be unit tested.

SOCKET_PREFIX = 'Socket joint origin'
BOX_CELL_PREFIX = 'Cell joint origin'
# the bin's own joint origin at the center of its front left cell, at the bottom of the feet like the foot ones. Not
# 'Foot joint origin 1-1': in a half grid that one is at the center of a half foot, and a shaped bin leaving out the
# corner has none (spec round 31, decision 2)
PLACEMENT_JOINT_ORIGIN = 'Cell placement joint origin'
CELL_JOINT_SUFFIX = ' in cell'

_CELL = re.compile(rf'^(?:{SOCKET_PREFIX}|{BOX_CELL_PREFIX}) (\d+)-(\d+)$')
# Fusion counts a second joint of the same name up, "Bin in cell (2)"
_CELL_JOINT = re.compile(r' in cell( \(\d+\))?$')


def cellOf(jointOriginName: str) -> tuple[int, int] | None:
    """Column and row, from 1, of a baseplate's socket or a box's floor cell by its joint origin's name, none for others"""
    match = _CELL.match(jointOriginName)
    return (int(match.group(1)), int(match.group(2))) if match is not None else None


def cellJointName(binName: str) -> str:
    return f'{binName}{CELL_JOINT_SUFFIX}'


def isCellJointName(name: str) -> bool:
    """Whether the joint is one the bin command made into a cell"""
    return _CELL_JOINT.search(name) is not None


def placementSource(isCentered: bool, hasCell: bool, hasKeptPlacement: bool) -> str:
    """
    Where a bin goes (round 38, upstream's Placement d37c166 joined with the cell): 'cell' into a picked cell, also a
    bin in a cell rebuilt; else 'center' on the origin, also on a rebuild, its size may have changed (upstream); else
    'kept', the spot of a bin rebuilt in place; else 'snap' to the free spot beside the other bins
    """
    if hasCell:
        return 'cell'
    if isCentered:
        return 'center'
    if hasKeptPlacement:
        return 'kept'
    return 'snap'


def positionEnabled(hasCell: bool) -> bool:
    """Snap or center doesn't apply to a bin going into a cell, so the dialog greys it out while one is picked"""
    return not hasCell


def offersCellPick(isNewBin: bool, hasBaseplateOrBox: bool) -> bool:
    """The dialog offers the cell only for a new bin, a rebuilt one keeps its joint, and only with a
    baseplate or box in the design"""
    return isNewBin and hasBaseplateOrBox
