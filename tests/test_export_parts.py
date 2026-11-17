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
    assert exportParts.EXPORT_TAGS == ("bin", "baseplate", "label", "box")


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
