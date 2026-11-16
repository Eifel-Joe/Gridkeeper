"""
Every module of the add-in compiles. The unit tests import only some of them: a syntax error in a builder passed
pytest and stopped the add-in in Fusion (round 18, labelBuilder.py, an apostrophe in a single quoted string).
"""

import os
import py_compile

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDERS = ['commands', 'lib']
FILES = [os.path.join(root, name) for folder in FOLDERS for (root, _, names) in os.walk(os.path.join(PROJECT_ROOT, folder)) for name in names if name.endswith('.py')]
FILES.append(os.path.join(PROJECT_ROOT, 'GridfinityGenerator.py'))


@pytest.mark.parametrize('path', FILES, ids=lambda path: os.path.relpath(path, PROJECT_ROOT))
def test_module_compiles(path, tmp_path):
    py_compile.compile(path, cfile=str(tmp_path / 'module.pyc'), doraise=True)
