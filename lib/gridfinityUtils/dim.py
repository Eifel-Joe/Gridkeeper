from enum import Enum
import adsk.core

class DimKind(Enum):
    # Fusion gets the plain number, the expression is only kept for combining with other dims
    VALUE = 'value'
    # Fusion gets the expression, so the model follows the parameters it references
    EXPRESSION = 'expression'

class Dim:
    """A number for the generator's own math together with the Fusion expression it stands for.
    The kind decides which of the two is fed to Fusion, combining dims keeps the expression kind if any side has it.
    Values are in Fusion internal units, cm for lengths."""

    def __init__(self, value: float, expression: str, kind: DimKind = DimKind.VALUE, isCompound: bool = False, form: dict | None = None):
        self.value = value
        self.expression = expression
        self.kind = kind
        # compound expressions get parentheses when used as an operand
        self.isCompound = isCompound
        # the linear form of the value (round 45, p480): coefficient per parameter name or per non-linear part (min,
        # max, abs, a product of two parameter-bound dims), keyed by its expression text; the constant part is left
        # out, only whether anything is left matters (dependsOnParameters). None: not known, taken at its kind
        self.form = form

    @staticmethod
    def length(value: float) -> 'Dim':
        return Dim(value, f'{round(value * 10, 6):g} mm', form={})

    @staticmethod
    def asLength(value) -> 'Dim':
        """Dims pass through, plain values become lengths"""
        return value if isinstance(value, Dim) else Dim.length(value)

    @staticmethod
    def number(value: float, expression: str = None) -> 'Dim':
        return Dim(value, expression if expression is not None else f'{value:g}', form={})

    @staticmethod
    def parameter(parameter: adsk.core.Base) -> 'Dim':
        return Dim(parameter.value, parameter.name, DimKind.EXPRESSION, form={parameter.name: 1.0})

    @property
    def isExpression(self) -> bool:
        return self.kind == DimKind.EXPRESSION

    @property
    def dependsOnParameters(self) -> bool:
        """
        Whether the value can change with a parameter (round 45, p480). False when every parameter part cancels, e.g.
        the distance of two points that hang on the same measure: (w * 42 mm + 20 mm - 21 mm) - (w * 42 mm + 20 mm - 41 mm).
        Only identical parts cancel (by their expression text), so it never says constant wrongly; a dim made by hand
        without a form is taken at its kind. Tested in tests/test_dim_linear.py
        """
        if self.form is None:
            return self.isExpression
        return any(abs(coefficient) > _FORM_TOLERANCE for coefficient in self.form.values())

    def asExpression(self) -> 'Dim':
        """Same dim fed to Fusion as its expression, to keep the formula visible in the model"""
        return Dim(self.value, self.expression, DimKind.EXPRESSION, self.isCompound, self.form)

    def abs(self) -> 'Dim':
        expression = f'abs({self.expression})'
        return Dim(abs(self.value), expression, self.kind, form=_part(expression, self))

    @staticmethod
    def min(first: 'Dim', second: 'Dim') -> 'Dim':
        """The smaller of the two, as Fusion's min function, so it changes with the parameters"""
        return Dim._function('min', first, second, min(first.value, second.value))

    @staticmethod
    def max(first: 'Dim', second: 'Dim') -> 'Dim':
        """The larger of the two, as Fusion's max function, so it changes with the parameters"""
        return Dim._function('max', first, second, max(first.value, second.value))

    @staticmethod
    def _function(name: str, first: 'Dim', second: 'Dim', value: float) -> 'Dim':
        kind = DimKind.EXPRESSION if first.isExpression or second.isExpression else DimKind.VALUE
        # Fusion separates function arguments with semicolons
        expression = f'{name}({first.expression}; {second.expression})'
        return Dim(value, expression, kind, form=_part(expression, first, second))

    def _operand(self) -> str:
        return f'({self.expression})' if self.isCompound else self.expression

    @staticmethod
    def _coerce(other, operator: str) -> 'Dim':
        if isinstance(other, Dim):
            return other
        if operator in ('*', '/') and isinstance(other, (int, float)):
            return Dim.number(other)
        # a bare number has no unit, so sums need it spelled out as Dim.length or Dim.number
        raise TypeError(f"Dim {operator} {type(other).__name__} needs a Dim operand")

    @staticmethod
    def _combine(left: 'Dim', right: 'Dim', operator: str, value: float) -> 'Dim':
        kind = DimKind.EXPRESSION if left.isExpression or right.isExpression else DimKind.VALUE
        expression = f'{left._operand()} {operator} {right._operand()}'
        return Dim(value, expression, kind, True, _combineForms(left, right, operator, expression))

    def __add__(self, other):
        other = Dim._coerce(other, '+')
        return Dim._combine(self, other, '+', self.value + other.value)

    def __radd__(self, other):
        other = Dim._coerce(other, '+')
        return Dim._combine(other, self, '+', other.value + self.value)

    def __sub__(self, other):
        other = Dim._coerce(other, '-')
        return Dim._combine(self, other, '-', self.value - other.value)

    def __rsub__(self, other):
        other = Dim._coerce(other, '-')
        return Dim._combine(other, self, '-', other.value - self.value)

    def __mul__(self, other):
        other = Dim._coerce(other, '*')
        return Dim._combine(self, other, '*', self.value * other.value)

    def __rmul__(self, other):
        other = Dim._coerce(other, '*')
        return Dim._combine(other, self, '*', other.value * self.value)

    def __truediv__(self, other):
        other = Dim._coerce(other, '/')
        return Dim._combine(self, other, '/', self.value / other.value)

    def __rtruediv__(self, other):
        other = Dim._coerce(other, '/')
        return Dim._combine(other, self, '/', other.value / self.value)

    def __repr__(self):
        return f'Dim({self.value!r}, {self.expression!r}, {self.kind.name})'

