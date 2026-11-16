# End-to-end check of round 21 (docs/specs/2026-11-16-runde-21-design.md), run in Fusion with the add-in loaded from
# this checkout. Set GROUP to 'a' to 'c' before running, each runs under a minute, no dialog. Each group builds into a
# document of its own, closes it when everything passes and prints OK or FAIL per point, ALL OK or N FAILED last.
import adsk.core, adsk.fusion, sys, os, dataclasses

ADDIN = '__main__D%3A%2FEntwicklung%2FGridfinity%2FFusionGridfinityGenerator%2FGridfinityGenerator_py'
CASES = r'D:\Entwicklung\Gridfinity\FusionGridfinityGenerator\tests\e2e\cases'
TOLERANCE = 0.001  # cm


def module(name):
    return sys.modules[f'{ADDIN}.{name}']


class Run:
    def __init__(self, des):
        self.des = des
        self.results = []
        snap = module('commands.commandSnapshotTests.entry')
        self.tc = module('commands.commandSnapshotTests.testCases')
        self.stateClasses = snap.STATE_CLASSES
        self.labelBuilder = module('commands.commandCreateLabel.labelBuilder')
        self.binBuilder = module('commands.commandCreateBin.binBuilder')
        self.textStyles = module('lib.gridfinityUtils.textStyles')

    def check(self, point: str, ok: bool, detail: str = ''):
        self.results.append(ok)
        print(f'{"OK  " if ok else "FAIL"} {point}{": " + detail if detail else ""}')

    def state(self, caseName, **changes):
        case = self.tc.loadCase(os.path.join(CASES, caseName + '.json'), self.stateClasses)
        return (dataclasses.replace(case.state, **changes), self.tc.caseSettings(case))

    def healthy(self, name):
        bad = [(self.des.timeline.item(i).name, self.des.timeline.item(i).errorOrWarningMessage[:80]) for i in range(self.des.timeline.count) if self.des.timeline.item(i).healthState not in (0, 5)]
        self.check(f'{name}: nothing in the timeline unhealthy', len(bad) == 0, str(bad))


def groupA(run):
    # p232, bin: bins have Regular and Bold only (no Heavy). A narrow tab gives Regular letters lower than 4.43 mm,
    # the hint names that limit; a wide tab gives no hint
    for (tabWidth, expected) in ((0.6, True), (1.3, False)):
        run.textStyles.clearNotes()
        (state, settings) = run.state('bin_2x1x3_label_text_engraved', labelText='M3', isLabelBold=False, tabWidth=tabWidth)
        run.binBuilder.buildBin(run.des, state, settings)
        noted = run.textStyles.notes()
        hint = run.textStyles.hintText(noted, suggestHeavy=False) or ''
        heights = [round(height * 10, 2) for (_, height, _) in noted]
        if expected:
            run.check(f'a: tab {tabWidth * 10:g} mm, Regular below 4.43 mm is hinted', len(noted) > 0 and 'below the 4.43 mm' in hint, f'{heights} mm: {hint}')
        else:
            run.check(f'a: tab {tabWidth * 10:g} mm, no hint', len(noted) == 0, f'{heights} mm')
    run.healthy('a')


def groupB(run):
    # p233: an insert without a symbol, its long text fitted, the width made 1 mm smaller after: the text stays inside
    (state, settings) = run.state('label_1u_welle_6mm', line1='Zylinderschraube DIN912', textStyle='Heavy')
    bodies = run.labelBuilder.buildLabel(run.des, state, settings)
    insertName = bodies[0].name
    letterNames = [body.name for body in bodies[1:]]
    component = bodies[0].parentComponent
    textComponent = bodies[1].parentComponent if len(bodies) > 1 else component
    width = next(parameter for parameter in run.des.userParameters if parameter.name.endswith('_width'))
    width.expression = f'{width.expression} - 1 mm'
    adsk.doEvents()
    insert = next(body for body in component.bRepBodies if body.name == insertName)
    letters = [body for body in textComponent.bRepBodies if body.name in letterNames]
    right = max(body.boundingBox.maxPoint.x for body in letters)
    edge = insert.boundingBox.maxPoint.x
    run.check('b: text inside the insert after -1 mm', right <= edge + TOLERANCE, f'letters to {right * 10:.3f} mm, edge {edge * 10:.3f} mm, {(edge - right) * 10:.3f} mm to spare')
    run.healthy('b')


def groupC(run):
    # p232, insert: a long Regular text fitted below 4.43 mm is hinted with that limit, Heavy with 3.05 mm
    for (style, limit) in (('Regular', '4.43'), ('Heavy', '3.05')):
        run.textStyles.clearNotes()
        (state, settings) = run.state('label_1u_screw_text', line1='Zylinderschraube DIN 912', textStyle=style)
        run.labelBuilder.buildLabel(run.des, state, settings)
        noted = run.textStyles.notes()
        hint = run.textStyles.hintText(noted) or ''
        run.check(f'c: {style} insert hinted with {limit} mm', len(noted) > 0 and f'below the {limit} mm' in hint and f'in {style}' in hint, hint)
        run.check(f'c: {style} preview note', run.textStyles.previewNote(noted) == ', text below the print limit')
    run.healthy('c')


GROUPS = {'a': groupA, 'b': groupB, 'c': groupC}


def run(_context: str):
    app = adsk.core.Application.get()
    original = app.activeDocument
    group = globals().get('GROUP')
    failed = 0
    for (key, build) in GROUPS.items():
        if group is not None and key != group:
            continue
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.name = f'Runde 21 end-to-end {key}'
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
