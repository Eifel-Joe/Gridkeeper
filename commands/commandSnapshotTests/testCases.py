import dataclasses
import json
import math
import os
import re

# Shape test cases, one JSON file each, holding the settings of a bin, baseplate or label InputState that differ from the
# dialog's defaults, see lib/defaultSettings.py, by field name in the config format of lib/configJson.py. A case
# is built the way a new bin is, a default changing changes it too.
# Kept free of Fusion imports so it can be unit tested, the state classes come in as an argument

def _loadLibFile(name: str):
    """A module of lib, when the tests and tools load this file on its own, outside the add-in package"""
    import importlib.util
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'lib', f'{name}.py')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

try:
    from ...lib import configJson
    from ...lib import defaultSettings
except ImportError:
    configJson = _loadLibFile('configJson')
    defaultSettings = _loadLibFile('defaultSettings')
GENERATOR_BIN = configJson.GENERATOR_BIN
GENERATOR_BASEPLATE = configJson.GENERATOR_BASEPLATE
GENERATOR_LABEL = configJson.GENERATOR_LABEL
GENERATOR_BOX = configJson.GENERATOR_BOX
stateFromJson = configJson.stateFromJson
stateToJson = configJson.stateToJson
# by generator
DEFAULT_SETTINGS = defaultSettings.SETTINGS

# the user parameters a case may change after building, with the setting each stands for. Keep the names literal,
# they're in user documents. Bins and baseplates have units of their own, the first of a case's new document is
# numbered 1, see binBuilder.BIN_PARAMETERS, baseplateBuilder.BASEPLATE_PARAMETERS and labelBuilder.LABEL_PARAMETERS
PARAMETER_FIELDS = {
    GENERATOR_BIN: {'gfBin1_baseWidth': 'baseWidth', 'gfBin1_baseLength': 'baseLength', 'gfBin1_heightUnit': 'heightUnit'},
    GENERATOR_BASEPLATE: {'gfPlate1_baseWidth': 'baseWidth', 'gfPlate1_baseLength': 'baseLength'},
    GENERATOR_LABEL: {'gfLabel1_baseWidth': 'baseWidth'},
    # storage boxes after Pred (round 27): grid cells and height units, counts
    GENERATOR_BOX: {'gfBox1_baseWidth': 'gridX', 'gfBox1_baseLength': 'gridY', 'gfBox1_heightU': 'heightU'},
}
# parameters that are counts, set without a unit
UNITLESS_PARAMETERS = set(PARAMETER_FIELDS[GENERATOR_BOX])

def isUnitless(name: str) -> bool:
    return name in UNITLESS_PARAMETERS

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
    # parameters set after building, in cm, the result has to be the same as built with them, see editedState
    parameters: dict[str, float] = dataclasses.field(default_factory=dict)
    designIntent: str = DESIGN_INTENT_HYBRID
    # the design intent the document has to have once built, None for any, a generator may switch it
    designIntentAfter: str | None = None
    # text parameters of an insert set after building, as a user edits its text (p70). Not compared with a build
    # from the start, that fits the text anew, see insertTextProblems
    texts: dict[str, str] = dataclasses.field(default_factory=dict)

def parametersFromJson(generator: str, parameters: dict) -> dict[str, float]:
    """Values in mm of the generator's parameters, in cm; counts (a box's size) stay as they are"""
    unknown = [name for name in parameters if name not in PARAMETER_FIELDS[generator]]
    if unknown:
        raise TestCaseError(f'unknown parameters {unknown}, a {generator} has {sorted(PARAMETER_FIELDS[generator])}')
    for (name, value) in parameters.items():
        if isUnitless(name):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise TestCaseError(f'parameter {name} has to be a whole count, not {value!r}')
        elif isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise TestCaseError(f'parameter {name} has to be a length in mm, not {value!r}')
    return {name: value if isUnitless(name) else value / 10 for (name, value) in parameters.items()}

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
        if not isinstance(data['settings'], dict):
            raise TestCaseError('settings are an object of the settings that differ from the defaults')
        state = stateFromJson(generator, stateClasses[generator], {**DEFAULT_SETTINGS[generator], **data['settings']})
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
    except (OSError, ValueError, KeyError, TypeError, AttributeError, TestCaseError, configJson.ConfigError) as err:
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

def changedSettings(generator: str, settings: dict) -> dict:
    """The settings, as stateToJson has them, that differ from the defaults"""
    defaults = DEFAULT_SETTINGS[generator]
    return {name: value for (name, value) in settings.items() if name not in defaults or value != defaults[name]}

