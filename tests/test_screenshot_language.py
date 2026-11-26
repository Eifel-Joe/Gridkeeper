"""
The dialog screenshots in German (round 60): --language de names the pictures name.de.png beside the English ones, as
the German docs pages find them (mkdocs-static-i18n), and Fusion's right-click menu shows the add-in's items translated.
"""

import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "screenshots")


def _module():
    if TOOL not in sys.path:
        sys.path.insert(0, TOOL)
    spec = importlib.util.spec_from_file_location("screenshotsUnderTest", os.path.join(TOOL, "screenshots.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


screenshots = _module()


def test_english_names_stay_as_they_are():
    shot = {"name": "context-menu"}
    assert screenshots.outputPath("out", shot, "dark", ["dark", "light"]) == os.path.join("out", "context-menu-dark.png")
    assert screenshots.outputPath("out", shot, "light", ["light"], "en") == os.path.join("out", "context-menu.png")


def test_german_pictures_get_the_language_suffix():
    shot = {"name": "context-menu"}
    assert screenshots.outputPath("out", shot, "dark", ["dark", "light"], "de") == os.path.join("out", "context-menu-dark.de.png")
    assert screenshots.outputPath("out", shot, "light", ["light"], "de") == os.path.join("out", "context-menu.de.png")
    animation = {"name": "bin-features", "steps": [{}]}
    assert screenshots.outputPath("out", animation, "dark", ["dark", "light"], "de") == os.path.join("out", "bin-features-dark.de.gif")


def test_menu_items_are_translated_and_the_shot_is_left_as_it_is():
    shot = {"name": "menu", "menu": {"items": [{"label": "Gridkeeper settings", "icon": "x.png"}, {"separator": True},
                                               {"label": "Copy", "shortcut": "Ctrl+C"}]}}
    german = {"Gridkeeper settings": "Gridkeeper Einstellungen"}
    translated = screenshots.translateMenu(shot, lambda text: german.get(text, text))
    assert translated["menu"]["items"][0] == {"label": "Gridkeeper Einstellungen", "icon": "x.png"}
    assert translated["menu"]["items"][1] == {"separator": True}
    assert translated["menu"]["items"][2]["label"] == "Copy"
    assert shot["menu"]["items"][0]["label"] == "Gridkeeper settings"
