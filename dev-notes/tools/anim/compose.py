"""
Puts the animations of the documentation together: per state the rendered model on the left with its caption below
and the part of the dialog that changes on the right, then a GIF that holds each state and fades the model to the next.

Usage: python compose.py [--language de] [name ...]   (no name: all animations of anims.json)
Reads anims.json and the raw pictures in raw/<name>/, writes docs/assets/gif/<name>-light.gif and -dark.gif.

The model pictures come from Fusion with a transparent background, the dialog pictures are screenshots of Fusion's
dark theme. Both GIFs of an animation show the same dialog; light and dark differ only in the page around it, so the
picture fits the light and the dark theme of the documentation site.
"""
import json
import os
import sys
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(REPO, 'docs', 'assets', 'gif')

# page colours of the documentation site (MkDocs Material, light: default, dark: slate)
PAGE = {'light': (255, 255, 255), 'dark': (30, 33, 41)}
CAPTION = {'light': (60, 60, 60), 'dark': (220, 220, 225)}
HOLD_MS = 1500
FADE_MS = 400
FADE_STEPS = 5
PAD = 40
MODEL_BOX = (640, 520)
DIALOG_MAX_WIDTH = 900
TOOTH = 8
CURSOR_HEIGHT = 26
EDGE = 40


@dataclass
class State:
    model: Image.Image
    dialog: Image.Image
    caption: str
    cursor: tuple | None
    source: str


