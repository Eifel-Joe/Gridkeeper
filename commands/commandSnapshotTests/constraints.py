# Sketch constraint check of the shape tests: every sketch a case builds should be fully constrained, otherwise the model
# can break when its parameters change. Sketches of the Cullenect code and of label cases have to be, those of the
# older generator code are only reported. Kept free of Fusion imports so it can be unit tested

# boxes after Pred are built fully constrained from the start (round 27, Jörg: every sketch fully constrained)
STRICT_GENERATORS = {'label', 'box'}
STRICT_CASE_MARKER = 'cullenect'

def _isBound(entity) -> bool:
    return entity.isFullyConstrained or entity.isFixed

def _isBoundButForLiveText(sketch) -> bool:
    """Fusion never reports a sketch with live text as fully constrained, however its box is dimensioned or fixed
    (spike in the Cullenect label spec). Jörg chose live text for the insert on 14.11.2026 (p50), so such a sketch
    counts as constrained when every curve and point in it, the text box or baseline included, is bound and only the
    text isn't"""
    if not any(True for _ in sketch.sketchTexts):
        return False
    return all(_isBound(curve) for curve in sketch.sketchCurves) and all(_isBound(point) for point in sketch.sketchPoints)

def unconstrainedSketches(sketches) -> list[str]:
    """Names of the sketches that aren't fully constrained, anything with a name and isFullyConstrained, a sketch with
    live text also with sketchTexts, sketchCurves and sketchPoints"""
    return [sketch.name for sketch in sketches if not sketch.isFullyConstrained and not _isBoundButForLiveText(sketch)]

def constraintFailure(generator: str, caseName: str, names: list[str]) -> str | None:
    """Why the case fails for its loose sketches, none if it doesn't"""
    if len(names) == 0:
        return None
    if generator in STRICT_GENERATORS or STRICT_CASE_MARKER in caseName:
        return f'sketches not fully constrained: {", ".join(names)}'
    return None
