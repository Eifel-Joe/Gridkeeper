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

SCREWS_FOLDER = 'screws'
HARDWARE_FOLDER = 'hardware'

_SCREW_FILE = re.compile(r'^screw_([^_]+)_([^_]+)_([^_]+)_(.+)_(flange|noflange)_(sec|nosec)\.svg$')


def displayName(key: str) -> str:
    """phillips_slot shows as Phillips slot, dowel.svg as Dowel"""
    return key.replace('_', ' ').replace('-', ' ').capitalize()


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
    """(display name, path) of every svg in <folder>/hardware, sorted by file name"""
    hardwareFolder = os.path.join(folder, HARDWARE_FOLDER)
    if not os.path.isdir(hardwareFolder):
        return []
    fileNames = sorted(fileName for fileName in os.listdir(hardwareFolder) if fileName.lower().endswith('.svg'))
    return [(displayName(os.path.splitext(fileName)[0]), os.path.join(hardwareFolder, fileName)) for fileName in fileNames]


def screwOptions(folder: str) -> dict[str, list]:
    """The values of each building block found in the file names of <folder>/screws, sorted"""
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
    return {name: sorted(values) for name, values in options.items()}


def screwIconPath(folder: str, head: str, shaft: str, threads: str, driver: str, flange: bool, security: bool) -> str | None:
    """None when there is no file for this combination, the dialog locks such a choice"""
    path = os.path.join(folder, SCREWS_FOLDER, screwIconFileName(head, shaft, threads, driver, flange, security))
    return path if os.path.isfile(path) else None


def svgSize(path: str) -> tuple[float, float]:
    """Width and height in mm of an svg, from width and height, else from the view box"""
    with open(path, 'r', encoding='utf-8') as file:
        text = file.read(4096)
    tag = re.search(r'<svg\b[^>]*>', text, re.DOTALL)
    if tag is None:
        raise ValueError(f'No svg element in {path}')
    attributes = dict(re.findall(r'([\w:-]+)\s*=\s*"([^"]*)"', tag.group(0)))
    number = r'^\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*(mm)?\s*$'
    width, height = (re.match(number, attributes.get(name, '')) for name in ('width', 'height'))
    if width and height:
        return (float(width.group(1)), float(height.group(1)))
    viewBox = attributes.get('viewBox', '').replace(',', ' ').split()
    if len(viewBox) == 4:
        return (float(viewBox[2]), float(viewBox[3]))
    raise ValueError(f'No size in {path}')
