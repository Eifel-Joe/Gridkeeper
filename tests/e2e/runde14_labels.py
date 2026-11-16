# End-to-end check of round 14 (docs/specs/2026-11-15-runde-14-design.md, "Ende-zu-Ende-Kriterium"), run in Fusion with
# the add-in loaded from this checkout. Each case is built, its label text made three letters longer through its
# parameter, and checked. The cases run in groups, each under a minute for the Fusion MCP's time limit: set GROUP to
# 'a' to 'g' before running (all of them without). Each group builds into a document of its own, closes it when
# everything passes and prints OK or FAIL per point, ALL OK or N FAILED last.
import adsk.core, adsk.fusion, sys, os, dataclasses

ADDIN = '__main__D%3A%2FEntwicklung%2FGridfinity%2FFusionGridfinityGenerator%2FGridfinityGenerator_py'
CASES = r'D:\Entwicklung\Gridfinity\FusionGridfinityGenerator\tests\e2e\cases'
MORE = 'XYZ'
NO_ICON = 'None'


def isLabelName(name):
    """Features of a bin label, 'Label ...' or 'Compartment N label ...', not those of the compartments"""
    return name.startswith('Label') or (name.startswith('Compartment') and ' label' in name)


def module(name):
    return sys.modules[f'{ADDIN}.{name}']


def mm(value):
    return round(value * 10, 2)


class Run:
    def __init__(self, des):
        self.des = des
        self.results = []
        snap = module('commands.commandSnapshotTests.entry')
        self.tc = module('commands.commandSnapshotTests.testCases')
        self.stateClasses = snap.STATE_CLASSES
        self.binBuilder = module('commands.commandCreateBin.binBuilder')
        self.labelBuilder = module('commands.commandCreateLabel.labelBuilder')
        self.parameterUtils = module('lib.gridfinityUtils.parameterUtils')
        self.tagUtils = module('lib.tagUtils')
        self.labelColors = module('lib.gridfinityUtils.labelColors')
        self.constraints = module('commands.commandSnapshotTests.constraints')

    def check(self, point: str, ok: bool, detail: str = ''):
        self.results.append(ok)
        print(f'{"OK  " if ok else "FAIL"} {point}{": " + detail if detail else ""}')

    def load(self, name):
        case = self.tc.loadCase(os.path.join(CASES, name + '.json'), self.stateClasses)
        return (case, self.tc.caseSettings(case))

    def bin(self, caseName, **changes):
        (case, settings) = self.load(caseName)
        body = self.binBuilder.buildBin(self.des, dataclasses.replace(case.state, **changes), settings)[0]
        occurrence = self.des.rootComponent.allOccurrencesByComponent(body.parentComponent).item(0)
        return (body, body.parentComponent, occurrence)

    def labelParameters(self, component):
        """The text parameters the label sketches of the component and its Text component are driven by"""
        names = []
        components = [component] + [occurrence.component for occurrence in component.occurrences]
        for each in components:
            for sketch in each.sketches:
                for text in sketch.sketchTexts:
                    expression = text.textParameter.expression
                    if expression not in names:
                        names.append(expression)
        return [self.des.userParameters.itemByName(name) for name in names]

    def lengthen(self, parameters):
        for parameter in parameters:
            parameter.expression = self.parameterUtils.textExpression(parameter.textValue + MORE)
        adsk.doEvents()

    def labelFeatures(self, component):
        return [feature for feature in component.features.extrudeFeatures if isLabelName(feature.name)]

    def faceBox(self, features):
        faces = [face for feature in features for face in feature.faces]
        if not faces:
            return None
        lo = [min(getattr(face.boundingBox.minPoint, a) for face in faces) for a in 'xyz']
        hi = [max(getattr(face.boundingBox.maxPoint, a) for face in faces) for a in 'xyz']
        return (lo, hi)

    def onTab(self, name, binBody, box, mayRunOver=False):
        """On the tab: inside the bin's outline, in its back half, near its top. Not at the origin and not above it.
        A text made longer keeps the height of its letters, so it runs on to the right, with mayRunOver also past the
        bin's right side (a text filling a label already, round 14 hand-over)"""
        if box is None:
            self.check(f'{name}: label geometry found', False)
            return
        bb = binBody.boundingBox
        (lo, hi) = box
        inside = lo[0] >= bb.minPoint.x - 0.001 and (mayRunOver or hi[0] <= bb.maxPoint.x + 0.001) and lo[1] >= (bb.minPoint.y + bb.maxPoint.y) / 2 and hi[1] <= bb.maxPoint.y + 0.001
        nearTop = lo[2] >= bb.maxPoint.z - 2.5 and hi[2] <= bb.maxPoint.z + 0.1
        self.check(f'{name}: all letters on the tab', inside and nearTop, f'x {mm(lo[0])}..{mm(hi[0])} y {mm(lo[1])}..{mm(hi[1])} z {mm(lo[2])}..{mm(hi[2])}, bin z top {mm(bb.maxPoint.z)}')

    def healthy(self, name):
        bad = [(self.des.timeline.item(i).name, self.des.timeline.item(i).errorOrWarningMessage[:80]) for i in range(self.des.timeline.count) if self.des.timeline.item(i).healthState not in (0, 5)]
        self.check(f'{name}: nothing in the timeline unhealthy', len(bad) == 0, str(bad))

    def placed(self, name, component, iconMoves=False):
        """No moves of label text, of a large icon only with iconMoves; every label sketch bound but for its live text
        (p50), and seen from above, a sketch seen from below shows its text mirrored"""
        components = [component] + [occurrence.component for occurrence in component.occurrences]
        moves = [move.name for each in components for move in each.features.moveFeatures if isLabelName(move.name) and (move.name.endswith(' tilt') or move.name.endswith(' placement'))]
        textMoves = [move for move in moves if ' icon ' not in move]
        self.check(f'{name}: no moves of the text', len(textMoves) == 0, str(textMoves))
        self.check(f'{name}: icon {"moved" if iconMoves else "not moved"}', (len(moves) > 0) == iconMoves, str(moves))
        sketches = [sketch for each in components for sketch in each.sketches if isLabelName(sketch.name) and (sketch.name.endswith('text sketch') or sketch.name.endswith('icon sketch'))]
        loose = self.constraints.unconstrainedSketches(sketches)
        self.check(f'{name}: label sketches bound', len(loose) == 0, str(loose))
        downwards = [sketch.name for sketch in sketches if sketch.transform.getAsCoordinateSystem()[3].z <= 0]
        self.check(f'{name}: label sketches face up', len(sketches) > 0 and len(downwards) == 0, str(downwards))


