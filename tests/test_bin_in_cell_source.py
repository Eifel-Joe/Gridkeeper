"""
A new bin jointed into a cell of a baseplate or box (round 31, p312), the Fusion side: binBuilder builds the bin's
placement joint origin and the joint into the cell in the bin's timeline group, a rebuilt bin goes into its cell again
(Nutzer 18.11.2026: "vorhandene Bins behalten beim Neubau ihr Gelenk"). binBuilder needs Fusion to load, so the tests
read its source, the geometry is checked in Fusion (tests/e2e/runde31_cells.py).
"""

import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_BUILDER = os.path.join(ROOT, "commands", "commandCreateBin", "binBuilder.py")
LABEL_BUILDER = os.path.join(ROOT, "commands", "commandCreateLabel", "labelBuilder.py")
ASSEMBLY = os.path.join(ROOT, "lib", "assembly.py")
REBUILD_UTILS = os.path.join(ROOT, "lib", "rebuildUtils.py")


def _function(path, name):
    tree = ast.parse(open(path, encoding="utf-8").read())
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def _source(path, name):
    return ast.unparse(_function(path, name))


def _arguments(path, name):
    return [argument.arg for argument in _function(path, name).args.args + _function(path, name).args.kwonlyargs]


def test_build_bin_takes_the_cell_and_hands_it_on():
    assert "cell" in _arguments(BIN_BUILDER, "buildBin")
    assert "cell" in _arguments(BIN_BUILDER, "_buildBin")
    assert "cell" in _source(BIN_BUILDER, "buildBin").split("buildWithStructure", 1)[1]


def test_a_bin_into_a_cell_is_built_where_it_is_jointed_from():
    """No spot beside the other bins: the joint moves the bin, a move feature for nothing is left out"""
    source = _source(BIN_BUILDER, "_buildBin")
    assert "binPlacement = placement or ((0, 0) if cell is not None and newCmpOcc is not None else placementUtils.findPlacement(" in source


def test_the_bin_gets_its_placement_joint_origin_and_is_jointed_rigidly_into_the_cell():
    source = _source(BIN_BUILDER, "_buildBin")
    assert "binCell.PLACEMENT_JOINT_ORIGIN" in source
    assert "root.joints.createInput(assembly.inContext(placementOrigin, newCmpOcc), cell)" in source
    assert "setAsRigidJointMotion()" in source
    assert "binCell.cellJointName(binName)" in source
    assert "assembly.keepShown(cell)" in source


def test_the_joint_is_in_the_bins_timeline_group():
    source = _source(BIN_BUILDER, "_buildBin")
    assert source.index("binCell.cellJointName(binName)") < source.index("des.timeline.timelineGroups.add(")


def test_the_placement_joint_origin_follows_the_bins_base_unit():
    """At the center of the front left cell of the bin's own unit parameters, not a foot's (half grid)"""
    source = _source(BIN_BUILDER, "_buildBin")
    assert "cellCenters(baseWidth, baseLength, xyClearance, range(1), range(1)" in source


def test_a_rebuilt_bin_goes_into_its_cell_again():
    source = _source(BIN_BUILDER, "rebuildBin")
    assert "cell = binCellOf(des, target)" in source
    assert "cell=cell" in source
    # the joint places it, its old transform would be taken twice
    assert "None if cell is not None else transform" in source
    # parameter edits leave the timeline and the joint as they are
    assert source.index("edits = parameterEdits(") < source.index("binCellOf(")


def test_a_cell_coming_after_the_bin_isnt_jointed_and_says_so():
    source = _source(BIN_BUILDER, "rebuildBin")
    assert "rebuildUtils.comesAfter(target, cell)" in source
    assert "notes" in source


def test_the_cell_is_read_from_the_old_bins_joint():
    source = _source(BIN_BUILDER, "binCellOf")
    assert "binCell.isCellJointName(joint.name)" in source
    assert "binCell.PLACEMENT_JOINT_ORIGIN" in source
    assert "assembly.jointOriginInRoot(" in source


def test_label_and_bin_share_the_root_proxy_and_timeline_order():
    assert "def jointOriginInRoot" in open(ASSEMBLY, encoding="utf-8").read()
    assert "def comesAfter" in open(REBUILD_UTILS, encoding="utf-8").read()
    label = open(LABEL_BUILDER, encoding="utf-8").read()
    assert "assembly.jointOriginInRoot(" in label and "def _inRoot" not in label
    assert "rebuildUtils.comesAfter(" in label and "def _isAfter" not in label
