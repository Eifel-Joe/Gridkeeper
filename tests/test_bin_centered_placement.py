"""
Round 54 (p670): a bin centered on the origin stays centered when its base units change in the parameter table. Its
offset is a Dim of the bin's base unit parameters, so the Bin placement move follows them; the value at build time is
the one the bin got before. binBuilder needs Fusion to load, so centeredPlacement is taken from its source and run
with the real Dim, the move and the rest of the bin are checked in Fusion (snapshot case
bin_2x1x3_centered_params_base_50x46).
"""

import ast
import os
import sys
import types
import importlib.util

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_BUILDER = os.path.join(ROOT, "commands", "commandCreateBin", "binBuilder.py")


def _load_dim():
    # only while loading, for dim's annotations: other tests put stand-ins of their own when there are none (test_dim)
    core = sys.modules["adsk.core"]
    added = [name for name in ("Base", "ValueInput") if not hasattr(core, name)]
    for name in added:
        setattr(core, name, type(name, (), {}))
    try:
        spec = importlib.util.spec_from_file_location("dimForCenteredPlacement", os.path.join(ROOT, "lib", "gridfinityUtils", "dim.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for name in added:
            delattr(core, name)


Dim = _load_dim().Dim


def _centeredPlacement():
    tree = ast.parse(open(BIN_BUILDER, encoding="utf-8").read())
    node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "centeredPlacement")
    namespace = {"Dim": Dim, "InputState": object}
    exec(compile(ast.Module(body=[node], type_ignores=[]), BIN_BUILDER, "exec"), namespace)
    return namespace["centeredPlacement"]


class _Parameter:
    def __init__(self, name, value):
        self.name = name
        self.value = value


def _state(binWidth, binLength, baseWidth=4.2, baseLength=4.2, xyClearance=0.025):
    return types.SimpleNamespace(binWidth=binWidth, binLength=binLength, baseWidth=baseWidth, baseLength=baseLength, xyClearance=xyClearance)


def _units(baseWidth=4.2, baseLength=4.2):
    return (Dim.parameter(_Parameter("gfBin1_baseWidth", baseWidth)), Dim.parameter(_Parameter("gfBin1_baseLength", baseLength)))


def _before(state):
    """The offset the bin got before round 54, plain numbers"""
    return (
        -(state.binWidth * state.baseWidth - state.xyClearance * 2) / 2,
        -(state.binLength * state.baseLength - state.xyClearance * 2) / 2,
    )


@pytest.mark.parametrize("binWidth, binLength, baseWidth, baseLength", [
    (2, 1, 4.2, 4.2),
    # half grid: the size counts in base units, 1.5 is three half feet
    (1.5, 2.5, 4.2, 4.2),
    # base units of different sides
    (1, 1, 4.0, 5.0),
    (3, 3, 5.0, 5.0),
])
def test_the_value_at_build_time_is_the_one_before(binWidth, binLength, baseWidth, baseLength):
    state = _state(binWidth, binLength, baseWidth, baseLength)
    (x, y) = _centeredPlacement()(state, *_units(baseWidth, baseLength))
    assert x.value == pytest.approx(_before(state)[0], abs=1e-9)
    assert y.value == pytest.approx(_before(state)[1], abs=1e-9)


def test_the_offset_follows_the_base_unit_parameters():
    (x, y) = _centeredPlacement()(_state(2, 1), *_units())
    assert x.isExpression and y.isExpression
    assert "gfBin1_baseWidth" in x.expression and "gfBin1_baseLength" not in x.expression
    assert "gfBin1_baseLength" in y.expression and "gfBin1_baseWidth" not in y.expression
    assert x.dependsOnParameters and y.dependsOnParameters


@pytest.mark.parametrize("binWidth, newBaseWidth", [(2, 5.0), (1.5, 4.0), (3, 4.6)])
def test_with_a_new_base_unit_it_is_the_offset_of_a_bin_built_with_it(binWidth, newBaseWidth):
    """The expression Fusion evaluates with the new unit gives the offset a new bin of that unit gets: half the
    footprint, the bin from -w/2 to +w/2"""
    (x, _) = _centeredPlacement()(_state(binWidth, 1), *_units())
    evaluated = eval(x.expression.replace("gfBin1_baseWidth", f"{newBaseWidth * 10}").replace(" mm", ""))
    assert evaluated / 10 == pytest.approx(_before(_state(binWidth, 1, newBaseWidth))[0], abs=1e-9)


# --- the bin and what is placed with it take the offset as it is (source checks, the geometry in Fusion) ---

LABEL_GENERATOR = os.path.join(ROOT, "lib", "gridfinityUtils", "labelGenerator.py")


def _source(path, name):
    tree = ast.parse(open(path, encoding="utf-8").read())
    return ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name))


def test_the_centered_offset_is_made_once_the_base_unit_parameters_are_there():
    source = _source(BIN_BUILDER, "_buildBin")
    assert source.index("baseLength = Dim.parameter(baseLengthParameter)") < source.index("centeredPlacement(state, baseWidth, baseLength)")
    # a free, kept or cell spot stays numbers
    assert "(Dim.length(spot[0]), Dim.length(spot[1]))" in source


def test_the_move_and_the_joint_origins_take_the_offset_as_it_is():
    source = _source(BIN_BUILDER, "_buildBin")
    assert "placementUtils.moveBodies(generatedBodies, *binPlacement, gridfinityBinComponent, name=BIN_PLACEMENT_FEATURE)" in source
    assert "Dim.length(binPlacement" not in source
    assert "binPlacement != (0, 0)" not in source
    assert "offsetX = binPlacement[0]" in source
    assert source.count("None if isZero(binPlacement[0]) else binPlacement[0]") == 2


def test_colored_letters_take_the_offset_as_it_is():
    source = _source(LABEL_GENERATOR, "createLabel")
    assert "Dim.length(dx)" not in source and "Dim.length(shiftX)" not in source
    assert "Dim.asLength(dx)" in source and "Dim.asLength(shiftX)" in source
    assert "isZero(shiftX) and isZero(shiftY)" in source
