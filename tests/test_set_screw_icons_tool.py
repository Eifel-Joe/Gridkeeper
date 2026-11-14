"""
Tests for tools/setScrewIcons.py, the one-off tool that renders the set screw symbols of this fork to svg with
OpenSCAD. The tool itself is not run here, only what it builds.
"""

import os
import importlib.util

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    path = os.path.join(PROJECT_ROOT, "tools", "setScrewIcons.py")
    spec = importlib.util.spec_from_file_location("setScrewIcons", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tool = _load()


def test_wrapper_uses_the_set_screw_module():
    scad = tool.wrapperScad(('none', 'machine', 'full', 'hex', False, False))
    assert 'use <SetScrew.scad>' in scad
    assert 'set_screw(shaft="machine", driver="hex", security=false);' in scad
    assert 'projection(' in scad


def test_wrapper_security_and_point():
    scad = tool.wrapperScad(('none', 'tapping', 'full', 'torx', False, True))
    assert 'set_screw(shaft="tapping", driver="torx", security=true);' in scad


def test_wrapper_refuses_other_screws():
    try:
        tool.wrapperScad(('socket', 'machine', 'full', 'hex', False, False))
    except ValueError:
        return
    assert False, 'a screw with a head is not a set screw'


def test_jobs_go_to_the_setscrews_folder():
    jobs = tool.renderJobs('icons')
    assert len(jobs) == 10
    assert all(os.path.dirname(svgPath) == os.path.join('icons', 'setscrews') for (_, svgPath) in jobs)
    assert ('none', 'machine', 'full', 'slot', False, False) in [combination for (combination, _) in jobs]


def test_set_screw_scad_uses_cullenect_next_to_it():
    with open(os.path.join(PROJECT_ROOT, 'tools', 'setscrew', 'SetScrew.scad'), encoding='utf-8') as file:
        scad = file.read()
    assert 'use <../cullenect/Cullenect.scad>' in scad
    assert 'module set_screw(' in scad
