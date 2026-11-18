# Round 33 (p321) job A: stops the git add-in (same command ids as the copy), registers and runs the TEST copy
# built by build_copy.py. Fusion script, one run(_context), no document.
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
    git = find(GIT)
    show("git add-in", git)
    if len(git) != 1:
        print("not exactly one git add-in, nothing done")
        return
    if git[0].isRunning:
        print("stop git ->", git[0].stop(), "isRunning", git[0].isRunning)
    copy = find(COPY)
    if not copy:
        scripts = adsk.core.Application.get().scripts
        try:
            added = scripts.addExisting(COPY)
        except Exception as err:
            print("addExisting(folder) failed:", err)
            added = scripts.addExisting(os.path.join(COPY, "Gridkeeper.py"))
        print("added", added and added.folder)
        copy = find(COPY)
    show("test copy", copy)
    if len(copy) != 1:
        print("not exactly one test copy, git add-in stays stopped, run job D")
        return
    print("run copy ->", copy[0].run(), "isRunning", copy[0].isRunning)
    probeLog()
