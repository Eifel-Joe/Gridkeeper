"""
Round 45 (p480, p296): the box's joint origins without a sketch each. Today every point gets a construction plane, a
sketch, a point and two driving dimensions (846 ms, 8 model parameters); a joint origin on the component's origin point
with its offsets X, Y, Z as the point's dims sits at the same place with the same axes, follows the parameters the same
way (fusion-auftraege/r45_probe.log: gfBox1_baseWidth 5 -> 6 moved both 200 -> 242 mm) and costs 160 ms and 4.
Bins, baseplates and labels keep the sketch way this round.
"""

import ast
import os
import sys
import types

import pytest

from tests.test_joint_origin_layout import layout, dim, Dim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _ValueInput:
    def __init__(self, real=None, string=None):
        self.real, self.string = real, string

    @staticmethod
    def createByReal(value):
        return _ValueInput(real=value)

    @staticmethod
    def createByString(value):
        return _ValueInput(string=value)


class _Input:
    def __init__(self, geometry):
        self.geometry = geometry
        self.offsetX = self.offsetY = self.offsetZ = None


class _JointOrigin:
    def __init__(self, joInput):
        self.input = joInput
        self.name = None


class _JointOrigins:
    def __init__(self):
        self.added = []

    def createInput(self, geometry):
        return _Input(geometry)

    def add(self, joInput):
        self.added.append(_JointOrigin(joInput))
        return self.added[-1]


class _Component:
    def __init__(self):
        self.originConstructionPoint = object()
        self.jointOrigins = _JointOrigins()
        # anything else the function touched would fail here: no sketches, no planes
        self.sketches = None
        self.constructionPlanes = None


@pytest.fixture
def fusion(monkeypatch):
    monkeypatch.setattr(sys.modules["adsk.core"], "ValueInput", _ValueInput, raising=False)
    monkeypatch.setattr(sys.modules["adsk.fusion"], "JointGeometry",
                        types.SimpleNamespace(createByPoint=lambda point: ("byPoint", point)), raising=False)


def test_one_joint_origin_per_point_on_the_origin_point_with_the_dims_as_offsets(fusion):
    width = Dim.parameter(types.SimpleNamespace(name="gfBox1_baseWidth", value=5))
    points = [("Cell joint origin 1-1", Dim.length(2.1), Dim.length(-3.0), Dim.length(0.5)),
              ("Stack bottom joint origin", width * Dim.length(4.2) / 2, Dim.length(9.4), Dim.length(0.0))]
    component = _Component()
    made = layout.createOffsetJointOrigins(points, component, name="whatever")
    assert [jo.name for jo in made] == ["Cell joint origin 1-1", "Stack bottom joint origin"]
    assert made == component.jointOrigins.added
    first, second = (jo.input for jo in made)
    assert first.geometry == ("byPoint", component.originConstructionPoint)
    assert (first.offsetX.real, first.offsetY.real, first.offsetZ.real) == (2.1, -3.0, 0.5)
    assert second.offsetX.string == "(gfBox1_baseWidth * 42 mm) / 2"
    assert (second.offsetY.real, second.offsetZ.real) == (9.4, 0.0)


def _source(*parts):
    return open(os.path.join(ROOT, *parts), encoding="utf-8").read()


def _function(source, name):
    tree = ast.parse(source)
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)


def test_the_box_and_its_handle_pin_use_it():
    for (path, function) in [(("commands", "commandCreateBox", "boxBuilder.py"), "_buildBox"),
                             (("lib", "gridfinityUtils", "predHandlePin.py"), "addJointOrigin")]:
        body = ast.unparse(_function(_source(*path), function))
        assert "createOffsetJointOrigins(" in body, path
        assert "createPointJointOrigins(" not in body, path


def test_bins_baseplates_and_labels_keep_the_sketch_way():
    for path in [("commands", "commandCreateBin", "binBuilder.py"), ("commands", "commandCreateBaseplate", "baseplateBuilder.py"),
                 ("commands", "commandCreateLabel", "labelBuilder.py")]:
        assert "createOffsetJointOrigins" not in _source(*path), path


def test_the_place_of_a_joint_origin_counts_its_offsets(monkeypatch):
    """geometry.origin of an offset joint origin is the point it is made on, the component's origin
    (fusion-auftraege/r45_probe.log: [0, 0, 0] against 200, 30, 20 mm); its transform carries the offsets, and for a
    sketch-made one it is the same point as its geometry (probe: both 200, 30, 20 mm)"""
    monkeypatch.setattr(sys.modules["adsk.core"], "Point3D",
                        types.SimpleNamespace(create=lambda x, y, z: (x, y, z)), raising=False)
    jointOrigin = types.SimpleNamespace(
        geometry=types.SimpleNamespace(origin=(0.0, 0.0, 0.0)),
        transform=types.SimpleNamespace(translation=types.SimpleNamespace(x=20.0, y=3.0, z=2.0)))
    assert layout.jointOriginPlace(jointOrigin) == (20.0, 3.0, 2.0)


def test_the_box_label_finds_the_front_of_the_box_by_the_seat_place():
    """rebuildUtils._frontSpot placed the rebuilt box label by the Label seat's geometry.origin: with the box's offset
    joint origins that is the box's own origin, the label would go beside the wrong spot"""
    body = ast.unparse(_function(_source("lib", "rebuildUtils.py"), "_frontSpot"))
    assert "jointOriginPlace(boxJointOrigin.nativeObject or boxJointOrigin)" in body
    assert "geometry.origin" not in body


def test_no_code_reads_a_joint_origin_place_by_its_geometry():
    """Sister paths of _frontSpot (review request round 45): the only geometry.origin reads left in the add-in are of
    construction planes; a joint origin's place goes through jointOriginPlace. Joints, the rebuild's repointing (by
    name and seat), cells, stacking, lid, small parts and export don't read a joint origin's place at all"""
    found = []
    for folder in ("lib", "commands"):
        for (directory, _, files) in os.walk(os.path.join(ROOT, folder)):
            for file in files:
                if not file.endswith(".py"):
                    continue
                for (number, line) in enumerate(open(os.path.join(directory, file), encoding="utf-8"), 1):
                    if "geometry.origin" in line and "plane.geometry.origin" not in line:
                        found.append(f"{file}:{number}: {line.strip()}")
    assert found == []
