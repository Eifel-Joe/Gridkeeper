import adsk.core, adsk.fusion
from dataclasses import dataclass
from typing import Callable, TypeVar

from . import tagUtils
from .gridfinityUtils import commonUtils, designIntent

# Where bins, baseplates and inserts go in the design (round 13, p90, Joerg 15.11.2026): the root holds a container per
# kind, Grid, Bins and Label, each part is a component of its own in it, its colored text and symbol bodies are in a
# component Text inside the part, so they export apart for a multicolor print.
#
# Occurrences below the top level come back from addNewComponent without the path from the root (shown in Fusion
# 15.11.2026: assemblyContext None, fullPathName 'Bin A:1'). A combine in the part with a tool body of Text failed with
# "Fehler beim Abrufen der Zielexemplartransformation" until target and tool were proxies with the full path from the
# root, so every occurrence handed out here is such a proxy, see inContext

LOG_PREFIX = 'Gridfinity assembly'

T = TypeVar('T')

TEXT_COMPONENT_NAME = 'Text'


@dataclass
class OldPlace:
    """Where a part rebuilt in place was: bodies in the root, or a component in the parent occurrence (None for the
    root). The new one goes to the same place, Joerg 15.11.2026: old parts stay where they are"""
    isComponent: bool
    parent: adsk.fusion.Occurrence | None = None


def rebuildKind(oldPlace: OldPlace | None) -> str:
    if oldPlace is None:
        return designIntent.REBUILD_NONE
    return designIntent.REBUILD_OLD_OCCURRENCE if oldPlace.isComponent else designIntent.REBUILD_OLD_BODIES


def inContext(entity, occurrence: adsk.fusion.Occurrence | None):
    """The entity of a component as seen through the occurrence, itself without one (the root)"""
    return entity.createForAssemblyContext(occurrence) if occurrence is not None else entity


def findContainer(des: adsk.fusion.Design, kind: str) -> adsk.fusion.Occurrence | None:
    """The container of the kind in the root, found by its tag so the user may rename it"""
    root = des.rootComponent
    for attribute in des.findAttributes(tagUtils.TAG_GROUP, tagUtils.TAG_CONTAINER):
        component = adsk.fusion.Component.cast(attribute.parent)
        if component is None or attribute.value != kind:
            continue
        occurrences = root.occurrencesByComponent(component)
        if occurrences.count > 0:
            return occurrences.item(0)
    return None


def containerOccurrence(des: adsk.fusion.Design, kind: str) -> adsk.fusion.Occurrence:
    """
    The container of the kind, made at the timeline marker if there's none. Called before a part's timeline group
    starts: inside it a rebuild would delete the container along with the old part
    """
    found = findContainer(des, kind)
    if found is not None:
        return found
    occurrence = des.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occurrence.component.name = tagUtils.CONTAINER_NAMES[kind]
    occurrence.component.attributes.add(tagUtils.TAG_GROUP, tagUtils.TAG_CONTAINER, kind)
    # A container only sorts, it never moves: a joint of a part in it, an insert into a pocket or a bin onto a
    # baseplate, would otherwise move the whole container with every part in it (Fusion 15.11.2026: the first insert
    # jointed into a pocket took the container Label and a second insert in it into the bin), see addOccurrence
    occurrence.isGrounded = True
    commonUtils.debugLog(f'{LOG_PREFIX} made the container {occurrence.component.name}')
    return occurrence


def addOccurrence(
    des: adsk.fusion.Design,
    parent: adsk.fusion.Occurrence | None,
    name: str,
    transform: adsk.core.Matrix3D | None = None,
    isMovable: bool = False,
) -> adsk.fusion.Occurrence:
    """
    A new component in the parent occurrence, the root for None, as a proxy with the full path from the root. A movable
    one, a part in its container, is let go of its parent: Fusion grounds the first occurrence of a component to its
    parent (isGroundToParent, read 15.11.2026), a joint of that part then failed against the grounded container or
    moved the container instead. A Text component stays with its part
    """
    owner = parent.component if parent is not None else des.rootComponent
    native = owner.occurrences.addNewComponent(transform or adsk.core.Matrix3D.create())
    native.component.name = name
    occurrence = inContext(native, parent)
    if isMovable and parent is not None and occurrence.isGroundToParent:
        occurrence.isGroundToParent = False
    return occurrence


