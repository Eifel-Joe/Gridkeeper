"""
Round 55 (p680): Bambu Studio projects to open in Bambu Studio by hand, made from unit-test style meshes the way the
3MF export makes them (printLayout.layOutKinds, threeMf.writeBambuProject), no Fusion needed.

    python tests/e2e/bambu_project_samples.py <folder>

writes
- r55-p1s-three-plates.3mf: Bambu Lab P1S, bins on two plates, Cullenect style labels on a third, label text in red, blue
  and without a color (black), on filaments 2, 3 and 4
- r55-a1mini-one-plate.3mf: Bambu Lab A1 mini, one plate, red text
- r56-h2d-two-plates.3mf (round 56, p690): Bambu Lab H2D, the bins and labels of the P1S sample on its larger bed,
  two plates, with purging volumes for both nozzles
"""

import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "lib", f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


threeMf = _load("threeMf")
printLayout = _load("printLayout")
printBeds = _load("printBeds")
exportParts = _load("exportParts")

RED = "#D02020"
BLUE = "#2060D0"


def box(name, width, length, height, letters=None):
    """A box standing on z 0, its top's two triangles painted with the filament of letters"""
    vertices = [(dx, dy, dz) for dz in (0, height) for dy in (0, length) for dx in (0, width)]
    triangles = [(0, 2, 1), (1, 2, 3), (4, 5, 6), (5, 7, 6), (0, 1, 4), (1, 5, 4), (2, 6, 3), (3, 6, 7), (0, 4, 2), (2, 4, 6), (1, 3, 5), (3, 7, 5)]
    painted = {2: letters, 3: letters} if letters is not None else {}
    return threeMf.MeshObject(name, vertices, triangles, painted)


def project(path, label, parts, filaments, kinds=None):
    """The parts laid out as the export does, each its own group, written as the export writes the project"""
    bed = printBeds.PRINT_BED_PRESETS[label]
    groups = [[part] for part in parts]
    (laid, plates, tooLarge, noPurge, nearExcluded) = printLayout.layOutKinds(
        groups, kinds or [None] * len(groups), bed, exportParts.DEFAULT_SPACING, exportParts.DEFAULT_PURGE,
        printBeds.purgeAnchor(label), printBeds.excludedAreas(label))
    threeMf.writeBambuProject(path, [meshObject for (_, meshObject) in laid], [plate for (plate, _) in laid], bed,
                              printBeds.bambuProfiles(label), exportParts.filamentColours(filaments),
                              os.path.splitext(os.path.basename(path))[0], "1.4.0")
    return (plates, tooLarge, noPurge, nearExcluded)


def writeSamples(folder):
    """The sample projects in the folder, by file name their plates and what the layout reported"""
    os.makedirs(folder, exist_ok=True)
    filaments = {RED: 2, BLUE: 3, "": 4}
    bins = [box(f"Bin 3x2 #{index + 1}", 125.5, 83.5, 21) for index in range(3)] + \
           [box(f"Bin 2x2 #{index + 1}", 83.5, 83.5, 42) for index in range(2)]
    labels = [box(f"Label {color or 'black'} #{index + 1}", 36, 11.5, 1.2, letters=filament)
              for index in range(2) for (color, filament) in filaments.items()]
    results = {}
    results["r55-p1s-three-plates.3mf"] = project(os.path.join(folder, "r55-p1s-three-plates.3mf"), "Bambu Lab P1S (256 x 256 mm)",
                                                 bins + labels, filaments, ["bins"] * len(bins) + ["labels"] * len(labels))
    results["r55-a1mini-one-plate.3mf"] = project(os.path.join(folder, "r55-a1mini-one-plate.3mf"), "Bambu Lab A1 mini (180 x 180 mm)",
                                                 [box("Bin 2x1", 83.5, 41.5, 21), box("Label red", 36, 11.5, 1.2, letters=2)], {RED: 2})
    results["r56-h2d-two-plates.3mf"] = project(os.path.join(folder, "r56-h2d-two-plates.3mf"), "Bambu Lab H2D (350 x 320 mm)",
                                               bins + labels, filaments, ["bins"] * len(bins) + ["labels"] * len(labels))
    return results


if __name__ == "__main__":
    for (name, (plates, tooLarge, noPurge, nearExcluded)) in writeSamples(sys.argv[1]).items():
        print(f"{name}: {plates} plate(s), too large {tooLarge}, no purge room {noPurge}, near excluded {nearExcluded}")
