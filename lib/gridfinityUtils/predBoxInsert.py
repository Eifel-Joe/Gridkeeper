"""
Inserts the small parts of the storage box after Pred's parametric Gridfinity Storage Box v1.1
(https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric, CC BY-NC, by Pred) into a box
set, round 28 (p261, plan task 6). The parts are Fusion files in resources/predBox, taken over once from Pred's file
(resources/predBox/README.md); which parts, how many and where they sit are in predBoxParts and predBoxSeats.

Each file is inserted once with importManager.importToTarget (plan decision 1, the spike kept timeline, sketches and
features), further occurrences of a part are the same component again. Latches, handle and pins are jointed rigidly,
their joint origin on the box's at their seat, turned about z (predBoxSeats.turnAboutZ); the handle's one size
dimension is bound to the box's label width; the hinges lie beside the box in their print position, not jointed.
"""

import os

import adsk.core, adsk.fusion

from .. import tagUtils
from . import predBoxParts, predBoxSeats
from .predBox import PredBoxDims

RESOURCES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'predBox')
HANDLE_WIDTH_PARAMETER = 'HandleHalfWidth'


def partJointOriginName(role: str) -> str:
    """The joint origin each jointed part file carries, see fusion-auftraege/r28_extract.py and r28_handle_build.py"""
    return f'{role} joint origin'


def insertParts(
    des: adsk.fusion.Design,
    setOccurrence: adsk.fusion.Occurrence,
    boxOccurrence: adsk.fusion.Occurrence,
    dims: PredBoxDims,
    setName: str,
    inContext,
) -> list[adsk.fusion.BRepBody]:
    """
    The small parts into the set, jointed to the box. Returns their native bodies, each part's once, after box and lid
    in buildBox's list (plan decision 5). inContext is assembly.inContext
    """
    app = adsk.core.Application.get()
    setComponent = (setOccurrence.nativeObject or setOccurrence).component
    boxComponent = (boxOccurrence.nativeObject or boxOccurrence).component
    seats = {seat.name: seat for seat in predBoxSeats.seats(dims)}
    bodies = []
    for part in predBoxParts.PARTS:
        before = setComponent.occurrences.count
        options = app.importManager.createFusionArchiveImportOptions(os.path.join(RESOURCES, part.file))
        if not app.importManager.importToTarget(options, setComponent) or setComponent.occurrences.count == before:
            raise RuntimeError(f'{part.file} could not be inserted')
        first = setComponent.occurrences.item(setComponent.occurrences.count - 1)
        component = first.component
        component.name = part.role
        component.attributes.add(tagUtils.TAG_GROUP, tagUtils.TAG_PART_ROLE, part.role)
        if part.role == 'Handle':
            bindHandleWidth(component, dims)
        occurrences = [first]
        if part.seats:
            for _ in range(part.count - 1):
                occurrences.append(setComponent.occurrences.addExistingComponent(component, adsk.core.Matrix3D.create()))
            jointOrigin = component.jointOrigins.itemByName(partJointOriginName(part.role))
            if jointOrigin is None:
                raise RuntimeError(f'{part.file} has no joint origin {partJointOriginName(part.role)}')
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
        else:
            # the hinges beside the box in their print position, the first where Pred's lies (plan decision 6)
            transforms = []
            for (x, y, z) in predBoxSeats.hingePlaces()[:part.count]:
                transform = adsk.core.Matrix3D.create()
                transform.translation = adsk.core.Vector3D.create(x / 10, y / 10, z / 10)
                transforms.append(transform)
            predBoxSeats.placeAllInSet(
                first, lambda: setComponent.occurrences.addExistingComponent(component, adsk.core.Matrix3D.create()),
                setOccurrence, inContext, transforms)
            if des.designType == adsk.fusion.DesignTypes.ParametricDesignType and des.snapshots.hasPendingSnapshot:
                des.snapshots.add()
        bodies += list(component.bRepBodies)
    return bodies


def bindHandleWidth(component: adsk.fusion.Component, dims: PredBoxDims):
    """The handle's one size dimension gets the box's label width / 2 + 14.25 mm, so it follows a width change
    (Jörg 17.11.2026: "Der Griff bleibt bei Max. 113,5mm stehen."); a copy is named "HandleHalfWidth_1" or so"""
    for parameter in component.modelParameters:
        if parameter.name.startswith(HANDLE_WIDTH_PARAMETER):
            parameter.expression = predBoxSeats.handleHalfWidth(dims).expression
            return
    raise RuntimeError(f'the handle has no dimension {HANDLE_WIDTH_PARAMETER}')
