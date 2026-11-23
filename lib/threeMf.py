import dataclasses
import datetime
import json
import math
import zipfile
from xml.sax.saxutils import escape, quoteattr

# 3MF files of meshes, the triangles of label letters painted with the filaments the slicer picks up. Kept free of
# Fusion imports so it can be unit tested.
# The slicers keep their filament painting on the triangles, as their paint tool saves it: Bambu Studio and
# OrcaSlicer in paint_color, PrusaSlicer in slic3rpe:mmu_segmentation, both coded the same, see paintCode. They read
# it from a plain 3MF made elsewhere too. PrusaSlicer 3 still writes slic3rpe:mmu_segmentation but reads the painting
# only from a file of its own listing the painted triangles of each object, see facetsAnnotation

# where the objects are put, the middle of a 256 mm bed, the slicer arranges them on a bed of another size
PLATE_CENTER = (128.0, 128.0)
# the slicers tell their own projects by it, PrusaSlicer 3 refuses a file naming it that has no printer settings
APPLICATION = 'Fusion Gridfinity Generator'
# the most filaments a painted triangle can name, see paintCode
MAX_FILAMENT = 18

# Round 55 (p680, spec dev-notes/specs/2026-11-23-r55-bambu-project-3mf.md): a Bambu Studio project with all plates.
# Bambu Studio lays its plates out in a grid of about as many columns as rows, with a fifth of the bed between plates,
# and keeps which plate each object is on in a file of its own, see modelSettings (names as upstream 1ac1579 by
# Le0Michine has them). It takes the plates only from a file naming Bambu Studio that has project settings, without
# them it moves all objects to the middle of one plate (Plater::priv::load_files; plate probe 17.11.2026, Bambu
# Studio test 23.11.2026). Project settings naming only the profiles open cleanly, Bambu Studio takes the rest from its
# system profiles, see projectSettings
PLATE_GAP = 0.2
MODEL_SETTINGS_PATH = 'Metadata/model_settings.config'
PROJECT_SETTINGS_PATH = 'Metadata/project_settings.config'
# the Bambu Studio the test of 23.11.2026 opened the project in
BAMBU_VERSION = '02.09.01.70'
BAMBU_APPLICATION = f'BambuStudio-{BAMBU_VERSION}'
# Textured PEI, decided 23.11.2026
BAMBU_BED_TYPE = 'Textured PEI Plate'
# the generator in the project's designer, Bambu Studio keeps the application's name for itself
GENERATOR = 'Gridkeeper'

CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="json" ContentType="application/json"/>
</Types>'''
# where PrusaSlicer 3 keeps the painting
FACETS_ANNOTATION_PATH = 'Metadata/Slic3r_facets_annotation.json'
RELATIONSHIPS = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>'''

@dataclasses.dataclass
class MeshObject:
    name: str
    # mm
    vertices: list[tuple[float, float, float]]
    # vertex indices, counterclockwise seen from outside
    triangles: list[tuple[int, int, int]]
    # the painted triangles by index, each with its filament numbered from 1 (round 37, p301: each label color on a
    # filament of its own), the others print in the object's filament
    painted: dict[int, int] = dataclasses.field(default_factory=dict)

def paintCode(filament: int) -> str:
    """
    A whole triangle painted with the filament, numbered from 1, as the slicers' triangle selector writes it: hex
    digits in reverse order of the bits, two for how many sides the triangle is split on, none here, then two for
    the filament, or 3 and four more for the filament past 2
    """
    if filament < 1 or filament > MAX_FILAMENT:
        raise ValueError(f'filament {filament} is outside 1 to {MAX_FILAMENT}')
    return f'{filament << 2:X}' if filament < 3 else f'{filament - 3:X}C'

def placeOnPlate(objects: list[MeshObject]) -> list[MeshObject]:
    """Each standing on the plate, all as they were in the design side to side, around the middle of the plate"""
    vertices = [vertex for meshObject in objects for vertex in meshObject.vertices]
    if len(vertices) == 0:
        return objects
    shiftX = PLATE_CENTER[0] - (min(x for (x, _, _) in vertices) + max(x for (x, _, _) in vertices)) / 2
    shiftY = PLATE_CENTER[1] - (min(y for (_, y, _) in vertices) + max(y for (_, y, _) in vertices)) / 2
    placed = []
    for meshObject in objects:
        bottom = min((z for (_, _, z) in meshObject.vertices), default=0)
        vertices = [(x + shiftX, y + shiftY, z - bottom) for (x, y, z) in meshObject.vertices]
        placed.append(dataclasses.replace(meshObject, vertices=vertices))
    return placed

