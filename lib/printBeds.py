import dataclasses
import os

# The printers of the baseplate and export dialogs, kept free of Fusion imports so it can be unit tested. In lib as
# upstream has it since 1ac1579 (Le0Michine, "Pack the 3MF export on print plates"), with its table names.

PRINT_BED_CUSTOM = 'Custom'

# usable bed size X, Y in mm
PRINT_BED_SIZES: dict[str, tuple[float, float]] = {
    # Bambu Lab apart (round r29-export, click test 17.11.2026): the export keeps their purge tower's spot and excluded
    # area free, see PURGE_ANCHORS. From Bambu Studio 02.09.01.70's printer profiles, printable_area. One entry per
    # printer profile (round 55, p680), the export's Bambu Studio project names it, see BAMBU_PROFILES
    'Bambu Lab A1 mini': (180, 180),
    'Bambu Lab A1': (256, 256),
    'Bambu Lab A2L': (330, 320),
    'Bambu Lab P1P': (256, 256),
    'Bambu Lab P1S': (256, 256),
    'Bambu Lab X1': (256, 256),
    'Bambu Lab X1 Carbon': (256, 256),
    'Bambu Lab X1E': (256, 256),
    'Bambu Lab P2S': (256, 256),
    'Bambu Lab X2D': (256, 256),
    'Bambu Lab H2C': (330, 320),
    'Bambu Lab H2D': (350, 320),
    'Bambu Lab H2D Pro': (350, 320),
    'Bambu Lab H2S': (340, 320),
    'Bambu Lab H3C': (330, 320),
    'Prusa MINI': (180, 180),
    'Prusa MK3, MK4': (250, 210),
    'Prusa CORE One': (250, 220),
    'Prusa XL': (360, 360),
    'Creality Ender-3': (220, 220),
    'Creality K1, K1C': (220, 220),
    'Creality K1 Max': (300, 300),
    'Elegoo Neptune 4': (225, 225),
    'Voron 0': (120, 120),
    'Voron 250': (250, 250),
    'Voron 300': (300, 300),
    'Voron 350': (350, 350),
}

def presetLabel(name: str) -> str:
    (width, length) = PRINT_BED_SIZES[name]
    return f'{name} ({width:g} x {length:g} mm)'

# labels are what the dropdown shows and saved dialog defaults store, keep them stable
PRINT_BED_PRESETS: dict[str, tuple[float, float]] = {presetLabel(name): size for (name, size) in PRINT_BED_SIZES.items()}

# saved labels of entries gone from the list, by the one of the same bed they open as. Round 55: the shared Bambu
# entries are apart, a shared one opens as its common printer (the X1 Carbon, as the export's default was)
OLD_BED_NAMES = {
    'Bambu Lab A1, P1, X1 (256 x 256 mm)': presetLabel('Bambu Lab X1 Carbon'),
    'Bambu Lab P1P, P1S, X1, X1C, X1E (256 x 256 mm)': presetLabel('Bambu Lab X1 Carbon'),
    'Bambu Lab P2S, X2D (256 x 256 mm)': presetLabel('Bambu Lab P2S'),
    'Bambu Lab H2D, H2D Pro (350 x 320 mm)': presetLabel('Bambu Lab H2D'),
}

def currentLabel(label: str) -> str:
    """The label as the list has it now, see OLD_BED_NAMES"""
    return OLD_BED_NAMES.get(label, label)

def presetLabelOf(printer: str) -> str | None:
    """The dropdown's label of a printer by its label or its name, none for custom or one not listed"""
    if printer in PRINT_BED_PRESETS:
        return printer
    return presetLabel(printer) if printer in PRINT_BED_SIZES else None

def presetBedSize(label: str) -> tuple[float, float] | None:
    """Bed size in Fusion internal units, cm"""
    if label not in PRINT_BED_PRESETS:
        return None
    (width, length) = PRINT_BED_PRESETS[label]
    return (width / 10, length / 10)

# Where Bambu Studio puts the purge tower, as a share of the bed's width and depth, its corner nearest the origin
# (default_wipe_tower_pos of the printer profiles, Bambu Studio PartPlate.cpp get_wipe_tower_default_pos). Every other
# printer, and Custom, the back right corner, where the purge tower has to be moved by hand
DEFAULT_PURGE_ANCHOR = (1.0, 1.0)
_P1_X1_TOWER = (0.644, 0.977)
PURGE_ANCHORS: dict[str, tuple[float, float]] = {
    'Bambu Lab A1 mini': (0.0, 1.0),
    'Bambu Lab A1': (0.0, 1.0),
    'Bambu Lab A2L': (0.0, 1.0),
    'Bambu Lab P1P': _P1_X1_TOWER,
    'Bambu Lab P1S': _P1_X1_TOWER,
    'Bambu Lab X1': _P1_X1_TOWER,
    'Bambu Lab X1 Carbon': _P1_X1_TOWER,
    'Bambu Lab X1E': _P1_X1_TOWER,
    'Bambu Lab P2S': _P1_X1_TOWER,
    'Bambu Lab X2D': _P1_X1_TOWER,
    'Bambu Lab H2C': _P1_X1_TOWER,
    'Bambu Lab H2D': _P1_X1_TOWER,
    'Bambu Lab H2D Pro': _P1_X1_TOWER,
    'Bambu Lab H2S': _P1_X1_TOWER,
    'Bambu Lab H3C': (1.0, 0.0),
}

