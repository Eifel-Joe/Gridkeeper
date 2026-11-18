# End-to-end check of round 31 (dev-notes/specs/2026-11-18-runde-31-design.md, "Ende-zu-Ende-Kriterium"): a new bin
# jointed into a cell of a baseplate or a box floor, rebuilds keep it there. Run in Fusion per fusion_mcp_execute, one
# step per call (a box takes about a minute to build): the step comes from STATE, the document "r31_e2e" stays open
# between the steps and is closed without saving after the last one passes. Loads the add-in package fresh from REPO
# under a name of its own, the add-in Fusion has loaded isn't touched. Prints and logs OK or FAIL per point.
import adsk.core, adsk.fusion, dataclasses, importlib, importlib.util, json, os, sys, time, traceback

REPO = r'D:\Entwicklung\Gridfinity\wt-r31'
DIR = r'D:\Entwicklung\Gridfinity\fusion-auftraege'
STATE = DIR + r'\r31_cells.state'
LOG = DIR + r'\r31_cells.log'
CASES = REPO + r'\tests\e2e\cases'
PKG = 'r31cellsaddin'
DOC_NAME = 'r31_e2e'
TOLERANCE = 0.001  # cm, 0.01 mm
STEPS = ['plate', 'rebuild', 'box', 'boxbin', 'boxrebuild']


def log(text):
    print(text)
    with open(LOG, 'a', encoding='utf-8') as file:
        file.write(text + '\n')


def load():
    for name in [n for n in sys.modules if n == PKG or n.startswith(PKG + '.')]:
        del sys.modules[name]
    spec = importlib.util.spec_from_loader(PKG, loader=None, is_package=True)
    pkg = importlib.util.module_from_spec(spec)
    pkg.__path__ = [REPO]
    sys.modules[PKG] = pkg
    return lambda name: importlib.import_module(f'{PKG}.{name}')


class Run:
    def __init__(self, des, module, state):
        self.des = des
        self.state = state
        self.results = []
        snap = module('commands.commandSnapshotTests.entry')
        self.tc = module('commands.commandSnapshotTests.testCases')
        self.stateClasses = snap.STATE_CLASSES
        self.binBuilder = module('commands.commandCreateBin.binBuilder')
        self.plateBuilder = module('commands.commandCreateBaseplate.baseplateBuilder')
        self.boxBuilder = module('commands.commandCreateBox.boxBuilder')
        self.binCell = module('lib.gridfinityUtils.binCell')

    def check(self, point, ok, detail=''):
        self.results.append(bool(ok))
        log(f'{"OK  " if ok else "FAIL"} {point}{": " + detail if detail else ""}')

    def case(self, name, **changes):
        case = self.tc.loadCase(os.path.join(CASES, name + '.json'), self.stateClasses)
        return (dataclasses.replace(case.state, **changes), self.tc.caseSettings(case))

    def token(self, key, entity):
        self.state.setdefault('tokens', {})[key] = entity.entityToken

    def entity(self, key):
        found = self.des.findEntityByToken(self.state['tokens'][key])
        return found[0] if len(found) > 0 else None

    def occurrenceOf(self, component):
        occurrences = self.des.rootComponent.allOccurrencesByComponent(component)
        return occurrences.item(0) if occurrences.count > 0 else None

    def jointOrigin(self, component, name):
        native = component.jointOrigins.itemByName(name)
        occurrence = self.occurrenceOf(component)
        return native.createForAssemblyContext(occurrence) if native is not None and occurrence is not None else native

    def world(self, jointOrigin):
        """The joint origin's point in the root, its native point through the full transform of its occurrence"""
        native = jointOrigin.nativeObject or jointOrigin
        point = native.geometry.origin.copy()
        occurrence = jointOrigin.assemblyContext
        if occurrence is not None:
            point.transformBy(occurrence.transform2)
        return point

    def healthy(self, name):
        timeline = self.des.timeline
        bad = [(timeline.item(i).name, (timeline.item(i).errorOrWarningMessage or '')[:80]) for i in range(timeline.count) if timeline.item(i).healthState not in (0, 5)]
        self.check(f'{name}: nothing in the timeline unhealthy', len(bad) == 0, str(bad))

    def binInCell(self, name, binBody, cell):
        """The bin's Cell placement joint origin on the cell, one joint '... in cell' of the bin, its sketch constrained"""
        component = binBody.parentComponent
        own = self.jointOrigin(component, self.binCell.PLACEMENT_JOINT_ORIGIN)
        if own is None:
            self.check(f'{name}: has its {self.binCell.PLACEMENT_JOINT_ORIGIN}', False)
            return
        (a, b) = (self.world(own), self.world(cell))
        self.check(f'{name}: placement joint origin on {cell.name}', a.distanceTo(b) < TOLERANCE,
                   f'bin {[round(v * 10, 3) for v in (a.x, a.y, a.z)]} cell {[round(v * 10, 3) for v in (b.x, b.y, b.z)]} mm')
        def isOwnSide(side):
            jointOrigin = adsk.fusion.JointOrigin.cast(side)
            return jointOrigin is not None and jointOrigin.name == own.name and (jointOrigin.nativeObject or jointOrigin).parentComponent == component
        joints = [joint for joint in self.des.rootComponent.allJoints if self.binCell.isCellJointName(joint.name)
                  and (isOwnSide(joint.geometryOrOriginOne) or isOwnSide(joint.geometryOrOriginTwo))]
        self.check(f'{name}: one joint in cell', len(joints) == 1, str([joint.name for joint in joints]))
        loose = [sketch.name for sketch in component.sketches if sketch.name.startswith(self.binCell.PLACEMENT_JOINT_ORIGIN) and not sketch.isFullyConstrained]
        self.check(f'{name}: placement sketch fully constrained', len(loose) == 0, str(loose))
        self.check(f'{name}: the cell stays shown', (cell.nativeObject or cell).isLightBulbOn)

    def plateCells(self):
        component = self.entity('plate').parentComponent
        return lambda column, row: self.jointOrigin(component, f'Socket joint origin {column}-{row}')

    def boxCell(self, column, row):
        return self.jointOrigin(self.entity('box').parentComponent, f'Cell joint origin {column}-{row}')


