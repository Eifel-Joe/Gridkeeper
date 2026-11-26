# Shared by the Fusion jobs of the update round (p310): loads lib/updateCheck.py and lib/updateInstall.py of the
# worktree by path, they import nothing of the add-in, and builds a test add-in folder or release ZIP from the worktree
# as release.yml does. Plain Python, also used outside Fusion (build_test_install.py).
import importlib.util
import io
import json
import os
import zipfile

WORKTREE = r'D:\Entwicklung\Gridfinity\Gridkeeper\.claude\worktrees\upstream-2026-11-16-e588a3'
# what release.yml copies into the ZIP's Gridkeeper folder
RELEASE_FILES = ['Gridkeeper.manifest', 'Gridkeeper.py', 'config.py', 'LICENSE.md', 'lib', 'commands',
                 'documentation/PRIVACY_POLICY.md']


def load(name):
    # a package of lib's folder: since 1.5.0 both modules import lib/i18n relatively
    import sys
    import types
    package = 'uh_lib'
    if package not in sys.modules:
        packageModule = types.ModuleType(package)
        packageModule.__path__ = [os.path.join(WORKTREE, 'lib')]
        sys.modules[package] = packageModule
    spec = importlib.util.spec_from_file_location(f'{package}.{name}', os.path.join(WORKTREE, 'lib', name + '.py'))
    module = importlib.util.module_from_spec(spec)
    module.__package__ = package
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def releaseFiles(version):
    """relative path -> bytes of the add-in as release.yml packs it, the manifest set to version"""
    files = {}
    for entry in RELEASE_FILES:
        path = os.path.join(WORKTREE, *entry.split('/'))
        paths = [path] if os.path.isfile(path) else [
            os.path.join(root, name) for (root, folders, names) in os.walk(path)
            for name in names if '__pycache__' not in root and 'commandConfig' not in root]
        for filePath in paths:
            relative = os.path.relpath(filePath, WORKTREE).replace(os.sep, '/')
            with open(filePath, 'rb') as file:
                files[relative] = file.read()
    manifest = json.loads(files['Gridkeeper.manifest'].decode('utf-8'))
    manifest['version'] = version
    files['Gridkeeper.manifest'] = json.dumps(manifest, indent='\t').encode('utf-8')
    return files


def releaseZip(version):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('Gridkeeper/', b'')
        for (name, data) in releaseFiles(version).items():
            archive.writestr('Gridkeeper/' + name, data)
    return buffer.getvalue()


def writeFolder(folder, version, extra=None):
    for (name, data) in {**releaseFiles(version), **(extra or {})}.items():
        path = os.path.join(folder, *name.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as file:
            file.write(data)
    return folder
