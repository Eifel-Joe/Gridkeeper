"""
Round 58: a rebuilt box, box label and label insert keep the names the user gave them, as bins and baseplates do since
GridfinityGenerator 5d30bfa. Their tags hold the names the generator gave, the rebuild passes the prefix of those names,
and the box's own renaming of its parts only drops Fusion's counter, it doesn't undo a name the user gave a part.
Source checks for the Fusion code, the name rule on rebuildUtils' source as in test_rebuild_names.
"""

import ast
import os
import re
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REBUILD_UTILS = os.path.join(ROOT, "lib", "rebuildUtils.py")
BUILDERS = {
    "box": (os.path.join(ROOT, "commands", "commandCreateBox", "boxBuilder.py"), "BOX_NAME_PREFIX"),
    "box label": (os.path.join(ROOT, "commands", "commandCreateBoxLabel", "boxLabelBuilder.py"), "LABEL_NAME_PREFIX"),
    "insert": (os.path.join(ROOT, "commands", "commandCreateLabel", "labelBuilder.py"), "LABEL_NAME_PREFIX"),
}


def _source(path):
    with open(path, encoding="utf-8") as file:
        return file.read()


def _rebuild_utils(*names):
    namespace = {"re": re}
    tree = ast.parse(_source(REBUILD_UTILS))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    future = ast.parse("from __future__ import annotations").body
    exec(compile(ast.Module(body=future + functions, type_ignores=[]), REBUILD_UTILS, "exec"), namespace)
    return types.SimpleNamespace(**{name: namespace[name] for name in names})


def _calls(source, name):
    """The source of every call of name, a dotted name like rebuildUtils.rebuild"""
    calls = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and ast.unparse(node.func) == name:
            calls.append(node)
    return calls


def test_each_rebuild_passes_the_prefix_of_its_names():
    for (title, (path, prefix)) in BUILDERS.items():
        calls = _calls(_source(path), "rebuildUtils.rebuild")
        assert len(calls) == 1, title
        keywords = {keyword.arg: ast.unparse(keyword.value) for keyword in calls[0].keywords}
        assert keywords.get("namePrefix") == prefix, title


def test_each_tag_holds_the_generated_names():
    for (title, (path, _)) in BUILDERS.items():
        for call in _calls(_source(path), "tagUtils.tagBody"):
            keywords = {keyword.arg for keyword in call.keywords}
            assert {"name", "bodyName"} <= keywords, title


def test_the_name_prefixes_start_the_generated_names():
    # the prefix tells a generated name from the user's in a tag without names, see rebuildUtils.isGeneratedName
    folder = os.path.join(ROOT, "lib", "gridfinityUtils")
    for (title, layout, nameStart) in [
        ("box", "predBoxConfig.py", "return f'Box {state.gridX}"),
        ("box label", "predBoxLabelLayout.py", "return f'Gridkeeper box label {cells}"),
        ("insert", "cullenectLabelLayout.py", "return f'Gridfinity label {size}"),
    ]:
        (path, constant) = BUILDERS[title]
        value = re.search(rf"^{constant} = '([^']*)'$", _source(path), re.MULTILINE).group(1)
        assert nameStart in _source(os.path.join(folder, layout)), title
        assert nameStart[len("return f'"):].startswith(value), title


def test_a_part_drops_only_fusions_counter():
    names = _rebuild_utils("withoutCounter", "rebuiltPartName")
    assert names.rebuiltPartName("Lid (1)", "Lid") == "Lid"
    assert names.rebuiltPartName("Latch (2)", "Latch") == "Latch"
    assert names.rebuiltPartName("Lid", "Lid") is None
    # a name the user gave the part, back from the old one, stays
    assert names.rebuiltPartName("Deckel", "Lid") is None
    assert names.rebuiltPartName("Deckel (1)", "Lid") is None


def test_the_box_renames_its_parts_by_that_rule():
    source = _source(BUILDERS["box"][0])
    body = source[source.index("def _renameParts("):]
    body = body[:body.index("\ndef ", 1)] if "\ndef " in body[1:] else body
    assert "rebuildUtils.rebuiltPartName(component.name, role)" in body
