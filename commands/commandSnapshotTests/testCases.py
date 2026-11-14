import dataclasses
import json
import math
import os
import re

# Shape test cases, one JSON file each, holding every setting of a bin, baseplate or label InputState by its field name.
# Lengths are in mm and angles in degrees to read easily, the state keeps Fusion's cm and radians.
# Kept free of Fusion imports so it can be unit tested, the state classes come in as an argument

GENERATOR_BIN = 'bin'
GENERATOR_BASEPLATE = 'baseplate'
GENERATOR_LABEL = 'label'

# the rest are counts, base or height units, flags and names, kept as they are
MM_FIELDS = {
    GENERATOR_BIN: {
        'baseWidth', 'baseLength', 'heightUnit', 'xyClearance', 'wallThickness', 'screwHoleDiameter',
        'magnetCutoutDiameter', 'magnetCutoutDepth', 'scoopMaxRadius', 'tabWidth', 'creaseDepth',
        'cullenectSocketOffset',
    },
    GENERATOR_BASEPLATE: {
        'baseWidth', 'baseLength', 'xyClearance', 'magnetSocketSize', 'magnetSocketDepth', 'screwHoleSize',
        'screwHeadSize', 'paddingLeft', 'paddingTop', 'paddingRight', 'paddingBottom', 'extraBottomThickness',
        'verticalClearance', 'connectionHoleSize', 'areaWidth', 'areaLength', 'fitTolerance', 'bedWidth',
        'bedLength', 'bedMargin',
    },
    GENERATOR_LABEL: {'baseWidth', 'freeWidth', 'offsetX', 'offsetY'},
}
DEGREE_FIELDS = {
    GENERATOR_BIN: {'tabOverhangAngle', 'tabTopAngle'},
    GENERATOR_BASEPLATE: set(),
    GENERATOR_LABEL: set(),
}
# lists of cells, JSON has no tuples
CELL_LIST_FIELDS = {
    GENERATOR_BIN: {'shapeCells'},
    GENERATOR_BASEPLATE: set(),
    GENERATOR_LABEL: set(),
}

# the shared user parameters a case may change after building, see lib/gridfinityUtils/sharedParameters.py, with the
# setting each stands for. Keep the names literal, they're in user documents
PARAMETER_FIELDS = {
    GENERATOR_BIN: {'gfBaseWidth': 'baseWidth', 'gfBaseLength': 'baseLength', 'gfHeightUnit': 'heightUnit'},
    GENERATOR_BASEPLATE: {'gfBaseWidth': 'baseWidth', 'gfBaseLength': 'baseLength'},
    GENERATOR_LABEL: {'gfBaseWidth': 'baseWidth'},
}

# the design intent of the document a case is built in, hybrid unless the case says otherwise. In part design the
# generators build into the root component, as for a user whose documents are parts
DESIGN_INTENT_HYBRID = 'hybrid'
DESIGN_INTENT_PART = 'part'
DESIGN_INTENTS = (DESIGN_INTENT_HYBRID, DESIGN_INTENT_PART)

class TestCaseError(Exception):
    pass

@dataclasses.dataclass
class TestCase:
    # the file name without its extension
    name: str
    description: str
    generator: str
    state: object
    # shared parameters set after building, in cm, the result has to be the same as built with them, see editedState
    parameters: dict[str, float] = dataclasses.field(default_factory=dict)
    designIntent: str = DESIGN_INTENT_HYBRID
    # the design intent the document has to have once built, None for any, a generator may switch it
    designIntentAfter: str | None = None
    # text parameters of an insert set after building, as a user edits its text (p70). Not compared with a build
    # from the start, that fits the text anew, see insertTextProblems
    texts: dict[str, str] = dataclasses.field(default_factory=dict)

def stateFromJson(generator: str, stateClass: type, settings: dict) -> object:
    """Every field of the state has to be there and nothing else, so a case never falls back to a default"""
    fieldNames = [field.name for field in dataclasses.fields(stateClass)]
    missing = [name for name in fieldNames if name not in settings]
    unknown = [name for name in settings if name not in fieldNames]
    if missing or unknown:
        raise TestCaseError(f'missing settings {missing}, unknown settings {unknown}')
    def value(name: str):
        if name in MM_FIELDS[generator]:
            return settings[name] / 10
        if name in DEGREE_FIELDS[generator]:
            return settings[name] / 180 * math.pi
        if name in CELL_LIST_FIELDS[generator]:
            return [tuple(cell) for cell in settings[name]]
        return settings[name]
    return stateClass(**{name: value(name) for name in fieldNames})

