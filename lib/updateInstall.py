import datetime
import hashlib
import json
import os
import shutil
import threading
import zipfile

# Installing an update (p310): the release ZIP is downloaded, checked and unpacked before anything of the add-in folder
# is touched, then the folder is swapped with a way back on every failure. A git checkout is never replaced. Kept free
# of Fusion imports so it can be unit tested, the dialogs are in commands/commandUpdates

# the folder of the ZIP release.yml builds, Fusion loads the add-in only from a folder named like its manifest
ADDIN_FOLDER_NAME = 'Gridkeeper'
MAX_DOWNLOAD = 50 * 2**20
MAX_UNPACKED = 200 * 2**20
DOWNLOAD_TIMEOUT = 60
# the same neutral user agent as the update check, see updateCheck.USER_AGENT
USER_AGENT = 'Gridkeeper-update-check'

class UpdateError(Exception):
    """An update that didn't happen, its text is the reason shown to the user"""

def isGitCheckout(folder: str) -> bool:
    """A git checkout is never replaced by an update. .git is a folder in a clone and a file in a git worktree"""
    return os.path.exists(os.path.join(folder, '.git'))

def download(url: str, target: str, urlopen=None, limit: int = MAX_DOWNLOAD, progress=None) -> None:
    """Saves url to target, stops at limit bytes. progress is called with the bytes so far after each chunk"""
    import urllib.request
    urlopen = urlopen or urllib.request.urlopen
    try:
        # inside, a url the request refuses is a failed download too
        request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response, open(target, 'wb') as file:
            size = 0
            while chunk := response.read(64 * 1024):
                size += len(chunk)
                if size > limit:
                    raise UpdateError(f'The download is too large, more than {limit // 2**20} MB.')
                file.write(chunk)
                if progress is not None:
                    progress(size)
    except UpdateError:
        raise
    except Exception as err:
        raise UpdateError(f'The download failed: {err}') from err

def _entryParts(name: str) -> list[str] | None:
    """The path parts of a ZIP entry, none when it could land outside the folder it's unpacked to"""
    if name.startswith(('/', '\\')):
        return None
    parts = [part for part in name.replace('\\', '/').split('/') if part != '']
    if any(part in ('.', '..') or ':' in part for part in parts):
        return None
    return parts

def verifyZip(zipPath: str, version: tuple[int, int, int], digest: str | None, size: int | None,
              maxUnpacked: int = MAX_UNPACKED) -> None:
    """Raises UpdateError unless zipPath is the release ZIP of version: GitHub's sha256 checksum (or, without one, the
    size) matches, every entry is inside one folder Gridkeeper, its manifest has the version and Gridkeeper.py is there"""
    versionText = '.'.join(str(part) for part in version)
    if isinstance(digest, str) and digest.startswith('sha256:'):
        with open(zipPath, 'rb') as file:
            actual = hashlib.sha256(file.read()).hexdigest()
        if actual != digest[len('sha256:'):].lower():
            raise UpdateError('The checksum of the download is wrong.')
    elif size is None or os.path.getsize(zipPath) != size:
        raise UpdateError('The size of the download is wrong, and GitHub gave no checksum to check it.')
    try:
        with zipfile.ZipFile(zipPath) as archive:
            entries = archive.infolist()
            unpacked = 0
            for entry in entries:
                parts = _entryParts(entry.filename)
                if parts is None or len(parts) == 0 or parts[0] != ADDIN_FOLDER_NAME or (len(parts) == 1 and not entry.is_dir()):
                    raise UpdateError(f'The download holds a file outside the folder {ADDIN_FOLDER_NAME}: {entry.filename}')
                unpacked += entry.file_size
            if unpacked > maxUnpacked:
                raise UpdateError(f'The download is too large unpacked, more than {maxUnpacked // 2**20} MB.')
            names = {'/'.join(_entryParts(entry.filename)) for entry in entries}
            if f'{ADDIN_FOLDER_NAME}/Gridkeeper.py' not in names:
                raise UpdateError('The download has no Gridkeeper.py.')
            try:
                manifest = json.loads(archive.read(f'{ADDIN_FOLDER_NAME}/Gridkeeper.manifest').decode('utf-8'))
            except KeyError:
                raise UpdateError('The download has no Gridkeeper.manifest.')
    except zipfile.BadZipFile as err:
        raise UpdateError(f'The download is no ZIP file: {err}') from err
    except ValueError as err:
        raise UpdateError(f'The manifest of the download can\'t be read: {err}') from err
    found = manifest.get('version') if isinstance(manifest, dict) else None
    if found != versionText:
        raise UpdateError(f'The download is version {found}, not {versionText}.')

def extract(zipPath: str, targetParent: str) -> str:
    """Unpacks a ZIP verifyZip passed into targetParent, the path of the add-in folder in it"""
    with zipfile.ZipFile(zipPath) as archive:
        archive.extractall(targetParent)
    return os.path.join(targetParent, ADDIN_FOLDER_NAME)