_FORM_TOLERANCE = 1e-9


def _part(expression: str, *operands: Dim) -> dict:
    """The form of a non-linear part: constant when none of its operands depends on a parameter, else the part itself"""
    return {expression: 1.0} if any(operand.dependsOnParameters for operand in operands) else {}


def _scaled(form: dict, factor: float) -> dict:
    return {key: coefficient * factor for (key, coefficient) in form.items()}


def _combineForms(left: Dim, right: Dim, operator: str, expression: str) -> dict | None:
    """Sums and differences add the forms, a product or quotient by a constant scales them, anything else is a part"""
    if left.form is None or right.form is None:
        return None if (left.dependsOnParameters or right.dependsOnParameters) and operator in '+-' else _part(expression, left, right)
    if operator in '+-':
        sign = 1.0 if operator == '+' else -1.0
        form = dict(left.form)
        for (key, coefficient) in right.form.items():
            form[key] = form.get(key, 0.0) + sign * coefficient
        return {key: coefficient for (key, coefficient) in form.items() if abs(coefficient) > _FORM_TOLERANCE}
    if operator == '*' and not right.dependsOnParameters:
        return _scaled(left.form, right.value)
    if operator == '*' and not left.dependsOnParameters:
        return _scaled(right.form, left.value)
    if operator == '/' and not right.dependsOnParameters and right.value != 0:
        return _scaled(left.form, 1.0 / right.value)
    return _part(expression, left, right)


def isZero(value) -> bool:
    """
    Whether a number or a dim is 0 and stays 0 whatever its parameters: an offset nothing needs moving by. A dim made of
    parameters isn't, even when it is 0 now (round 54, p670, a centered bin's offset). Tested in tests/test_dim.py
    """
    if isinstance(value, Dim):
        return value.value == 0 and not value.dependsOnParameters
    return value == 0

def valueOf(value) -> float:
    """The number behind a dim or a plain value, for the generator's own math"""
    return value.value if isinstance(value, Dim) else value

def valueInput(value) -> adsk.core.ValueInput:
    """The only place a dim's kind is looked at, everything handed to Fusion goes through here or applyTo"""
    if isinstance(value, Dim):
        if value.isExpression:
            return adsk.core.ValueInput.createByString(value.expression)
        return adsk.core.ValueInput.createByReal(value.value)
    return adsk.core.ValueInput.createByReal(value)

def lengthExpression(value) -> str:
    """A length as Fusion is to keep it, a dim's formula or the value in mm, whatever the document's units"""
    if isinstance(value, Dim) and value.isExpression:
        return value.expression
    return f"{f'{valueOf(value) * 10:.9f}'.rstrip('0').rstrip('.')} mm"

def lengthInput(value) -> adsk.core.ValueInput:
    """A length for a feature that keeps it as a parameter, a fillet, chamfer or plane offset say, see lengthExpression.
    Given a real, Fusion keeps the length in the document's units to 6 or 7 decimals, in inches it's a hair off and the
    feature's faces don't merge with those they should meet"""
    return adsk.core.ValueInput.createByString(lengthExpression(value))

def applyTo(parameter: adsk.core.Base, value):
    """Drives an existing model parameter, e.g. a sketch dimension, plain values are left as created"""
    if isinstance(value, Dim) and value.isExpression:
        parameter.expression = value.expression