def uncolored(run, name, caseName, style, volumeChange, **changes):
    changes.setdefault('labelIcon', NO_ICON)
    (body, component, _) = run.bin(caseName, labelStyle=style, labelColor='', **changes)
    parameters = run.labelParameters(component)
    volume = body.volume
    run.lengthen(parameters)
    run.check(f'{name}: text parameters lengthened', len(parameters) > 0 and all(p.textValue.endswith(MORE) for p in parameters), str([p.name for p in parameters]))
    run.check(f'{name}: only the bin body in its component', component.bRepBodies.count == 1, str([b.name for b in component.bRepBodies]))
    change = (body.volume - volume) * 1000
    run.check(f'{name}: bin volume {volumeChange} by the new letters', change < -0.01 if volumeChange == 'smaller' else change > 0.01 if volumeChange == 'larger' else abs(change) < 1, f'{round(change, 3)} mm3')
    run.onTab(name, body, run.faceBox(run.labelFeatures(component)))
    run.placed(name, component)
    return (body, component)


def groupA(run):
    uncolored(run, 'Outline', 'bin_2x1x3_label_text_engraved', 'Outline', 'about the same')
    uncolored(run, 'Engraved', 'bin_2x1x3_label_text_engraved', 'Engraved', 'smaller')
    uncolored(run, 'Embossed', 'bin_2x1x3_label_text_engraved', 'Embossed', 'larger')


def groupB(run):
    # Embossed colored, text alone, icons see groups d and e
    (body, component, occurrence) = run.bin('bin_2x1x3_label_icon_text_embossed_colored', labelIcon=NO_ICON)
    texts = [child for child in occurrence.childOccurrences if child.component.name.startswith('Text')]
    run.check('Embossed colored: a Text component', len(texts) == 1)
    if texts:
        text = texts[0]
        before = text.component.bRepBodies.count
        run.lengthen(run.labelParameters(component))
        letters = list(text.component.bRepBodies)
        run.check('Embossed colored: new letters in Text', len(letters) > before, f'{before} -> {len(letters)}')
        color = run.labelColors.appearanceName('#D02020')
        run.check('Embossed colored: Text shows the color', text.appearance is not None and text.appearance.name == color and all(b.appearance.name == color for b in letters), f'{text.appearance.name if text.appearance else None}')
        run.check('Embossed colored: only the bin body in the bin', component.bRepBodies.count == 1)
        lo = [min(getattr(b.boundingBox.minPoint, a) for b in letters) for a in 'xyz']
        hi = [max(getattr(b.boundingBox.maxPoint, a) for b in letters) for a in 'xyz']
        run.onTab('Embossed colored', body, (lo, hi))
        run.placed('Embossed colored', component)
    # compartment labels, two compartments with a label each
    uncolored(run, 'Compartments', 'bin_2x1x3_label_text_engraved', 'Outline', 'about the same', compartmentsX=2)


