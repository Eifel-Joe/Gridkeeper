import adsk.core, adsk.fusion
import math
import re
from dataclasses import dataclass, field
from typing import Callable

from . import configJson
from . import tagUtils
from . import assembly
from . import placementUtils
from .gridfinityUtils import commonUtils
from .gridfinityUtils import cullenect
from .gridfinityUtils import boxLabelConfig, predBoxLabelLayout, predBoxParts, predBoxSeats
from .gridfinityUtils import timelineRemoval
from .gridfinityUtils import jointNames
from .gridfinityUtils import componentNames
from .gridfinityUtils import binCell
from .gridfinityUtils.jointOriginLayout import jointOriginPlace

# Rebuilding a generated body at its place in the timeline: the new one is built right after the old one's timeline
# group, the features after it that use the old bodies get the new ones and the old group goes. Features picking a
# face or an edge of the old bodies can't be moved over, Fusion flags them, see RebuildTarget.newlyUnhealthy

LOG_PREFIX = 'Gridfinity rebuild'

HEALTHY = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState

@dataclass
class RebuildTarget:
    """A generated body's timeline group and what is needed to build its replacement in place"""
    group: adsk.fusion.TimelineGroup
    # native bodies the group generated with the tag, the ones features after it may use
    bodies: list[adsk.fusion.BRepBody]
    # the component the group made, none for a part built as bodies into the root
    occurrence: adsk.fusion.Occurrence | None
    # the offset the group moved its bodies by, in cm
    placement: tuple[float, float]
    # timeline items after the group, in order, with their health before the rebuild
    laterItems: list[adsk.fusion.TimelineObject]
    laterHealth: list[int] = field(default_factory=list)
    # the group's items before the rebuild, the only ones it deletes, see removeOldGroup
    groupItems: list[adsk.fusion.TimelineObject] = field(default_factory=list)
    # where the part is, the new one goes there too (round 13: old parts stay where they are)
    oldPlace: assembly.OldPlace | None = None
    # the old joint origins (native) joints were moved away from to the new part, deleted first, see removeOldGroup
    movedFrom: list[adsk.fusion.JointOrigin] = field(default_factory=list)

def nativeBody(body: adsk.fusion.BRepBody) -> adsk.fusion.BRepBody:
    return body.nativeObject if body.assemblyContext is not None else body

def isGroupItem(group: adsk.fusion.TimelineGroup, item: adsk.fusion.TimelineObject) -> bool:
    return item == group or (item.parentGroup is not None and item.parentGroup == group)

def timelineItems(timeline: adsk.fusion.Timeline) -> list[adsk.fusion.TimelineObject]:
    """Every item in timeline order, items of groups in place of their group, groups themselves left out"""
    items = []
    def add(item: adsk.fusion.TimelineObject):
        # an item of a group may come up on its own as well, see commandSnapshotTests.unhealthyFeatures
        if not any(seen == item for seen in items):
            items.append(item)
    for index in range(timeline.count):
        item = timeline.item(index)
        if item.isGroup:
            group = adsk.fusion.TimelineGroup.cast(item)
            for childIndex in range(group.count):
                add(group.item(childIndex))
        else:
            add(item)
    return items

def generatedBy(item: adsk.fusion.TimelineObject, body: adsk.fusion.BRepBody) -> bool:
    """Whether the item made or changed the native body, or made the component it's in"""
    entity = item.entity
    occurrence = adsk.fusion.Occurrence.cast(entity)
    if occurrence is not None:
        return occurrence.component == body.parentComponent
    feature = adsk.fusion.Feature.cast(entity)
    if feature is None:
        return False
    return any(featureBody == body for featureBody in feature.bodies)

def findGroup(design: adsk.fusion.Design, body: adsk.fusion.BRepBody) -> adsk.fusion.TimelineGroup | None:
    """The timeline group the generator made the native body in, none when it was ungrouped"""
    groups = design.timeline.timelineGroups
    for groupIndex in range(groups.count):
        group = groups.item(groupIndex)
        if any(generatedBy(group.item(index), body) for index in range(group.count)):
            return group
    return None

def isPlacementName(name: str, placementName: str) -> bool:
    """Fusion numbers a name already taken in the component, like Bin placement (2) of the second bin in a part design"""
    return name == placementName or (name.startswith(f'{placementName} (') and name.endswith(')'))

def groupPlacement(group: adsk.fusion.TimelineGroup, placementName: str) -> tuple[float, float]:
    """XY offset the group's placement move of that name translates by, none moved the bodies when it isn't there"""
    moves = []
    for index in range(group.count):
        move = adsk.fusion.MoveFeature.cast(group.item(index).entity)
        if move is None:
            continue
        moves.append(move.name)
        if not isPlacementName(move.name, placementName):
            continue
        definition = adsk.fusion.MoveFeatureTranslateXYZDefinition.cast(move.definition)
        if definition is not None:
            return (definition.xDistance.value, definition.yDistance.value)
        commonUtils.fileLog(f'{LOG_PREFIX} {move.name} in {group.name} isn\'t a translation, placing at the origin')
    # a bin built at the origin has none
    commonUtils.debugLog(f'{LOG_PREFIX} no {placementName} in {group.name}, placing at the origin, its moves: {moves}')
    return (0, 0)

def findTarget(design: adsk.fusion.Design, body: adsk.fusion.BRepBody, tagName: str, placementName: str) -> RebuildTarget:
    """Placement name is of the move the generator places the bodies with. Raises ValueError when the body can't be rebuilt in place"""
    if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
        raise ValueError('Rebuilding needs the design history, the timeline, turned on')
    body = nativeBody(body)
    group = findGroup(design, body)
    if group is None:
        raise ValueError(f'The timeline group {body.name} was generated in wasn\'t found, it may have been ungrouped')
    items = [group.item(index) for index in range(group.count)]
    bodies = [taggedBody for (taggedBody, _) in tagUtils.findTaggedBodies(design, tagName) if any(generatedBy(item, taggedBody) for item in items)]
    if len(bodies) == 0:
        raise ValueError(f'No generated bodies were found in the timeline group {group.name}')
    occurrence = next((adsk.fusion.Occurrence.cast(item.entity) for item in items if adsk.fusion.Occurrence.cast(item.entity) is not None), None)
    allItems = timelineItems(design.timeline)
    lastGroupIndex = max(index for (index, item) in enumerate(allItems) if isGroupItem(group, item))
    laterItems = allItems[lastGroupIndex + 1:]
    return RebuildTarget(
        group,
        bodies,
        occurrence,
        groupPlacement(group, placementName),
        laterItems,
        [item.healthState for item in laterItems],
        items,
        assembly.oldPlaceOf(design, occurrence),
    )

def rollAfterGroup(target: RebuildTarget):
    """Puts the marker right after the group, what is built next goes before the later features"""
    # an expanded group can't be rolled to, and with the marker after its last item what is built next joins it
    target.group.isCollapsed = True
    target.group.rollTo(False)

