"""
Tests for the magnet size choice before the free "Magnet cutout depth" field (round 27, p263; Jörg 16.11.2026:
"Magnetlöcher einstellbar. 2,4mm für 2mm Magnete und 3,4mm für 3mm Magnete."). Only the depth is saved, the choice is
read back from it, so settings files with other depths still load.
"""

import pytest

from tests.test_joint_origin_layout import _load

sizes = _load("magnetSizes")


@pytest.mark.parametrize("depth, choice", [(0.24, sizes.SIZE_6X2), (0.34, sizes.SIZE_6X3), (0.3, sizes.CUSTOM), (0.2, sizes.CUSTOM)])
def test_choice_for_depth(depth, choice):
    assert sizes.choiceForDepth(depth, sizes.ALL_CHOICES) == choice


def test_depth_for_choice():
    assert sizes.depthForChoice(sizes.SIZE_6X2) == 0.24
    assert sizes.depthForChoice(sizes.SIZE_6X3) == 0.34


def test_custom_has_no_depth():
    assert sizes.depthForChoice(sizes.CUSTOM) is None


def test_box_offers_only_6x2():
    # Jörg 16.11.2026: "Box nur 6×2", a 3.4 mm hole would break through Pred's 2.8 mm floor pad
    assert sizes.BOX_CHOICES == [sizes.SIZE_6X2, sizes.CUSTOM]
    assert sizes.choiceForDepth(0.34, sizes.BOX_CHOICES) == sizes.CUSTOM


def test_names_say_magnet_and_depth():
    assert sizes.SIZE_6X2 == "6×2 mm (2.4 mm deep)"
    assert sizes.SIZE_6X3 == "6×3 mm (3.4 mm deep)"
    assert sizes.ALL_CHOICES == [sizes.SIZE_6X2, sizes.SIZE_6X3, sizes.CUSTOM]


import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.parametrize("folder, depthInput", [
    ("commandCreateBin", "BIN_MAGNET_HEIGHT_INPUT"),
    ("commandCreateBaseplate", "BASEPLATE_MAGNET_HEIGHT_INPUT"),
    ("commandCreateBox", "MAGNET_DEPTH_INPUT"),
])
def test_magnet_size_choice_comes_before_the_depth(folder, depthInput):
    """p263: bins, baseplates and boxes get the choice right before the free depth field, and read it back from the
    depth when settings are loaded"""
    source = open(os.path.join(ROOT, "commands", folder, "entry.py"), encoding="utf-8").read()
    choice = source.find("magnetSizes.")
    depthField = re.search(r"add(?:ValueInput|Length)\([^)]*?\b" + depthInput + r"\b", source)
    assert choice != -1 and depthField is not None
    # the box adds its own dropdown, bin and baseplate the shared one of lib/ui/magnetSizeInput.py
    added = max(source.find("'Magnet size'"), source.find('addMagnetSizeInput('))
    assert added != -1 and added < depthField.start(), "the choice is added before the depth field"
    assert ("choiceForDepth" in source or "syncMagnetSize" in source) and ("depthForChoice" in source or "onMagnetSizeChanged" in source)
