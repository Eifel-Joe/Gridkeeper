"""
Tests for the measures of the storage box after Pred's parametric Gridfinity Storage Box v1.1 (round 27, p260).
Expected values in mm come from Pred's file, read on 16.11.2026 (fusion-auftraege/r27_pred_walk.log at 5 x 4 x 6,
pred_height.out for the heights 6, 8 and 10, r27_pred_dump.out at 5 x 4 x 5).
"""

import pytest

from tests.test_joint_origin_layout import _load

predBox = _load("predBox")
Dim = predBox.Dim


def _dims(gridX=5, gridY=4, heightU=6):
    parameter = predBox.Dim
    return predBox.PredBoxDims(
        parameter(gridX, "gfBox1_baseWidth", predBox.DimKind.EXPRESSION),
        parameter(gridY, "gfBox1_baseLength", predBox.DimKind.EXPRESSION),
        parameter(heightU, "gfBox1_heightU", predBox.DimKind.EXPRESSION),
    )


def mm(dim):
    return round(dim.value * 10, 6)


def test_outer_size_5x4():
    dims = _dims(5, 4)
    assert (mm(dims.outerWidth), mm(dims.outerLength)) == (230, 188)


def test_outer_size_4x3():
    dims = _dims(4, 3)
    assert (mm(dims.outerWidth), mm(dims.outerLength)) == (188, 146)


@pytest.mark.parametrize("heightU, top, lidCut", [(5, 45.2, 35.2), (6, 52.2, 42.2), (8, 66.2, 56.2), (10, 80.2, 70.2)])
def test_heights_follow_pred(heightU, top, lidCut):
    dims = _dims(heightU=heightU)
    assert mm(dims.bodyTop) == top
    assert mm(dims.lidCut) == lidCut
    assert mm(dims.bottom) == -2.8


def test_middle_planes_5x4x6():
    dims = _dims()
    assert (mm(dims.midX), mm(dims.midY), mm(dims.midZ)) == (115, 94, 24.7)


def test_inner_cut_5x4x6():
    dims = _dims()
    assert (mm(dims.innerCutStart), mm(dims.innerCutDepth)) == (4.15, 42.8)


@pytest.mark.parametrize("gridX, width", [(4, 28.5), (5, 70.5), (6, 85)])
def test_label_width(gridX, width):
    assert mm(_dims(gridX=gridX).labelWidth) == width


def test_back_cutout_width():
    assert mm(_dims().backCutoutWidth) == 66


@pytest.mark.parametrize("heightU, depth", [(5, 36), (6, 43), (10, 43)])
def test_catch_slide_depth(heightU, depth):
    """Pred's slot is 43 mm long from 6 mm below the top; at height 5 it would break through the floor, so it ends
    6 mm above the bottom there as at height 6 (decision 1 of the plan)"""
    dims = _dims(heightU=heightU)
    assert mm(dims.catchSlideDepth) == depth
    slotEnd = dims.bodyTop.value - 0.6 - dims.catchSlideDepth.value
    assert round((slotEnd - dims.bottom.value) * 10, 6) >= 6


@pytest.mark.parametrize("heightU, edge", [(5, 8.7), (6, 12.2), (8, 19.2), (10, 26.2)])
def test_holder_bottom_moves_with_the_height(heightU, edge):
    assert mm(_dims(heightU=heightU).holderBottom) == edge


def test_moving_edge_clears_lower_groove_at_height_5():
    dims = _dims(heightU=5)
    assert round(dims.holderBottom.value * 10 - predBox.PRED["lowerGrooveTop"] * 10, 6) == 0.5


def test_stacking_joint_heights():
    bottom, top = predBox.stackingJointZ(_dims())
    assert (mm(bottom), mm(top)) == (-2.8, 52.2)


def test_expressions_reference_parameters():
    dims = _dims()
    assert "gfBox1_baseWidth" in dims.outerWidth.expression and dims.outerWidth.isExpression
    assert "gfBox1_baseLength" in dims.outerLength.expression
    assert "gfBox1_heightU" in dims.bodyTop.expression
    assert dims.labelWidth.expression.startswith("min(")
    assert dims.catchSlideDepth.expression.startswith("min(")


@pytest.mark.parametrize("heightU, radius", [(5, 0.01), (6, 3.75), (10, 3.75)])
def test_holder_top_blend_is_square_at_height_5(heightU, radius):
    """Nutzer 16.11.2026, "Rundung weglassen (2)": at height 5 the top rounding of the handle holders would reach 1.3 mm
    past the lid joint, there it is square (0.01 mm), from height 6 Pred's 3.75 mm; as an expression, so a parameter
    change between 5 and 6 follows"""
    blend = _dims(heightU=heightU).holderTopBlend
    assert mm(blend) == radius
    assert "gfBox1_heightU" in blend.expression and blend.expression.startswith("max(")
