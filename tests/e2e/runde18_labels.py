# End-to-end check of round 18 (dev-notes/specs/2026-11-15-runde-18-design.md, "Ende-zu-Ende-Kriterium"), run in Fusion with
# the add-in loaded from this checkout. Set GROUP to 'a' to 'c' before running, each runs under a minute. No group
# opens a dialog: a script can't, execute() runs once the script is over (r18_dialog_probe). That the three dialogs open
# after a restart is on Joerg's hand test list. Each group builds into a
# document of its own, closes it when everything passes and prints OK or FAIL per point, ALL OK or N FAILED last.
import adsk.core, adsk.fusion, sys, os, dataclasses, json

ADDIN = '__main__D%3A%2FEntwicklung%2FGridfinity%2FFusionGridfinityGenerator%2FGridfinityGenerator_py'
CASES = r'D:\Entwicklung\Gridfinity\FusionGridfinityGenerator\tests\e2e\cases'
TOLERANCE = 0.001  # cm, 0.01 mm
SELECT = 'SelectCommand'


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
        self.configJson = module('lib.configJson')

    def check(self, point: str, ok: bool, detail: str = ''):
        self.results.append(ok)
        print(f'{"OK  " if ok else "FAIL"} {point}{": " + detail if detail else ""}')

    def state(self, caseName, **changes):
        case = self.tc.loadCase(os.path.join(CASES, caseName + '.json'), self.stateClasses)
        return (dataclasses.replace(case.state, **changes), self.tc.caseSettings(case))

    def healthy(self, name):
        bad = [(self.des.timeline.item(i).name, self.des.timeline.item(i).errorOrWarningMessage[:80]) for i in range(self.des.timeline.count) if self.des.timeline.item(i).healthState not in (0, 5)]
        self.check(f'{name}: nothing in the timeline unhealthy', len(bad) == 0, str(bad))

    def occurrenceOf(self, component):
        occurrences = self.des.rootComponent.allOccurrencesByComponent(component)
        return occurrences.item(0) if occurrences.count > 0 else None

    def inRoot(self, body):
        """The body as seen from the root, its box where it is in the design"""
        occurrence = self.occurrenceOf(body.parentComponent)
        return body.createForAssemblyContext(occurrence) if occurrence is not None else body

    def inserts(self):
        """Tagged insert bodies (not their letters) in the design, native"""
        return [body for (body, value) in self.tagUtils.findTaggedBodies(self.des, self.tagUtils.TAG_LABEL) if not body.parentComponent.name.startswith('Text')]


def box(body):
    b = body.boundingBox
    return tuple(round(v, 3) for v in (b.minPoint.x, b.minPoint.y, b.minPoint.z, b.maxPoint.x, b.maxPoint.y, b.maxPoint.z))


def sameBox(a, b):
    return all(abs(x - y) < TOLERANCE * 2 for (x, y) in zip(a, b))


def pocketOf(run, binBody):
    """The first Cullenect pocket joint origin of the bin, as seen from the root"""
    component = binBody.parentComponent
    occurrence = run.occurrenceOf(component)
    for jointOrigin in component.jointOrigins:
        if jointOrigin.attributes.itemByName(run.tagUtils.TAG_GROUP, run.tagUtils.TAG_POCKET) is not None:
            return jointOrigin.createForAssemblyContext(occurrence) if occurrence is not None else jointOrigin
    return None


def groupA(run):
    # an insert jointed into a pocket, rebuilt with another text: same spot, joint there, one insert in its component
    (binState, binSettings) = run.state('bin_1x1x3_cullenect')
    binBody = run.binBuilder.buildBin(run.des, binState, binSettings)[0]
    pocket = pocketOf(run, binBody)
    run.check('a: pocket found', pocket is not None)
    (state, settings) = run.state('label_1u_screw_text')
    built = run.labelBuilder.buildLabel(run.des, state, settings, True, pocket)
    insert = built[0]
    # started from a letter, as a right click on the raised text does (review: the pocket was lost then)
    letter = built[1]
    before = box(run.inRoot(insert))
    oldGroup = insert.name
    tag = run.tagUtils.readBodyTag(insert)
    run.check('a: the tag has the config', tag is not None and isinstance(tag[1].get('config'), dict))
    found = run.labelBuilder.insertPocket(run.des, letter)
    run.check('a: the old pocket is found from a letter', found is not None and found.name == pocket.name, found.name if found else 'none')
    (bodies, notes) = run.labelBuilder.rebuildLabel(run.des, letter, dataclasses.replace(state, line1='M5x20'), settings, False, found)
    run.check('a: rebuilt without notes', len(notes) == 0, str(notes))
    new = bodies[0]
    after = box(run.inRoot(new))
    run.check('a: new insert at the same spot', sameBox(before, after), f'{before} -> {after}')
    inserts = run.inserts()
    run.check('a: one insert left', len(inserts) == 1, str([b.name for b in inserts]))
    run.check('a: one insert in its component', len([b for b in new.parentComponent.bRepBodies if b.attributes.itemByName(run.tagUtils.TAG_GROUP, run.tagUtils.TAG_LABEL) is not None]) == 1)
    joints = [joint for joint in run.des.rootComponent.allJoints if 'in pocket' in joint.name]
    jointed = run.labelBuilder.insertPocket(run.des, new)
    run.check('a: jointed into the pocket again', len(joints) == 1 and jointed is not None and jointed.name == pocket.name and joints[0].healthState == 0,
              f'{[(j.name, j.healthState) for j in joints]}')
    names = [run.des.timeline.timelineGroups.item(i).name for i in range(run.des.timeline.timelineGroups.count)]
    run.check('a: the old group is gone', names.count(oldGroup) == 0 or oldGroup == new.name and names.count(oldGroup) == 1, str(names))
    newTag = run.tagUtils.readBodyTag(new)
    run.check('a: the new tag has the new text', newTag is not None and newTag[1]['config']['line1'] == 'M5x20')
    run.healthy('a')


