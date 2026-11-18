"""
Upstream round 17.11. (p300): what the export takes as a part, bins, baseplates, Cullenect inserts and later boxes,
and how the colored text bodies of a part go into its mesh, painted for the slicer.
"""

import ast
import pytest
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

def triangle_mesh(name, offset, painted=None):
    return threeMf.MeshObject(name, [(offset, 0, 0), (offset + 1, 0, 0), (offset, 1, 0)], [(0, 1, 2)], dict(painted or {}))


def test_text_meshes_join_their_part_and_are_painted():
    part = threeMf.MeshObject("Bin", [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)], [(0, 1, 2), (1, 3, 2)], {1: 4})
    merged = exportParts.withMarkings(part, [(triangle_mesh("t1", 5), 2), (triangle_mesh("t2", 9), 2)])
    assert merged.name == "Bin"
    assert len(merged.vertices) == 10
    assert merged.triangles == [(0, 1, 2), (1, 3, 2), (4, 5, 6), (7, 8, 9)]
    # the part's own painted letters stay, every text triangle is painted
    assert merged.painted == {1: 4, 2: 2, 3: 2}


def test_each_text_mesh_is_painted_with_its_colors_filament():
    # round 37 (p301): red text on 2, blue on 3
    part = triangle_mesh("Bin", 0)
    merged = exportParts.withMarkings(part, [(triangle_mesh("red", 5), 2), (triangle_mesh("blue", 9), 3)])
    assert merged.painted == {1: 2, 2: 3}


def test_unpainted_text_meshes_still_complete_the_part():
    part = triangle_mesh("Insert", 0)
    merged = exportParts.withMarkings(part, [(triangle_mesh("t", 5), None)])
    assert merged.triangles == [(0, 1, 2), (3, 4, 5)]
    assert merged.painted == {}


def test_a_part_without_text_stays_as_it_is():
    part = triangle_mesh("Baseplate", 0, painted={0: 2})
    assert exportParts.withMarkings(part, []) == part


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


def test_layout_choices_default_to_the_documented_values():
    choices = exportParts.layoutChoices({}, BED_NAMES)
    assert choices == {"bed": "Bambu Lab P1P, P1S, X1, X1C, X1E (256 x 256 mm)", "bedWidth": 256.0, "bedLength": 256.0, "spacing": 5.0, "purge": 50.0}


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


def test_the_question_tells_replaced_files_from_removed_ones():
    # review r29-export: older plate files are removed, not replaced, the question must say so
    question = exportParts.replaceQuestion(["Box.3mf"], ["Box, plate 2.3mf", "Box, plate 3.3mf"], "D:/out", 8)
    assert question.startswith("Replace the existing file and remove 2 plate files of an earlier export in D:/out?")
    assert "Box.3mf" in question and "Box, plate 3.3mf" in question


def test_the_question_for_removed_files_alone():
    question = exportParts.replaceQuestion([], ["Box, plate 2.3mf"], "D:/out", 8)
    assert question.startswith("Remove 1 plate file of an earlier export in D:/out?")


def test_the_question_for_replaced_files_alone_stays_as_it_was():
    question = exportParts.replaceQuestion(["a.stl", "b.stl"], [], "D:/out", 8)
    assert question.startswith("Replace 2 existing files in D:/out?")


def test_the_question_lists_a_few_and_counts_the_rest():
    question = exportParts.replaceQuestion([f"{n}.stl" for n in range(10)], [], "D:/out", 8)
    assert "and 2 more" in question


def test_an_older_plate_file_that_cant_be_removed_doesnt_fail_the_export():
    source = _entry_function("export3mf")
    assert "except OSError" in source


def test_the_layout_keeps_the_printers_tower_spot_and_excluded_area_free():
    # Bambu click test 17.11.2026 (F1, F2): when the printer is given exactly, the exclusion zone is no longer
    # the user's concern
    source = _entry_function("export3mf")
    assert "printBeds.purgeAnchor(layout['bed'])" in source
    assert "printBeds.excludedAreas(layout['bed'])" in source


def test_a_plate_near_an_excluded_area_is_named_painted_or_not():
    # review r29-export: it was named only with paint, and as without room for the purge tower
    source = _entry_function("plateNote")
    assert "nearExcluded" in source
    assert "if nearExcluded" in source


def test_the_purge_square_only_when_label_text_is_painted():
    # a box set has no text: with Color label text on nothing is painted and no tower is printed
    source = _entry_function("export3mf")
    assert "if filaments is not None and paintedCount > 0" in source