# occurrences a preview hid by their light bulb, turned back on when the command ends, see restoreHiddenForPreview
_hiddenForPreview = []

def hideOldBody(target: RebuildTarget, byLightBulb: bool = False):
    """
    For a preview, the old bodies stay where the new ones are shown otherwise. Turning the bodies' light bulbs off left
    them shown, the group is suppressed instead, its items one by one when Fusion won't suppress the group.
    byLightBulb (the box, round 39, p481): the old set's occurrence's light bulb goes off instead. Fusion never
    suppresses a box set's group ("Some group features are not suppression-configurable"), its 298 items went one by
    one after that message in every preview; the light bulb hides all its bodies at once (fusion-auftraege/
    r39_probe.log). A part of bodies in the root has no occurrence and goes the old way
    """
    if byLightBulb and target.occurrence is not None:
        # only one that is on: a set the user hid stays hidden after the command (review round 39), and a preview
        # recomputed after Fusion's undo of the last one records the set once
        if target.occurrence.isLightBulbOn:
            target.occurrence.isLightBulbOn = False
            if not any(hidden == target.occurrence for hidden in _hiddenForPreview):
                _hiddenForPreview.append(target.occurrence)
        return
    try:
        target.group.isSuppressed = True
        return
    except RuntimeError as err:
        commonUtils.debugLog(f'{LOG_PREFIX} the timeline group {target.group.name} wasn\'t suppressed for the preview, {err}')
    for item in target.groupItems:
        try:
            item.isSuppressed = True
        except RuntimeError as err:
            commonUtils.debugLog(f'{LOG_PREFIX} {item.name} wasn\'t suppressed for the preview, {err}')

def restoreHiddenForPreview():
    """
    Turns the light bulbs hideOldBody turned off back on, once, when the command ends whichever way (cancel, OK,
    failure). Fusion undoes a preview by itself; this holds should it not. A set gone with OK is no longer valid
    """
    hidden = list(_hiddenForPreview)
    _hiddenForPreview.clear()
    for occurrence in hidden:
        try:
            if occurrence.isValid and not occurrence.isLightBulbOn:
                occurrence.isLightBulbOn = True
        except RuntimeError as err:
            commonUtils.fileLog(f'{LOG_PREFIX} an old part hidden for the preview stayed hidden, {err}')

def bodyMap(target: RebuildTarget, newBodies: list[adsk.fusion.BRepBody]) -> list[tuple[adsk.fusion.BRepBody, adsk.fusion.BRepBody]]:
    """
    Pairs of an old native body and the new one taking its place. Bodies of the same count pair up by where they
    are, front row first, all go to a single new body, none pair up otherwise
    """
    def position(body: adsk.fusion.BRepBody):
        box = body.boundingBox
        # a box and its lid start at the same corner, the lower one first (round 27)
        return (round(box.minPoint.y, 3), round(box.minPoint.x, 3), round(box.minPoint.z, 3))
    newBodies = [nativeBody(body) for body in newBodies]
    if len(newBodies) == 1:
        return [(body, newBodies[0]) for body in target.bodies]
    if len(newBodies) == len(target.bodies):
        return list(zip(sorted(target.bodies, key=position), sorted(newBodies, key=position)))
    return []

def replaceBodies(
    target: RebuildTarget,
    newBodies: list[adsk.fusion.BRepBody],
    newOccurrence: adsk.fusion.Occurrence | None,
) -> list[str]:
    """
    Gives the later features using the old bodies the new ones instead, returns the names of those it couldn't.
    Features only take new bodies with the marker right before them, so it moves through the later items
    """
    pairs = bodyMap(target, newBodies)

    def replacement(entity):
        body = adsk.fusion.BRepBody.cast(entity)
        if body is None:
            return entity
        native = nativeBody(body)
        newBody = next((new for (old, new) in pairs if old == native), None)
        if newBody is None:
            return entity
        if body.assemblyContext is None:
            return newBody
        # a body of the old component is now one of the new component, a body of a copy of it stays in that copy
        context = newOccurrence if assembly.isSameOccurrence(body.assemblyContext, target.occurrence) else body.assemblyContext
        return newBody.createForAssemblyContext(context) if context is not None else newBody

    def replaced(entities: list) -> list | None:
        """The entities with the new bodies, none when there's nothing to replace"""
        swapped = [replacement(entity) for entity in entities]
        return swapped if any(new is not old for (new, old) in zip(swapped, entities)) else None

    def collection(entities: list) -> adsk.core.ObjectCollection:
        return commonUtils.objectCollectionFromList(entities)

    # items of a collapsed group can't be rolled to, the groups are expanded meanwhile
    collapsedGroups = []
    for item in target.laterItems:
        group = item.parentGroup
        if group is not None and group.isCollapsed and not any(seen == group for seen in collapsedGroups):
            collapsedGroups.append(group)
    for group in collapsedGroups:
        group.isCollapsed = False

    failed = []
    for item in target.laterItems:
        entity = item.entity
        feature = adsk.fusion.Feature.cast(entity)
        if feature is None:
            continue
        try:
            replaceFeatureBodies(item, feature, replaced, collection)
        except Exception as err:
            commonUtils.fileLog(f'{LOG_PREFIX} couldn\'t give {item.name} the new bodies, {err}')
            failed.append(item.name)
    # a group the marker is in can't be collapsed
    target.group.parentTimeline.moveToEnd()
    for group in collapsedGroups:
        group.isCollapsed = True
    return failed

# the inputs of a feature that may hold bodies, by the feature type, ObjectCollections and lists of entities
BODY_LIST_INPUTS = [
    (adsk.fusion.ExtrudeFeature, 'participantBodies'),
    (adsk.fusion.RevolveFeature, 'participantBodies'),
    (adsk.fusion.SweepFeature, 'participantBodies'),
    (adsk.fusion.LoftFeature, 'participantBodies'),
    (adsk.fusion.HoleFeature, 'participantBodies'),
    (adsk.fusion.PipeFeature, 'participantBodies'),
]
BODY_COLLECTION_INPUTS = [
    (adsk.fusion.CombineFeature, 'toolBodies'),
    (adsk.fusion.MoveFeature, 'inputEntities'),
    (adsk.fusion.MirrorFeature, 'inputEntities'),
    (adsk.fusion.RectangularPatternFeature, 'inputEntities'),
    (adsk.fusion.CircularPatternFeature, 'inputEntities'),
    (adsk.fusion.PathPatternFeature, 'inputEntities'),
    (adsk.fusion.ScaleFeature, 'inputEntities'),
    (adsk.fusion.SplitBodyFeature, 'splitBodies'),
]
BODY_INPUTS = [
    (adsk.fusion.CombineFeature, 'targetBody'),
    (adsk.fusion.SilhouetteSplitFeature, 'targetBody'),
]

