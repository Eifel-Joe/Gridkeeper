"""
Tests for the colors of label text and symbols (p86): the choices of the dialogs, a custom color, the name of the
appearance and which library appearance it is copied from.
"""

import os
import importlib.util


def _load():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(project_root, "lib", "gridfinityUtils", "labelColors.py")
    spec = importlib.util.spec_from_file_location("labelColors", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


colors = _load()


def test_choices_start_with_none_and_end_with_custom():
    assert colors.CHOICES[0] == colors.NO_COLOR_CHOICE == 'None'
    assert colors.CHOICES[-1] == colors.CUSTOM_CHOICE == 'Custom'
    assert 'Black' in colors.CHOICES and 'White' in colors.CHOICES and 'Red' in colors.CHOICES


def test_color_of_a_choice():
    assert colors.colorOf('None', '') == ''
    assert colors.colorOf('Black', '#123456') == '#000000'
    assert colors.colorOf('Custom', '#a0B1c2') == '#A0B1C2'
    assert colors.colorOf('Custom', ' a0b1c2 ') == '#A0B1C2'


def test_invalid_custom_color():
    assert colors.colorOf('Custom', 'red') is None
    assert colors.colorOf('Custom', '#12345') is None
    assert colors.colorOf('Custom', '') is None
    assert colors.colorProblem('Custom', 'red') == 'The custom color is #rrggbb, e.g. #D02020'
    assert colors.colorProblem('Custom', '#d02020') is None
    assert colors.colorProblem('Red', 'nonsense') is None


def test_unknown_choice_counts_as_none():
    assert colors.colorOf('Purple', '') == ''


def test_choice_of_a_color_goes_back():
    assert colors.choiceOf('') == ('None', '')
    assert colors.choiceOf('#000000') == ('Black', '')
    assert colors.choiceOf('#A0B1C2') == ('Custom', '#A0B1C2')


def test_valid_color():
    assert colors.isColor('') is True
    assert colors.isColor('#00ff00') is True
    assert colors.isColor('00ff00') is False
    assert colors.isColor('#00ff0') is False


def test_appearance_name_is_plain_ascii():
    # Fusion refuses some characters in appearance names, # among them
    assert colors.appearanceName('#d02020') == 'Gridfinity label D02020'


def test_rgb():
    assert colors.rgb('#D02010') == (208, 32, 16)


def test_base_appearance_rank_prefers_plastic_in_any_language():
    # the libraries are in the user's language, p31: there is no "Plastic" in a German Fusion
    assert colors.baseRank('Plastic - Matte (White)') < colors.baseRank('Paint - Enamel Glossy (White)')
    assert colors.baseRank('Kunststoff - Matt (Weiß)') < colors.baseRank('Lack - Emaille glänzend (Weiß)')
    assert colors.baseRank('Plastic - Matte (White)') <= colors.baseRank('Plastic - Glossy (White)')
    assert colors.baseRank('Lack') == colors.baseRank('Anything else')
