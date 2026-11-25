"""
The add-in for scripts run in Fusion while it runs, such as those of an MCP server: `import gridkeeper`, see
lib/scriptModule.py. The modules scripts use are here by short names, each as the add-in has it loaded, so a script
works with the same objects as the dialogs. Fusion's API runs on its main thread only, and a script blocks Fusion
while it runs, so a long build is better split into several scripts
"""

from . import config
from .lib import configJson
from .lib import defaultSettings
from .lib import tagUtils
from .lib import printBeds
from .lib import threeMf
from .lib import stlFile
from .commands.commandCreateBin import binBuilder
from .commands.commandCreateBin.inputState import InputState as BinInputState
from .commands.commandCreateBaseplate import baseplateBuilder
from .commands.commandCreateBaseplate.inputState import InputState as BaseplateInputState
from .commands.commandCreateBox import boxBuilder
from .commands.commandCreateBox.inputState import InputState as BoxInputState
from .commands.commandCreateBoxLabel import boxLabelBuilder
from .commands.commandCreateBoxLabel.inputState import InputState as BoxLabelInputState
from .commands.commandCreateLabel import labelBuilder
from .commands.commandCreateLabel.inputState import InputState as LabelInputState
from .commands.commandExport import entry as export
# the export without dialogs (round 59), as the original's script export: gridkeeper.exportBodies(bodies, folder, options)
from .commands.commandExport.entry import exportBodies, ExportOptions, ExportResult
# model pictures for the docs without the palette, see its renderRaw and tools/screenshots/finishPictures.py
from .commands.commandModelScreenshots import scriptRender

# see scriptModule.MARKER
IS_GRIDKEEPER = True

def version() -> str:
    """The add-in's version, as its bodies are tagged with"""
    return tagUtils.getGeneratorVersion()
