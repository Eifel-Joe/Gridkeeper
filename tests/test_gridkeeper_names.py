"""
Round 23, p234: the add-in shows as Gridkeeper everywhere, its command ids no longer collide with the original
FusionGridfinityGenerator, and what parts already built carry stays as it is, so they still show their settings and can
be rebuilt and cloned (16.11.2026: the name Gridkeeper is visible everywhere, internal identifiers stay). The modules
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
            elif (isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'tr'
                  and isinstance(node.value.args[0], ast.Constant)):
                # a name in the add-in's language, the English text is the call's argument (round 60)
                found[node.targets[0].id] = node.value.args[0].value
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
    assert "tr('Save Gridkeeper config')" in source and "tr('Load Gridkeeper config')" in source


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
    # the storage box after Pred (round 27)
    assert _constants('commands/commandCreateBox/boxBuilder.py')['BOX_PARAMETER_BASE_NAME'] == 'gfBox'
    assert generators['GENERATOR_BOX'] == 'box'
    assert _constants('lib/tagUtils.py')['TAG_BOX'] == 'box'


def test_manifest_is_gridkeepers():
    manifest = json.load(open(os.path.join(ROOT, 'Gridkeeper.manifest'), encoding='utf-8'))
    assert manifest['id'] != 'bbbd3c0a-34f1-4bcf-b9f9-accd46c35cd0'
    assert re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', manifest['id'])
    assert manifest['version'] == '1.5.0'
    description = manifest['description']['']
    assert 'Gridkeeper' in description and 'Le0Michine' in description


def test_release_zip_is_named_gridkeeper():
    workflow = open(os.path.join(ROOT, '.github', 'workflows', 'release.yml'), encoding='utf-8').read()
    # tag gridkeeper-v1.0.0 gives Gridkeeper-v1.0.0.zip, only Gridkeeper's own tags start a release (16.11.2026)
    assert 'zip="dist/Gridkeeper-${GITHUB_REF_NAME#gridkeeper-}.zip"' in workflow
    assert "- 'gridkeeper-v*'" in workflow and "- '*'" not in workflow
    # review 16.11.2026: the repository's token is read-only by default, the release step needs write access
    assert 'permissions:\n  contents: write' in workflow
    # round 25: the files are named like the folder, Fusion loads the add-in only then
    assert 'cp -r Gridkeeper.manifest Gridkeeper.py' in workflow and '7z a' in workflow and 'Gridkeeper/' in workflow


def test_add_in_files_are_named_like_the_folder():
    assert os.path.isfile(os.path.join(ROOT, 'Gridkeeper.manifest')) and os.path.isfile(os.path.join(ROOT, 'Gridkeeper.py'))
    assert not os.path.exists(os.path.join(ROOT, 'GridfinityGenerator.manifest'))


def _sources(*patterns):
    for pattern in patterns:
        for path in glob.glob(os.path.join(ROOT, pattern), recursive=True):
            yield (path, open(path, encoding='utf-8').read())


def test_bug_reports_go_to_the_fork():
    # review round 23: two startup errors still linked the original's issues
    for (path, source) in _sources('commands/**/*.py', 'lib/**/*.py', 'commands/**/*.html', 'lib/**/*.html'):
        assert 'Le0Michine/FusionGridfinityGenerator/issues' not in source, path


def test_no_old_ids_in_pages_either():
    for (path, source) in _sources('commands/**/*.html', 'commands/**/*.js', 'lib/**/*.html', 'lib/**/*.js'):
        assert 'LevMishin_GridfinityGenerator' not in source, path


def test_every_palette_title_says_gridkeeper():
    found = 0
    for (path, source) in _sources('commands/**/*.py', 'lib/**/*.py'):
        for match in re.finditer(r"^PALETTE_TITLE = (?:tr\()?'([^']*)'", source, re.MULTILINE):
            found += 1
            assert match.group(1).startswith('Gridkeeper '), path
    assert found >= 3


@pytest.mark.parametrize('folder', ['commandCreateBin', 'commandCreateBaseplate', 'commandCreateLabel', 'commandCreateBox'])
def test_settings_of_a_part_are_titled_by_the_part(folder):
    # review round 23: the first section of the settings window took the command's name, "Gridkeeper bin" under the
    # window title "Gridfinity bin"; it names the part like the window does
    source = open(os.path.join(ROOT, 'commands', folder, 'entry.py'), encoding='utf-8').read()
    call = re.search(r'snapshotInputs\(\s*inputs,\s*\[[^\]]*\],\s*([A-Z_]+),?\s*\)', source)
    assert call is not None and call.group(1) == 'SETTINGS_TITLE'
    assert _constants(f'commands/{folder}/entry.py')['SETTINGS_TITLE'].startswith('Gridfinity ')


def test_error_reports_go_to_the_renamed_repository():
    from lib import errorReport
    assert errorReport.ISSUES_URL == 'https://github.com/Eifel-Joe/Gridkeeper/issues/new'


def test_dialog_help_links_go_to_the_gridkeeper_docs():
    # 16.11.2026: "Here on our GitHub" in the bin dialog still opened the original's wiki
    for (path, source) in _sources('commands/**/*.py', 'lib/**/*.py', 'commands/**/*.html', 'lib/**/*.html'):
        assert 'Le0Michine/FusionGridfinityGenerator/wiki' not in source, path
    bins = open(os.path.join(ROOT, 'commands/commandCreateBin/entry.py'), encoding='utf-8').read()
    plates = open(os.path.join(ROOT, 'commands/commandCreateBaseplate/entry.py'), encoding='utf-8').read()
    assert 'https://eifel-joe.github.io/Gridkeeper/bins/' in bins
    assert 'https://eifel-joe.github.io/Gridkeeper/baseplates/' in plates
    labels = open(os.path.join(ROOT, 'commands/commandCreateLabel/entry.py'), encoding='utf-8').read()
    assert 'https://eifel-joe.github.io/Gridkeeper/cullenect/inserts/' in labels
    boxes = open(os.path.join(ROOT, 'commands/commandCreateBox/entry.py'), encoding='utf-8').read()
    assert 'https://eifel-joe.github.io/Gridkeeper/boxes/' in boxes