def replaceFeatureBodies(item: adsk.fusion.TimelineObject, feature: adsk.fusion.Feature, replaced, collection):
    inputs = [(featureType.cast(feature), name, kind) for (inputs, kind) in [(BODY_LIST_INPUTS, 'list'), (BODY_COLLECTION_INPUTS, 'collection'), (BODY_INPUTS, 'body')] for (featureType, name) in inputs]
    inputs = [(typed, name, kind) for (typed, name, kind) in inputs if typed is not None]
    if len(inputs) == 0:
        return
    item.rollTo(True)
    for (typed, name, kind) in inputs:
        value = getattr(typed, name)
        if value is None:
            continue
        entities = [value] if kind == 'body' else list(value)
        swapped = replaced(entities)
        if swapped is None:
            continue
        if kind == 'body':
            setattr(typed, name, swapped[0])
        elif kind == 'collection':
            setattr(typed, name, collection(swapped))
        else:
            setattr(typed, name, swapped)
        commonUtils.debugLog(f'{LOG_PREFIX} {item.name} {name} now uses the new bodies')

def removeOldGroup(target: RebuildTarget, jointsMoved: bool = False) -> list[str]:
    """
    Once the later features have the new bodies, with the marker back at the end. Returns the names of the items
    Fusion wouldn't delete, suppressed instead. With a joint moved over to the new part the old joint origins the
    moved joints used go one by one first, then the rest as a whole, see timelineRemoval.deleteMovedFirst: the group
    as a whole took a moved joint along (Fusion 15.11.2026, the insert dropped back to the origin; again round 43),
    item by item took up to 274 s for a box (round 39). Without, the group goes as a whole; Fusion may refuse that,
    without saying why, then its items go one by one, the last first so none is still used by what's left
    """
    group = target.group
    groupName = group.name
    if group.count != len(target.groupItems):
        # deleting it would take whatever joined it too
        commonUtils.fileLog(f'{LOG_PREFIX} the timeline group {groupName} has {group.count} items, {len(target.groupItems)} before the rebuild')
        raise RuntimeError(f'The timeline group {groupName} of the old bin changed while rebuilding, it was left as is')
    group.isCollapsed = True
    timeline = group.parentTimeline
    log = lambda message: commonUtils.fileLog(f'{LOG_PREFIX} {message} ({groupName})')
    if jointsMoved:
        movedFrom = []
        for jointOrigin in target.movedFrom:
            # several joints may have used one
            if not any(jointOrigin == seen for seen in movedFrom):
                movedFrom.append(jointOrigin)
        commonUtils.fileLog(f'{LOG_PREFIX} deleting the timeline group {groupName}: the {len(movedFrom)} joint origins joints were moved away from first, then the rest as a whole')
        # items of a group can't be deleted on their own, the header goes and they stay in the timeline
        group.deleteMe(False)
        def isMoved(item) -> bool:
            # an item Fusion gives no entity of isn't one: the header is gone already, raising here would leave the
            # old part ungrouped (review round 43)
            try:
                jointOrigin = adsk.fusion.JointOrigin.cast(item.entity)
            except RuntimeError:
                return False
            return jointOrigin is not None and any(jointOrigin == old for old in movedFrom)
        return timelineRemoval.deleteMovedFirst(target.groupItems, isMoved, timeline, log, expectedMoved=len(movedFrom))
    try:
        if group.deleteMe(True):
            return []
        commonUtils.fileLog(f'{LOG_PREFIX} deleting the items of the timeline group {groupName} one by one, Fusion didn\'t delete the group')
    except RuntimeError as err:
        commonUtils.fileLog(f'{LOG_PREFIX} the timeline group {groupName} wasn\'t deleted, {err}, deleting its items one by one')
    if group.isValid:
        group.deleteMe(False)
    return timelineRemoval.deleteOneByOne(target.groupItems, timeline, log)

def existingJoints(design: adsk.fusion.Design) -> list[adsk.fusion.Joint]:
    """
    The joints there are, to tell those a build makes, see dropJointCounters. As objects: an entity token string may
    differ between fetches (Fusion's docs), a joint of the user would pass for a new one (review round 43)
    """
    return list(design.rootComponent.allJoints)

def dropJointCounters(design: adsk.fusion.Design, before: list[adsk.fusion.Joint]):
    """
    A joint the build made, not among before, named with Fusion's counter while the old part's joint was still there
    ("... in cell (1)", round 43, p430) gets the lowest free name among the joints of its component, see
    jointNames.freedName. Joints there were before, the user's own included, keep their names
    """
    for joint in list(design.rootComponent.allJoints):
        try:
            if any(joint == old for old in before):
                continue
            taken = [other.name for other in joint.parentComponent.joints if other != joint]
            name = jointNames.freedName(joint.name, taken)
            if name is not None:
                commonUtils.debugLog(f'{LOG_PREFIX} {joint.name} is now {name}')
                joint.name = name
        except RuntimeError as err:
            commonUtils.fileLog(f'{LOG_PREFIX} a joint the rebuild made kept its name, {err}')

def dropComponentCounters(design: adsk.fusion.Design, named: list[tuple[adsk.fusion.Component, str]]):
    """
    A component the build named, see componentNames.recording, that got Fusion's counter on the name it asked for while
    the old part was still there ("Gridfinity bin 1x1x3 (1)", round 44, p570) gets the lowest free name, see
    jointNames.freedName. A name asked for with an "(n)" of its own stays (review round 44: the old part's own name
    counted as taken, a label text "M3 (2)" would have lost its "(2)"). Components the build didn't name, the user's
    own included, keep their names
    """
    taken = None
    for (component, requested) in named:
        try:
            if not component.isValid:
                continue
            current = component.name
            if current == requested or jointNames.countedBase(current) != requested:
                continue
            if taken is None:
                taken = [other.name for other in design.allComponents]
            # a name Fusion doesn't list among the components isn't taken twice (review round 44)
            others = list(taken)
            if current in others:
                others.remove(current)
            name = jointNames.freedName(current, others)
            if name is not None:
                commonUtils.debugLog(f'{LOG_PREFIX} {current} is now {name}')
                component.name = name
                taken = others + [name]
        except RuntimeError as err:
            commonUtils.fileLog(f'{LOG_PREFIX} a component the rebuild made kept its name, {err}')

def readJointEnds(joints) -> list:
    """
    Each joint with its timeline item and what its sides hold, read in one go before anything is moved: moving a joint
    over rolls the marker back before it, and reading the sides of the joints further on, rolled back then, raised
    "InternalValidationError : jointOcc" (round 39, p530: a box rebuilt with a second box after it, its own joints
    later in the timeline, fusion-auftraege/r39_mess.log). Per joint (joint, item, sides), sides a list of
    (side, joint origin, its occurrence, the other side's joint origin, the other side's occurrence) for each side that
    is a joint origin
    """
    ends = []
    for joint in joints:
        values = {name: getattr(joint, name) for name in ('geometryOrOriginOne', 'geometryOrOriginTwo', 'occurrenceOne', 'occurrenceTwo')}
        sides = []
        for (side, occurrence, other, otherOccurrence) in (('geometryOrOriginOne', 'occurrenceOne', 'geometryOrOriginTwo', 'occurrenceTwo'),
                                                           ('geometryOrOriginTwo', 'occurrenceTwo', 'geometryOrOriginOne', 'occurrenceOne')):
            jointOrigin = adsk.fusion.JointOrigin.cast(values[side])
            if jointOrigin is None:
                continue
            sides.append((side, jointOrigin, values[occurrence], adsk.fusion.JointOrigin.cast(values[other]), values[otherOccurrence]))
        ends.append((joint, joint.timelineObject, sides))
    return ends