@pytest.mark.parametrize("role, tag, body, setName, kind", [
    ("Box", "box", "Base", "Box 5×4×6", ("Box 5×4×6", "box")),
    ("Lid", "box", "Lid", "Box 5×4×6", ("Box 5×4×6", "lid")),
    ("Latch", None, "Latch", "Box 5×4×6", ("Box 5×4×6", "parts")),
    ("Handle", None, "Handle", "Box 5×4×6", ("Box 5×4×6", "parts")),
    ("Handle pin", None, "Handle pin", "Box 5×4×6", ("Box 5×4×6", "parts")),
    ("Hinge", None, "Hinge pin", "Box 5×4×6", ("Box 5×4×6", "parts")),
    # a box built as bodies in the root: no set, its bodies by name
    (None, "box", "Base", None, (None, "box")),
    (None, "box", "Lid", None, (None, "lid")),
    (None, "bin", "Gridfinity bin 1x2x3", None, None),
    (None, "label", "Gridfinity label", None, None),
    (None, "boxLabel", "Box label", None, None),
])
def test_a_box_sets_box_lid_and_small_parts_go_on_plates_of_their_own(role, tag, body, setName, kind):
    # 17.11.2026: the box's accessories go on a separate plate; a box comes to 3 plates depending on its size
    assert exportParts.plateKind(role, tag, body, setName) == kind


def test_the_export_lays_out_by_kind():
    source = _entry_function("export3mf")
    assert "printLayout.layOutKinds(" in source
    assert "exportParts.plateKind(" in source


def test_the_old_shared_bambu_bed_is_read_as_the_p1_and_x1():
    # review r29-export: the click test's export saved it, Custom would put the tower back right again
    choices = exportParts.layoutChoices({"bed": "Bambu Lab A1, P1, X1 (256 x 256 mm)"}, BED_NAMES)
    assert choices["bed"] == "Bambu Lab P1P, P1S, X1, X1C, X1E (256 x 256 mm)"


def test_the_dialog_summary_tells_of_a_file_per_plate():
    # Found in testing 17.11.2026: the summary still said "26 parts, one file" after the export got a 3MF per plate
    source = open(os.path.join(PROJECT_ROOT, "commands", "commandExport", "entry.py"), encoding="utf-8").read()
    assert "'one file' if format == FORMAT_3MF" not in source
    assert "a 3MF file per plate" in source


# --- round 37 (p301): each label color on a filament of its own, bodies on 1 ---

def test_label_colors_get_filaments_from_2_in_their_order():
    assert exportParts.assignFilaments(["#D02020", "#2060D0", ""], {}) == {"#D02020": 2, "#2060D0": 3, "": 4}


def test_a_saved_filament_wins_and_the_others_skip_it():
    assert exportParts.assignFilaments(["#D02020", "#2060D0"], {"#2060D0": 2}) == {"#D02020": 3, "#2060D0": 2}


def test_a_new_color_skips_the_saved_filaments_of_other_colors():
    # review round 37: red exported alone got 2, blue alone 2 too, together they shared a filament unasked
    assert exportParts.assignFilaments(["#D02020"], {"#2060D0": 2}) == {"#D02020": 3}
    assigned = exportParts.assignFilaments(["#2060D0"], {"#D02020": 2})
    assert exportParts.assignFilaments(["#D02020", "#2060D0"], {"#D02020": 2, **assigned}) == {"#D02020": 2, "#2060D0": 3}


def test_when_every_filament_is_saved_a_new_color_takes_one_free_in_the_export():
    saved = {f"#0000{index:02X}": index for index in range(2, 19)}
    assert exportParts.assignFilaments(["#D02020", "#000005"], saved) == {"#D02020": 2, "#000005": 5}


def test_two_colors_may_share_a_filament_when_saved_so():
    assert exportParts.assignFilaments(["#D02020", "#2060D0"], {"#D02020": 2, "#2060D0": 2}) == {"#D02020": 2, "#2060D0": 2}


def test_past_the_last_filament_the_colors_share_it():
    keys = [f"#0000{index:02X}" for index in range(20)]
    assigned = exportParts.assignFilaments(keys, {})
    assert [assigned[key] for key in keys] == list(range(2, 19)) + [18, 18, 18]
    assert exportParts.MAX_FILAMENT == threeMf.MAX_FILAMENT


