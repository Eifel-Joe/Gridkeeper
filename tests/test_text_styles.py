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
