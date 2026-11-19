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


class LeftBehind(RuntimeError):
    """A failed copy whose base feature Fusion did not remove: the part must not be drawn on top of it"""


def keepDrawn(parent: adsk.fusion.Component, draw) -> list:
    """
    [(name, temporary body)] of every body draw(component) leaves in a scratch component of parent (as insertParts took
    all of a part's bodies before); the scratch occurrence is deleted again, also when drawing fails, without hiding
    that failure. A scratch occurrence Fusion does not delete is an error, the part is then drawn in place
    """
    scratch = parent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    try:
        draw(scratch.component)
        tbm = adsk.fusion.TemporaryBRepManager.get()
        kept = [(body.name, tbm.copy(body)) for body in scratch.component.bRepBodies]
    except Exception:
        _deleteQuietly(scratch)
        raise
    if not scratch.deleteMe():
        raise RuntimeError('the scratch component of the part was not deleted')
    return kept


def addCopies(component: adsk.fusion.Component, kept: list) -> list[adsk.fusion.BRepBody]:
    """
    Copies of the kept bodies into the component as one base feature, named as kept; the kept bodies stay as they are
    for the next box. Fails without leaving the base feature behind (insertParts then draws the part into the
    component, the hinge's generator wants it empty)
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
        # named after the edit: a name given inside it did not stay (fusion-auftraege/r47_mess.log, step copy); the
        # component's bodies come in the order they were added
        bodies = list(component.bRepBodies)
        if len(bodies) != len(kept):
            raise RuntimeError(f'{len(bodies)} bodies in the base feature, {len(kept)} kept')
        for (body, (name, _)) in zip(bodies, kept):
            body.name = name
    except Exception:
        if not _deleteQuietly(base):
            raise LeftBehind('the copied part could not be removed again, it is not drawn anew')
        raise
    return bodies


def _deleteQuietly(entity) -> bool:
    """Deleted, for a clean-up whose own failure must not hide why it was needed"""
    try:
        return bool(entity.deleteMe())
    except Exception:
        return False
