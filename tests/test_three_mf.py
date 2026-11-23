"""
Tests for the 3MF writer: the slicers' paint codes, placing the objects on the plate and the file they end up in.
"""

import os
import importlib.util
import datetime
import json
import zipfile
import xml.etree.ElementTree as ElementTree
import pytest


def _load_three_mf():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "threeMf.py")
    spec = importlib.util.spec_from_file_location("threeMf", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


threeMf = _load_three_mf()
CORE = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
SLIC3R = "{http://schemas.slic3r.org/3mf/2017/06}"


def cube(name, x=0.0, z=0.0, painted=None):
    """painted: triangle index -> filament"""
    vertices = [(x + dx, dy, z + dz) for dz in (0, 10) for dy in (0, 10) for dx in (0, 10)]
    triangles = [(0, 2, 1), (1, 2, 3), (4, 5, 6), (5, 7, 6), (0, 1, 4), (1, 5, 4), (2, 6, 3), (3, 6, 7), (0, 4, 2), (2, 4, 6), (1, 3, 5), (3, 7, 5)]
    return threeMf.MeshObject(name, vertices, triangles, dict(painted or {}))


# ---------------------------------------------------------------------------
# paintCode
# ---------------------------------------------------------------------------

def test_paint_codes_match_what_the_slicers_saved():
    # Bambu Studio and OrcaSlicer saved filament 2 as 8, PrusaSlicer extruder 5 as 2C
    assert threeMf.paintCode(2) == "8"
    assert threeMf.paintCode(5) == "2C"


def test_paint_codes_of_the_first_filaments():
    assert [threeMf.paintCode(n) for n in range(1, 6)] == ["4", "8", "0C", "1C", "2C"]
    assert threeMf.paintCode(threeMf.MAX_FILAMENT) == "FC"


@pytest.mark.parametrize("filament", [0, threeMf.MAX_FILAMENT + 1])
def test_paint_code_refuses_filaments_it_cant_name(filament):
    with pytest.raises(ValueError):
        threeMf.paintCode(filament)


# ---------------------------------------------------------------------------
# placeOnPlate
# ---------------------------------------------------------------------------

def test_objects_keep_their_layout_around_the_plate_middle():
    placed = threeMf.placeOnPlate([cube("a", x=0), cube("b", x=20)])
    xs = [x for meshObject in placed for (x, _, _) in meshObject.vertices]
    ys = [y for meshObject in placed for (_, y, _) in meshObject.vertices]
    assert (min(xs) + max(xs)) / 2 == pytest.approx(threeMf.PLATE_CENTER[0])
    assert (min(ys) + max(ys)) / 2 == pytest.approx(threeMf.PLATE_CENTER[1])
    assert min(x for (x, _, _) in placed[1].vertices) - min(x for (x, _, _) in placed[0].vertices) == pytest.approx(20)


def test_each_object_stands_on_the_plate():
    placed = threeMf.placeOnPlate([cube("low", z=-5), cube("high", x=20, z=30)])
    assert [min(z for (_, _, z) in meshObject.vertices) for meshObject in placed] == [0, 0]


# ---------------------------------------------------------------------------
# write
# ---------------------------------------------------------------------------

def read_model(path):
    with zipfile.ZipFile(path) as package:
        assert {"[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model"} <= set(package.namelist())
        return ElementTree.fromstring(package.read("3D/3dmodel.model"))


def read_annotation(path):
    with zipfile.ZipFile(path) as package:
        if threeMf.FACETS_ANNOTATION_PATH not in package.namelist():
            return None
        return json.loads(package.read(threeMf.FACETS_ANNOTATION_PATH))


def test_painted_triangles_carry_both_slicers_codes(tmp_path):
    path = tmp_path / "bins.3mf"
    threeMf.write(str(path), [cube("bin", painted={1: 2, 4: 2})])
    triangles = read_model(path).findall(f".//{CORE}triangle")
    painted = [index for (index, triangle) in enumerate(triangles) if triangle.get("paint_color")]
    assert painted == [1, 4]
    assert all(triangles[index].get(f"{SLIC3R}mmu_segmentation") == "8" for index in painted)


def test_each_painted_triangle_carries_its_own_filament(tmp_path):
    # round 37 (p301): red text on filament 2, blue on 3, in one object
    path = tmp_path / "bins.3mf"
    threeMf.write(str(path), [cube("bin", painted={1: 2, 4: 3})])
    triangles = read_model(path).findall(f".//{CORE}triangle")
    assert [(triangles[index].get("paint_color"), triangles[index].get(f"{SLIC3R}mmu_segmentation")) for index in (1, 4)] == [("8", "8"), ("0C", "0C")]
    assert read_annotation(path)[0]["mmSegmentationFacets"] == [{"triangle": 1, "dividing": "8"}, {"triangle": 4, "dividing": "0C"}]


def test_without_painted_triangles_nothing_is_painted(tmp_path):
    path = tmp_path / "bins.3mf"
    threeMf.write(str(path), [cube("bin")])
    model = read_model(path)
    assert not any(triangle.get("paint_color") for triangle in model.iter(f"{CORE}triangle"))
    assert not any(item.get("name") == "slic3rpe:MmPaintingVersion" for item in model.findall(f"{CORE}metadata"))


def test_every_object_is_built_with_its_name(tmp_path):
    path = tmp_path / "bins.3mf"
    threeMf.write(str(path), [cube('Bin "M3" & M4'), cube("Baseplate", x=20)])
    model = read_model(path)
    assert [item.get("name") for item in model.findall(f".//{CORE}object")] == ['Bin "M3" & M4', "Baseplate"]
    assert [item.get("objectid") for item in model.findall(f".//{CORE}item")] == ["1", "2"]


def test_prusaslicer_3_gets_the_painted_triangles_of_each_object(tmp_path):
    path = tmp_path / "bins.3mf"
    threeMf.write(str(path), [cube("a", painted={4: 5, 1: 5}), cube("b", x=20, painted={}), cube("c", x=40, painted={0: 5})])
    assert read_annotation(path) == [
        {"mmSegmentationFacets": [{"triangle": 1, "dividing": "2C"}, {"triangle": 4, "dividing": "2C"}], "mmSegmentationFacetsVersion": 1, "id": 1},
        {"mmSegmentationFacets": [], "mmSegmentationFacetsVersion": 1, "id": 2},
        {"mmSegmentationFacets": [{"triangle": 0, "dividing": "2C"}], "mmSegmentationFacetsVersion": 1, "id": 3},
    ]


def test_no_annotation_without_painting(tmp_path):
    path = tmp_path / "bins.3mf"
    threeMf.write(str(path), [cube("a"), cube("b", x=20)])
    assert read_annotation(path) is None


def metadata(model):
    return {item.get("name"): item.text for item in model.findall(f"{CORE}metadata")}


def test_the_file_names_the_generator_its_version_the_title_and_day(tmp_path):
    path = tmp_path / "bins.3mf"
    threeMf.write(str(path), [cube("bin")], 'M3 & M4 "bins"', "1.4.2")
    found = metadata(read_model(path))
    assert found["Application"] == "Fusion Gridfinity Generator 1.4.2"
    assert found["Title"] == 'M3 & M4 "bins"'
    assert found["CreationDate"] == datetime.date.today().isoformat()


def test_without_a_version_or_title_the_generator_is_named_alone(tmp_path):
    path = tmp_path / "bins.3mf"
    threeMf.write(str(path), [cube("bin")])
    found = metadata(read_model(path))
    assert found["Application"] == "Fusion Gridfinity Generator"
    assert "Title" not in found


def test_objects_laid_out_on_plates_are_written_where_they_are(tmp_path):
    # round r29-export: printLayout placed them already, write keeps them
    path = tmp_path / "laid.3mf"
    objects = [cube("a", x=300, z=0), cube("b", x=5, z=0)]
    threeMf.write(str(path), objects, isLaidOut=True)
    model = read_model(path)
    xs = sorted(float(vertex.get("x")) for vertex in model.iter(f"{CORE}vertex"))
    assert xs[0] == pytest.approx(5) and xs[-1] == pytest.approx(310)


# ---------------------------------------------------------------------------
# Round 55 (p680): a Bambu Studio project with all plates. Plate grid and plate list as upstream 1ac1579 (Le0Michine)
# names them, the file as Bambu Studio 02.09.01.70 opened it in the test of 23.11.2026 (V2: Bambu's own name and the
# profile names in the project settings, the rest from its system profiles)
# ---------------------------------------------------------------------------

import types

PROFILES = types.SimpleNamespace(printer="Bambu Lab P1S 0.4 nozzle", process="0.20mm Standard @BBL X1C", filament="Bambu PLA Basic @BBL P1S 0.4 nozzle",
                                 nozzleVolumes=(107.0,), flushDatasets=(0,), hotends=(1,), hotendAsExtruder=False, extruders=1)
BAMBU = "{http://schemas.bambulab.com/package/2021}"


def bounds(vertices):
    xs = [x for (x, _, _) in vertices]
    ys = [y for (_, y, _) in vertices]
    zs = [z for (_, _, z) in vertices]
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def test_plates_fill_a_grid_of_about_as_many_columns_as_rows():
    assert [threeMf.plateColumns(count) for count in range(1, 11)] == [1, 2, 2, 2, 3, 3, 3, 3, 3, 4]


def test_plates_are_a_fifth_of_the_bed_apart_rows_going_down():
    # as Bambu Studio put the objects of three plates of a 256 mm bed
    assert threeMf.plateOrigin(0, 3, (256, 256)) == (0, 0)
    assert threeMf.plateOrigin(1, 3, (256, 256)) == pytest.approx((307.2, 0))
    assert threeMf.plateOrigin(2, 3, (256, 256)) == pytest.approx((0, -307.2))
    assert threeMf.plateOrigin(1, 2, (350, 320)) == pytest.approx((420, 0))


def test_the_slicer_gets_the_objects_of_each_plate():
    settings = ElementTree.fromstring(threeMf.modelSettings([cube("a"), cube('b & "c"'), cube("d")], [0, 1, 0]))
    objects = settings.findall("object")
    assert [item.get("id") for item in objects] == ["1", "2", "3"]
    assert [item.find("metadata[@key='name']").get("value") for item in objects] == ["a", 'b & "c"', "d"]
    assert [item.find("metadata[@key='extruder']").get("value") for item in objects] == ["1", "1", "1"]
    part = objects[1].find("part")
    assert part.get("subtype") == "normal_part"
    assert part.find("metadata[@key='name']").get("value") == 'b & "c"'
    assert part.find("metadata[@key='matrix']").get("value") == "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"
    plates = [
        (plate.find("metadata[@key='plater_id']").get("value"), [instance.find("metadata[@key='object_id']").get("value") for instance in plate.findall("model_instance")])
        for plate in settings.findall("plate")
    ]
    assert plates == [("1", ["1", "3"]), ("2", ["2"])]


def test_an_empty_plate_between_is_kept():
    settings = ElementTree.fromstring(threeMf.modelSettings([cube("a"), cube("b")], [0, 2]))
    assert [len(plate.findall("model_instance")) for plate in settings.findall("plate")] == [1, 0, 1]


def test_the_project_settings_name_the_profiles_and_their_parents_only():
    settings = json.loads(threeMf.projectSettings(PROFILES, ["#808080", "#D02020", "#000000"]))
    # round 57: and the purging volumes, see test_one_extruder_gets_a_block_of_purging_volumes
    flush = {"flush_volumes_matrix", "flush_volumes_vector", "flush_multiplier", "flush_multiplier_fast", "filament_map", "filament_map_mode"}
    assert flush <= set(settings)
    settings = {key: value for (key, value) in settings.items() if key not in flush}
    assert settings == {
        "version": "02.09.01.70",
        "name": "project_settings",
        "from": "project",
        "printer_settings_id": "Bambu Lab P1S 0.4 nozzle",
        "print_settings_id": "0.20mm Standard @BBL X1C",
        "filament_settings_id": ["Bambu PLA Basic @BBL P1S 0.4 nozzle"] * 3,
        "filament_colour": ["#808080", "#D02020", "#000000"],
        "curr_bed_type": "Textured PEI Plate",
        # Bambu Studio test of 23.11.2026: without the parents filaments 2 and on came as project copies of Bambu
        # Studio's general defaults (200 °C, 2 mm³/s); with them as Bambu PLA Basic (220 °C, 21 mm³/s)
        "inherits_group": ["0.20mm Standard @BBL X1C"] + ["Bambu PLA Basic @BBL P1S 0.4 nozzle"] * 3 + ["Bambu Lab P1S 0.4 nozzle"],
    }


def test_the_bambu_model_names_bambu_studio_and_keeps_the_paint():
    model = ElementTree.fromstring(threeMf.bambuModelXml([cube("a", x=40, painted={2: 2, 5: 4})], "Bins", date=datetime.date(2026, 11, 23)))
    meta = {item.get("name"): item.text for item in model.findall(f"{CORE}metadata")}
    assert meta["Application"] == "BambuStudio-02.09.01.70"
    assert meta["BambuStudio:3mfVersion"] == "1"
    assert meta["Title"] == "Bins"
    assert meta["CreationDate"] == "2026-11-23"
    triangles = model.findall(f".//{CORE}triangle")
    assert [triangle.get("paint_color") for triangle in triangles[:6]] == [None, None, "8", None, None, "1C"]
    assert all(triangle.get(f"{SLIC3R}mmu_segmentation") is None for triangle in triangles)


def test_each_bambu_object_is_around_its_middle_moved_by_its_build_item():
    model = ElementTree.fromstring(threeMf.bambuModelXml([cube("a", x=40, z=3)], ""))
    vertices = [tuple(float(vertex.get(axis)) for axis in "xyz") for vertex in model.findall(f".//{CORE}vertex")]
    assert bounds(vertices) == pytest.approx((-5, -5, -5, 5, 5, 5))
    item = model.find(f"{CORE}build/{CORE}item")
    assert item.get("objectid") == "1"
    assert item.get("printable") == "1"
    assert [float(value) for value in item.get("transform").split()] == pytest.approx([1, 0, 0, 0, 1, 0, 0, 0, 1, 45, 5, 8])


def test_the_project_holds_the_plates_on_bambus_grid(tmp_path):
    path = tmp_path / "bins.3mf"
    # laid out on the bed, a plate each: a at 10, 20 on plate 1, b at 100, 30 on plate 2
    objects = [cube("a", x=10), cube("b", x=100)]
    objects[0].vertices[:] = [(x, y + 20, z) for (x, y, z) in objects[0].vertices]
    objects[1].vertices[:] = [(x, y + 30, z) for (x, y, z) in objects[1].vertices]
    threeMf.writeBambuProject(str(path), objects, [0, 1], (256, 256), PROFILES, ["#808080"], "bins", "1.3.0")
    with zipfile.ZipFile(path) as package:
        names = set(package.namelist())
        model = ElementTree.fromstring(package.read("3D/3dmodel.model"))
        settings = ElementTree.fromstring(package.read(threeMf.MODEL_SETTINGS_PATH))
        project = json.loads(package.read(threeMf.PROJECT_SETTINGS_PATH))
    assert names == {"[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model", threeMf.MODEL_SETTINGS_PATH, threeMf.PROJECT_SETTINGS_PATH}
    shifts = [[float(value) for value in item.get("transform").split()][9:] for item in model.findall(f"{CORE}build/{CORE}item")]
    assert shifts == [pytest.approx([15, 25, 5]), pytest.approx([307.2 + 105, 35, 5])]
    assert len(settings.findall("plate")) == 2
    assert project["filament_colour"] == ["#808080"]


def test_the_projects_model_names_the_generator_beside_bambu_studio(tmp_path):
    path = tmp_path / "bins.3mf"
    threeMf.writeBambuProject(str(path), [cube("a")], [0], (180, 180), PROFILES, ["#808080"], "bins", "1.3.0")
    meta = metadata(read_model(path))
    assert meta["Application"] == "BambuStudio-02.09.01.70"
    assert meta["Designer"] == "Gridkeeper 1.3.0"


def test_each_plate_has_the_textured_pei_plate():
    # Bambu Studio test of 23.11.2026: the P1S project with three plates opened on the Smooth PEI plate although the
    # project settings name the textured one; Bambu Studio keeps the bed type per plate too (bbs_3mf.cpp BED_TYPE_ATTR)
    settings = ElementTree.fromstring(threeMf.modelSettings([cube("a"), cube("b")], [0, 1]))
    assert [plate.find("metadata[@key='bed_type']").get("value") for plate in settings.findall("plate")] == ["Textured PEI Plate"] * 2


# ---------------------------------------------------------------------------
# purging volumes, round 56 (p690)
# ---------------------------------------------------------------------------

GREY, RED, BLUE, BLACK, WHITE = "#808080", "#D02020", "#2060D0", "#000000", "#FFFFFF"
# the H2D's extruders, see printBeds.BAMBU_PROFILES
H2D = types.SimpleNamespace(printer="Bambu Lab H2D 0.4 nozzle", process="0.20mm Standard @BBL H2D", filament="Bambu PLA Basic @BBL H2D",
                            nozzleVolumes=(130.0, 145.0), flushDatasets=(1, 1), hotends=(1, 1), hotendAsExtruder=False, extruders=2)
P1S = PROFILES


@pytest.mark.parametrize(("source", "target", "minimum", "volume"), [
    # Bambu Studio's "Re-calculate" on the H2D, test of 23.11.2026: left extruder 130, right 145
    (GREY, RED, 130, 295), (RED, GREY, 130, 407), (GREY, BLUE, 130, 295), (BLUE, GREY, 130, 397), (BLACK, GREY, 130, 475),
    (GREY, RED, 145, 310), (RED, GREY, 145, 422),
    # to black from a lighter colour 1.3 times as much before the nozzle's volume (60 · 1.3 + 130)
    (GREY, BLACK, 130, 208), (GREY, BLACK, 145, 223),
])
def test_the_purging_volume_is_bambu_studios(source, target, minimum, volume):
    assert threeMf.flushVolume(source, target, minimum, 1) == volume


def test_without_a_flush_data_set_black_is_not_purged_more():
    assert threeMf.flushVolume(GREY, BLACK, 130, 0) == 190


def test_the_same_colour_is_purged_60_at_least():
    assert threeMf.flushVolume(RED, RED, 0, 1) == 60


def test_the_purging_volume_is_900_at_most():
    # 560 in Bambu Studio's float, a hair below in Python's double
    assert threeMf.flushVolume(BLACK, WHITE, 0, 1) in (559, 560)
    assert threeMf.flushVolume(BLACK, WHITE, 400, 1) == 900


def flushingMatrixError(settings):
    """Bambu Studio's GLCanvas3D::is_flushing_matrix_error, the check behind "Partial purging volume set to 0" """
    matrix = [float(value) for value in settings["flush_volumes_matrix"]]
    multipliers = [float(value) for value in settings["flush_multiplier"]]
    if any(multiplier == 0 for multiplier in multipliers):
        return True
    size = len(matrix) // len(multipliers)
    row = round(size ** 0.5)
    assert row * row == size and size * len(multipliers) == len(matrix)
    return any(value == 0 and (index % size) // row != (index % size) % row for (index, value) in enumerate(matrix))


def test_two_extruders_get_a_block_of_purging_volumes_each():
    settings = json.loads(threeMf.projectSettings(H2D, [GREY, RED]))
    # Bambu Studio test of 23.11.2026, r56-h2d-2colours.3mf: opened without a warning, Re-calculate the same
    assert settings["flush_volumes_matrix"] == ["0", "295", "407", "0", "0", "310", "422", "0"]
    assert settings["flush_volumes_vector"] == ["140"] * 4
    assert settings["flush_multiplier"] == ["1", "1"]
    assert settings["flush_multiplier_fast"] == ["1.2", "1.2"]
    assert settings["filament_map"] == ["1", "1"]
    assert settings["filament_map_mode"] == "Auto For Flush"
    assert not flushingMatrixError(settings)


def test_four_colours_on_two_extruders():
    settings = json.loads(threeMf.projectSettings(H2D, [GREY, RED, BLUE, BLACK]))
    matrix = [int(value) for value in settings["flush_volumes_matrix"]]
    assert len(matrix) == 2 * 16
    assert matrix[0:4] == [0, 295, 295, 208]
    assert matrix[16:20] == [0, 310, 310, 223]
    assert [matrix[index * 5] for index in range(4)] == [0] * 4
    assert settings["filament_map"] == ["1"] * 4
    assert settings["flush_volumes_vector"] == ["140"] * 8
    assert not flushingMatrixError(settings)


def test_one_extruder_gets_a_block_of_purging_volumes():
    # round 57: as Bambu Studio's own project for one nozzle (resources/calib/pressure_advance/auto_pa_line_single.3mf,
    # A1: n² values, flush_multiplier with one entry, filament_map n × 1, Auto For Flush); without them every change
    # of color purged Bambu Studio's flat 280. The P1S has no flush data set: no 1.3 towards black
    settings = json.loads(threeMf.projectSettings(P1S, [GREY, RED]))
    assert settings["flush_volumes_matrix"] == ["0", "272", "384", "0"]
    assert settings["flush_volumes_vector"] == ["140"] * 4
    assert settings["flush_multiplier"] == ["1"]
    assert settings["flush_multiplier_fast"] == ["1.2"]
    assert settings["filament_map"] == ["1", "1"]
    assert settings["filament_map_mode"] == "Auto For Flush"
    assert not flushingMatrixError(settings)


def test_the_h3c_gets_one_block_with_its_flush_data_set():
    # one extruder with nine hotends: one block (Bambu Studio test of 23.11.2026, r56-h3c-4colours-spuelmengen.3mf
    # opened without a warning); its data set 1 purges grey to black 60 · 1.3 + 125
    h3c = types.SimpleNamespace(**{**vars(P1S), "nozzleVolumes": (125.9,), "flushDatasets": (1,), "hotends": (9,), "hotendAsExtruder": True})
    settings = json.loads(threeMf.projectSettings(h3c, [GREY, RED, BLUE, BLACK]))
    matrix = [int(value) for value in settings["flush_volumes_matrix"]]
    assert len(matrix) == 16 and matrix[3] == 203
    assert settings["flush_multiplier"] == ["1"] and settings["flush_multiplier_fast"] == ["1.2"]
    assert not flushingMatrixError(settings)


def test_one_and_two_extruders_get_the_same_keys():
    one = set(json.loads(threeMf.projectSettings(P1S, [GREY, RED])))
    two = set(json.loads(threeMf.projectSettings(H2D, [GREY, RED])))
    assert one == two


def test_the_project_settings_of_a_printbeds_profile():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "printBeds.py")
    spec = importlib.util.spec_from_file_location("printBeds", path)
    printBeds = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(printBeds)
    # round 57: every Bambu printer, a block of 9 per extruder
    for name in printBeds.BAMBU_PROFILES:
        profiles = printBeds.bambuProfiles(printBeds.presetLabel(name))
        settings = json.loads(threeMf.projectSettings(profiles, [GREY, RED, BLUE]))
        assert len(settings["flush_volumes_matrix"]) == 9 * profiles.extruders and not flushingMatrixError(settings)


def test_one_colour_on_two_extruders():
    settings = json.loads(threeMf.projectSettings(H2D, [GREY]))
    assert settings["flush_volumes_matrix"] == ["0", "0"] and settings["flush_multiplier"] == ["1", "1"]
    assert not flushingMatrixError(settings)


def test_extruders_without_a_flush_data_set_each_are_refused():
    # review round 56: a block missing would bring Bambu Studio's zeros back
    broken = types.SimpleNamespace(**{**vars(H2D), "flushDatasets": (1,)})
    with pytest.raises(ValueError):
        threeMf.projectSettings(broken, [GREY, RED])
