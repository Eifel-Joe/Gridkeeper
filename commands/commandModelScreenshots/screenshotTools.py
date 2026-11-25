import json
import os
import shutil
import subprocess
import sys

# What the pictures palette runs outside Fusion (round 58): the docs' animations, dev-notes/tools/anim/compose.py, and
# the dialog screenshots, tools/screenshots/screenshots.py, each with a Python that has what it needs. Fusion's own
# Python has no imaging. The Python is found without a venv of its own: the checkout's tools/screenshots/.venv, the
# main checkout's for a git worktree, or a Python on the computer that has the modules. Kept free of Fusion imports
# so it can be unit tested

# variables Fusion sets for its own Python, another Python started from Fusion must not see them
FUSION_PYTHON_VARIABLES = ['PYTHONHOME', 'PYTHONPATH', 'PYTHONEXECUTABLE', '__PYVENV_LAUNCHER__']
# Pythons of the computer, tried in turn: the Windows launcher, then what is on the path
SYSTEM_PYTHONS = [['py', '-3'], ['python'], ['python3']]
ANIM_FOLDER = os.path.join('dev-notes', 'tools', 'anim')
GIF_THEMES = ['light', 'dark']

def venvPython(checkout: str) -> str:
    venv = os.path.join(checkout, 'tools', 'screenshots', '.venv')
    return os.path.join(venv, 'Scripts', 'python.exe') if sys.platform == 'win32' else os.path.join(venv, 'bin', 'python')

def mainCheckout(checkout: str) -> str | None:
    """The main checkout of a git worktree, whose .git is a file naming .git/worktrees/<name> there, none otherwise"""
    gitFile = os.path.join(checkout, '.git')
    if not os.path.isfile(gitFile):
        return None
    with open(gitFile, encoding='utf-8') as file:
        line = file.readline().strip()
    if not line.startswith('gitdir:'):
        return None
    # git writes it absolute, or relative to the worktree with worktree.useRelativePaths
    gitDir = os.path.normpath(os.path.join(checkout, line[len('gitdir:'):].strip()))
    # <main>/.git/worktrees/<name>
    parts = gitDir.split(os.sep)
    if len(parts) < 3 or parts[-2] != 'worktrees' or parts[-3] != '.git':
        return None
    return os.sep.join(parts[:-3])

def toolEnvironment(environment: dict) -> dict:
    return {key: value for (key, value) in environment.items() if key not in FUSION_PYTHON_VARIABLES}

def canRun(command: list[str], modules: list[str]) -> bool:
    """Whether the Python runs and imports the modules"""
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        result = subprocess.run([*command, '-c', f'import {", ".join(modules)}'], env=toolEnvironment(dict(os.environ)),
                                capture_output=True, timeout=30, creationflags=flags)
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False

def findPython(checkout: str, modules: list[str], main: str | None = None, system: list[list[str]] = None,
               exists=os.path.exists, canRun=canRun) -> list[str] | None:
    """The command of the first Python that has the modules, see the module's comment, none without one"""
    candidates = [[venvPython(checkout)]]
    if main is not None:
        candidates.append([venvPython(main)])
    for command in (SYSTEM_PYTHONS if system is None else system):
        candidates.append(command)
    for command in candidates:
        isFile = os.path.isabs(command[0]) or os.sep in command[0]
        if isFile and not exists(command[0]):
            continue
        if not isFile and system is None and shutil.which(command[0]) is None:
            continue
        if canRun(command, modules):
            return command
    return None

def composeCommand(python: list[str], checkout: str, name: str) -> list[str]:
    """compose.py making one animation, its light and dark GIF"""
    return [*python, os.path.join(checkout, ANIM_FOLDER, 'compose.py'), name]

def savedFile(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    return {'file': path, 'version': int(os.path.getmtime(path) * 1000)}

def gifRows(animFolder: str, gifFolder: str, saved=savedFile) -> list[dict]:
    """
    The animations of anims.json: their GIFs by theme, the raw pictures of their states compose.py puts together
    (raw/<name>/<n>-model.png and -dialog.png), the ones missing, and if one changed after the GIF was made
    """
    with open(os.path.join(animFolder, 'anims.json'), encoding='utf-8') as file:
        anims = json.load(file)
    rows = []
    for (name, states) in anims.items():
        # a state may name a dialog picture of another, as compose.py reads it
        pictures = list(dict.fromkeys(picture for (index, state) in enumerate(states, 1)
                                      for picture in (f'{index}-model.png', state.get('dialog', f'{index}-dialog.png'))))
        paths = [os.path.join(animFolder, 'raw', name, picture) for picture in pictures]
        files = {f'model-{theme}': saved(os.path.join(gifFolder, f'{name}-{theme}.gif')) for theme in GIF_THEMES}
        made = files['model-light']
        rows.append({
            'name': name,
            'description': ' · '.join(state.get('caption', '') for state in states),
            'pictures': pictures,
            'missing': [picture for (picture, path) in zip(pictures, paths) if not os.path.exists(path)],
            'outdated': bool(made) and any(os.path.exists(path) and os.path.getmtime(path) > os.path.getmtime(made['file']) for path in paths),
            'files': files,
        })
    return rows
