"""
Tests for the text styles of the labels (p130): font and bold of each style, the stroke width estimated from the text
height, and the notes and hint for text too thin for a 0.4 mm nozzle.
"""

import os
import importlib.util

import pytest
from pytest import approx


def _load():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(project_root, "lib", "gridfinityUtils", "textStyles.py")
    spec = importlib.util.spec_from_file_location("textStyles", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


styles = _load()


@pytest.fixture(autouse=True)
def _clear():
    styles.clearNotes()
    yield
    styles.clearNotes()


def test_font_and_bold_of_each_style():
    assert styles.STYLES == ['Regular', 'Bold', 'Heavy']
    assert styles.DEFAULT_INSERT_STYLE == 'Heavy'
    assert styles.fontAndBold('Regular') == (None, False)
    assert styles.fontAndBold('Bold') == (None, True)
    assert styles.fontAndBold('Heavy') == ('Arial Black', False)


def test_unknown_style_raises():
    with pytest.raises(ValueError):
        styles.fontAndBold('Italic')


def test_style_of_bold():
    assert styles.styleOfBold(True) == 'Bold'
    assert styles.styleOfBold(False) == 'Regular'


def test_stroke_width_factors():
    assert styles.strokeWidth('Regular', 0.5) == approx(0.055)
    assert styles.strokeWidth('Bold', 0.5) == approx(0.0825)
    assert styles.strokeWidth('Heavy', 0.5) == approx(0.1075)
    assert styles.MIN_STROKE == approx(0.06)


def test_two_line_heavy_gets_no_note():
    styles.noteText('Hex key', 'Heavy', 0.35)
    assert styles.notes() == []


def test_shrunk_regular_gets_a_note():
    styles.noteText('Hex key', 'Regular', 0.35)
    [(text, height, stroke)] = styles.notes()
    assert text == 'Hex key'
    assert height == approx(0.35)
    assert stroke == approx(0.0385)


def test_clear_notes():
    styles.noteText('Hex key', 'Regular', 0.35)
    styles.clearNotes()
    assert styles.notes() == []


def test_hint_text():
    assert styles.hintText([('Hex key', 0.2, 0.022)]) == (
        '"Hex key": 2.0 mm high, stroke about 0.22 mm. Below 0.6 mm a 0.4 mm nozzle leaves parts out: '
        'shorten the text, make it wider or use the Heavy style.'
    )


def test_hint_text_of_two_lines():
    hint = styles.hintText([('5mm', 0.2, 0.022), ('Hex key', 0.2, 0.022)])
    assert hint.count('Below 0.6 mm') == 1
    assert '"5mm": 2.0 mm high' in hint and '"Hex key": 2.0 mm high' in hint


def test_no_hint_without_notes():
    assert styles.hintText([]) is None


def test_preview_note():
    # shown after the preview time instead of a message box
    assert styles.previewNote([]) == ''
    assert styles.previewNote([('Hex key', 0.2, 0.022)]) == ', text thinner than 0.6 mm'


def test_hint_text_for_a_bin_label_offers_no_heavy_style():
    # the bin dialog only has a bold switch
    assert styles.hintText([('Schrauben M4', 0.35, 0.058)], suggestHeavy=False) == (
        '"Schrauben M4": 3.5 mm high, stroke about 0.58 mm. Below 0.6 mm a 0.4 mm nozzle leaves parts out: '
        'shorten the text or make it wider.'
    )


def test_hint_text_names_a_repeated_text_once():
    # a bin labels each compartment, the same text on all of them is one sentence
    hint = styles.hintText([('Schrauben M4', 0.35, 0.058)] * 8, suggestHeavy=False)
    assert hint.count('"Schrauben M4"') == 1


def test_note_threshold():
    # Heavy at 0.279 cm text height is just below 0.6 mm stroke, at 0.28 cm just above
    styles.noteText('a', 'Heavy', 0.279)
    styles.noteText('b', 'Heavy', 0.28)
    assert [text for (text, _, _) in styles.notes()] == ['a']


@pytest.mark.parametrize('style', ['Regular', 'Bold', 'Heavy'])
def test_min_text_height_keeps_a_04mm_stroke(style):
    # round 17: at the least height the thinnest stroke of the font is one 0.4 mm line
    assert styles.THINNEST_STROKE_FACTORS[style] * styles.minTextHeight(style) == approx(0.04)


def test_descenders_reach_below_the_baseline():
    # measured in Fusion 15.11.2026 on "gjpqy", the same for all three styles, the text height is the capitals' height
    assert styles.DESCENT_FACTOR == approx(0.294, abs=1e-3)


# --- round 19, p181: bin label text fitted to the width, not below the floor

def test_short_text_keeps_the_label_height():
    assert styles.fittedHeight(0.5, 0.8, 'Bold') == (approx(0.5), False)


def test_long_text_shrinks_to_the_width_above_the_floor():
    assert styles.fittedHeight(0.5, 0.4, 'Bold') == (approx(0.4), False)


def test_long_text_stops_at_the_floor():
    (height, overflows) = styles.fittedHeight(0.5, 0.2, 'Regular')
    assert height == approx(styles.minTextHeight('Regular'))
    assert overflows


def test_label_height_below_the_floor_stays():
    # a small tab gives letters lower than the floor, they stay, only the shrink for the width is held at the floor
    assert styles.fittedHeight(0.3, 0.8, 'Regular') == (approx(0.3), False)
    assert styles.fittedHeight(0.3, 0.2, 'Regular') == (approx(0.3), True)


def test_overflow_problem_names_text_and_floor():
    assert styles.overflowProblem('Schrauben M4x20 DIN 912', 0.443) == (
        '"Schrauben M4x20 DIN 912" doesn\'t fit the label even at 4.4 mm, the least height a 0.4 mm nozzle prints. '
        'Shorten it or make the bin wider.'
    )
