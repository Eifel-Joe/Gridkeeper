"""
Round 55 (p680): the sample Bambu Studio projects for the test in Bambu Studio come out as the spec says, see
tests/e2e/bambu_project_samples.py.
"""

import importlib.util
import json
import os
import zipfile
import xml.etree.ElementTree as ElementTree

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("bambu_project_samples", os.path.join(ROOT, "tests", "e2e", "bambu_project_samples.py"))
samples = importlib.util.module_from_spec(spec)
spec.loader.exec_module(samples)


def read(path):
    with zipfile.ZipFile(path) as package:
        return (
            ElementTree.fromstring(package.read("3D/3dmodel.model")),
            ElementTree.fromstring(package.read("Metadata/model_settings.config")),
            json.loads(package.read("Metadata/project_settings.config")),
        )


def test_the_p1s_sample_has_three_plates_with_its_profiles_and_colors(tmp_path):
    results = samples.writeSamples(str(tmp_path))
    assert results["r55-p1s-three-plates.3mf"] == (3, [], [], [])
    (model, settings, project) = read(tmp_path / "r55-p1s-three-plates.3mf")
    assert [len(plate.findall("model_instance")) for plate in settings.findall("plate")] == [3, 2, 6]
    assert project["printer_settings_id"] == "Bambu Lab P1S 0.4 nozzle"
    assert project["filament_settings_id"] == ["Bambu PLA Basic @BBL P1S 0.4 nozzle"] * 4
    assert project["filament_colour"] == ["#808080", "#D02020", "#2060D0", "#000000"]
    codes = {triangle.get("paint_color") for triangle in model.iter("{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}triangle")}
    assert codes == {None, "8", "0C", "1C"}


def test_the_one_plate_samples(tmp_path):
    samples.writeSamples(str(tmp_path))
    assert sorted(os.listdir(tmp_path)) == ["r55-a1mini-one-plate.3mf", "r55-p1s-three-plates.3mf", "r56-h2d-two-plates.3mf",
                                            "r57-a1mini-4colours.3mf", "r57-h3c-4colours.3mf", "r57-p1s-4colours.3mf"]
    (_, settings, project) = read(tmp_path / "r55-a1mini-one-plate.3mf")
    assert len(settings.findall("plate")) == 1
    assert project["printer_settings_id"] == "Bambu Lab A1 mini 0.4 nozzle"
    assert project["filament_colour"] == ["#808080", "#D02020"]


def test_the_h2d_sample_has_purging_volumes_for_both_nozzles(tmp_path):
    # round 56 (p690): as r56-h2d-4colours.3mf of the Bambu Studio test of 23.11.2026, which opened without a warning
    results = samples.writeSamples(str(tmp_path))
    assert results["r56-h2d-two-plates.3mf"] == (2, [], [], [])
    (_, settings, project) = read(tmp_path / "r56-h2d-two-plates.3mf")
    assert len(settings.findall("plate")) == 2
    assert project["printer_settings_id"] == "Bambu Lab H2D 0.4 nozzle"
    assert project["filament_colour"] == ["#808080", "#D02020", "#2060D0", "#000000"]
    matrix = [int(value) for value in project["flush_volumes_matrix"]]
    assert matrix[0:4] == [0, 295, 295, 208] and matrix[16:20] == [0, 310, 310, 223] and len(matrix) == 32
    assert project["flush_multiplier"] == ["1", "1"]
    # round 57: one nozzle gets them too
    assert read(tmp_path / "r55-p1s-three-plates.3mf")[2]["flush_multiplier"] == ["1"]


def offDiagonalZeros(project):
    matrix = [float(value) for value in project["flush_volumes_matrix"]]
    size = round((len(matrix) // len(project["flush_multiplier"])) ** 0.5)
    return [index for (index, value) in enumerate(matrix) if value == 0 and (index % (size * size)) // size != index % size]


@pytest.mark.parametrize(("name", "printer", "row"), [
    # round 57: one extruder, one block; grey to red, blue, black: the formula plus the nozzle volume, 1.3 towards
    # black only with a flush data set (H3C)
    ("r57-p1s-4colours.3mf", "Bambu Lab P1S 0.4 nozzle", [0, 272, 272, 167]),
    ("r57-a1mini-4colours.3mf", "Bambu Lab A1 mini 0.4 nozzle", [0, 257, 257, 152]),
    ("r57-h3c-4colours.3mf", "Bambu Lab H3C 0.4 nozzle", [0, 290, 290, 203]),
])
def test_the_one_extruder_samples_have_a_block_of_purging_volumes(tmp_path, name, printer, row):
    results = samples.writeSamples(str(tmp_path))
    assert results[name][1:] == ([], [], [])
    (_, _, project) = read(tmp_path / name)
    assert project["printer_settings_id"] == printer
    assert project["filament_colour"] == ["#808080", "#D02020", "#2060D0", "#000000"]
    matrix = [int(value) for value in project["flush_volumes_matrix"]]
    assert len(matrix) == 16 and matrix[0:4] == row
    assert project["flush_multiplier"] == ["1"] and project["filament_map"] == ["1"] * 4
    assert not offDiagonalZeros(project)
