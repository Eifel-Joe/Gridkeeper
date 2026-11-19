"""
Round 47 (p591): how the box's latch, hinge and handle pin (after Pred's parametric Gridfinity Storage Box v1.1,
https://www.printables.com/model/543553, CC BY-NC, by Pred) are kept and copied, see predPartCache and
predBoxInsert.insertParts.

A part to keep is drawn by its generator into a scratch component, its bodies are copied as temporary bodies and the
scratch occurrence is deleted again (fusion-auftraege/r47_cmdprobe.log: works in the box command's execute, 0.1 s; a
hidden helper document does not, Documents.add with visible False is not implemented in Fusion). A box set gets a copy
as one base feature in the part's component, its bodies named as drawn: snapshots and export go by body names.
"""

from __future__ import annotations

import adsk.core, adsk.fusion


def keepDrawn(parent: adsk.fusion.Component, draw) -> list:
    """
    [(name, temporary body)] of what draw(component) draws into a scratch component of parent; the scratch occurrence
    is deleted again, also when drawing fails
    """
    scratch = parent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    try:
        tbm = adsk.fusion.TemporaryBRepManager.get()
        return [(body.name, tbm.copy(body)) for body in draw(scratch.component)]
    finally:
        scratch.deleteMe()


def addCopies(component: adsk.fusion.Component, kept: list) -> list[adsk.fusion.BRepBody]:
    """
    Copies of the kept bodies into the component as one base feature, named as kept; the kept bodies stay as they are
    for the next box. Fails without leaving the base feature behind
    """
    tbm = adsk.fusion.TemporaryBRepManager.get()
    base = component.features.baseFeatures.add()
    try:
        base.startEdit()
        try:
            for (_, body) in kept:
                component.bRepBodies.add(tbm.copy(body), base)
        finally:
            base.finishEdit()
    except Exception:
        base.deleteMe()
        raise
    # named after the edit: a name given inside it did not stay (fusion-auftraege/r47_mess.log, step copy)
    bodies = list(component.bRepBodies)
    for (body, (name, _)) in zip(bodies, kept):
        body.name = name
    return bodies
