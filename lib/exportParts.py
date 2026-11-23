"""
What the export takes as a part (upstream round 17.11.2026, p300). Upstream's export knew bins and baseplates only,
ours exports every part the generators make, and the colored text and symbol bodies of a part (p86, in its Text
component, round 13, p90) go into the part's mesh, painted for the slicer. No Fusion imports, so it is testable, the
export command (commands/commandExport) finds the bodies.
"""

import dataclasses

# The tags of the bodies the export takes, as tagUtils writes them (tags are literals, they're stored in documents).
# 'box' is the box and the lid of round 27, there from its merge on. A new part, the small parts of round 28 or the box
# label (p262), is one more entry here and in tests/test_export_parts.py
EXPORT_TAGS = ('bin', 'baseplate', 'label', 'box', 'boxLabel')

# Pred's small parts in a box set (round 28): untagged, their component carries the part role (tagUtils.TAG_PART_ROLE);
# the same roles as lib/gridfinityUtils/predBoxParts.PARTS, tests/test_export_parts.py checks it
SMALL_PART_ROLES = ('Latch', 'Handle', 'Handle pin', 'Hinge')

# the component of a part holding its colored text and symbol bodies, tagUtils.TEXT_COMPONENT_NAME, a copy of it is
# named "Text (1)", see tagUtils.partTag
TEXT_COMPONENT_NAME = 'Text'


def partFileName(bodyName: str, setName: str | None) -> str:
    """
    The file name of a part's body: a body of a set, the box's Base and Lid and its small parts, carries the set's name
    in front, "Box 5×4×6 Base"; every box gave "Base.stl", "Base (2).stl" before (click test 17.11.2026, F3)
    """
    if not setName or bodyName.startswith(setName):
        return bodyName
    return f'{setName} {bodyName}'


def isExportTag(tagName: str | None) -> bool:
    return tagName in EXPORT_TAGS


def isTextComponentName(name: str, isRoot: bool = False) -> bool:
    """
    The same test as tagUtils.partTag, so the export and the right-click menu agree on a part's letters. Never the
    root component: it is named after the document, which may well start with "Text" (review 17.11.2026)
    """
    return not isRoot and name.startswith(TEXT_COMPONENT_NAME)


def isPartBody(tagName: str | None, componentName: str, isRoot: bool = False, role: str | None = None) -> bool:
    """
    A body exported as a part of its own. The text bodies of a Cullenect insert are tagged like its base, they go with
    the base instead. A small part of a box set is one by its component's role (review round 28: the export left them
    out, a right-click on a set gave Base and Lid only)
    """
    if role in SMALL_PART_ROLES:
        return True
    return isExportTag(tagName) and not isTextComponentName(componentName, isRoot)


def partBodiesUnder(occurrence, *, isText, parentOf, childrenOf, bodiesOf, isPart) -> list:
    """
    The part bodies of an occurrence and the occurrences in it, for the right-click menu on a component or container.
    A Text occurrence stands for its part, climbed to once at the start; Text occurrences below aren't walked into,
    their letters come with their part. Climbing in the walk itself went back and forth between a part and its Text
    until the recursion limit (review 17.11.2026)
    """
    if isText(occurrence) and parentOf(occurrence) is not None:
        occurrence = parentOf(occurrence)

    def walk(current) -> list:
        found = [body for body in bodiesOf(current) if isPart(body)]
        for child in childrenOf(current):
            if not isText(child):
                found += walk(child)
        return found

    return walk(occurrence)


def exportTargets(bodies: list, partOf, key) -> list:
    """
    The bodies to export for the selected ones, in their order, each once: a letter stands for its part, partOf gives
    what a body stands for, itself when it is a part or nothing generated. key tells two apart, a body placed twice is
    two
    """
    targets = []
    keys = []
    for body in bodies:
        target = partOf(body)
        targetKey = key(target)
        if targetKey not in keys:
            keys.append(targetKey)
            targets.append(target)
    return targets


