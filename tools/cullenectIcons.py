r"""
Renders the Cullenect symbols to svg with OpenSCAD, once, so the add-in needs no OpenSCAD at runtime.

    python3 tools/cullenectIcons.py --openscad "C:/Program Files/OpenSCAD/openscad.exe"

Every valid screw combination goes to lib/gridfinityUtils/cullenectIcons/screws and every hardware symbol
to .../hardware, named as lib/gridfinityUtils/cullenectCatalog.py expects. The geometry is the one of
tools/cullenect/Cullenect.scad (CullenJWebb/Cullenect-Labels, MIT, see tools/cullenect/LICENSE): a
wrapper per symbol loads its modules and projects them to 2D, composed like fastener() in
cullenect_label_generate. Existing svgs are kept unless --force is given.
"""

import argparse
import concurrent.futures
import importlib.util
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

TOOLS_FOLDER = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TOOLS_FOLDER)
CULLENECT_FOLDER = os.path.join(TOOLS_FOLDER, 'cullenect')
ICONS_FOLDER = os.path.join(PROJECT_ROOT, 'lib', 'gridfinityUtils', 'cullenectIcons')
LABEL_ICONS_FOLDER = os.path.join(PROJECT_ROOT, 'lib', 'gridfinityUtils', 'labelIcons')

# Set at the top of the wrapper for the screws. It doesn't reach into Cullenect's modules, whose own top level
# ($fa = 1, $fs = 0.01) wins there (found in round 17): the screws are drawn as fine as in the original. They keep their
# files (Hauptsitzung 15.11.2026), so this line stays as it was
SCREW_RESOLUTION = '$fa = 3; $fs = 0.1;'
# Round 17, p51: a hardware symbol of a thousand points took 15 s to import into an insert, a sketch point costs time.
# Passed to the module call, which overrides Cullenect's own setting inside it: coarser circles, the contour within
# MAX_DEVIATION of the fine one, which a 0.4 mm nozzle doesn't show (15.11.2026), checked with --compare
HARDWARE_RESOLUTION = '$fa = 12, $fs = 0.2'
MAX_DEVIATION = 0.05


def _loadCatalog():
    path = os.path.join(PROJECT_ROOT, 'lib', 'gridfinityUtils', 'cullenectCatalog.py')
    spec = importlib.util.spec_from_file_location('cullenectCatalog', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


catalog = _loadCatalog()


def wrapperScad(kind: str, combination) -> str:
    """The .scad text rendering one symbol: kind 'screw' with (head, shaft, threads, driver, flange, security)
    or kind 'hardware' with the Cullenect key"""
    lines = ['use <Cullenect.scad>'] + ([SCREW_RESOLUTION] if kind == 'screw' else [])
    if kind == 'screw':
        (head, shaft, threads, driver, flange, security) = combination
        lines += [
            'projection(cut = false) union() {',
            '    difference() {',
            f'        cullenect_head(head="{head}", flange={"true" if flange else "false"});',
            f'        cullenect_driver(driver="{driver}");',
            '    }',
            f'    cullenect_shaft(shaft="{shaft}", threads="{threads}");',
        ]
        if security:
            lines.append('    cullenect_driver(driver="security");')
        lines.append('}')
    elif kind == 'hardware':
        lines += ['projection(cut = false) {', f'    cullenect_hardware("{combination}", {HARDWARE_RESOLUTION});', '}']
    else:
        raise ValueError(f'Unknown symbol kind {kind}')
    return '\n'.join(lines) + '\n'


def openscadCommand(exe: str, scadPath: str, svgPath: str) -> list[str]:
    return [exe, '-o', svgPath, scadPath]


def renderJobs(iconsFolder: str) -> list[tuple[str, object, str]]:
    """(kind, combination, svg path) for every symbol"""
    jobs = [('screw', combination, os.path.join(iconsFolder, catalog.SCREWS_FOLDER, catalog.screwIconFileName(*combination)))
            for combination in catalog.allScrewCombinations()]
    jobs += [('hardware', key, os.path.join(iconsFolder, catalog.HARDWARE_FOLDER, f'{key}.svg')) for key in catalog.CULLENECT_HARDWARE]
    return jobs


def tightenSvg(svg: str) -> str:
    """OpenSCAD pads the view box of its svg to whole millimeters, which hides the real size of the symbol.
    The width, height and view box are set to the bounding box of the path points instead."""
    points = [(float(x), float(y)) for x, y in re.findall(r'[ML]\s*(-?[\d.]+(?:e-?\d+)?),(-?[\d.]+(?:e-?\d+)?)', svg)]
    if not points:
        raise ValueError('The svg has no path points')
    (minX, maxX) = (min(x for x, _ in points), max(x for x, _ in points))
    (minY, maxY) = (min(y for _, y in points), max(y for _, y in points))
    (width, height) = (maxX - minX, maxY - minY)
    number = lambda value: f'{value:.5f}'.rstrip('0').rstrip('.')
    header = f'<svg width="{number(width)}mm" height="{number(height)}mm" viewBox="{number(minX)} {number(minY)} {number(width)} {number(height)}"'
    (tight, count) = re.subn(r'<svg width="[^"]*" height="[^"]*" viewBox="[^"]*"', lambda _: header, svg, count=1)
    if count != 1:
        raise ValueError('The svg header is not the one OpenSCAD writes')
    return tight


_POINT = r'(-?[\d.]+(?:e-?\d+)?),(-?[\d.]+(?:e-?\d+)?)'


def svgSegments(svg: str) -> list[tuple[float, float, float, float]]:
    """The straight segments of the path loops OpenSCAD writes (M x,y L x,y ... z), each loop closed"""
    segments = []
    for loop in re.findall(r'M[^Mz]*z', svg):
        points = [(float(x), float(y)) for (x, y) in re.findall(_POINT, loop)]
        segments += [(*a, *b) for (a, b) in zip(points, points[1:] + points[:1]) if a != b]
    return segments


def _pointToSegment(x: float, y: float, segment: tuple[float, float, float, float]) -> float:
    (x1, y1, x2, y2) = segment
    (dx, dy) = (x2 - x1, y2 - y1)
    lengthSquared = dx * dx + dy * dy
    t = 0 if lengthSquared == 0 else max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / lengthSquared))
    return math.hypot(x - x1 - t * dx, y - y1 - t * dy)


