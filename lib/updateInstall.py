import hashlib
import json
import os
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

def download(url: str, target: str, urlopen=None, limit: int = MAX_DOWNLOAD) -> None:
    """Saves url to target, stops at limit bytes"""
    import urllib.request
    urlopen = urlopen or urllib.request.urlopen
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response, open(target, 'wb') as file:
            size = 0
            while chunk := response.read(64 * 1024):
                size += len(chunk)
                if size > limit:
                    raise UpdateError(f'The download is too large, more than {limit // 2**20} MB.')
                file.write(chunk)
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