def _number(value: float) -> str:
    text = f'{value:.4f}'.rstrip('0').rstrip('.')
    return '0' if text == '-0' else text

def isPainted(objects: list[MeshObject]) -> bool:
    return any(meshObject.painted for meshObject in objects)

def modelXml(objects: list[MeshObject], title: str = '', version: str = '', date: datetime.date | None = None) -> str:
    """
    The model part of the file, each painted triangle with its filament's code. Named after the generator in the
    version, with the title and the day it was made, as the slicers show of a project
    """
    application = f'{APPLICATION} {version}' if version else APPLICATION
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:slic3rpe="http://schemas.slic3r.org/3mf/2017/06">',
        f' <metadata name="Application">{escape(application)}</metadata>',
        f' <metadata name="CreationDate">{(date or datetime.date.today()).isoformat()}</metadata>',
    ]
    if title:
        lines.append(f' <metadata name="Title">{escape(title)}</metadata>')
    if isPainted(objects):
        lines.append(' <metadata name="slic3rpe:MmPaintingVersion">1</metadata>')
    lines.append(' <resources>')
    for (index, meshObject) in enumerate(objects):
        lines += [f'  <object id="{index + 1}" type="model" name={quoteattr(meshObject.name)}>', '   <mesh>', '    <vertices>']
        lines += [f'     <vertex x="{_number(x)}" y="{_number(y)}" z="{_number(z)}"/>' for (x, y, z) in meshObject.vertices]
        lines += ['    </vertices>', '    <triangles>']
        for (triangleIndex, (a, b, c)) in enumerate(meshObject.triangles):
            filament = meshObject.painted.get(triangleIndex)
            code = paintCode(filament) if filament is not None else None
            paint = f' paint_color="{code}" slic3rpe:mmu_segmentation="{code}"' if code is not None else ''
            lines.append(f'     <triangle v1="{a}" v2="{b}" v3="{c}"{paint}/>')
        lines += ['    </triangles>', '   </mesh>', '  </object>']
    lines += [' </resources>', ' <build>']
    lines += [f'  <item objectid="{index + 1}"/>' for index in range(len(objects))]
    lines += [' </build>', '</model>']
    return '\n'.join(lines)

def facetsAnnotation(objects: list[MeshObject]) -> str:
    """PrusaSlicer 3's list of the painted triangles of each object, by the object's id in the model, see modelXml"""
    return json.dumps([
        {
            'mmSegmentationFacets': [{'triangle': triangle, 'dividing': paintCode(meshObject.painted[triangle])} for triangle in sorted(meshObject.painted)],
            'mmSegmentationFacetsVersion': 1,
            'id': index + 1,
        }
        for (index, meshObject) in enumerate(objects)
    ])

def plateColumns(count: int) -> int:
    """The columns of Bambu Studio's grid of plates"""
    return math.ceil(math.sqrt(count) - 1e-9) if count > 0 else 1

