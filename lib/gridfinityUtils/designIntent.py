"""
Where a generator puts what it builds, by the design intent of the document. Plain values, no Fusion, so it can be
unit tested; the numbers are those of adsk.fusion.DesignIntentTypes.
"""

from dataclasses import dataclass

# adsk.fusion.DesignIntentTypes, read in Fusion 14.11.2026
PART = 0
ASSEMBLY = 1
HYBRID = 2


@dataclass(frozen=True)
class ComponentPlan:
    # the document is a part design and turns hybrid first, it can't be turned back once it holds a component
    switchToHybrid: bool
    # a component of its own, else bodies in the root component
    isComponent: bool


def componentPlan(designIntent: int, mayChangeDocument: bool) -> ComponentPlan:
    """
    A component of its own wherever the document takes one. A part design takes a single component only (Fusion refuses
    a second one), so it is switched to hybrid, which keeps its bodies and timeline as they are (shown in Fusion
    14.11.2026). Not where the document may not change, as in a preview, which builds into the root then
    """
    if designIntent == PART:
        return ComponentPlan(switchToHybrid=mayChangeDocument, isComponent=mayChangeDocument)
    return ComponentPlan(switchToHybrid=False, isComponent=True)
