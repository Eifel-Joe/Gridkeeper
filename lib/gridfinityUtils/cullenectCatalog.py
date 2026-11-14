"""
Catalog of the Cullenect symbols (https://github.com/CullenJWebb/Cullenect-Labels, MIT).

The symbols are svg files rendered once from Cullenect.scad by tools/cullenectIcons.py into
cullenectIcons/screws (one file per valid screw combination) and cullenectIcons/hardware. The building
block lists below are only what that tool renders; at runtime everything is read back from the folders,
so a new symbol is a new svg file and needs no code change. No Fusion imports, so it is testable.
"""

import itertools
import os
import re

# building blocks of the screw symbol, the names are the ones Cullenect.scad uses
HEADS = ['none', 'socket', 'countersunk', 'roundh', 'pan']
SHAFTS = ['machine', 'tapping']
THREADS = ['full', 'partial']
DRIVERS = ['none', 'slot', 'phillips', 'phillips_slot', 'phillips_square', 'torx', 'hex', 'square', 'triangle']

# the hardware symbols of Select_Hardware in Cullenect.scad (without "none")
CULLENECT_HARDWARE = [
    'washer', 'washer_locking', 'threaded_insert', 'nut', 'nut_square', 'nut_nylon', 'tnut_1', 'tnut_2', 'magnet',
    'crimp_ring_open', 'crimp_ring_closed', 'crimp_fork_open', 'crimp_fork_closed', 'crimp_spade_open',
    'crimp_spade_closed', 'crimp_receptacle_open', 'crimp_receptacle_closed', 'crimp_butt_splice',
]

# the folder of labelIcons/ a hardware symbol is copied to so it can be picked on normal bin labels too
HARDWARE_LABEL_ICON_TYPE = {
    key: ('washers' if key.startswith('washer') else
          'nuts' if key.startswith(('nut', 'tnut')) else
          'inserts' if key == 'threaded_insert' else
          'magnets' if key == 'magnet' else
          'crimps')
    for key in CULLENECT_HARDWARE
}

# names Cullenect.scad shows in its customizer, its lists are also the order of the choices
CULLENECT_NAMES = {
    'none': 'None', 'socket': 'Socket', 'countersunk': 'Countersunk', 'roundh': 'Round', 'pan': 'Pan',
    'machine': 'Machine', 'tapping': 'Tapping', 'full': 'Full', 'partial': 'Partial',
    'slot': 'Slot', 'phillips': 'Phillips', 'phillips_slot': 'Phillips Slot', 'phillips_square': 'Phillips Square',
    'torx': 'Torx/Star', 'hex': 'Hex', 'square': 'Robertson/Square', 'triangle': 'Triangle',
    'washer': 'Washer', 'washer_locking': 'Locking Washer', 'threaded_insert': 'Threaded Insert', 'nut': 'Nut',
    'nut_square': 'Square Nut', 'nut_nylon': 'Nylon Lock Nut', 'tnut_1': 'T-Nut Side', 'tnut_2': 'T-Nut Top',
    'magnet': 'Magnet', 'crimp_ring_open': 'Crimp Ring - Open', 'crimp_ring_closed': 'Crimp Ring - Closed',
    'crimp_fork_open': 'Crimp Fork - Open', 'crimp_fork_closed': 'Crimp Fork - Closed',
    'crimp_spade_open': 'Crimp Spade - Open', 'crimp_spade_closed': 'Crimp Spade - Closed',
    'crimp_receptacle_open': 'Crimp Receptacle - Open', 'crimp_receptacle_closed': 'Crimp Receptacle - Closed',
    'crimp_butt_splice': 'Crimp Butt Splice',
}

SCREWS_FOLDER = 'screws'
HARDWARE_FOLDER = 'hardware'

_SCREW_FILE = re.compile(r'^screw_([^_]+)_([^_]+)_([^_]+)_(.+)_(flange|noflange)_(sec|nosec)\.svg$')


def displayName(key: str) -> str:
    """The name Cullenect shows, roundh as Round, others from the key, dowel.svg as Dowel"""
    if key in CULLENECT_NAMES:
        return CULLENECT_NAMES[key]
    return key.replace('_', ' ').replace('-', ' ').capitalize()


def _inOrder(values, order: list) -> list:
    """Values in the given order, unknown ones after them sorted"""
    return sorted(values, key=lambda value: (order.index(value), '') if value in order else (len(order), str(value)))