def plateOrigin(plate: int, count: int, bed: tuple[float, float]) -> tuple[float, float]:
    """Where the plate's corner is of count plates, numbered from 0, rows going toward -y"""
    columns = plateColumns(count)
    return ((plate % columns) * bed[0] * (1 + PLATE_GAP), -(plate // columns) * bed[1] * (1 + PLATE_GAP))

def modelSettings(objects: list[MeshObject], plates: list[int]) -> str:
    """
    Bambu Studio's plates, numbered from 0, and the objects on each by their id in the model. Each object prints on
    filament 1, its one part as it is, as the file Bambu Studio opened in the test of 23.11.2026
    """
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<config>']
    for (index, meshObject) in enumerate(objects):
        name = quoteattr(meshObject.name)
        lines += [
            f' <object id="{index + 1}">', f'  <metadata key="name" value={name}/>', '  <metadata key="extruder" value="1"/>',
            '  <part id="1" subtype="normal_part">', f'   <metadata key="name" value={name}/>',
            '   <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>', '  </part>', ' </object>',
        ]
    for plate in range(max(plates, default=-1) + 1):
        # the bed type of each plate as well, without it Bambu Studio took the Smooth PEI plate for a project of three
        # plates (test of 23.11.2026)
        lines += [' <plate>', f'  <metadata key="plater_id" value="{plate + 1}"/>', '  <metadata key="plater_name" value=""/>', '  <metadata key="locked" value="false"/>',
                  f'  <metadata key="bed_type" value="{BAMBU_BED_TYPE}"/>']
        for (index, objectPlate) in enumerate(plates):
            if objectPlate == plate:
                lines += ['  <model_instance>', f'   <metadata key="object_id" value="{index + 1}"/>', '   <metadata key="instance_id" value="0"/>', '  </model_instance>']
        lines.append(' </plate>')
    lines.append('</config>')
    return '\n'.join(lines)

def projectSettings(profiles, colours: list[str]) -> str:
    """
    The project's printer, process and a filament per colour by Bambu Studio's profile names (printer, process and
    filament of profiles, see printBeds.BAMBU_PROFILES), the same as each one's parent, and the bed. Nothing else:
    settings flattened from the profiles were an invalid configuration file to Bambu Studio (test of 23.11.2026, V3).
    The parents in Bambu Studio's order, process, filaments, printer (PresetBundle::load_config_file_config): with
    the names alone filaments 2 and on came as project copies of Bambu Studio's general defaults, 200 °C and
    2 mm³/s; with their parent named Bambu Studio takes its system profile, Bambu PLA Basic's 220 °C and 21 mm³/s
    (tests of 23.11.2026). Round 56: the purging volumes for two extruders, round 57 for every printer, see
    flushSettings
    """
    return json.dumps({
        'version': BAMBU_VERSION,
        'name': 'project_settings',
        'from': 'project',
        'printer_settings_id': profiles.printer,
        'print_settings_id': profiles.process,
        'filament_settings_id': [profiles.filament] * len(colours),
        'filament_colour': list(colours),
        'curr_bed_type': BAMBU_BED_TYPE,
        'inherits_group': [profiles.process] + [profiles.filament] * len(colours) + [profiles.printer],
        **flushSettings(profiles, colours),
    }, indent=4)

# Round 56 (p690, spec dev-notes/specs/2026-11-23-r56-multi-nozzle-flush.md): the purging volumes of a printer with
# two extruders. A project without them gets Bambu Studio's defaults for one extruder, rebuilt for two with zeros
# (PresetBundle::update_multi_material_filament_presets reads past their end), and the warning "Partial purging volume
# set to 0" (GLCanvas3D::is_flushing_matrix_error). Bambu Studio doesn't work them out itself when it opens a project.
# Round 57 (spec dev-notes/specs/2026-11-23-r57-one-nozzle-flush.md): every Bambu printer gets them, a printer with one
# extruder had Bambu Studio's flat 280 for every change of color
FLUSH_MAX = 900
FLUSH_MIN = 60
# Bambu Studio's defaults, PrintConfig.cpp
FLUSH_VECTOR = '140'
FLUSH_MULTIPLIER = '1'
FLUSH_MULTIPLIER_FAST = '1.2'
FLUSH_MAP_MODE = 'Auto For Flush'
# Bambu PLA Basic's filament_diameter, mm
FILAMENT_DIAMETER = 1.75

def _hsv(red: float, green: float, blue: float) -> tuple[float, float, float]:
    """Hue in degrees, saturation and value 0 to 1, as Bambu Studio's RGB2HSV"""
    top = max(red, green, blue)
    delta = top - min(red, green, blue)
    if abs(delta) < 0.001:
        hue = 0.0
    elif top == red:
        hue = 60 * math.fmod((green - blue) / delta, 6)
    elif top == green:
        hue = 60 * ((blue - red) / delta + 2)
    else:
        hue = 60 * ((red - green) / delta + 4)
    return (hue, 0.0 if abs(top) < 0.001 else delta / top, top)

def _luminance(red: float, green: float, blue: float) -> float:
    return red * 0.3 + green * 0.59 + blue * 0.11

def _rgb(colour: str) -> tuple[int, int, int]:
    return tuple(int(colour[index:index + 2], 16) for index in (1, 3, 5))

def flushVolume(source: str, target: str, minimum: float, dataset: int) -> int:
    """
    mm³ to purge going from the colour source to target, '#RRGGBB', on an extruder of the least volume minimum (round 57:
    minFlushVolume, not the bare nozzle volume) and the flush data set (nozzle_flush_dataset of the printer profile). Rebuilt after Bambu Studio 02.09.01.70
    (src/libslic3r/FlushVolCalc.cpp, AGPL-3.0, no code taken): FlushVolCalculator::calc_flush_vol_rgb, distance of hue
    and saturation and the change of luminance, 60 at least; with a data set 1.3 times as much from a "dark" colour to
    a "light" one, the least volume minimum on top (round 57: minFlushVolume), 900 at most.
    Not rebuilt (decided 23.11.2026): Bambu Studio's colour tables (FlushVolPredictor), which take over when both
    colours are near one of its filament colours; its "Re-calculate" may differ there. Bambu Studio counts in float, a
    value right at a whole number may come out one apart
    """
    (sourceRgb, targetRgb) = ([value / 255 for value in _rgb(source)], [value / 255 for value in _rgb(target)])
    (sourceHue, sourceSaturation, sourceValue) = _hsv(*sourceRgb)
    (targetHue, targetSaturation, targetValue) = _hsv(*targetRgb)
    dx = math.cos(math.radians(sourceHue)) * sourceSaturation * sourceValue - math.cos(math.radians(targetHue)) * targetSaturation * targetValue
    dy = math.sin(math.radians(sourceHue)) * sourceSaturation * sourceValue - math.sin(math.radians(targetHue)) * targetSaturation * targetValue
    hueDistance = min(1.2, math.hypot(dx, dy))
    (sourceLuminance, targetLuminance) = (_luminance(*sourceRgb), _luminance(*targetRgb))
    if targetLuminance >= sourceLuminance:
        luminanceFlush = (targetLuminance - sourceLuminance) ** 0.7 * 560
    else:
        luminanceFlush = (sourceLuminance - targetLuminance) * 80
        hueDistance = min(0.67 * targetValue + 0.33 * sourceValue, hueDistance)
    hueFlush = 230 * hueDistance
    # the third side of a triangle of the two at 120°
    volume = int(max(math.sqrt(hueFlush ** 2 + luminanceFlush ** 2 - 2 * hueFlush * luminanceFlush * math.cos(math.radians(120))), FLUSH_MIN))
    # Bambu Studio compares the luminance of the 0 to 255 values with 180/255 and 75/255: nearly any colour but black
    # is "dark", only black and near black "light" (Bambu Studio test of 23.11.2026: grey to black 208, 60 · 1.3 + 130)
    if dataset != 0 and _luminance(*_rgb(source)) > 180 / 255 and _luminance(*_rgb(target)) < 75 / 255:
        volume *= 1.3
    return min(int(volume + int(minimum)), FLUSH_MAX)

def minFlushVolume(nozzleVolume: float, cutRetraction: int) -> int:
    """
    The least mm³ Bambu Studio purges on an extruder of the nozzle volume nozzleVolume (nozzle_volume of the printer
    profile) whose filament it pulls back cutRetraction mm when it cuts it (printBeds.BambuProfiles.cutRetractions):
    that filament comes back in first. Rebuilt after Bambu Studio 02.09.01.70 (src/slic3r/GUI/Plater.cpp
    get_min_flush_volumes, AGPL-3.0, no code taken), cut to whole numbers where Bambu Studio counts in int. Round 57:
    without it the purging volumes of the P1S and A1 mini were 44 above Bambu Studio's Re-calculate (test of 23.11.2026)
    """
    return int(int(nozzleVolume) - math.pi * FILAMENT_DIAMETER ** 2 / 4 * cutRetraction)

def flushSettings(profiles, colours: list[str]) -> dict:
    """
    The purging volumes of the project for the printer's extruders (printBeds.BambuProfiles): a block of each
    filament to each per extruder, row by row, 0 to itself, as Bambu Studio keeps them; the filaments go on the
    extruders as Bambu Studio finds it purges least, the user may change that and the volumes.
    Round 57: one extruder too, the H3C's nine hotends are one. Bambu Studio counts the blocks by the entries of
    flush_multiplier (PresetBundle::update_multi_material_filament_presets) and keeps the matrix when they match the
    printer's extruders; its own project for one nozzle (resources/calib/pressure_advance/auto_pa_line_single.3mf, A1)
    has the same keys, filament_map one for each filament as Bambu Studio sets it for any printer. Without them every
    change of color purged Bambu Studio's flat 280 (Bambu Studio test of 23.11.2026)
    """
    matrix = [
        str(0 if source == target else flushVolume(colours[source], colours[target], minFlushVolume(volume, cut), dataset))
        # strict: a block missing would bring Bambu Studio's zeros back (review round 56)
        for (volume, dataset, cut) in zip(profiles.nozzleVolumes, profiles.flushDatasets, profiles.cutRetractions, strict=True)
        for source in range(len(colours)) for target in range(len(colours))
    ]
    return {
        'flush_volumes_matrix': matrix,
        'flush_volumes_vector': [FLUSH_VECTOR] * (2 * len(colours)),
        'flush_multiplier': [FLUSH_MULTIPLIER] * profiles.extruders,
        'flush_multiplier_fast': [FLUSH_MULTIPLIER_FAST] * profiles.extruders,
        'filament_map': ['1'] * len(colours),
        'filament_map_mode': FLUSH_MAP_MODE,
    }

def bambuModelXml(objects: list[MeshObject], title: str = '', version: str = '', date: datetime.date | None = None) -> str:
    """
    The model part of the project as Bambu Studio writes it: named after Bambu Studio, each object around its
    middle, moved where it is by its build item. The painted triangles with Bambu Studio's code, see paintCode
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">',
        f' <metadata name="Application">{BAMBU_APPLICATION}</metadata>',
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>',
        f' <metadata name="CreationDate">{(date or datetime.date.today()).isoformat()}</metadata>',
    ]
    if version:
        lines.append(f' <metadata name="Designer">{escape(f"{GENERATOR} {version}")}</metadata>')
    if title:
        lines.append(f' <metadata name="Title">{escape(title)}</metadata>')
    lines.append(' <resources>')
    middles = []
    for (index, meshObject) in enumerate(objects):
        vertices = meshObject.vertices or [(0.0, 0.0, 0.0)]
        middle = tuple((min(vertex[axis] for vertex in vertices) + max(vertex[axis] for vertex in vertices)) / 2 for axis in range(3))
        middles.append(middle)
        lines += [f'  <object id="{index + 1}" type="model" name={quoteattr(meshObject.name)}>', '   <mesh>', '    <vertices>']
        lines += [f'     <vertex x="{_number(x - middle[0])}" y="{_number(y - middle[1])}" z="{_number(z - middle[2])}"/>' for (x, y, z) in meshObject.vertices]
        lines += ['    </vertices>', '    <triangles>']
        for (triangleIndex, (a, b, c)) in enumerate(meshObject.triangles):
            filament = meshObject.painted.get(triangleIndex)
            paint = f' paint_color="{paintCode(filament)}"' if filament is not None else ''
            lines.append(f'     <triangle v1="{a}" v2="{b}" v3="{c}"{paint}/>')
        lines += ['    </triangles>', '   </mesh>', '  </object>']
    lines += [' </resources>', ' <build>']
    lines += [f'  <item objectid="{index + 1}" transform="1 0 0 0 1 0 0 0 1 {_number(x)} {_number(y)} {_number(z)}" printable="1"/>' for (index, (x, y, z)) in enumerate(middles)]
    lines += [' </build>', '</model>']
    return '\n'.join(lines)

def writeBambuProject(path: str, objects: list[MeshObject], plates: list[int], bed: tuple[float, float], profiles, colours: list[str], title: str = '', version: str = ''):
    """
    A Bambu Studio project of the objects, each laid out on the bed of its plate, numbered from 0, see
    printLayout.layOutKinds; the plates go on Bambu Studio's grid, see plateOrigin. Named after Bambu Studio, the
    profiles and a filament per colour in its settings, see projectSettings
    """
    count = max(plates, default=-1) + 1
    placed = []
    for (meshObject, plate) in zip(objects, plates):
        (originX, originY) = plateOrigin(plate, count, bed)
        placed.append(dataclasses.replace(meshObject, vertices=[(x + originX, y + originY, z) for (x, y, z) in meshObject.vertices]))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as package:
        package.writestr('[Content_Types].xml', CONTENT_TYPES)
        package.writestr('_rels/.rels', RELATIONSHIPS)
        package.writestr('3D/3dmodel.model', bambuModelXml(placed, title, version))
        package.writestr(MODEL_SETTINGS_PATH, modelSettings(placed, plates))
        package.writestr(PROJECT_SETTINGS_PATH, projectSettings(profiles, colours))

def write(path: str, objects: list[MeshObject], title: str = '', version: str = '', isLaidOut: bool = False):
    """
    The objects in one file, their triangles painted as they are, see modelXml. Placed on the plate, see
    placeOnPlate, unless they're laid out already (round r29-export, printLayout.layOut), then they stay where they are
    """
    placed = objects if isLaidOut else placeOnPlate(objects)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as package:
        package.writestr('[Content_Types].xml', CONTENT_TYPES)
        package.writestr('_rels/.rels', RELATIONSHIPS)
        package.writestr('3D/3dmodel.model', modelXml(placed, title, version))
        if isPainted(objects):
            package.writestr(FACETS_ANNOTATION_PATH, facetsAnnotation(objects))
