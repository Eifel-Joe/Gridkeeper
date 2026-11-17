"""
The context menu of generated bodies (commands/commandShowSettings/entry.py): rebuild and, since the merge of upstream
in round 22 (4ae7afb by Le0Michine), clone, for bins, baseplates and the inserts of this fork. The module needs Fusion
to load, so its source is read: a later merge mustn't drop the inserts or leave a definition behind on stop.
"""

import ast
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = open(os.path.join(PROJECT_ROOT, 'commands', 'commandShowSettings', 'entry.py'), encoding='utf-8').read()
TREE = ast.parse(SOURCE)


def _dict_keys(name):
    for node in TREE.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return [ast.unparse(key) for key in node.value.keys]
    raise AssertionError(f'{name} not found')


def _function(name):
    return next(node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name == name)


def test_clone_and_rebuild_cover_inserts():
    for name in ('CLONE_COMMANDS', 'REBUILD_COMMANDS'):
        assert _dict_keys(name) == ['tagUtils.TAG_BIN', 'tagUtils.TAG_BASEPLATE', 'tagUtils.TAG_LABEL', 'tagUtils.TAG_BOX', 'tagUtils.TAG_BOX_LABEL'], name


def test_stop_deletes_every_definition():
    source = ast.unparse(_function('stop'))
    for commandId in ('CMD_ID', 'REBUILD_CMD_ID', 'CLONE_CMD_ID'):
        assert commandId in source


def test_clone_needs_a_config_in_the_tag():
    # bodies generated before the generator kept the config can't be cloned
    source = ast.unparse(_function('canClone'))
    assert 'CLONE_COMMANDS' in source and 'tagUtils.buildConfig(' in source


def test_one_clone_item_in_the_menu():
    source = ast.unparse(_function('marking_menu_displaying'))
    assert source.count('CLONE_CMD_ID') == 1