def _oneWay(a, b) -> float:
    """Largest distance of a point of contour a to contour b"""
    return max(min(_pointToSegment(x, y, segment) for segment in b) for (x, y, _, _) in a)


def contourDeviation(a, b) -> float:
    """How far two contours of segments are apart at most, from the points of either to the other"""
    return max(_oneWay(a, b), _oneWay(b, a))


def compare(oldFolder: str, newFolder: str) -> list[tuple[str, int, int, float]]:
    """(name, old points, new points, deviation in mm) of each hardware symbol in both folders"""
    rows = []
    for key in catalog.CULLENECT_HARDWARE:
        paths = [os.path.join(folder, catalog.HARDWARE_FOLDER, f'{key}.svg') for folder in (oldFolder, newFolder)]
        if not all(os.path.isfile(path) for path in paths):
            continue
        (old, new) = [svgSegments(open(path, encoding='utf-8').read()) for path in paths]
        rows.append((key, len(old), len(new), contourDeviation(old, new)))
    return rows


def labelIconPath(key: str, labelIconsFolder: str) -> str:
    """Where the hardware symbol is copied to so bin labels can pick it too: labelIcons/<type>/cullenect-<key>.svg.
    The prefix keeps it apart from the icons of tools/labelIcons.py (washer.svg) and shows in the dropdown"""
    return os.path.join(labelIconsFolder, catalog.HARDWARE_LABEL_ICON_TYPE[key], f"cullenect-{key.replace('_', '-')}.svg")


def copyHardwareToLabelIcons(iconsFolder: str, labelIconsFolder: str) -> list[str]:
    """Copies every rendered hardware svg to the label icons, returns the new paths"""
    copied = []
    for key in catalog.CULLENECT_HARDWARE:
        source = os.path.join(iconsFolder, catalog.HARDWARE_FOLDER, f'{key}.svg')
        if not os.path.isfile(source):
            continue
        target = labelIconPath(key, labelIconsFolder)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(source, target)
        copied.append(target)
    return copied


def render(exe: str, job: tuple[str, object, str], workFolder: str) -> str | None:
    """Renders one symbol, returns an error text or None"""
    try:
        return _render(exe, job, workFolder)
    except Exception as err:
        return f'{os.path.basename(job[2])}: {err!r}'


def _render(exe: str, job: tuple[str, object, str], workFolder: str) -> str | None:
    (kind, combination, svgPath) = job
    return renderScad(exe, wrapperScad(kind, combination), svgPath, workFolder, CULLENECT_FOLDER)


