import datetime
import os
import threading
import traceback
import webbrowser

import adsk.core

from ...lib import fusion360utils as futil
from ...lib import updateCheck
from ...lib import updateInstall
from ...lib import selfReload
from ...lib.i18n import tr
from ...lib.ui import dialogSize
from ... import config

# The update check (p310, dev-notes/specs/2026-11-17-update-hinweis-design.md): once a day at startup a background
# thread asks GitHub for a newer Gridkeeper, a custom event brings the answer to Fusion's main thread, which shows it
# in this command's dialog. The same dialog, opened from Utilities > Add-ins, shows the version and turns the check
# off. What's Fusion-free is in lib/updateCheck.py and lib/updateInstall.py

app = adsk.core.Application.get()
ui = app.userInterface


def showFailure(englishName: str, shownName: str, err: Exception):
    """The log in English, the message box in the add-in's language (review round 60, as the export's)"""
    futil.handle_error(f'{englishName} failed, {err}')
    ui.messageBox(tr('{command} failed, {error}', command=shownName, error=err) + '\n' + traceback.format_exc())

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdUpdates'
CMD_NAME = tr('Gridkeeper updates')
CMD_DESCRIPTION = tr('Shows the Gridkeeper version, checks for a new one and turns the check at startup on or off')
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')
# Utilities > Add-ins, out of the way of the generator commands, as the test commands
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'

ADDIN_FOLDER = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# the answer of the background check, see checkInBackground
RESULT_EVENT_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_updateCheckResult'
# the dialog waits for Fusion to be idle, tried again this often this many seconds apart, see result_custom_event
SHOW_RETRY_SECONDS = 30
SHOW_RETRIES = 10
# Reload Gridkeeper (p321, lib/selfReload.py): the add-in stops and runs itself from this custom event, never in a
# handler of its own command. It waits for Gridkeeper's dialogs to close, tried this often this many seconds apart
# (spec R2: at most 10 times); for the updates dialog itself without a limit, it says "Close this dialog to reload"
RELOAD_EVENT_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_reload'
RELOAD_RETRY_SECONDS = 3
RELOAD_RETRIES = 10
# the ids of every Gridkeeper command start with it
COMMAND_PREFIX = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_'

INFO_INPUT = 'updateInfo'
CHECK_AT_STARTUP_INPUT = 'checkAtStartup'
CHECK_NOW_INPUT = 'checkNow'
UPDATE_NOW_INPUT = 'updateNow'
RELEASE_NOTES_INPUT = 'releaseNotes'

local_handlers = []
event_handlers = []
# the version of the code running, read once at start: the manifest on disk may already be the next one
runningVersion: tuple[int, int, int] | None = None
# the newer release the last check found, none before one or when there is none
pendingRelease: updateCheck.Release | None = None
# log lines of the background thread, which mustn't call Fusion, written by the custom event
pendingLogs: list[str] = []
showRetries = 0
stopped = False
# the timer waiting for Fusion to be idle, cancelled at stop (review finding 3)
retryTimer: threading.Timer | None = None
# the dialog opened by the check at startup has Update now and Later as its buttons (spec E6), the one opened from
# the menu shows the version and the settings
openedByCheck = False
# an update is being installed, a second click or Check now waits (review finding 1)
installing = False
# what OK of the open dialog does: 'update' (opened by the check), 'reload' (from the menu, spec R1) or None
okAction: str | None = None
# Reload Gridkeeper waiting for a Gridkeeper dialog to close, see reload_custom_event
reloadTries = 0
reloadTimer: threading.Timer | None = None
# a reload was asked for and waits for Gridkeeper's dialogs to close; the updates dialog says so (second review N4, N5)
reloadWaiting = False

def start():
    global runningVersion, stopped, showRetries
    stopped = False
    showRetries = 0
    runningVersion = updateCheck.manifestVersion(ADDIN_FOLDER)
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_DESCRIPTION, ICON_FOLDER)
    futil.add_handler(cmd_def.commandCreated, command_created)
    try:
        panel = ui.workspaces.itemById(WORKSPACE_ID).toolbarPanels.itemById(PANEL_ID)
        if panel is not None and panel.controls.itemById(CMD_ID) is None:
            panel.controls.addCommand(cmd_def)
    except Exception as err:
        futil.log(f'Gridkeeper updates button not added, {err}')
    # left over when the add-in wasn't stopped
    app.unregisterCustomEvent(RESULT_EVENT_ID)
    futil.add_handler(app.registerCustomEvent(RESULT_EVENT_ID), result_custom_event, local_handlers=event_handlers)
    app.unregisterCustomEvent(RELOAD_EVENT_ID)
    futil.add_handler(app.registerCustomEvent(RELOAD_EVENT_ID), reload_custom_event, local_handlers=event_handlers)
    settings = updateCheck.readSettings(updateCheck.settingsPath(ADDIN_FOLDER))
    today = datetime.date.today()
    if updateCheck.isDue(settings, today):
        # a failed check counts too, a computer without network doesn't ask at every start
        updateCheck.writeSettings(updateCheck.settingsPath(ADDIN_FOLDER), {**settings, 'lastCheck': today.isoformat()})
        # daemon: Fusion never waits for it, neither at startup nor when it closes
        threading.Thread(target=checkInBackground, name='Gridkeeper update check', daemon=True).start()
    else:
        threading.Thread(target=cleanUpInBackground, name='Gridkeeper update cleanup', daemon=True).start()

