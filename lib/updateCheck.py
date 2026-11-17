import dataclasses
import datetime
import json
import os
import re

# The update check (p310): once a day at startup Gridkeeper asks GitHub for its newest release and offers it when it's
# newer than the running add-in. Kept free of Fusion imports so it can be unit tested, the dialogs are in
# commands/commandUpdates, replacing the add-in folder is in lib/updateInstall.py

# only Gridkeeper's own tags count, GridfinityGenerator's vX.Y.Z.W tags and anything else never do
TAG_PATTERN = re.compile(r'^gridkeeper-v(\d+)\.(\d+)\.(\d+)$')
VERSION_PATTERN = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')
# the longest short info shown in the update dialog, the release page has the rest
SUMMARY_LIMIT = 300

@dataclasses.dataclass(frozen=True)
class Release:
    version: tuple[int, int, int]
    tag: str
    # the release page with the release notes
    pageUrl: str
    summary: str
    # the ZIP release.yml builds, none when the release has no such asset: it's shown but can't be installed
    assetUrl: str | None
    assetSize: int | None
    # 'sha256:<hex>' as GitHub reports it for the asset
    assetDigest: str | None

    @property
    def versionText(self) -> str:
        return versionText(self.version)

def versionText(version: tuple[int, int, int]) -> str:
    return '.'.join(str(part) for part in version)

def parseVersion(text: str | None) -> tuple[int, int, int] | None:
    """X.Y.Z as numbers, none for anything else"""
    match = VERSION_PATTERN.match(text) if isinstance(text, str) else None
    return tuple(int(part) for part in match.groups()) if match else None

def tagVersion(tag: str | None) -> tuple[int, int, int] | None:
    """The version of a gridkeeper-vX.Y.Z tag, none for every other tag"""
    match = TAG_PATTERN.match(tag) if isinstance(tag, str) else None
    return tuple(int(part) for part in match.groups()) if match else None

def assetName(version: tuple[int, int, int]) -> str:
    """The ZIP release.yml uploads, gridkeeper-v1.0.0 -> Gridkeeper-v1.0.0.zip"""
    return f'Gridkeeper-v{versionText(version)}.zip'

def newestRelease(releases: list, current: tuple[int, int, int]) -> Release | None:
    """The newest published Gridkeeper release of the GitHub API's release list, none unless it's newer than current"""
    newest = None
    for entry in releases if isinstance(releases, list) else []:
        if not isinstance(entry, dict) or entry.get('draft') or entry.get('prerelease'):
            continue
        version = tagVersion(entry.get('tag_name'))
        if version is None or version <= current or (newest is not None and version <= newest[0]):
            continue
        newest = (version, entry)
    if newest is None:
        return None
    (version, entry) = newest
    assets = entry.get('assets') if isinstance(entry.get('assets'), list) else []
    asset = next((asset for asset in assets if isinstance(asset, dict) and asset.get('name') == assetName(version)), None)
    def assetField(name: str, fieldType: type):
        value = asset.get(name) if asset is not None else None
        return value if isinstance(value, fieldType) else None
    return Release(
        version=version,
        tag=entry['tag_name'],
        pageUrl=gitHubUrl(entry.get('html_url')) or '',
        summary=summary(entry.get('body')),
        assetUrl=gitHubUrl(assetField('browser_download_url', str)),
        assetSize=assetField('size', int),
        assetDigest=assetField('digest', str),
    )

# the link in the dialog and the download only ever go to GitHub (review: no other scheme or host from the answer)
GITHUB_PREFIX = 'https://github.com/'

def gitHubUrl(url) -> str | None:
    return url if isinstance(url, str) and url.startswith(GITHUB_PREFIX) else None