def caseJson(case: TestCase) -> str:
    data = {
        'description': case.description,
        'generator': case.generator,
    }
    if case.designIntent != DESIGN_INTENT_HYBRID:
        data['designIntent'] = case.designIntent
    if case.designIntentAfter is not None:
        data['designIntentAfter'] = case.designIntentAfter
    data['settings'] = changedSettings(case.generator, stateToJson(case.generator, case.state))
    if case.parameters:
        data['parameters'] = parametersToJson(case)
    if case.texts:
        data['texts'] = dict(case.texts)
    return json.dumps(data, indent=4, ensure_ascii=False) + '\n'

# the case list in tests/e2e/README.md, see tests/e2e/write_readme.py
GENERATOR_TITLES = {GENERATOR_BIN: 'Bins', GENERATOR_BASEPLATE: 'Baseplates', GENERATOR_LABEL: 'Labels', GENERATOR_BOX: 'Boxes'}

# the container each generator builds into, the kind tagged on it, see tagUtils.KIND_* (round 13, p90). Every case builds
# a new part, so it goes there also in a part design, which turns hybrid for it
CONTAINER_KINDS = {GENERATOR_BIN: 'bins', GENERATOR_BASEPLATE: 'grid', GENERATOR_LABEL: 'labels', GENERATOR_BOX: 'boxes'}
# the part roles of Pred's small parts in a box set (lib/gridfinityUtils/predBoxParts.PARTS, round 28), kept here as
# this module loads without the add-in's package; tests/test_test_cases.py checks they are the same
BOX_SMALL_PART_ROLES = ['Latch', 'Handle', 'Handle pin', 'Hinge']


def smallPartBodies(generator: str, bodies: list[tuple[str, str | None]]) -> list[str]:
    """
    Of (key, part role of the body's component) the keys of a box set's small parts. buildBox returns their bodies
    untagged after box and lid (round 28); without this structureNotes took them for marking bodies outside a Text
    component and failed every box case. Test: tests/test_test_cases.py
    """
    if generator != GENERATOR_BOX:
        return []
    return [key for (key, role) in bodies if role in BOX_SMALL_PART_ROLES]

def expectedContainer(generator: str) -> str:
    return CONTAINER_KINDS[generator]
README_INTRO = """# Shape snapshot tests

Each case is a JSON file in [cases](cases) holding the settings of a bin, baseplate or label that differ from the dialog's
defaults in [lib/defaultSettings.py](../../lib/defaultSettings.py), lengths in mm and angles in degrees. Its snapshot in
[snapshots](snapshots), a folder named after the case, has the shapes it built, their fingerprints, every setting they
were built with and a preview picture. A run tells when the settings changed, a default changing among them, even
when the shapes stay the same.

Run them in Fusion from Utilities > Add-ins with **Gridkeeper tests: run**, record new snapshots with **Gridkeeper
tests: update snapshots**. The commands are there when the add-in runs from a git checkout.

A case with parameters sets those user parameters once built, the snapshot is of the bodies Fusion recomputed,
and a run also compares them with the case built with the new values from the start.

This page is written from the case files, run `python3 tests/e2e/write_readme.py` after adding or changing one.
"""

# the name of a snapshot's picture, see commandSnapshotTests/snapshots.py
PREVIEW_FILE = 'preview.png'
# every setting of the case its snapshot was built with, see snapshotSettings
SETTINGS_FILE = 'settings.json'
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

def snapshotSettings(case: TestCase) -> dict:
    """Every setting the case is built with, its defaults filled in, as its snapshot keeps them"""
    return stateToJson(case.generator, case.state)

def settingsText(settings: dict) -> str:
    return json.dumps(settings, indent=4, ensure_ascii=False) + '\n'

def settingChanges(expected: dict, actual: dict, defaults: dict | None = None) -> list[dict]:
    """
    Each setting that differs, as the snapshot was built with it and as the case has it now, none for a setting only
    one of them has. Values that aren't numbers, flags or text are written as JSON, the report shows them as they are.
    A setting the snapshot doesn't have, newer than it, is no change where the case has it at its default, one of
    defaults (round 16, p30): the snapshot was built the way the default builds
    """
    def shown(value):
        return value if value is None or isinstance(value, (bool, int, float, str)) else json.dumps(value, ensure_ascii=False)
    def same(a, b) -> bool:
        # a flag isn't the number it equals in Python
        if isinstance(a, bool) or isinstance(b, bool):
            return type(a) is type(b) and a == b
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
        return a == b
    defaults = defaults or {}
    def isNewerAtDefault(name) -> bool:
        return name not in expected and name in actual and name in defaults and same(defaults[name], actual[name])
    names = list(expected) + [name for name in actual if name not in expected]
    return [
        {'key': name, 'expected': shown(expected.get(name)), 'actual': shown(actual.get(name))}
        for name in names
        if (name not in expected or name not in actual or not same(expected[name], actual[name])) and not isNewerAtDefault(name)
    ]


