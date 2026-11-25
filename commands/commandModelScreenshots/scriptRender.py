import adsk.core, adsk.fusion
import json
import os
import re

from ...lib.ui import viewportPictures
from . import entry, presets

# Model pictures from a script, without the palette or a dialog (round 58): Fusion's Python can't cut and scale a
# picture, the palette's page does that. A script renders the preset larger than the picture and writes a sidecar of
# its options beside it; tools/screenshots/finishPictures.py finishes it outside Fusion, with Pillow, the same way as
# the page. The document is closed without saving.
#
#     from gridkeeper import scriptRender   # or the add-in package loaded by a test script
#     scriptRender.renderRaw('bin-scoops-4', r'C:\temp\raw')

app = adsk.core.Application.get()

# the render is moved back once before it is saved: the finisher cuts it to the model anyway, and a model touching
# the render's edge can't be moved back afterwards as the palette does
ZOOM_OUTS = 1

def renderRaw(name: str, folder: str, presetsFolder: str = entry.PRESETS_FOLDER) -> str:
    """Renders the preset into folder as <name>.render.png with its sidecar <name>.json, returns the sidecar's path"""
    preset = presets.loadPreset(presetsFolder, f'{name}.json')
    state = entry.presetState(preset)
    os.makedirs(folder, exist_ok=True)
    document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        bodies = entry.buildModel(design, preset.generator, state)
        entry.prepareView(design, bodies, preset)
        viewport = app.activeViewport
        for _ in range(ZOOM_OUTS):
            viewportPictures.zoomOut(viewport)
        size = viewportPictures.renderSize(viewport, min(max(preset.width, preset.height) * preset.supersample, viewportPictures.MAX_RENDER_SIZE))
        renderPath = os.path.join(folder, f'{re.sub(r"[^A-Za-z0-9_.-]+", "-", name)}.render.png')
        viewportPictures.saveViewport(viewport, renderPath, *size, preset.transparent)
        sidecarPath = os.path.join(folder, f'{name}.json')
        with open(sidecarPath, 'w', encoding='utf-8') as file:
            json.dump(presets.sidecar(preset, renderPath, entry.ROOT_FOLDER), file, indent=2)
        return sidecarPath
    finally:
        document.close(False)