def stop():
    global stopped, event_handlers, retryTimer, reloadTimer
    stopped = True
    if retryTimer is not None:
        retryTimer.cancel()
        retryTimer = None
    if reloadTimer is not None:
        reloadTimer.cancel()
        reloadTimer = None
    app.unregisterCustomEvent(RESULT_EVENT_ID)
    # also when the reload itself stops the add-in from this event's handler, measured harmless (p321)
    app.unregisterCustomEvent(RELOAD_EVENT_ID)
    event_handlers = []
    panel = ui.workspaces.itemById(WORKSPACE_ID).toolbarPanels.itemById(PANEL_ID)
    control = panel.controls.itemById(CMD_ID) if panel is not None else None
    if control:
        control.deleteMe()
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if cmd_def:
        cmd_def.deleteMe()

def cleanUpInBackground():
    """What an update left in .gridkeeper-update but the newest backup, see updateInstall.cleanupBackups"""
    try:
        updateInstall.cleanupBackups(ADDIN_FOLDER)
    except Exception as err:
        pendingLogs.append(f'Gridkeeper update cleanup failed: {err}')

def checkInBackground():
    """Runs in its own thread, Fusion's API is only called through the custom event"""
    global pendingRelease
    cleanUpInBackground()
    try:
        release = updateCheck.checkForUpdate(ADDIN_FOLDER, log=pendingLogs.append)
    except Exception as err:
        pendingLogs.append(f'Gridkeeper update check failed: {err}')
        release = None
    if release is not None:
        pendingRelease = release
    if not stopped:
        app.fireCustomEvent(RESULT_EVENT_ID, 'check')

def retryLater():
    if not stopped:
        app.fireCustomEvent(RESULT_EVENT_ID, 'retry')

def result_custom_event(args: adsk.core.CustomEventArgs):
    global showRetries, retryTimer, openedByCheck
    try:
        while pendingLogs:
            futil.log(pendingLogs.pop(0))
        if pendingRelease is None:
            return
        # not in the middle of another command, its dialog would be cancelled
        if ui.activeCommand != 'SelectCommand':
            if showRetries < SHOW_RETRIES:
                showRetries += 1
                retryTimer = threading.Timer(SHOW_RETRY_SECONDS, retryLater)
                # Fusion never waits for it when it closes
                retryTimer.daemon = True
                retryTimer.start()
            else:
                futil.log(f'Gridkeeper {pendingRelease.versionText} is available, Fusion was busy, asking tomorrow')
            return
        openedByCheck = True
        try:
            ui.commandDefinitions.itemById(CMD_ID).execute()
        except Exception:
            # no command_created follows, the next open from the menu is the menu's (second review). Not reset after
            # a good execute: whether Fusion creates the command during execute or after it isn't known
            openedByCheck = False
            raise
    except Exception:
        futil.handle_error('Gridkeeper update check')

# Reload Gridkeeper (p321)

def requestReload():
    """Reloads Gridkeeper once Fusion is idle and no Gridkeeper dialog is open, see reload_custom_event"""
    global reloadTries, reloadTimer, reloadWaiting
    reloadTries = 0
    reloadWaiting = True
    # one reload at a time: a second request (Yes after Update now, then OK) replaces a waiting one (review finding 3)
    if reloadTimer is not None:
        reloadTimer.cancel()
        reloadTimer = None
    # Fusion 2706 answered False when a script fired an add-in's event, the handler ran anyway (p321 measurement)
    app.fireCustomEvent(RELOAD_EVENT_ID, 'reload')

def retryReload():
    if not stopped:
        app.fireCustomEvent(RELOAD_EVENT_ID, 'retry')

