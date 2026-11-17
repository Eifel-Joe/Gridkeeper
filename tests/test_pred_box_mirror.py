"""
The storage box's feature mirrors (round 27, Pred's #42 Mirror6) copy the mirrored faces instead of finding the
fillet and chamfer edges again on the other side. Fusion's default compute type Adjust failed #42 Mirror6 with
FILLET_NO_EDGE_FOUND as soon as the box was built through the command (grounded container, tagged parameters),
Identical and Optimized built it with the same volume (fusion-auftraege/r27_diag2.log, variants 7 to 11).
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
    feature = builder.mirror(["holders", "fillet10"], "midXPlane", "#42 Mirror6")
    [mirrorInput] = builder.features.mirrorFeatures.added
    assert mirrorInput.patternComputeOption == COMPUTE.IdenticalPatternCompute
    assert mirrorInput.features == ["holders", "fillet10"] and mirrorInput.plane == "midXPlane"
    assert feature.name == "Mirror6"
    assert steps == ["#42 Mirror6"]
