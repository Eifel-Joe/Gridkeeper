"""
Layout of the label of the storage box after Pred's parametric Gridfinity Storage Box v1.1
(https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric, CC BY-NC, by Pred), round 29
(p262, dev-notes/r29/boxlabel-plan.md). Plain math, no Fusion, lengths in cm.

Pred's flat plate (Label / Label_M_Screws in Pred's file, 67.5 x 24.5 x 0.85 mm at 5 cells wide), its width the box's
label width less 3 mm. On it, Gridkeeper text and Cullenect symbols (https://github.com/CullenJWebb/Cullenect-Labels,
MIT, by CullenJWebb):

    +---------------------------------------+
    |  large  |  line 1                     |
    |  text   |  line 2                     |
    |         |  up to five symbols         |
    +---------------------------------------+

Coordinates in the plate's own frame: x along its width, y up its height, both centred, as seen from the front.
"""

import os
from dataclasses import dataclass, field

from . import cullenectCatalog
from .predBox import PRED

# Pred's plate, cm (pred_read2.out: EmptyLabel 67.5 x 24.5 x 0.85 mm at 5 x 4 x 6)
PLATE_HEIGHT = 2.45
PLATE_THICKNESS = 0.085
# Label/Sketch1: the corners rounded 3.5 mm; Chamfer1: 0.2 mm all round, front and back (r29_walk/Label.json)
PLATE_CORNER_RADIUS = 0.35
PLATE_CHAMFER = 0.02
# 1.5 mm in from each edge of the box's label width (x 81.25 against the label edge at 79.75 mm)
PLATE_INSET = 0.15
# raised, debossed or flush by this much, as Pred's Label_M_Screws (1.25 mm thick, 0.4 mm raised letters)
MARKING_DEPTH = 0.04
# the plate's back face in the holder, 0.2 mm in front of the slot's back wall at 7.5 mm (y 6.45 ... 7.3 in Pred's file)
SEAT_Y = 0.73

MIN_CELLS = 4

# Proposals [V] of the plan, dev-notes/r29/boxlabel-plan.md section 2
# free all around: the holder's lips cover 1 mm at the sides and the bottom, slanted 2.5 mm at the corners
MARGIN = 0.25
BIG_FIELD_SHARE = 0.35
FIELD_GAP = 0.2
BIG_TEXT_HEIGHT = 1.2
LINE_HEIGHT = 0.4
LINE_GAP = 0.25
MAX_LINES = 2
SYMBOL_ROW_HEIGHT = 0.6
SYMBOL_GAP = 0.15
# between the symbol row and the lines above it
ROW_GAP = 0.2
MAX_SYMBOLS = 5

NO_SYMBOL = 'None'
# the plate's body, its text and symbols 'Box label text 1', 'Box label symbol 1'; free labels are found by it
PLATE_BODY_NAME = 'Box label'


def labelWidth(cells: int) -> float:
    """The box's label width, Pred's _LabelWidth: min(X * 42 + 20 - 159.5, 85) mm, as predBox.PredBoxDims.labelWidth"""
    return min(cells * PRED['grid'] + 2 * PRED['margin'] - PRED['labelWidthTaken'], PRED['labelWidthMax'])


def plateWidth(cells: int) -> float:
    return labelWidth(cells) - 2 * PLATE_INSET


# Jörg 17.11.2026: "Da das Schild ja feste Breiten hat, sollte es nur ein Auswahlmenü dafür geben. Nicht frei
# einstellbar." Pred's label width stops growing at 85 mm from 6 cells on, so there are three
WIDTH_CHOICE_CELLS = [4, 5, 6]
DEFAULT_CELLS = 5


def widthChoices() -> list[tuple[str, int]]:
    """(dialog name, cells) of each label width there is, named by the box and Pred's label width"""
    return [(f'Box {cells}{"+" if cells == WIDTH_CHOICE_CELLS[-1] else ""} cells ({labelWidth(cells) * 10:g} mm)', cells)
            for cells in WIDTH_CHOICE_CELLS]


def widthChoiceFor(cells: int) -> str:
    """The choice of a box that many cells wide, the widest from 6 cells on"""
    choices = widthChoices()
    return next((name for (name, choiceCells) in choices if choiceCells == cells), choices[-1][0] if cells > WIDTH_CHOICE_CELLS[-1] else choices[0][0])


def cellsOfChoice(name: str) -> int:
    return dict(widthChoices()).get(name, DEFAULT_CELLS)


def cellsOfBoxWidth(width: float) -> int | None:
    """The width in grid cells of a box of that outer width (cm): cells x 42 mm + 20 mm, none below the smallest box"""
    cells = round((width - 2 * PRED['margin']) / PRED['grid'])
    return cells if cells >= MIN_CELLS else None


def sizeProblem(cells: int) -> str | None:
    if cells < MIN_CELLS:
        return f'A box is at least {MIN_CELLS} cells wide'
    return None