def groupC(run):
    # the insert, colored: new letters in Text, colored, settings found from a new letter
    (case, settings) = run.load('label_1u_screw_text_colored')
    insert = run.labelBuilder.buildLabel(run.des, dataclasses.replace(case.state, useUnits=True, widthUnits=1), settings)
    base = insert[0]
    textComponent = insert[1].parentComponent
    before = textComponent.bRepBodies.count
    parameter = [p for p in run.des.userParameters if p.name.startswith('gfLabel') and p.name.endswith('_text1')][0]
    run.lengthen([parameter])
    letters = list(textComponent.bRepBodies)
    run.check('Insert: new letters in Text', len(letters) > before, f'{before} -> {len(letters)}')
    textOccurrence = run.des.rootComponent.allOccurrencesByComponent(textComponent).item(0)
    run.check('Insert: Text shows the color', textOccurrence.appearance is not None and textOccurrence.appearance.name == run.labelColors.appearanceName(case.state.textColor), textOccurrence.appearance.name if textOccurrence.appearance else 'none')
    untagged = [body for body in letters if run.tagUtils.readBodyTag(body) is None]
    found = run.tagUtils.partTag(untagged[0].createForAssemblyContext(textOccurrence), lambda c: None) if untagged else None
    run.check('Insert: settings found from a new letter', found is not None and found[0] == base and found[1] == run.tagUtils.TAG_LABEL, f'{len(untagged)} untagged letters')
    # tilted tab, engraved
    uncolored(run, 'Tilted', 'bin_3x2x6_tab_steep_tilted', 'Engraved', 'smaller', labelText='AB')
    # parameters changed after building, then the text
    (body, component, _) = run.bin('bin_2x1x3_label_text_engraved', labelStyle='Engraved', labelColor='', labelIcon=NO_ICON)
    prefix = [p for p in run.labelParameters(component)][0].name.rsplit('_', 1)[0]
    run.des.userParameters.itemByName(f'{prefix}_heightUnit').expression = '10 mm'
    run.des.userParameters.itemByName(f'{prefix}_baseWidth').expression = '50 mm'
    adsk.doEvents()
    volume = body.volume
    run.lengthen(run.labelParameters(component))
    run.check('Parameters after building: only the bin body', component.bRepBodies.count == 1)
    run.check('Parameters after building: new letters cut', (body.volume - volume) * 1000 < -0.01, f'{round((body.volume - volume) * 1000, 3)} mm3')
    run.onTab('Parameters after building', body, run.faceBox(run.labelFeatures(component)))


def withIcon(run, name, icon):
    """Two compartments with a colored raised label each, icon and text: the second compartment's label follows a
    wider base unit as one, icon included, then a longer text adds its letters there"""
    (body, component, occurrence) = run.bin('bin_2x1x3_label_icon_text_embossed_colored', labelIcon=icon, labelText='M3', compartmentsX=2)
    texts = [child for child in occurrence.childOccurrences if child.component.name.startswith('Text')]
    run.check(f'{name}: a Text component', len(texts) == 1)
    if not texts:
        return
    text = texts[0]
    bb = body.boundingBox
    middle = (bb.minPoint.x + bb.maxPoint.x) / 2
    second = [(b, b.boundingBox.minPoint.x) for b in text.component.bRepBodies if b.boundingBox.minPoint.x > middle]
    prefix = run.labelParameters(component)[0].name.rsplit('_', 1)[0]
    run.des.userParameters.itemByName(f'{prefix}_baseWidth').expression = '50 mm'
    adsk.doEvents()
    shifts = [round((b.boundingBox.minPoint.x - x) * 10, 3) for (b, x) in second]
    run.check(f'{name}: second label follows the base width as one, icon included', len(shifts) > 1 and min(shifts) > 1 and max(shifts) - min(shifts) < 0.01, f'{shifts} mm')
    before = text.component.bRepBodies.count
    run.lengthen(run.labelParameters(component))
    letters = list(text.component.bRepBodies)
    run.check(f'{name}: new letters in Text', len(letters) > before, f'{before} -> {len(letters)}')
    run.check(f'{name}: only the bin body in the bin', component.bRepBodies.count == 1)
    lo = [min(getattr(b.boundingBox.minPoint, a) for b in letters) for a in 'xyz']
    hi = [max(getattr(b.boundingBox.maxPoint, a) for b in letters) for a in 'xyz']
    run.onTab(name, body, (lo, hi), mayRunOver=True)
    color = run.labelColors.appearanceName('#D02020')
    run.check(f'{name}: all of it shows the color', text.appearance is not None and text.appearance.name == color and all(b.appearance.name == color for b in letters))
    return (body, component)