# Areas of the bed a printer keeps free, x0, y0, x1, y1 in mm (bed_exclude_area of the profiles): P1 and X1 wipe the
# nozzle front left. Bambu Studio warns of a part too close to it, there may be collisions
_WIPING_CORNER = [(0, 0, 18, 28)]
EXCLUDED_AREAS: dict[str, list[tuple[float, float, float, float]]] = {
    'Bambu Lab P1P': _WIPING_CORNER,
    'Bambu Lab P1S': _WIPING_CORNER,
    'Bambu Lab X1': _WIPING_CORNER,
    'Bambu Lab X1 Carbon': _WIPING_CORNER,
    'Bambu Lab X1E': _WIPING_CORNER,
}

@dataclasses.dataclass(frozen=True)
class BambuProfiles:
    """
    Bambu Studio's system profile names of a printer with its 0.4 mm nozzle, and its extruders as the printer profile
    has them (round 56, p690): per extruder nozzle_volume and nozzle_flush_dataset of its Standard nozzle and
    extruder_max_nozzle_count, the hotends it changes between, and handle_hotend_as_extruder. Round 57: per extruder
    the mm of the long retraction when cut Bambu Studio takes off the least purging volume for the printer's Bambu PLA
    Basic (Plater.cpp get_min_flush_volumes, see threeMf.minFlushVolume)
    """
    printer: str
    process: str
    filament: str
    nozzleVolumes: tuple[float, ...] = (107.0,)
    flushDatasets: tuple[int, ...] = (0,)
    hotends: tuple[int, ...] = (1,)
    hotendAsExtruder: bool = False
    cutRetractions: tuple[int, ...] = (18,)

    @property
    def extruders(self) -> int:
        """The entries of nozzle_diameter, Bambu Studio's purging volumes have a block of them each"""
        return len(self.nozzleVolumes)