def repointJoints(
    design: adsk.fusion.Design,
    target: RebuildTarget,
    newOccurrence: adsk.fusion.Occurrence | None,
) -> tuple[int, list[str]]:
    """
    Joints using a pocket joint origin of the old part, an insert jointed into a Cullenect pocket (round 13, p160), get
    the pocket of the same name of the new part, so the insert stays in its pocket. A joint only takes it with the marker
    right before it, the new part coming before it in the timeline (tried in Fusion 15.11.2026: at the end of the
    timeline it failed). Returns how many were moved over and a note per joint whose pocket the new part doesn't have
    """
    if target.occurrence is None or newOccurrence is None:
        return (0, [])
    oldComponent = (target.occurrence.nativeObject or target.occurrence).component
    newComponent = newOccurrence.component
    def pocketTag(jointOrigin: adsk.fusion.JointOrigin) -> str | None:
        attribute = jointOrigin.attributes.itemByName(tagUtils.TAG_GROUP, tagUtils.TAG_POCKET)
        return attribute.value if attribute is not None else None
    # pockets only: a joint on a foot's joint origin, a bin onto a baseplate, is the user's own and stays as it is (review)
    remap = cullenect.pocketRemap(
        cullenect.pocketNames([(jointOrigin.name, pocketTag(jointOrigin)) for jointOrigin in oldComponent.jointOrigins]),
        cullenect.pocketNames([(jointOrigin.name, pocketTag(jointOrigin)) for jointOrigin in newComponent.jointOrigins]),
    )

    def insertSizeMm(jointOrigin: adsk.fusion.JointOrigin) -> tuple[float, float] | None:
        """Width and height of the insert the joint origin is on, from its tagged body, the insert lies flat along X"""
        component = (jointOrigin.nativeObject or jointOrigin).parentComponent
        bodies = [body for body in component.bRepBodies if body.attributes.itemByName(tagUtils.TAG_GROUP, tagUtils.TAG_LABEL) is not None]
        if len(bodies) == 0:
            return None
        box = bodies[0].boundingBox
        return (round((box.maxPoint.x - box.minPoint.x) * 10, 4), round((box.maxPoint.y - box.minPoint.y) * 10, 4))
    moved = 0
    notes = []
    shown = []
    # items of a collapsed group can't be rolled to ("Associated feature is invalid", Fusion 15.11.2026), the group of
    # the insert holding the joint is expanded meanwhile, as in replaceBodies
    collapsedGroups = []
    for (joint, item, sides) in readJointEnds(list(design.rootComponent.allJoints)):
        for (side, jointOrigin, _, otherSide, _) in sides:
            if (jointOrigin.nativeObject or jointOrigin).parentComponent != oldComponent or jointOrigin.name not in remap:
                continue
            newName = remap[jointOrigin.name]
            if newName is None:
                notes.append(f'{joint.name}: the new {newComponent.name} has no {jointOrigin.name}, the joint goes with the old one')
                continue
            try:
                group = item.parentGroup
                if group is not None and group.isCollapsed:
                    group.isCollapsed = False
                    collapsedGroups.append(group)
                item.rollTo(True)
                newPocket = newComponent.jointOrigins.itemByName(newName)
                setattr(joint, side, newPocket.createForAssemblyContext(newOccurrence))
                target.movedFrom.append(jointOrigin.nativeObject or jointOrigin)
                # the insert's pocket stays shown, see assembly.keepShown
                shown.append(newPocket.createForAssemblyContext(newOccurrence))
                moved += 1
                commonUtils.debugLog(f'{LOG_PREFIX} {joint.name} now uses {newName} of the new part')
                # a narrower pocket of the same name, after other base units or compartments, may no longer take the
                # insert, the label command wouldn't joint it there (spec 12), the rebuild says so (review)
                insertSize = insertSizeMm(otherSide) if otherSide is not None else None
                pocketSize = cullenect.readPocketTagValue(pocketTag(newPocket) or '')
                if insertSize is not None and pocketSize is not None:
                    fitNote = cullenect.pocketFitNote(joint.name, newName, insertSize, pocketSize)
                    if fitNote is not None:
                        notes.append(fitNote)
            except Exception as err:
                commonUtils.fileLog(f'{LOG_PREFIX} {joint.name} couldn\'t be moved over to {newName}, {err}')
                notes.append(f'{joint.name}: couldn\'t be moved over to {newName} of the new {newComponent.name}, it goes with the old one')
    design.timeline.moveToEnd()
    for group in collapsedGroups:
        group.isCollapsed = True
    for jointOrigin in shown:
        assembly.keepShown(jointOrigin)
    return (moved, notes)

def partRole(component: adsk.fusion.Component) -> str:
    """The role of a component inside a part, its tag (a box set's 'Box', 'Lid'), else its name"""
    attribute = component.attributes.itemByName(tagUtils.TAG_GROUP, tagUtils.TAG_PART_ROLE)
    return attribute.value if attribute is not None else component.name

def seatsByOccurrence(joints) -> dict[str, str]:
    """
    The seat of each small part of a box set, by its occurrence's full path: the set joints every part at a seat, a box
    joint origin named after it (predBoxParts.seatJointOriginName), the occurrence on the other side of that joint is
    the part. Round 36 (p293): the four latches, two handle pins and two hinges are each one component, only their seat
    tells them apart. The part is the context of its joint origin; a joint's side may come without an occurrence
    (round 20, p220)
    """
    seats = {}
    for joint in joints:
        for (side, other, otherOccurrence) in (('geometryOrOriginOne', 'geometryOrOriginTwo', 'occurrenceTwo'), ('geometryOrOriginTwo', 'geometryOrOriginOne', 'occurrenceOne')):
            jointOrigin = adsk.fusion.JointOrigin.cast(getattr(joint, side))
            seat = predBoxParts.seatOfJointOriginName(jointOrigin.name) if jointOrigin is not None else None
            if seat is None:
                continue
            otherJointOrigin = adsk.fusion.JointOrigin.cast(getattr(joint, other))
            # the joint origin's own context first, as oldJointOriginKey and newJointOriginKeys go by the part's
            # occurrence; the joint's occurrence only when it has none (review round 36)
            occurrence = (otherJointOrigin.assemblyContext if otherJointOrigin is not None else None) or getattr(joint, otherOccurrence)
            if occurrence is not None:
                seats[occurrence.fullPathName] = seat
    return seats

