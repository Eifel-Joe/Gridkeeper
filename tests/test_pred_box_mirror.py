"""
The storage box's feature mirrors (round 27, Pred's #72, #73, #80, #81) copy the mirrored faces instead of finding the
fillet and chamfer edges again on the other side (Fusion's default compute type Adjust, fusion-auftraege/r27_diag2.log).
Pred's #42 Mirror6 failed with both, the right handle holders are built as the left ones' counterpart instead.
"""

import sys
from types import SimpleNamespace

from tests.test_joint_origin_layout import _load


def _loadGenerator():
    """The generator with the Fusion types its modules name in annotations stood in for while loading"""
    modules = [sys.modules["adsk.core"], sys.modules["adsk.fusion"]]
    for module in modules:
        module.__getattr__ = lambda name: type(name, (), {})
    try:
        return _load("predBoxGenerator")
    finally:
        for module in modules:
            del module.__getattr__


generator = _loadGenerator()

COMPUTE = SimpleNamespace(OptimizedPatternCompute=0, IdenticalPatternCompute=1, AdjustPatternCompute=2)


class _MirrorInput:
    def __init__(self, features, plane):
        self.features = features
        self.plane = plane
        # Fusion's default, read in r27_diag2 (2 = Adjust)
        self.patternComputeOption = COMPUTE.AdjustPatternCompute


class _MirrorFeatures:
    def __init__(self):
        self.added = []

    def createInput(self, features, plane):
        return _MirrorInput(features, plane)

    def add(self, mirrorInput):
        self.added.append(mirrorInput)
        return SimpleNamespace(name=None)


def _builder(monkeypatch):
    monkeypatch.setattr(sys.modules["adsk.fusion"], "PatternComputeOptions", COMPUTE, raising=False)
    monkeypatch.setattr(generator, "collection", lambda items: list(items))
    builder = generator._Builder.__new__(generator._Builder)
    builder.features = SimpleNamespace(mirrorFeatures=_MirrorFeatures())
    steps = []
    builder.onStep = steps.append
    return builder, steps


def test_the_mirror_copies_the_faces(monkeypatch):
    builder, steps = _builder(monkeypatch)
    feature = builder.mirror(["frontTabs", "frontTabChamfer"], "midXPlane", "#73 Mirror2")
    [mirrorInput] = builder.features.mirrorFeatures.added
    assert mirrorInput.patternComputeOption == COMPUTE.IdenticalPatternCompute
    assert mirrorInput.features == ["frontTabs", "frontTabChamfer"] and mirrorInput.plane == "midXPlane"
    assert feature.name == "Mirror2"
    assert steps == ["#73 Mirror2"]


from tests.test_edge_lists import Collection  # noqa: E402


def test_the_right_holders_pick_the_mirrored_edges(monkeypatch):
    """The right handle and label holders' chamfers and fillets look up the left ones' edges mirrored across the box
    middle (round 27: built as the counterpart instead of Pred's #42 Mirror6)"""
    edges = sys.modules[generator.__name__.rsplit(".", 1)[0] + ".predBoxEdges"]
    values = {"outerWidth": 23.0, "outerLength": 18.8, "midX": 11.5, "midY": 9.4, "bodyTop": 5.22, "midZ": 2.47,
              "labelWidth": 7.05, "catchSlideDepth": 4.3}
    left = edges.expectedItems("#40 Chamfer29", values)
    right = edges.expectedItems("#40 Chamfer29", values, mirrored=True)
    monkeypatch.setattr(sys.modules["adsk.fusion"], "BRepEntityTypes",
                        SimpleNamespace(BRepEdgeEntityType="edge", BRepFaceEntityType="face"), raising=False)
    monkeypatch.setattr(sys.modules["adsk.core"], "Point3D", SimpleNamespace(create=lambda x, y, z: [x, y, z]), raising=False)
    monkeypatch.setattr(generator, "_edgeItem", lambda edge: edge.item)
    builder = generator._Builder.__new__(generator._Builder)
    builder.base = SimpleNamespace(edges=Collection([SimpleNamespace(item=item) for item in left + right]), faces=Collection([]))
    for edge in builder.base.edges.entries:
        edge.body = builder.base

    # round 45: looked up at each item's point (findBRepUsingPoint), Fusion gives what lies there
    def find(point, entityType, tolerance, visibleOnly):
        return Collection([edge for edge in builder.base.edges.entries
                           if point in edges.probePoints(edge.item) or edge.item["start"] == point])
    builder.component = SimpleNamespace(findBRepUsingPoint=find)
    assert [e.item for e in builder._pick("#40 Chamfer29", values, mirrored=True)] == right
    assert [e.item for e in builder._pick("#40 Chamfer29", values)] == left

    # nothing found there: the walk over the whole body, as before, logged
    logged = []
    monkeypatch.setitem(sys.modules, generator.__name__.rsplit(".", 1)[0] + ".commonUtils", SimpleNamespace(debugLog=logged.append))
    builder.component = SimpleNamespace(findBRepUsingPoint=lambda *args: Collection([]))
    assert [e.item for e in builder._pick("#40 Chamfer29", values, mirrored=True)] == right
    assert len(logged) == 1 and "#40 Chamfer29" in logged[0]
