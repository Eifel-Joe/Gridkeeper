"""
Tests for lib/gridfinityUtils/svgSymbol.py: reading the symbol svgs (lines, circular arcs, cubic splines), their
outline and point count, and where Sketch.importSVG puts them (round 40, p371)
"""

import glob
import os
import importlib.util

from pytest import approx

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = os.path.join(PROJECT_ROOT, 'lib', 'gridfinityUtils')


def _load():
    path = os.path.join(ICONS, 'svgSymbol.py')
    spec = importlib.util.spec_from_file_location('svgSymbol', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


svgSymbol = _load()

# the probe imported in Fusion (18.11.2026): a triangle and a half circle, 6 sketch points besides the origin
TRIANGLE_AND_ARC = 'M 2,1 L 12,1 L 2,4 z M 14,-3 A 2,2 0 0 1 18,-3 L 14,-3 z'


def _write(tmp_path, d):
    path = tmp_path / 'symbol.svg'
    path.write_text(f'<svg width="20mm" height="10mm" viewBox="0 -5 20 10" xmlns="http://www.w3.org/2000/svg"><path d="{d}"/></svg>')
    return str(path)


def test_parse_polygon_and_arcs():
    loops = svgSymbol.parsePath(TRIANGLE_AND_ARC)
    assert [len(loop) for loop in loops] == [3, 2]
    assert [segment[0] for segment in loops[1]] == ['arc', 'line']
    assert loops[1][0][1:] == ((14, -3), (18, -3), 2, 2, 0, False, True)


def test_parse_numbers_without_spaces_and_closing_line():
    loops = svgSymbol.parsePath('M95.00,50.00 L72.50,88.97 L5.00,50.00 Z')
    assert [segment[0] for segment in loops[0]] == ['line', 'line', 'line']
    assert loops[0][-1][2] == (95, 50)


def test_parse_cubic_and_exponent():
    loops = svgSymbol.parsePath('M 0,0 C 1,2 3,2 4,0 L 1e-1,-2e0 z')
    assert loops[0][0] == ('cubic', (0, 0), (1, 2), (3, 2), (4, 0))
    assert loops[0][1][2] == (0.1, -2)


def test_point_count_matches_fusion(tmp_path):
    # measured in Fusion: the probe 6, hex-nut.svg 10 (six corners, a circle of two half arcs with a centre each)
    assert svgSymbol.readSymbol(_write(tmp_path, TRIANGLE_AND_ARC)).pointCount == 6
    assert svgSymbol.readSymbol(os.path.join(ICONS, 'labelIcons', 'nuts', 'hex-nut.svg')).pointCount == 10


def test_arc_bounds_include_bulge():
    assert svgSymbol.segmentBounds(('arc', (14, -3), (18, -3), 2, 2, 0, False, True)) == approx((14, -5, 18, -3))
    assert svgSymbol.segmentBounds(('arc', (14, -3), (18, -3), 2, 2, 0, False, False)) == approx((14, -3, 18, -1))


def test_arc_radius_too_small_is_scaled_up():
    # svg rule: a radius too small for the endpoints is scaled up to a half circle
    assert svgSymbol.segmentBounds(('arc', (0, 0), (4, 0), 1, 1, 0, False, True)) == approx((0, -2, 4, 0))


def test_cubic_bounds_at_extremum():
    assert svgSymbol.segmentBounds(('cubic', (0, 0), (1, 2), (3, 2), (4, 0))) == approx((0, 0, 4, 1.5))


def test_hex_nut_bounds_and_aspect():
    symbol = svgSymbol.readSymbol(os.path.join(ICONS, 'labelIcons', 'nuts', 'hex-nut.svg'))
    assert symbol.bounds == approx((5, 11.03, 95, 88.97))
    assert symbol.aspect == approx(90 / 77.94)


def test_import_arguments_place_bottom_left():
    (x, y, scale) = svgSymbol.importArguments((-11.56, -5, 3, 5), 2.0, 1.0, 0.8)
    unit = svgSymbol.SVG_UNIT_CM * scale
    # sketch point = (x, -y) * unit + (x, y), measured in Fusion
    assert -11.56 * unit + x == approx(2.0)
    assert -5 * unit + y == approx(1.0)
    assert 5 * unit + y == approx(1.8)
    assert 10 * unit == approx(0.8)


def test_reads_every_symbol_file():
    paths = glob.glob(os.path.join(ICONS, 'cullenectIcons', '**', '*.svg'), recursive=True) \
        + glob.glob(os.path.join(ICONS, 'labelIcons', '**', '*.svg'), recursive=True)
    assert len(paths) > 500
    for path in paths:
        symbol = svgSymbol.readSymbol(path)
        assert len(symbol.loops) > 0, path
        for loop in symbol.loops:
            assert loop[0][1] == svgSymbol.segmentEnd(loop[-1]), path
            for (segment, following) in zip(loop, loop[1:]):
                assert svgSymbol.segmentEnd(segment) == following[1], path
        assert symbol.bounds[2] > symbol.bounds[0] and symbol.bounds[3] > symbol.bounds[1], path


def test_unsupported_commands_are_refused():
    for d in ('M 0,0 H 4 V 2 z', 'm 0,0 l 4,0 l 0,2 z', 'M 0,0 Q 1,1 2,0 z'):
        try:
            svgSymbol.parsePath(d)
        except ValueError:
            continue
        raise AssertionError(f'{d} was read')


def test_other_drawing_elements_are_refused(tmp_path):
    # a symbol dropped in by hand may draw with circles or transforms, its outline isn't in its paths alone
    for body in ('<path d="M 0,0 L 4,0 L 0,2 z"/><circle cx="1" cy="1" r="3"/>',
                 '<g transform="scale(2)"><path d="M 0,0 L 4,0 L 0,2 z"/></g>'):
        path = tmp_path / 'hand.svg'
        path.write_text(f'<svg viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg">{body}</svg>')
        try:
            svgSymbol.readSymbol(str(path))
        except ValueError:
            continue
        raise AssertionError(body)
