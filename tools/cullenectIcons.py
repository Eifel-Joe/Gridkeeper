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

# Cullenect.scad sets $fs and $fa in its own top level, which `use` does not run: coarser than the
# 0.01 mm of the original, a symbol is only about 15 mm wide
RESOLUTION = '$fa = 3; $fs = 0.1;'


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
    lines = ['use <Cullenect.scad>', RESOLUTION]
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
        lines += ['projection(cut = false) {', f'    cullenect_hardware("{combination}");', '}']
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
    return re.sub(r'<svg width="[^"]*" height="[^"]*" viewBox="[^"]*"', lambda _: header, svg, count=1)


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
    (kind, combination, svgPath) = job
    os.makedirs(os.path.dirname(svgPath), exist_ok=True)
    scadPath = os.path.join(workFolder, os.path.splitext(os.path.basename(svgPath))[0] + '.scad')
    with open(scadPath, 'w', encoding='utf-8') as file:
        file.write(wrapperScad(kind, combination))
    environment = dict(os.environ, OPENSCADPATH=CULLENECT_FOLDER)
    partial = os.path.splitext(svgPath)[0] + '.partial.svg'  # OpenSCAD picks the format by extension
    result = subprocess.run(openscadCommand(exe, scadPath, partial), capture_output=True, text=True, env=environment)
    if result.returncode != 0 or not os.path.isfile(partial):
        return f'{os.path.basename(svgPath)}: {result.stderr.strip()[-300:]}'
    with open(partial, 'r', encoding='utf-8') as file:
        svg = file.read()
    os.remove(partial)
    with open(svgPath, 'w', encoding='utf-8', newline='\n') as file:
        file.write(tightenSvg(svg))
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('--openscad', required=True, help='path of openscad.exe')
    parser.add_argument('--out', default=ICONS_FOLDER, help='folder with screws/ and hardware/')
    parser.add_argument('--jobs', type=int, default=max(1, (os.cpu_count() or 2) - 1))
    parser.add_argument('--force', action='store_true', help='render svgs that exist already')
    args = parser.parse_args()
    jobs = [job for job in renderJobs(args.out) if args.force or not os.path.isfile(job[2])]
    print(f'{len(jobs)} symbols to render with {args.jobs} jobs')
    started = time.time()
    errors = []
    with tempfile.TemporaryDirectory() as workFolder, concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        for index, error in enumerate(pool.map(lambda job: render(args.openscad, job, workFolder), jobs), 1):
            if error:
                errors.append(error)
            if index % 50 == 0:
                print(f'{index}/{len(jobs)} after {time.time() - started:.0f} s', flush=True)
    copied = copyHardwareToLabelIcons(args.out, LABEL_ICONS_FOLDER) if args.out == ICONS_FOLDER else []
    print(f'{len(copied)} hardware svgs copied to the label icons, run tools/labelIcons.py for their previews')
    print(f'done in {time.time() - started:.0f} s, {len(jobs) - len(errors)} rendered, {len(errors)} failed')
    for error in errors:
        print('FAILED', error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
