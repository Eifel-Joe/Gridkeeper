"""
Upstream round 17.11. (p300): what the export takes as a part, bins, baseplates, Cullenect inserts and later boxes,
and how the colored text bodies of a part go into its mesh, painted for the slicer.
"""

import ast
import os
import importlib.util

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, *path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PROJECT_ROOT, *path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


exportParts = _load("exportParts", "lib", "exportParts.py")
threeMf = _load("threeMf", "lib", "threeMf.py")


def _tag_constants():
    tree = ast.parse(open(os.path.join(PROJECT_ROOT, "lib", "tagUtils.py"), encoding="utf-8").read())
    return {
        node.targets[0].id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
    }


# --- which tags are parts ---

def test_the_parts_the_export_knows():
    assert exportParts.EXPORT_TAGS == ("bin", "baseplate", "label", "box", "boxLabel")


def test_export_tags_are_those_the_generators_write():
    tags = _tag_constants()
    assert {tags["TAG_BIN"], tags["TAG_BASEPLATE"], tags["TAG_LABEL"]} <= set(exportParts.EXPORT_TAGS)


def test_only_part_tags_are_exported():
    assert exportParts.isExportTag("bin")
    assert exportParts.isExportTag("label")
    assert exportParts.isExportTag("box")
    assert not exportParts.isExportTag("pocket")
    assert not exportParts.isExportTag("container")
    assert not exportParts.isExportTag(None)


def test_text_components_are_named_like_partTag_finds_them():
    assert exportParts.TEXT_COMPONENT_NAME == _tag_constants()["TEXT_COMPONENT_NAME"]
    assert exportParts.isTextComponentName("Text")
    assert exportParts.isTextComponentName("Text (1)")
    assert not exportParts.isTextComponentName("Bin 2x1x3")


def test_a_text_body_is_never_a_part_of_its_own():
    # the text bodies of a Cullenect insert are tagged label like its base, they go with the base
    assert exportParts.isPartBody("label", "Label 25mm")
    assert not exportParts.isPartBody("label", "Text")
    assert not exportParts.isPartBody(None, "Bin 2x1x3")
    assert not exportParts.isPartBody("pocket", "Bin 2x1x3")


# --- selected bodies stand for their parts ---

def test_selected_bodies_stand_for_their_parts_once_each():
    parts = {"letter a": "bin", "letter b": "bin", "insert text": "insert"}
    targets = exportParts.exportTargets(["letter a", "bin", "insert text", "letter b", "other"], lambda body: parts.get(body, body), lambda body: body)
    assert targets == ["bin", "insert", "other"]


def test_targets_are_told_apart_by_their_key():
    # the same native body placed twice is two parts
    targets = exportParts.exportTargets([("bin", 1), ("bin", 2), ("bin", 1)], lambda body: body, lambda body: body)
    assert targets == [("bin", 1), ("bin", 2)]


# --- the text bodies in the part's mesh ---

def triangle_mesh(name, offset, painted=()):
    return threeMf.MeshObject(name, [(offset, 0, 0), (offset + 1, 0, 0), (offset, 1, 0)], [(0, 1, 2)], set(painted))


def test_text_meshes_join_their_part_and_are_painted():
    part = threeMf.MeshObject("Bin", [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)], [(0, 1, 2), (1, 3, 2)], {1})
    merged = exportParts.withMarkings(part, [triangle_mesh("t1", 5), triangle_mesh("t2", 9)], True)
    assert merged.name == "Bin"
    assert len(merged.vertices) == 10
    assert merged.triangles == [(0, 1, 2), (1, 3, 2), (4, 5, 6), (7, 8, 9)]
    # the part's own painted letters stay, every text triangle is painted
    assert merged.painted == {1, 2, 3}


def test_unpainted_text_meshes_still_complete_the_part():
    part = triangle_mesh("Insert", 0)
    merged = exportParts.withMarkings(part, [triangle_mesh("t", 5)], False)
    assert merged.triangles == [(0, 1, 2), (3, 4, 5)]
    assert merged.painted == set()


def test_a_part_without_text_stays_as_it_is():
    part = triangle_mesh("Baseplate", 0, painted={0})
    assert exportParts.withMarkings(part, [], True) == part


# --- review round 17.11.: the parts under an occurrence, a Text occurrence once for its part, the root never Text ---

class Occ:
    def __init__(self, name, bodies=(), children=(), parent=None):
        self.name = name
        self.bodies = list(bodies)
        self.children = list(children)
        self.parent = parent
        for child in self.children:
            child.parent = self


