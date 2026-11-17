from dataclasses import dataclass, field

# Settings of the label of a box after Pred (round 29, p262), see predBoxLabel. Symbols by their names in the dialog,
# predBoxLabelLayout.symbolChoices, 'None' for an empty place


@dataclass
class InputState:
    # the box's width in grid cells, the plate's width follows from it (predBoxLabelLayout.plateWidth)
    cells: int
    bigText: str
    line1: str
    line2: str
    symbols: list[str] = field(default_factory=list)
    # one of textStyles.STYLES
    textStyle: str = 'Heavy'
    # one of predBoxLabel.SURFACES
    surface: str = 'Embossed'
    # color of the text and symbol bodies, '#RRGGBB', empty for none, see labelColors
    textColor: str = ''