def reload_custom_event(args: adsk.core.CustomEventArgs):
    global reloadTries, reloadTimer, reloadWaiting
    try:
        step = selfReload.nextStep(ui.activeCommand, COMMAND_PREFIX, reloadTries, RELOAD_RETRIES, patientFor=CMD_ID)
        if step in ('wait', 'waitPatiently'):
            if step == 'wait':
                reloadTries += 1
            # one timer at a time: a retry and a new request arriving together mustn't leave two (second review N3)
            if reloadTimer is not None:
                reloadTimer.cancel()
            reloadTimer = threading.Timer(RELOAD_RETRY_SECONDS, retryReload)
            # Fusion never waits for it when it closes
            reloadTimer.daemon = True
            reloadTimer.start()
            return
        reloadWaiting = False
        if step == 'giveUp':
            ui.messageBox(selfReload.GAVE_UP_TEXT, CMD_NAME)
            return
        scripts = app.scripts
        # by its folder only, a clone and a worktree are both named Gridkeeper (spec R2)
        script = selfReload.ownScript([scripts.item(index) for index in range(scripts.count)], ADDIN_FOLDER)
        if script is None:
            ui.messageBox(selfReload.NOT_FOUND_TEXT, CMD_NAME)
            return
        futil.log(f'Gridkeeper reloads itself, running {runningVersion}, on disk {updateCheck.manifestVersion(ADDIN_FOLDER)}')
        # stop() runs Gridkeeper's stop, this module's included; the code here still runs to its end (measured)
        failed = selfReload.reloadScript(script)
        if failed is not None:
            futil.log(f'Gridkeeper reload failed: {failed.reason}')
            ui.messageBox(selfReload.failedText(failed), CMD_NAME)
    except Exception as err:
        showFailure('Reload Gridkeeper', tr('Reload Gridkeeper'), err)

# the dialog

def infoHtml(reloadButton: bool = False, reloadPending: bool = False) -> str:
    installed = updateCheck.manifestVersion(ADDIN_FOLDER)
    lines = [updateCheck.versionLine(runningVersion, installed, reloadButton, reloadPending)]
    if pendingRelease is not None and (installed is None or pendingRelease.version > installed):
        lines.append(updateCheck.dialogHtml(pendingRelease, installed or runningVersion or (0, 0, 0), updateInstall.isGitCheckout(ADDIN_FOLDER)))
    return '<br><br>'.join(lines)

def canInstall() -> bool:
    installed = updateCheck.manifestVersion(ADDIN_FOLDER)
    return (pendingRelease is not None and pendingRelease.assetUrl is not None
            and (installed is None or pendingRelease.version > installed)
            and not updateInstall.isGitCheckout(ADDIN_FOLDER))

