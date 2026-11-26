"""Tests for dev-notes/tools/anim/compose.py, the tool that puts the documentation animations together"""
import importlib.util
import os

import pytest

Image = pytest.importorskip('PIL.Image')

HERE = os.path.dirname(__file__)
SPEC = importlib.util.spec_from_file_location('compose', os.path.join(HERE, '..', 'dev-notes', 'tools', 'anim', 'compose.py'))
compose = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compose)

DIALOG_GREY = (60, 68, 82)


def dialog(size=(400, 200), edge=None):
    picture = Image.new('RGB', size, DIALOG_GREY)
    if edge:
        picture.paste(Image.new('RGB', (40, size[1]), edge), (size[0] - 40, 0))
    return picture


def model(size=(600, 400)):
    picture = Image.new('RGBA', size, (0, 0, 0, 0))
    picture.paste(Image.new('RGBA', (200, 200), (70, 130, 200, 255)), (200, 100))
    return picture


def test_red_edge_is_found_on_the_right():
    assert compose.hasRedEdge(dialog(edge=(128, 84, 75)))


def test_plain_dialog_has_no_red_edge():
    assert not compose.hasRedEdge(dialog())


def test_red_edge_is_found_on_every_side():
    picture = dialog()
    picture.paste(Image.new('RGB', (400, 40), (128, 84, 75)), (0, 0))
    assert compose.hasRedEdge(picture)


def test_frame_refuses_a_dialog_with_red_edge():
    with pytest.raises(ValueError, match='red edge'):
        compose.frame(model(), dialog(edge=(128, 84, 75)), 'Text', 'light', None, 'x.png')


def test_light_and_dark_frames_differ_only_in_the_page():
    light = compose.frame(model(), dialog(), 'Text', 'light', None, 'x.png')
    dark = compose.frame(model(), dialog(), 'Text', 'dark', None, 'x.png')
    assert light.size == dark.size
    assert light.getpixel((2, 2)) == compose.PAGE['light']
    assert dark.getpixel((2, 2)) == compose.PAGE['dark']


def test_frame_shows_the_model_and_the_dialog():
    picture = compose.frame(model(), dialog(), 'Text', 'dark', None, 'x.png')
    colors = {picture.getpixel((x, y)) for x in range(0, picture.size[0], 10) for y in range(0, picture.size[1], 10)}
    assert (70, 130, 200) in colors
    assert DIALOG_GREY in colors


def test_cursor_is_drawn_where_asked():
    without = compose.frame(model(), dialog(), 'Text', 'dark', None, 'x.png')
    with_cursor = compose.frame(model(), dialog(), 'Text', 'dark', (50, 50), 'x.png')
    assert without.tobytes() != with_cursor.tobytes()


def test_gif_holds_every_state_and_fades_between(tmp_path):
    states = [compose.State(model(), dialog(), f'State {i}', None, 'x.png') for i in range(3)]
    out = tmp_path / 'demo-light.gif'
    compose.writeGif(states, 'light', str(out))
    gif = Image.open(out)
    durations = []
    for index in range(gif.n_frames):
        gif.seek(index)
        durations.append(gif.info['duration'])
    assert sum(durations) == pytest.approx(3 * (compose.HOLD_MS + compose.FADE_MS), abs=30)
    assert durations.count(compose.HOLD_MS) == 3


def test_animation_writes_light_and_dark(tmp_path):
    states = [compose.State(model(), dialog(), 'A', None, 'x.png'), compose.State(model(), dialog(), 'B', None, 'x.png')]
    compose.writeAnimation('demo', states, str(tmp_path))
    assert sorted(os.listdir(tmp_path)) == ['demo-dark.gif', 'demo-light.gif']


def test_models_are_cropped_to_their_common_box():
    small = Image.new('RGBA', (600, 400), (0, 0, 0, 0))
    small.paste(Image.new('RGBA', (100, 50), (70, 130, 200, 255)), (250, 150))
    cropped = compose.cropToCommonBox([model(), small])
    assert cropped[0].size == cropped[1].size
    assert cropped[0].size[0] < 600 and cropped[0].size[1] < 400
    assert cropped[0].getbbox() is not None


def test_cursor_near_the_bottom_stays_inside_the_untorn_part():
    picture = dialog(size=(400, 120))
    kept = compose.cursorInside((300, 115), picture.size)
    assert compose.TOOTH <= kept[1] and kept[1] + compose.CURSOR_HEIGHT <= picture.size[1] - compose.TOOTH
    assert kept[0] == 300


# Round 60: the animations in German, the same models with German dialog pictures and captions

def _raw(tmp_path, names):
    folder = tmp_path / 'raw' / 'demo'
    folder.mkdir(parents=True)
    for name in names:
        (model() if 'model' in name else dialog()).save(folder / name)
    return str(tmp_path / 'raw')


def test_german_states_take_the_german_dialog_and_caption(tmp_path):
    raw = _raw(tmp_path, ['1-model.png', '1-dialog.png', '1-dialog.de.png', '2-model.png', '2-tool.png', '2-tool.de.png'])
    entries = [{'caption': 'Hollow', 'captionDe': 'Hohl', 'cursor': [1, 2], 'cursorDe': [3, 4]},
               {'caption': 'Solid', 'captionDe': 'Voll', 'dialog': '2-tool.png'}]
    states = compose.loadStates('demo', entries, 'de', raw)
    assert [s.caption for s in states] == ['Hohl', 'Voll']
    assert [os.path.basename(s.source) for s in states] == ['1-dialog.de.png', '2-tool.de.png']
    assert [s.cursor for s in states] == [(3, 4), None]
    english = compose.loadStates('demo', entries, 'en', raw)
    assert [s.caption for s in english] == ['Hollow', 'Solid']
    assert [os.path.basename(s.source) for s in english] == ['1-dialog.png', '2-tool.png']


def test_a_missing_german_dialog_or_caption_is_named(tmp_path):
    raw = _raw(tmp_path, ['1-model.png', '1-dialog.png'])
    with pytest.raises(FileNotFoundError, match='1-dialog.de.png'):
        compose.loadStates('demo', [{'caption': 'A', 'captionDe': 'B'}], 'de', raw)
    raw = _raw(tmp_path / 'b', ['1-model.png', '1-dialog.png', '1-dialog.de.png'])
    with pytest.raises(KeyError, match='captionDe'):
        compose.loadStates('demo', [{'caption': 'A'}], 'de', raw)


def test_german_animations_get_the_language_suffix(tmp_path):
    states = [compose.State(model(), dialog(), 'A', None, 'x.png'), compose.State(model(), dialog(), 'B', None, 'x.png')]
    compose.writeAnimation('demo', states, str(tmp_path), 'de')
    assert sorted(os.listdir(tmp_path)) == ['demo-dark.de.gif', 'demo-light.de.gif']


def test_every_state_has_a_german_caption():
    import json
    anims = json.load(open(os.path.join(HERE, '..', 'dev-notes', 'tools', 'anim', 'anims.json'), encoding='utf-8'))
    assert all(entry.get('captionDe') for entries in anims.values() for entry in entries)