def walk(start):
    return exportParts.partBodiesUnder(
        start,
        isText=lambda occ: exportParts.isTextComponentName(occ.name),
        parentOf=lambda occ: occ.parent,
        childrenOf=lambda occ: occ.children,
        bodiesOf=lambda occ: occ.bodies,
        isPart=lambda body: not body.startswith("letter"),
    )


def tree():
    text1 = Occ("Text", ["letter A"])
    text2 = Occ("Text (1)", ["letter B"])
    bin1 = Occ("Bin 2x1x3", ["bin 1"], [text1])
    bin2 = Occ("Bin 1x1x3", ["bin 2"], [text2])
    bins = Occ("Bins", [], [bin1, bin2])
    return (bins, bin1, text1)


def test_a_container_gives_its_parts_once_each():
    (bins, _, _) = tree()
    assert walk(bins) == ["bin 1", "bin 2"]


def test_a_part_gives_itself():
    (_, bin1, _) = tree()
    assert walk(bin1) == ["bin 1"]


def test_a_text_occurrence_stands_for_its_part_and_ends():
    # climbing to the part and walking down into its Text again went on until the recursion limit
    (_, _, text1) = tree()
    assert walk(text1) == ["bin 1"]


def test_the_root_is_never_a_text_component():
    # the root component is named after the document, "Texthalter" mustn't make its parts letters
    assert not exportParts.isTextComponentName("Texthalter", isRoot=True)
    assert exportParts.isTextComponentName("Text", isRoot=False)


# -- file names (click test 17.11.2026, F3): a box's bodies are named Base and Lid, every box exported gave "Base.stl",
# "Base (2).stl"; the file name carries the set's name, "Box 5×4×6 Base"

def test_a_box_body_is_named_after_its_set():
    assert exportParts.partFileName("Base", "Box 5×4×6") == "Box 5×4×6 Base"
    assert exportParts.partFileName("Lid", "Box 7×5×10") == "Box 7×5×10 Lid"


def test_a_body_outside_a_set_keeps_its_name():
    assert exportParts.partFileName("Gridfinity bin 2x1x3", None) == "Gridfinity bin 2x1x3"


def test_a_name_that_starts_with_the_set_name_isnt_doubled():
    assert exportParts.partFileName("Box 5×4×6 Base", "Box 5×4×6") == "Box 5×4×6 Base"


# --- the small parts of a box set (round 28, review) ---

def test_the_small_parts_of_a_box_are_parts_the_export_takes():
    """Latches, handle, pins and hinges are untagged, their component carries the part role; the export left them out,
    a right-click on a set gave Base and Lid only"""
    for role in ("Latch", "Handle", "Handle pin", "Hinge"):
        assert exportParts.isPartBody(None, role, role=role)
    assert not exportParts.isPartBody(None, "Component1", role=None)
    assert not exportParts.isPartBody(None, "Box", role="Box")


def test_the_small_part_roles_are_the_box_parts():
    parts = _load("predBoxParts", "lib", "gridfinityUtils", "predBoxParts.py")
    assert set(exportParts.SMALL_PART_ROLES) == {part.role for part in parts.PARTS}


def test_a_small_part_carries_its_sets_name():
    assert exportParts.partFileName("Latch", "Box 5×4×6") == "Box 5×4×6 Latch"


# ---------------------------------------------------------------------------
# Round r29-export: what the print layout needs of a part
# ---------------------------------------------------------------------------

def test_a_labels_surface_comes_from_its_tag():
    assert exportParts.labelSurface(("label", {"config": {"surface": "Flush"}})) == "Flush"
    assert exportParts.labelSurface(("label", {"config": {"surface": "Embossed"}})) == "Embossed"


def test_parts_without_a_label_surface_have_none():
    assert exportParts.labelSurface(None) is None
    assert exportParts.labelSurface(("bin", {"config": {"surface": "Flush"}})) is None
    assert exportParts.labelSurface(("label", {})) is None
    assert exportParts.labelSurface(("label", {"config": "broken"})) is None


def test_parts_of_one_place_and_turn_go_together():
    # the halves of a hinge: one occurrence, one turn; its pin turns on its own
    keys = [("hinge 1", "none"), ("latch", "none"), ("hinge 1", "none"), ("hinge 1", "x-90"), (None, "none"), (None, "none")]
    assert exportParts.printGroups(keys) == [[0, 2], [1], [3], [4], [5]]


printBeds = _load("printBeds", "commands", "commandCreateBaseplate", "printBeds.py")
BED_NAMES = [printBeds.PRINT_BED_CUSTOM] + list(printBeds.PRINT_BED_PRESETS)


