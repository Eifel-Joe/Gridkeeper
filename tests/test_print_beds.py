"""
The printer list of the baseplate and export dialogs (lib/printBeds.py, as upstream 1ac1579 has it). Round
r29-export, Bambu click test 17.11.2026: Bambu's printers apart, with where the slicer puts the purge tower and the
area the printer keeps free, read from Bambu Studio 02.09.01.70's printer profiles (resources/profiles/BBL/machine,
the 0.4 nozzle profiles with what they inherit). Round 55 (p680): one entry per Bambu printer profile, the Bambu
Studio profile names of each, and the printer chosen last.
"""

import importlib.util
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "lib", "printBeds.py")
spec = importlib.util.spec_from_file_location("printBeds", PATH)
printBeds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(printBeds)

WIPING_CORNER = [(0, 0, 18, 28)]
P1_X1_TOWER = (0.644, 0.977)

# name: (printable_area, default_wipe_tower_pos, bed_exclude_area) of Bambu Studio's profiles
BAMBU = {
    "Bambu Lab A1 mini": ((180, 180), (0.0, 1.0), []),
    "Bambu Lab A1": ((256, 256), (0.0, 1.0), []),
    "Bambu Lab A2L": ((330, 320), (0.0, 1.0), []),
    "Bambu Lab P1P": ((256, 256), P1_X1_TOWER, WIPING_CORNER),
    "Bambu Lab P1S": ((256, 256), P1_X1_TOWER, WIPING_CORNER),
    "Bambu Lab X1": ((256, 256), P1_X1_TOWER, WIPING_CORNER),
    "Bambu Lab X1 Carbon": ((256, 256), P1_X1_TOWER, WIPING_CORNER),
    "Bambu Lab X1E": ((256, 256), P1_X1_TOWER, WIPING_CORNER),
    "Bambu Lab P2S": ((256, 256), P1_X1_TOWER, []),
    "Bambu Lab X2D": ((256, 256), P1_X1_TOWER, []),
    "Bambu Lab H2C": ((330, 320), P1_X1_TOWER, []),
    "Bambu Lab H2D": ((350, 320), P1_X1_TOWER, []),
    "Bambu Lab H2D Pro": ((350, 320), P1_X1_TOWER, []),
    "Bambu Lab H2S": ((340, 320), P1_X1_TOWER, []),
    "Bambu Lab H3C": ((330, 320), (1.0, 0.0), []),
}

# the spec's table: printer, process and filament profile of each, default_print_profile and default_filament_profile
# of the printer profile
PROFILES = {
    "Bambu Lab A1 mini": ("Bambu Lab A1 mini 0.4 nozzle", "0.20mm Standard @BBL A1M", "Bambu PLA Basic @BBL A1M"),
    "Bambu Lab A1": ("Bambu Lab A1 0.4 nozzle", "0.20mm Standard @BBL A1", "Bambu PLA Basic @BBL A1"),
    "Bambu Lab A2L": ("Bambu Lab A2L 0.4 nozzle", "0.20mm Standard @BBL A2L", "Bambu PLA Basic @BBL A2L 0.4 nozzle"),
    "Bambu Lab P1P": ("Bambu Lab P1P 0.4 nozzle", "0.20mm Standard @BBL P1P", "Bambu PLA Basic @BBL P1P"),
    "Bambu Lab P1S": ("Bambu Lab P1S 0.4 nozzle", "0.20mm Standard @BBL X1C", "Bambu PLA Basic @BBL P1S 0.4 nozzle"),
    "Bambu Lab X1": ("Bambu Lab X1 0.4 nozzle", "0.20mm Standard @BBL X1C", "Bambu PLA Basic @BBL X1"),
    "Bambu Lab X1 Carbon": ("Bambu Lab X1 Carbon 0.4 nozzle", "0.20mm Standard @BBL X1C", "Bambu PLA Basic @BBL X1C"),
    "Bambu Lab X1E": ("Bambu Lab X1E 0.4 nozzle", "0.20mm Standard @BBL X1C", "Bambu PLA Basic @BBL X1C"),
    "Bambu Lab P2S": ("Bambu Lab P2S 0.4 nozzle", "0.20mm Standard @BBL P2S", "Bambu PLA Basic @BBL P2S"),
    "Bambu Lab X2D": ("Bambu Lab X2D 0.4 nozzle", "0.20mm Standard @BBL X2D", "Bambu PLA Basic @BBL X2D 0.4 nozzle"),
    "Bambu Lab H2C": ("Bambu Lab H2C 0.4 nozzle", "0.20mm Standard @BBL H2C", "Bambu PLA Basic @BBL H2C"),
    "Bambu Lab H2D": ("Bambu Lab H2D 0.4 nozzle", "0.20mm Standard @BBL H2D", "Bambu PLA Basic @BBL H2D"),
    "Bambu Lab H2D Pro": ("Bambu Lab H2D Pro 0.4 nozzle", "0.20mm Standard @BBL H2DP", "Bambu PLA Basic @BBL H2DP"),
    "Bambu Lab H2S": ("Bambu Lab H2S 0.4 nozzle", "0.20mm Standard @BBL H2S", "Bambu PLA Basic @BBL H2S"),
    "Bambu Lab H3C": ("Bambu Lab H3C 0.4 nozzle", "0.20mm Standard @BBL H3C", "Bambu PLA Basic @BBL H3C"),
}


