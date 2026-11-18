"""
Tests for dev-notes/tools/arcSymbols.py, the tool that rebuilds the polygons of the symbol svgs as lines, circular
arcs and cubic splines within a tolerance (round 40, p371). Fixtures: two screw symbols as OpenSCAD rendered them
(Cullenect-Labels by CullenJWebb, MIT License, see lib/gridfinityUtils/cullenectIcons/README.md)
"""

import json
import math
import os
import shutil
import importlib.util

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(PROJECT_ROOT, 'tests', 'fixtures', 'symbols')
TOLERANCE = 0.01


def _load():
    path = os.path.join(PROJECT_ROOT, 'dev-notes', 'tools', 'arcSymbols.py')
    spec = importlib.util.spec_from_file_location('arcSymbols', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tool = _load()


def kinds(segments):
    return [segment[0] for segment in segments]


def circle(cx, cy, r, count, start=0.0):
    return [(cx + r * math.cos(start + 2 * math.pi * i / count), cy + r * math.sin(start + 2 * math.pi * i / count)) for i in range(count)]


def roundedRectangle(width, height, radius, perCorner):
    points = []
    for (cx, cy, base) in ((width - radius, radius, -math.pi / 2), (width - radius, height - radius, 0),
                           (radius, height - radius, math.pi / 2), (radius, radius, math.pi)):
        points += [(cx + radius * math.cos(base + math.pi / 2 * i / perCorner), cy + radius * math.sin(base + math.pi / 2 * i / perCorner)) for i in range(perCorner + 1)]
    return points


def checked(points, segments):
    """The decomposition re-read from its path data, as the files are, and its deviation from the polygon"""
    loops = tool.svgSymbol.parsePath(tool.pathData([segments]))
    return (loops[0], tool.contourDeviation([points], loops))


def test_circle_polygon_becomes_two_half_arcs():
    points = circle(1, 2, 0.75, 360)
    (loop, deviation) = checked(points, tool.decomposeLoop(points, TOLERANCE))
    assert kinds(loop) == ['arc', 'arc']
    assert deviation <= TOLERANCE


def test_rounded_rectangle_is_4_lines_4_arcs():
    points = roundedRectangle(10, 6, 1.5, 40)
    (loop, deviation) = checked(points, tool.decomposeLoop(points, TOLERANCE))
    assert sorted(kinds(loop)) == ['arc'] * 4 + ['line'] * 4
    assert deviation <= TOLERANCE


def test_thread_zigzag_stays_lines():
    zigzag = [(i * 0.7, 0.7 if i % 2 else 0.0) for i in range(12)] + [(7.7, -2.0), (0.0, -2.0)]
    (loop, deviation) = checked(zigzag, tool.decomposeLoop(zigzag, TOLERANCE))
    assert set(kinds(loop)) == {'line'}
    assert len(loop) == len(zigzag)
    assert deviation <= TOLERANCE


def test_start_point_does_not_matter():
    points = roundedRectangle(10, 6, 1.5, 40)
    for shift in (0, 7, 20, 63):
        rotated = points[shift:] + points[:shift]
        assert len(tool.decomposeLoop(rotated, TOLERANCE)) == 8


def test_free_form_uses_cubic():
    # an ellipse is no circle anywhere: splines, not dozens of short arcs
    points = [(3 * math.cos(2 * math.pi * i / 400), 1.5 * math.sin(2 * math.pi * i / 400)) for i in range(400)]
    (loop, deviation) = checked(points, tool.decomposeLoop(points, TOLERANCE))
    assert 'cubic' in kinds(loop)
    assert len(loop) <= 12
    assert deviation <= TOLERANCE


def test_area_of_arcs_and_cubics():
    loop = tool.svgSymbol.parsePath('M 1,0 A 1,1 0 0 1 -1,0 A 1,1 0 0 1 1,0 z')[0]
    assert abs(tool.loopArea(loop)) == pytest.approx(math.pi, rel=1e-4)


@pytest.mark.parametrize('name, maxSegments', [('torx_countersunk_original.svg', 60), ('pan_torx_security_original.svg', 70)])
def test_screw_symbols_within_tolerance(tmp_path, name, maxSegments):
    path = str(tmp_path / name)
    shutil.copyfile(os.path.join(FIXTURES, name), path)
    report = tool.convertFile(path, TOLERANCE, write=True)
    assert report.changed
    assert report.deviation <= TOLERANCE
    assert report.lines + report.arcs + report.cubics <= maxSegments
    assert report.pointsBefore > 1600
    # the file keeps its header, only the path changes
    with open(path, encoding='utf-8') as file:
        svg = file.read()
    assert '<svg width="14.56mm"' in svg and 'OpenSCAD Model' in svg
    symbol = tool.svgSymbol.readSymbol(path)
    original = tool.svgSymbol.readSymbol(os.path.join(FIXTURES, name))
    assert symbol.bounds == pytest.approx(original.bounds, abs=TOLERANCE)
    for (new, old) in zip(symbol.loops, original.loops):
        assert abs(tool.loopArea(new)) == pytest.approx(abs(tool.loopArea(old)), rel=0.005)


def test_converting_twice_changes_nothing(tmp_path):
    path = str(tmp_path / 'torx.svg')
    shutil.copyfile(os.path.join(FIXTURES, 'torx_countersunk_original.svg'), path)
    tool.convertFile(path, TOLERANCE, write=True)
    with open(path, encoding='utf-8') as file:
        once = file.read()
    assert not tool.convertFile(path, TOLERANCE, write=True).changed
    with open(path, encoding='utf-8') as file:
        assert file.read() == once


def test_existing_arcs_are_kept(tmp_path):
    path = str(tmp_path / 'hex-nut.svg')
    shutil.copyfile(os.path.join(PROJECT_ROOT, 'lib', 'gridfinityUtils', 'labelIcons', 'nuts', 'hex-nut.svg'), path)
    with open(path, encoding='utf-8') as file:
        before = file.read()
    report = tool.convertFile(path, TOLERANCE, write=True)
    assert not report.changed
    with open(path, encoding='utf-8') as file:
        assert file.read() == before


def test_check_does_not_write(tmp_path):
    path = str(tmp_path / 'torx.svg')
    shutil.copyfile(os.path.join(FIXTURES, 'torx_countersunk_original.svg'), path)
    assert tool.convertFile(path, TOLERANCE, write=False).changed
    with open(path, encoding='utf-8') as file, open(os.path.join(FIXTURES, 'torx_countersunk_original.svg'), encoding='utf-8') as original:
        assert file.read() == original.read()


def test_check_error_when_tolerance_exceeded(monkeypatch, tmp_path):
    path = str(tmp_path / 'torx.svg')
    shutil.copyfile(os.path.join(FIXTURES, 'torx_countersunk_original.svg'), path)
    # a decomposition that cuts every loop short to a triangle is far off
    monkeypatch.setattr(tool, 'decomposeLoop', lambda points, tolerance: [('line', points[0], points[len(points) // 3]), ('line', points[len(points) // 3], points[2 * len(points) // 3]), ('line', points[2 * len(points) // 3], points[0])])
    with pytest.raises(tool.SymbolCheckError):
        tool.convertFile(path, TOLERANCE, write=True)
    with open(path, encoding='utf-8') as file, open(os.path.join(FIXTURES, 'torx_countersunk_original.svg'), encoding='utf-8') as original:
        assert file.read() == original.read()


def test_convert_folder_writes_check_file(tmp_path):
    shutil.copyfile(os.path.join(FIXTURES, 'torx_countersunk_original.svg'), tmp_path / 'torx.svg')
    tool.convertFolder(str(tmp_path), TOLERANCE, write=True)
    with open(tmp_path / tool.CHECK_FILE, encoding='utf-8') as file:
        check = json.load(file)
    original = tool.svgSymbol.readSymbol(os.path.join(FIXTURES, 'torx_countersunk_original.svg'))
    assert check['torx.svg']['bounds'] == pytest.approx(list(original.bounds))
    assert len(check['torx.svg']['areas']) == len(original.loops)
    # a second run keeps the areas of the polygons, not of the arcs
    tool.convertFolder(str(tmp_path), TOLERANCE, write=True)
    with open(tmp_path / tool.CHECK_FILE, encoding='utf-8') as file:
        assert json.load(file) == check


def _write(tmp_path, name, points):
    d = 'M ' + ' L '.join(f'{x:.6f},{y:.6f}' for (x, y) in points) + ' z'
    path = tmp_path / name
    path.write_text(f'<svg width="3mm" height="3mm" viewBox="-1.5 -1.5 3 3" xmlns="http://www.w3.org/2000/svg"><path d="{d}"/></svg>')
    return str(path)


def test_coarse_circle_may_grow_by_perimeter_times_tolerance(tmp_path):
    # the hardware symbols are coarse polygons ($fs = 0.2): the arc through their corners is the circle they stand
    # for and has a little more area than the polygon, more than 0.5 % but within the outline tolerance all round
    points = circle(0, 0, 0.5, 18)
    report = tool.convertFile(_write(tmp_path, 'coarse.svg', points), TOLERANCE, write=True)
    assert report.changed and report.arcs == 2
    polygonArea = abs(tool._signedArea(points))
    assert report.areaChange > 0.005 * polygonArea
    assert report.areaChange <= 2 * math.pi * 0.5 * TOLERANCE


def test_folder_keeps_a_file_that_fails_and_goes_on(monkeypatch, tmp_path):
    good = _write(tmp_path, 'a.svg', circle(0, 0, 0.5, 64))
    bad = _write(tmp_path, 'b.svg', roundedRectangle(1, 1, 0.3, 30))
    with open(bad, encoding='utf-8') as file:
        before = file.read()
    real = tool.decomposeLoop
    monkeypatch.setattr(tool, 'decomposeLoop', lambda points, tolerance: real(points, tolerance) if len(points) == 64 else [('line', points[0], points[len(points) // 2]), ('line', points[len(points) // 2], points[0])])
    reports = tool.convertFolder(str(tmp_path), TOLERANCE, write=True)
    assert [(report.name, report.changed, bool(report.error)) for report in reports] == [('a.svg', True, False), ('b.svg', False, True)]
    with open(bad, encoding='utf-8') as file:
        assert file.read() == before
    with open(good, encoding='utf-8') as file:
        assert ' A ' in file.read()


def test_folder_skips_a_hand_made_svg_it_cannot_read(tmp_path):
    good = _write(tmp_path, 'a.svg', circle(0, 0, 0.5, 64))
    hand = tmp_path / 'hand.svg'
    hand.write_text('<svg viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg"><path d="m 1,1 h 8 v 8 h -8 z"/></svg>')
    before = hand.read_text()
    reports = tool.convertFolder(str(tmp_path), TOLERANCE, write=True)
    assert [(report.name, report.changed, bool(report.error)) for report in reports] == [('a.svg', True, False), ('hand.svg', False, True)]
    assert hand.read_text() == before
    with open(tmp_path / tool.CHECK_FILE, encoding='utf-8') as file:
        assert sorted(json.load(file)) == ['a.svg']
