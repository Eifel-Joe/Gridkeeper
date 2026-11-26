import ntpath
from dataclasses import dataclass

from . import updateCheck
from .i18n import tr

# Reload Gridkeeper (p321, dev-notes/specs/2026-11-18-runde-33-design.md): the add-in stops and runs itself through
# Fusion's API, app.scripts and its own Script. Measured 18.11.2026 in Fusion 2706 (update spec, "Messung
# Selbst-Neustart"): from a custom event handler of the add-in, stop() and run() both work, the new version then runs
# with every command alive. Reloading its modules in place instead (W4) leaves the commands dead, so it's not used.
# Fusion-free, the Script objects are duck typed (folder, stop, run), the event and dialogs are in commands/commandUpdates

@dataclass
class ReloadFailed:
    """Why the reload didn't happen. stillRunning: the old version runs on, else Gridkeeper is stopped now"""
    reason: str
    stillRunning: bool

def reloadOffered(running: tuple[int, int, int] | None, installed: tuple[int, int, int] | None) -> bool:
    """The code running isn't the version on disk: after an update, a git pull or a branch switch (spec R1, R4)"""
    return running is not None and installed is not None and running != installed

def sameFolder(first: str | None, second: str | None) -> bool:
    """Fusion's folder of a Script against the add-in's own, ntpath's rules on every OS (CI 18.11.2026: os.path on the
    Linux runner kept case and backslashes, the Windows spelling didn't match). On Windows Fusion gives / while __file__
    has \\ and the case may differ; on macOS both are the same / paths and stay equal to themselves under ntpath, its
    file system ignores case by default too. tests/test_self_reload.py"""
    if not first or not second:
        return False
    return ntpath.normcase(ntpath.normpath(first)) == ntpath.normcase(ntpath.normpath(second))

def ownScript(scripts, addinFolder: str):
    """The Script of the add-in in addinFolder, by its folder only: a clone and a worktree are both named Gridkeeper.
    None unless exactly one"""
    found = [script for script in scripts if sameFolder(script.folder, addinFolder)]
    return found[0] if len(found) == 1 else None

def okAction(openedByCheck: bool, canInstall: bool, running: tuple[int, int, int] | None,
             installed: tuple[int, int, int] | None) -> str | None:
    """What OK of the Gridkeeper updates dialog does: 'update' in the one the check opened with a release to install
    (OK is Update now, never a reload), 'reload' while the version on disk isn't the running one (spec R1), else None,
    the dialog as before (main session 18.11.2026). Cancel never reloads"""
    if openedByCheck and canInstall:
        return 'update'
    return 'reload' if reloadOffered(running, installed) else None

def nextStep(activeCommand: str | None, commandPrefix: str, tries: int, maxTries: int,
             patientFor: str | None = None) -> str:
    """'reload' once no Gridkeeper command is open, stopping the add-in would delete it under the user's hands;
    'wait' while one is and tries are left, 'giveUp' after. 'waitPatiently', without a limit, while patientFor is
    open: the updates dialog says "Close this dialog to reload" (review finding 1)"""
    if patientFor and activeCommand == patientFor:
        return 'waitPatiently'
    if activeCommand and activeCommand.startswith(commandPrefix):
        return 'wait' if tries < maxTries else 'giveUp'
    return 'reload'

def reloadScript(script) -> ReloadFailed | None:
    """Stops and runs script, None when both worked. Called from the add-in's own event handler: stop() unloads the
    add-in, this code still runs to the end (measured), run() loads the code on disk again. A start that fails inside
    the new version isn't seen here: Gridkeeper.py's run catches it and logs it, run() still answers True, as with any
    failed start (review finding 5)"""
    try:
        if not script.stop():
            return ReloadFailed(tr('Fusion didn\'t stop it'), True)
    except Exception as err:
        return ReloadFailed(tr('Fusion didn\'t stop it: {err}', err=err), True)
    try:
        if not script.run():
            return ReloadFailed(tr('Fusion stopped it but didn\'t start it again'), False)
    except Exception as err:
        return ReloadFailed(tr('Fusion stopped it but didn\'t start it again: {err}', err=err), False)
    return None

# what the messages say, each ends with the ways by hand

NOT_FOUND_TEXT = tr("Gridkeeper couldn't reload itself, Fusion doesn't list it under its folder. To load the new version, {ways}.",
                    ways=updateCheck.RELOAD_WAYS)
GAVE_UP_TEXT = tr("Gridkeeper didn't reload, one of its dialogs stayed open. Close it and click Reload Gridkeeper in Gridkeeper updates, or {ways}.",
                  ways=updateCheck.RELOAD_WAYS)

def failedText(failed: ReloadFailed) -> str:
    if failed.stillRunning:
        return tr("Gridkeeper couldn't reload itself, {reason}. The old version runs on. To load the new one, {ways}.",
                  reason=failed.reason, ways=updateCheck.RELOAD_WAYS)
    return tr("Gridkeeper couldn't reload itself, {reason}. Gridkeeper is stopped now. To start it, restart Fusion, or run Gridkeeper in Utilities › Add-Ins › Scripts and Add-Ins.",
              reason=failed.reason)