def test_the_label_filaments_are_saved_and_read_back():
    mapping = {"#D02020": 2, "#2060D0": 3, "": 4}
    text = exportParts.formatLabelFilaments(mapping)
    assert text == "D02020=2,2060D0=3,none=4"
    assert exportParts.parseLabelFilaments(text) == mapping


@pytest.mark.parametrize("text", ["", "D02020", "D02020=x", "D02020=0", "D02020=19", "XYZ=2", "=2", ",,"])
def test_broken_saved_entries_are_left_out(text):
    assert exportParts.parseLabelFilaments(text + ",2060D0=3") == {"#2060D0": 3}


def test_saving_keeps_the_colors_not_shown():
    assert exportParts.mergeLabelFilaments({"#2060D0": 3, "#D02020": 2}, {"#D02020": 5}) == {"#2060D0": 3, "#D02020": 5}


def _config_section(text):
    import configparser
    parser = configparser.ConfigParser()
    parser.read_string(text)
    return dict(parser["Export"])


def test_an_old_config_keeps_its_label_color_index_for_text_without_a_color():
    # an export before round 37 saved one index for all label text: outline letters keep printing on it
    section = _config_section("[Export]\nfolder = exports\nformat = 3MF\npaint = yes\ncolorIndex = 4\n")
    assert exportParts.labelFilamentChoices(section) == {"": 4}


def test_an_old_config_with_a_broken_index_has_no_saved_filaments():
    for index in ("x", "0", "19"):
        assert exportParts.labelFilamentChoices(_config_section(f"[Export]\ncolorIndex = {index}\n")) == {}


def test_the_saved_label_filaments_win_over_the_old_index():
    section = _config_section("[Export]\ncolorIndex = 4\nlabelFilaments = none=6,D02020=2\n")
    assert exportParts.labelFilamentChoices(section) == {"": 6, "#D02020": 2}
    section = _config_section("[Export]\ncolorIndex = 4\nlabelFilaments = D02020=2\n")
    assert exportParts.labelFilamentChoices(section) == {"#D02020": 2, "": 4}


def test_the_export_paints_each_text_body_with_its_colors_filament():
    # round 37 (p301): the color comes from the Text occurrence's appearance, else the body's
    source = _entry_function("partMesh")
    assert "filamentOf(marking.labelColor)" in source
    assert "filamentOf('') if item.hasOutlineLabels" in source
    entry = open(os.path.join(PROJECT_ROOT, "commands", "commandExport", "entry.py"), encoding="utf-8").read()
    assert "for holder in (self.occurrence, self.body):" in entry


def test_the_dialog_saves_the_label_filaments_and_reads_the_old_index():
    assert "exportParts.labelFilamentChoices(dict(section))" in _entry_function("readChoices")
    source = _entry_function("saveChoices")
    assert "'labelFilaments': exportParts.formatLabelFilaments(exportParts.mergeLabelFilaments(saved, filaments))" in source
    assert "colorIndex" not in source


def test_a_filament_changed_by_hand_is_kept_without_rebuilding_the_inputs():
    # its input mustn't be deleted while its own change is handled
    source = _entry_function("command_input_changed")
    assert "dialogFilaments[color] = " in source
    after_keeping = source.split("dialogFilaments[color] = ")[1].splitlines()
    assert after_keeping[1].strip() == "return"
    assert "!= [filamentInputId(color) for color in colors]" in _entry_function("updateFilamentInputs")


def test_the_filaments_that_go_out_are_saved():
    # review round 37: a color assigned only at export time wasn't saved
    source = _entry_function("command_execute")
    assert "saveChoices(folder, format, paint, {**shown, **filaments}, layout)" in source
    assert source.index("filaments = exportParts.assignFilaments(") < source.index("saveChoices(")


def test_label_colors_are_listed_once_even_when_a_part_repeats_them():
    # Fusion run r37: one bin's letters are several marking bodies of the same color
    perPart = [["", "#D02020", "#D02020", "#D02020"], ["#2060D0", "#2060D0", "#D02020", ""]]
    assert exportParts.distinctLabelColors(perPart) == ["", "#D02020", "#2060D0"]


def test_label_colors_of_the_dialog_use_the_distinct_list():
    source = _entry_function("labelColorsOf")
    assert "exportParts.distinctLabelColors(" in source


# Click test r37 C: a filament typed into the dialog was lost when the selection changed. Fusion fires a spinner's
# inputChanged only for some ways of leaving the field, so the rebuild reads the spinners' values itself.
RED = "#D02020"
BLUE = "#2060D0"


