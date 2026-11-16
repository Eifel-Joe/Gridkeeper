# End-to-end check of round 20 (docs/specs/runde-20-uebergabe.md), run in Fusion with the add-in loaded from this
# checkout. Set GROUP to 'a' to 'c' before running, each runs under a minute, no dialog. Each group builds into a
# document of its own, closes it when everything passes and prints OK or FAIL per point, ALL OK or N FAILED last.
import adsk.core, adsk.fusion, sys, os, dataclasses

ADDIN = '__main__D%3A%2FEntwicklung%2FGridfinity%2FFusionGridfinityGenerator%2FGridfinityGenerator_py'
CASES = r'D:\Entwicklung\Gridfinity\FusionGridfinityGenerator\tests\e2e\cases'


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
        self.tagUtils = module('lib.tagUtils')

    def check(self, point: str, ok: bool, detail: str = ''):
        self.results.append(ok)
        print(f'{"OK  " if ok else "FAIL"} {point}{": " + detail if detail else ""}')

    def state(self, caseName, **changes):
        case = self.tc.loadCase(os.path.join(CASES, caseName + '.json'), self.stateClasses)
        return (dataclasses.replace(case.state, **changes), self.tc.caseSettings(case))

    def healthy(self, name):
        bad = [(self.des.timeline.item(i).name, self.des.timeline.item(i).errorOrWarningMessage[:80]) for i in range(self.des.timeline.count) if self.des.timeline.item(i).healthState not in (0, 5)]
        self.check(f'{name}: nothing in the timeline unhealthy', len(bad) == 0, str(bad))

    def pocket(self, occurrence):
        native = next(o for o in occurrence.component.jointOrigins if o.attributes.itemByName(self.tagUtils.TAG_GROUP, self.tagUtils.TAG_POCKET) is not None)
        return native.createForAssemblyContext(occurrence)

    def occurrence(self, body):
        return self.des.rootComponent.allOccurrencesByComponent(body.parentComponent).item(0)


def groupA(run):
    # p220: the pocket insertPocket gives is seen from the root and selectable, the rebuild joints into it again
    (binState, binSettings) = run.state('bin_1x1x3_cullenect')
    binBody = run.binBuilder.buildBin(run.des, binState, binSettings)[0]
    pocket = run.pocket(run.occurrence(binBody))
    (state, settings) = run.state('label_1u_screw_text')
    insert = run.labelBuilder.buildLabel(run.des, state, settings, True, pocket)[0]
    found = run.labelBuilder.insertPocket(run.des, insert)
    run.check('a: pocket seen from the root', found is not None and found.assemblyContext is not None,
              f'{found.name if found else None} in {found.assemblyContext.fullPathName if found and found.assemblyContext else None}')
    ui = adsk.core.Application.get().userInterface
    ui.activeSelections.clear()
    try:
        ui.activeSelections.add(found)
        run.check('a: pocket selectable', ui.activeSelections.count == 1)
    except Exception as err:
        run.check('a: pocket selectable', False, str(err))
    finally:
        ui.activeSelections.clear()
    (bodies, notes) = run.labelBuilder.rebuildLabel(run.des, insert, dataclasses.replace(state, line1='M5x20'), settings, False, found)
    again = run.labelBuilder.insertPocket(run.des, bodies[0])
    run.check('a: rebuilt into the same pocket, no notes', again is not None and again.name == pocket.name and len(notes) == 0, f'{notes}')
    run.healthy('a')


def groupB(run):
    # the pocket of a bin built after the insert is refused, the rebuild would build before that bin
    (state, settings) = run.state('label_1u_screw_text')
    insert = run.labelBuilder.buildLabel(run.des, state, settings)[0]
    (binState, binSettings) = run.state('bin_1x1x3_cullenect')
    binBody = run.binBuilder.buildBin(run.des, binState, binSettings)[0]
    later = run.pocket(run.occurrence(binBody))
    try:
        run.labelBuilder.rebuildLabel(run.des, insert, state, settings, False, later)
        run.check('b: pocket of a later bin refused', False, 'it was rebuilt')
    except ValueError as err:
        run.check('b: pocket of a later bin refused', 'comes after the insert' in str(err), str(err))
    run.healthy('b')


def groupC(run):
    # a bin copied in Fusion, a second occurrence of its component: the insert in the copy's pocket stays in the copy
    (binState, binSettings) = run.state('bin_1x1x3_cullenect')
    binBody = run.binBuilder.buildBin(run.des, binState, binSettings)[0]
    first = run.occurrence(binBody)
    move = adsk.core.Matrix3D.create()
    move.translation = adsk.core.Vector3D.create(10, 0, 0)
    parent = first.assemblyContext.component if first.assemblyContext is not None else run.des.rootComponent
    copy = parent.occurrences.addExistingComponent(first.component, move)
    copy = copy.createForAssemblyContext(first.assemblyContext) if first.assemblyContext is not None else copy
    (state, settings) = run.state('label_1u_screw_text')
    insert = run.labelBuilder.buildLabel(run.des, state, settings, True, run.pocket(copy))[0]
    found = run.labelBuilder.insertPocket(run.des, insert)
    path = found.assemblyContext.fullPathName if found is not None and found.assemblyContext is not None else None
    run.check('c: pocket of the copy, not of the first bin', path == copy.fullPathName, f'{path} / copy {copy.fullPathName} / first {first.fullPathName}')
    (bodies, _) = run.labelBuilder.rebuildLabel(run.des, insert, state, settings, False, found)
    again = run.labelBuilder.insertPocket(run.des, bodies[0])
    run.check('c: rebuilt into the copy', again is not None and again.assemblyContext is not None and again.assemblyContext.fullPathName == copy.fullPathName,
              again.assemblyContext.fullPathName if again is not None and again.assemblyContext is not None else 'none')
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
        doc.name = f'Runde 20 end-to-end {key}'
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
