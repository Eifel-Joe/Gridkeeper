"""
The box label module (round 29, p262, dev-notes/r29/boxlabel-plan.md) needs Fusion to run, so these tests read its
source: the parts the plan makes binding, every sketch fully constrained (17.11.2026: all sketches must be fully constrained), no feature mirror (dev-notes/r29/README.md), the joint origin in the
part frame, the markings like the Cullenect inserts'.
"""

import ast
import os

SOURCE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "gridfinityUtils", "predBoxLabel.py")


def _tree():
    return ast.parse(open(SOURCE, encoding="utf-8").read())


def _function(name):
    return next(node for node in _tree().body if isinstance(node, ast.FunctionDef) and node.name == name)


def _source(name):
    return ast.unparse(_function(name))


def test_the_plate_is_preds_rounded_rectangle_on_the_origin():
    """Pred's Label/Sketch1 (r29_walk/Label.json): 67.5 x 24.5 mm, corners rounded 3.5 mm. predSketch's rounded
    rectangle: createRectangle with its corner dimensioned from the origin, four fillets, equal, one radius dimension"""
    source = _source("_plate")
    assert "WorldSketch(component, component.xYConstructionPlane" in source
    assert "roundedRectangle(-width / 2, -PLATE_HEIGHT / 2, width / 2, PLATE_HEIGHT / 2, 0, PLATE_CORNER_RADIUS)" in source


def test_the_plate_gets_preds_chamfer_all_round_front_and_back():
    """Pred's Chamfer1: equal distance 0.2 mm, the outline of both faces as tangent chains"""
    source = _source("_plate")
    assert "extrude.startFaces" in source and "extrude.endFaces" in source
    assert "addEqualDistanceChamferEdgeSet(" in source and "PLATE_CHAMFER" in source


def test_the_plate_is_preds_thickness_up_from_the_back_face():
    source = _source("_plate")
    assert "_extrude([sketch.profiles.item(0)], PLATE_THICKNESS, True, component" in source.replace("plateSketch.sketch", "sketch")


def test_the_joint_origin_needs_no_sketch():
    """On the component's origin point: a sketch point there would need a dimension of zero (sketchChain)"""
    source = _source("_labelJointOrigin")
    assert "JointGeometry.createByPoint(component.originConstructionPoint)" in source
    assert "zAxisEntity = component.yConstructionAxis" in source
    assert "xAxisEntity = component.xConstructionAxis" in source
    assert "LABEL_JOINT_ORIGIN" in source


def test_texts_stand_on_fixed_baselines_like_the_inserts():
    """cullenectLabelGenerator._texts fixes each baseline and every point of the sketch (_fixSketch)"""
    source = _source("createBoxLabel")
    assert "_texts(sketch, fieldLayout" in source


def test_symbol_sketches_are_fixed():
    source = _source("createBoxLabel")
    assert source.index("_importIcon(sketch") < source.index("_fixSketch(sketch)") < source.index("_iconProfiles(sketch)")


def test_no_feature_mirror_and_no_loose_sketches():
    text = open(SOURCE, encoding="utf-8").read()
    assert "mirrorFeatures" not in text
    assert "sketches.add(" in text
    # every sketch the module adds is on the XY plane or the marking plane over the plate
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Call) and ast.unparse(node.func).endswith("sketches.add"):
            assert ast.unparse(node.args[0]) == "plane", ast.unparse(node)


def test_markings_are_preds_04_mm_and_cut_like_the_inserts():
    source = _source("createBoxLabel")
    assert "_extrude(fieldTexts, MARKING_DEPTH, isEmbossed" in source
    assert "_cutExtrude(twins, MARKING_DEPTH, plateInContext" in source
    assert "cutBody(plateInContext" in source


def test_debossed_hides_the_filling():
    source = _source("createBoxLabel")
    assert "if input.surface == SURFACE_DEBOSSED:" in source and "isLightBulbOn = False" in source


def test_only_the_symbols_that_fit_are_drawn():
    source = _source("createBoxLabel")
    assert "zip(input.symbolPaths, layout.symbolBoxes)" in source


def test_no_imports_inside_functions():
    for node in ast.walk(_tree()):
        if isinstance(node, ast.FunctionDef):
            assert not any(isinstance(inner, (ast.Import, ast.ImportFrom)) for inner in ast.walk(node)), node.name
