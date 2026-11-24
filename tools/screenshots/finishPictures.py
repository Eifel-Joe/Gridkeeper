"""
Finishes model pictures outside Fusion, as the palette's page does in Fusion (lib/ui/html/pictureFinish.js): Fusion's
Python has no imaging, so a script in Fusion saves the viewport larger than the picture with a JSON sidecar of its
options (see commands/commandModelScreenshots/scriptRender.py), and this cuts the render to the model, grades it, fits
it in the picture with a margin and scales it down. Needs Pillow only.

    python tools/screenshots/finishPictures.py <folder of sidecars> [--only name ...]

writes each picture where its sidecar says, by default docs/assets/models/<preset>.png, and reports a model that
touches the edge of its render (it may be cut off, render it again from further away).
"""

import argparse
import dataclasses
import json
import os
import sys

from PIL import Image, ImageChops

# what differs less from the background than this, per channel, is background (as the page)
BACKGROUND_TOLERANCE = 12
# a pixel of a transparent render is the model above this alpha
ALPHA_THRESHOLD = 8
# luma of Rec. 709, as the page takes a color's grey
LUMA = (0.2126, 0.7152, 0.0722, 0)


@dataclasses.dataclass
class Options:
    width: int
    height: int
    # space around the model, a share of the picture's width and height
    margin: float
    transparent: bool
    # stops the picture is brightened by, and how much its colors are deepened, 1 keeps them
    exposure: float
    saturation: float


def exposureTable(stops: float) -> list[int]:
    """Brighter by stops as a camera's exposure, in linear light so the darkest stays dark, clipped at white"""
    factor = 2 ** stops
    table = []
    for value in range(256):
        channel = value / 255
        linear = (channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4) * factor
        encoded = linear * 12.92 if linear <= 0.0031308 else 1.055 * linear ** (1 / 2.4) - 0.055
        table.append(max(0, min(255, round(encoded * 255))))
    return table


def _backgroundMask(image: Image.Image, background: tuple[int, int, int]) -> Image.Image:
    """255 where the pixel is within the tolerance of the background in every channel"""
    difference = ImageChops.difference(image.convert("RGB"), Image.new("RGB", image.size, background))
    bands = [band.point(lambda value: 255 if value <= BACKGROUND_TOLERANCE else 0) for band in difference.split()]
    return ImageChops.multiply(ImageChops.multiply(bands[0], bands[1]), bands[2])


def contentBounds(image: Image.Image, transparent: bool) -> tuple[int, int, int, int] | None:
    """The box of the model, (left, top, right, bottom) with right and bottom past it, none for an empty render"""
    if transparent:
        return image.getchannel("A").point(lambda value: 255 if value > ALPHA_THRESHOLD else 0).getbbox()
    background = image.getpixel((0, 0))[:3]
    return ImageChops.invert(_backgroundMask(image, background)).getbbox()


def grade(image: Image.Image, stops: float, saturation: float, background: tuple[int, int, int] | None) -> Image.Image:
    """Brighter by stops, colors deepened by saturation away from their grey; an opaque background keeps its color"""
    (r, g, b, a) = image.convert("RGBA").split()
    table = exposureTable(stops)
    exposed = Image.merge("RGB", [band.point(table) for band in (r, g, b)])
    if saturation != 1:
        grey = exposed.convert("L", LUMA).convert("RGB")
        # past 1 the blend moves away from the grey, Pillow clips at 0 and 255
        exposed = Image.blend(grey, exposed, saturation)
    graded = Image.merge("RGBA", [*exposed.split(), a])
    if background is not None:
        graded = Image.composite(image.convert("RGBA"), graded, _backgroundMask(image, background))
    return graded


def scaled(image: Image.Image, width: int, height: int) -> Image.Image:
    """Halving at most each time keeps every pixel in the average, one big step would skip most of them"""
    current = image
    while current.width / 2 >= width and current.height / 2 >= height:
        current = current.resize((max(1, round(current.width / 2)), max(1, round(current.height / 2))), Image.Resampling.BOX)
    return current.resize((max(1, round(width)), max(1, round(height))), Image.Resampling.LANCZOS)


def finish(render: Image.Image, options: Options) -> tuple[Image.Image, bool]:
    """The picture of a render and whether the model touches the edge of the render"""
    render = render.convert("RGBA")
    background = None if options.transparent else render.getpixel((0, 0))[:3]
    bounds = contentBounds(render, options.transparent)
    if bounds is None:
        raise ValueError("the render is empty")
    (left, top, right, bottom) = bounds
    touchesEdge = left <= 1 or top <= 1 or right >= render.width - 1 or bottom >= render.height - 1
    if options.exposure or options.saturation != 1:
        render = grade(render, options.exposure or 0, options.saturation, background)
    model = render.crop(bounds)
    scale = min(options.width * (1 - 2 * options.margin) / model.width, options.height * (1 - 2 * options.margin) / model.height)
    model = scaled(model, model.width * scale, model.height * scale)
    picture = Image.new("RGBA", (options.width, options.height), (0, 0, 0, 0) if options.transparent else (*background, 255))
    position = (round((options.width - model.width) / 2), round((options.height - model.height) / 2))
    picture.alpha_composite(model, position)
    return (picture, touchesEdge)


def finishSidecar(path: str) -> dict:
    """Finishes the render a sidecar names and saves the picture where it says"""
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    options = Options(data["width"], data["height"], data["margin"], data["transparent"], data["exposure"], data["saturation"])
    with Image.open(data["render"]) as render:
        (picture, touchesEdge) = finish(render, options)
    os.makedirs(os.path.dirname(data["output"]), exist_ok=True)
    picture.save(data["output"], optimize=True)
    return {"name": data["name"], "output": data["output"], "touchesEdge": touchesEdge}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Finishes the raw model renders of a folder")
    parser.add_argument("folder")
    parser.add_argument("--only", nargs="*", help="preset names")
    args = parser.parse_args(argv)
    sidecars = sorted(name for name in os.listdir(args.folder) if name.endswith(".json"))
    failed = False
    for name in sidecars:
        if args.only and os.path.splitext(name)[0] not in args.only:
            continue
        try:
            result = finishSidecar(os.path.join(args.folder, name))
            print(f"{result['name']}: {result['output']}{', the model may be cut off' if result['touchesEdge'] else ''}")
        except Exception as err:
            failed = True
            print(f"{os.path.splitext(name)[0]}: failed, {err}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