def isTextLabelCase(generator: str, settings: dict) -> bool:
    """A bin with a text label on its tab, its own or a compartment's: where its letters lie depends on the font and the
    Fusion version, its snapshot is compared by form (round 16, p30, see formChanges). Cullenect tabs carry no text"""
    if generator != GENERATOR_BIN or not settings.get('hasTab') or settings.get('labelStyle') == 'Cullenect':
        return False
    # compartment labels as the bin builder takes them, only with the layout shown (review round 16); a creased bin
    # drops them too, which isn't worked out here
    pockets = (settings.get('compartmentPockets') or []) if settings.get('showCompartmentsLayout') else []
    return bool(str(settings.get('labelText') or '').strip()) or any(str(pocket.get('label') or '').strip() for pocket in pockets)


# how thick a leftover of letters lying elsewhere can be, mm: the label depth of 0.5 mm and a little
LETTER_SLAB = 0.6


def isLetterSlab(leftover: dict | None) -> bool:
    """Whether what a subtraction left over, snapshots.leftoverData, is no thicker than the letters of a label: where
    they lie depends on the font (round 16, p30). A tab or label moved by a change leaves more (review round 16)"""
    if leftover is None:
        return True
    return leftover['max'][2] - leftover['min'][2] <= LETTER_SLAB


def _close(expected: float, actual: float) -> bool:
    # as snapshots.isClose, relative to the size of the numbers
    return abs(expected - actual) <= 1e-6 * max(abs(expected), abs(actual), 1)


def formChanges(expected: list[dict], built: list[dict]) -> list[dict]:
    """
    The form of the bodies against the snapshot's, fingerprints as in snapshots.fingerprint: how many bodies, their
    volume together and the box around all of them, not where each letter body lies (round 16, p30). Each that differs
    """
    def box(entries):
        if not entries:
            return ([], [])
        return ([min(entry['bboxMin'][axis] for entry in entries) for axis in range(3)], [max(entry['bboxMax'][axis] for entry in entries) for axis in range(3)])
    changes = []
    if len(expected) != len(built):
        changes.append({'key': 'bodies', 'expected': len(expected), 'actual': len(built)})
    (expectedVolume, builtVolume) = (sum(entry['volume'] for entry in expected), sum(entry['volume'] for entry in built))
    if not _close(expectedVolume, builtVolume):
        changes.append({'key': 'volume', 'expected': round(expectedVolume, 6), 'actual': round(builtVolume, 6)})
    ((expectedMin, expectedMax), (builtMin, builtMax)) = (box(expected), box(built))
    for (key, a, b) in (('bboxMin', expectedMin, builtMin), ('bboxMax', expectedMax, builtMax)):
        if len(a) != len(b) or not all(_close(x, y) for (x, y) in zip(a, b)):
            changes.append({'key': key, 'expected': a, 'actual': b})
    return changes


def runChecks(checks: list) -> list[str]:
    """
    The notes of the checks after a case is built, (name, function giving its notes) in order. A check that breaks is a
    note of its own, a check failure, not a build failure (round 16, p34)
    """
    notes = []
    for (name, check) in checks:
        try:
            notes += check()
        except Exception as err:
            notes.append(f'check {name} failed, {err}')
    return notes

# A raised divider corner carries on from the compartment corner below without a ledge (p83): an upward face left
# where they meet is a sickle found by hand, 0.36 mm2 where the fillet couldn't follow a short wall under the
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
# broken in two leaves a gap of half a capital and more (the "Welle 6mm" label: 2.7 mm at 5 mm)
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

def colorProblems(appearanceName: str, base: tuple[str, str | None], parts: list[tuple[str, str | None]]) -> list[str]:
    """
    What is wrong with the colors of a colored case (p86): every text and symbol body has the appearance of the label
    color, the insert or bin itself doesn't. base and parts as (body name, appearance name), the appearance a body
    shows, None for none of its own
    """
    problems = []
    if len(parts) == 0:
        problems.append('no colored label bodies')
    if base[1] == appearanceName:
        problems.append(f'{base[0]} has the label color')
    problems += [f'{name} is {appearance}, not {appearanceName}' for (name, appearance) in parts if appearance != appearanceName]
    return problems
