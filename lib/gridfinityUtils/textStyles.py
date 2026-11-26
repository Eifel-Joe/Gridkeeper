"""
Text styles of the labels and how thin their letters come out (p130). Plain math, no Fusion, lengths in cm.

A 0.4 mm nozzle lays lines ~0.42-0.45 mm wide. Arial at the insert's text heights has strokes of 0.4-0.6 mm and the
slicer left parts of the letters out (15.11.2026). How low a text of each style still prints is measured on its
thinnest stroke, see minTextHeight (round 17). The hint on thin text follows the same limit (round 21, p232).
"""

STYLE_REGULAR = 'Regular'  # tr-value
STYLE_BOLD = 'Bold'  # tr-value
STYLE_HEAVY = 'Heavy'  # tr-value
STYLES = [STYLE_REGULAR, STYLE_BOLD, STYLE_HEAVY]
DEFAULT_INSERT_STYLE = STYLE_HEAVY

HEAVY_FONT = 'Arial Black'

# (font name, None for Fusion's default Arial; bold)
_FONTS = {
    STYLE_REGULAR: (None, False),
    STYLE_BOLD: (None, True),
    STYLE_HEAVY: (HEAVY_FONT, False),
}

# Round 21, p232: the hint on thin text came from an estimated mean stroke under 0.6 mm (round 11), a second number
# beside the measured print limit: Heavy was hinted only below 2.79 mm, its limit is 3.05 mm. Decided on the test day
# (question 2): the hint from the print limit on, minTextHeight is the one source now

# Round 17: no text shrinks below the height where the thinnest stroke of its font is narrower than one line of a
# 0.4 mm nozzle (15.11.2026: 0.4 mm nozzle, Bambu standard profile, Arachne). Measured in Fusion on 15.11.2026
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


def fittedHeight(labelHeight: float, widthHeight: float, style: str) -> tuple[float, bool]:
    """Height of a bin label text and whether it runs over the label (round 19, p181). labelHeight is what the tab
    allows, widthHeight where the text fills the width. The text shrinks for the width, but not below the floor of
    its style; a tab lower than the floor keeps its own height (Hauptsitzung 16.11.2026: the floor only holds the shrink
    for the width). Over the label it would print past the tab or the bin, the dialog refuses it, see overflowProblem"""
    floor = min(labelHeight, minTextHeight(style))
    height = min(labelHeight, max(widthHeight, floor))
    return (height, widthHeight < height - 1e-9)


def overflowProblem(text: str, height: float, style: str) -> str:
    """Why a bin label isn't built: its text doesn't fit even at the least height, or on a tab lower than that at the
    tab's own height (review round 19)"""
    reason = 'as high as its tab lets it be' if height < minTextHeight(style) - 1e-9 else 'the least height a 0.4 mm nozzle prints'
    return f'"{text}" doesn\'t fit the label even at {height * 10:.1f} mm, {reason}. Shorten it or make the bin wider.'


_notes: list[tuple[str, float, str]] = []


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


def clearNotes():
    _notes.clear()


def noteText(text: str, style: str, height: float):
    """Remembers the text if the height it came out at is below the print limit of its style, see minTextHeight"""
    if height < minTextHeight(style) - 1e-9:
        _notes.append((text, height, style))


def notes() -> list[tuple[str, float, str]]:
    """Text, height and style of each text noted since clearNotes"""
    return list(_notes)


def hintText(noted: list[tuple[str, float, str]], suggestHeavy: bool = True, isBinLabel: bool = False) -> str | None:
    """What the command tells about thin text, none without any. suggestHeavy: the dialog offers the Heavy style.
    isBinLabel: a bin label is below the limit only on a tab lower than it, a text too wide isn't built (round 19), a
    wider tab helps there, Bold for Regular (review round 21)"""
    if len(noted) == 0:
        return None
    # a bin labels each compartment, the same text there is said once
    sentences = dict.fromkeys(
        f'"{text}": {height * 10:.1f} mm high, below the {minTextHeight(style) * 10:.2f} mm a 0.4 mm nozzle prints in {style}.'
        for (text, height, style) in noted
    )
    lines = ' '.join(sentences)
    if isBinLabel:
        remedy = 'Make the tab wider or use the Bold style' if any(style == STYLE_REGULAR for (_, _, style) in noted) else 'Make the tab wider'
    else:
        remedy = 'Shorten the text, make it wider or use the Heavy style' if suggestHeavy else 'Shorten the text or make it wider'
    return f'{lines} {remedy}.'


def previewNote(noted: list[tuple[str, float, str]]) -> str:
    """Added to the preview time, a preview shows no message box"""
    return ', text below the print limit' if len(noted) > 0 else ''