# swapping the add-in folder

# next to the add-in folder, so renaming stays on one drive. Fusion loads add-ins only from folders named like their
# manifest, the copies in here (new/Gridkeeper, backup-<time>/Gridkeeper) are one level too deep to be picked up
WORK_FOLDER_NAME = '.gridkeeper-update'
# never carried over from the old version: its code, the caches of that code (partCache: the box's small parts as its
# code drew them, round 49) and the manifest
CARRY_OVER_SKIPPED_FOLDERS = ('__pycache__', '.git', 'partCache')
CARRY_OVER_SKIPPED_SUFFIXES = ('.py', '.pyc', '.manifest')

# one install at a time, and no cleanup meanwhile: the cleanup thread at startup and a click on Update now must not
# work in .gridkeeper-update together (review finding 4)
WORK_LOCK = threading.Lock()

def workFolder(addinFolder: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(addinFolder)), WORK_FOLDER_NAME)

def _files(folder: str) -> set[str]:
    """Relative paths, with /, of every file below folder"""
    files = set()
    for (root, _, names) in os.walk(folder):
        for name in names:
            files.add(os.path.relpath(os.path.join(root, name), folder).replace(os.sep, '/'))
    return files

def carryOver(oldFolder: str, newFolder: str) -> list[str]:
    """
    Copies every file of the old add-in folder the new version doesn't have into it, the relative paths copied. That's
    the user's: the saved dialog defaults (commands/*/commandConfig), the update settings (updateConfig) and symbols
    added to the symbol folders, without a list that would miss the next such folder. Code, its caches and the manifest
    are left behind. A side effect: a picture or symbol a new version left out on purpose comes back from the old one
    """
    carried = []
    # Windows doesn't tell Symbols/Nut.svg from symbols/nut.svg, the new version's file must win there too
    newFiles = {name.lower() for name in _files(newFolder)}
    for (root, folders, names) in os.walk(oldFolder):
        folders[:] = [folder for folder in folders if folder not in CARRY_OVER_SKIPPED_FOLDERS]
        for name in names:
            relative = os.path.relpath(os.path.join(root, name), oldFolder).replace(os.sep, '/')
            if name.lower().endswith(CARRY_OVER_SKIPPED_SUFFIXES) or relative.lower() in newFiles:
                continue
            target = os.path.join(newFolder, *relative.split('/'))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(os.path.join(root, name), target)
            carried.append(relative)
    return carried

def _sameFiles(folder: str, other: str) -> bool:
    """Both hold the same files with the same content"""
    import filecmp
    files = _files(folder)
    if files != _files(other):
        return False
    return all(filecmp.cmp(os.path.join(folder, *name.split('/')), os.path.join(other, *name.split('/')), shallow=False)
               for name in files)

def _prune(folder: str, keep: set[str]) -> None:
    """Deletes the files below folder that aren't in keep, and folders left empty, as far as it can. Compared without
    case, as the file systems of Windows and macOS (both supported, see the manifest) do: copying over lib/Symbols
    writes lib/symbols/x.svg into the old spelling, that file is kept (second review,
    test_copy_path_keeps_new_files_whose_folder_differs_in_case). The same as carryOver"""
    keep = {name.lower() for name in keep}
    for (root, folders, names) in os.walk(folder, topdown=False):
        for name in names:
            path = os.path.join(root, name)
            if os.path.relpath(path, folder).replace(os.sep, '/').lower() not in keep:
                try:
                    os.remove(path)
                except OSError:
                    pass
        if root != folder:
            try:
                os.rmdir(root)
            except OSError:
                pass

def swap(addinFolder: str, newFolder: str, backupFolder: str, rename=os.replace, copyFile=shutil.copy2) -> str:
    """
    Puts newFolder in the place of addinFolder, the old one moves to backupFolder. 'renamed' when two renames did it,
    'copied' when the add-in folder couldn't be moved (Windows refuses while a file in it is open) and the new version
    was copied over it after a full backup copy. Raises UpdateError after putting the old version back
    """
    try:
        rename(addinFolder, backupFolder)
    except OSError:
        return _swapByCopy(addinFolder, newFolder, backupFolder, copyFile)
    try:
        rename(newFolder, addinFolder)
    except OSError as err:
        try:
            rename(backupFolder, addinFolder)
        except OSError:
            raise UpdateError(f"The new version couldn't be put in place ({err}) and the old one not back. "
                              f"It's in {backupFolder}, move it back to {addinFolder}.") from err
        raise UpdateError(f"The new version couldn't be put in place: {err}. Nothing changed.") from err
    return 'renamed'

