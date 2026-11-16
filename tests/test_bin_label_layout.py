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


def test_letters_stand_on_the_bottom_of_a_taller_icon():
    # round 22, upstream f1cb49b: the icon keeps its full size, smaller letters stand on its bottom, the icon centered
    result = placement(hasIcon=True, textHeight=0.3, iconHeight=0.7)
    assert result.iconMinFromBack == approx(LENGTH / 2 + 0.7 / 2)
    assert result.baselineFromBack == approx(result.iconMinFromBack)
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


# p60: the label and its Cullenect socket span the overlap of the tab and its compartment, as an expression, so a
# changed base width that turns which of the two ends first is followed

def test_span_is_the_overlap_of_tab_and_compartment():
    (low, high) = layout.labelSpan(Dim.length(1.0), Dim.length(8.0), Dim.length(2.0), Dim.length(4.0))
    assert (low.value, high.value) == (2.0, 6.0)
    (low, high) = layout.labelSpan(Dim.length(3.0), Dim.length(2.0), Dim.length(2.0), Dim.length(4.0))
    assert (low.value, high.value) == (3.0, 5.0)


def test_span_follows_both_as_expressions():
    tabX = Dim(1.0, "gfBin1_baseWidth * 0.25", DimKind.EXPRESSION, True)
    compartmentX = Dim(2.0, "gfBin1_baseWidth / 2", DimKind.EXPRESSION, True)
    (low, high) = layout.labelSpan(tabX, Dim.length(8.0), compartmentX, Dim.length(4.0))
    assert low.isExpression and high.isExpression
    assert low.expression.startswith("max(") and "gfBin1_baseWidth * 0.25" in low.expression and "gfBin1_baseWidth / 2" in low.expression
    assert high.expression.startswith("min(")


# round 17, p180: points of each Cullenect symbol on a bin label after p51 and the time to hold it by dims, measured
# in Fusion 15.11.2026 (job r17_dims, the limit raised for the run). Under 2 s they take the dims (spec)
MEASURED_HELD_SECONDS = {
    'tnut-2': (26, 1.30), 'tnut-1': (32, 1.77), 'nut-square': (34, 1.75), 'nut': (36, 1.92),
    'magnet': (50, 3.04), 'crimp-spade-open': (57, 3.75), 'washer-locking': (58, 4.33), 'washer': (60, 4.45),
    'crimp-fork-open': (69, 6.18), 'crimp-receptacle-open': (76, 6.29), 'threaded-insert': (76, 5.55),
    'crimp-ring-open': (85, 7.50), 'crimp-spade-closed': (96, 9.79), 'nut-nylon': (96, 9.11),
    'crimp-fork-closed': (108, 12.84), 'crimp-receptacle-closed': (115, 14.11), 'crimp-ring-closed': (120, 15.19),
    'crimp-butt-splice': (122, 15.08),
}


def test_measured_symbols_held_under_2s_take_the_dims():
    fast = [name for (name, (points, seconds)) in MEASURED_HELD_SECONDS.items() if seconds < 2]
    assert fast == ['tnut-2', 'tnut-1', 'nut-square', 'nut']
    assert all(layout.isIconHeldByDims(MEASURED_HELD_SECONDS[name][0]) for name in fast)


def test_measured_slow_symbols_are_moved():
    slow = [points for (points, seconds) in MEASURED_HELD_SECONDS.values() if seconds >= 2]
    assert not any(layout.isIconHeldByDims(points) for points in slow)


# round 19, p181: a label text changed since the bin was built is fitted anew by a rebuild, not set by its parameter

BUILT = {"labelText": "Schrauben", "binHeight": 3, "compartmentPockets": [{"label": "M3"}, {"label": ""}]}


def test_text_changed_by_parameter_rebuilds():
    assert layout.textChangedSinceBuild(BUILT, {**BUILT, "labelText": "Schrauben M4x20"})


def test_compartment_label_changed_rebuilds():
    assert layout.textChangedSinceBuild(BUILT, {**BUILT, "compartmentPockets": [{"label": "M3x20"}, {"label": ""}]})


