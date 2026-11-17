import adsk.core, adsk.fusion
import json
import os

# Tags are stored in user documents, keep these literal so they don't change with add-in config
TAG_GROUP = 'LevMishin.GridfinityGenerator'
TAG_BIN = 'bin'
TAG_BASEPLATE = 'baseplate'
# Cullenect inserts of the label command
TAG_LABEL = 'label'
# storage boxes after Pred (round 27), on the box and on the lid body
TAG_BOX = 'box'
# the box label's plate (round r29-export, p380), a tag of its own: readBodyTag leaves it out, the settings menu and
# rebuild would take it for a Cullenect insert. Its config holds the surface only, for the export's print orientation
TAG_BOX_LABEL = 'boxLabel'
# on a user parameter of a bin, the config field its value is, see tagParameterField
TAG_PARAMETER_FIELD = 'parameterField'
# name of the component of a part holding its colored text and symbol bodies (round 13, p90), a copy is named
# "Text (1)", see assembly.TextOccurrence
TEXT_COMPONENT_NAME = 'Text'
# on the component holding the parts of a kind, the value is the kind, see lib/gridfinityUtils/assembly.py (round 13)
TAG_CONTAINER = 'container'
KIND_GRID = 'grid'
KIND_BINS = 'bins'
KIND_LABELS = 'labels'
KIND_BOXES = 'boxes'
# names the containers get, Nutzer 15.11.2026, the user may rename them, they are found by the tag
CONTAINER_NAMES = {KIND_GRID: 'Grid', KIND_BINS: 'Bins', KIND_LABELS: 'Label', KIND_BOXES: 'Boxes'}
# on the joint origin of a Cullenect pocket, the value holds its size in mm, see cullenect.pocketTagValue
TAG_POCKET = 'pocket'
# on a component inside a part, its role there (a box set: 'Box', 'Lid'). Fusion names the components of a second
# set "Box (1)", "Lid (1)", a rebuild finds the matching one by the role (round 27)
TAG_PART_ROLE = 'partRole'

# Bump only on incompatible changes to the tag value, readers ignore fields they don't know
TAG_SCHEMA_VERSION = 1

MANIFEST_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Gridkeeper.manifest')

_generatorVersion = None

def getGeneratorVersion() -> str:
    global _generatorVersion
    if _generatorVersion is None:
        try:
            with open(MANIFEST_PATH, 'r') as manifest:
                _generatorVersion = str(json.load(manifest).get('version', ''))
        except (OSError, ValueError, AttributeError):
            _generatorVersion = ''
    return _generatorVersion

def createTagValue(
    generatorVersion: str,
    settings: list[dict] = None,
    parameters: list[list[str]] = None,
    config: dict = None,
    field: str = None,
    bodyId: str = None,
    owner: str = None,
) -> str:
    """Settings are the dialog inputs the body was generated with, as sections of label and value pairs,
    parameters are label and name pairs of the user parameters driving it, config the settings to build it again
    by field name, see configJson.stateToJson. Field is the config field a user parameter holds. bodyId names the
    bin or baseplate, unique in the design, its own parameters have it as their owner and as the prefix of their names"""
    value = {
        'schemaVersion': TAG_SCHEMA_VERSION,
        'generatorVersion': generatorVersion,
    }
    if settings is not None:
        value['settings'] = settings
    if parameters is not None:
        value['parameters'] = parameters
    if config is not None:
        value['config'] = config
    if bodyId is not None:
        value['id'] = bodyId
    if field is not None:
        value['field'] = field
    if owner is not None:
        value['owner'] = owner
    return json.dumps(value)

def parseTagValue(value: str) -> dict:
    """The tag's presence is what marks an entity, so an unreadable value still yields a dict"""
    try:
        data = json.loads(value)
    except (TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}

def tagBody(body: adsk.fusion.BRepBody, tagName: str, settings: list[dict] = None, parameters: list[list[str]] = None, config: dict = None, bodyId: str = None):
    """bodyId links the body with its parameters, see tagParameterField"""
    body.attributes.add(TAG_GROUP, tagName, createTagValue(getGeneratorVersion(), settings, parameters, config, bodyId=bodyId))

def readExportTag(body: adsk.fusion.BRepBody) -> tuple[str, dict] | None:
    """The tag the export knows a part by: a generator's, see readBodyTag, or the box label's"""
    tag = readBodyTag(body)
    if tag is not None:
        return tag
    attribute = body.attributes.itemByName(TAG_GROUP, TAG_BOX_LABEL)
    return (TAG_BOX_LABEL, parseTagValue(attribute.value)) if attribute is not None else None

def readBodyTag(body: adsk.fusion.BRepBody) -> tuple[str, dict] | None:
    """Which generator tagged the body and the tag value, none for bodies it didn't generate"""
    for tagName in (TAG_BIN, TAG_BASEPLATE, TAG_LABEL, TAG_BOX):
        attribute = body.attributes.itemByName(TAG_GROUP, tagName)
        if attribute is not None:
            return (tagName, parseTagValue(attribute.value))
    return None

