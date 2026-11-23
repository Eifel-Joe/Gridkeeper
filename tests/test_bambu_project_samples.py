"""
Round 55 (p680): the sample Bambu Studio projects for the test in Bambu Studio come out as the spec says, see
tests/e2e/bambu_project_samples.py.
"""

import importlib.util
import json
import os
import zipfile
import xml.etree.ElementTree as ElementTree

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
    # no H2D: a printer with two nozzles gets a file per plate, see printBeds.TWO_NOZZLES
    assert sorted(os.listdir(tmp_path)) == ["r55-a1mini-one-plate.3mf", "r55-p1s-three-plates.3mf"]
    (_, settings, project) = read(tmp_path / "r55-a1mini-one-plate.3mf")
    assert len(settings.findall("plate")) == 1
    assert project["printer_settings_id"] == "Bambu Lab A1 mini 0.4 nozzle"
    assert project["filament_colour"] == ["#808080", "#D02020"]
