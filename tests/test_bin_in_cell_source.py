"""
A new bin jointed into a cell of a baseplate or box (round 31, p312), the Fusion side: binBuilder builds the bin's
placement joint origin and the joint into the cell in the bin's timeline group, a rebuilt bin goes into its cell again
(spec decision 4). binBuilder needs Fusion to load, so the tests
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
    """No spot beside the other bins: the joint moves the bin, a move feature for nothing is left out. Round 38: the
    source comes from binCell.placementSource, a cell before Center on origin, a kept spot and a free one"""
    source = _source(BIN_BUILDER, "_buildBin")
    assert "binCell.placementSource(state.placement == PLACEMENT_CENTER, cell is not None and newCmpOcc is not None, placement is not None)" in source
    assert "(0, 0) if source in ('cell', 'center')" in source
    assert "centeredPlacement(state, baseWidth, baseLength) if source == 'center'" in source
    assert "placement if source == 'kept'" in source
    assert "placementUtils.findPlacement(" in source


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
    assert "found = binCellOf(des, target)" in source and "cell = found.cell" in source
    assert "cell=cell" in source
    # the joint places it, its old transform would be taken twice
    assert "None if cell is not None else transform" in source
    # every rebuild builds the bin again, there is no parameters-only path to skip the cell (round 58)
    assert "parameterEdits" not in source


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


BIN_ENTRY = os.path.join(ROOT, "commands", "commandCreateBin", "entry.py")


def test_the_dialog_offers_the_cell_only_for_a_new_bin_with_a_baseplate_or_box():
    source = _source(BIN_ENTRY, "command_created")
    assert "binCell.offersCellPick(dialogWorkflow != WORKFLOW_REBUILD, binBuilder.hasCellParts(" in source
    assert "addSelectionInput(BIN_CELL_INPUT_ID" in source
    assert "addSelectionFilter(adsk.core.SelectionCommandInput.JointOrigins)" in source
    assert "setSelectionLimits(0, 1)" in source
    assert "args.command.select, command_select" in source


def test_only_cells_can_be_picked():
    source = _source(BIN_ENTRY, "command_select")
    assert "BIN_CELL_INPUT_ID" in source
    assert "args.isSelectable = binBuilder.isCellJointOrigin(" in source


def test_cells_are_the_baseplates_sockets_and_the_box_floor_not_the_lid():
    source = _source(BIN_BUILDER, "isCellJointOrigin")
    assert "binCell.cellOf(" in source
    assert "tagUtils.TAG_BASEPLATE" in source and "tagUtils.TAG_BOX" in source
    assert "LID_ROLE" in source


def test_the_new_bin_is_built_into_the_cell_picked():
    source = _source(BIN_ENTRY, "generateBin")
    assert "binBuilder.buildBin(des, state, settings, mayChangeDocument=not isPreview, cell=selectedCell(args.command.commandInputs))" in source


def test_the_cell_isnt_part_of_the_settings():
    """Round 32 asks every config field for its value in older models, the cell isn't one: it only places a new bin.
    Since round 38 the Placement group also holds the position, which is a setting, so the cell alone is left out"""
    assert "BIN_CELL_INPUT_ID" in _source(BIN_ENTRY, "snapshotSettings")
    tree = ast.parse(open(os.path.join(ROOT, "commands", "commandCreateBin", "inputState.py"), encoding="utf-8").read())
    fields = [node.target.id for node in ast.walk(tree) if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)]
    assert [field for field in fields if "cell" in field.lower()] == ["shapeCells"]


def test_a_rebuilt_baseplate_keeps_the_bins_jointed_into_its_cells():
    """Round 31, spec decision 6: joints onto the old baseplate's socket joint origins move to the new one by name"""
    source = _source(os.path.join(ROOT, "commands", "commandCreateBaseplate", "baseplateBuilder.py"), "rebuildBaseplate")
    assert "jointsByName=True" in source


def test_parts_of_bodies_in_the_root_offer_no_cells():
    """Review round 31: a baseplate or box of bodies in the root is rebuilt without a component to move the joint to"""
    source = _source(BIN_BUILDER, "isCellJointOrigin")
    assert "component == component.parentDesign.rootComponent" in source


def test_a_rebuilt_baseplate_or_box_keeps_the_cells_of_moved_joints_shown():
    """Review round 31: Fusion turns off a joint origin a joint uses, the bin command keeps the cell shown, so does the
    rebuild moving the joint over"""
    source = _source(REBUILD_UTILS, "repointJointsByName")
    assert "binCell.cellOf(jointOrigin.name) is not None" in source
    assert source.index("binCell.cellOf(jointOrigin.name)") < source.index("setattr(joint, side, newJointOrigin)")


def test_a_bin_in_a_cell_is_built_and_tagged_without_centering():
    """Review round 38: a bin jointed into a cell is stored as snapped, so losing its cell keeps it in place"""
    source = _source(BIN_BUILDER, "buildBin")
    assert "binCell.storedPosition(state.placement, cell is not None, PLACEMENT_AUTO)" in source
    assert source.index("storedPosition") < source.index("buildWithStructure")


def _hasCellParts():
    from types import SimpleNamespace
    import adsk.fusion
    namespace = {"adsk": __import__("adsk"), "tagUtils": SimpleNamespace(TAG_GROUP="g", TAG_BASEPLATE="baseplate", TAG_BOX="box")}
    exec(compile(ast.Module([_function(BIN_BUILDER, "hasCellParts")], []), BIN_BUILDER, "exec"), namespace)
    return namespace["hasCellParts"]


def test_no_design_has_no_cell_parts():
    """Without a design (Fusion's Design.cast of another product, the dialog screenshot tool) the dialog offers no cell"""
    assert _hasCellParts()(None) is False


def test_a_design_with_a_baseplate_has_cell_parts():
    from types import SimpleNamespace
    design = SimpleNamespace(findAttributes=lambda group, name: ["tag"] if name == "baseplate" else [])
    assert _hasCellParts()(design) is True
    assert _hasCellParts()(SimpleNamespace(findAttributes=lambda group, name: [])) is False