def newJointOriginKeys(newPart: adsk.fusion.Occurrence, seats: dict[str, str]) -> dict:
    """
    The joint origins of the rebuilt part, its own and those of the components inside it, by (place, seat, name): the
    place is the component's role ('' for the part itself), the seat that of a small part (seatsByOccurrence), '' for
    one occurrence like box and lid. Keyed by role and name alone the four latches overwrote each other and a joint
    on any latch went to the last one (p293)
    """
    keys = {}
    for (occurrence, place) in [(newPart, '')] + [(child, partRole(child.component)) for child in newPart.childOccurrences]:
        seat = seats.get(occurrence.fullPathName, '') if place else ''
        for jointOrigin in occurrence.component.jointOrigins:
            keys[(place, seat, jointOrigin.name)] = jointOrigin.createForAssemblyContext(occurrence)
    return keys

def oldJointOriginKey(
    jointOrigin: adsk.fusion.JointOrigin,
    oldNative: adsk.fusion.Occurrence,
    seats: dict[str, str],
    jointOccurrence: adsk.fusion.Occurrence = None,
) -> tuple[str, str, str]:
    """
    The key of newJointOriginKeys for a joint origin of the old part, seen through the occurrence it is of. Fusion
    gives a joint's joint origins native, without a context (Fusion run round 36): the part is then the joint's
    occurrence of that side, jointOccurrence
    """
    component = (jointOrigin.nativeObject or jointOrigin).parentComponent
    place = '' if component == oldNative.component else partRole(component)
    occurrence = jointOrigin.assemblyContext or jointOccurrence
    seat = seats.get(occurrence.fullPathName, '') if place and occurrence is not None else ''
    return (place, seat, jointOrigin.name)

def repointJointsByName(
    design: adsk.fusion.Design,
    target: RebuildTarget,
    newBodies: list[adsk.fusion.BRepBody],
) -> tuple[int, list[str]]:
    """
    Joints of the user on a joint origin of the old part, its own component or one inside it (a box set: Box and Lid,
    round 27), get the joint origin of the same name in the same place of the new part. The part's own joints, in its
    timeline group, go with the old part. A box label too wide for the rebuilt box isn't moved over, it is laid in front
    of the box or beside the parts, see _layBeside. Returns how many were moved over and a note per joint that couldn't be or needs a look
    """
    if target.occurrence is None or len(newBodies) == 0:
        return (0, [])
    oldNative = target.occurrence.nativeObject or target.occurrence
    oldComponents = [oldNative.component] + [occurrence.component for occurrence in oldNative.component.allOccurrences]
    proxies = design.rootComponent.allOccurrencesByComponent(nativeBody(newBodies[0]).parentComponent)
    if proxies.count == 0:
        return (0, [])
    newPart = proxies.item(0)
    # a set with components inside (box and lid) was replaced by a set again: the body's component is one level down
    if oldNative.component.occurrences.count > 0 and newPart.assemblyContext is not None:
        newPart = newPart.assemblyContext
    allJoints = list(design.rootComponent.allJoints)
    # the small parts by their seat, the old set's and the new one's, both are there now (p293)
    seats = seatsByOccurrence(allJoints)
    newJointOrigins = newJointOriginKeys(newPart, seats)
    moved = 0
    notes = []
    shown = []
    # box labels to lay beside: the joint, the label's occurrence, the cells it was built for and the box takes now, and
    # the rebuilt box's Label joint origin
    tooWide = []
    collapsedGroups = []
    for (joint, item, sides) in readJointEnds(allJoints):
        if item is not None and isGroupItem(target.group, item):
            continue
        for (side, jointOrigin, jointOccurrence, otherSide, otherOccurrence) in sides:
            component = (jointOrigin.nativeObject or jointOrigin).parentComponent
            if not any(component == old for old in oldComponents):
                continue
            newJointOrigin = newJointOrigins.get(oldJointOriginKey(jointOrigin, oldNative, seats, jointOccurrence))
            if newJointOrigin is None:
                notes.append(f'{joint.name}: the new part has no {jointOrigin.name}, the joint goes with the old one')
                continue
            try:
                # rolled to first: the marker may still stand before a joint moved earlier, the label's bodies after it
                # rolled back, and its width check found no plate (review round 39)
                group = item.parentGroup
                if group is not None and group.isCollapsed:
                    group.isCollapsed = False
                    collapsedGroups.append(group)
                item.rollTo(True)
                if jointOrigin.name == predBoxSeats.LABEL_JOINT_ORIGIN:
                    # a box rebuilt with its label in the holder (it is nicer when the joint is kept on
                    # rebuild): the holder stays shown, a label of another width is said. One too
                    # wide goes beside (decided 17.11.2026: when a box rebuild makes the
                    # label too wide, the label is laid beside it)
                    shown.append(newJointOrigin)
                    (labelCells, boxCells) = (_labelCells(otherSide), _boxCells(newJointOrigin))
                    if boxLabelConfig.labelFit(labelCells, boxCells) == boxLabelConfig.FIT_TOO_WIDE:
                        # the label's occurrence from the joint: its sides may come without one (round 20, p220, review)
                        labelOccurrence = otherOccurrence or otherSide.assemblyContext
                        tooWide.append((joint, labelOccurrence, labelCells, boxCells, newJointOrigin))
                        continue
                    widthNote = boxLabelConfig.widthNote(joint.name, labelCells, boxCells)
                    if widthNote is not None:
                        notes.append(widthNote)
                if binCell.cellOf(jointOrigin.name) is not None:
                    # a bin jointed into a cell of the baseplate or box (round 31): the cell stays shown, as the bin
                    # command keeps it (review)
                    shown.append(newJointOrigin)
                setattr(joint, side, newJointOrigin)
                target.movedFrom.append(jointOrigin.nativeObject or jointOrigin)
                moved += 1
            except Exception as err:
                commonUtils.fileLog(f"{LOG_PREFIX} {joint.name} couldn't be moved over to {jointOrigin.name}, {err}")
                notes.append(f"{joint.name}: couldn't be moved over to the new part, it goes with the old one")
    design.timeline.moveToEnd()
    for group in collapsedGroups:
        group.isCollapsed = True
    # with the timeline at its end, before the old part goes: its joints would break with it
    # the old set too: still there, it may reach further out in front than the new one. The instance being rebuilt, not
    # the first of its component: a pasted copy elsewhere would widen the extents (review). The new set's component is
    # new, newPart is its only instance
    oldPart = _rebuiltInstance(design.rootComponent.allOccurrencesByComponent(oldNative.component), oldNative)
    boxParts = [newPart] + ([oldPart] if oldPart is not None else [])
    for (joint, occurrence, labelCells, boxCells, boxJointOrigin) in tooWide:
        jointName = joint.name
        laid = _layBeside(design, joint, occurrence, labelCells, boxJointOrigin, boxParts)
        if laid == LAID_FRONT:
            notes.append(boxLabelConfig.widthNote(jointName, labelCells, boxCells, place='in front of'))
        elif laid == LAID_BESIDE:
            notes.append(boxLabelConfig.widthNote(jointName, labelCells, boxCells))
        elif laid == LAID_FREE:
            notes.append(f"{jointName}: the label is too wide for the box now, it was taken out but lies where it was built; move it and rebuild it with the new width")
        else:
            notes.append(f"{jointName}: the label is too wide for the box now and couldn't be taken out, it goes with the old box; rebuild the label")
    for jointOrigin in shown:
        assembly.keepShown(jointOrigin)
    return (moved, notes)

