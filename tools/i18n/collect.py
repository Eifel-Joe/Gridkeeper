"""
The texts the add-in shows, for keeping lib/i18n/de.json complete (tests/test_i18n_complete.py) and for translators.

Python: every call of tr('English text'[, 'context']) and trValue('value') in the add-in's code, read with ast, the text and the context
must be string literals. Pages: data-i18n, data-i18n-title and data-i18n-placeholder attributes and calls of
fusionBridge.t('English text'). The development commands stay English and are left out.

Usage: python tools/i18n/collect.py [--missing | --stale]
  --missing  the texts without a German entry, as JSON to fill in
  --stale    the entries no code uses any more
"""

import ast
import importlib.util

import json
import os
import re
import string
import sys

CONTEXT_SEPARATOR = '|'
# English only (dev-notes/specs/2026-11-26-r60-german.md)
DEVELOPMENT_COMMANDS = ('commandSnapshotTests', 'commandModelScreenshots')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _loadI18n():
    """lib/i18n by its path, it reads pages the same way for the dialogs (lib/ui/browserPages.py)"""
    spec = importlib.util.spec_from_file_location('gridkeeper_i18n', os.path.join(ROOT, 'lib', 'i18n', '__init__.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


i18n = _loadI18n()


# tr translates a literal, trValue marks a value a dropdown shows translated (lib/ui/dropdowns.py)
COLLECTED = ('tr', 'trValue')


def _isTr(func: ast.expr) -> bool:
    if isinstance(func, ast.Name):
        return func.id in COLLECTED
    return isinstance(func, ast.Attribute) and func.attr in COLLECTED and isinstance(func.value, ast.Name) and func.value.id == 'i18n'


def _literal(node) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def collectTexts(source: str, fileName: str) -> tuple[set[str], list[str]]:
    """The keys of the tr calls in a Python source, and an error for each call whose text isn't a literal"""
    texts = set()
    errors = []
    for node in ast.walk(ast.parse(source, fileName)):
        if not (isinstance(node, ast.Call) and _isTr(node.func)):
            continue
        text = _literal(node.args[0]) if node.args else None
        contextNodes = node.args[1:2] + [keyword.value for keyword in node.keywords if keyword.arg == 'context']
        context = _literal(contextNodes[0]) if contextNodes else None
        if text is None or (contextNodes and context is None):
            errors.append(f'{fileName}:{node.lineno} tr() needs a literal text and context')
            continue
        texts.add(f'{context}{CONTEXT_SEPARATOR}{text}' if context else text)
    return (texts, errors)


def collectPageTexts(page: str) -> set[str]:
    """The texts a page (HTML or JavaScript) has translated"""
    return i18n.pageTexts(page)


def _isDevelopment(path: str) -> bool:
    return any(part in DEVELOPMENT_COMMANDS for part in path.replace(os.sep, '/').split('/'))


def _walk(root: str, folders: list[str], extensions: tuple[str, ...]) -> list[str]:
    files = []
    for folder in folders:
        for (directory, subfolders, names) in os.walk(os.path.join(root, folder)):
            subfolders[:] = [name for name in subfolders if name != '__pycache__' and name not in DEVELOPMENT_COMMANDS]
            files.extend(os.path.join(directory, name) for name in names if name.endswith(extensions))
    return sorted(path for path in files if not _isDevelopment(os.path.relpath(path, root)))


def sourceFiles(root: str) -> list[str]:
    return _walk(root, ['commands', 'lib'], ('.py',)) + [os.path.join(root, 'Gridkeeper.py')]


def pageFiles(root: str) -> list[str]:
    return _walk(root, ['commands', 'lib'], ('.html', '.js'))


def pageFileTexts(path: str) -> set[str]:
    with open(path, encoding='utf-8') as file:
        return collectPageTexts(file.read())


def collectAll(root: str) -> tuple[set[str], list[str]]:
    texts = set()
    errors = []
    for path in sourceFiles(root):
        with open(path, encoding='utf-8') as file:
            (found, failed) = collectTexts(file.read(), os.path.relpath(path, root))
        texts |= found
        errors += failed
    for path in pageFiles(root):
        texts |= pageFileTexts(path)
    return (texts, errors)


def _placeholders(text: str) -> set[str]:
    try:
        return {field for (_, field, _, _) in string.Formatter().parse(text) if field is not None}
    except ValueError:
        return {'<unbalanced braces>'}


def checkTable(texts: set[str], table: dict[str, str]) -> dict[str, list[str]]:
    """Texts without a German entry, entries no text uses, entries with other placeholders than their English text"""
    missing = sorted(text for text in texts if not table.get(text))
    stale = sorted(key for key in table if key not in texts)
    placeholders = sorted(text for text in texts if table.get(text)
                          and _placeholders(text.split(CONTEXT_SEPARATOR, 1)[-1]) != _placeholders(table[text]))
    return {'missing': missing, 'stale': stale, 'placeholders': placeholders}


def main(arguments: list[str]) -> int:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    (texts, errors) = collectAll(root)
    for error in errors:
        print(error, file=sys.stderr)
    with open(os.path.join(root, 'lib', 'i18n', 'de.json'), encoding='utf-8') as file:
        table = json.load(file)
    report = checkTable(texts, table)
    if '--stale' in arguments:
        print(json.dumps(report['stale'], ensure_ascii=False, indent=1))
    elif '--missing' in arguments:
        print(json.dumps({text: '' for text in report['missing']}, ensure_ascii=False, indent=1))
    else:
        print({name: len(items) for (name, items) in report.items()})
    return 1 if errors or any(report.values()) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