def isValidScrew(head: str, shaft: str, threads: str, driver: str, flange: bool, security: bool) -> bool:
    """A flange needs a head that can carry it, a driver needs a head and a security pin needs a driver"""
    if head not in HEADS or shaft not in SHAFTS or threads not in THREADS or driver not in DRIVERS:
        return False
    if flange and head in ('countersunk', 'none'):
        return False
    if head == 'none' and driver != 'none':
        return False
    if security and driver == 'none':
        return False
    return True


def screwIconFileName(head: str, shaft: str, threads: str, driver: str, flange: bool, security: bool) -> str:
    return f"screw_{head}_{shaft}_{threads}_{driver}_{'flange' if flange else 'noflange'}_{'sec' if security else 'nosec'}.svg"


def allScrewCombinations() -> list[tuple]:
    """Every valid combination as (head, shaft, threads, driver, flange, security), the ones the tool renders"""
    return [combination for combination in itertools.product(HEADS, SHAFTS, THREADS, DRIVERS, (False, True), (False, True))
            if isValidScrew(*combination)]


def listHardwareIcons(folder: str) -> list[tuple[str, str]]:
    """(display name, path) of every svg in <folder>/hardware, Cullenect's in its order, new ones after them by name"""
    hardwareFolder = os.path.join(folder, HARDWARE_FOLDER)
    if not os.path.isdir(hardwareFolder):
        return []
    fileNames = [fileName for fileName in os.listdir(hardwareFolder) if fileName.lower().endswith('.svg')]
    order = [f'{key}.svg' for key in CULLENECT_HARDWARE]
    fileNames = _inOrder(fileNames, order)
    return [(displayName(os.path.splitext(fileName)[0]), os.path.join(hardwareFolder, fileName)) for fileName in fileNames]


def screwOptions(folder: str) -> dict[str, list]:
    """The values of each building block found in the file names of <folder>/screws, in Cullenect's order"""
    options = {'head': set(), 'shaft': set(), 'threads': set(), 'driver': set(), 'flange': set(), 'security': set()}
    screwsFolder = os.path.join(folder, SCREWS_FOLDER)
    fileNames = os.listdir(screwsFolder) if os.path.isdir(screwsFolder) else []
    for fileName in fileNames:
        match = _SCREW_FILE.match(fileName.lower())
        if match is None:
            continue
        (head, shaft, threads, driver, flange, security) = match.groups()
        options['head'].add(head)
        options['shaft'].add(shaft)
        options['threads'].add(threads)
        options['driver'].add(driver)
        options['flange'].add(flange == 'flange')
        options['security'].add(security == 'sec')
    orders = {'head': HEADS, 'shaft': SHAFTS, 'threads': THREADS, 'driver': DRIVERS, 'flange': [False, True], 'security': [False, True]}
    return {name: _inOrder(values, orders[name]) for name, values in options.items()}


def screwIconPath(folder: str, head: str, shaft: str, threads: str, driver: str, flange: bool, security: bool) -> str | None:
    """None when there is no file for this combination, the dialog locks such a choice"""
    path = os.path.join(folder, SCREWS_FOLDER, screwIconFileName(head, shaft, threads, driver, flange, security))
    return path if os.path.isfile(path) else None


# length units of svg width and height in mm, a number without unit is in user units, CSS pixels of 1/96 in
_SVG_UNITS = {'mm': 1.0, 'cm': 10.0, 'in': 25.4, 'pt': 25.4 / 72, 'pc': 25.4 / 6, 'px': 25.4 / 96, '': 25.4 / 96}


def svgSize(path: str) -> tuple[float, float]:
    """Width and height in mm of an svg, from width and height with their units, else from the view box. A view box
    alone is taken as mm, the way OpenSCAD and the symbols of this repository write it"""
    with open(path, 'r', encoding='utf-8') as file:
        text = file.read(262144)
    tag = re.search(r'<svg\b[^>]*>', text, re.DOTALL)
    if tag is None:
        raise ValueError(f'No svg element in {path}')
    attributes = {name: value1 or value2 for name, value1, value2 in re.findall(r'''([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')''', tag.group(0))}
    number = r'^\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*(mm|cm|in|pt|pc|px|)\s*$'
    width, height = (re.match(number, attributes.get(name, '')) for name in ('width', 'height'))
    if width and height:
        return tuple(float(match.group(1)) * _SVG_UNITS[match.group(2)] for match in (width, height))
    viewBox = attributes.get('viewBox', '').replace(',', ' ').split()
    if len(viewBox) == 4:
        return (float(viewBox[2]), float(viewBox[3]))
    raise ValueError(f'No size in {path}')
