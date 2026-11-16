"""
Round 23, p234: the add-in shows as Gridkeeper everywhere, its command ids no longer collide with the original
FusionGridfinityGenerator, and what parts already built carry stays as it is, so they still show their settings and can
be rebuilt and cloned (Nutzer 16.11.2026: "Name Gridkeeper ueberall sichtbar; interne Kennungen bleiben"). The modules
need Fusion to load, their constants are read from the source.
"""

import ast
import glob
import json
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _constants(path: str) -> dict[str, str]:
    """String constants assigned at the top of a module, f-strings by their source"""
    tree = ast.parse(open(os.path.join(ROOT, path), encoding='utf-8').read())
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                found[node.targets[0].id] = node.value.value
            elif isinstance(node.value, ast.JoinedStr):
                found[node.targets[0].id] = ast.unparse(node.value)
    return found


COMMAND_FILES = sorted(glob.glob(os.path.join(ROOT, 'commands', '*', 'entry.py')))


@pytest.mark.parametrize('path', COMMAND_FILES, ids=lambda path: os.path.basename(os.path.dirname(path)))
def test_command_names_say_gridkeeper(path):
    names = {name: value for (name, value) in _constants(path).items() if name.endswith('CMD_NAME')}
    assert len(names) > 0
    for (name, value) in names.items():
        assert value.startswith('Gridkeeper '), (name, value)


@pytest.mark.parametrize('path', [
    'lib/ui/errorPalette.py',
    'commands/commandSnapshotTests/reportPalette.py',
    'commands/commandModelScreenshots/picturesPalette.py',
])
def test_window_titles_say_gridkeeper(path):
    assert _constants(path)['PALETTE_TITLE'].startswith('Gridkeeper ')


def test_config_dialogs_say_gridkeeper():
    source = open(os.path.join(ROOT, 'lib', 'ui', 'configButtons.py'), encoding='utf-8').read()
    assert 'Gridfinity config' not in source
    assert "'Save Gridkeeper config'" in source and "'Load Gridkeeper config'" in source


def test_ids_no_longer_those_of_the_original():
    config = _constants('config.py')
    assert (config['COMPANY_NAME'], config['ADDIN_NAME']) == ('EifelJoe', 'Gridkeeper')
    # every id is made of these two, none is written out with the original's
    for path in glob.glob(os.path.join(ROOT, '**', '*.py'), recursive=True):
        if os.sep + 'tests' + os.sep in path:
            continue
        assert 'LevMishin_GridfinityGenerator' not in open(path, encoding='utf-8').read(), path


def test_what_built_parts_carry_stays():
    # the tag group, the parameter prefixes, the generator names and the names of the bodies: parts built before
    # still show their settings, rebuild and clone
    assert _constants('lib/tagUtils.py')['TAG_GROUP'] == 'LevMishin.GridfinityGenerator'
    assert _constants('commands/commandSnapshotTests/entry.py')['TEST_TAG_GROUP'] == 'LevMishin.GridfinityGenerator.Tests'
    assert _constants('commands/commandCreateBin/binBuilder.py')['BIN_PARAMETER_BASE_NAME'] == 'gfBin'
    assert _constants('commands/commandCreateBaseplate/baseplateBuilder.py')['BASEPLATE_PARAMETER_BASE_NAME'] == 'gfPlate'
    assert _constants('commands/commandCreateLabel/labelBuilder.py')['LABEL_PARAMETER_BASE_NAME'] == 'gfLabel'
    assert _constants('commands/commandCreateLabel/labelBuilder.py')['LABEL_NAME_PREFIX'] == 'Gridfinity label'
    generators = _constants('lib/configJson.py')
    assert (generators['GENERATOR_BIN'], generators['GENERATOR_BASEPLATE'], generators['GENERATOR_LABEL']) == ('bin', 'baseplate', 'label')


def test_manifest_is_gridkeepers():
    manifest = json.load(open(os.path.join(ROOT, 'GridfinityGenerator.manifest'), encoding='utf-8'))
    assert manifest['id'] != 'bbbd3c0a-34f1-4bcf-b9f9-accd46c35cd0'
    assert re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', manifest['id'])
    assert manifest['version'] == '1.0.0'
    description = manifest['description']['']
    assert 'Gridkeeper' in description and 'Le0Michine' in description


def test_release_zip_is_named_gridkeeper():
    workflow = open(os.path.join(ROOT, '.github', 'workflows', 'release.yml'), encoding='utf-8').read()
    assert 'dist/Gridkeeper-${{ github.ref_name }}.zip' in workflow
