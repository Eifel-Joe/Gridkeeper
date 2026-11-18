"""
Every label symbol file after round 40 (p371): lines, circular arcs and splines instead of polygons of thousands of
points, its outline and the area of each closed path as the polygons it was rebuilt from had them
(symbol-check.json, written by dev-notes/tools/arcSymbols.py), and the tools that render symbols rebuild them too.
"""

import glob
import json
import os
import importlib.util

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = os.path.join(ROOT, 'lib', 'gridfinityUtils')
FOLDERS = sorted({os.path.dirname(path) for pattern in ('cullenectIcons/**/*.svg', 'labelIcons/**/*.svg')
                  for path in glob.glob(os.path.join(ICONS, pattern), recursive=True)})
TOLERANCE = 0.01
MAX_SEGMENTS = 150


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


arcSymbols = _load(os.path.join(ROOT, 'dev-notes', 'tools', 'arcSymbols.py'), 'arcSymbols')
svgSymbol = arcSymbols.svgSymbol


def test_symbol_folders_are_found():
    names = [os.path.relpath(folder, ICONS).replace(os.sep, '/') for folder in FOLDERS]
    assert {'cullenectIcons/screws', 'cullenectIcons/hardware', 'cullenectIcons/setscrews', 'labelIcons/nuts'} <= set(names)


@pytest.mark.parametrize('folder', FOLDERS, ids=lambda folder: os.path.relpath(folder, ICONS).replace(os.sep, '/'))
def test_symbols_are_few_segments_and_match_their_polygons(folder):
    with open(os.path.join(folder, arcSymbols.CHECK_FILE), encoding='utf-8') as file:
        check = json.load(file)
    names = sorted(name for name in os.listdir(folder) if name.lower().endswith('.svg'))
    assert sorted(check) == names
    for name in names:
        symbol = svgSymbol.readSymbol(os.path.join(folder, name))
        segments = sum(len(loop) for loop in symbol.loops)
        assert segments <= MAX_SEGMENTS, f'{name}: {segments} segments'
        entry = check[name]
        assert symbol.bounds == pytest.approx(entry['bounds'], abs=TOLERANCE), name
        assert len(symbol.loops) == len(entry['areas']), name
        for (loop, area) in zip(symbol.loops, entry['areas']):
            assert abs(abs(arcSymbols.loopArea(loop)) - abs(area)) <= arcSymbols._perimeter(loop) * TOLERANCE + 1e-9, name


def test_the_torx_symbol_is_arcs():
    symbol = svgSymbol.readSymbol(os.path.join(ICONS, 'cullenectIcons', 'screws', 'screw_countersunk_machine_full_torx_noflange_nosec.svg'))
    kinds = [segment[0] for loop in symbol.loops for segment in loop]
    assert kinds.count('arc') >= 10
    assert len(kinds) <= 60


@pytest.mark.parametrize('tool, call', [('cullenectIcons.py', 'convertFolder('), ('labelIcons.py', 'convertFolder('),
                                        ('setScrewIcons.py', 'cullenectIcons.rebuildSymbols(')])
def test_render_tools_rebuild_their_symbols(tool, call):
    with open(os.path.join(ROOT, 'tools', tool), encoding='utf-8') as file:
        assert call in file.read()


def test_previews_read_splines_and_lowercase_close():
    labelIcons = _load(os.path.join(ROOT, 'tools', 'labelIcons.py'), 'labelIconsTool')
    loops = labelIcons.pathLoops('M 0,0 L 4,0 C 4,2 0,2 0,0 z M 10,10 L 12,10 L 10,12 z')
    assert len(loops) == 2
    assert len(loops[0]) > 4
    assert max(y for (_, y) in loops[0]) == pytest.approx(1.5, abs=0.05)