def withMarkings(part, markings: list):
    """
    The part's mesh (threeMf.MeshObject) with the meshes of its text and symbol bodies added, where they are, so the
    slicer gets the part whole. markings are (mesh, filament) pairs: every triangle of a marking with a filament is
    painted with it, each color on its own (round 37, p301), none leaves it unpainted. The part's own painted letters
    (outline labels) stay painted as they are
    """
    if len(markings) == 0:
        return part
    vertices = list(part.vertices)
    triangles = list(part.triangles)
    painted = dict(part.painted)
    for (marking, filament) in markings:
        offset = len(vertices)
        vertices += marking.vertices
        for triangle in marking.triangles:
            if filament is not None:
                painted[len(triangles)] = filament
            triangles.append(tuple(vertex + offset for vertex in triangle))
    return dataclasses.replace(part, vertices=vertices, triangles=triangles, painted=painted)


# Round r29-export (spec dev-notes/specs/2026-11-17-r29-export-drucklage.md): what the print layout needs of a part,
# and the dialog's bed, spacing and purge choices

# the printer preset (lib/printBeds.py) the export starts on with no printer chosen before, Bambu Lab's X1 Carbon, a
# common printer (round 55: one entry per printer, until then the shared P1 and X1 entry)
DEFAULT_BED = 'Bambu Lab X1 Carbon (256 x 256 mm)'
DEFAULT_BED_SIZE = 256.0
CUSTOM_BED = 'Custom'
# Round 55 (p680): for a Bambu Lab printer the 3MF is one Bambu Studio project with all plates or a file per plate,
# the names as upstream 1ac1579 has them; other printers always get a file per plate
FILES_ONE = 'One Bambu Studio project with all plates'
FILES_PER_PLATE = 'A file per plate'
FILES_CHOICES = [FILES_ONE, FILES_PER_PLATE]
# the project's filament colors: the parts' filament 1 and a filament no label color has grey, text without a color
# black (spec round 55)
PART_COLOUR = '#808080'
NO_COLOR_COLOUR = '#000000'
# mm, 17.11.2026 (D2), see printLayout
DEFAULT_SPACING = 5.0
DEFAULT_PURGE = 50.0


def labelSurface(tag: tuple | None) -> str | None:
    """The surface of a Cullenect insert or box label (Embossed, Debossed, Flush) from its tag, none for every other part"""
    if tag is None or tag[0] not in ('label', 'boxLabel') or not isinstance(tag[1], dict):
        return None
    settings = tag[1].get('config')
    return settings.get('surface') if isinstance(settings, dict) else None


def printGroupKey(role: str | None, occurrencePath: str | None, rotation: str) -> tuple:
    """
    What lays a part out together with others: the halves of a hinge, one occurrence and one turn. Every other part goes
    alone (review r29-export: the pieces of a filled area are bodies of one baseplate component, they were glued into
    one block larger than the bed)
    """
    return (occurrencePath if role == 'Hinge' and occurrencePath is not None else None, rotation)


def printGroups(keys: list) -> list[list[int]]:
    """
    The parts laid out as one block, by index, in order: those of one place and one turn (the halves of a hinge, one
    occurrence), a part without a place (key None) alone
    """
    groups: list[list[int]] = []
    found: dict = {}
    for (index, key) in enumerate(keys):
        if key[0] is None:
            groups.append([index])
        elif key in found:
            found[key].append(index)
        else:
            found[key] = [index]
            groups.append(found[key])
    return groups


def layoutChoices(section: dict, bedNames: list[str], lastPrinter: str | None = None, presets: dict | None = None,
                  oldNames: dict | None = None) -> dict:
    """
    The saved bed, its size, spacing and purge square in mm, the defaults for what is missing or broken. configparser
    gives its keys in lower case (review r29-export: bedWidth was never read back). The printer chosen last in the
    baseplate or export dialog comes first (round 55, decided 23.11.2026), a preset brings its own size, Custom the
    size the export saved. A saved name gone from the list is read as the one it is now, see printBeds.OLD_BED_NAMES
    """
    section = {str(key).lower(): value for (key, value) in section.items()}
    def number(key: str, default: float, minimum: float) -> float:
        try:
            value = float(section.get(key, default))
        except (TypeError, ValueError):
            return default
        return value if value >= minimum and value == value else default

    bed = lastPrinter if lastPrinter is not None else section.get('bed', DEFAULT_BED)
    # the shared entries before the Bambu Lab printers were apart (click test 17.11.2026, round 55)
    bed = (oldNames or {}).get(bed, bed)
    bed = bed if bed in bedNames else CUSTOM_BED
    (width, length) = (presets or {}).get(bed) or (number('bedwidth', DEFAULT_BED_SIZE, 1e-6), number('bedlength', DEFAULT_BED_SIZE, 1e-6))
    return {
        'bed': bed,
        'bedWidth': float(width),
        'bedLength': float(length),
        'spacing': number('spacing', DEFAULT_SPACING, 0),
        'purge': number('purge', DEFAULT_PURGE, 0),
        'files': section.get('files') if section.get('files') in FILES_CHOICES else FILES_ONE,
    }