@pytest.mark.parametrize("name", sorted(BAMBU))
def test_every_bambu_printer_has_its_bed_tower_spot_and_excluded_area(name):
    (size, tower, excluded) = BAMBU[name]
    label = printBeds.presetLabel(name)
    assert printBeds.PRINT_BED_PRESETS[label] == size
    assert printBeds.purgeAnchor(label) == tower
    assert printBeds.excludedAreas(label) == excluded


def test_the_bambu_printers_are_exactly_those_of_the_spec():
    assert [name for name in printBeds.PRINT_BED_SIZES if name.startswith("Bambu Lab")] == list(BAMBU)


def test_the_upstream_names_of_the_tables():
    assert set(printBeds.PURGE_ANCHORS) <= set(printBeds.PRINT_BED_SIZES)
    assert set(printBeds.EXCLUDED_AREAS) <= set(printBeds.PRINT_BED_SIZES)


def test_the_old_shared_bambu_entries_are_gone():
    for name in ("Bambu Lab A1, P1, X1", "Bambu Lab P1P, P1S, X1, X1C, X1E", "Bambu Lab P2S, X2D", "Bambu Lab H2D, H2D Pro"):
        assert name not in printBeds.PRINT_BED_SIZES


def test_the_old_shared_entries_open_as_one_printer_of_the_same_bed():
    old = {
        "Bambu Lab A1, P1, X1 (256 x 256 mm)": "Bambu Lab X1 Carbon (256 x 256 mm)",
        "Bambu Lab P1P, P1S, X1, X1C, X1E (256 x 256 mm)": "Bambu Lab X1 Carbon (256 x 256 mm)",
        "Bambu Lab P2S, X2D (256 x 256 mm)": "Bambu Lab P2S (256 x 256 mm)",
        "Bambu Lab H2D, H2D Pro (350 x 320 mm)": "Bambu Lab H2D (350 x 320 mm)",
    }
    assert printBeds.OLD_BED_NAMES == old
    for (gone, now) in old.items():
        assert printBeds.currentLabel(gone) == now
        assert now in printBeds.PRINT_BED_PRESETS
    assert printBeds.currentLabel("Prusa MK3, MK4 (250 x 210 mm)") == "Prusa MK3, MK4 (250 x 210 mm)"


def test_other_printers_and_custom_have_the_back_right_corner_and_nothing_excluded():
    for label in ("Custom", printBeds.presetLabel("Prusa MK3, MK4"), "Gone printer"):
        assert printBeds.purgeAnchor(label) == printBeds.DEFAULT_PURGE_ANCHOR == (1.0, 1.0)
        assert printBeds.excludedAreas(label) == []


def test_the_labels_of_the_other_printers_stay():
    # saved dialog defaults store them
    assert printBeds.presetLabel("Prusa MK3, MK4") == "Prusa MK3, MK4 (250 x 210 mm)"
    assert printBeds.presetLabel("Bambu Lab A1 mini") == "Bambu Lab A1 mini (180 x 180 mm)"


# ---------------------------------------------------------------------------
# the printer chosen last, shared by the baseplate and export dialogs
# ---------------------------------------------------------------------------

def test_the_last_printer_is_read_back(tmp_path):
    path = str(tmp_path / "commandConfig" / "lastPrinter.txt")
    assert printBeds.readLastPrinter(path) is None
    printBeds.writeLastPrinter("Bambu Lab A1 (256 x 256 mm)", path)
    assert printBeds.readLastPrinter(path) == "Bambu Lab A1 (256 x 256 mm)"
    printBeds.writeLastPrinter(printBeds.PRINT_BED_CUSTOM, path)
    assert printBeds.readLastPrinter(path) == printBeds.PRINT_BED_CUSTOM