# grid free spots are looked for on, as a new box label's (boxLabelBuilder.PLACEMENT_CELL)
LABEL_PLACEMENT_CELL = 4.2
# what _layBeside did: laid in front of the box, beside the parts, taken out but left where it was built, or left in
LAID_FRONT = 'front'
LAID_BESIDE = 'beside'
LAID_FREE = 'free'
LAID_NOT = 'not'

def _layBeside(
    design: adsk.fusion.Design,
    joint: adsk.fusion.Joint,
    occurrence: adsk.fusion.Occurrence | None,
    labelCells: int,
    boxJointOrigin: adsk.fusion.JointOrigin | None = None,
    boxParts: list[adsk.fusion.Occurrence] | None = None,
) -> str:
    """
    Takes the label out of the holder of a box rebuilt too narrow for it and lays it flat in front of the box, its
    middle on the box's (decided 17.11.2026: in front of the front is better, otherwise it is easily overlooked), see
    _frontSpot; is something in the way there, at a free spot beside the parts as a new label without a box. Without
    its joint Fusion puts it back where it was built, for a jointed label the origin (p391); a new place holds only
    with its position captured right after it is set (p392: transform2, then snapshots.add). Returns LAID_FRONT,
    LAID_BESIDE, LAID_FREE or LAID_NOT
    """
    if occurrence is None:
        return LAID_NOT
    deleted = False
    group = None
    wasCollapsed = False
    try:
        item = joint.timelineObject
        group = item.parentGroup if item is not None else None
        wasCollapsed = group is not None and group.isCollapsed
        if wasCollapsed:
            group.isCollapsed = False
        if item is not None:
            item.rollTo(True)
        joint.deleteMe()
        deleted = True
        design.timeline.moveToEnd()
        (width, height) = (predBoxLabelLayout.plateWidth(labelCells), predBoxLabelLayout.PLATE_HEIGHT)
        spot = _frontSpot(design, occurrence, (width, height), boxJointOrigin, boxParts or [])
        laid = LAID_FRONT
        if spot is None:
            (x, y) = placementUtils.findPlacement(
                design,
                [tagUtils.TAG_BOX, tagUtils.TAG_LABEL, tagUtils.TAG_BIN, tagUtils.TAG_BASEPLATE],
                predBoxLabelLayout.PLATE_BODY_NAME,
                (0, 0, width, height),
                LABEL_PLACEMENT_CELL,
                LABEL_PLACEMENT_CELL,
            )
            (spot, laid) = ((x + width / 2, y + height / 2, 0), LAID_BESIDE)
        # the plate lies centred on its component's origin (as findPlacement's spot assumes); turned with the box, its
        # text reads from the box's front
        place = adsk.core.Matrix3D.create()
        if spot[2] != 0:
            place.setToRotation(spot[2] * math.pi / 2, adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(0, 0, 0))
        place.translation = adsk.core.Vector3D.create(spot[0], spot[1], 0)
        occurrence.transform2 = place
        if design.snapshots.hasPendingSnapshot:
            design.snapshots.add()
        return laid
    except Exception as err:
        commonUtils.fileLog(f"{LOG_PREFIX} a box label {'taken out' if deleted else 'left in'}, not laid beside the box, {err}")
        return LAID_FREE if deleted else LAID_NOT
    finally:
        # a group the marker is in can't be collapsed (review: the error path left it open)
        try:
            design.timeline.moveToEnd()
            if wasCollapsed and group is not None and group.isValid:
                group.isCollapsed = True
        except Exception as err:
            commonUtils.fileLog(f'{LOG_PREFIX} timeline not put back after laying a box label beside, {err}')

def _frontSpot(
    design: adsk.fusion.Design,
    labelOccurrence: adsk.fusion.Occurrence,
    size: tuple[float, float],
    boxJointOrigin: adsk.fusion.JointOrigin | None,
    boxParts: list[adsk.fusion.Occurrence],
) -> tuple[float, float, int] | None:
    """
    Where the label lies in front of the rebuilt box, see placementUtils.frontPlacement, cm. The box's front faces -y
    in its own frame (its Label joint origin is 7.3 mm behind the front, predBoxSeats.LABEL_BACK, on the box's middle
    in x). Kept clear of the box set's parts, old and new, and of boxes, bins, baseplates, inserts and box labels, the
    label itself left out. None when something is in the way or the box can't be read; the caller looks for a free
    spot then
    """
    if boxJointOrigin is None or boxJointOrigin.assemblyContext is None or len(boxParts) == 0:
        return None
    try:
        # the box's place in the root from the native transforms up its path, each relative to its parent: what a
        # proxy's own transform2 gives isn't relied on
        boxOccurrence = boxJointOrigin.assemblyContext
        world = (boxOccurrence.nativeObject or boxOccurrence).transform2.copy()
        parent = boxOccurrence.assemblyContext
        while parent is not None:
            world.transformBy((parent.nativeObject or parent).transform2)
            parent = parent.assemblyContext
        # by its transform: the box's joint origins sit on the box's origin with offsets since round 45 (p480)
        centre = jointOriginPlace(boxJointOrigin.nativeObject or boxJointOrigin)
        centre.transformBy(world)
        front = adsk.core.Vector3D.create(0, -1, 0)
        front.transformBy(world)
        labelComponent = (labelOccurrence.nativeObject or labelOccurrence).component
        labelComponents = [labelComponent] + [child.component for child in labelComponent.allOccurrences]
        occupied = placementUtils.getOccupiedExtents(
            design,
            [tagUtils.TAG_BOX, tagUtils.TAG_LABEL, tagUtils.TAG_BIN, tagUtils.TAG_BASEPLATE],
            predBoxLabelLayout.PLATE_BODY_NAME,
            skipComponents=labelComponents,
        )
        boxExtents = [extent for part in boxParts for extent in _worldExtents(part)]
        return placementUtils.frontPlacement((front.x, front.y), (centre.x, centre.y), boxExtents, size, placementUtils.FRONT_GAP, occupied + boxExtents)
    except Exception as err:
        commonUtils.fileLog(f'{LOG_PREFIX} the front of the rebuilt box not found for its label, {err}')
        return None

def _rebuiltInstance(proxies, native):
    """
    Of the instances seen from the root of a component, the one of the native occurrence being rebuilt (its proxy, or
    itself in the root), none if none is
    """
    for index in range(proxies.count):
        proxy = proxies.item(index)
        if (proxy.nativeObject or proxy) == native:
            return proxy
    return None

