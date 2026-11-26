"""
The add-in's texts in Fusion's language: German when Fusion is set to German, English otherwise
(dev-notes/specs/2026-11-26-r60-german.md).

English is the source, the text in the code is the key: tr('Bin type'). German comes from de.json beside this file,
English text to German text; a context tells apart the same English word with two meanings, its key is
'context|text'. tests/test_i18n_complete.py keeps de.json complete. The function is tr and not gettext's _, the code
uses _ as a throwaway name, which would shadow it.

Only what the user reads is translated: values the add-in keeps (dropdown values, configs, tags) stay English, see
lib/ui/dropdowns.py.
"""

import json
import os

LANGUAGES = ('en', 'de')
DEFAULT_LANGUAGE = 'en'
# the add-in's folder, ignored by git: 'de' or 'en' wins over Fusion's language, for tests and for English in a German
# Fusion
OVERRIDE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'languageOverride')
CONTEXT_SEPARATOR = '|'

_language: str | None = None
_table: dict[str, str] = {}


def detectLanguage(preferences, overrideText: str | None) -> str:
    """'de' for Fusion's German, 'en' for any other language and when its preferences can't be read"""
    override = (overrideText or '').strip().lower()
    if override in LANGUAGES:
        return override
    try:
        import adsk.core
        if preferences is not None and preferences.generalPreferences.userLanguage == adsk.core.UserLanguages.GermanLanguage:
            return 'de'
    except Exception:
        pass
    return DEFAULT_LANGUAGE


def readTable(language: str) -> dict[str, str]:
    """German entries of de.json, none for English, which is the code's own text"""
    if language == DEFAULT_LANGUAGE:
        return {}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'{language}.json')
    try:
        with open(path, encoding='utf-8') as file:
            return json.load(file)
    except (OSError, ValueError):
        return {}


def _readOverride() -> str | None:
    try:
        with open(OVERRIDE_FILE, encoding='utf-8') as file:
            return file.read()
    except OSError:
        return None


def _fusionPreferences():
    try:
        import adsk.core
        return adsk.core.Application.get().preferences
    except Exception:
        return None


def setLanguage(language: str, table: dict[str, str] | None = None) -> None:
    """The language from now on, with its table from de.json unless one is given (tests)"""
    global _language, _table
    _language = language if language in LANGUAGES else DEFAULT_LANGUAGE
    _table = table if table is not None else readTable(_language)


def language() -> str:
    """Read once: Fusion needs a restart after its language changes"""
    if _language is None:
        setLanguage(detectLanguage(_fusionPreferences(), _readOverride()))
    return _language


def key(text: str, context: str | None = None) -> str:
    return f'{context}{CONTEXT_SEPARATOR}{text}' if context else text


def _lookup(text: str, context: str | None, values: dict) -> str:
    language()
    translated = _table.get(key(text, context), text)
    return translated.format(**values) if values else translated


def tr(text: str, context: str | None = None, **values) -> str:
    """The text in the add-in's language, English when it has no entry, then formatted with the values"""
    return _lookup(text, context, values)


def trValue(text: str) -> str:
    """Marks a value a dropdown shows translated (tools/i18n/collect.py finds it), the value itself stays English"""
    return text


def trKnown(text: str, context: str | None = None, **values) -> str:
    """tr for a text marked elsewhere, with trValue or a tr call, where the code only has it in a variable"""
    return _lookup(text, context, values)


def number(value) -> str:
    """A number for a text, with a decimal comma in German; strings are taken as they are formatted"""
    text = value if isinstance(value, str) else f'{value:g}'
    return text.replace('.', ',') if language() == 'de' else text


def pageStrings(texts) -> dict[str, str]:
    """The entries of texts a page shows, for the page to replace, none in English"""
    language()
    return {text: _table[text] for text in texts if text in _table}
