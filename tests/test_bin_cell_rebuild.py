"""
Round 31, review: what a rebuilt bin reads of its cell, and whether a cell's part comes after it in the timeline, run
on stand-ins instead of Fusion. binCellOf tells a bin that was in a cell apart from one that never was, so a rebuild
can say when the cell is gone (spec decision 4), and a joint whose cell was deleted mustn't stop the rebuild.
"""

import ast
import os
import types
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_BUILDER = os.path.join(ROOT, "commands", "commandCreateBin", "binBuilder.py")
REBUILD_UTILS = os.path.join(ROOT, "lib", "rebuildUtils.py")

spec = importlib.util.spec_from_file_location("binCellForRebuild", os.path.join(ROOT, "lib", "gridfinityUtils", "binCell.py"))
binCell = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binCell)


def _load(path, name, namespace):
    tree = ast.parse(open(path, encoding="utf-8").read())
    node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), path, "exec"), namespace)
    return namespace[name]


# --- comesAfter ---

class _Occurrence:
    def __init__(self, item, parent=None):
        self.timelineObject = item
        self.nativeObject = None
        self.assemblyContext = parent


def _comesAfter():
    return _load(REBUILD_UTILS, "comesAfter", {"adsk": types.SimpleNamespace(fusion=types.SimpleNamespace(JointOrigin=object)), "RebuildTarget": object})


def test_a_cell_of_a_part_before_the_bin_doesnt_come_after():
    comesAfter = _comesAfter()
    cell = types.SimpleNamespace(assemblyContext=_Occurrence("plate"))
    assert comesAfter(types.SimpleNamespace(laterItems=["other"]), cell) is False


def test_a_box_set_after_the_bin_comes_after_even_if_its_box_component_has_no_item():
    """A box's floor cells are in its component Box inside the set; the set is what the timeline has"""
    comesAfter = _comesAfter()
    cell = types.SimpleNamespace(assemblyContext=_Occurrence(None, parent=_Occurrence("set")))
    assert comesAfter(types.SimpleNamespace(laterItems=["set"]), cell) is True


def test_no_cell_never_comes_after():
    assert _comesAfter()(types.SimpleNamespace(laterItems=["set"]), None) is False


# --- binCellOf ---

class _Component:
    pass


class _Side:
    def __init__(self, name, component, deleted=False):
        self._name = name
        self.nativeObject = None
        self.parentComponent = component
        self.deleted = deleted

    @property
    def name(self):
        if self.deleted:
            raise RuntimeError("InternalValidationError : the object is deleted")
        return self._name


class _Joint:
    def __init__(self, name, one, two):
        self.name = name
        self.geometryOrOriginOne = one
        self.geometryOrOriginTwo = two
        self.occurrenceOne = None
        self.occurrenceTwo = None


class _JointOriginType:
    """adsk.fusion.JointOrigin: cast gives the entity back, the stand-ins are joint origins"""
    @staticmethod
    def cast(entity):
        return entity


def _binCellOf(joints):
    namespace = {
        "adsk": types.SimpleNamespace(fusion=types.SimpleNamespace(JointOrigin=_JointOriginType, Design=object)),
        "binCell": binCell,
        "assembly": types.SimpleNamespace(jointOriginInRoot=lambda des, jointOrigin, occurrence: ("root", jointOrigin.name)),
        "rebuildUtils": types.SimpleNamespace(RebuildTarget=object),
        "commonUtils": types.SimpleNamespace(fileLog=lambda text: None),
        "LOG_PREFIX": "Gridfinity bin",
    }
    exec("from dataclasses import dataclass", namespace)
    _load(BIN_BUILDER, "_readSide", namespace)
    tree = ast.parse(open(BIN_BUILDER, encoding="utf-8").read())
    classNode = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "CellOfBin")
    exec(compile(ast.Module(body=[classNode], type_ignores=[]), BIN_BUILDER, "exec"), namespace)
    binCellOf = _load(BIN_BUILDER, "binCellOf", namespace)
    component = _Component()
    occurrence = types.SimpleNamespace(nativeObject=None, component=component)
    des = types.SimpleNamespace(rootComponent=types.SimpleNamespace(allJoints=joints(component)))
    return binCellOf(des, types.SimpleNamespace(occurrence=occurrence))


def test_a_bin_in_a_cell_finds_it():
    found = _binCellOf(lambda own: [_Joint("Bin 1x1x3 in cell", _Side(binCell.PLACEMENT_JOINT_ORIGIN, own), _Side("Socket joint origin 2-2", _Component()))])
    assert found.cell == ("root", "Socket joint origin 2-2") and found.wasInCell


def test_either_side_may_be_the_bins():
    found = _binCellOf(lambda own: [_Joint("Bin in cell (2)", _Side("Cell joint origin 1-1", _Component()), _Side(binCell.PLACEMENT_JOINT_ORIGIN, own))])
    assert found.cell == ("root", "Cell joint origin 1-1")


def test_a_bin_never_in_a_cell_has_none_and_wasnt():
    found = _binCellOf(lambda own: [_Joint("Rigid 1", _Side("Foot joint origin 1-1", own), _Side("Socket joint origin 1-1", _Component()))])
    assert found.cell is None and not found.wasInCell


def test_another_bins_cell_joint_isnt_this_ones():
    found = _binCellOf(lambda own: [_Joint("Bin in cell", _Side(binCell.PLACEMENT_JOINT_ORIGIN, _Component()), _Side("Socket joint origin 1-1", _Component()))])
    assert found.cell is None and not found.wasInCell


def test_a_cell_gone_is_told_apart_and_doesnt_stop_the_rebuild():
    for other in (None, _Side("Socket joint origin 1-1", _Component(), deleted=True)):
        found = _binCellOf(lambda own: [_Joint("Bin in cell", _Side(binCell.PLACEMENT_JOINT_ORIGIN, own), other)])
        assert found.cell is None and found.wasInCell


def test_a_joint_failing_to_read_is_skipped():
    class Broken:
        name = "Bin in cell"
        @property
        def geometryOrOriginOne(self):
            raise RuntimeError("broken")
        geometryOrOriginTwo = None
        occurrenceOne = occurrenceTwo = None
    found = _binCellOf(lambda own: [Broken(), _Joint("Bin in cell", _Side(binCell.PLACEMENT_JOINT_ORIGIN, own), _Side("Socket joint origin 3-1", _Component()))])
    assert found.cell == ("root", "Socket joint origin 3-1")


def test_a_cell_side_failing_to_read_still_counts_as_in_a_cell():
    """Re-review: Fusion may raise reading the side of a deleted cell, the bin was in a cell all the same"""
    class Joint(_Joint):
        @property
        def geometryOrOriginTwo(self):
            raise RuntimeError("deleted")
        @geometryOrOriginTwo.setter
        def geometryOrOriginTwo(self, value):
            pass
    found = _binCellOf(lambda own: [Joint("Bin in cell", _Side(binCell.PLACEMENT_JOINT_ORIGIN, own), None)])
    assert found.cell is None and found.wasInCell