def stateToJson(generator: str, state: object) -> dict:
    """Settings of a case file, rounded so float noise from the unit change doesn't show"""
    def value(name: str, fieldValue):
        if name in MM_FIELDS[generator]:
            return round(fieldValue * 10, 6)
        if name in DEGREE_FIELDS[generator]:
            return round(fieldValue * 180 / math.pi, 6)
        if name in CELL_LIST_FIELDS[generator]:
            return [list(cell) for cell in fieldValue]
        return fieldValue
    return {field.name: value(field.name, getattr(state, field.name)) for field in dataclasses.fields(state)}

def parametersFromJson(generator: str, parameters: dict) -> dict[str, float]:
    """Values in mm of the generator's shared parameters, in cm"""
    unknown = [name for name in parameters if name not in PARAMETER_FIELDS[generator]]
    if unknown:
        raise TestCaseError(f'unknown parameters {unknown}, a {generator} has {sorted(PARAMETER_FIELDS[generator])}')
    for (name, value) in parameters.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise TestCaseError(f'parameter {name} has to be a length in mm, not {value!r}')
    return {name: value / 10 for (name, value) in parameters.items()}

# the text parameters of an insert, see commandCreateLabel/labelBuilder.py
TEXT_PARAMETER_PATTERN = re.compile(r'gfLabel\d+_text[12]')

def textsFromJson(generator: str, texts: dict) -> dict[str, str]:
    """Text parameters of an insert to set after building"""
    if texts and generator != GENERATOR_LABEL:
        raise TestCaseError(f'only a label sets texts after building, not a {generator}')
    for (name, value) in texts.items():
        if not TEXT_PARAMETER_PATTERN.fullmatch(name) or not isinstance(value, str):
            raise TestCaseError(f'texts set an insert text parameter gfLabel<n>_text1 or _text2 to a string, not {name} to {value!r}')
    return dict(texts)

def editedState(case: TestCase) -> object:
    """The settings the case would have built with its parameters set from the start"""
    fields = PARAMETER_FIELDS[case.generator]
    return dataclasses.replace(case.state, **{fields[name]: value for (name, value) in case.parameters.items()})

def loadCase(path: str, stateClasses: dict[str, type]) -> TestCase:
    """stateClasses: the InputState class of each generator"""
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        with open(path, encoding='utf-8') as file:
            data = json.load(file)
        generator = data['generator']
        if generator not in stateClasses:
            raise TestCaseError(f'unknown generator {generator!r}')
        state = stateFromJson(generator, stateClasses[generator], data['settings'])
        parameters = parametersFromJson(generator, data.get('parameters', {}))
        texts = textsFromJson(generator, data.get('texts', {}))
        if texts and parameters:
            # the build with the parameters from the start it is compared with can't have the edited text
            raise TestCaseError('a case sets either parameters or texts after building, not both')
        designIntent = data.get('designIntent', DESIGN_INTENT_HYBRID)
        if designIntent not in DESIGN_INTENTS:
            raise TestCaseError(f'unknown design intent {designIntent!r}')
        designIntentAfter = data.get('designIntentAfter')
        if designIntentAfter is not None and designIntentAfter not in DESIGN_INTENTS:
            raise TestCaseError(f'unknown design intent after building {designIntentAfter!r}')
    except (OSError, ValueError, KeyError, TypeError, AttributeError, TestCaseError) as err:
        raise TestCaseError(f'case {name}: {err}') from err
    return TestCase(name, data.get('description', ''), generator, state, parameters, designIntent, designIntentAfter, texts)

def loadCases(folder: str, stateClasses: dict[str, type]) -> list[TestCase]:
    """Cases of the folder by name"""
    paths = sorted(os.path.join(folder, fileName) for fileName in os.listdir(folder) if fileName.endswith('.json'))
    return [loadCase(path, stateClasses) for path in paths]

def looseBodyNames(designBodies: list[tuple[str, str]], builtKeys: set[str]) -> list[str]:
    """
    Names of the bodies in a case's document the generator didn't return, by (key, name) of every body there. A body
    left over from a join that couldn't merge it stays out of the snapshot, it has to fail the case all the same
    """
    return [name for (key, name) in designBodies if key not in builtKeys]

def parametersToJson(case: TestCase) -> dict:
    return {name: round(value * 10, 6) for (name, value) in case.parameters.items()}