def replaceQuestion(replaced: list[str], removed: list[str], folder: str, listed: int) -> str:
    """
    The question before an export overwrites files, by name: those it replaces, and the plate files of an earlier
    export it removes (review r29-export: they were asked for as replaced), a few listed and the rest counted
    """
    parts = []
    if replaced:
        parts.append(f'replace {"the existing file" if len(replaced) == 1 else f"{len(replaced)} existing files"}')
    if removed:
        parts.append(f'remove {len(removed)} plate file{"" if len(removed) == 1 else "s"} of an earlier export')
    question = ' and '.join(parts)
    names = replaced + removed
    shown = names[:listed] + ([f'and {len(names) - listed} more'] if len(names) > listed else [])
    return f'{question[0].upper()}{question[1:]} in {folder}?\n\n' + '\n'.join(shown)


def plateKind(role: str | None, tagName: str | None, bodyName: str, setName: str | None) -> tuple | None:
    """
    Which plates a part may share, see printLayout.layOutKinds: a box set's box, its lid and its small parts each
    plates of their own, per set (17.11.2026: the box accessories go on a separate plate, a box
    gives 3 plates in all depending on its size). A box built as bodies in the root has no set, its Base and Lid
    are told by name. None for every other part, they share plates
    """
    if role in SMALL_PART_ROLES:
        return (setName, 'parts')
    if role == 'Lid' or (role is None and tagName == 'box' and bodyName == 'Lid'):
        return (setName, 'lid')
    if role == 'Box' or (role is None and tagName == 'box'):
        return (setName, 'box')
    return None


# Round 37 (p301, spec dev-notes/specs/2026-11-18-r37-export-filaments.md): each label color on a filament of its own.
# A color is '#RRGGBB' as labelColors has it, '' the label text without a color (outline letters, text left
# uncolored). The bodies print on filament 1, the slicer's filament of the object

# the most filaments a painted triangle can name, threeMf.MAX_FILAMENT
MAX_FILAMENT = 18
FIRST_LABEL_FILAMENT = 2
# the saved name of the text without a color
NO_COLOR_KEY = 'none'


def distinctLabelColors(perPart: list[list[str]]) -> list[str]:
    """
    The label colors of the parts, each once in the order found. A part's letters are often several marking bodies of
    one color, so a color repeats within a part as well as across parts. With repeats the export dialog's color list
    never matched its spinners, and every input change rebuilt them, the one being changed included
    """
    colors = []
    for color in (color for found in perPart for color in found):
        if color not in colors:
            colors.append(color)
    return colors


def filamentChoices() -> list[str]:
    """
    The items of a color's filament list in the export dialog, 1 to MAX_FILAMENT. A list, not a spinner: Fusion drops
    a number typed into a spinner when OK is clicked straight from the field (click test round 37)
    """
    return [str(number) for number in range(1, MAX_FILAMENT + 1)]


def filamentOfChoice(name: str | None) -> int | None:
    """The filament of a list item, see filamentChoices, none for anything else"""
    return int(name) if name in filamentChoices() else None


def keepTypedFilaments(changed: dict[str, int], shown: dict[str, int], assigned: dict[str, int]) -> dict[str, int]:
    """
    The filaments changed by hand in the dialog: those already known and each shown one that isn't the number it was
    assigned. The dialog reads its filament lists before it rebuilds them, so a number changed whose change event
    didn't reach us still stays (the spinners used first lost typed numbers that way, click test round 37).
    Numbers left as assigned stay automatic and may change with the selection; for a color changed before, the number
    shown wins, also when it's back at the assigned one (review round 37)
    """
    typed = {color: filament for (color, filament) in shown.items() if color in changed or assigned.get(color) != filament}
    return {**changed, **typed}


