# End-to-end check of round 19 (dev-notes/specs/2026-11-15-runde-19-design.md, "Ende-zu-Ende-Kriterium" and the p210
# addition), run in Fusion with the add-in loaded from this checkout. Set GROUP to 'a' to 'f' before running, each runs
# under a minute, no dialog. Each group builds into a document of its own, closes it when everything passes and prints
# OK or FAIL per point, ALL OK or N FAILED last.
import adsk.core, adsk.fusion, sys, os, dataclasses

ADDIN = '__main__D%3A%2FEntwicklung%2FGridfinity%2FGridkeeper%2FGridkeeper_py'
CASES = r'D:\Entwicklung\Gridfinity\Gridkeeper\tests\e2e\cases'
TOLERANCE = 0.001  # cm, 0.01 mm
MORE = ' M4x2'  # five characters


def module(name):
    return sys.modules[f'{ADDIN}.{name}']


class Run:
    def __init__(self, des):
        self.des = des
        self.results = []
        snap = module('commands.commandSnapshotTests.entry')
        self.tc = module('commands.commandSnapshotTests.testCases')
        self.stateClasses = snap.STATE_CLASSES
        self.binBuilder = module('commands.commandCreateBin.binBuilder')
        self.labelBuilder = module('commands.commandCreateLabel.labelBuilder')
        self.tagUtils = module('lib.tagUtils')
        self.textStyles = module('lib.gridfinityUtils.textStyles')
        self.parameterUtils = module('lib.gridfinityUtils.parameterUtils')
        self.constraints = module('commands.commandSnapshotTests.constraints')

    def check(self, point: str, ok: bool, detail: str = ''):
        self.results.append(ok)
        print(f'{"OK  " if ok else "FAIL"} {point}{": " + detail if detail else ""}')

    def state(self, caseName, **changes):
        case = self.tc.loadCase(os.path.join(CASES, caseName + '.json'), self.stateClasses)
        return (dataclasses.replace(case.state, **changes), self.tc.caseSettings(case))

    def healthy(self, name):
        bad = [(self.des.timeline.item(i).name, self.des.timeline.item(i).errorOrWarningMessage[:80]) for i in range(self.des.timeline.count) if self.des.timeline.item(i).healthState not in (0, 5)]
        self.check(f'{name}: nothing in the timeline unhealthy', len(bad) == 0, str(bad))

    def components(self, body):
        occurrences = self.des.rootComponent.allOccurrencesByComponent(body.parentComponent)
        occurrence = occurrences.item(0) if occurrences.count > 0 else None
        return [body.parentComponent] + ([child.component for child in occurrence.childOccurrences] if occurrence is not None else [])

    def texts(self, body):
        return [text for component in self.components(body) for sketch in component.sketches for text in sketch.sketchTexts]

    def letters(self, body):
        """Letter bodies of a colored label, in the bin's Text component"""
        return [b for component in self.components(body)[1:] if component.name.startswith('Text') for b in component.bRepBodies]

    def lengthen(self, body, more):
        """The label text parameters made longer, as a user does in Fusion's parameter dialog"""
        names = []
        for text in self.texts(body):
            if text.textParameter is not None and text.textParameter.expression not in names:
                names.append(text.textParameter.expression)
        for name in names:
            parameter = self.des.userParameters.itemByName(name)
            parameter.expression = self.parameterUtils.textExpression(parameter.textValue + more)
        adsk.doEvents()
        return names

    def rebuild(self, body, settings):
        """A right click rebuild with the settings its dialog opens with: the tag's config with the parameters"""
        tag = self.tagUtils.readBodyTag(body)[1]
        config = self.binBuilder.configWithParameters(tag['config'], tag.get('parameters'), self.des.userParameters.itemByName)
        configJson = module('lib.configJson')
        state = configJson.stateFromJson(configJson.GENERATOR_BIN, type(self.state('bin_2x1x3_label_text_engraved_colored')[0]), config)
        return self.binBuilder.rebuildBin(self.des, body, state, settings, False)


def heights(run, body):
    return [round(text.height, 4) for text in run.texts(body)]