def command_created(args: adsk.core.CommandCreatedEventArgs):
    global openedByCheck, okAction
    command = args.command
    # opened by the check with a release to install: OK is Update now, Cancel is Later (spec E6). Else, while another
    # version than the running one is on disk: OK is Reload Gridkeeper (p321, spec R1), see selfReload.okAction.
    # OK and not a button input: a command can't end itself in its own events, OK closes the dialog, then it reloads
    okAction = selfReload.okAction(openedByCheck, canInstall(), runningVersion, updateCheck.manifestVersion(ADDIN_FOLDER))
    openedByCheck = False
    updateDialog = okAction == 'update'
    reloadDialog = okAction == 'reload'
    command.isOKButtonVisible = okAction is not None
    if updateDialog:
        command.okButtonText = tr('Update now')
        command.cancelButtonText = tr('Later')
    else:
        if reloadDialog:
            command.okButtonText = tr('Reload Gridkeeper')
        command.cancelButtonText = tr('Close')
    if okAction is not None:
        futil.add_handler(command.execute, command_execute, local_handlers=local_handlers)
    dialogSize.setDialogSize(command, 420, 300)
    inputs = command.commandInputs
    info = inputs.addTextBoxCommandInput(INFO_INPUT, '', infoHtml(reloadDialog, reloadWaiting), 8, True)
    info.isFullWidth = True
    # in the dialog opened from the menu, after Check now found a release
    updateNow = inputs.addBoolValueInput(UPDATE_NOW_INPUT, tr('Update now'), False, '', False)
    updateNow.isVisible = canInstall() and not updateDialog
    releaseNotes = inputs.addBoolValueInput(RELEASE_NOTES_INPUT, tr('Release notes'), False, '', False)
    releaseNotes.isVisible = pendingRelease is not None and bool(pendingRelease.pageUrl)
    inputs.addBoolValueInput(CHECK_NOW_INPUT, tr('Check now'), False, '', False)
    settings = updateCheck.readSettings(updateCheck.settingsPath(ADDIN_FOLDER))
    inputs.addBoolValueInput(CHECK_AT_STARTUP_INPUT, tr('Check for updates at startup'), True, '', settings['checkAtStartup'])
    futil.add_handler(command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(command.destroy, command_destroy, local_handlers=local_handlers)

def hideProgress(progress: adsk.core.ProgressDialog):
    try:
        if progress.isShowing:
            progress.hide()
    except Exception as err:
        futil.log(f'Gridkeeper updates: progress window not closed, {err}')

def installRelease(release: updateCheck.Release) -> str | None:
    """Installs release with a progress window, tells the user how it went and asks whether to reload. None when it
    isn't installed, else 'reload' or 'installed'"""
    global installing
    if installing:
        return None
    installing = True
    progress = ui.createProgressDialog()
    try:
        progress.isCancelButtonShown = False
        progress.show(CMD_NAME, tr('Downloading Gridkeeper {version}…', version=release.versionText), 0, max(release.assetSize or 0, 1))
        def downloaded(size: int):
            progress.progressValue = min(size, progress.maximumValue)
            adsk.doEvents()
        updateInstall.install(release, ADDIN_FOLDER, progress=downloaded)
    except updateInstall.UpdateError as err:
        hideProgress(progress)
        futil.log(f'Gridkeeper update to {release.versionText} failed: {err}')
        ui.messageBox(tr('Gridkeeper {version} couldn\'t be installed.\n\n{err}', version=release.versionText, err=err), CMD_NAME)
        return None
    finally:
        installing = False
        # also when something else went wrong, the caller's error message mustn't sit under it (second review)
        hideProgress(progress)
    # first, before any input of a dialog that may be gone by now (review finding 1). p321: Yes reloads Gridkeeper
    answer = ui.messageBox(updateCheck.successQuestion(release), CMD_NAME,
                           adsk.core.MessageBoxButtonTypes.YesNoButtonType, adsk.core.MessageBoxIconTypes.QuestionIconType)
    if answer == adsk.core.DialogResults.DialogYes:
        requestReload()
        return 'reload'
    return 'installed'

def command_execute(args: adsk.core.CommandEventArgs):
    """OK: Update now of the dialog the check opened, Reload Gridkeeper of the one from the menu (spec R1)"""
    try:
        if okAction == 'reload':
            # the dialog closes after this, the reload waits for it
            requestReload()
        elif okAction == 'update' and canInstall():
            installRelease(pendingRelease)
    except Exception as err:
        showFailure('Gridkeeper updates', CMD_NAME, err)

def command_input_changed(args: adsk.core.InputChangedEventArgs):
    global pendingRelease
    inputs = args.inputs
    changed = args.input
    info = adsk.core.TextBoxCommandInput.cast(inputs.itemById(INFO_INPUT))
    if installing:
        return
    try:
        if changed.id == CHECK_AT_STARTUP_INPUT:
            path = updateCheck.settingsPath(ADDIN_FOLDER)
            settings = updateCheck.readSettings(path)
            settings['checkAtStartup'] = adsk.core.BoolValueCommandInput.cast(changed).value
            if not updateCheck.writeSettings(path, settings):
                ui.messageBox(tr('The setting couldn\'t be saved to {path}.', path=path), CMD_NAME)
        elif changed.id == RELEASE_NOTES_INPUT:
            if pendingRelease is not None and pendingRelease.pageUrl:
                webbrowser.open(pendingRelease.pageUrl)
        elif changed.id == CHECK_NOW_INPUT:
            info.formattedText = tr('Checking GitHub for a new version…')
            adsk.doEvents()
            logs = []
            releases = updateCheck.fetchReleases(log=logs.append)
            for line in logs:
                futil.log(line)
            installed = updateCheck.manifestVersion(ADDIN_FOLDER) or runningVersion
            versionLine = updateCheck.versionLine(runningVersion, installed, okAction == "reload", reloadWaiting)
            if releases is None:
                reason = logs[-1] if logs else tr('no answer')
                info.formattedText = f'{versionLine}<br><br>{tr("GitHub couldn't be asked: {reason}", reason=reason)}'
            elif installed is None:
                info.formattedText = f'{versionLine}<br><br>{tr("The installed version is unknown, it can't be compared.")}'
            else:
                pendingRelease = updateCheck.newestRelease(releases, installed)
                info.formattedText = infoHtml(okAction == "reload", reloadWaiting) if pendingRelease is not None else f'{versionLine}<br><br>{tr("You have the newest version.")}'
            inputs.itemById(UPDATE_NOW_INPUT).isVisible = canInstall()
            inputs.itemById(RELEASE_NOTES_INPUT).isVisible = pendingRelease is not None and bool(pendingRelease.pageUrl)
        elif changed.id == UPDATE_NOW_INPUT and canInstall():
            installed = installRelease(pendingRelease)
            if installed is not None:
                # the dialog may have been closed meanwhile, the update is in place anyway
                try:
                    # Yes to reload: it waits for this dialog to close (p321, spec R2), the text says so (review finding 4)
                    info.formattedText = infoHtml(okAction == 'reload', reloadWaiting)
                    inputs.itemById(UPDATE_NOW_INPUT).isVisible = False
                except Exception as err:
                    futil.log(f'Gridkeeper updates: dialog not updated after the update, {err}')
    except Exception as err:
        showFailure('Gridkeeper updates', CMD_NAME, err)

def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
