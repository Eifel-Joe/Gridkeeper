# Sketch constraint check of the shape tests: every sketch a case builds should be fully constrained, otherwise the model
# can break when its parameters change. Sketches of the Cullenect code and of label cases have to be, those of the
# older generator code are only reported. Kept free of Fusion imports so it can be unit tested

STRICT_GENERATORS = {'label'}
STRICT_CASE_MARKER = 'cullenect'

def unconstrainedSketches(sketches) -> list[str]:
    """Names of the sketches that aren't fully constrained, anything with a name and isFullyConstrained"""
    return [sketch.name for sketch in sketches if not sketch.isFullyConstrained]

def constraintFailure(generator: str, caseName: str, names: list[str]) -> str | None:
    """Why the case fails for its loose sketches, none if it doesn't"""
    if len(names) == 0:
        return None
    if generator in STRICT_GENERATORS or STRICT_CASE_MARKER in caseName:
        return f'sketches not fully constrained: {", ".join(names)}'
    return None