def _swapByCopy(addinFolder: str, newFolder: str, backupFolder: str, copyFile) -> str:
    try:
        shutil.copytree(addinFolder, backupFolder, copy_function=copyFile)
    except OSError as err:
        shutil.rmtree(backupFolder, ignore_errors=True)
        raise UpdateError(f"The old version couldn't be backed up: {err}. Nothing changed.") from err
    try:
        shutil.copytree(newFolder, addinFolder, dirs_exist_ok=True, copy_function=copyFile)
    except OSError as err:
        # The way back: the backup over the add-in folder, the files of the new version it doesn't have removed.
        # Whether it's back is decided by comparing with the backup, not by errors of the copy: a file Windows holds
        # open can't be written either way, it failed the forward copy too and still has the old content (review
        # finding 2, test_copy_fails_both_ways_on_a_locked_file)
        try:
            shutil.copytree(backupFolder, addinFolder, dirs_exist_ok=True, copy_function=copyFile)
        except OSError:
            pass
        _prune(addinFolder, _files(backupFolder))
        if not _sameFiles(addinFolder, backupFolder):
            raise UpdateError(f"The new version couldn't be copied ({err}) and the old one not back. "
                              f"It's in {backupFolder}, copy it back to {addinFolder} with Fusion closed.") from err
        raise UpdateError(f"The new version couldn't be copied: {err}. The old version is back.") from err
    # as after a rename, files of the old version the new one doesn't have go, the user's are in it, see carryOver
    _prune(addinFolder, _files(newFolder))
    return 'copied'

def install(release, addinFolder: str, urlopen=None, now=datetime.datetime.now, progress=None, rename=os.replace,
            lockTimeout: float = 30) -> str:
    """
    Downloads, checks and unpacks the release ZIP, then swaps the add-in folder, see swap; 'renamed' or 'copied'.
    release has version, assetUrl, assetSize and assetDigest, see updateCheck.Release. Raises UpdateError with the
    reason, the add-in folder is unchanged or back then. A git checkout is refused before anything is downloaded.
    One at a time, and not while cleanupBackups runs, see WORK_LOCK
    """
    if isGitCheckout(addinFolder):
        raise UpdateError('This add-in runs from a git checkout, update it with git.')
    if not release.assetUrl:
        raise UpdateError('The release has no ZIP file to install.')
    # mostly the cleanup at startup holding it, a few seconds at most
    if not WORK_LOCK.acquire(timeout=lockTimeout):
        raise UpdateError('Gridkeeper is still tidying up after the last update or installing one, try again in a moment.')
    try:
        return _install(release, addinFolder, urlopen, now, progress, rename)
    finally:
        WORK_LOCK.release()

def _install(release, addinFolder: str, urlopen, now, progress, rename) -> str:
    versionText = '.'.join(str(part) for part in release.version)
    work = workFolder(addinFolder)
    newParent = os.path.join(work, 'new')
    zipPath = os.path.join(work, f'Gridkeeper-v{versionText}.zip')
    backupParent = None
    try:
        os.makedirs(work, exist_ok=True)
        # a run that broke off may have left its unpacked files
        shutil.rmtree(newParent, ignore_errors=True)
        download(release.assetUrl, zipPath, urlopen=urlopen, progress=progress)
        verifyZip(zipPath, release.version, release.assetDigest, release.assetSize)
        newFolder = extract(zipPath, newParent)
        carryOver(addinFolder, newFolder)
        stamp = now().strftime('%Y%m%d-%H%M%S')
        backupParent = os.path.join(work, f'backup-{stamp}')
        count = 1
        while os.path.exists(backupParent):
            count += 1
            backupParent = os.path.join(work, f'backup-{stamp}-{count}')
        os.makedirs(backupParent)
        return swap(addinFolder, newFolder, os.path.join(backupParent, ADDIN_FOLDER_NAME), rename=rename)
    except Exception as err:
        # swap raises UpdateError only, any other error came before it and left the add-in folder alone
        if backupParent is not None and os.path.isdir(backupParent) and not os.listdir(backupParent):
            os.rmdir(backupParent)
        if isinstance(err, UpdateError):
            raise
        raise UpdateError(f"The update couldn't be prepared: {err}. Nothing changed.") from err
    finally:
        shutil.rmtree(newParent, ignore_errors=True)
        try:
            os.remove(zipPath)
        except OSError:
            pass

def _backupKey(name: str) -> tuple:
    """backup-<YYYYmmdd-HHMMSS>[-<n>] in the order they were made, -10 after -2"""
    parts = name.split('-')
    return (parts[1:3], int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 1)

def cleanupBackups(addinFolder: str) -> None:
    """
    Removes the backups of earlier updates but the newest, as far as it can. Only backups: new/ and the ZIP belong to
    an update that may be running, install clears them itself (review finding 4). Waits for a running install
    """
    work = workFolder(addinFolder)
    with WORK_LOCK:
        if not os.path.isdir(work):
            return
        backups = sorted((name for name in os.listdir(work) if name.startswith('backup-')), key=_backupKey)
        for name in backups[:-1]:
            shutil.rmtree(os.path.join(work, name), ignore_errors=True)