@dataclass
class PartPlace:
    """Where a part is built: a component of its own in the parent (None for the root), or bodies in the root"""
    isComponent: bool
    parent: adsk.fusion.Occurrence | None = None


def partPlace(
    des: adsk.fusion.Design,
    plan: designIntent.StructurePlan,
    kind: str,
    oldPlace: OldPlace | None,
) -> PartPlace:
    """
    Where the part goes, see designIntent.structurePlan. Makes the container if needed, so it's called before the
    part's timeline group starts, and the part's component is added after, see addOccurrence
    """
    if plan.place == designIntent.PLACE_ROOT_BODIES:
        return PartPlace(isComponent=False)
    if plan.place == designIntent.PLACE_OLD_PARENT:
        return PartPlace(isComponent=True, parent=oldPlace.parent if oldPlace is not None else None)
    return PartPlace(isComponent=True, parent=containerOccurrence(des, kind))


def oldPlaceOf(des: adsk.fusion.Design, occurrence: adsk.fusion.Occurrence | None) -> OldPlace:
    """Where a part with that component, none for bodies in the root, is: its parent as a proxy with the full path"""
    if occurrence is None:
        return OldPlace(isComponent=False)
    native = occurrence.nativeObject or occurrence
    proxies = des.rootComponent.allOccurrencesByComponent(native.component)
    proxy = proxies.item(0) if proxies.count > 0 else None
    return OldPlace(isComponent=True, parent=proxy.assemblyContext if proxy is not None else None)


def isSameOccurrence(a: adsk.fusion.Occurrence | None, b: adsk.fusion.Occurrence | None) -> bool:
    """Native and proxy of an occurrence count as the same"""
    if a is None or b is None:
        return False
    return (a.nativeObject or a) == (b.nativeObject or b)


class TextOccurrence:
    """The Text component of a part, made the first time it's asked for, so a part without colored bodies gets none"""

    def __init__(self, des: adsk.fusion.Design, part: adsk.fusion.Occurrence | None):
        self.des = des
        self.part = part
        self._occurrence: adsk.fusion.Occurrence | None = None

    @property
    def isAvailable(self) -> bool:
        """Bodies in the root have no part component to hold a Text component"""
        return self.part is not None

    def get(self) -> adsk.fusion.Occurrence:
        if self._occurrence is None:
            self._occurrence = addOccurrence(self.des, self.part, TEXT_COMPONENT_NAME)
        return self._occurrence


def buildWithStructure(des: adsk.fusion.Design, plan: designIntent.StructurePlan, build: Callable[[], T]) -> T:
    """
    Runs the build, a part design switched to hybrid first when the plan says so. A part design left hybrid without the
    part couldn't go back, so on an error the new occurrences of the root are taken out and the document switched back,
    the error goes on. The root is active afterwards: an active component shows every other one half transparent and the
    user had to switch back each time (Joerg 15.11.2026), also after a failed build
    """
    try:
        if not plan.switchToHybrid:
            return build()
        occurrenceCount = des.rootComponent.occurrences.count
        des.designIntent = adsk.fusion.DesignIntentTypes.HybridDesignIntentType
        try:
            return build()
        except Exception:
            des.activateRootComponent()
            undoHybridSwitch(des, occurrenceCount)
            raise
    finally:
        des.activateRootComponent()


def undoHybridSwitch(des: adsk.fusion.Design, occurrenceCount: int):
    root = des.rootComponent
    try:
        while root.occurrences.count > occurrenceCount:
            root.occurrences.item(root.occurrences.count - 1).deleteMe()
        des.designIntent = adsk.fusion.DesignIntentTypes.PartDesignIntentType
    except Exception as err:
        commonUtils.debugLog(f'{LOG_PREFIX} document stays hybrid after a failed build, {err}')
