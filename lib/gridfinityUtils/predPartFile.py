"""
Round 49 (p610): the box's latch, handle pin and hinge (after Pred's parametric Gridfinity Storage Box v1.1,
https://www.printables.com/model/543553, CC BY-NC, by Pred) kept on disk as well, behind the session's memory of
predPartCache, so the first box after Fusion starts need not draw them (spec
dev-notes/specs/2026-11-19-r49-small-parts-file.md).

The parts are still drawn in code; the file is only a store the add-in writes and reads itself, no part file ships.
Where: partCache in the add-in folder, beside updateConfig and the dialog defaults (git ignores it, an update does not
carry it over, updateInstall.CARRY_OVER_SKIPPED_FOLDERS). Per part and key of predPartCache.cacheKey a pair
<version>-<code>-<role>[-<hinge>].smt with the bodies and .json with their names in order (an .smt keeps no body
names; snapshots and export go by them). <code> is a hash of lib/gridfinityUtils, so a code change without a version
step (a git checkout) reads no stale file.

Fusion's export and import come in as io (FusionIo), the rest runs in pytest.
"""

from __future__ import annotations

import hashlib
import json
import os
import re

FOLDER_NAME = 'partCache'
# the kinds of file the store writes; clean-up deletes nothing else
OWN_SUFFIXES = ('.smt', '.json', '.tmp')
CODE_SUFFIXES = ('.py', '.json')


def addinFolder() -> str:
    """lib/gridfinityUtils/predPartFile.py → the add-in folder"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def codeStamp(folder: str) -> str:
    """
    12 hex digits of a SHA-256 over every .py and .json file below folder (relative path and content, sorted by path,
    __pycache__ left out). Line endings are made LF first: git on Windows checks out CRLF, a release zip has what the
    tag has, the same code gives the same key. The whole folder, not the generators' imports: it cannot miss a module
    the drawing uses, the price is one redraw after any change there
    """
    files = []
    for (root, folders, names) in os.walk(folder):
        folders[:] = [name for name in folders if name != '__pycache__']
        for name in names:
            if name.endswith(CODE_SUFFIXES):
                path = os.path.join(root, name)
                files.append((os.path.relpath(path, folder).replace(os.sep, '/'), path))
    digest = hashlib.sha256()
    for (relative, path) in sorted(files):
        with open(path, 'rb') as file:
            content = file.read().replace(b'\r\n', b'\n')
        digest.update(relative.encode('utf-8') + b'\0' + content + b'\0')
    return digest.hexdigest()[:12]


def keyPrefix(version: str, stamp: str) -> str:
    return f'{version}-{stamp}-'


def fileStem(version: str, stamp: str, key: tuple) -> str:
    """'1.1.0-abc123def456-Hinge-Pinned' for ('Hinge', 'Pinned'), blanks as _ ('Handle_pin')"""
    return keyPrefix(version, stamp) + '-'.join(part.replace(' ', '_') for part in key)


class PartFile:
    """The pairs of one add-in version and code in folder; io has export(bodies, path) and load(path) → bodies"""

    def __init__(self, folder: str, version: str, stamp: str, io, log=print):
        self.folder = folder
        self.version = version
        self.stamp = stamp
        self.io = io
        self.log = log

    def _paths(self, key: tuple) -> tuple[str, str]:
        stem = os.path.join(self.folder, fileStem(self.version, self.stamp, key))
        return (stem + '.smt', stem + '.json')

    def load(self, key: tuple) -> list | None:
        """[(name, body)] as saved, None when the pair is missing or broken in any way (the part is then drawn)"""
        (smt, names) = self._paths(key)
        if not (os.path.isfile(smt) and os.path.isfile(names)):
            return None
        try:
            with open(names, encoding='utf-8') as file:
                bodyNames = json.load(file)
            if not (isinstance(bodyNames, list) and bodyNames and all(isinstance(name, str) for name in bodyNames)):
                raise ValueError('no list of body names')
            bodies = list(self.io.load(smt))
            if len(bodies) != len(bodyNames):
                raise ValueError(f'{len(bodies)} bodies for {len(bodyNames)} names')
        except Exception as err:
            self.log(f'part file {os.path.basename(smt)} not read, drawn anew: {err}')
            return None
        return list(zip(bodyNames, bodies))

    def save(self, key: tuple, kept: list):
        """
        Writes the pair, each to a .tmp.<suffix> renamed into place (Fusion picks the export format by the suffix), the
        .smt first and the names last: a pair without its names is not read. Raises when writing fails (the caller
        logs it); cleans up older keys afterwards
        """
        os.makedirs(self.folder, exist_ok=True)
        (smt, names) = self._paths(key)
        # the names go first: a half-written pair must not survive as the old names beside a new .smt
        self._remove(names)
        smtTemporary = _temporary(smt)
        self.io.export([body for (_, body) in kept], smtTemporary)
        os.replace(smtTemporary, smt)
        namesTemporary = _temporary(names)
        with open(namesTemporary, 'w', encoding='utf-8') as file:
            json.dump([name for (name, _) in kept], file)
        os.replace(namesTemporary, names)
        self.cleanUp()

    def cleanUp(self):
        """
        Deletes the store's own files (OWN_SUFFIXES) of other versions or code and left-over temporaries, only files
        right in folder, nothing below or beside it; failures only logged
        """
        prefix = keyPrefix(self.version, self.stamp)
        try:
            names = os.listdir(self.folder)
        except OSError as err:
            self.log(f'part files not cleaned up: {err}')
            return
        for name in names:
            path = os.path.join(self.folder, name)
            # the current key's files stay, its temporaries too: another Fusion on the same add-in folder may be
            # writing them (review round 49); a left-over one is overwritten by the next write of its key
            if name.endswith(OWN_SUFFIXES) and not name.startswith(prefix) and os.path.isfile(path):
                self._remove(path)

    def discard(self, key: tuple):
        """Deletes the key's pair, the names first: its bodies could not be used, the part is drawn and written anew"""
        (smt, names) = self._paths(key)
        self._remove(names)
        self._remove(smt)

    def _remove(self, path: str):
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError as err:
            self.log(f'part file {os.path.basename(path)} not deleted: {err}')