def groupD(run):
    (body, component) = withIcon(run, 'Small icon', 'Hex nut') or (None, None)
    if component is not None:
        run.placed('Small icon', component, iconMoves=False)
    # uncolored, engraved, the small icon cut by the same extrusion as the text
    uncolored(run, 'Small icon engraved', 'bin_2x1x3_label_text_engraved', 'Engraved', 'smaller', labelIcon='Hex nut')


def groupE(run):
    # a symbol above the dims limit (binLabelLayout.ICON_POINTS_HELD_BY_DIMS): tnut 2 has 26 points since the coarser
    # symbols of round 17 and is held by dims now, the magnet (50 points) is moved (round 22)
    (body, component) = withIcon(run, 'Large icon', 'Cullenect magnet') or (None, None)
    if component is not None:
        run.placed('Large icon', component, iconMoves=True)


def tiltedTab(run):
    """Tab settings of the steep tilted case, its angle as the case loads it"""
    (case, _) = run.load('bin_3x2x6_tab_steep_tilted')
    return {'tabTopAngle': case.state.tabTopAngle, 'tabWidth': case.state.tabWidth, 'tabOverhangAngle': case.state.tabOverhangAngle}


def placedColored(run, name, icon, style):
    """A second bin goes beside the first, moved there after building: the colored letters a longer text adds go
    there too, on its tilted tab, cut into it when engraved"""
    run.bin('bin_2x1x3_label_text_engraved', labelColor='', labelIcon=NO_ICON)
    (body, component, occurrence) = run.bin('bin_2x1x3_label_text_engraved_colored', labelStyle=style, labelIcon=icon, **tiltedTab(run))
    texts = [child for child in occurrence.childOccurrences if child.component.name.startswith('Text')]
    run.check(f'{name}: a Text component', len(texts) == 1)
    if not texts:
        return
    text = texts[0]
    before = text.component.bRepBodies.count
    volume = body.volume
    run.lengthen(run.labelParameters(component))
    letters = list(text.component.bRepBodies)
    run.check(f'{name}: new letters in Text', len(letters) > before, f'{before} -> {len(letters)}')
    run.check(f'{name}: only the bin body in the bin', component.bRepBodies.count == 1)
    if style == 'Engraved':
        run.check(f'{name}: new letters cut into the bin', (body.volume - volume) * 1000 < -0.01, f'{round((body.volume - volume) * 1000, 3)} mm3')
    lo = [min(getattr(b.boundingBox.minPoint, a) for b in letters) for a in 'xyz']
    hi = [max(getattr(b.boundingBox.maxPoint, a) for b in letters) for a in 'xyz']
    run.onTab(name, body, (lo, hi), mayRunOver=True)
    color = run.labelColors.appearanceName('#2060D0')
    run.check(f'{name}: all of it shows the color', text.appearance is not None and text.appearance.name == color)
    run.placed(name, component, iconMoves=icon != NO_ICON and icon != 'Hex nut')


def groupF(run):
    placedColored(run, 'Second bin, tilted, small icon, engraved', 'Hex nut', 'Engraved')


def groupG(run):
    placedColored(run, 'Second bin, tilted, large icon, embossed', 'Cullenect magnet', 'Embossed')


GROUPS = {'a': groupA, 'b': groupB, 'c': groupC, 'd': groupD, 'e': groupE, 'f': groupF, 'g': groupG}


def run(_context: str):
    app = adsk.core.Application.get()
    original = app.activeDocument
    group = globals().get('GROUP')
    failed = 0
    for (key, build) in GROUPS.items():
        if group is not None and key != group:
            continue
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.name = f'Runde 14 end-to-end {key}'
        des = adsk.fusion.Design.cast(app.activeProduct)
        des.designIntent = adsk.fusion.DesignIntentTypes.PartDesignIntentType
        checks = Run(des)
        try:
            build(checks)
            checks.healthy(f'group {key}')
        except Exception:
            import traceback
            checks.check(f'group {key} ran through', False, traceback.format_exc()[-800:])
        failed += checks.results.count(False)
        if all(checks.results):
            doc.close(False)
        else:
            print(f'document left open: {doc.name}')
    if original is not None and original.isValid:
        original.activate()
    print('ALL OK' if failed == 0 else f'{failed} FAILED')