# Round 55 (p680): the profiles the export's Bambu Studio project names, Bambu Studio takes their settings from its
# own system profiles. The printer profile's default_print_profile and default_filament_profile of Bambu Studio
# 02.09.01.70, the 0.4 mm nozzle only (decided 23.11.2026); tests/fixtures/bambu_system_profiles.json lists the names
# Bambu Studio has. A filament profile of another printer (Bambu PLA Basic @BBL X1C on a P1S) came in as a project
# profile in the Bambu Studio test of 23.11.2026
# Round 56 (p690): the extruders from Bambu Studio's printer profiles (sources of 02.09.01.70, profiles BBL
# 02.09.00.74), tests/fixtures/bambu_system_profiles.json lists them as machine_extruders. Defaults of BambuProfiles:
# one extruder of the P1 and X1. The H2C's right extruder changes between 6 hotends, the H3C's one between 9.
# Round 57 (spec dev-notes/specs/2026-11-23-r57-one-nozzle-flush.md): the long retraction when cut, the fixture has the
# profile values as machine_extruders' cut. The A1, P1 and X1 leave it to the filament, Bambu PLA Basic's is 18 mm;
# the X1E only takes the printer's, which is off; the H2C's printer profile has 14 mm on; it is off for the others
_ONE = dict(nozzleVolumes=(92.0,))
_TWO = dict(nozzleVolumes=(130.0, 145.0), flushDatasets=(1, 1), hotends=(1, 1), cutRetractions=(0, 0))
BAMBU_PROFILES: dict[str, BambuProfiles] = {
    'Bambu Lab A1 mini': BambuProfiles('Bambu Lab A1 mini 0.4 nozzle', '0.20mm Standard @BBL A1M', 'Bambu PLA Basic @BBL A1M', **_ONE),
    'Bambu Lab A1': BambuProfiles('Bambu Lab A1 0.4 nozzle', '0.20mm Standard @BBL A1', 'Bambu PLA Basic @BBL A1', **_ONE),
    'Bambu Lab A2L': BambuProfiles('Bambu Lab A2L 0.4 nozzle', '0.20mm Standard @BBL A2L', 'Bambu PLA Basic @BBL A2L 0.4 nozzle', **_ONE),
    'Bambu Lab P1P': BambuProfiles('Bambu Lab P1P 0.4 nozzle', '0.20mm Standard @BBL P1P', 'Bambu PLA Basic @BBL P1P'),
    'Bambu Lab P1S': BambuProfiles('Bambu Lab P1S 0.4 nozzle', '0.20mm Standard @BBL X1C', 'Bambu PLA Basic @BBL P1S 0.4 nozzle'),
    'Bambu Lab X1': BambuProfiles('Bambu Lab X1 0.4 nozzle', '0.20mm Standard @BBL X1C', 'Bambu PLA Basic @BBL X1'),
    'Bambu Lab X1 Carbon': BambuProfiles('Bambu Lab X1 Carbon 0.4 nozzle', '0.20mm Standard @BBL X1C', 'Bambu PLA Basic @BBL X1C'),
    'Bambu Lab X1E': BambuProfiles('Bambu Lab X1E 0.4 nozzle', '0.20mm Standard @BBL X1C', 'Bambu PLA Basic @BBL X1C', cutRetractions=(0,)),
    'Bambu Lab P2S': BambuProfiles('Bambu Lab P2S 0.4 nozzle', '0.20mm Standard @BBL P2S', 'Bambu PLA Basic @BBL P2S', nozzleVolumes=(110.0,), cutRetractions=(0,)),
    'Bambu Lab X2D': BambuProfiles('Bambu Lab X2D 0.4 nozzle', '0.20mm Standard @BBL X2D', 'Bambu PLA Basic @BBL X2D 0.4 nozzle', **{**_TWO, 'nozzleVolumes': (92.0, 92.0)}),
    'Bambu Lab H2C': BambuProfiles('Bambu Lab H2C 0.4 nozzle', '0.20mm Standard @BBL H2C', 'Bambu PLA Basic @BBL H2C', **{**_TWO, 'hotends': (1, 6), 'cutRetractions': (14, 14)}),
    'Bambu Lab H2D': BambuProfiles('Bambu Lab H2D 0.4 nozzle', '0.20mm Standard @BBL H2D', 'Bambu PLA Basic @BBL H2D', **_TWO),
    'Bambu Lab H2D Pro': BambuProfiles('Bambu Lab H2D Pro 0.4 nozzle', '0.20mm Standard @BBL H2DP', 'Bambu PLA Basic @BBL H2DP', **_TWO),
    'Bambu Lab H2S': BambuProfiles('Bambu Lab H2S 0.4 nozzle', '0.20mm Standard @BBL H2S', 'Bambu PLA Basic @BBL H2S', nozzleVolumes=(145.0,), flushDatasets=(1,), cutRetractions=(0,)),
    'Bambu Lab H3C': BambuProfiles('Bambu Lab H3C 0.4 nozzle', '0.20mm Standard @BBL H3C', 'Bambu PLA Basic @BBL H3C', nozzleVolumes=(125.9,), flushDatasets=(1,),
                                   hotends=(9,), hotendAsExtruder=True, cutRetractions=(0,)),
}

_NAMES = {presetLabel(name): name for name in PRINT_BED_SIZES}

def purgeAnchor(label: str) -> tuple[float, float]:
    """Where the slicer puts the purge tower on the bed of the dropdown's label, see PURGE_ANCHORS"""
    return PURGE_ANCHORS.get(_NAMES.get(label), DEFAULT_PURGE_ANCHOR)

def excludedAreas(label: str) -> list[tuple[float, float, float, float]]:
    """The areas the printer of the dropdown's label keeps free, mm, see EXCLUDED_AREAS"""
    return list(EXCLUDED_AREAS.get(_NAMES.get(label), []))

def bambuProfiles(label: str) -> BambuProfiles | None:
    """Bambu Studio's profile names of the dropdown's label, none for other printers and Custom"""
    return BAMBU_PROFILES.get(_NAMES.get(label))

def isBambu(label: str) -> bool:
    """
    Whether the export writes a Bambu Studio project for the dropdown's label, see BAMBU_PROFILES. Round 56 (p690):
    the printers with two extruders too, their project brings purging volumes, see threeMf.flushSettings (round 57:
    every Bambu printer's project does)
    """
    return bambuProfiles(label) is not None

# Round 55 (decided 23.11.2026: the printer chosen last is the default): the label of the printer dropdown the baseplate
# or export dialog was last run with, Custom too, shared by both. In the add-in's config folder, git ignores it
LAST_PRINTER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'commandConfig', 'lastPrinter.txt')

def readLastPrinter(path: str = LAST_PRINTER_PATH) -> str | None:
    """The printer chosen last as the list has it now, none when none is saved or it's gone from the list"""
    try:
        with open(path, encoding='utf-8') as file:
            label = currentLabel(file.read().strip())
    except (OSError, UnicodeError):
        return None
    return label if label == PRINT_BED_CUSTOM or label in PRINT_BED_PRESETS else None

def writeLastPrinter(label: str, path: str = LAST_PRINTER_PATH) -> bool:
    """Keeps the label as the printer chosen last, whether it could be"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as file:
            file.write(label)
        return True
    except OSError:
        return False
