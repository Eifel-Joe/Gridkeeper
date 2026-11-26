"""
Every text the add-in shows has a German entry in lib/i18n/de.json, no entry is left over and the placeholders
match, see tools/i18n/collect.py and dev-notes/specs/2026-11-26-r60-german.md.
"""

import importlib.util
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    path = os.path.join(ROOT, "tools", "i18n", "collect.py")
    spec = importlib.util.spec_from_file_location("i18n_collect", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


collect = _load()


def test_tr_calls_are_found_with_their_context():
    source = "from ..lib.i18n import tr\nx = tr('Bin type')\ny = i18n.tr(\"Label\", 'container')\nz = tr('Lid', context='box')\n"
    (texts, errors) = collect.collectTexts(source, "x.py")
    assert texts == {"Bin type", "container|Label", "box|Lid"}
    assert errors == []


def test_values_marked_for_dropdowns_are_found():
    source = "HOLLOW = trValue('Hollow')\nSOLID = i18n.trValue('Solid')\nx = trKnown(v)\n"
    (texts, errors) = collect.collectTexts(source, "x.py")
    assert texts == {"Hollow", "Solid"}
    assert errors == []


def test_values_are_no_part_of_the_key():
    (texts, errors) = collect.collectTexts("tr('Total {name}', name=n)\n", "x.py")
    assert texts == {"Total {name}"}
    assert errors == []


def test_other_functions_are_ignored():
    (texts, errors) = collect.collectTexts("_('x')\nother.tr2('y')\ngettext('z')\nstr('w')\n", "x.py")
    assert texts == set()
    assert errors == []


@pytest.mark.parametrize("call", ["tr(name)", "tr(f'Bin {x}')", "tr('a' + b)", "tr('a', ctx)", "tr()"])
def test_a_text_built_at_runtime_is_an_error(call):
    (texts, errors) = collect.collectTexts(call + "\n", "x.py")
    assert texts == set()
    assert len(errors) == 1 and "x.py:1" in errors[0]


def test_page_texts_are_found():
    html = """
    <h1 data-i18n="Compartments">Compartments</h1>
    <button data-i18n-title="Merge the cells" title="Merge the cells">+</button>
    <input data-i18n-placeholder="Label text &amp; more" placeholder="x">
    <script>
        const a = fusionBridge.t('Depth {depth}', {depth: 3});
        const b = fusionBridge.t("Reset");
    </script>
    """
    assert collect.collectPageTexts(html) == {"Compartments", "Merge the cells", "Label text & more", "Depth {depth}", "Reset"}


def test_the_table_check_reports_missing_stale_and_placeholders():
    texts = {"Bin type", "Total {name}", "container|Label"}
    table = {"Bin type": "Behältertyp", "Total {name}": "Gesamt {nam}", "Old text": "Alter Text"}
    report = collect.checkTable(texts, table)
    assert report["missing"] == ["container|Label"]
    assert report["stale"] == ["Old text"]
    assert report["placeholders"] == ["Total {name}"]


def test_an_empty_german_text_is_missing():
    report = collect.checkTable({"Bin type"}, {"Bin type": ""})
    assert report["missing"] == ["Bin type"]


def test_the_development_commands_are_left_out():
    files = [os.path.relpath(path, ROOT).replace(os.sep, "/") for path in collect.sourceFiles(ROOT)]
    assert "commands/commandCreateBin/entry.py" in files
    assert "lib/ui/commandUiState.py" in files
    assert "Gridkeeper.py" in files
    assert not any(f.startswith(("commands/commandSnapshotTests/", "commands/commandModelScreenshots/")) for f in files)
    pages = [os.path.relpath(path, ROOT).replace(os.sep, "/") for path in collect.pageFiles(ROOT)]
    assert "commands/commandCreateBin/html/compartments.html" in pages
    assert "lib/ui/html/fusionBridge.js" in pages
    assert not any(f.startswith(("commands/commandSnapshotTests/", "commands/commandModelScreenshots/")) for f in pages)


def test_german_table_complete():
    """The whole add-in: every text translated, nothing left over, the same placeholders"""
    (texts, errors) = collect.collectAll(ROOT)
    assert errors == []
    with open(os.path.join(ROOT, "lib", "i18n", "de.json"), encoding="utf-8") as file:
        table = json.load(file)
    report = collect.checkTable(texts, table)
    assert report == {"missing": [], "stale": [], "placeholders": []}
