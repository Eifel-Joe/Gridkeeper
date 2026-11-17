# Reload matrix (spec E13), way W3: stops and runs the TEST installation through Fusion's API (app.scripts, Script.stop
# and Script.run, found by uh_probe on Fusion 2706.1.17), then prints which version the running code read at start.
# Run with _runner.py, JOBS = ['uh_m_api_restart'], only while no Fusion dialog is open.
import os, sys
import adsk.core

TEST_ADDIN = r'D:\Entwicklung\Gridfinity\uh-test\Gridkeeper'


def run(_context):
    app = adsk.core.Application.get()
    scripts = app.scripts
    found = [scripts.item(index) for index in range(scripts.count)
             if os.path.normcase(os.path.normpath(scripts.item(index).folder or '')) == os.path.normcase(TEST_ADDIN)]
    print('scripts with folder', TEST_ADDIN, [(s.name, s.isRunning, s.version) for s in found])
    if len(found) != 1:
        print('not exactly one, nothing done')
        return
    script = found[0]
    print('stop ->', script.stop(), 'isRunning', script.isRunning)
    print('run ->', script.run(), 'isRunning', script.isRunning, 'manifest version', script.version)
    target = os.path.normcase(os.path.join(TEST_ADDIN, 'Gridkeeper.py'))
    names = [name for (name, module) in list(sys.modules.items())
             if os.path.normcase(getattr(module, '__file__', '') or '') == target]
    print('add-in modules', names)
    for name in names:
        updates = sys.modules.get(name + '.commands.commandUpdates.entry')
        print('running version after API restart:', getattr(updates, 'runningVersion', 'module not found'))
