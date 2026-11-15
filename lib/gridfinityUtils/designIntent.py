"""
Where a generator puts what it builds, by the design intent of the document. Plain values, no Fusion, so it can be
unit tested; the numbers are those of adsk.fusion.DesignIntentTypes.
"""

from dataclasses import dataclass

# adsk.fusion.DesignIntentTypes, read in Fusion 14.11.2026
PART = 0
ASSEMBLY = 1
HYBRID = 2


# where a generator builds, see structurePlan
PLACE_CONTAINER = 'container'
PLACE_OLD_PARENT = 'oldParent'
PLACE_ROOT_BODIES = 'rootBodies'

# what a rebuild replaces: nothing (a new part), bodies in the root, or a component
REBUILD_NONE = 'none'
REBUILD_OLD_BODIES = 'oldBodies'
REBUILD_OLD_OCCURRENCE = 'oldOccurrence'


@dataclass(frozen=True)
class StructurePlan:
    # the document is a part design and turns hybrid first, it can't be turned back once it holds a component. A part
    # design takes a single component only (Fusion refuses a second one), hybrid keeps its bodies and timeline as they
    # are (shown in Fusion 14.11.2026)
    switchToHybrid: bool
    # PLACE_CONTAINER: a component of its own in the container of its kind (Grid, Bins, Label), PLACE_OLD_PARENT: a
    # component where the rebuilt one was, PLACE_ROOT_BODIES: bodies in the root component
    place: str


def structurePlan(designIntent: int, mayChangeDocument: bool, rebuild: str = REBUILD_NONE) -> StructurePlan:
    """
    Where a bin, baseplate or insert goes (round 13, p90): a new one into its container, a part design switched to
    hybrid for it. A rebuilt one stays where the old one was, also when it was built before the containers, Nutzer
    15.11.2026: "Bleiben, wo sie sind". A preview doesn't change a part design, it builds bodies into the root then
    """
    if rebuild == REBUILD_OLD_BODIES:
        return StructurePlan(switchToHybrid=False, place=PLACE_ROOT_BODIES)
    if rebuild == REBUILD_OLD_OCCURRENCE:
        return StructurePlan(switchToHybrid=False, place=PLACE_OLD_PARENT)
    if designIntent == PART and not mayChangeDocument:
        return StructurePlan(switchToHybrid=False, place=PLACE_ROOT_BODIES)
    return StructurePlan(switchToHybrid=designIntent == PART, place=PLACE_CONTAINER)