def renderScad(exe: str, scad: str, svgPath: str, workFolder: str, libraryFolder: str) -> str | None:
    """Renders the .scad text to the tightened svg, its `use` found in the library folder, returns an error text or None"""
    os.makedirs(os.path.dirname(svgPath), exist_ok=True)
    scadPath = os.path.join(workFolder, os.path.splitext(os.path.basename(svgPath))[0] + '.scad')
    with open(scadPath, 'w', encoding='utf-8') as file:
        file.write(scad)
    environment = dict(os.environ, OPENSCADPATH=libraryFolder)
    partial = os.path.join(workFolder, os.path.basename(svgPath))  # in the work folder, a stop leaves nothing in the repo
    result = subprocess.run(openscadCommand(exe, scadPath, partial), capture_output=True, text=True, errors='replace', env=environment)
    if result.returncode != 0 or not os.path.isfile(partial):
        return f'{os.path.basename(svgPath)}: {result.stderr.strip()[-300:]}'
    with open(partial, 'r', encoding='utf-8') as file:
        svg = file.read()
    os.remove(partial)
    with open(svgPath, 'w', encoding='utf-8', newline='\n') as file:
        file.write(tightenSvg(svg))
    return None


def _loadArcSymbols():
    path = os.path.join(PROJECT_ROOT, 'dev-notes', 'tools', 'arcSymbols.py')
    spec = importlib.util.spec_from_file_location('arcSymbols', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rebuildSymbols(folders: list[str]):
    """Rebuilds the polygons of the rendered svgs in the folders as lines, arcs and splines, see
    dev-notes/tools/arcSymbols.py; a file that fails its check stays a polygon and is named"""
    arcSymbols = _loadArcSymbols()
    for folder in folders:
        if os.path.isdir(folder):
            for report in arcSymbols.convertFolder(folder):
                if report.error:
                    print(f'{report.name}: left as a polygon, {report.error}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('--openscad', help='path of openscad.exe, needed to render')
    parser.add_argument('--out', default=ICONS_FOLDER, help='folder with screws/ and hardware/')
    parser.add_argument('--jobs', type=int, default=max(1, (os.cpu_count() or 2) - 1))
    parser.add_argument('--force', action='store_true', help='render svgs that exist already')
    parser.add_argument('--only', choices=['screw', 'hardware'], help='render only symbols of this kind')
    parser.add_argument('--compare', metavar='OLD_FOLDER', help='only compare the hardware symbols of --out with the ones in OLD_FOLDER')
    args = parser.parse_args()
    if args.compare:
        rows = compare(args.compare, args.out)
        for (key, oldCount, newCount, deviation) in rows:
            print(f'{key}: {oldCount} -> {newCount} segments, deviation {deviation:.4f} mm')
        missing = [key for key in catalog.CULLENECT_HARDWARE if key not in [row[0] for row in rows]]
        if missing:
            # a wrong folder skips every symbol, that is no pass
            print(f'not compared, missing in either folder: {", ".join(missing)}')
            return 1
        worst = max(row[3] for row in rows)
        print(f'largest deviation {worst:.4f} mm, allowed {MAX_DEVIATION} mm')
        return 0 if worst <= MAX_DEVIATION + 1e-9 else 1
    if not args.openscad:
        parser.error('--openscad is needed to render')
    jobs = [job for job in renderJobs(args.out) if (args.force or not os.path.isfile(job[2])) and args.only in (None, job[0])]
    print(f'{len(jobs)} symbols to render with {args.jobs} jobs')
    started = time.time()
    errors = []
    with tempfile.TemporaryDirectory() as workFolder, concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        for index, error in enumerate(pool.map(lambda job: render(args.openscad, job, workFolder), jobs), 1):
            if error:
                errors.append(error)
            if index % 50 == 0:
                print(f'{index}/{len(jobs)} after {time.time() - started:.0f} s', flush=True)
    # the polygons OpenSCAD writes as lines and arcs, as the add-in imports them quickly (round 40)
    rebuildSymbols([os.path.join(args.out, folder) for folder in (catalog.SCREWS_FOLDER, catalog.HARDWARE_FOLDER)])
    copied = copyHardwareToLabelIcons(args.out, LABEL_ICONS_FOLDER) if os.path.abspath(args.out) == os.path.abspath(ICONS_FOLDER) else []
    print(f'{len(copied)} hardware svgs copied to the label icons, run tools/labelIcons.py for their previews')
    print(f'done in {time.time() - started:.0f} s, {len(jobs) - len(errors)} rendered, {len(errors)} failed')
    for error in errors:
        print('FAILED', error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
