"""
Tests for lib/ui/expressionFormat.py (round 41, p291): a number typed into a length input without its unit stayed
"2.9" instead of "2.90 mm". The expression is set anew once inputChanged is over, Fusion shows a change made inside
inputChanged or validateInputs only in the API, not in the field (measured).
"""

import sys

import pytest

expressionFormat = sys.modules['FusionGridfinityGenerator.lib.ui.expressionFormat']
normalizedExpression = expressionFormat.normalizedExpression


@pytest.mark.parametrize('expression', ['2.9 mm', '2.9', ' 2.9 ', '2.9mm', '+2.9 mm', '2.9 mm '])
def test_a_plain_number_gets_the_formatted_text(expression):
    assert normalizedExpression(expression, 'mm', '2.90 mm') == '2.90 mm'


def test_negative_and_leading_point_numbers_are_plain_numbers():
    assert normalizedExpression('-1', 'mm', '-1.00 mm') == '-1.00 mm'
    assert normalizedExpression('.5', 'mm', '0.50 mm') == '0.50 mm'
    assert normalizedExpression('3.', 'mm', '3.00 mm') == '3.00 mm'


def test_an_already_formatted_expression_is_left_alone():
    # nothing to set, so a set that might call inputChanged again can't come round
    assert normalizedExpression('2.90 mm', 'mm', '2.90 mm') is None


@pytest.mark.parametrize('expression', ['10 + 2', 'a*2', '2.9 * 2', '1 in', '2.9 cm', '', '2.9 mm mm', 'mm', '1e3'])
def test_formulas_other_units_and_empty_stay_as_typed(expression):
    assert normalizedExpression(expression, 'mm', '2.90 mm') is None


def test_other_length_units_take_their_own_unit():
    assert normalizedExpression('1.5 in', 'in', '1.500 in') == '1.500 in'
    assert normalizedExpression('1.5 mm', 'in', '0.059 in') is None


@pytest.mark.parametrize('unitType', ['', 'deg'])
def test_inputs_without_a_length_unit_are_not_formatted(unitType):
    assert normalizedExpression('4.5', unitType, '4.50') is None
