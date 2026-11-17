"""
What the export takes as a part (upstream round 17.11.2026, p300). Upstream's export knew bins and baseplates only,
ours exports every part the generators make, and the colored text and symbol bodies of a part (p86, in its Text
component, round 13, p90) go into the part's mesh, painted for the slicer. No Fusion imports, so it is testable, the
export command (commands/commandExport) finds the bodies.
"""

import dataclasses

# The tags of the bodies the export takes, as tagUtils writes them (tags are literals, they're stored in documents).
# 'box' is the box and the lid of round 27, there from its merge on. A new part, the small parts of round 28 or the box
# label (p262), is one more entry here and in tests/test_export_parts.py
EXPORT_TAGS = ('bin', 'baseplate', 'label', 'box')

# the component of a part holding its colored text and symbol bodies, tagUtils.TEXT_COMPONENT_NAME, a copy of it is
# named "Text (1)", see tagUtils.partTag
TEXT_COMPONENT_NAME = 'Text'


def isExportTag(tagName: str | None) -> bool:
    return tagName in EXPORT_TAGS


def isTextComponentName(name: str) -> bool:
    """The same test as tagUtils.partTag, so the export and the right-click menu agree on a part's letters"""
    return name.startswith(TEXT_COMPONENT_NAME)


def isPartBody(tagName: str | None, componentName: str) -> bool:
    """
    A body exported as a part of its own. The text bodies of a Cullenect insert are tagged like its base, they go with
    the base instead
    """
    return isExportTag(tagName) and not isTextComponentName(componentName)


def exportTargets(bodies: list, partOf, key) -> list:
    """
    The bodies to export for the selected ones, in their order, each once: a letter stands for its part, partOf gives
    what a body stands for, itself when it is a part or nothing generated. key tells two apart, a body placed twice is
    two
    """
    targets = []
    keys = []
    for body in bodies:
        target = partOf(body)
        targetKey = key(target)
        if targetKey not in keys:
            keys.append(targetKey)
            targets.append(target)
    return targets


def withMarkings(part, markings: list, paint: bool):
    """
    The part's mesh (threeMf.MeshObject) with the meshes of its text and symbol bodies added, where they are, so the
    slicer gets the part whole. With paint every text triangle is painted with the label filament, the part's own
    painted letters (outline labels) stay painted either way
    """
    if len(markings) == 0:
        return part
    vertices = list(part.vertices)
    triangles = list(part.triangles)
    painted = set(part.painted)
    for marking in markings:
        offset = len(vertices)
        vertices += marking.vertices
        for triangle in marking.triangles:
            if paint:
                painted.add(len(triangles))
            triangles.append(tuple(vertex + offset for vertex in triangle))
    return dataclasses.replace(part, vertices=vertices, triangles=triangles, painted=painted)
