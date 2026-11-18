# Round 33 (p321): builds the TEST copy of Gridkeeper for the self-restart measurement in Fusion's add-in folder, from
# this worktree as release.yml packs it, manifest 9.9.1, plus a probe appended to the copy's Gridkeeper.py only. The probe
# logs every start and, on the custom event GridkeeperR33SelfRestart, stops and runs its own add-in through Fusion's API
# from inside the add-in, as a "Reload Gridkeeper" button would. Plain Python, run outside Fusion:
#   python dev-notes/tools/r33-self-restart/build_copy.py          builds the copy
#   python dev-notes/tools/r33-self-restart/build_copy.py --no-probe builds it without the probe (the product's
#                                                         Reload Gridkeeper is tested, job r33_e_reload)
#   python dev-notes/tools/r33-self-restart/build_copy.py --remove removes it (after job D stopped it)
import json
import os
import shutil
import sys

WORKTREE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
COPY = os.path.join(os.environ['APPDATA'], 'Autodesk', 'Autodesk Fusion 360', 'API', 'AddIns', 'Gridkeeper')
RELEASE_FILES = ['Gridkeeper.manifest', 'Gridkeeper.py', 'config.py', 'LICENSE.md', 'lib', 'commands']
VERSION = '9.9.1'
# --version X.Y.Z sets another one, e.g. 1.0.0 for the click test of a real update (dev-notes/klicktest-r33.md part B)

PROBE = r'''

# --- round 33 self-restart probe, TEST COPY ONLY (dev-notes/tools/r33-self-restart/build_copy.py) ---
import json as _probeJson, os as _probeOs, sys as _probeSys, time as _probeTime, traceback as _probeTraceback
import adsk.core as _probeCore
from . import config

_PROBE_FOLDER = _probeOs.path.dirname(_probeOs.path.abspath(__file__))
_PROBE_EVENT = 'GridkeeperR33SelfRestart'
_probeHandlers = []

def _probeLog(text):
    with open(_probeOs.path.join(_PROBE_FOLDER, 'probe.log'), 'a', encoding='utf-8') as file:
        file.write(_probeTime.strftime('%H:%M:%S ') + text + '\n')

def _probeManifestVersion():
    with open(_probeOs.path.join(_PROBE_FOLDER, 'Gridkeeper.manifest'), encoding='utf-8') as file:
        return _probeJson.load(file)['version']

class _ProbeRestartHandler(_probeCore.CustomEventHandler):
    def notify(self, args):
        try:
            scripts = _probeCore.Application.get().scripts
            mine = [scripts.item(i) for i in range(scripts.count)
                    if _probeOs.path.normcase(_probeOs.path.normpath(scripts.item(i).folder or '')) == _probeOs.path.normcase(_PROBE_FOLDER)]
            _probeLog(f'handler: own scripts {len(mine)}')
            if len(mine) != 1:
                return
            script = mine[0]
            stopped = script.stop()
            _probeLog(f'handler: stop -> {stopped}, isRunning {script.isRunning}')
            started = script.run()
            _probeLog(f'handler: run -> {started}, isRunning {script.isRunning}')
        except Exception:
            _probeLog('handler: error ' + _probeTraceback.format_exc())

_probeOriginalRun = run
_probeOriginalStop = stop

def run(context):
    _probeOriginalRun(context)
    try:
        updates = _probeSys.modules.get(__name__ + '.commands.commandUpdates.entry')
        _probeLog(f'start: manifest {_probeManifestVersion()}, module {id(_probeSys.modules.get(__name__))}, '
                  f'runningVersion {getattr(updates, "runningVersion", "no module")}, dev tools {config.DEV_TOOLS}')
        app = _probeCore.Application.get()
        app.unregisterCustomEvent(_PROBE_EVENT)
        event = app.registerCustomEvent(_PROBE_EVENT)
        handler = _ProbeRestartHandler()
        event.add(handler)
        _probeHandlers.append((event, handler))
    except Exception:
        _probeLog('start: error ' + _probeTraceback.format_exc())

def stop(context):
    try:
        _probeLog('stop: called')
        for (event, handler) in _probeHandlers:
            event.remove(handler)
        _probeHandlers.clear()
        _probeCore.Application.get().unregisterCustomEvent(_PROBE_EVENT)
    except Exception:
        _probeLog('stop: error ' + _probeTraceback.format_exc())
    _probeOriginalStop(context)
'''


def build(probe=True, version=VERSION):
    if os.path.exists(COPY):
        sys.exit(f'{COPY} exists, not touched')
    for entry in RELEASE_FILES:
        source = os.path.join(WORKTREE, entry)
        target = os.path.join(COPY, entry)
        if os.path.isdir(source):
            shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', 'commandConfig'))
        else:
            os.makedirs(COPY, exist_ok=True)
            shutil.copy(source, target)
    manifestPath = os.path.join(COPY, 'Gridkeeper.manifest')
    with open(manifestPath, encoding='utf-8') as file:
        manifest = json.load(file)
    manifest['version'] = version
    # the git add-in has runOnStartup, the copy never starts by itself
    manifest['runOnStartup'] = False
    with open(manifestPath, 'w', encoding='utf-8') as file:
        json.dump(manifest, file, indent='\t')
    with open(os.path.join(COPY, 'Gridkeeper.py'), 'a', encoding='utf-8') as file:
        # without the probe a marker only, so --remove recognises the copy
        file.write(PROBE if probe else '\n# --- round 33 self-restart probe, TEST COPY ONLY: left out (--no-probe) ---\n')
    print('built', COPY, version, 'probe' if probe else 'no probe', 'has .git:', os.path.exists(os.path.join(COPY, '.git')))


def remove():
    entry = os.path.join(COPY, 'Gridkeeper.py')
    if (os.path.exists(os.path.join(COPY, '.git')) or not os.path.isfile(entry)
            or 'round 33 self-restart probe' not in open(entry, encoding='utf-8').read()):
        sys.exit('not the test copy, not touched')
    shutil.rmtree(COPY)
    print('removed', COPY)


if __name__ == '__main__':
    version = sys.argv[sys.argv.index('--version') + 1] if '--version' in sys.argv else VERSION
    remove() if '--remove' in sys.argv else build(probe='--no-probe' not in sys.argv, version=version)
