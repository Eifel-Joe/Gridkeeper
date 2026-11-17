"""
Puts the small parts of the storage box after Pred's parametric Gridfinity Storage Box v1.1
(https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric, CC BY-NC, by Pred) into a box
set; which parts, how many and where they sit are in predBoxParts and predBoxSeats.

Round 29 (Nutzer 17.11.2026: "Wir zeichnen die Teile im Code."): every part is drawn by its generator into a new
component of the set, in the box command, so it lands in the set's timeline group. Importing the former part
files failed in a command with a dialog (fusion-auftraege/r28_cmdvariants.log). Further occurrences of a part are
the same component again. Every part is jointed rigidly, its joint origin on the box's at its seat, turned about z
(predBoxSeats.turnAboutZ); the hinges of the chosen variant at two seats beside the box in their print position.
Parts come in one by one as their generators are done (predBoxParts.DRAWN_ROLES), the others stay out meanwhile.
"""

import adsk.core, adsk.fusion

from .. import tagUtils
from . import appearanceUtils, commonUtils, predBoxParts, predBoxSeats, predHandle, predHandlePin, predHinge, predLatch
from .predBox import PredBoxDims


def partJointOriginName(role: str) -> str:
    """The joint origin each part's generator gives it, see dev-notes/r29"""
    return f'{role} joint origin'


def drawPart(component: adsk.fusion.Component, part: predBoxParts.Part, dims: PredBoxDims, hinge: str) -> list[adsk.fusion.BRepBody]:
    """
    Draws the part into the empty component, in the part frame of dev-notes/r29 (the frame of the former part file),
    with its joint origin except for the hinges. One branch per role of predBoxParts.DRAWN_ROLES
    """
    if part.role == 'Latch':
        return predLatch.createLatch(component)
    if part.role == 'Handle':
        # its width follows the label width, an expression on gfBoxN_baseWidth (Nutzer: at most 113.5 mm)
        return predHandle.createHandle(component, predBoxSeats.handleHalfWidth(dims).expression)
    if part.role == 'Handle pin':
        return predHandlePin.createHandlePin(component)
    if part.role == 'Hinge':
        # in the variant of the box's setting; its joint origin comes from insertParts (addOriginJointOrigin)
        return predHinge.createHinge(component, hinge)
    raise RuntimeError(f'no generator for {part.role} yet')


def insertParts(
    des: adsk.fusion.Design,
    setOccurrence: adsk.fusion.Occurrence,
    boxOccurrence: adsk.fusion.Occurrence,
    dims: PredBoxDims,
    hinge: str,
    setName: str,
    inContext,
) -> list[adsk.fusion.BRepBody]:
    """
    The small parts into the set, each jointed rigidly to the box at its seat; the hinges of the chosen variant (one
    of predBoxParts.HINGES) at two seats beside the box in their print position. Returns their native bodies, each
    part's once, after box and lid in buildBox's list (plan decision 5). inContext is assembly.inContext.

    Every part is jointed, none is placed by a transform (Nutzer 17.11.2026, "Ja, beides" to Vorschlag J): hinges set by
    their proxy's transform stayed where they were when the set was stacked, and the position Fusion captured for
    them stayed in the timeline, suppressed, after a rebuild (fusion-auftraege/r28_cmd.l1.out, .l2.out)
    """
    setComponent = (setOccurrence.nativeObject or setOccurrence).component
    boxComponent = (boxOccurrence.nativeObject or boxOccurrence).component
    seats = {seat.name: seat for seat in predBoxSeats.seats(dims, hinge)}
    bodies = []
    # the small parts in a color of their own, box and lid keep theirs (Nutzer 17.11.2026); without a library appearance
    # to copy they stay uncoloured, the box is built all the same (review round 29: before, a box needed none)
    appearance = None
    if predBoxParts.partsToDraw(hinge):
        try:
            appearance = appearanceUtils.boxPartsAppearance(des)
        except appearanceUtils.AppearanceError as err:
            commonUtils.fileLog(f'small parts of {setName} not coloured, {err}')
    for part in predBoxParts.partsToDraw(hinge):
        first = setComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        component = first.component
        component.name = part.role
        component.attributes.add(tagUtils.TAG_GROUP, tagUtils.TAG_PART_ROLE, part.role)
        drawPart(component, part, dims, hinge)
        # a part's only body after the part: snapshots and export go by body names
        if component.bRepBodies.count == 1:
            component.bRepBodies.item(0).name = part.role
        for body in (component.bRepBodies if appearance is not None else []):
            body.appearance = appearance
        occurrences = [first]
        for _ in range(part.count - 1):
            occurrences.append(setComponent.occurrences.addExistingComponent(component, adsk.core.Matrix3D.create()))
        jointOrigin = component.jointOrigins.itemByName(partJointOriginName(part.role))
        if jointOrigin is None and part.role == 'Hinge':
            jointOrigin = addOriginJointOrigin(component, partJointOriginName(part.role))
        if jointOrigin is None:
            raise RuntimeError(f'{part.role} has no joint origin {partJointOriginName(part.role)}')
        reference = seats[part.seats[0]]
        for (native, seatName) in zip(occurrences, part.seats):
            occurrence = inContext(native, setOccurrence)
            if occurrence.isGroundToParent:
                occurrence.isGroundToParent = False
            boxJointOrigin = boxComponent.jointOrigins.itemByName(predBoxParts.seatJointOriginName(seatName))
            jointInput = des.rootComponent.joints.createInput(inContext(jointOrigin, occurrence), inContext(boxJointOrigin, boxOccurrence))
            jointInput.setAsRigidJointMotion()
            jointInput.angle = adsk.core.ValueInput.createByString(f'{predBoxSeats.turnAboutZ(reference, seats[seatName])} deg')
            joint = des.rootComponent.joints.add(jointInput)
            joint.name = f'{setName} {seatName}'
        bodies += list(component.bRepBodies)
    return bodies


def addOriginJointOrigin(component: adsk.fusion.Component, name: str) -> adsk.fusion.JointOrigin:
    """
    A joint origin at the component's origin, its axes the component's: the hinges have none of their own, Pred's
    hinges lie in their print position in their own frame, so the box's hinge seats (predBoxSeats.hingeOrigins) take
    that frame as it is
    """
    jointOriginInput = component.jointOrigins.createInput(adsk.fusion.JointGeometry.createByPoint(component.originConstructionPoint))
    jointOrigin = component.jointOrigins.add(jointOriginInput)
    jointOrigin.name = name
    return jointOrigin
