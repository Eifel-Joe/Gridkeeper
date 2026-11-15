"""
Tests for tools/cullenectIcons.py, the one-off tool that renders the Cullenect symbols to svg with OpenSCAD.
The tool itself is not run here, only what it builds.
"""

import os
import importlib.util

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    path = os.path.join(PROJECT_ROOT, "tools", "cullenectIcons.py")
    spec = importlib.util.spec_from_file_location("cullenectIcons", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tool = _load()


def test_screw_wrapper_uses_cullenect_modules():
    scad = tool.wrapperScad('screw', ('socket', 'machine', 'full', 'hex', False, False))
    assert 'use <Cullenect.scad>' in scad
    assert 'cullenect_head(head="socket", flange=false)' in scad
    assert 'cullenect_driver(driver="hex")' in scad
    assert 'cullenect_shaft(shaft="machine", threads="full")' in scad
    assert 'projection(' in scad
    assert 'security' not in scad


def test_screw_wrapper_flange_and_security():
    scad = tool.wrapperScad('screw', ('pan', 'tapping', 'partial', 'torx', True, True))
    assert 'cullenect_head(head="pan", flange=true)' in scad
    assert 'cullenect_shaft(shaft="tapping", threads="partial")' in scad
    assert 'cullenect_driver(driver="security")' in scad


def test_hardware_wrapper():
    scad = tool.wrapperScad('hardware', 'crimp_fork_open')
    assert 'use <Cullenect.scad>' in scad
    assert 'cullenect_hardware("crimp_fork_open", $fa = 12, $fs = 0.2)' in scad
    assert 'projection(' in scad


def test_wrapper_rejects_unknown_kind():
    try:
        tool.wrapperScad('bogus', 'x')
    except ValueError:
        return
    raise AssertionError('expected ValueError')


def test_openscad_command():
    assert tool.openscadCommand('openscad.exe', 'a.scad', 'a.svg') == ['openscad.exe', '-o', 'a.svg', 'a.scad']


def test_render_jobs_cover_all_symbols(tmp_path):
    jobs = tool.renderJobs(str(tmp_path))
    names = [os.path.basename(svg) for (_, _, svg) in jobs]
    assert len(jobs) == 480 + 18
    assert len(set(names)) == len(names)
    assert 'screw_socket_machine_full_hex_noflange_nosec.svg' in names
    assert 'washer_locking.svg' in names
    assert all(svg.startswith(str(tmp_path)) for (_, _, svg) in jobs)


def test_tighten_svg_sets_exact_size():
    svg = ('<svg width="15mm" height="10mm" viewBox="-12 -5 15 10" xmlns="http://www.w3.org/2000/svg" version="1.1">\n'
           '<path d="\nM 3,-5 L -3,-5 L -11.56,2.5 L 3,2.5 z\n" stroke="black"/>\n</svg>\n')
    tight = tool.tightenSvg(svg)
    assert 'width="14.56mm" height="7.5mm" viewBox="-11.56 -5 14.56 7.5"' in tight
    assert 'xmlns=' in tight and 'M 3,-5' in tight


def test_tighten_svg_rejects_empty():
    try:
        tool.tightenSvg('<svg width="1mm" height="1mm" viewBox="0 0 1 1"></svg>')
    except ValueError:
        return
    raise AssertionError('expected ValueError')


def test_label_icon_path_avoids_existing_icons(tmp_path):
    path = tool.labelIconPath('washer_locking', str(tmp_path))
    assert path == str(tmp_path / 'washers' / 'cullenect-washer-locking.svg')
    assert tool.labelIconPath('washer', str(tmp_path)) != str(tmp_path / 'washers' / 'washer.svg')


def test_copy_hardware_to_label_icons(tmp_path):
    hardware = tmp_path / 'icons' / 'hardware'
    hardware.mkdir(parents=True)
    (hardware / 'magnet.svg').write_text('<svg/>')
    (hardware / 'dowel.svg').write_text('<svg/>')
    copied = tool.copyHardwareToLabelIcons(str(tmp_path / 'icons'), str(tmp_path / 'label'))
    assert copied == [str(tmp_path / 'label' / 'magnets' / 'cullenect-magnet.svg')]
    assert os.path.isfile(copied[0])


def test_tighten_svg_rejects_unknown_header():
    try:
        tool.tightenSvg('<svg viewBox="0 0 1 1" width="1mm" height="1mm"><path d="M 0,0 L 1,1"/></svg>')
    except ValueError:
        return
    raise AssertionError('expected ValueError')


def test_render_reports_errors_instead_of_raising(tmp_path):
    job = ('screw', ('socket', 'machine', 'full', 'hex', False, False), str(tmp_path / 'a.svg'))
    error = tool.render(str(tmp_path / 'no-such-openscad.exe'), job, str(tmp_path))
    assert error is not None and 'a.svg' in error


# --- round 17, p51: coarser hardware symbols, within 0.05 mm of the fine ones

import math

import pytest


def _circleSegments(radius, count):
    points = [(radius * math.cos(2 * math.pi * i / count), radius * math.sin(2 * math.pi * i / count)) for i in range(count)]
    return [(*a, *b) for (a, b) in zip(points, points[1:] + points[:1])]


def test_deviation_of_a_coarse_circle():
    deviation = tool.contourDeviation(_circleSegments(5, 360), _circleSegments(5, 30))
    assert deviation == pytest.approx(5 * (1 - math.cos(math.radians(6))), abs=1e-6)


def test_identical_contours_have_no_deviation():
    assert tool.contourDeviation(_circleSegments(5, 60), _circleSegments(5, 60)) == pytest.approx(0, abs=1e-9)


def test_svg_segments_close_each_loop():
    svg = '<svg><path d="\nM 0,0 L 1,0 L 1,1\n z\nM 2,2 L 3,2 L 3,3\n z\n"/></svg>'
    assert tool.svgSegments(svg) == [
        (0, 0, 1, 0), (1, 0, 1, 1), (1, 1, 0, 0),
        (2, 2, 3, 2), (3, 2, 3, 3), (3, 3, 2, 2),
    ]


def test_wrapper_uses_the_resolution_of_its_kind():
    assert tool.HARDWARE_RESOLUTION in tool.wrapperScad('hardware', 'nut_nylon')
    assert tool.SCREW_RESOLUTION in tool.wrapperScad('screw', ('socket', 'machine', 'full', 'hex', False, False))
    assert tool.HARDWARE_RESOLUTION != tool.SCREW_RESOLUTION


def test_screws_keep_their_resolution():
    # only the hardware symbols are rendered anew (Hauptsitzung 15.11.2026), the screws stay as they were made
    assert tool.SCREW_RESOLUTION == '$fa = 3; $fs = 0.1;'


def test_compare_fails_when_it_compared_nothing(tmp_path, monkeypatch):
    # a wrong folder skipped every symbol and passed with "largest deviation 0" (review round 17)
    monkeypatch.setattr('sys.argv', ['cullenectIcons.py', '--compare', str(tmp_path / 'nothing')])
    assert tool.main() == 1