def groupA(run):
    # p181: two compartments, the text fills the label, made 5 characters longer by its parameter, rebuilt: every
    # letter in its compartment, not below the floor, sketches fully constrained
    # Test data (runs of 16.11.2026): "Schrauben M4x2", 14 characters, doesn't fit a compartment of a 2x1 bin even at
    # Bold's 3.42 mm and was refused, rightly. "Bolzen" (6) was still limited by the tab, not the width: the tab
    # limits the height of the letters themselves, "Bolzen" with its ascenders came out 7.773 mm, "M3" 7.736 mm, so the
    # height of a short text is no measure for another one. "Bolzen M4x2" (11) fitted at 4.385 mm: a compartment takes
    # about 48 mm of text height per character count, a text fills it from 7 characters at 7.77 mm and still fits at
    # the floor of 3.42 mm with 14. "Muttern" (7) fills it, "Muttern M4x2" (12) fits
    (state, settings) = run.state('bin_2x1x3_label_text_engraved_colored', compartmentsX=2, labelText='Muttern', isLabelBold=True)
    body = run.binBuilder.buildBin(run.des, state, settings)[0]
    before = heights(run, body)
    short = run.binBuilder.buildBin(run.des, dataclasses.replace(state, labelText='Mu'), settings)[0]
    tabHeight = max(heights(run, short))
    run.check('a: the built text fills the width, lower than the tab lets "Mu" be', len(before) > 0 and max(before) < tabHeight - 1e-4, f'{before}, "Mu" {tabHeight}')
    names = run.lengthen(body, MORE)
    run.check('a: text parameters made longer', len(names) > 0, str(names))
    try:
        (bodies, notes) = run.rebuild(body, settings)
    except ValueError as err:
        run.check('a: rebuilt', False, str(err))
        return
    body = bodies[0]
    box = body.boundingBox
    middle = (box.minPoint.x + box.maxPoint.x) / 2
    letters = run.letters(body)
    left = [b for b in letters if b.boundingBox.minPoint.x < middle]
    right = [b for b in letters if b.boundingBox.minPoint.x >= middle]
    run.check('a: letters in the left compartment', len(left) > 0 and max(b.boundingBox.maxPoint.x for b in left) <= middle + TOLERANCE,
              f'{len(left)} letters to {max(b.boundingBox.maxPoint.x for b in left) * 10:.2f} mm, middle {middle * 10:.2f} mm' if left else 'none')
    run.check('a: letters in the right compartment', len(right) > 0 and max(b.boundingBox.maxPoint.x for b in right) <= box.maxPoint.x + TOLERANCE,
              f'{len(right)} letters to {max(b.boundingBox.maxPoint.x for b in right) * 10:.2f} mm, bin to {box.maxPoint.x * 10:.2f} mm' if right else 'none')
    after = heights(run, body)
    floor = run.textStyles.minTextHeight('Bold')
    run.check('a: text smaller, not below the floor', len(after) > 0 and max(after) < max(before) and min(after) >= floor - 1e-6, f'{before} -> {after}, floor {floor:.4f}')
    loose = run.constraints.unconstrainedSketches([s for c in run.components(body) for s in c.sketches if 'text' in s.name or 'icon' in s.name])
    run.check('a: label sketches fully constrained', len(loose) == 0, str(loose))
    run.check('a: colored letters in Text', all(b.appearance is not None and b.appearance.name == module('lib.gridfinityUtils.labelColors').appearanceName('#2060D0') for b in letters), str({b.appearance.name if b.appearance else None for b in letters}))
    run.check('a: no notes', len(notes) == 0, str(notes))
    run.healthy('a')


def groupB(run):
    # a short text made longer that still fits keeps its height
    (state, settings) = run.state('bin_2x1x3_label_text_engraved_colored', labelText='M3')
    body = run.binBuilder.buildBin(run.des, state, settings)[0]
    before = heights(run, body)
    run.lengthen(body, 'x5')
    (bodies, _) = run.rebuild(body, settings)
    after = heights(run, bodies[0])
    run.check('b: height unchanged', before == after and len(after) > 0, f'{before} -> {after}')
    run.healthy('b')