def _worldExtents(occurrence: adsk.fusion.Occurrence) -> list[tuple[float, float, float, float]]:
    """World XY extents of the bodies of an occurrence seen from the root (a proxy) and of those inside it"""
    extents = []
    for body in occurrence.bRepBodies:
        box = body.boundingBox
        extents.append((box.minPoint.x, box.minPoint.y, box.maxPoint.x, box.maxPoint.y))
    for child in occurrence.childOccurrences:
        extents += _worldExtents(child)
    return extents

def _labelCells(jointOrigin: adsk.fusion.JointOrigin | None) -> int | None:
    """The cells a box label on the joint origin was built for, from its plate's config, none for anything else"""
    if jointOrigin is None:
        return None
    for body in (jointOrigin.nativeObject or jointOrigin).parentComponent.bRepBodies:
        tag = tagUtils.readPartTag(body)
        if tag is not None and tag[0] == tagUtils.TAG_BOX_LABEL:
            cells = tagUtils.buildConfig(tag[0], tag[1]) or {}
            return cells.get('cells') if isinstance(cells.get('cells'), int) else None
    return None

def _boxCells(jointOrigin: adsk.fusion.JointOrigin) -> int | None:
    """The width in grid cells of the box the joint origin is of, its widest body, as boxLabelBuilder.boxCells"""
    bodies = list((jointOrigin.nativeObject or jointOrigin).parentComponent.bRepBodies)
    if len(bodies) == 0:
        return None
    return predBoxLabelLayout.cellsOfBoxWidth(max(body.boundingBox.maxPoint.x - body.boundingBox.minPoint.x for body in bodies))

def withoutCounter(name: str) -> str:
    """A component name without the " (1)" Fusion adds to a name that is taken"""
    return re.sub(r' \(\d+\)$', '', name)

def rebuiltPartName(current: str, role: str) -> str | None:
    """
    The name a part of a rebuilt set gets, a box's lid or latch say, by its role: Fusion counted it up while the old set
    had the name ("Lid (1)"), that goes. Any other name is the user's, back from the old part, and stays
    """
    if current == role or withoutCounter(current) != role:
        return None
    return role

def isGeneratedName(name: str, generatedName: str | None, namePrefix: str) -> bool:
    """
    Whether the generator gave the name, the one in the tag, maybe counted up by Fusion, rather than the user. A tag from
    before it held the name goes by the prefix the generator's names start with
    """
    if generatedName is None:
        return name.startswith(namePrefix)
    return withoutCounter(name) == withoutCounter(generatedName)

def keptName(newName: str, oldName: str, generatedName: str | None, namePrefix: str) -> str | None:
    """
    The name the new component, timeline group or body gets once the old one is gone, none to leave its own. The user's
    name stays. A generated one only when Fusion counted the same name up while the old one had it, the generator's
    names never end in a number in brackets, a bin of another size has a name of its own
    """
    if newName == oldName:
        return None
    if not isGeneratedName(oldName, generatedName, namePrefix):
        return oldName
    if withoutCounter(newName) != withoutCounter(oldName):
        return None
    return oldName

def keepName(item, oldName: str, generatedName: str | None, namePrefix: str):
    """Gives the new component, timeline group or body the old one's name, see keptName"""
    name = keptName(item.name, oldName, generatedName, namePrefix)
    if name is None:
        return
    try:
        item.name = name
    except RuntimeError as err:
        commonUtils.fileLog(f'{LOG_PREFIX} {item.name} wasn\'t renamed to {name}, {err}')

def generatedNames(body: adsk.fusion.BRepBody) -> tuple[str | None, str | None]:
    """The names the generator gave the bin or baseplate, its component and timeline group, and the body, see tagUtils.tagBody"""
    tag = tagUtils.readBodyTag(body)
    if tag is None:
        return (None, None)
    return (tag[1].get('name'), tag[1].get('bodyName'))

def newlyUnhealthy(target: RebuildTarget) -> list[str]:
    """Later items that were fine before and have a warning or an error now, with Fusion's message"""
    notes = []
    for (item, health) in zip(target.laterItems, target.laterHealth):
        if not item.isValid or health != HEALTHY or item.healthState == HEALTHY:
            continue
        notes.append(f'{item.name}: {item.errorOrWarningMessage or "needs its inputs picked again"}')
    return notes

def removeUnusedParameters(design: adsk.fusion.Design, names: list[str]):
    """Parameters of the old body the new one doesn't use, kept when something else refers to them"""
    for name in names:
        parameter = design.userParameters.itemByName(name)
        if parameter is None or not parameter.isDeletable:
            continue
        # deleteMe is said to answer true for parameters still referenced, isDeletable covers that
        parameter.deleteMe()
        commonUtils.debugLog(f'{LOG_PREFIX} deleted the unused parameter {name}')

def findBodyByToken(design: adsk.fusion.Design, token: str) -> adsk.fusion.BRepBody:
    """The body a dialog rebuilds, found again after each preview is undone"""
    entities = design.findEntityByToken(token)
    body = adsk.fusion.BRepBody.cast(entities[0]) if len(entities) > 0 else None
    if body is None:
        raise ValueError('The body to rebuild is no longer in the design')
    return body

def tagParameterNames(body: adsk.fusion.BRepBody) -> list[str]:
    """Names of the user parameters in the body's tag"""
    tag = tagUtils.readPartTag(body)
    parameters = tag[1].get('parameters') if tag is not None else None
    if not isinstance(parameters, list):
        return []
    return [str(item[1]) for item in parameters if isinstance(item, list) and len(item) == 2]

def prefixOf(names: list[str], baseName: str) -> str | None:
    """The numbered prefix of a body's own parameters, like gfBin2 of gfBin2_heightU, none when it has none"""
    pattern = re.compile(rf'^({re.escape(baseName)}\d+)_')
    for name in names:
        match = pattern.match(name)
        if match is not None:
            return match.group(1)
    return None

def bodyId(body: adsk.fusion.BRepBody, baseName: str) -> str | None:
    """The id of the body, see tagUtils.tagBody, one built before bodies had ids goes by the prefix of its parameters"""
    tag = tagUtils.readPartTag(body)
    return (tag[1].get('id') if tag is not None else None) or prefixOf(tagParameterNames(body), baseName)

def parameterFields(parameters: list, findParameter, labelFields: dict[str, str]) -> list[tuple[str, adsk.fusion.UserParameter]]:
    """
    The parameters of a body's tag, its label and name pairs, that are still in the design, with the config field
    each holds, see tagUtils.tagParameterField. Parameters made before they were tagged go by their label in
    labelFields
    """
    fields = []
    for item in parameters if isinstance(parameters, list) else []:
        if not isinstance(item, list) or len(item) != 2:
            continue
        parameter = findParameter(str(item[1]))
        if parameter is None:
            continue
        fieldName = tagUtils.readParameterField(parameter) or labelFields.get(str(item[0]))
        if fieldName is not None:
            fields.append((fieldName, parameter))
    return fields

