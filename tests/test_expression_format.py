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


# ---------------------------------------------------------------------------
# The custom event that sets the expression once inputChanged is over
# ---------------------------------------------------------------------------

class _Units:
    def formatInternalValue(self, value, unitType, showUnits):
        assert showUnits is True
        return f'{value * 10:.2f} {unitType}'


class _Product:
    unitsManager = _Units()


class _App:
    def __init__(self):
        self.calls = []
        self.activeProduct = _Product()

    def registerCustomEvent(self, eventId):
        self.calls.append(('register', eventId))
        return object()

    def unregisterCustomEvent(self, eventId):
        self.calls.append(('unregister', eventId))
        return True

    def fireCustomEvent(self, eventId, info=''):
        self.calls.append(('fire', eventId))
        return True


class _LengthInput:
    def __init__(self, expression, value=0.29, unitType='mm', isValid=True, isValidExpression=True):
        self.expression = expression
        self.value = value
        self.unitType = unitType
        self.isValid = isValid
        self.isValidExpression = isValidExpression
        self.sets = 0

    def __setattr__(self, name, value):
        if name == 'expression' and hasattr(self, 'sets'):
            self.sets += 1
        object.__setattr__(self, name, value)


@pytest.fixture
def app(monkeypatch):
    fake = _App()
    monkeypatch.setattr(expressionFormat, 'app', fake)
    expressionFormat.pendingInputs.clear()
    yield fake
    expressionFormat.pendingInputs.clear()


def test_start_registers_the_event_anew_and_stop_removes_it(app):
    expressionFormat.start()
    assert app.calls == [('unregister', expressionFormat.NORMALIZE_EVENT_ID), ('register', expressionFormat.NORMALIZE_EVENT_ID)]
    expressionFormat.pendingInputs.append(_LengthInput('2.9 mm'))
    app.calls.clear()
    expressionFormat.stop()
    assert app.calls == [('unregister', expressionFormat.NORMALIZE_EVENT_ID)]
    assert expressionFormat.pendingInputs == []


def test_request_keeps_the_input_once_and_fires_the_event(app):
    lengthInput = _LengthInput('2.9 mm')
    expressionFormat.request(lengthInput)
    expressionFormat.request(lengthInput)
    assert expressionFormat.pendingInputs == [lengthInput]
    assert app.calls == [('fire', expressionFormat.NORMALIZE_EVENT_ID)] * 2


def test_the_event_sets_the_formatted_expression(app):
    lengthInput = _LengthInput('2.9 mm')
    expressionFormat.request(lengthInput)
    expressionFormat.normalize_custom_event(None)
    assert lengthInput.expression == '2.90 mm'
    assert expressionFormat.pendingInputs == []


def test_the_event_sets_nothing_that_needs_no_change(app):
    formatted = _LengthInput('2.90 mm')
    formula = _LengthInput('10 + 2', value=1.2)
    for lengthInput in (formatted, formula):
        expressionFormat.request(lengthInput)
    expressionFormat.normalize_custom_event(None)
    assert (formatted.sets, formula.sets) == (0, 0)


def test_the_event_skips_closed_dialogs_and_invalid_expressions(app):
    closed = _LengthInput('2.9 mm', isValid=False)
    invalid = _LengthInput('2.9 mm', isValidExpression=False)
    for lengthInput in (closed, invalid):
        expressionFormat.request(lengthInput)
    expressionFormat.normalize_custom_event(None)
    assert (closed.sets, invalid.sets) == (0, 0)


def test_an_error_on_one_input_leaves_the_others_formatted(app):
    class _Broken(_LengthInput):
        @property
        def unitType(self):
            raise RuntimeError('dialog gone')

        @unitType.setter
        def unitType(self, value):
            pass

    broken = _Broken('2.9 mm')
    fine = _LengthInput('2.9 mm')
    expressionFormat.request(broken)
    expressionFormat.request(fine)
    expressionFormat.normalize_custom_event(None)
    assert fine.expression == '2.90 mm'
    assert expressionFormat.pendingInputs == []


# ---------------------------------------------------------------------------
# Review r41: the formatted text is rounded to the display precision, it must not change the value
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(('expression', 'formatted'), [('1.125', '1.13 mm'), ('0.25', '0.3 mm'), ('2.999 mm', '3.00 mm')])
def test_more_decimals_than_shown_stay_as_typed(expression, formatted):
    assert normalizedExpression(expression, 'mm', formatted) is None


def test_trailing_zeros_and_a_bare_point_keep_the_value():
    assert normalizedExpression('2.50', 'mm', '2.5 mm') == '2.5 mm'
    assert normalizedExpression('3.', 'mm', '3.00 mm') == '3.00 mm'


def test_a_formatted_text_fusion_wont_take_is_set_back(app):
    class _Refusing(_LengthInput):
        def __setattr__(self, name, value):
            _LengthInput.__setattr__(self, name, value)
            if name == 'expression' and value == '2.90 mm':
                object.__setattr__(self, 'isValidExpression', False)

    lengthInput = _Refusing('2.9 mm')
    expressionFormat.request(lengthInput)
    expressionFormat.normalize_custom_event(None)
    assert lengthInput.expression == '2.9 mm'
