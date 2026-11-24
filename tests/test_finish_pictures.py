"""
Round 58: the finishing of a model picture outside Fusion, tools/screenshots/finishPictures.py, the same as the
palette's page does it (lib/ui/html/pictureFinish.js): cut to the model, graded, fitted with a margin, scaled down.
Needs Pillow, skipped without it.
"""

import importlib.util
import json
import os

import pytest

Image = pytest.importorskip("PIL.Image")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "tools", "screenshots", "finishPictures.py")


def _module():
    spec = importlib.util.spec_from_file_location("finishPictures", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


finish = _module()


def _render(size, box, color=(78, 121, 167, 255), background=(0, 0, 0, 0)):
    image = Image.new("RGBA", size, background)
    image.paste(Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), color), box[:2])
    return image


def test_the_content_box_of_a_transparent_render():
    render = _render((400, 300), (100, 50, 300, 250))
    assert finish.contentBounds(render, transparent=True) == (100, 50, 300, 250)


def test_the_content_box_of_an_opaque_render_goes_by_the_corner_color():
    render = _render((400, 300), (100, 50, 300, 250), background=(200, 200, 200, 255))
    assert finish.contentBounds(render, transparent=False) == (100, 50, 300, 250)
    # within 12 of the corner is still background
    faint = _render((400, 300), (100, 50, 300, 250), color=(210, 205, 195, 255), background=(200, 200, 200, 255))
    assert finish.contentBounds(faint, transparent=False) is None


def test_a_model_at_the_edge_is_flagged():
    options = finish.Options(width=100, height=100, margin=0.05, transparent=True, exposure=0, saturation=1)
    (_, touches) = finish.finish(_render((400, 300), (0, 50, 300, 250)), options)
    assert touches
    (_, inside) = finish.finish(_render((400, 300), (10, 50, 300, 250)), options)
    assert not inside


def test_the_model_is_fitted_with_its_margin_and_centred():
    options = finish.Options(width=200, height=100, margin=0.1, transparent=True, exposure=0, saturation=1)
    (picture, _) = finish.finish(_render((1000, 1000), (100, 100, 500, 300)), options)
    assert picture.size == (200, 100)
    # 400 x 200 into 160 x 80, centred
    (left, top, right, bottom) = picture.getbbox()
    assert (right - left, bottom - top) == (160, 80)
    assert (left, top) == (20, 10)


def test_an_opaque_picture_is_padded_with_the_render_background():
    options = finish.Options(width=100, height=100, margin=0.2, transparent=False, exposure=0, saturation=1)
    (picture, _) = finish.finish(_render((400, 400), (100, 100, 300, 300), background=(240, 240, 240, 255)), options)
    assert picture.getpixel((2, 2))[:3] == (240, 240, 240)


def test_grading_brightens_in_linear_light_as_the_page_does():
    table = finish.exposureTable(1)
    # as pictureFinish.js: sRGB to linear, times 2 ** stops, back, rounded, clipped
    assert table[0] == 0
    assert table[255] == 255
    assert table[128] == 176
    assert finish.exposureTable(0)[100] == 100


def test_saturation_moves_colors_away_from_their_grey():
    options = finish.Options(width=10, height=10, margin=0, transparent=True, exposure=0, saturation=1.5)
    (picture, _) = finish.finish(_render((10, 10), (0, 0, 10, 10), color=(100, 120, 160, 255)), options)
    (r, g, b, _) = picture.getpixel((5, 5))
    grey = 0.2126 * 100 + 0.7152 * 120 + 0.0722 * 160
    assert abs(b - (grey + 1.5 * (160 - grey))) <= 2
    assert abs(r - (grey + 1.5 * (100 - grey))) <= 2


def test_a_sidecar_names_the_render_and_its_picture(tmp_path):
    render = tmp_path / "bin.render.png"
    _render((400, 300), (100, 50, 300, 250)).save(render)
    output = tmp_path / "out" / "bin.png"
    sidecar = tmp_path / "bin.json"
    sidecar.write_text(json.dumps({
        "name": "bin", "render": str(render), "output": str(output), "width": 120, "height": 90, "margin": 0.05,
        "transparent": True, "exposure": 0.85, "saturation": 1.4,
    }), encoding="utf-8")
    result = finish.finishSidecar(str(sidecar))
    assert result == {"name": "bin", "output": str(output), "touchesEdge": False}
    assert Image.open(output).size == (120, 90)
