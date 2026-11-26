"""
Colors of the label text and symbols, of the Cullenect inserts and the bin labels (p86). A color is '#RRGGBB', an empty
text for none: the text keeps the look of its body as before. The dialogs offer a few named colors and a custom one.
No Fusion imports, so it is testable, the appearance itself is made by appearanceUtils.
"""

import re

try:
    from ..i18n import tr, number
except ImportError:
    # loaded on its own by a test or a tool, outside the add-in package: English
    def tr(text, context=None, /, **values):
        return text.format(**values) if values else text

    def number(value):
        return value if isinstance(value, str) else f'{value:g}'

NO_COLOR_CHOICE = 'None'  # tr-value
CUSTOM_CHOICE = 'Custom'  # tr-value
# named colors, about the filaments one has
NAMED_COLORS = {
    'Black': '#000000',
    'White': '#FFFFFF',
    'Red': '#D02020',
    'Orange': '#FF8000',
    'Yellow': '#FFD700',
    'Green': '#20A040',
    'Blue': '#2060D0',
    'Gray': '#808080',
}  # tr-keys
CHOICES = [NO_COLOR_CHOICE] + list(NAMED_COLORS) + [CUSTOM_CHOICE]

_COLOR = re.compile(r'^#[0-9A-Fa-f]{6}$')

# library appearances the color is copied from, by the start of their name, best first, in any case. The libraries
# come in the user's language (p31: a German Fusion has no "Plastic", it has "Kunststoff - matt (Rot)"), a name not
# listed still serves when it has a color
BASE_PREFIXES = ['plastic - matte', 'kunststoff - matt', 'plastic', 'kunststoff']
# Fusion's appearance library, by its id, its name is in the user's language too ("Fusion-Darstellungsbibliothek")
APPEARANCE_LIBRARY_ID = 'BA5EE55E-9982-449B-9D66-9F036540E140'


def isColor(color: str) -> bool:
    """'#RRGGBB' or empty for none"""
    return color == '' or _COLOR.match(color) is not None


def colorOf(choice: str, custom: str) -> str | None:
    """The color of a dialog choice, '' for none, None when the custom color isn't one. An unknown choice, from saved
    defaults of another version, counts as none"""
    if choice == CUSTOM_CHOICE:
        text = custom.strip()
        if not text.startswith('#'):
            text = '#' + text
        return text.upper() if _COLOR.match(text) else None
    return NAMED_COLORS.get(choice, '')


def colorProblem(choice: str, custom: str) -> str | None:
    """Why the color can't be used, none if it can"""
    if colorOf(choice, custom) is None:
        return tr('The custom color is #rrggbb, e.g. {example}', example=NAMED_COLORS['Red'])
    return None


def choiceOf(color: str) -> tuple[str, str]:
    """The dialog choice and custom text of a color, the way back of colorOf"""
    if color == '':
        return (NO_COLOR_CHOICE, '')
    named = next((name for (name, value) in NAMED_COLORS.items() if value == color.upper()), None)
    return (named, '') if named is not None else (CUSTOM_CHOICE, color.upper())


def appearanceName(color: str) -> str:
    """Name of the appearance in the document, Fusion refuses some characters in names, # among them"""
    return f'Gridfinity label {color.lstrip("#").upper()}'


_APPEARANCE_NAME = re.compile(r'^Gridfinity label ([0-9A-F]{6})$')


def colorOfAppearanceName(name: str | None) -> str:
    """
    The color of a label appearance by its name, the way back of appearanceName, '' for any other appearance: the
    export puts each label color on a filament of its own by it (round 37, p301). Text recolored by hand in Fusion
    has another appearance and counts as text without a color
    """
    found = _APPEARANCE_NAME.match(name or '')
    return f'#{found.group(1)}' if found else ''


def textName(color: str) -> str:
    """The export dialog's name of the label text of a color, by its choice in the dialogs, see choiceOf"""
    if color == '':
        return 'Text without color'
    (choice, custom) = choiceOf(color)
    return f'{custom or choice} text'


def rgb(color: str) -> tuple[int, int, int]:
    return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))


def baseRank(appearanceName: str) -> int:
    """Lower is a better appearance to copy the color from, any other name ranks last"""
    name = appearanceName.lower()
    return next((index for (index, prefix) in enumerate(BASE_PREFIXES) if name.startswith(prefix)), len(BASE_PREFIXES))


def baseCandidates(libraries: list[tuple[str, list[str]]]) -> list[tuple[int, int]]:
    """
    (library, appearance) indexes of the appearances to copy the color from, best first: by baseRank, then Fusion's
    appearance library before the others, then as listed. libraries as (library id, appearance names). A favorites
    library may hold a wood ("3D Esche") that ranks no better than a plastic name in another language would
    """
    candidates = []
    for (libraryIndex, (libraryId, names)) in enumerate(libraries):
        isAppearanceLibrary = libraryId.upper() == APPEARANCE_LIBRARY_ID
        for (index, name) in enumerate(names):
            candidates.append(((baseRank(name), 0 if isAppearanceLibrary else 1, libraryIndex, index), (libraryIndex, index)))
    return [position for (_, position) in sorted(candidates)]


def dialogColor(choice: str, custom: str) -> str:
    """The color of a dialog choice for the state: the color, '' for none, a custom text that is no color as it is
    ('Custom' for an empty one), so isColor fails and the dialog locks OK with colorProblem"""
    color = colorOf(choice, custom)
    if color is not None:
        return color
    return custom.strip() or CUSTOM_CHOICE


def configCurrentColor(choice: str, custom: str) -> str:
    """The color a loaded config keeps when it has none, saved before bins had label colors (round 18, p151): the
    dialog's choice as it is. The bin state's own color is '' without a label to color (labelColorFor), an old config
    with a label took that and the choice jumped to None"""
    return dialogColor(choice, custom)


def labelColorFor(color: str, hasLabel: bool, isCullenect: bool) -> str:
    """The color a bin's state keeps: none where there is no label to color, without a tab or with a Cullenect socket,
    so a remembered color doesn't go into the bin's settings"""
    return color if hasLabel and not isCullenect else ''


def binHasLabel(generateBody: bool, hasTab: bool, isShaped: bool, isSolid: bool) -> bool:
    """Whether a bin gets a label tab label, as binBuilder makes one: a hollow or shelled bin body with a tab, not
    shaped. The dialog locks the label inputs otherwise, so their color mustn't lock OK there"""
    return bool(generateBody and hasTab and not isShaped and not isSolid)


def restoresColor(labelColor: str, hasLabel: bool, isCullenect: bool) -> bool:
    """
    Whether a bin's state sets the dialog's color choice, see commandCreateBin.entry.applyInputsState. A bin without a
    label to color keeps '' (see labelColorFor), that says nothing about the color, the choice in the dialog stays for
    when the label style or tab changes (review of round 12)
    """
    return labelColor != '' or (hasLabel and not isCullenect)


def paintsOutlineLetterFaces(generateBody: bool, isOutline: bool, labelColor: str) -> bool:
    """
    Whether the letter faces of a bin's outline label get upstream's label appearance in Fusion, see labelFaces
    (upstream round 17.11.2026, d0ad89c). Only without a color: with one the letters are bodies of their own filling the
    outline cut (p86), the faces under them can't be seen and aren't the letters' tops
    """
    return bool(generateBody and isOutline and labelColor == '')