def assignFilaments(colors: list[str], saved: dict[str, int]) -> dict[str, int]:
    """
    The filament of each label color of an export, in their order: the saved one, else the lowest from 2 no other color
    has, of the export or saved. Saved ones count too: red exported alone got 2, blue alone 2 as well, together they
    shared it unasked (review round 37). With every filament saved, the lowest no other color of the export has; past
    the last filament the colors share it
    """
    assigned = {color: saved[color] for color in colors if color in saved}
    numbers = range(FIRST_LABEL_FILAMENT, MAX_FILAMENT + 1)
    for color in colors:
        if color in assigned:
            continue
        taken = set(assigned.values())
        everTaken = taken | set(saved.values())
        assigned[color] = next((number for number in numbers if number not in everTaken), None) \
            or next((number for number in numbers if number not in taken), MAX_FILAMENT)
    return {color: assigned[color] for color in colors}


def formatLabelFilaments(mapping: dict[str, int]) -> str:
    """How the dialog saves them, 'D02020=2,none=4'"""
    return ','.join(f'{color.lstrip("#") or NO_COLOR_KEY}={number}' for (color, number) in mapping.items())


def parseLabelFilaments(text: str) -> dict[str, int]:
    """The saved ones back, see formatLabelFilaments, a broken entry left out"""
    mapping = {}
    for entry in text.split(','):
        (name, _, number) = entry.strip().partition('=')
        name = name.strip().upper()
        if name == NO_COLOR_KEY.upper():
            color = ''
        elif len(name) == 6 and all(digit in '0123456789ABCDEF' for digit in name):
            color = f'#{name}'
        else:
            continue
        try:
            value = int(number)
        except ValueError:
            continue
        if 1 <= value <= MAX_FILAMENT:
            mapping[color] = value
    return mapping


def mergeLabelFilaments(saved: dict[str, int], shown: dict[str, int]) -> dict[str, int]:
    """The saved ones with those of the dialog, a color not shown keeps its filament for the next export"""
    return {**saved, **shown}


def labelFilamentChoices(section: dict) -> dict[str, int]:
    """
    The saved filaments of the label colors. An export before round 37 saved one filament for all label text,
    colorIndex: it stays the one of the text without a color, so outline letters print as before. configparser gives
    its keys in lower case
    """
    section = {str(key).lower(): value for (key, value) in section.items()}
    mapping = parseLabelFilaments(section.get('labelfilaments', ''))
    if '' not in mapping:
        try:
            index = int(section.get('colorindex', ''))
        except ValueError:
            index = 0
        if 1 <= index <= MAX_FILAMENT:
            mapping[''] = index
    return mapping


def filamentColours(filaments: dict[str, int] | None) -> list[str]:
    """
    The colors of the Bambu Studio project's filaments, one per filament up to the last a label color has: the parts'
    filament 1 grey, each label color's its own, text without a color black, those in between grey (round 55). Colors
    sharing a filament, past the last one, show the first
    """
    colours = [PART_COLOUR] * max([1, *(filaments or {}).values()])
    shown = set()
    for (color, filament) in (filaments or {}).items():
        if filament in shown or filament < FIRST_LABEL_FILAMENT:
            continue
        shown.add(filament)
        colours[filament - 1] = color or NO_COLOR_COLOUR
    return colours


def bambuNotice(profiles, plates: int) -> str:
    """
    What the export asks before it saves a Bambu Studio project (round 55, decided 23.11.2026): it comes with Bambu
    Studio's standard profiles of the printer chosen, the user may have to change them. printBeds.BambuProfiles.
    Round 56 (p690, decided 23.11.2026): for two nozzles, where the purging volumes come from and that the user decides
    on them, see threeMf.flushSettings. Round 57: every Bambu printer's project brings purging volumes, the sentence on
    them is for all, the one on the nozzles for two
    """
    which = 'its plate' if plates == 1 else f'all {plates} plates'
    nozzles = (
        " Bambu Studio puts the filaments on the nozzles so it purges least; change that and the volumes there if you want."
    ) if profiles.extruders > 1 else ''
    purging = (
        "The purging volumes come from Bambu Studio's color formula; for its own filament colors Bambu Studio has its "
        f"own values, Re-calculate under Purging volumes takes them.{nozzles}\n\n"
    )
    return (
        f"This file is a Bambu Studio project with {which}. It comes with Bambu Studio's standard profiles: "
        f"{profiles.printer}, {profiles.process}, Bambu PLA Basic for every filament and the Textured PEI Plate. "
        "Change them in Bambu Studio to your printer, nozzle, filament and plate where they differ.\n\n"
        f"{purging}OK saves the project, Cancel saves nothing."
    )
