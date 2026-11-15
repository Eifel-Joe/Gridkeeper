"""
Tests for where a bin label goes (round 14, p72): its text and icon are drawn at the finished spot rather than moved
there, so the layout is worked out as dims that follow the bin's parameters.
"""

import os
import sys
import importlib.util

from pytest import approx


def _load(name):
    # dim annotates with adsk.core types, they only need to exist while it loads. Taken out again afterwards:
    # tests/test_dim.py puts in a working ValueInput of its own only where there's none
    core = sys.modules["adsk.core"]
    added = [typeName for typeName in ("Base", "ValueInput") if not hasattr(core, typeName)]
    for typeName in added:
        setattr(core, typeName, type(typeName, (), {}))
    try:
        return _loadModule(name)
    finally:
        for typeName in added:
            delattr(core, typeName)


def _loadModule(name):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(project_root, "lib", "gridfinityUtils")
    # the module imports const and dim as sibling modules, load them under a throwaway package
    package = "binLabelLayoutTestPackage"
    if package not in sys.modules:
        packageSpec = importlib.util.spec_from_loader(package, loader=None, is_package=True)
        packageModule = importlib.util.module_from_spec(packageSpec)
        packageModule.__path__ = [folder]
        sys.modules[package] = packageModule
    spec = importlib.util.spec_from_file_location(f"{package}.{name}", os.path.join(folder, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


layout = _load("binLabelLayout")
const = sys.modules["binLabelLayoutTestPackage.const"]
Dim = sys.modules["binLabelLayoutTestPackage.dim"].Dim
DimKind = sys.modules["binLabelLayoutTestPackage.dim"].DimKind

SIDE = const.BIN_LABEL_SIDE_MARGIN
GAP = const.BIN_LABEL_ICON_GAP
LENGTH = 1.3


def placement(originX=None, hasIcon=False, hasText=True, tilt=0.0, textHeight=0.5, iconWidth=0.6, iconHeight=0.5):
    return layout.binLabelPlacement(
        originX if originX is not None else Dim.length(2.0),
        Dim.length(-1.5),
        Dim.length(2.4),
        Dim.length(4.0),
        LENGTH,
        tilt,
        textHeight,
        iconWidth,
        iconHeight,
        hasIcon,
        hasText,
    )


def test_text_alone_is_centered_on_the_label_area():
    result = placement()
    assert result.isCentered
    assert result.baselineStartX.value == approx(2.0 + SIDE)
    assert result.baselineEndX.value == approx(2.0 + 4.0 - SIDE)
    assert (result.baselineStartX.value + result.baselineEndX.value) / 2 == approx(2.0 + 4.0 / 2)
    assert result.iconMinX is None


def test_icon_sits_left_and_text_starts_after_it():
    result = placement(hasIcon=True, iconWidth=0.6)
    assert not result.isCentered
    assert result.iconMinX.value == approx(2.0 + SIDE)
    assert result.baselineStartX.value == approx(2.0 + SIDE + 0.6 + GAP)
    assert result.baselineEndX.value == approx(2.0 + 4.0 - SIDE)


def test_dims_follow_the_origin_expression():
    parametric = placement(originX=Dim(2.0, "gfBin1_x", DimKind.EXPRESSION), hasIcon=True)
    assert parametric.baselineStartX.isExpression
    assert parametric.baselineEndX.isExpression
    assert parametric.iconMinX.isExpression
    assert "gfBin1_x" in parametric.baselineStartX.expression
    plain = placement(hasIcon=True)
    assert not plain.baselineStartX.isExpression
    assert not plain.iconMinX.isExpression


def test_baseline_is_middle_of_the_label_minus_half_the_letters():
    result = placement(textHeight=0.5)
    assert result.baselineFromBack == approx(LENGTH / 2 + 0.5 / 2)


def test_icon_stands_on_the_baseline():
    withText = placement(hasIcon=True, textHeight=0.5)
    assert withText.iconMinFromBack == approx(withText.baselineFromBack)
    alone = placement(hasIcon=True, hasText=False, iconHeight=0.7)
    assert alone.iconMinFromBack == approx(LENGTH / 2 + 0.7 / 2)


def test_hinge_is_the_back_edge():
    result = placement(tilt=0.3)
    assert result.hingeY.value == approx(-1.5 + LENGTH)
    assert result.planeZ.value == approx(2.4)
    assert result.tiltAngle == 0.3


def test_small_icons_are_held_by_dims_large_ones_moved():
    # Fusion 15.11.2026: the hex nut's 10 points took 20 dims in 0.3 s, the 263 points of a Cullenect crimp ring not
    # even all of their dims in a minute
    assert layout.ICON_POINTS_HELD_BY_DIMS == 40
    assert layout.isIconHeldByDims(10)
    assert layout.isIconHeldByDims(40)
    assert not layout.isIconHeldByDims(41)
    assert not layout.isIconHeldByDims(263)