def stepPlate(run):
    run.check('no baseplate or box: no cell offered', not run.binBuilder.hasCellParts(run.des))
    (state, settings) = run.case('baseplate_3x2_full', plateWidth=3, plateLength=3, hasJointOrigins=True)
    plate = run.plateBuilder.buildBaseplate(run.des, state, settings)[0]
    run.token('plate', plate)
    run.check('with a baseplate: cell offered', run.binBuilder.hasCellParts(run.des))
    cell = run.plateCells()
    for (key, caseName, changes, (column, row)) in [
        ('binA', 'bin_1x1x3_plain', {}, (2, 2)),
        ('binB', 'bin_1_5x2_5x3_half_grid', {'binWidth': 1, 'binLength': 1}, (3, 3)),
        ('binC', 'bin_1x1x3_plain', {'binWidth': 2}, (1, 1)),
    ]:
        target = cell(column, row)
        run.check(f'{key}: socket {column}-{row} can be picked', run.binBuilder.isCellJointOrigin(target))
        (state, settings) = run.case(caseName, **changes)
        body = run.binBuilder.buildBin(run.des, state, settings, cell=target)[0]
        run.token(key, body)
        run.binInCell(key, body, cell(column, row))
    foot = run.jointOrigin(run.entity('binA').parentComponent, run.binCell.PLACEMENT_JOINT_ORIGIN)
    run.check('a bin\'s placement joint origin isn\'t a cell', not run.binBuilder.isCellJointOrigin(foot))
    run.healthy('plate')


def stepRebuild(run):
    cell = run.plateCells()
    (state, settings) = run.case('bin_1x1x3_plain', binType='Solid')
    (bodies, notes) = run.binBuilder.rebuildBin(run.des, run.entity('binA'), state, settings, False)
    run.token('binA', bodies[0])
    run.check('binA rebuilt without notes', len(notes) == 0, str(notes))
    run.binInCell('binA rebuilt', bodies[0], cell(2, 2))
    # the half grid bin rebuilt for real too, its placement joint origin stays at the whole cell's center
    (state, settings) = run.case('bin_1_5x2_5x3_half_grid', binWidth=1, binLength=1, binType='Solid')
    (bodies, notes) = run.binBuilder.rebuildBin(run.des, run.entity('binB'), state, settings, False)
    run.token('binB', bodies[0])
    run.check('binB rebuilt without notes', len(notes) == 0, str(notes))
    run.binInCell('binB rebuilt', bodies[0], cell(3, 3))
    # a height only sets the parameter, the timeline and the joint stay
    (state, settings) = run.case('bin_1x1x3_plain', binWidth=2, binHeight=5)
    (bodies, notes) = run.binBuilder.rebuildBin(run.des, run.entity('binC'), state, settings, False)
    run.check('binC height set by its parameter without notes', len(notes) == 0, str(notes))
    run.check('binC kept its bodies (parameter edit, no rebuild)', bodies[0] == run.entity('binC'))
    run.token('binC', bodies[0])
    run.binInCell('binC after its height changed', bodies[0], cell(1, 1))
    (state, settings) = run.case('baseplate_3x2_full', plateWidth=3, plateLength=3, hasJointOrigins=True, plateType='Light')
    (bodies, notes) = run.plateBuilder.rebuildBaseplate(run.des, run.entity('plate'), state, settings, False)
    run.token('plate', bodies[0])
    run.check('baseplate rebuilt without notes', len(notes) == 0, str(notes))
    cell = run.plateCells()
    for (key, (column, row)) in [('binA', (2, 2)), ('binB', (3, 3)), ('binC', (1, 1))]:
        run.binInCell(f'{key} after the baseplate rebuild', run.entity(key), cell(column, row))
    run.healthy('rebuild')


