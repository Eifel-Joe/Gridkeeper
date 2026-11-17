# Reload matrix (spec E13), way W4: reloads the running TEST installation's modules as fusion-addin-reload.py does
# (stop, drop its modules, run again), then prints the version the reloaded code reads at start. Run with
# _runner.py, JOBS = ['uh_m_reload'], only while no Fusion dialog is open.
import os, sys, types

TEST_ADDIN = r'D:\Entwicklung\Gridfinity\uh-test\Gridkeeper'


def run(_context):
    target = os.path.normcase(os.path.join(TEST_ADDIN, 'Gridkeeper.py'))
    names = [name for (name, module) in list(sys.modules.items())
             if os.path.normcase(getattr(module, '__file__', '') or '') == target]
    print('add-in modules for', target, names)
    if len(names) != 1:
        print('not exactly one, nothing done')
        return
    name = names[0]
    old = sys.modules[name]
    path = old.__file__
    folder = old.__path__[0] if hasattr(old, '__path__') else os.path.dirname(path)
    old.stop('')
    removed = [n for n in list(sys.modules) if n == name or n.startswith(name + '.')]
    for n in removed:
        del sys.modules[n]
    module = types.ModuleType(name)
    module.__file__ = path
    module.__path__ = [folder]
    module.__package__ = name
    sys.modules[name] = module
    exec(compile(open(path, encoding='utf-8').read(), path, 'exec'), module.__dict__)
    module.run('')
    print('reloaded', len(removed), 'modules')
    updates = sys.modules.get(name + '.commands.commandUpdates.entry')
    print('running version after reload:', getattr(updates, 'runningVersion', 'module not found'))
