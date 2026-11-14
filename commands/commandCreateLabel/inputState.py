from dataclasses import dataclass

# Settings of a Cullenect insert, lengths in cm. The screw building blocks and the hardware are the names
# Cullenect.scad uses (socket, tnut_1, ...), 'none' for no hardware

@dataclass
class InputState:
    baseWidth: float
    # width in grid units, or free in cm
    useUnits: bool
    widthUnits: float
    freeWidth: float
    # corrections for the printer, added to width and height
    offsetX: float
    offsetY: float

    line1: str
    line2: str
    isBold: bool

    showScrew: bool
    head: str
    shaft: str
    threads: str
    driver: str
    flange: bool
    security: bool
    hardware: str

    # one of cullenectLabelGenerator.SURFACES
    surface: str
    # color of the text and symbol bodies, '#RRGGBB', empty for none, see labelColors
    textColor: str
