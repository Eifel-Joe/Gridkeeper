"""
The config of a Cullenect insert from the label command (round 18, p150), saved, loaded, cloned and rebuilt like the
bins' and baseplates' (upstream v2.4 by Le0Michine, see configJson and rebuildUtils). Plain math, no Fusion.

Settings are by field name as configJson.stateToJson has them: lengths in mm, the screw blocks and hardware by their
Cullenect names. The dialog shows those by their display names, the surface by its own name and the color as a choice
and a custom text.
"""

from . import cullenectCatalog, labelColors

NO_HARDWARE = 'none'
NO_HARDWARE_NAME = 'None'
SCREW_FIELDS = ['head', 'shaft', 'threads', 'driver']

# the insert's parameters a rebuild takes over, by the label the tag gives them (labelBuilder.labelParameters), see
# rebuildUtils.configWithParameters. The width itself follows from them and the config
PARAMETER_FIELDS = {
    'Base width unit': 'baseWidth',
    'Text line 1': 'line1',
    'Text line 2': 'line2',
}


def dialogValues(settings: dict, surfaceNames: dict[str, str]) -> dict:
    """The settings as the dialog shows them, see settingsOfDialog for the way back"""
    values = {name: value for (name, value) in settings.items() if name != 'textColor'}
    for field in SCREW_FIELDS:
        values[field] = cullenectCatalog.displayName(settings[field])
    values['hardware'] = NO_HARDWARE_NAME if settings['hardware'] == NO_HARDWARE else cullenectCatalog.displayName(settings['hardware'])
    values['surface'] = surfaceNames[settings['surface']]
    (values['colorChoice'], values['customColor']) = labelColors.choiceOf(settings['textColor'])
    return values


def _keyOf(name: str, keys: list[str]) -> str:
    """The Cullenect name of a shown name, the name itself when no key shows as it"""
    return next((key for key in keys if cullenectCatalog.displayName(key) == name), name)


def settingsOfDialog(values: dict, surfaceNames: dict[str, str], screwOptions: dict[str, list], hardwareKeys: list[str]) -> dict:
    """The settings of what the dialog shows, the way back of dialogValues"""
    settings = {name: value for (name, value) in values.items() if name not in ('colorChoice', 'customColor')}
    for field in SCREW_FIELDS:
        settings[field] = _keyOf(values[field], screwOptions[field])
    settings['hardware'] = NO_HARDWARE if values['hardware'] == NO_HARDWARE_NAME else _keyOf(values['hardware'], hardwareKeys)
    settings['surface'] = next((key for (key, name) in surfaceNames.items() if name == values['surface']), values['surface'])
    settings['textColor'] = labelColors.dialogColor(values['colorChoice'], values['customColor'])
    return settings


def rebuildCorner(oldBox: tuple[float, float, float, float]) -> tuple[float, float]:
    """Where a rebuilt insert is drawn: the bottom left corner of the old one, (min x, min y, max x, max y) in its
    component, so it stays where it was however its width changes"""
    return (oldBox[0], oldBox[1])
