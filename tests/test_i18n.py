"""
The add-in's language (Fusion's language, German or English, an override file wins) and the lookup of its texts,
see lib/i18n and dev-notes/specs/2026-11-26-r60-german.md.
"""

import importlib.util
import os
import sys
from types import SimpleNamespace

import adsk.core
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    path = os.path.join(ROOT, "lib", "i18n", "__init__.py")
    spec = importlib.util.spec_from_file_location("i18n_under_test", path, submodule_search_locations=[])
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


i18n = _load()


def _preferences(language):
    return SimpleNamespace(generalPreferences=SimpleNamespace(userLanguage=language))


class _Raising:
    @property
    def generalPreferences(self):
        raise RuntimeError("no preferences")


@pytest.fixture
def german():
    i18n.setLanguage("de", {"Bin type": "Behältertyp", "container|Label": "Einleger", "Label": "Beschriftung",
                            "Total bin {name}: {value}mm": "Behälter gesamt {name}: {value} mm"})
    yield
    i18n.setLanguage("en")


def test_german_fusion_gives_german():
    assert i18n.detectLanguage(_preferences(adsk.core.UserLanguages.GermanLanguage), None) == "de"


@pytest.mark.parametrize("language", ["EnglishLanguage", "FrenchLanguage", "JapaneseLanguage"])
def test_other_languages_give_english(language):
    assert i18n.detectLanguage(_preferences(getattr(adsk.core.UserLanguages, language)), None) == "en"


def test_no_preferences_or_an_error_gives_english():
    assert i18n.detectLanguage(None, None) == "en"
    assert i18n.detectLanguage(_Raising(), None) == "en"


@pytest.mark.parametrize("text, expected", [("de", "de"), (" DE\n", "de"), ("en", "en"), ("En ", "en")])
def test_the_override_wins(text, expected):
    other = adsk.core.UserLanguages.EnglishLanguage if expected == "de" else adsk.core.UserLanguages.GermanLanguage
    assert i18n.detectLanguage(_preferences(other), text) == expected


@pytest.mark.parametrize("text", ["", "fr", "deutsch", None])
def test_other_override_text_is_ignored(text):
    assert i18n.detectLanguage(_preferences(adsk.core.UserLanguages.GermanLanguage), text) == "de"
    assert i18n.detectLanguage(_preferences(adsk.core.UserLanguages.EnglishLanguage), text) == "en"


def test_english_returns_the_text():
    i18n.setLanguage("en")
    assert i18n.tr("Bin type") == "Bin type"
    assert i18n.tr("Label", "container") == "Label"


def test_german_looks_up_the_text(german):
    assert i18n.tr("Bin type") == "Behältertyp"


def test_a_context_picks_its_own_entry(german):
    assert i18n.tr("Label", "container") == "Einleger"
    assert i18n.tr("Label") == "Beschriftung"


def test_a_missing_entry_falls_back_to_english(german):
    assert i18n.tr("Not translated") == "Not translated"
    assert i18n.tr("Not translated", "ctx") == "Not translated"


def test_values_are_formatted_after_the_lookup(german):
    assert i18n.tr("Total bin {name}: {value}mm", name="Breite", value="83,5") == "Behälter gesamt Breite: 83,5 mm"
    i18n.setLanguage("en")
    assert i18n.tr("Total bin {name}: {value}mm", name="width", value="83.5") == "Total bin width: 83.5mm"


def test_numbers_get_a_decimal_comma_in_german(german):
    assert i18n.number(83.5) == "83,5"
    assert i18n.number("0.25") == "0,25"
    assert i18n.number(42) == "42"


def test_numbers_stay_as_they_are_in_english():
    i18n.setLanguage("en")
    assert i18n.number(83.5) == "83.5"
    assert i18n.number("0.25") == "0.25"


def test_the_german_table_is_read_from_de_json():
    table = i18n.readTable("de")
    assert isinstance(table, dict)
    assert all(isinstance(key, str) and isinstance(value, str) for (key, value) in table.items())
    assert i18n.readTable("en") == {}


def test_strings_for_a_page_are_the_ones_it_names(german):
    assert i18n.pageStrings(["Bin type", "Not translated"]) == {"Bin type": "Behältertyp"}
    i18n.setLanguage("en")
    assert i18n.pageStrings(["Bin type"]) == {}


def test_placeholders_may_be_named_text_or_context(german):
    """tr's own parameters are positional only, a {text} or {context} placeholder is a value like any other"""
    assert i18n.tr("Cullenect: {text}", text="ok") == "Cullenect: ok"
    assert i18n.tr("{context} and {text}", context="a", text="b") == "a and b"
    assert i18n.trKnown("Cullenect: {text}", text="ok") == "Cullenect: ok"