def partTag(body: adsk.fusion.BRepBody, occurrenceOf) -> tuple[adsk.fusion.BRepBody, str, dict] | None:
    """
    The generated body that answers for the body, native, with its tag: the body itself when it has one, else for a body
    in a Text component the first tagged body of the part one level up, none when there's neither. Letters a longer text adds come out of the
    extrusion untagged, in the Text component of their bin or insert (round 14, p71), the part answers for them.
    A body selected in the design is a proxy whose occurrence is its assemblyContext, a native one is looked up by its
    component with occurrenceOf, which gives None for the root
    """
    native = body.nativeObject or body
    tag = readBodyTag(native)
    if tag is not None:
        return (native, *tag)
    # only a letter in Text: a bin nested in the user's own assembly would answer for the user's bodies otherwise
    if not native.parentComponent.name.startswith(TEXT_COMPONENT_NAME):
        return None
    occurrence = body.assemblyContext if body.nativeObject is not None else occurrenceOf(native.parentComponent)
    part = occurrence.assemblyContext if occurrence is not None else None
    if part is None:
        return None
    for partBody in part.component.bRepBodies:
        partBodyTag = readBodyTag(partBody)
        if partBodyTag is not None:
            return (partBody, *partBodyTag)
    return None

def taggedBodies(bodies: list[adsk.fusion.BRepBody], tagName: str) -> list[adsk.fusion.BRepBody]:
    """
    The bodies with the tag, in their order. A bin's colored labels are bodies of their own without one, a rebuild
    pairs only the bin bodies with the old ones, see rebuildUtils.bodyMap
    """
    return [body for body in bodies if body.attributes.itemByName(TAG_GROUP, tagName) is not None]

def findTaggedBodies(design: adsk.fusion.Design, tagName: str) -> list[tuple[adsk.fusion.BRepBody, dict]]:
    """Returns native bodies, bodies inside components still need an occurrence for their placement"""
    taggedBodies = []
    for attribute in design.findAttributes(TAG_GROUP, tagName):
        body = adsk.fusion.BRepBody.cast(attribute.parent)
        if body is not None:
            taggedBodies.append((body, parseTagValue(attribute.value)))
    return taggedBodies

def tagParameterField(parameter: adsk.fusion.UserParameter, field: str, owner: str):
    """
    The config field the parameter's value is, see configJson.stateToJson, like binHeight, or an item's field by its
    index like compartmentPockets.2.label, and the id of the bin or baseplate it's of, see tagBody. Tagging again
    replaces it
    """
    parameter.attributes.add(TAG_GROUP, TAG_PARAMETER_FIELD, createTagValue(getGeneratorVersion(), field=field, owner=owner))

def readParameterTag(parameter: adsk.fusion.UserParameter) -> dict:
    """The field and owner the parameter was tagged with, empty for parameters made before they were tagged"""
    attribute = parameter.attributes.itemByName(TAG_GROUP, TAG_PARAMETER_FIELD)
    return parseTagValue(attribute.value) if attribute is not None else {}

def readParameterField(parameter: adsk.fusion.UserParameter) -> str | None:
    field = readParameterTag(parameter).get('field')
    return field if isinstance(field, str) and field else None

def findOwnedParameters(design: adsk.fusion.Design, owner: str) -> list[tuple[adsk.fusion.UserParameter, str]]:
    """The parameters of the bin or baseplate with that id, see tagBody, with the config field each holds"""
    owned = []
    for attribute in design.findAttributes(TAG_GROUP, TAG_PARAMETER_FIELD):
        parameter = adsk.fusion.UserParameter.cast(attribute.parent)
        value = parseTagValue(attribute.value)
        if parameter is not None and value.get('owner') == owner and isinstance(value.get('field'), str):
            owned.append((parameter, value['field']))
    return owned

def usedBodyIds(design: adsk.fusion.Design, tagName: str) -> set[str]:
    """The ids of the bodies with the tag, so a new one gets another, see tagBody"""
    return {str(tag['id']) for (_, tag) in findTaggedBodies(design, tagName) if tag.get('id')}


# the part of a set whose body answers for the set in the right-click menu: a box set's components are Box and Lid
# (boxBuilder.BOX_COMPONENT_NAME, kept as their part role), the settings sit on both, the box stands for the set
SET_ANSWERING_ROLE = 'Box'

def menuTagOf(ownTags: list[tuple], children: list[tuple[str, list[tuple]]]) -> tuple | None:
    """
    What a component selected in the browser stands for in the right-click menu: its one tagged body; for a box set,
    which holds no body itself, the body of its component with the role Box (click test 17.11.2026, F1: the menu on
    "Box 5×4×6" had export only, rebuild, settings and clone stood on Box:1 alone). Children are (part role, tags)
    """
    if ownTags:
        return ownTags[0] if len(ownTags) == 1 else None
    answering = [tags for (role, tags) in children if role == SET_ANSWERING_ROLE]
    return answering[0][0] if len(answering) == 1 and len(answering[0]) == 1 else None