def stepBox(run):
    started = time.time()
    (state, settings) = run.case('box_4x3x6', hasJointOrigins=False)
    bodies = run.boxBuilder.buildBox(run.des, state, settings)
    log(f'box built in {time.time() - started:.1f} s')
    box = [body for body in bodies if run.binBuilder.rebuildUtils.partRole(body.parentComponent) == 'Box'][0]
    run.token('box', box)
    names = [jointOrigin.name for jointOrigin in box.parentComponent.jointOrigins if jointOrigin.name.startswith('Cell joint origin ')]
    run.check('box built with hasJointOrigins False has its 12 floor cells', len(names) == 12, str(len(names)))


def stepBoxBin(run):
    cell = run.boxCell(1, 1)
    run.check('box cell 1-1 can be picked', run.binBuilder.isCellJointOrigin(cell))
    setOccurrence = run.occurrenceOf(run.entity('box').parentComponent).assemblyContext
    lid = [child.component for child in setOccurrence.childOccurrences if run.binBuilder.rebuildUtils.partRole(child.component) == 'Lid'][0]
    others = [jointOrigin.name for component in (run.entity('box').parentComponent, lid) for jointOrigin in component.jointOrigins
              if not jointOrigin.name.startswith('Cell joint origin ') and run.binBuilder.isCellJointOrigin(run.jointOrigin(component, jointOrigin.name))]
    run.check('no other joint origin of box or lid can be picked', len(others) == 0, str(others))
    (state, settings) = run.case('bin_1x1x3_plain', binWidth=2)
    body = run.binBuilder.buildBin(run.des, state, settings, cell=cell)[0]
    run.token('binD', body)
    run.binInCell('binD in the box', body, run.boxCell(1, 1))
    # rebuilt for real: the cell is three levels down, Boxes, the set and its Box (review)
    (state, settings) = run.case('bin_1x1x3_plain', binWidth=2, binType='Solid')
    (bodies, notes) = run.binBuilder.rebuildBin(run.des, run.entity('binD'), state, settings, False)
    run.token('binD', bodies[0])
    run.check('binD rebuilt without notes', len(notes) == 0, str(notes))
    run.binInCell('binD rebuilt in the box', bodies[0], run.boxCell(1, 1))
    run.healthy('boxbin')


def stepBoxRebuild(run):
    started = time.time()
    (state, settings) = run.case('box_4x3x6', heightU=7)
    (bodies, notes) = run.boxBuilder.rebuildBox(run.des, run.entity('box'), state, settings, False)
    log(f'box rebuilt in {time.time() - started:.1f} s, notes {notes}')
    box = [body for body in bodies if run.binBuilder.rebuildUtils.partRole(body.parentComponent) == 'Box'][0]
    run.token('box', box)
    run.binInCell('binD after the box rebuild', run.entity('binD'), run.boxCell(1, 1))
    run.healthy('boxrebuild')


def run(_context):
    app = adsk.core.Application.get()
    before = app.activeDocument
    state = json.load(open(STATE)) if os.path.exists(STATE) else {'next': 0}
    step = STEPS[state['next']]
    started = time.time()
    log(f'=== step {state["next"] + 1} of {len(STEPS)}: {step}')
    document = None
    passed = False
    try:
        module = load()
        if step == 'plate':
            document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            document.name = DOC_NAME
            des = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
            des.designType = adsk.fusion.DesignTypes.ParametricDesignType
            des.designIntent = adsk.fusion.DesignIntentTypes.HybridDesignIntentType
        else:
            document = [doc for doc in app.documents if doc.name.startswith(DOC_NAME)][0]
            document.activate()
            des = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
        runner = Run(des, module, state)
        {'plate': stepPlate, 'rebuild': stepRebuild, 'box': stepBox, 'boxbin': stepBoxBin, 'boxrebuild': stepBoxRebuild}[step](runner)
        passed = all(runner.results)
        log('ALL OK' if passed else f'{runner.results.count(False)} FAILED')
    except Exception:
        log(traceback.format_exc()[-2500:])
    finally:
        if passed:
            state['next'] += 1
        json.dump(state, open(STATE, 'w'))
        if passed and state['next'] >= len(STEPS) and document is not None:
            document.close(False)
            log('document closed')
        elif before is not None and before.isValid and document is not None and before != document:
            try:
                before.activate()
            except Exception:
                pass
        log(f'=== {"DONE" if state["next"] >= len(STEPS) else "NEXT " + STEPS[state["next"]]} after {time.time() - started:.1f} s')
