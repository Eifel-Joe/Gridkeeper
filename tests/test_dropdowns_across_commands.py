"""
The dialogs opened one after another in German keep their dropdowns' English values (round 60). Several commands use
the same dropdown id (sizing_mode_dropdown in the baseplate and the insert, text_style, text_color and surface_dropdown
in both labels, magnet_size in bin, baseplate and box); opening the baseplate and then the insert failed in Fusion,
both sizing modes are German "Rastereinheiten". The dialogs run in the screenshot tool's fake Fusion API
(tools/screenshots/dialogRecorder.py), in a process of their own because the tests' Fusion stubs are loaded here.
"""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMANDS = ["bin", "baseplate", "export", "commandCreateBox", "commandCreateBoxLabel", "commandCreateLabel"]

SCRIPT = """
import json, sys
sys.path.insert(0, 'tools/screenshots')
import dialogRecorder
dialogRecorder.setLanguage(sys.argv[1])
from gridfinityAddin.lib.ui import dropdowns
result = []
for command in sys.argv[2:]:
    session = dialogRecorder.DialogSession(command)
    values = {}
    for input in dialogRecorder._allInputs(session.inputs):
        if type(input).__name__ == 'DropDownCommandInput':
            values[input.id] = [dropdowns.valueOf(input, input.listItems.item(i).name) for i in range(input.listItems.count)]
    result.append([command, values])
print(json.dumps(result))
"""


def _open(language: str, commands: list[str]) -> dict:
    run = subprocess.run([sys.executable, "-c", SCRIPT, language, *commands], cwd=ROOT, capture_output=True,
                         text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert run.returncode == 0, run.stderr[-2000:]
    opened = {}
    for (command, values) in json.loads(run.stdout.strip().splitlines()[-1]):
        opened.setdefault(command, []).append(values)
    return opened


def test_german_dialogs_opened_one_after_another_keep_the_english_values():
    english = {command: values[0] for (command, values) in _open("en", COMMANDS).items()}
    # each dialog after every other one, and again after the others in the opposite order
    order = COMMANDS + COMMANDS[::-1]
    german = _open("de", order)
    for command in COMMANDS:
        for values in german[command]:
            assert values == english[command], command


def test_some_dropdown_ids_are_shared_between_commands():
    """The case the test above is for; if no id is shared any more it still holds, but should be looked at"""
    english = _open("en", COMMANDS)
    ids = [dropdownId for values in english.values() for dropdownId in values[0]]
    assert "sizing_mode_dropdown" in [dropdownId for dropdownId in ids if ids.count(dropdownId) > 1]