def test_a_typed_filament_survives_a_selection_change_without_its_change_event():
    assigned = exportParts.assignFilaments([RED, BLUE, ""], {"": 4})
    assert assigned == {RED: 2, BLUE: 3, "": 4}
    shown = {RED: 2, BLUE: 5, "": 4}  # blue typed as 5, no inputChanged arrived
    changed = exportParts.keepTypedFilaments({"": 4}, shown, assigned)
    assert exportParts.assignFilaments([BLUE], changed) == {BLUE: 5}
    assert exportParts.assignFilaments([RED, BLUE, ""], changed) == {RED: 2, BLUE: 5, "": 4}


def test_filaments_left_as_assigned_stay_automatic():
    assigned = {RED: 2, BLUE: 3}
    changed = exportParts.keepTypedFilaments({}, {RED: 2, BLUE: 3}, assigned)
    assert changed == {}
    # blue alone then takes the lowest free number again
    assert exportParts.assignFilaments([BLUE], changed) == {BLUE: 2}


def test_a_typed_filament_set_back_to_its_assigned_number_is_still_kept():
    # the change event did arrive earlier and stored it; the spinner shows the same number
    changed = exportParts.keepTypedFilaments({BLUE: 3}, {BLUE: 3}, {BLUE: 3})
    assert changed == {BLUE: 3}


def test_keeping_typed_filaments_leaves_its_input_alone():
    changed = {"": 4}
    exportParts.keepTypedFilaments(changed, {BLUE: 5}, {BLUE: 3})
    assert changed == {"": 4}


def test_the_dialog_reads_typed_filaments_before_it_rebuilds_them():
    source = _entry_function("updateFilamentInputs")
    keep = source.index("exportParts.keepTypedFilaments(")
    rebuild = source.index("deleteMe()")
    assert keep < rebuild
    assert "dialogAssigned" in source


def test_a_filament_typed_back_to_its_assigned_number_beats_the_one_stored_before():
    # review r37: blue typed 5 (event arrived, stored), then typed back to 3 without an event
    changed = exportParts.keepTypedFilaments({BLUE: 5}, {BLUE: 3}, {BLUE: 3})
    assert changed == {BLUE: 3}


# Click test r37 D: a number typed into a Fusion spinner and confirmed by clicking OK straight from the field never
# reached the command (no inputChanged, value unchanged). Decided: a list 1 to 18 per color instead of a spinner.
def test_filament_choices_are_the_numbers_1_to_18():
    assert exportParts.filamentChoices() == [str(n) for n in range(1, 19)]


def test_a_filament_choice_reads_back_as_its_number():
    assert exportParts.filamentOfChoice("7") == 7
    assert exportParts.filamentOfChoice("18") == 18


def test_a_filament_choice_outside_the_list_reads_as_none():
    for name in ("", "0", "19", "x", None):
        assert exportParts.filamentOfChoice(name) is None


def test_the_dialog_offers_each_color_a_list_of_filaments_not_a_spinner():
    source = open(os.path.join(PROJECT_ROOT, "commands", "commandExport", "entry.py"), encoding="utf-8").read()
    assert "IntegerSpinnerCommandInput" not in source
    update = _entry_function("updateFilamentInputs")
    assert "addDropDownCommandInput(" in update
    assert "exportParts.filamentChoices()" in update


def test_the_dialog_reads_a_filament_from_the_selected_list_item():
    assert "exportParts.filamentOfChoice(" in _entry_function("selectedFilament")
    for name in ("shownFilaments", "command_input_changed"):
        assert "selectedFilament(" in _entry_function(name), name


def test_typed_lengths_of_the_export_dialog_are_shown_formatted():
    # round 41, p291: "2.9" typed into the bed or spacing inputs is shown as "2.90 mm" like in the other dialogs
    source = open(os.path.join(PROJECT_ROOT, "commands", "commandExport", "entry.py"), encoding="utf-8").read()
    assert "from ...lib.ui import expressionFormat" in source
    changed = source[source.index("def command_input_changed("):source.index("\ndef ", source.index("def command_input_changed(") + 1)]
    call = changed.index("expressionFormat.request(")
    lengths = changed[changed.rindex("if args.input.id in (", 0, call):call]
    for inputId in ("BED_WIDTH_INPUT_ID", "BED_LENGTH_INPUT_ID", "SPACING_INPUT_ID", "PURGE_INPUT_ID"):
        assert inputId in lengths
