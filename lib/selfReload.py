import os
from dataclasses import dataclass

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
    if not first or not second:
        return False
    return os.path.normcase(os.path.normpath(first)) == os.path.normcase(os.path.normpath(second))

def ownScript(scripts, addinFolder: str):
    """The Script of the add-in in addinFolder, by its folder only: a clone and a worktree are both named Gridkeeper.
    None unless exactly one"""
    found = [script for script in scripts if sameFolder(script.folder, addinFolder)]
    return found[0] if len(found) == 1 else None

def nextStep(activeCommand: str | None, commandPrefix: str, tries: int, maxTries: int) -> str:
    """'reload' once no Gridkeeper command is open, stopping the add-in would delete it under the user's hands;
    'wait' while one is and tries are left, 'giveUp' after"""
    if activeCommand and activeCommand.startswith(commandPrefix):
        return 'wait' if tries < maxTries else 'giveUp'
    return 'reload'

def reloadScript(script) -> ReloadFailed | None:
    """Stops and runs script, None when both worked. Called from the add-in's own event handler: stop() unloads the
    add-in, this code still runs to the end (measured), run() loads the code on disk again"""
    try:
        if not script.stop():
            return ReloadFailed('Fusion didn\'t stop it', True)
    except Exception as err:
        return ReloadFailed(f'Fusion didn\'t stop it: {err}', True)
    try:
        if not script.run():
            return ReloadFailed('Fusion stopped it but didn\'t start it again', False)
    except Exception as err:
        return ReloadFailed(f'Fusion stopped it but didn\'t start it again: {err}', False)
    return None
