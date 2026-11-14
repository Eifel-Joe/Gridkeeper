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
    assert 'cullenect_hardware("crimp_fork_open")' in scad
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