def test_the_default_bed_is_one_of_the_baseplate_dialogs():
    assert exportParts.DEFAULT_BED in printBeds.PRINT_BED_PRESETS
    assert printBeds.PRINT_BED_PRESETS[exportParts.DEFAULT_BED] == (exportParts.DEFAULT_BED_SIZE, exportParts.DEFAULT_BED_SIZE)


def test_layout_choices_default_to_values():
    choices = exportParts.layoutChoices({}, BED_NAMES)
    assert choices == {"bed": "Bambu Lab A1, P1, X1 (256 x 256 mm)", "bedWidth": 256.0, "bedLength": 256.0, "spacing": 5.0, "purge": 50.0}


def test_layout_choices_are_read_back():
    section = {"bed": "Custom", "bedWidth": "300", "bedLength": "320.5", "spacing": "8", "purge": "0"}
    assert exportParts.layoutChoices(section, BED_NAMES) == {"bed": "Custom", "bedWidth": 300.0, "bedLength": 320.5, "spacing": 8.0, "purge": 0.0}


def test_broken_layout_choices_fall_back():
    section = {"bed": "Gone printer", "bedWidth": "-3", "bedLength": "abc", "spacing": "-1", "purge": "x"}
    choices = exportParts.layoutChoices(section, BED_NAMES)
    assert choices["bed"] == "Custom"
    assert (choices["bedWidth"], choices["bedLength"], choices["spacing"], choices["purge"]) == (256.0, 256.0, 5.0, 50.0)


def test_the_box_label_is_a_part_by_a_tag_of_its_own():
    # p380: not the Cullenect insert's tag, the settings menu and rebuild would take it for an insert
    assert _tag_constants()["TAG_BOX_LABEL"] == "boxLabel"
    assert exportParts.isPartBody("boxLabel", "Box label 5")


def test_a_box_labels_surface_comes_from_its_tag():
    assert exportParts.labelSurface(("boxLabel", {"config": {"surface": "Flush"}})) == "Flush"


def test_the_export_reads_the_box_label_tag_too():
    source = open(os.path.join(PROJECT_ROOT, "commands", "commandExport", "entry.py"), encoding="utf-8").read()
    assert "tagUtils.readBodyTag(native)" not in source
    assert source.count("tagUtils.readExportTag(") >= 2


def test_layout_choices_survive_the_config_file():
    # review r29-export: configparser writes its keys in lower case, bedWidth came back as the default
    import configparser
    config = configparser.ConfigParser()
    config["Export"] = {"bed": "Custom", "bedWidth": "180", "bedLength": "210", "spacing": "8", "purge": "40"}
    choices = exportParts.layoutChoices(dict(config["Export"]), BED_NAMES)
    assert (choices["bedWidth"], choices["bedLength"], choices["spacing"], choices["purge"]) == (180.0, 210.0, 8.0, 40.0)


def test_only_the_halves_of_a_hinge_are_one_block():
    # review r29-export: the pieces of a filled area are bodies of one baseplate component, they go apart
    assert exportParts.printGroupKey("Hinge", "Box:1+Hinge 1:1", "none") == ("Box:1+Hinge 1:1", "none")
    assert exportParts.printGroupKey(None, "Grid:1", "none")[0] is None
    assert exportParts.printGroupKey("Latch", "Box:1+Latch:1", "none")[0] is None
    assert exportParts.printGroupKey("Hinge", None, "none")[0] is None


def _entry_function(name):
    tree = ast.parse(open(os.path.join(PROJECT_ROOT, "commands", "commandExport", "entry.py"), encoding="utf-8").read())
    return ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name))


def test_a_change_in_the_bed_group_updates_the_whole_dialog():
    # review r29-export: inside a group args.inputs holds only the group's inputs, as the baseplate dialog notes
    source = _entry_function("command_input_changed")
    assert "args.input.parentCommand.commandInputs" in source
    assert "updateInputs(args.inputs)" not in source


def test_a_size_typed_turns_the_bed_to_custom_only_when_it_differs_from_the_preset():
    source = _entry_function("bedInputChanged")
    assert "math.isclose" in source


def test_the_3mf_goes_out_as_a_file_per_plate():
    source = _entry_function("export3mf")
    assert "printLayout.plateFileName(" in source
    assert "exportParts.printGroupKey(" in source


def test_older_plate_files_are_replaced_too():
    # review r29-export: a plate file of an earlier export with more plates stayed beside the new ones
    source = _entry_function("export3mf")
    assert "printLayout.isPlateFileOf(" in source
    assert "os.remove(" in source


def test_the_format_tooltip_tells_of_a_file_per_plate():
    source = open(os.path.join(PROJECT_ROOT, "commands", "commandExport", "entry.py"), encoding="utf-8").read()
    assert "3MF puts every body in one file" not in source