def summary(body: str | None, limit: int = SUMMARY_LIMIT) -> str:
    """The first paragraph of the release notes as plain text, headings skipped, cut to limit characters"""
    if not isinstance(body, str):
        return ''
    paragraphs = re.split(r'\n\s*\n', body.replace('\r\n', '\n').replace('\r', '\n'))
    # heading lines go, not the paragraph they head: "## What's new" right above a list is common
    paragraphs = ['\n'.join(line for line in text.split('\n') if not line.strip().startswith('#')).strip() for text in paragraphs]
    paragraph = next((text for text in paragraphs if text), '')
    # markdown links become their text, emphasis and code marks go
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', paragraph)
    text = re.sub(r'(\*\*|__|`)', '', text)
    text = ' '.join(text.split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + '…'

def manifestVersion(addinFolder: str) -> tuple[int, int, int] | None:
    """The version in Gridkeeper.manifest of the add-in folder, none when it can't be read"""
    try:
        with open(os.path.join(addinFolder, 'Gridkeeper.manifest'), encoding='utf-8') as file:
            return parseVersion(json.load(file).get('version'))
    except (OSError, ValueError, AttributeError):
        return None

# what the dialogs say, see commands/commandUpdates

GIT_CHECKOUT_TEXT = 'This add-in runs from a git checkout, update it with git.'
# How the new version gets loaded, measured in Fusion 2706 (spec E13, 17.11.2026): a restart of Fusion, Stop and Run
# in Scripts and Add-Ins, or Script.stop/run of the API from a script all load it with every command working.
# Reloading the add-in's modules in place leaves every command dead, without an error, so it's not offered; the
# add-in restarting itself through the API wasn't measured and would unload the code that has to run it again
RELOAD_WAYS = 'restart Fusion, or stop and run Gridkeeper in Utilities › Add-Ins › Scripts and Add-Ins'
# spec E11.7; until then the old code runs with the new files on disk, so it says so (review finding 5)
SUCCESS_RESTART_TEXT = f'To load it, {RELOAD_WAYS}. Until then the old version runs.'

def dialogHtml(release: Release, current: tuple[int, int, int], gitCheckout: bool) -> str:
    """The text of the update dialog: the new version, its short info and the link to its release notes"""
    import html
    lines = [f'<b>Gridkeeper {release.versionText} is available (you have {versionText(current)}).</b>']
    if release.summary:
        lines.append(html.escape(release.summary))
    if release.pageUrl:
        lines.append(f'<a href="{html.escape(release.pageUrl, quote=True)}">Release notes</a>')
    if gitCheckout:
        lines.append(GIT_CHECKOUT_TEXT)
    elif release.assetUrl is None:
        lines.append('The release has no ZIP file to install, download it from the release page.')
    return '<br><br>'.join(lines)

def versionLine(running: tuple[int, int, int] | None, installed: tuple[int, int, int] | None) -> str:
    """The version running, read when the add-in started, and the one on disk an update put there"""
    if running is None:
        return 'Running Gridkeeper, its version is unknown.'
    if installed is None or installed == running:
        return f'Running Gridkeeper {versionText(running)}.'
    return (f'Running Gridkeeper {versionText(running)}, installed {versionText(installed)}. '
            f'{RELOAD_WAYS[0].upper()}{RELOAD_WAYS[1:]}, to use {versionText(installed)}.')

def successText(release: Release) -> str:
    return f'Gridkeeper {release.versionText} is installed. {SUCCESS_RESTART_TEXT}'

# settings

SETTINGS_FOLDER = 'updateConfig'
SETTINGS_FILE = 'update.json'

def settingsPath(addinFolder: str) -> str:
    """Kept in the add-in folder like the dialog defaults, an update carries it over, see updateInstall.carryOver"""
    return os.path.join(addinFolder, SETTINGS_FOLDER, SETTINGS_FILE)

def readSettings(path: str) -> dict:
    """The update settings, checking at startup unless a readable file turns it off"""
    settings = {'checkAtStartup': True}
    try:
        with open(path, encoding='utf-8') as file:
            data = json.load(file)
    except (OSError, ValueError):
        return settings
    if isinstance(data, dict):
        if isinstance(data.get('checkAtStartup'), bool):
            settings['checkAtStartup'] = data['checkAtStartup']
        if isinstance(data.get('lastCheck'), str):
            settings['lastCheck'] = data['lastCheck']
    return settings

def writeSettings(path: str, settings: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(settings, file, indent=1)
        return True
    except OSError:
        return False

def isDue(settings: dict, today: datetime.date) -> bool:
    """At most one check a calendar day, a failed one counts too so a computer without network doesn't wait each start"""
    return settings.get('checkAtStartup', True) is not False and settings.get('lastCheck') != today.isoformat()

# asking GitHub

API_URL = 'https://api.github.com/repos/Eifel-Joe/Gridkeeper/releases?per_page=30'
# GitHub wants a user agent, this one says nothing about the user, the computer or the version (p310: no personal data)
USER_AGENT = 'Gridkeeper-update-check'
TIMEOUT = 10
MAX_ANSWER = 5 * 2**20

def fetchReleases(url: str = API_URL, urlopen=None, log=print) -> list | None:
    """The release list of the GitHub API, none when it can't be had: no network, a timeout, an HTTP error or no list.
    Errors are only logged, the check is silent at startup"""
    import urllib.request
    urlopen = urlopen or urllib.request.urlopen
    try:
        request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/vnd.github+json'})
        with urlopen(request, timeout=TIMEOUT) as response:
            # a release list is a few hundred kB, more is no answer of GitHub's
            raw = response.read(MAX_ANSWER + 1)
            if len(raw) > MAX_ANSWER:
                raise ValueError(f'answer larger than {MAX_ANSWER // 2**20} MB')
            data = json.loads(raw.decode('utf-8'))
    except Exception as err:
        log(f'Gridkeeper update check failed: {type(err).__name__}: {err}')
        return None
    if not isinstance(data, list):
        log('Gridkeeper update check failed: GitHub sent no release list')
        return None
    return data

def checkForUpdate(addinFolder: str, fetch=None, log=print) -> Release | None:
    """The release newer than the add-in in addinFolder, none when there is none or GitHub can't be asked"""
    current = manifestVersion(addinFolder)
    if current is None:
        log(f'Gridkeeper update check skipped: no X.Y.Z version in the manifest of {addinFolder}')
        return None
    releases = fetch() if fetch is not None else fetchReleases(log=log)
    return newestRelease(releases, current) if releases is not None else None
