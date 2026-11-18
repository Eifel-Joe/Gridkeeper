# Round 33 (p321) job D: stops and unlinks the TEST copy and runs the git add-in again. The copy's folder is removed
# afterwards with build_copy.py --remove.
import os, time
import adsk.core

GIT = r"D:\Entwicklung\Gridfinity\Gridkeeper"
COPY = os.path.join(os.environ["APPDATA"], "Autodesk", "Autodesk Fusion 360", "API", "AddIns", "Gridkeeper")


def norm(path):
    return os.path.normcase(os.path.normpath(path or ""))


def find(folder):
    scripts = adsk.core.Application.get().scripts
    return [scripts.item(i) for i in range(scripts.count) if norm(scripts.item(i).folder) == norm(folder)]


def show(label, found):
    print(label, [(s.name, s.folder, s.version, s.isRunning, s.isRunOnStartup) for s in found])


def probeLog():
    path = os.path.join(COPY, "probe.log")
    print("probe.log:")
    print(open(path, encoding="utf-8").read() if os.path.exists(path) else "(none)")


def run(_context):
    probeLog()
    for script in find(COPY):
        if script.isRunning:
            print("stop copy ->", script.stop())
        print("unlink copy ->", script.unlink())
    show("test copy", find(COPY))
    git = find(GIT)
    if len(git) == 1 and not git[0].isRunning:
        print("run git ->", git[0].run())
    show("git add-in", find(GIT))
