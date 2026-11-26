"""
The texts the add-in shows, for keeping lib/i18n/de.json complete (tests/test_i18n_complete.py) and for translators.

Python: every call of tr('English text'[, 'context']) and trValue('value') in the add-in's code and string constants marked
'# tr-value' (Fusion-free modules), read with ast, the text and the context
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
# on the last line of an assignment: '# tr-value' a string, '# tr-values' the strings of a list, a tuple or the values of
# a dict, '# tr-keys' the keys of a dict; a word after it is the context, as in tr(text, context)
VALUE_MARK = re.compile(r'#\s*tr-(value|values|keys)\b(?:\s+(\w+))?')


def _markedValues(node: ast.expr, kind: str) -> list[str] | None:
    """The strings a mark names, none when the assignment isn't what the mark needs"""
    if kind == 'value':
        items = [node]
    elif kind == 'values' and isinstance(node, (ast.List, ast.Tuple)):
        items = node.elts
    elif kind == 'values' and isinstance(node, ast.Dict):
        items = node.values
    elif kind == 'keys' and isinstance(node, ast.Dict):
        items = node.keys
    else:
        return None
    values = [_literal(item) for item in items]
    return None if None in values else values


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
    lines = source.splitlines()
    for node in ast.walk(ast.parse(source, fileName)):
        # values in a module that can't import lib/i18n (Fusion-free ones): NAME = 'Value'  # tr-value
        mark = VALUE_MARK.search(lines[node.end_lineno - 1]) if isinstance(node, ast.Assign) else None
        if mark:
            values = _markedValues(node.value, mark.group(1))
            if values is None:
                errors.append(f'{fileName}:{node.lineno} # tr-{mark.group(1)} needs string literals')
            else:
                context = mark.group(2)
                texts |= {f'{context}{CONTEXT_SEPARATOR}{value}' if context else value for value in values}
            continue
        if not (isinstance(node, ast.Call) and _isTr(node.func)):
            continue
        text = _literal(node.args[0]) if node.args else None
        # tr's text and context are positional only, keywords are placeholders
        contextNodes = node.args[1:2]
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


def collectFiles(root: str, paths: list[str]) -> tuple[set[str], list[str]]:
    """The texts of some files only, Python or pages"""
    texts = set()
    errors = []
    for path in paths:
        with open(os.path.join(root, path), encoding='utf-8') as file:
            source = file.read()
        if path.endswith('.py'):
            (found, failed) = collectTexts(source, path)
            (texts, errors) = (texts | found, errors + failed)
        else:
            texts |= collectPageTexts(source)
    return (texts, errors)


def _option(arguments: list[str], name: str) -> list[str]:
    """The values after --name up to the next option"""
    if name not in arguments:
        return []
    values = arguments[arguments.index(name) + 1:]
    return values[:next((i for (i, value) in enumerate(values) if value.startswith('--')), len(values))]


def main(arguments: list[str]) -> int:
    """
    --files PATH...  only these files' texts (missing only, stale needs all files)
    --extra JSON...  further German entries beside de.json, such as a translator's part not merged yet
    """
    root = ROOT
    files = _option(arguments, '--files')
    (texts, errors) = collectFiles(root, files) if files else collectAll(root)
    for error in errors:
        print(error, file=sys.stderr)
    with open(os.path.join(root, 'lib', 'i18n', 'de.json'), encoding='utf-8') as file:
        table = json.load(file)
    for extra in _option(arguments, '--extra'):
        with open(extra, encoding='utf-8') as file:
            table.update(json.load(file))
    report = checkTable(texts, table)
    if files:
        report['stale'] = []
    if '--stale' in arguments:
        print(json.dumps(report['stale'], ensure_ascii=False, indent=1))
    elif '--missing' in arguments:
        print(json.dumps({text: '' for text in report['missing']}, ensure_ascii=False, indent=1))
    else:
        print({name: len(items) for (name, items) in report.items()})
    return 1 if errors or any(report.values()) else 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