def groupB(run):
    # an insert on its own, rebuilt wider: the same bottom left corner
    (state, settings) = run.state('label_1u_screw_text')
    insert = run.labelBuilder.buildLabel(run.des, state, settings)[0]
    before = box(run.inRoot(insert))
    (bodies, notes) = run.labelBuilder.rebuildLabel(run.des, insert, dataclasses.replace(state, widthUnits=2), settings, False, None)
    after = box(run.inRoot(bodies[0]))
    run.check('b: same bottom left corner', abs(before[0] - after[0]) < TOLERANCE and abs(before[1] - after[1]) < TOLERANCE, f'{before} -> {after}')
    run.check('b: wider', after[3] - after[0] > before[3] - before[0] + 3, f'{(before[3] - before[0]) * 10:.1f} -> {(after[3] - after[0]) * 10:.1f} mm')
    run.check('b: one insert left', len(run.inserts()) == 1)
    run.check('b: no notes', len(notes) == 0, str(notes))
    # a text only in line 2 goes back into line 2 (review: it came back in both lines)
    (second, secondSettings) = run.state('label_1u_screw_text', line1='', line2='DIN 912')
    insert = run.labelBuilder.buildLabel(run.des, second, secondSettings)[0]
    tag = run.tagUtils.readBodyTag(insert)[1]
    config = module('lib.rebuildUtils').configWithParameters(run.configJson.GENERATOR_LABEL, tag['config'], tag.get('parameters'), run.des.userParameters.itemByName, module('lib.gridfinityUtils.labelConfig').PARAMETER_FIELDS)
    run.check('b: line 2 alone stays line 2', (config['line1'], config['line2']) == ('', 'DIN 912'), f"{config['line1']!r}, {config['line2']!r}, {tag.get('parameters')}")
    run.healthy('b')


def groupC(run):
    # the config of a built insert read back, and cloned into the dialog's state without opening the dialog: a script
    # can't open a dialog, execute() only runs once the script is over (r18_dialog_probe, 16.11.2026). The dialog's
    # state is filled the way a clone fills it, readConfig and applyInputsState, read back with getInputsState, and set
    # back to what it was after
    labelEntry = module('commands.commandCreateLabel.entry')
    (state, settings) = run.state('label_25mm_free', textColor='#D02020', line2='DIN 912', showScrew=False, hardware='nut_nylon', surface='Debossed')
    insert = run.labelBuilder.buildLabel(run.des, state, settings)[0]
    config = run.tagUtils.readBodyTag(insert)[1]['config']
    text = run.configJson.configText(run.configJson.GENERATOR_LABEL, config)
    (read, notes) = run.configJson.readConfig(text, run.configJson.GENERATOR_LABEL, type(state), state)
    run.check('c: saved and loaded, same values', notes.isEmpty() and run.configJson.stateToJson(run.configJson.GENERATOR_LABEL, read) == config)
    if not notes.isEmpty():
        # labelEntry.readConfig would show its notes in a message box, which stops the script
        return
    kept = labelEntry.uiState.toDict()
    try:
        cloned = labelEntry.readConfig(text, 'Cloned')
        labelEntry.applyInputsState(cloned)
        shown = run.configJson.stateToJson(run.configJson.GENERATOR_LABEL, labelEntry.getInputsState())
    finally:
        labelEntry.uiState.initValues(kept)
    differing = {name: (config[name], shown[name]) for name in config if shown.get(name) != config[name]}
    run.check('c: the dialog state of the clone has the same values', len(differing) == 0, str(differing))
    run.check('c: the file name names the insert', labelEntry.configFileName(config) == insert.name, f'{labelEntry.configFileName(config)} / {insert.name}')


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
        doc.name = f'Runde 18 end-to-end {key}'
        des = adsk.fusion.Design.cast(app.activeProduct)
        des.designIntent = adsk.fusion.DesignIntentTypes.PartDesignIntentType
        checks = Run(des)
        try:
            build(checks)
        except Exception:
            import traceback
            checks.check(f'group {key} ran through', False, traceback.format_exc()[-800:])
        finally:
            # whatever happened, no dialog stays open
            if app.userInterface.activeCommand != SELECT:
                print('final terminate:', app.userInterface.terminateActiveCommand())
        failed += checks.results.count(False)
        if all(checks.results):
            doc.close(False)
        else:
            print(f'document left open: {doc.name}')
    if original is not None and original.isValid:
        original.activate()
    print('ALL OK' if failed == 0 else f'{failed} FAILED')
