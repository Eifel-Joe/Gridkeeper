# Fusion job 2 of the update round (p310, plan Task 6): (a) a background thread's custom event arrives in Fusion's main
# thread, as commands/commandUpdates relies on; (b) updateInstall.install swaps a test add-in folder (9.9.8 -> 9.9.9,
# built from the worktree, ZIP served by a fake urlopen, no network) inside Fusion's Python, the saved defaults carried
# over; (c) the panel Utilities > Add-ins is there. Touches only fusion-auftraege\uh_work, no document, no running
# add-in. Run with _runner.py, JOBS = ['uh_thread_install'].
import hashlib, io, os, shutil, sys, threading, time
import adsk.core

sys.path.insert(0, r'D:\Entwicklung\Gridfinity\Gridkeeper\.claude\worktrees\upstream-2026-11-16-e588a3\dev-notes\tools\update-fusion-jobs')
import uh_common

WORK = r'D:\Entwicklung\Gridfinity\fusion-auftraege\uh_work'
EVENT_ID = 'EifelJoe_GridkeeperUpdateJobTest'
# kept alive past the job, Fusion drops handlers nobody references
keep = []


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class Release:
    def __init__(self, payload):
        self.version = (9, 9, 9)
        self.assetUrl = 'https://example.invalid/Gridkeeper-v9.9.9.zip'
        self.assetSize = len(payload)
        self.assetDigest = 'sha256:' + hashlib.sha256(payload).hexdigest()


def run(_context):
    app = adsk.core.Application.get()
    ui = app.userInterface

    # (a) custom event from a thread
    received = []

    class Handler(adsk.core.CustomEventHandler):
        def notify(self, args):
            received.append((args.additionalInfo, threading.current_thread() is threading.main_thread()))

    app.unregisterCustomEvent(EVENT_ID)
    event = app.registerCustomEvent(EVENT_ID)
    handler = Handler()
    event.add(handler)
    keep.append(handler)
    threading.Thread(target=lambda: (time.sleep(0.5), app.fireCustomEvent(EVENT_ID, 'from thread')), daemon=True).start()
    started = time.time()
    while not received and time.time() - started < 10:
        adsk.doEvents()
        time.sleep(0.05)
    print('custom event:', received, 'after %.1f s' % (time.time() - started))
    event.remove(handler)
    app.unregisterCustomEvent(EVENT_ID)

    # (b) install into a test folder
    updateCheck = uh_common.load('updateCheck')
    updateInstall = uh_common.load('updateInstall')
    shutil.rmtree(WORK, ignore_errors=True)
    addin = uh_common.writeFolder(os.path.join(WORK, 'addins', 'Gridkeeper'), '9.9.8', {
        'commands/commandCreateBin/commandConfig/defaults.json': b'{"kept": true}',
        'updateConfig/update.json': b'{"checkAtStartup": false}',
    })
    payload = uh_common.releaseZip('9.9.9')
    started = time.time()
    way = updateInstall.install(Release(payload), addin, urlopen=lambda request, timeout=None: Response(payload))
    print('install:', way, '%.1f s' % (time.time() - started))
    print('manifest now', updateCheck.manifestVersion(addin))
    with open(os.path.join(addin, 'commands', 'commandCreateBin', 'commandConfig', 'defaults.json'), 'rb') as file:
        print('defaults kept:', file.read())
    print('settings:', updateCheck.readSettings(updateCheck.settingsPath(addin)))
    print('work folder:', sorted(os.listdir(os.path.join(WORK, 'addins', '.gridkeeper-update'))))

    # (c) the panel of the new command
    panel = ui.workspaces.itemById('FusionSolidEnvironment').toolbarPanels.itemById('SolidScriptsAddinsPanel')
    print('panel SolidScriptsAddinsPanel:', None if panel is None else panel.name)
    print('active command:', ui.activeCommand)
