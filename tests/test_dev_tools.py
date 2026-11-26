# p320: the developer commands (snapshot tests, model images) show when the add-in runs from a git checkout, in a clone
# (.git folder) and in a git worktree (.git file). config.py is loaded the way Fusion loads it, as part of the add-in's
# package, from a copy of the real config.py, lib/updateInstall.py and lib/i18n
import importlib
import importlib.util
import itertools
import os
import shutil
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
counter = itertools.count()


def loadConfig(addinFolder):
    (addinFolder / 'lib').mkdir()
    shutil.copy(os.path.join(PROJECT_ROOT, 'config.py'), addinFolder / 'config.py')
    shutil.copy(os.path.join(PROJECT_ROOT, 'lib', 'updateInstall.py'), addinFolder / 'lib' / 'updateInstall.py')
    # updateInstall shows its errors in the add-in's language
    shutil.copytree(os.path.join(PROJECT_ROOT, 'lib', 'i18n'), addinFolder / 'lib' / 'i18n', ignore=shutil.ignore_patterns('__pycache__'))
    # lib has no __init__.py in the add-in either, it is a namespace package
    (addinFolder / '__init__.py').write_text('')
    package = f'devtools_addin_{next(counter)}'
    spec = importlib.util.spec_from_file_location(package, addinFolder / '__init__.py',
                                                  submodule_search_locations=[str(addinFolder)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[package] = module
    try:
        spec.loader.exec_module(module)
        return importlib.import_module(package + '.config')
    finally:
        for name in [name for name in sys.modules if name == package or name.startswith(package + '.')]:
            del sys.modules[name]


@pytest.mark.parametrize('git', ['folder', 'file', None])
def test_dev_tools_in_a_git_checkout(tmp_path, git):
    addinFolder = tmp_path / 'Gridkeeper'
    addinFolder.mkdir()
    if git == 'folder':
        (addinFolder / '.git').mkdir()
    elif git == 'file':
        # a git worktree has a .git file pointing to the repository
        (addinFolder / '.git').write_text('gitdir: D:/Entwicklung/Gridfinity/Gridkeeper/.git/worktrees/wt-r33')
    assert loadConfig(addinFolder).DEV_TOOLS is (git is not None)
