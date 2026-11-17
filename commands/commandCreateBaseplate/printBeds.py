PRINT_BED_CUSTOM = 'Custom'

# usable bed size X, Y in mm
PRINT_BED_SIZES: dict[str, tuple[float, float]] = {
    # Bambu Lab apart (round r29-export, click test 17.11.2026): the export keeps their purge tower's spot free, see
    # BAMBU_PURGE_ANCHORS. From Bambu Studio 02.09.01.70's printer profiles, printable_area
    'Bambu Lab A1 mini': (180, 180),
    'Bambu Lab A1': (256, 256),
    'Bambu Lab A2L': (330, 320),
    'Bambu Lab P1P, P1S, X1, X1C, X1E': (256, 256),
    'Bambu Lab P2S, X2D': (256, 256),
    'Bambu Lab H2C': (330, 320),
    'Bambu Lab H2D, H2D Pro': (350, 320),
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
BAMBU_PURGE_ANCHORS: dict[str, tuple[float, float]] = {
    'Bambu Lab A1 mini': (0.0, 1.0),
    'Bambu Lab A1': (0.0, 1.0),
    'Bambu Lab A2L': (0.0, 1.0),
    'Bambu Lab P1P, P1S, X1, X1C, X1E': (0.644, 0.977),
    'Bambu Lab P2S, X2D': (0.644, 0.977),
    'Bambu Lab H2C': (0.644, 0.977),
    'Bambu Lab H2D, H2D Pro': (0.644, 0.977),
    'Bambu Lab H2S': (0.644, 0.977),
    'Bambu Lab H3C': (1.0, 0.0),
}

_NAMES = {presetLabel(name): name for name in PRINT_BED_SIZES}

def purgeAnchor(label: str) -> tuple[float, float]:
    """Where the slicer puts the purge tower on the bed of the dropdown's label, see BAMBU_PURGE_ANCHORS"""
    return BAMBU_PURGE_ANCHORS.get(_NAMES.get(label), DEFAULT_PURGE_ANCHOR)
