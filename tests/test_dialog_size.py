"""
German dialogs are wider (click test round 60: at the English widths Fusion cut the German input names off). In
German a dialog starts 150 px wider and can't be made narrower than that, whatever size Fusion remembers; English
dialogs stay as they were. lib/ui/dialogSize.py
"""

import glob
import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
i18n = sys.modules["FusionGridfinityGenerator.lib.i18n"]


def _load():
    spec = importlib.util.spec_from_file_location("FusionGridfinityGenerator.lib.ui.dialogSize", os.path.join(ROOT, "lib", "ui", "dialogSize.py"))
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "FusionGridfinityGenerator.lib.ui"
    spec.loader.exec_module(module)
    return module


dialogSize = _load()


class FakeCommand:
    def __init__(self):
        self.calls = []

    def setDialogInitialSize(self, width, height):
        self.calls.append(("initial", width, height))

    def setDialogMinimumSize(self, width, height):
        self.calls.append(("minimum", width, height))


@pytest.fixture
def german():
    i18n.setLanguage("de", {})
    yield
    i18n.setLanguage("en")


def test_english_dialogs_keep_their_size():
    command = FakeCommand()
    dialogSize.setDialogSize(command, 450, 500)
    assert command.calls == [("initial", 450, 500)]


def test_english_minimum_stays():
    command = FakeCommand()
    dialogSize.setDialogSize(command, 450, 400, minimum=(450, 300))
    assert command.calls == [("initial", 450, 400), ("minimum", 450, 300)]


def test_german_dialogs_are_wider_and_not_narrower(german):
    command = FakeCommand()
    dialogSize.setDialogSize(command, 450, 500)
    assert command.calls == [("initial", 600, 500), ("minimum", 600, dialogSize.GERMAN_MINIMUM_HEIGHT)]


def test_german_minimum_keeps_its_height(german):
    command = FakeCommand()
    dialogSize.setDialogSize(command, 450, 400, minimum=(450, 300))
    assert command.calls == [("initial", 600, 400), ("minimum", 600, 300)]


def test_every_dialog_takes_its_size_from_the_helper():
    """The add-in's commands set no dialog size of their own, the development commands aside"""
    for path in glob.glob(os.path.join(ROOT, "commands", "*", "entry.py")):
        if "commandSnapshotTests" in path or "commandModelScreenshots" in path:
            continue
        with open(path, encoding="utf-8") as file:
            source = file.read()
        name = os.path.relpath(path, ROOT)
        assert ".setDialogInitialSize(" not in source and ".setDialogMinimumSize(" not in source, name