@dataclass
class BoxLabelLayout:
    width: float
    height: float
    # the large text's field, None for its height without one
    bigMinX: float
    bigMaxX: float
    bigCenterY: float
    bigHeight: float | None
    # the field of the lines and the symbols at the right
    textMinX: float
    textMaxX: float
    # cap heights of the lines before they shrink to fit the width, their centres
    lineHeights: list[float] = field(default_factory=list)
    lineCenters: list[float] = field(default_factory=list)
    # (left x, centre y, width, height) of each symbol that fits, from the left
    symbolBoxes: list[tuple[float, float, float, float]] = field(default_factory=list)
    # symbols left out at the right for want of room
    dropped: int = 0


def labelLayout(width: float, hasBigText: bool, lineCount: int, symbolSizes: list[tuple[float, float]]) -> BoxLabelLayout:
    """Where the large text, the lines and the symbols go on a plate `width` wide. `symbolSizes`: the chosen symbols'
    svg sizes (cm), each is scaled to the row height keeping its shape; the ones that don't fit are left out from the
    right, nothing gets smaller (Hauptsitzung). Without symbols the lines are centred in the height, without lines the
    symbols, without a large text the right field takes the whole width"""
    if lineCount < 0 or lineCount > MAX_LINES:
        raise ValueError(f'A box label takes up to {MAX_LINES} lines')
    if len(symbolSizes) > MAX_SYMBOLS:
        raise ValueError(f'A box label takes up to {MAX_SYMBOLS} symbols')
    height = PLATE_HEIGHT
    (minX, maxX) = (-width / 2 + MARGIN, width / 2 - MARGIN)
    (minY, maxY) = (-height / 2 + MARGIN, height / 2 - MARGIN)
    if hasBigText:
        bigMaxX = minX + (maxX - minX) * BIG_FIELD_SHARE
        textMinX = bigMaxX + FIELD_GAP
        bigHeight = min(BIG_TEXT_HEIGHT, maxY - minY)
    else:
        bigMaxX = minX
        textMinX = minX
        bigHeight = None

    boxes = []
    x = textMinX
    for (svgWidth, svgHeight) in symbolSizes:
        scale = SYMBOL_ROW_HEIGHT / svgHeight
        symbolWidth = svgWidth * scale
        if x + symbolWidth > maxX + 1e-9:
            break
        boxes.append((x, 0.0, symbolWidth, svgHeight * scale))
        x += symbolWidth + SYMBOL_GAP
    dropped = len(symbolSizes) - len(boxes)

    if len(boxes) > 0 and lineCount > 0:
        rowCenter = minY + SYMBOL_ROW_HEIGHT / 2
        boxes = [(left, rowCenter, w, h) for (left, _, w, h) in boxes]
        linesMinY = minY + SYMBOL_ROW_HEIGHT + ROW_GAP
    else:
        linesMinY = minY
    middle = (linesMinY + maxY) / 2
    pitch = LINE_HEIGHT + LINE_GAP
    lineCenters = [middle] if lineCount == 1 else [middle + pitch / 2, middle - pitch / 2] if lineCount == 2 else []
    return BoxLabelLayout(
        width=width,
        height=height,
        bigMinX=minX,
        bigMaxX=bigMaxX,
        bigCenterY=0.0,
        bigHeight=bigHeight,
        textMinX=textMinX,
        textMaxX=maxX,
        lineHeights=[LINE_HEIGHT] * lineCount,
        lineCenters=lineCenters,
        symbolBoxes=boxes,
        dropped=dropped,
    )


# the screws offered on the box label: machine screws with full thread, no flange, no security pin, every head and
# driver there is an svg of (proposal [V], six fields per symbol as in the insert dialog would be 30 fields)
SCREW_KIND = ('machine', 'full', False, False)


def _screwName(head: str, driver: str) -> str:
    headName = 'Threaded rod' if head == 'none' else cullenectCatalog.displayName(head)
    return headName if driver == 'none' else f'{headName} {cullenectCatalog.displayName(driver)}'


def symbolChoices(folder: str) -> list[tuple[str, str | None]]:
    """(name, svg path) of every symbol a place on the label offers: none first, the screws, then the hardware"""
    (shaft, threads, flange, security) = SCREW_KIND
    choices: list[tuple[str, str | None]] = [(NO_SYMBOL, None)]
    for head in cullenectCatalog.HEADS:
        for driver in cullenectCatalog.DRIVERS:
            path = os.path.join(folder, cullenectCatalog.SCREWS_FOLDER,
                                cullenectCatalog.screwIconFileName(head, shaft, threads, driver, flange, security))
            if os.path.isfile(path):
                choices.append((_screwName(head, driver), path))
    names = {name for (name, _) in choices}
    for (name, path) in cullenectCatalog.listHardwareIcons(folder):
        choices.append((name if name not in names else f'{name} (hardware)', path))
    return choices


TITLE_TEXT_LENGTH = 20


def labelTitle(cells: int, bigText: str, lines: list[str]) -> str:
    """Name of the label's component and timeline group, with the start of its text"""
    texts = [text.strip() for text in [bigText] + list(lines) if len(text.strip()) > 0]
    text = ''
    if len(texts) > 0:
        text = ' ' + (texts[0] if len(texts[0]) <= TITLE_TEXT_LENGTH else texts[0][:TITLE_TEXT_LENGTH] + '…')
    return f'Gridkeeper box label {cells} cells{text}'