def configWithParameters(generator: str, config: dict, parameters: list, findParameter, labelFields: dict[str, str]) -> dict:
    """
    The config a body was built with, with the values its parameters have now, so changes made to them since aren't
    undone by building it again. findParameter looks one up by name. A field of a list item goes by its index, like
    compartmentPockets.2.label. Settings a config saved before them doesn't have get the value it was built with, see
    configJson.OLDER_VALUES, and settings saved under an older name are read under their new one, see
    configJson.RENAMED_FIELDS
    """
    config = configJson.withOlderValues(generator, configJson.renamedSettings(generator, config))
    for (fieldName, parameter) in parameterFields(parameters, findParameter, labelFields):
        isText = parameter.valueType == adsk.fusion.ParameterValueTypes.TextParameterValueType
        if isText:
            value = parameter.textValue
        elif fieldName in configJson.MM_FIELDS[generator]:
            value = round(parameter.value * 10, 6)
        else:
            value = round(parameter.value, 6)
        path = fieldName.split('.')
        if len(path) == 3 and path[1].isdigit() and isinstance(config.get(path[0]), list):
            items = [dict(item) if isinstance(item, dict) else item for item in config[path[0]]]
            if int(path[1]) < len(items) and isinstance(items[int(path[1])], dict):
                items[int(path[1])][path[2]] = value
                config[path[0]] = items
        elif len(path) == 1 and fieldName in config:
            config[fieldName] = value
    return config

def comesAfter(target: RebuildTarget, jointOrigin: adsk.fusion.JointOrigin | None) -> bool:
    """Whether the part the joint origin is of comes after the target in the timeline: the rebuild builds right after
    the old group, where that joint origin isn't there yet. An insert's pocket (review round 18), a bin's cell (round 31).
    The part may sit in a set, a box's floor cells are in its component Box (round 27), either may be the later one
    (as boxLabelBuilder._isAfter)"""
    occurrence = jointOrigin.assemblyContext if jointOrigin is not None else None
    while occurrence is not None:
        item = (occurrence.nativeObject or occurrence).timelineObject
        if item is not None and any(later == item for later in target.laterItems):
            return True
        occurrence = occurrence.assemblyContext
    return False

def rebuild(
    design: adsk.fusion.Design,
    target: RebuildTarget,
    prefix: str | None,
    baseName: str,
    isPreview: bool,
    build: Callable[[tuple[float, float], str | None, adsk.core.Matrix3D | None, assembly.OldPlace | None], list[adsk.fusion.BRepBody]],
    title: str,
    jointsByName: bool = False,
    hideByLightBulb: bool = False,
    namePrefix: str | None = None,
) -> tuple[list[adsk.fusion.BRepBody], list[str]]:
    """
    Builds the replacement of the target in its place, keeping the features after it. build gets the placement, the
    prefix of the parameters to keep, none for new ones, the transform of the component and where the old part is, and
    returns the new bodies. Returns them with what of the later features needs a look, title names the body in it.
    namePrefix starts every name the generator gives, see isGeneratedName; without one the new items keep the names the
    build gave them.
    A preview is undone anyway, it builds at the end of the timeline with the old body suppressed, rolling the
    timeline back and forth for each would be slow
    """
    transform = target.occurrence.transform2 if target.occurrence is not None else None
    if isPreview:
        hideOldBody(target, byLightBulb=hideByLightBulb)
        return (build(target.placement, None, transform, target.oldPlace), [])

    oldNames = tagParameterNames(target.bodies[0])
    jointsBefore = existingJoints(design)
    # the new items get the user's names once the old ones are gone, see keptName
    (generatedName, _) = generatedNames(target.bodies[0])
    oldGroupName = target.group.name
    oldComponentName = target.occurrence.component.name if target.occurrence is not None else None
    rollAfterGroup(target)
    with componentNames.recording() as named:
        newBodies = build(target.placement, prefix, transform, target.oldPlace)
    newOccurrence = None
    if len(newBodies) > 0 and newBodies[0].parentComponent != design.rootComponent:
        occurrences = design.rootComponent.allOccurrencesByComponent(newBodies[0].parentComponent)
        newOccurrence = occurrences.item(0) if occurrences.count > 0 else None
    newGroup = findGroup(design, nativeBody(newBodies[0])) if len(newBodies) > 0 else None
    renames = [(item, oldName, generatedName) for (item, oldName) in [
        (newGroup, oldGroupName),
        (newOccurrence.component if newOccurrence is not None else None, oldComponentName),
    ] if item is not None and oldName is not None]
    # bodies taking the place of one each, several going into one have no single name to keep
    if len(newBodies) == len(target.bodies):
        renames += [(new, old.name, generatedNames(old)[1]) for (old, new) in bodyMap(target, newBodies)]
    failed = replaceBodies(target, newBodies, newOccurrence)
    if jointsByName:
        (_, jointNotes) = repointJointsByName(design, target, newBodies)
    else:
        (_, jointNotes) = repointJoints(design, target, newOccurrence)
    # by what was noted, not the count: a joint moved whose note line failed after it wasn't counted (review round 43)
    keptOldItems = removeOldGroup(target, jointsMoved=len(target.movedFrom) > 0)
    dropJointCounters(design, jointsBefore)
    dropComponentCounters(design, named)
    if len(keptOldItems) == 0 and namePrefix is not None:
        # the old items are gone with their group, their names are free: a name the user gave comes back, see keptName
        for (item, oldName, itemGeneratedName) in renames:
            keepName(item, oldName, itemGeneratedName, namePrefix)
    # shared units stay, the body's own ones it no longer has go, like the label of a tab turned off
    newNames = tagParameterNames(newBodies[0]) if len(newBodies) > 0 else []
    removeUnusedParameters(design, [name for name in oldNames if prefix is not None and prefixOf([name], baseName) == prefix and name not in newNames])
    notes = [f'{name}: couldn\'t be given the new {title}' for name in failed] + jointNotes + newlyUnhealthy(target)
    notes += [f'{name}: of the old {title}, Fusion wouldn\'t delete it, it\'s suppressed instead' for name in keptOldItems]
    return (newBodies, notes)

def configChanges(generator: str, body: adsk.fusion.BRepBody, newConfig: dict) -> str:
    """What the rebuild changes of the config in the body's tag, a line per field as old -> new, for the log"""
    tag = tagUtils.readPartTag(body)
    oldConfig = tag[1].get('config') if tag is not None else None
    if not isinstance(oldConfig, dict):
        return 'its old config isn\'t in its tag'
    # settings saved under an older name compare under their new one, see configJson.RENAMED_FIELDS, and ones it was
    # saved without with the value it was built with, see configJson.OLDER_VALUES (round 32, p280)
    oldConfig = configJson.withOlderValues(generator, configJson.renamedSettings(generator, oldConfig))
    changes = [f'  {name}: {oldConfig.get(name)!r} -> {value!r}' for (name, value) in newConfig.items() if oldConfig.get(name) != value]
    return 'changes:\n' + '\n'.join(changes) if len(changes) > 0 else 'no changes to its config'