def caseJson(case: TestCase) -> str:
    data = {
        'description': case.description,
        'generator': case.generator,
    }
    if case.designIntent != DESIGN_INTENT_HYBRID:
        data['designIntent'] = case.designIntent
    if case.designIntentAfter is not None:
        data['designIntentAfter'] = case.designIntentAfter
    data['settings'] = stateToJson(case.generator, case.state)
    if case.parameters:
        data['parameters'] = parametersToJson(case)
    if case.texts:
        data['texts'] = dict(case.texts)
    return json.dumps(data, indent=4, ensure_ascii=False) + '\n'

# the case list in tests/e2e/README.md, see tests/e2e/write_readme.py
GENERATOR_TITLES = {GENERATOR_BIN: 'Bins', GENERATOR_BASEPLATE: 'Baseplates', GENERATOR_LABEL: 'Labels'}
README_INTRO = """# Shape snapshot tests

Each case is a JSON file in [cases](cases) holding every setting of a bin or baseplate, lengths in mm and angles in
degrees. Its snapshot in [snapshots](snapshots), a folder named after the case, has the shapes it built, their
fingerprints and a preview picture.

Run them in Fusion from Utilities > Add-ins with **Gridfinity tests: run**, record new snapshots with **Gridfinity
tests: update snapshots**. The commands are there when the add-in runs from a git checkout.

A case with parameters sets those shared user parameters once built, the snapshot is of the bodies Fusion recomputed,
and a run also compares them with the case built with the new values from the start.

This page is written from the case files, run `python3 tests/e2e/write_readme.py` after adding or changing one.
"""

# the name of a snapshot's picture, see commandSnapshotTests/snapshots.py
PREVIEW_FILE = 'preview.png'
README_PREVIEW_WIDTH = 120

def casesMarkdown(folder: str) -> str:
    """
    The cases of the folder by generator, each linked to its file, with its description and the preview of its
    snapshot, in the snapshots folder beside it, when there is one
    """
    snapshotsFolder = os.path.join(os.path.dirname(folder), 'snapshots')
    def preview(name: str) -> str:
        if not os.path.isfile(os.path.join(snapshotsFolder, name, PREVIEW_FILE)):
            return ''
        return f'<img src="snapshots/{name}/{PREVIEW_FILE}" width="{README_PREVIEW_WIDTH}" alt="{name}">'
    cases = []
    for fileName in sorted(name for name in os.listdir(folder) if name.endswith('.json')):
        with open(os.path.join(folder, fileName), encoding='utf-8') as file:
            data = json.load(file)
        description = data.get('description', '')
        if data.get('parameters'):
            edits = ', '.join(f'`{name}` {value:g} mm' for (name, value) in data['parameters'].items())
            description += f'. Sets {edits} once built, a run compares that with a build using those values from the start'
        if data.get('texts'):
            edits = ', '.join(f'`{name}` "{value}"' for (name, value) in data['texts'].items())
            description += f'. Sets {edits} once built'
        cases.append((os.path.splitext(fileName)[0], fileName, data.get('generator', ''), description))
    lines = [README_INTRO]
    for (generator, title) in GENERATOR_TITLES.items():
        section = [case for case in cases if case[2] == generator]
        if len(section) == 0:
            continue
        lines += [f'## {title}', '', '| Preview | Case | Description |', '| --- | --- | --- |']
        lines += [f'| {preview(name)} | [{name}](cases/{fileName}) | {description} |' for (name, fileName, _, description) in section]
        lines.append('')
    return '\n'.join(lines)

def caseSettings(case: TestCase) -> list[dict]:
    """The case as the settings a generated body is tagged with, so Show settings tells it's a test body and which"""
    return [
        {'title': 'Test case', 'items': [['Case', case.name], ['Description', case.description]]},
        {
            'title': 'Settings, mm and degrees',
            'items': [[name, json.dumps(value, ensure_ascii=False)] for (name, value) in stateToJson(case.generator, case.state).items()],
        },
    ] + ([{
        'title': 'Parameters set after building, mm',
        'items': [[name, json.dumps(value)] for (name, value) in parametersToJson(case).items()],
    }] if case.parameters else []) + ([{
        'title': 'Texts set after building',
        'items': [[name, json.dumps(value, ensure_ascii=False)] for (name, value) in case.texts.items()],
    }] if case.texts else [])

