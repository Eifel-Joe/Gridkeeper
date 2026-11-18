"""
Round 45 (p480, p296): a Dim knows whether its value depends on parameters at all. Two sketch points that hang on the
same measure (e.g. both at width * 42 mm + 20 mm minus a fixed offset) have a distance that never changes; the box's
WorldSketch then leaves that dimension at its value instead of giving it an expression (129 of 215 per box,
fusion-auftraege/r45_probe.log). Only identical parts cancel, so a dim never claims to be constant when it isn't.
"""

from tests.test_dim import Dim, dim, _FakeParameter

W = Dim.parameter(_FakeParameter("gfBox1_baseWidth", 5))
H = Dim.parameter(_FakeParameter("gfBox1_heightU", 6))
L = Dim.parameter(_FakeParameter("gfBox1_baseLength", 4))


def mm(value):
    return Dim.length(value / 10)


def outer():
    return W * mm(42) + mm(20)


def test_plain_dims_do_not_depend_on_parameters():
    assert not Dim.length(0.7).dependsOnParameters
    assert not Dim.number(3).dependsOnParameters
    assert not (mm(3) + mm(4) * 2).dependsOnParameters


def test_a_parameter_does():
    assert W.dependsOnParameters
    assert (W * mm(42) - mm(21)).dependsOnParameters
    assert (W * 2 - H * 2).dependsOnParameters


def test_the_same_measure_cancels_in_a_difference():
    assert not ((outer() - mm(21)) - (outer() - mm(41))).dependsOnParameters
    assert not (W - W).dependsOnParameters
    assert not (W / 2 - W * 0.5).dependsOnParameters
    assert not (outer() / 2 + mm(3) - (outer() / 2 - mm(4))).dependsOnParameters


def test_scaling_by_a_plain_dim_keeps_the_form():
    assert not (W * mm(42) - mm(42) * W).dependsOnParameters
    assert not ((W * mm(42)) / Dim.number(2) - W * mm(21)).dependsOnParameters


def test_abs_cancels_only_when_its_inside_does_or_the_same_abs_is_taken_away():
    assert not ((outer() - mm(21)) - (outer() - mm(41))).abs().dependsOnParameters
    assert (W - mm(1)).abs().dependsOnParameters
    a = (W * mm(42) - mm(1)).abs()
    assert not (a - (W * mm(42) - mm(1)).abs()).dependsOnParameters


def test_min_and_max_cancel_only_when_identical():
    a, b, c = outer() - mm(159.5), mm(85), L * mm(42)
    assert not (Dim.min(a, b) / 2 - Dim.min(a, b) / 2).dependsOnParameters
    assert (Dim.min(a, b) - Dim.min(a, c)).dependsOnParameters
    assert not (Dim.max(mm(1), mm(2)) + W - W).dependsOnParameters


def test_a_product_of_two_parameters_is_one_part_of_its_own():
    assert not (W * H - W * H).dependsOnParameters
    # another spelling of the same product is not recognised: on the safe side, it keeps its expression
    assert (W * H - H * W).dependsOnParameters
    assert (W / H).dependsOnParameters


def test_kind_and_expression_stay_as_they_were():
    difference = (outer() - mm(21)) - (outer() - mm(41))
    assert difference.isExpression
    assert difference.expression == "(((gfBox1_baseWidth * 42 mm) + 20 mm) - 21 mm) - (((gfBox1_baseWidth * 42 mm) + 20 mm) - 41 mm)"
    assert abs(difference.value - 2.0) < 1e-12
    assert difference.abs().expression == f"abs({difference.expression})"
    assert W.asExpression().dependsOnParameters
    assert not mm(3).asExpression().dependsOnParameters


def test_a_dim_made_by_hand_counts_as_depending_when_it_is_an_expression():
    """Dims built with the constructor (no form known) are taken at their kind: an expression may depend"""
    assert dim.Dim(1.0, "gfBin1_x", dim.DimKind.EXPRESSION).dependsOnParameters
    assert not dim.Dim(1.0, "1 mm").dependsOnParameters
