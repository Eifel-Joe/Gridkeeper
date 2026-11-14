import adsk.core, adsk.fusion

from . import labelColors, commonUtils

# The appearance label text and symbols are colored with (p86), see labelColors. It is a library appearance copied
# into the document and recolored, as Fusion does when one is dragged onto a body and recolored, and found again by
# its name next time. Library names are in the user's language (p31), so none is looked up by its full name: the
# best ranked one with a main color is taken, see labelColors.baseCandidates

# ids of the main color of Fusion's appearances, generic plastics, paints and metals
COLOR_PROPERTY_IDS = ['opaque_albedo', 'generic_diffuse', 'metal_f0']

class AppearanceError(Exception):
    pass

def colorProperty(appearance: adsk.core.Appearance, writable: bool = True) -> adsk.core.ColorProperty | None:
    """The main color it's drawn with, the one Fusion's appearance editor shows first, none when it has none. The
    colors of a library appearance are read-only, only those of its copy in a design can be set (p86, 14.11.2026:
    "Kunststoff - matt (Rot)" opaque_albedo read-only, so a writable wood of the favorites was taken)"""
    properties = appearance.appearanceProperties
    found = []
    for index in range(properties.count):
        property = adsk.core.ColorProperty.cast(properties.item(index))
        if property is not None and (not writable or not property.isReadOnly):
            found.append(property)
    return next((property for property in found if property.id in COLOR_PROPERTY_IDS), None) or (found[0] if found else None)

def baseAppearance() -> adsk.core.Appearance:
    """The library appearance the colors are copied from, see labelColors.baseCandidates, the first with a main color"""
    libraries = adsk.core.Application.get().materialLibraries
    appearances = [libraries.item(index).appearances for index in range(libraries.count)]
    names = [(libraries.item(index).id, [appearances[index].item(item).name for item in range(appearances[index].count)]) for index in range(libraries.count)]
    for (libraryIndex, index) in labelColors.baseCandidates(names):
        appearance = appearances[libraryIndex].item(index)
        try:
            property = colorProperty(appearance, writable=False)
        except Exception:
            continue
        if property is not None and property.id in COLOR_PROPERTY_IDS:
            return appearance
    raise AppearanceError('no appearance with a color in the material libraries')

def labelAppearance(design: adsk.fusion.Design, color: str) -> adsk.core.Appearance:
    """The appearance of the color in the design, made once and found again by its name"""
    name = labelColors.appearanceName(color)
    appearance = design.appearances.itemByName(name)
    if appearance is not None:
        return appearance
    base = baseAppearance()
    appearance = design.appearances.addByCopy(base, name)
    property = colorProperty(appearance)
    if property is None or property.id not in COLOR_PROPERTY_IDS:
        # another color of it (a tint, a reflection) wouldn't color the body, the snapshot check only sees the name
        raise AppearanceError(f'the copy of {base.name} has no main color to set')
    if property.hasConnectedTexture:
        property.hasConnectedTexture = False
    property.value = adsk.core.Color.create(*labelColors.rgb(color), 255)
    commonUtils.debugLog(f'appearance {name} copied from {base.name}, its {property.id}')
    return appearance

def colorBodies(bodies: list[adsk.fusion.BRepBody], color: str):
    """Gives the bodies the appearance of the color, nothing for no color"""
    if color == '' or len(bodies) == 0:
        return
    appearance = labelAppearance(bodies[0].parentComponent.parentDesign, color)
    for body in bodies:
        body.appearance = appearance