def _temporary(path: str) -> str:
    """x.smt → x.tmp.smt"""
    (stem, suffix) = os.path.splitext(path)
    return f'{stem}.tmp{suffix}'


class FusionIo:
    """TemporaryBRepManager's .smt export and import"""

    def export(self, bodies: list, path: str):
        import adsk.fusion
        if not adsk.fusion.TemporaryBRepManager.get().exportToFile(bodies, path):
            raise RuntimeError('exportToFile returned False')

    def load(self, path: str) -> list:
        import adsk.fusion
        return list(adsk.fusion.TemporaryBRepManager.get().createFromFile(path))


def sessionKey() -> tuple[str, str]:
    """
    (manifest version, code stamp) of the add-in as it is on disk now. predPartCache takes it when it is loaded, so the
    key belongs to the code that draws (review round 49: code checked out while Fusion runs must not be keyed with the
    code that is loaded). The manifest is read here, not by updateCheck, to keep this module free of the lib package
    """
    folder = addinFolder()
    with open(os.path.join(folder, 'Gridkeeper.manifest'), encoding='utf-8') as file:
        version = json.load(file).get('version')
    if not (isinstance(version, str) and re.fullmatch(r'\d+(\.\d+)*', version)):
        raise ValueError(f'no manifest version: {version!r}')
    return (version, codeStamp(os.path.dirname(os.path.abspath(__file__))))


def sessionStore(key: tuple[str, str], log=None) -> PartFile:
    """The store of the running add-in for its key of sessionKey: partCache in its folder"""
    if log is None:
        from . import commonUtils
        log = commonUtils.fileLog
    (version, stamp) = key
    return PartFile(os.path.join(addinFolder(), FOLDER_NAME), version, stamp, FusionIo(), log)
