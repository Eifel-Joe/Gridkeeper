"""
German input names fit the label column of their dialog (click test round 60). Fusion cuts a name off at about 23
characters in a 450 px dialog, the column grows with the dialog. A wider German dialog was tried and dropped: the API
can't place a dialog, Fusion opens it where the narrower one was and it ran off the screen. So the dialogs keep their
English widths and the German names are short; the tooltip says the rest. Group titles span the whole dialog.
"""

import ast
import glob
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# characters of a name in a 450 px dialog, others in proportion to their width
CHARACTERS_AT_450 = 22
DIALOG_WIDTHS = {
    "commandCreateBin": 450, "commandCreateBaseplate": 450, "commandExport": 450, "commandShowSettings": 450,
    "commandUpdates": 420, "commandCreateBox": 400, "commandCreateBoxLabel": 400, "commandCreateLabel": 400,
}
# lib/ui helpers go into several dialogs, the narrowest counts
SHARED_WIDTH = min(DIALOG_WIDTHS.values())
GERMAN = json.load(open(os.path.join(ROOT, "lib", "i18n", "de.json"), encoding="utf-8"))


def _name(func) -> str:
    return func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")


def _key(call: ast.Call) -> str | None:
    if not (isinstance(call, ast.Call) and _name(call.func) == "tr" and call.args and isinstance(call.args[0], ast.Constant)):
        return None
    if len(call.args) > 1 and isinstance(call.args[1], ast.Constant):
        return f"{call.args[1].value}|{call.args[0].value}"
    return call.args[0].value


def inputNames(path: str) -> list[tuple[int, str]]:
    """The tr() texts passed as an input's name: to Fusion's add...Input calls and the add-in's add... helpers, not to groups"""
    names = []
    for node in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
        if not isinstance(node, ast.Call):
            continue
        name = _name(node.func)
        if not name.startswith("add") or "Group" in name or "Tab" in name:
            continue
        # Fusion's add...Input(id, name, ...) has the name second, its third is a prompt or a text box's text; the
        # add-in's helpers take it second or third
        fusion = isinstance(node.func, ast.Attribute) and name.endswith("Input")
        for argument in node.args[1:2] if fusion else node.args[1:3]:
            key = _key(argument)
            if key is not None:
                names.append((node.lineno, key))
                break
    return names


def _sources():
    sources = []
    for path in sorted(glob.glob(os.path.join(ROOT, "commands", "*", "entry.py"))):
        folder = os.path.basename(os.path.dirname(path))
        if folder in DIALOG_WIDTHS:
            sources.append((path, DIALOG_WIDTHS[folder]))
    sources += [(path, SHARED_WIDTH) for path in sorted(glob.glob(os.path.join(ROOT, "lib", "ui", "*.py")))]
    return sources


@pytest.mark.parametrize("path, width", _sources(), ids=lambda value: os.path.relpath(value, ROOT) if isinstance(value, str) else str(value))
def test_german_input_names_fit_their_dialog(path, width):
    limit = round(CHARACTERS_AT_450 * width / 450)
    tooLong = [f"line {line}: {GERMAN[key]} ({len(GERMAN[key])})" for (line, key) in inputNames(path)
               if len(GERMAN.get(key, "")) > limit]
    assert tooLong == [], f"longer than {limit} characters"


def test_the_scan_finds_names_of_helpers_too():
    source = "x.addBoolValueInput('id', tr('Show preview (slow)'), True)\naddCheckbox(inputs, 'id', tr('Lid'))\nx.addGroupCommandInput('g', tr('Bin features'))\n"
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_labels_sample.py")
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(source)
        assert [key for (_, key) in inputNames(path)] == ["Show preview (slow)", "Lid"]
    finally:
        os.remove(path)


def test_german_rebuild_notes_are_no_longer_than_the_english_ones():
    """Click test round 60: the info area of a dialog shows two lines, the German rebuild note was cut off. Until it
    grows with its text the German note keeps to the English one's length"""
    notes = {key: value for (key, value) in GERMAN.items() if key.startswith("<b>Rebuilding {name}</b>")}
    assert len(notes) == 3
    assert {key: len(value) for (key, value) in notes.items() if len(value) > len(key)} == {}