def test_unchanged_text_keeps_the_parameter_edit():
    assert not layout.textChangedSinceBuild(BUILT, {**BUILT, "binHeight": 4})


def test_a_config_without_compartments_compares_the_bin_label():
    assert not layout.textChangedSinceBuild({"labelText": "A"}, {"labelText": "A", "compartmentPockets": []})


def test_empty_compartment_labels_filled_in_by_the_dialog_are_no_change():
    # review round 19 (I2): a tag without pockets, the dialog fills the grid with empty ones; nothing is labelled
    built = {"labelText": "A", "compartmentPockets": []}
    filled = {"labelText": "A", "compartmentPockets": [{"x": 0, "y": 0, "label": ""}, {"x": 1, "y": 0, "label": ""}]}
    assert not layout.textChangedSinceBuild(built, filled)
    assert not layout.textChangedSinceBuild({"labelText": "A"}, filled)
    assert not layout.textChangedSinceBuild(built, {**filled, "compartmentPockets": [{"x": 0, "y": 0, "label": None}]})


def test_a_compartment_label_is_keyed_by_its_cell():
    built = {"labelText": "", "compartmentPockets": [{"x": 0, "y": 0, "label": "M3"}]}
    moved = {"labelText": "", "compartmentPockets": [{"x": 1, "y": 0, "label": "M3"}]}
    assert layout.textChangedSinceBuild(built, moved)


def test_a_shared_text_takes_the_edited_parameter():
    # review round 19 (I1): two compartments show the bin label, each by a parameter of its own; one edited in Fusion
    # wins over the other, unchanged one, whichever comes last
    assert layout.sharedText("Bolzen", ["Bolzen M4", "Bolzen"]) == "Bolzen M4"
    assert layout.sharedText("Bolzen", ["Bolzen", "Bolzen M4"]) == "Bolzen M4"
    assert layout.sharedText("Bolzen", ["Bolzen", "Bolzen"]) == "Bolzen"
    assert layout.sharedText("Bolzen", []) == "Bolzen"



# round 22, p13 (Nutzer: "Wie das Original", upstream f1cb49b by Le0Michine): the label icon keeps its full size, as tall
# as the letters can be at most, only the text shrinks to the width left after it

RATIO = const.BIN_LABEL_TEXT_HEIGHT_RATIO


def test_icon_keeps_its_full_size_with_a_long_text():
    fit = layout.fitBinLabel(8.0, 1.1, 1.0, 20.0, 1.0, 'Bold')
    assert fit.iconSize == approx(1.1 * RATIO)
    width = 8.0 - 1.1 * RATIO - GAP
    assert fit.textHeight == approx(1.1 * min(1.1 * RATIO / 1.0, width / 20.0))
    assert fit.lettersHeight == approx(1.0 * fit.textHeight / 1.1)
    assert not fit.overflows


def test_a_wide_icon_is_limited_by_the_label_width():
    fit = layout.fitBinLabel(2.0, 1.1, 4.0, 0.5, 1.0, 'Bold')
    assert fit.iconSize == approx(min(1.1 * RATIO, 2.0 / 4.0))


def test_a_short_text_keeps_the_height_the_tab_allows():
    fit = layout.fitBinLabel(8.0, 1.1, 1.0, 2.0, 1.0, 'Bold')
    assert fit.textHeight == approx(1.1 * 1.1 * RATIO)
    assert fit.iconSize == approx(1.1 * RATIO)


def test_text_alone_fills_the_width():
    fit = layout.fitBinLabel(3.0, 1.1, None, 5.0, 1.0, 'Bold')
    assert fit.textHeight == approx(1.1 * 3.0 / 5.0)
    assert not fit.overflows


def test_a_text_too_long_beside_the_icon_overflows_at_the_floor():
    # the full size icon takes room, the text left beside it can't reach the print limit
    fit = layout.fitBinLabel(4.0, 1.1, 1.0, 40.0, 1.0, 'Bold')
    assert fit.overflows
    assert fit.textHeight == approx(0.04 / 0.1170)
