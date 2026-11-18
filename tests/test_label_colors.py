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
    # names as a German Fusion has them, 14.11.2026
    assert colors.baseRank('Kunststoff - matt (Weiß)') < colors.baseRank('Kunststoff - glänzend (Weiß)')
    assert colors.baseRank('Kunststoff - glänzend (Weiß)') < colors.baseRank('3D Esche - Halbglanz')
    assert colors.baseRank('Kunststoff - matt (Weiß)') < colors.baseRank('Kunststoff - durchscheinend matt (Weiß)')
    assert colors.baseRank('Plastic - Matte (White)') <= colors.baseRank('Plastic - Glossy (White)')
    assert colors.baseRank('Lack') == colors.baseRank('Anything else')


def test_base_candidates_prefer_the_appearance_library():
    # a user's favorites held "3D Esche", a wood that came first while the library's plastics were passed over (p86)
    libraries = [('FAV', ['3D Esche - Halbglanz', 'ABS (red)']), (colors.APPEARANCE_LIBRARY_ID, ['Glas - klar', 'Kunststoff - glänzend (Rot)', 'Kunststoff - matt (Rot)'])]
    order = colors.baseCandidates(libraries)
    assert order[0] == (1, 2)
    assert order[1] == (1, 1)
    assert order.index((0, 0)) > order.index((1, 0))


def test_dialog_color_keeps_an_invalid_custom_text_so_it_locks_ok():
    # review round 10: Custom with an empty field passed as no color in the label dialog, the bin dialog locked OK
    assert colors.dialogColor('Red', '') == '#D02020'
    assert colors.dialogColor('None', 'xyz') == ''
    assert colors.dialogColor('Custom', 'd02020') == '#D02020'
    assert colors.isColor(colors.dialogColor('Custom', '')) is False
    assert colors.isColor(colors.dialogColor('Custom', 'xyz')) is False


def test_label_color_applies_only_to_a_label_there_is():
    # review round 10: a remembered color went into the settings of a bin with a Cullenect socket or without tab
    assert colors.labelColorFor('#D02020', True, False) == '#D02020'
    assert colors.labelColorFor('#D02020', False, False) == ''
    assert colors.labelColorFor('#D02020', True, True) == ''


def test_a_bin_has_a_label_as_the_builder_makes_one():
    # review round 10: a shaped bin locks the label inputs, a remembered invalid color must not lock OK there
    assert colors.binHasLabel(True, True, False, False) is True
    assert colors.binHasLabel(True, True, True, False) is False
    assert colors.binHasLabel(True, True, False, True) is False
    assert colors.binHasLabel(False, True, False, False) is False
    assert colors.binHasLabel(True, False, False, False) is False


# --- upstream round 17.11. (p13, d0ad89c): outline letters painted in Fusion, only where they're no bodies of their own ---

def test_outline_letters_without_a_color_are_painted():
    assert colors.paintsOutlineLetterFaces(True, True, '')


def test_colored_outline_letters_are_bodies_of_their_own_and_not_painted():
    # the letters fill the outline cut as bodies in the label color, the faces under them aren't seen (p86)
    assert not colors.paintsOutlineLetterFaces(True, True, '#D02020')


def test_no_painting_without_an_outline_label_or_without_a_body():
    assert not colors.paintsOutlineLetterFaces(True, False, '')
    assert not colors.paintsOutlineLetterFaces(False, True, '')
