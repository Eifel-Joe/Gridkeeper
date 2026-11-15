"""
Text styles of the labels and how thin their letters come out (p130). Plain math, no Fusion, lengths in cm.

A 0.4 mm nozzle lays lines ~0.42-0.45 mm wide. Arial at the insert's text heights has strokes of 0.4-0.6 mm and the
slicer left parts of the letters out (Nutzer, 15.11.2026). Arial Black has about twice the stroke. The stroke is a fixed
share of the text height, measured in Fusion on 15.11.2026 at 3.5, 4 and 5 mm, one and two lines alike: mean stroke
width (2 x area / perimeter of the letter top faces) per text height, see docs/specs/2026-11-15-runde-11-design.md.
"""

STYLE_REGULAR = 'Regular'
STYLE_BOLD = 'Bold'
STYLE_HEAVY = 'Heavy'
STYLES = [STYLE_REGULAR, STYLE_BOLD, STYLE_HEAVY]
DEFAULT_INSERT_STYLE = STYLE_HEAVY

HEAVY_FONT = 'Arial Black'

# (font name, None for Fusion's default Arial; bold)
_FONTS = {
    STYLE_REGULAR: (None, False),
    STYLE_BOLD: (None, True),
    STYLE_HEAVY: (HEAVY_FONT, False),
}

# mean stroke width per text height, measured, see above
_STROKE_FACTORS = {
    STYLE_REGULAR: 0.11,
    STYLE_BOLD: 0.165,
    STYLE_HEAVY: 0.215,
}

# below this mean stroke a 0.4 mm nozzle leaves parts of the letters out: Arial at 3.5 mm (0.39 mm) lost 35 % of the
# area to a 0.42 mm line, bold at 3.5 mm (0.57 mm) 4 %. Not 0.9 mm (two full lines): two lines of Heavy have 0.76 mm
# and print complete as one wide line, they would always be hinted at
MIN_STROKE = 0.06

# Round 17: no text shrinks below the height where the thinnest stroke of its font is narrower than one line of a
# 0.4 mm nozzle (Nutzer 15.11.2026: 0.4 mm nozzle, Bambu standard profile, Arachne). Measured in Fusion on 15.11.2026
# (job r17_font): the outlines of A-Z a-z 0-9 at 10 mm, stroke across the letter from each point of the outline, the 1 %
# quantile away from sharp corners, see tools/fontStroke.py. Regular 0.903 mm, Bold 1.170 mm, Heavy 1.313 mm
THINNEST_STROKE_FACTORS = {
    STYLE_REGULAR: 0.0903,
    STYLE_BOLD: 0.1170,
    STYLE_HEAVY: 0.1313,
}
NOZZLE_LINE = 0.04

# depth of the descenders (g, j, p, q, y) below the baseline per text height, the text height being the capitals'
# height. Measured with r17_font on "gjpqy", the same 0.294 for Arial and Arial Black
DESCENT_FACTOR = 0.294


def minTextHeight(style: str) -> float:
    """Least height of text of this style whose thinnest stroke still is a nozzle line wide"""
    _check(style)
    return NOZZLE_LINE / THINNEST_STROKE_FACTORS[style]


_notes: list[tuple[str, float, float]] = []


def _check(style: str):
    if style not in _FONTS:
        raise ValueError(f'Unknown text style {style!r}, one of {STYLES}')


def fontAndBold(style: str) -> tuple[str | None, bool]:
    """Font name, None for Fusion's default, and whether the text is bold"""
    _check(style)
    return _FONTS[style]


def styleOfBold(isBold: bool) -> str:
    """The style of a bin label, which only has a bold switch"""
    return STYLE_BOLD if isBold else STYLE_REGULAR


def strokeWidth(style: str, height: float) -> float:
    """Estimated mean stroke width of text of this style and height"""
    _check(style)
    return _STROKE_FACTORS[style] * height


def clearNotes():
    _notes.clear()


def noteText(text: str, style: str, height: float):
    """Remembers the text if its stroke at the height it came out is below MIN_STROKE"""
    stroke = strokeWidth(style, height)
    if stroke < MIN_STROKE - 1e-9:
        _notes.append((text, height, stroke))


def notes() -> list[tuple[str, float, float]]:
    """Text, height and stroke of each text noted since clearNotes"""
    return list(_notes)


def hintText(noted: list[tuple[str, float, float]], suggestHeavy: bool = True) -> str | None:
    """What the command tells about thin text, none without any. suggestHeavy: the dialog offers the Heavy style"""
    if len(noted) == 0:
        return None
    # a bin labels each compartment, the same text there is said once
    sentences = dict.fromkeys(f'"{text}": {height * 10:.1f} mm high, stroke about {stroke * 10:.2f} mm.' for (text, height, stroke) in noted)
    lines = ' '.join(sentences)
    remedy = 'shorten the text, make it wider or use the Heavy style' if suggestHeavy else 'shorten the text or make it wider'
    return f'{lines} Below {MIN_STROKE * 10:g} mm a 0.4 mm nozzle leaves parts out: {remedy}.'


def previewNote(noted: list[tuple[str, float, float]]) -> str:
    """Added to the preview time, a preview shows no message box"""
    return f', text thinner than {MIN_STROKE * 10:g} mm' if len(noted) > 0 else ''
