import adsk.core, adsk.fusion

from . import labelColors, commonUtils

# The appearance label text and symbols are colored with (p86), see labelColors. It is a library appearance copied
# into the document and recolored, as Fusion does when one is dragged onto a body and recolored, and found again by
# its name next time. Library names are in the user's language (p31), so none is looked up by its full name: the
# best ranked one with a color to set is taken, see labelColors.baseRank

# ids of the main color of Fusion's appearances, generic plastics, paints and metals
COLOR_PROPERTY_IDS = ['opaque_albedo', 'generic_diffuse', 'metal_f0']

class AppearanceError(Exception):
    pass

def colorProperty(appearance: adsk.core.Appearance) -> adsk.core.ColorProperty | None:
    """The main color it's drawn with, the one Fusion's appearance editor shows first, none when it has no color to set"""
    properties = appearance.appearanceProperties
    found = []
    for index in range(properties.count):
        property = adsk.core.ColorProperty.cast(properties.item(index))
        if property is not None and not property.isReadOnly:
            found.append(property)
    return next((property for property in found if property.id in COLOR_PROPERTY_IDS), None) or (found[0] if found else None)

def baseAppearance() -> adsk.core.Appearance:
    """The library appearance the colors are copied from, the best ranked by name that has a color to set"""
    app = adsk.core.Application.get()
    candidates = []
    for libraryIndex in range(app.materialLibraries.count):
        appearances = app.materialLibraries.item(libraryIndex).appearances
        for index in range(appearances.count):
            appearance = appearances.item(index)
            candidates.append((labelColors.baseRank(appearance.name), libraryIndex, index, appearance))
    # sorted by rank, then as the libraries list them, the appearance library comes first
    for (_, _, _, appearance) in sorted(candidates, key=lambda candidate: candidate[:3]):
        try:
            if colorProperty(appearance) is not None:
                return appearance
        except Exception:
            continue
    raise AppearanceError('no appearance with a color to set in the material libraries')

def labelAppearance(design: adsk.fusion.Design, color: str) -> adsk.core.Appearance:
    """The appearance of the color in the design, made once and found again by its name"""
    name = labelColors.appearanceName(color)
    appearance = design.appearances.itemByName(name)
    if appearance is not None:
        return appearance
    base = baseAppearance()
    appearance = design.appearances.addByCopy(base, name)
    property = colorProperty(appearance)
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