def groupC(run):
    # a text that doesn't fit even at the floor isn't built, the reason names it
    (state, settings) = run.state('bin_2x1x3_label_text_engraved_colored', labelText='M3')
    body = run.binBuilder.buildBin(run.des, state, settings)[0]
    run.lengthen(body, ' Zylinderschrauben mit Innensechskant DIN 912 verzinkt')
    try:
        run.rebuild(body, settings)
        run.check('c: refused', False, 'it was built')
    except ValueError as err:
        run.check('c: refused, the reason names it', "doesn't fit the label" in str(err), str(err))


def groupD(run):
    # p210: two lines with umlauts and descenders, -1 mm: the letters between the bottom and the top edge
    (case, settings) = (lambda c: (c, run.tc.caseSettings(c)))(run.tc.loadCase(os.path.join(CASES, 'label_1u_two_lines_heavy.json'), run.stateClasses))
    bodies = run.labelBuilder.buildLabel(run.des, dataclasses.replace(case.state, line1='ÄÖÜ', line2='gjpy', offsetY=-0.1), settings)
    insert = bodies[0]
    letters = [b for b in bodies[1:] if ' text ' in b.name]
    (top, bottom) = (max(b.boundingBox.maxPoint.y for b in letters), min(b.boundingBox.minPoint.y for b in letters))
    run.check('d: umlauts under the top edge', top <= insert.boundingBox.maxPoint.y + TOLERANCE, f'{(insert.boundingBox.maxPoint.y - top) * 10:.3f} mm to spare')
    run.check('d: descenders over the bottom edge', bottom >= insert.boundingBox.minPoint.y - TOLERANCE, f'{(bottom - insert.boundingBox.minPoint.y) * 10:.3f} mm to spare')
    run.healthy('d')


def groupE(run):
    # the text changed in the rebuild dialog of an uncolored bin, the way the old code only set the parameter (review)
    (state, settings) = run.state('bin_2x1x3_label_text_engraved', compartmentsX=2, labelText='Bolzen', isLabelBold=True)
    body = run.binBuilder.buildBin(run.des, state, settings)[0]
    before = heights(run, body)
    (bodies, notes) = run.binBuilder.rebuildBin(run.des, body, dataclasses.replace(state, labelText='Bolzen' + MORE), settings, False)
    after = heights(run, bodies[0])
    floor = run.textStyles.minTextHeight('Bold')
    run.check('e: rebuilt and fitted anew, not below the floor', len(after) > 0 and max(after) < max(before) and min(after) >= floor - 1e-6, f'{before} -> {after}')
    texts = [t.text for t in run.texts(bodies[0])]
    run.check('e: the new text', len(texts) > 0 and all(text == 'Bolzen' + MORE for text in texts), str(texts))
    run.healthy('e')


def groupF(run):
    # only one of the two compartments' parameters made longer: the edit isn't lost (review)
    (state, settings) = run.state('bin_2x1x3_label_text_engraved_colored', compartmentsX=2, labelText='Bolzen', isLabelBold=True)
    body = run.binBuilder.buildBin(run.des, state, settings)[0]
    names = sorted({text.textParameter.expression for text in run.texts(body) if text.textParameter is not None})
    first = run.des.userParameters.itemByName(names[0])
    first.expression = run.parameterUtils.textExpression(first.textValue + MORE)
    adsk.doEvents()
    (bodies, _) = run.rebuild(body, settings)
    texts = sorted({t.text for t in run.texts(bodies[0])})
    run.check('f: the edited text is built', texts == ['Bolzen' + MORE], f'{names}: {texts}')
    run.healthy('f')


GROUPS = {'a': groupA, 'b': groupB, 'c': groupC, 'd': groupD, 'e': groupE, 'f': groupF}


def run(_context: str):
    app = adsk.core.Application.get()
    original = app.activeDocument
    group = globals().get('GROUP')
    failed = 0
    for (key, build) in GROUPS.items():
        if group is not None and key != group:
            continue
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.name = f'Runde 19 end-to-end {key}'
        des = adsk.fusion.Design.cast(app.activeProduct)
        des.designIntent = adsk.fusion.DesignIntentTypes.PartDesignIntentType
        checks = Run(des)
        try:
            build(checks)
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
