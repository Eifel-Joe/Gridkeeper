r"""
Renders the set screw symbols of this fork to svg with OpenSCAD, once, so the add-in needs no OpenSCAD at runtime.

    python3 tools/setScrewIcons.py --openscad "C:/Program Files/OpenSCAD/openscad.exe"

Every set screw of lib/gridfinityUtils/cullenectCatalog.setScrewCombinations goes to
lib/gridfinityUtils/cullenectIcons/setscrews, named like the Cullenect screws. The geometry is
tools/setscrew/SetScrew.scad (own work, MIT), which uses the thread and driver shapes of
tools/cullenect/Cullenect.scad (CullenJWebb, MIT). Existing svgs are kept unless --force is given.
"""

import argparse
import concurrent.futures
import importlib.util
import os
import sys
import tempfile
import time

TOOLS_FOLDER = os.path.dirname(os.path.abspath(__file__))
SETSCREW_FOLDER = os.path.join(TOOLS_FOLDER, 'setscrew')


def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# the rendering, the svg tightening and the catalog are the ones of the Cullenect symbols
cullenectIcons = _load('cullenectIcons', os.path.join(TOOLS_FOLDER, 'cullenectIcons.py'))
catalog = cullenectIcons.catalog


def wrapperScad(combination) -> str:
    """The .scad text rendering one set screw, combination as (head, shaft, threads, driver, flange, security)"""
    if not catalog.isSetScrew(*combination):
        raise ValueError(f'{combination} is not a set screw')
    (_, shaft, _, driver, _, security) = combination
    return '\n'.join([
        'use <SetScrew.scad>',
        cullenectIcons.SCREW_RESOLUTION,
        'projection(cut = false) {',
        f'    set_screw(shaft="{shaft}", driver="{driver}", security={"true" if security else "false"});',
        '}',
    ]) + '\n'


def renderJobs(iconsFolder: str) -> list[tuple[tuple, str]]:
    """(combination, svg path) for every set screw"""
    return [(combination, os.path.join(iconsFolder, catalog.SETSCREWS_FOLDER, catalog.screwIconFileName(*combination)))
            for combination in catalog.setScrewCombinations()]


def render(exe: str, job: tuple[tuple, str], workFolder: str) -> str | None:
    """Renders one symbol, returns an error text or None"""
    (combination, svgPath) = job
    try:
        return cullenectIcons.renderScad(exe, wrapperScad(combination), svgPath, workFolder, SETSCREW_FOLDER)
    except Exception as err:
        return f'{os.path.basename(svgPath)}: {err!r}'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('--openscad', required=True, help='path of openscad.exe')
    parser.add_argument('--out', default=cullenectIcons.ICONS_FOLDER, help='folder with setscrews/')
    parser.add_argument('--jobs', type=int, default=max(1, (os.cpu_count() or 2) - 1))
    parser.add_argument('--force', action='store_true', help='render svgs that exist already')
    args = parser.parse_args()
    jobs = [job for job in renderJobs(args.out) if args.force or not os.path.isfile(job[1])]
    print(f'{len(jobs)} symbols to render with {args.jobs} jobs')
    started = time.time()
    with tempfile.TemporaryDirectory() as workFolder, concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        errors = [error for error in pool.map(lambda job: render(args.openscad, job, workFolder), jobs) if error]
    print(f'done in {time.time() - started:.0f} s, {len(jobs) - len(errors)} rendered, {len(errors)} failed')
    for error in errors:
        print('FAILED', error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