def test_an_old_or_unknown_last_printer(tmp_path):
    path = tmp_path / "lastPrinter.txt"
    path.write_text("Bambu Lab P2S, X2D (256 x 256 mm)\n", encoding="utf-8")
    assert printBeds.readLastPrinter(str(path)) == "Bambu Lab P2S (256 x 256 mm)"
    path.write_text("Gone printer", encoding="utf-8")
    assert printBeds.readLastPrinter(str(path)) is None


def test_an_unreadable_last_printer_counts_as_none(tmp_path):
    # a folder where the file should be
    path = tmp_path / "lastPrinter.txt"
    path.mkdir()
    assert printBeds.readLastPrinter(str(path)) is None
    assert not printBeds.writeLastPrinter("Custom", str(path))


def test_the_last_printer_file_is_in_the_addins_config_folder():
    assert printBeds.LAST_PRINTER_PATH == os.path.join(ROOT, "commandConfig", "lastPrinter.txt")


# ---------------------------------------------------------------------------
# Bambu Studio's profile names, round 55
# ---------------------------------------------------------------------------

SYSTEM_PROFILES = json.load(open(os.path.join(ROOT, "tests", "fixtures", "bambu_system_profiles.json"), encoding="utf-8"))


EXTRUDERS = SYSTEM_PROFILES["machine_extruders"]


@pytest.mark.parametrize("name", sorted(PROFILES))
def test_every_bambu_printer_gets_a_project(name):
    # round 56 (p690): the printers with two nozzles too; since round 57 every Bambu printer's project brings purging
    # volumes, see threeMf.flushSettings
    assert printBeds.isBambu(printBeds.presetLabel(name))


@pytest.mark.parametrize("name", sorted(PROFILES))
def test_the_extruders_are_bambu_studios(name):
    profiles = printBeds.bambuProfiles(printBeds.presetLabel(name))
    extruders = EXTRUDERS[profiles.printer]
    assert profiles.extruders == extruders["nozzle_diameter"] == SYSTEM_PROFILES["machine_nozzles"][profiles.printer]
    assert list(profiles.nozzleVolumes) == extruders["nozzle_volume"]
    assert list(profiles.flushDatasets) == extruders["nozzle_flush_dataset"]
    assert list(profiles.hotends) == extruders["extruder_max_nozzle_count"]
    assert profiles.hotendAsExtruder == bool(extruders["handle_hotend_as_extruder"])


def test_the_printers_with_two_extruders():
    two = {name for (name, profiles) in PROFILES.items() if EXTRUDERS[profiles[0]]["nozzle_diameter"] == 2}
    assert two == {"Bambu Lab H2C", "Bambu Lab H2D", "Bambu Lab H2D Pro", "Bambu Lab X2D"}
    assert not hasattr(printBeds, "TWO_NOZZLES")


def test_the_h3c_changes_hotends_on_one_extruder():
    profiles = printBeds.bambuProfiles(printBeds.presetLabel("Bambu Lab H3C"))
    assert (profiles.extruders, sum(profiles.hotends), profiles.hotendAsExtruder) == (1, 9, True)


@pytest.mark.parametrize("name", sorted(PROFILES))
def test_every_bambu_printer_names_its_profiles(name):
    label = printBeds.presetLabel(name)
    profiles = printBeds.bambuProfiles(label)
    assert (profiles.printer, profiles.process, profiles.filament) == PROFILES[name]


@pytest.mark.parametrize("name", sorted(PROFILES))
def test_the_profile_names_are_bambu_studios(name):
    profiles = printBeds.bambuProfiles(printBeds.presetLabel(name))
    assert profiles.printer in SYSTEM_PROFILES["machine"]
    assert profiles.process in SYSTEM_PROFILES["process"]
    assert profiles.filament in SYSTEM_PROFILES["filament"]


def test_other_printers_have_no_bambu_profiles():
    for label in ("Custom", printBeds.presetLabel("Prusa MK3, MK4"), "Gone printer"):
        assert not printBeds.isBambu(label)
        assert printBeds.bambuProfiles(label) is None


def test_the_profile_table_covers_every_bambu_printer():
    assert set(printBeds.BAMBU_PROFILES) == set(BAMBU)