# A raised divider corner carries on from the compartment corner below without a ledge (p83): an upward face left
# where they meet is a sickle Nutzer found by hand, 0.36 mm2 where the fillet couldn't follow a short wall under the
# lip's chamfer. Tangent seams leave slivers of no area, which are no ledge, a corner's ledge is no wider than its
# fillet
LEDGE_MIN_AREA = 0.01
LEDGE_MAX_SIZE = 3.0

def raisedCornerLedges(faces: list[tuple[float, float, float]]) -> list[str]:
    """Notes on the ledges among the upward faces of a bin with raised dividers, each as area mm2, width and length mm"""
    return [
        f'ledge of {area:.2f} mm2 at a raised divider corner'
        for (area, width, length) in faces
        if area >= LEDGE_MIN_AREA and width <= LEDGE_MAX_SIZE and length <= LEDGE_MAX_SIZE
    ]

# A text line of an insert stays one line on the insert (p84, p70): Fusion broke a line it took for longer than its box
# in two, the second row hung off the insert. Each letter body belongs to the text line whose middle is nearest its
# own, the letters of a line form one band in height. Assigning them first keeps a descender of the upper line over
# the dots of an umlaut of the lower one from joining the lines (review of round 9). Dots are bodies of their own a
# little above their letter, a gap of up to TEXT_BAND_GAP of the line's tallest letter stays in the band; a line
# broken in two leaves a gap of half a capital and more (the user's "Welle 6mm": 2.7 mm at 5 mm)
TEXT_TOLERANCE = 0.01
TEXT_BAND_GAP = 0.2

def insertTextProblems(insert: tuple[float, float, float, float], letters: list[tuple[float, float, float, float]], lineCenters: list[float], mayRunOnRight: bool = False) -> list[str]:
    """
    Notes on the text of an insert, its box and those of its letter bodies as (min x, min y, max x, max y) in mm, the
    middles of its text lines in mm: each line one band of letters, all on the insert. A text made longer after building
    may run on past the right edge, `mayRunOnRight`
    """
    notes = []
    lines = [[] for _ in lineCenters]
    for box in letters:
        middle = (box[1] + box[3]) / 2
        nearest = min(range(len(lineCenters)), key=lambda index: abs(lineCenters[index] - middle)) if lineCenters else None
        if nearest is not None:
            lines[nearest].append(box)
    if not lineCenters and letters:
        notes.append(f'{len(letters)} text bodies on an insert without text')
    for (index, lineLetters) in enumerate(lines):
        bands = []
        gap = max(TEXT_TOLERANCE, TEXT_BAND_GAP * max((box[3] - box[1] for box in lineLetters), default=0))
        for (_, minY, _, maxY) in sorted(lineLetters, key=lambda box: box[1]):
            if bands and minY <= bands[-1][1] + gap:
                bands[-1][1] = max(bands[-1][1], maxY)
            else:
                bands.append([minY, maxY])
        if len(bands) == 0:
            notes.append(f'line {index + 1} has no text')
        elif len(bands) > 1:
            notes.append(f'line {index + 1} in {len(bands)} bands, y ' + ', '.join(f'{minY:.2f} to {maxY:.2f}' for (minY, maxY) in bands) + ' mm')
    (insertMinX, insertMinY, insertMaxX, insertMaxY) = insert
    off = [
        box for box in letters
        if box[0] < insertMinX - TEXT_TOLERANCE or box[1] < insertMinY - TEXT_TOLERANCE or box[3] > insertMaxY + TEXT_TOLERANCE
        or (not mayRunOnRight and box[2] > insertMaxX + TEXT_TOLERANCE)
    ]
    if off:
        (minX, minY, maxX, maxY) = (min(box[0] for box in off), min(box[1] for box in off), max(box[2] for box in off), max(box[3] for box in off))
        notes.append(f'{len(off)} text bodies off the insert, x {minX:.2f} to {maxX:.2f} mm, y {minY:.2f} to {maxY:.2f} mm')
    return notes

def addedLetterNames(insertName: str, corners: list[tuple[float, float]]) -> list[str]:
    """
    Names for the letter bodies a text edit added, by their (min x, min y), numbered in reading order. Fusion names
    them after the user's language and its body count ("Körper12"), the snapshot pairs bodies by name
    """
    order = sorted(range(len(corners)), key=lambda index: (round(corners[index][0], 3), round(corners[index][1], 3)))
    names = [''] * len(corners)
    for (number, index) in enumerate(order):
        names[index] = f'{insertName} text +{number + 1}'
    return names
