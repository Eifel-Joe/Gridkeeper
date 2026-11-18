# Round 33 (p321) job E: the product's Reload Gridkeeper on the TEST copy built with --no-probe. Sets the copy's
# manifest to 9.9.2 (a new version on disk) and fires Gridkeeper's own reload event, as its button does. Job C then
# shows the running version of the loaded package and whether the commands open.
import json, os, time
import adsk.core

COPY = os.path.join(os.environ["APPDATA"], "Autodesk", "Autodesk Fusion 360", "API", "AddIns", "Gridkeeper")
RELOAD_EVENT_ID = "EifelJoe_Gridkeeper_reload"


def run(_context):
    path = os.path.join(COPY, "Gridkeeper.manifest")
    with open(path, encoding="utf-8") as file:
        manifest = json.load(file)
    manifest["version"] = "9.9.2"
    with open(path, "w", encoding="utf-8") as file:
        json.dump(manifest, file, indent="\t")
    print("manifest of the copy now", manifest["version"])
    print("fire ->", adsk.core.Application.get().fireCustomEvent(RELOAD_EVENT_ID, "reload"))