def hasRedEdge(picture: Image.Image) -> bool:
    """
    True when a strip along any side is reddish on average. That is the glow Claude's computer use lays along the
    screen edges while it controls the screen; a dialog close to an edge gets it painted over (16.11.2026, five
    pictures of the documentation had it).
    """
    rgb = picture.convert('RGB')
    (width, height) = rgb.size
    edge = max(1, min(EDGE, width // 4, height // 4))
    strips = [(width - edge, 0, width, height), (0, 0, edge, height), (0, 0, width, edge), (0, height - edge, width, height)]
    for box in strips:
        (r, g, b) = rgb.crop(box).resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
        if r > g + 12 and r > b + 12:
            return True
    return False


def font(size: int):
    for name in ('segoeui.ttf', 'DejaVuSans.ttf', 'Arial.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size)


def torn(picture: Image.Image) -> Image.Image:
    """The dialog part with a zigzag top and bottom, a piece torn out of the dialog"""
    rgba = picture.convert('RGBA')
    (width, height) = rgba.size
    mask = Image.new('L', rgba.size, 255)
    draw = ImageDraw.Draw(mask)
    for top in (True, False):
        points = []
        for x in range(0, width + 2 * TOOTH, 2 * TOOTH):
            points += [(x, 0 if top else height), (x + TOOTH, TOOTH if top else height - TOOTH)]
        points += [(width, 0 if top else height)]
        draw.polygon(points + [(width, -1 if top else height + 1), (0, -1 if top else height + 1)], fill=0)
    rgba.putalpha(mask)
    return rgba


def drawCursor(picture: Image.Image, at: tuple):
    """A plain arrow pointer with its tip at the point, white with a black outline"""
    (x, y) = at
    arrow = [(0, 0), (0, 22), (6, 17), (10, 26), (14, 24), (10, 16), (17, 16)]
    ImageDraw.Draw(picture).polygon([(x + dx, y + dy) for (dx, dy) in arrow], fill=(255, 255, 255), outline=(0, 0, 0))


def cursorInside(at: tuple, size: tuple) -> tuple:
    """
    The cursor tip moved up or down so the whole arrow stays in the part of the dialog the zigzag leaves: a tip on a
    field near the bottom edge would otherwise be torn away with it (review round 26, connection holes)
    """
    (x, y) = at
    lowest = size[1] - TOOTH - CURSOR_HEIGHT
    return (x, max(TOOTH, min(y, lowest)))


def fit(picture: Image.Image, box: tuple) -> Image.Image:
    scale = min(box[0] / picture.size[0], box[1] / picture.size[1], 1.0)
    return picture.resize((round(picture.size[0] * scale), round(picture.size[1] * scale)), Image.Resampling.LANCZOS)


def frame(model: Image.Image, dialog: Image.Image, caption: str, theme: str, cursor, source: str) -> Image.Image:
    if hasRedEdge(dialog):
        raise ValueError(f'{source}: red edge, the dialog was too close to the screen edge while it was taken')
    part = fit(dialog.convert('RGB'), (DIALOG_MAX_WIDTH, 10_000))
    if cursor is not None:
        scale = part.size[0] / dialog.size[0]
        drawCursor(part, cursorInside((round(cursor[0] * scale), round(cursor[1] * scale)), part.size))
    part = torn(part)
    shape = fit(model.convert('RGBA'), MODEL_BOX)
    captionHeight = 60
    height = max(MODEL_BOX[1] + captionHeight, part.size[1]) + 2 * PAD
    width = PAD + MODEL_BOX[0] + PAD + part.size[0] + PAD
    page = Image.new('RGB', (width, height), PAGE[theme])
    page.paste(shape, (PAD + (MODEL_BOX[0] - shape.size[0]) // 2, PAD + (MODEL_BOX[1] - shape.size[1]) // 2), shape)
    page.paste(part, (PAD + MODEL_BOX[0] + PAD, (height - part.size[1]) // 2), part)
    draw = ImageDraw.Draw(page)
    text = font(26)
    textWidth = draw.textlength(caption, font=text)
    draw.text((PAD + (MODEL_BOX[0] - textWidth) / 2, PAD + MODEL_BOX[1] + 14), caption, fill=CAPTION[theme], font=text)
    return page


def writeGif(states: list, theme: str, path: str):
    """Each state held, then the next faded in; the last fades back to the first, so the GIF loops smoothly"""
    pictures = [frame(s.model, s.dialog, s.caption, theme, s.cursor, s.source) for s in states]
    size = (max(p.size[0] for p in pictures), max(p.size[1] for p in pictures))
    pictures = [centered(p, size, PAGE[theme]) for p in pictures]
    frames = []
    durations = []
    for (index, picture) in enumerate(pictures):
        following = pictures[(index + 1) % len(pictures)]
        frames.append(picture)
        durations.append(HOLD_MS)
        for step in range(1, FADE_STEPS + 1):
            frames.append(Image.blend(picture, following, step / (FADE_STEPS + 1)))
            durations.append(FADE_MS // FADE_STEPS)
    paletted = [f.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    paletted[0].save(path, save_all=True, append_images=paletted[1:], duration=durations, loop=0, optimize=True, disposal=1)


def centered(picture: Image.Image, size: tuple, background: tuple) -> Image.Image:
    if picture.size == size:
        return picture
    page = Image.new('RGB', size, background)
    page.paste(picture, ((size[0] - picture.size[0]) // 2, (size[1] - picture.size[1]) // 2))
    return page


def gifName(name: str, theme: str, language: str = 'en') -> str:
    """<name>-dark.gif, in German <name>-dark.de.gif beside it, as the German docs pages find it (round 60)"""
    return f'{name}-{theme}.gif' if language == 'en' else f'{name}-{theme}.{language}.gif'


def writeAnimation(name: str, states: list, folder: str, language: str = 'en'):
    for theme in ('light', 'dark'):
        writeGif(states, theme, os.path.join(folder, gifName(name, theme, language)))


def cropToCommonBox(models: list, margin: int = 20) -> list:
    """
    All models of an animation cut to the one box that holds each of them plus a margin: the renders leave a wide
    empty border, and one box for all keeps the scale and position from state to state
    """
    boxes = [m.convert('RGBA').getchannel('A').getbbox() for m in models]
    boxes = [b for b in boxes if b] or [(0, 0) + models[0].size]
    (width, height) = models[0].size
    box = (max(0, min(b[0] for b in boxes) - margin), max(0, min(b[1] for b in boxes) - margin),
           min(width, max(b[2] for b in boxes) + margin), min(height, max(b[3] for b in boxes) + margin))
    return [m.convert('RGBA').crop(box) for m in models]


def loadStates(name: str, entries: list, language: str = 'en', rawFolder: str | None = None) -> list:
    """
    The states of an animation from raw/<name>. In German (round 60) the same models with the dialog taken in German,
    N-dialog.de.png beside N-dialog.png, the caption captionDe and, where the German dialog's inputs moved, cursorDe
    """
    raw = os.path.join(rawFolder or os.path.join(HERE, 'raw'), name)
    german = language == 'de'
    states = []
    for (index, entry) in enumerate(entries):
        modelPath = os.path.join(raw, f'{index + 1}-model.png')
        (stem, extension) = os.path.splitext(entry.get('dialog', f'{index + 1}-dialog.png'))
        dialogPath = os.path.join(raw, f'{stem}.de{extension}' if german else f'{stem}{extension}')
        if not os.path.exists(dialogPath):
            raise FileNotFoundError(f'{name}: {os.path.basename(dialogPath)} is missing in {raw}')
        caption = entry['captionDe'] if german else entry['caption']
        cursor = (entry.get('cursorDe') or entry.get('cursor')) if german else entry.get('cursor')
        states.append(State(Image.open(modelPath), Image.open(dialogPath), caption, tuple(cursor) if cursor else None, dialogPath))
    for (state, model) in zip(states, cropToCommonBox([s.model for s in states])):
        state.model = model
    return states


def main(arguments: list):
    """[--language de] [name ...]"""
    language = 'en'
    if arguments[:1] == ['--language']:
        (language, arguments) = (arguments[1], arguments[2:])
    anims = json.load(open(os.path.join(HERE, 'anims.json'), encoding='utf-8'))
    for name in arguments or list(anims):
        writeAnimation(name, loadStates(name, anims[name], language), OUT, language)
        sizes = [os.path.getsize(os.path.join(OUT, gifName(name, t, language))) // 1024 for t in ('light', 'dark')]
        # not '<name>: ...', the palette takes such a line as what kept the GIF from being made
        print(f'{name} made, {sizes[0]} KB light, {sizes[1]} KB dark')
        # the pictures palette in Fusion takes these lines as the GIFs made (round 58)
        for theme in ('light', 'dark'):
            print(os.path.join(OUT, gifName(name, theme, language)))


if __name__ == '__main__':
    main(sys.argv[1:])
