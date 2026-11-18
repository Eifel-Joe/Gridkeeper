# Round 33 (p321) job B: simulates the update (copy's manifest 9.9.2) and fires the probe's custom event. Its
# handler runs inside the TEST copy and stops and runs its own add-in through Fusion's API, after this script returns.
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

import json


def run(_context):
    path = os.path.join(COPY, "Gridkeeper.manifest")
    with open(path, encoding="utf-8") as file:
        manifest = json.load(file)
    manifest["version"] = "9.9.2"
    with open(path, "w", encoding="utf-8") as file:
        json.dump(manifest, file, indent="\t")
    show("test copy", find(COPY))
    print("fire ->", adsk.core.Application.get().fireCustomEvent("GridkeeperR33SelfRestart"))
