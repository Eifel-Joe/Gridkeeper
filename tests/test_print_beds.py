"""
The printer list of the baseplate and export dialogs (commands/commandCreateBaseplate/printBeds.py). Round r29-export,
Bambu click test 17.11.2026: Bambu's printers apart, with where the slicer puts the purge tower, read from Bambu
Studio 02.09.01.70's printer profiles (resources/profiles/BBL/machine, the 0.4 nozzle profiles with what they
inherit).
"""

import importlib.util
import os

import pytest

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "commands", "commandCreateBaseplate", "printBeds.py")
spec = importlib.util.spec_from_file_location("printBeds", PATH)
printBeds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(printBeds)


# name: (printable_area, default_wipe_tower_pos) of Bambu Studio's profiles; the excluded areas are the user's
# (Jörg 17.11.2026: „Die Sperrzone ist Sache des Users.“)
BAMBU = {
    "Bambu Lab A1 mini": ((180, 180), (0.0, 1.0)),
    "Bambu Lab A1": ((256, 256), (0.0, 1.0)),
    "Bambu Lab A2L": ((330, 320), (0.0, 1.0)),
    "Bambu Lab P1P, P1S, X1, X1C, X1E": ((256, 256), (0.644, 0.977)),
    "Bambu Lab P2S, X2D": ((256, 256), (0.644, 0.977)),
    "Bambu Lab H2C": ((330, 320), (0.644, 0.977)),
    "Bambu Lab H2D, H2D Pro": ((350, 320), (0.644, 0.977)),
    "Bambu Lab H2S": ((340, 320), (0.644, 0.977)),
    "Bambu Lab H3C": ((330, 320), (1.0, 0.0)),
}


@pytest.mark.parametrize("name", sorted(BAMBU))
def test_every_bambu_printer_has_its_bed_and_tower_spot(name):
    (size, tower) = BAMBU[name]
    label = printBeds.presetLabel(name)
    assert printBeds.PRINT_BED_PRESETS[label] == size
    assert printBeds.purgeAnchor(label) == tower


def test_the_old_shared_bambu_entry_is_gone():
    # the A1's tower stands back left, the P1's and X1's at the back at two thirds of the width
    assert "Bambu Lab A1, P1, X1" not in printBeds.PRINT_BED_SIZES


def test_other_printers_and_custom_have_the_back_right_corner():
    for label in ("Custom", printBeds.presetLabel("Prusa MK3, MK4"), "Gone printer"):
        assert printBeds.purgeAnchor(label) == printBeds.DEFAULT_PURGE_ANCHOR == (1.0, 1.0)


def test_the_labels_of_the_other_printers_stay():
    # saved dialog defaults store them
    assert printBeds.presetLabel("Prusa MK3, MK4") == "Prusa MK3, MK4 (250 x 210 mm)"
    assert printBeds.presetLabel("Bambu Lab A1 mini") == "Bambu Lab A1 mini (180 x 180 mm)"
