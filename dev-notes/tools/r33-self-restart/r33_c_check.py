# Round 33 (p321) job C: after the self-restart, the probe log, the copy's state and whether the commands open
# (W4 left them dead: no dialog). Each command is executed, Fusion gets events, the active command is read, terminated.
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

PREFIX = "EifelJoe_Gridkeeper_"
COMMANDS = ["cmdUpdates", "cmdBin", "cmdBaseplate", "cmdLabel", "cmdBox"]


def runningVersions():
    """the runningVersion each loaded Gridkeeper package read at its start, by the folder of its Gridkeeper.py"""
    import sys
    for (name, module) in list(sys.modules.items()):
        path = getattr(module, "__file__", "") or ""
        if norm(path).endswith(norm("/Gridkeeper/Gridkeeper.py")):
            updates = sys.modules.get(name + ".commands.commandUpdates.entry")
            print("module", path, "id", id(module), "runningVersion", getattr(updates, "runningVersion", "no module"))


def run(_context):
    probeLog()
    runningVersions()
    show("git add-in", find(GIT))
    show("test copy", find(COPY))
    ui = adsk.core.Application.get().userInterface
    for name in COMMANDS:
        definition = ui.commandDefinitions.itemById(PREFIX + name)
        if not definition:
            print(name, "no definition")
            continue
        definition.execute()
        active = None
        for _ in range(40):
            adsk.doEvents()
            time.sleep(0.05)
            active = ui.activeCommand
            if active == PREFIX + name:
                break
        print(name, "active command:", active)
        ui.terminateActiveCommand()
        adsk.doEvents()
