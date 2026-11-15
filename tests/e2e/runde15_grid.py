# End-to-end check of round 15 (docs/specs/2026-11-15-runde-15-design.md, "Ende-zu-Ende-Kriterium"), run in Fusion with
# the add-in loaded from this checkout. The groups run each under a minute for the Fusion MCP's time limit: set GROUP
# to 'a' to 'f' before running (all without). Each group builds into a document of its own, closes it when everything
# passes and prints OK or FAIL per point, ALL OK or N FAILED last.
import adsk.core, adsk.fusion, sys, os, dataclasses, re

ADDIN = '__main__D%3A%2FEntwicklung%2FGridfinity%2FFusionGridfinityGenerator%2FGridfinityGenerator_py'
CASES = r'D:\Entwicklung\Gridfinity\FusionGridfinityGenerator\tests\e2e\cases'
TOLERANCE = 0.001  # cm, 0.01 mm


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
        self.plateBuilder = module('commands.commandCreateBaseplate.baseplateBuilder')
        self.tagUtils = module('lib.tagUtils')

    def check(self, point: str, ok: bool, detail: str = ''):
        self.results.append(ok)
        print(f'{"OK  " if ok else "FAIL"} {point}{": " + detail if detail else ""}')

    def load(self, name):
        case = self.tc.loadCase(os.path.join(CASES, name + '.json'), self.stateClasses)
        return (case, self.tc.caseSettings(case))

    def bin(self, caseName, **changes):
        (case, settings) = self.load(caseName)
        return self.binBuilder.buildBin(self.des, dataclasses.replace(case.state, **changes), settings)[0]

    def plate(self, caseName, **changes):
        (case, settings) = self.load(caseName)
        return self.plateBuilder.buildBaseplate(self.des, dataclasses.replace(case.state, **changes), settings)[0]

    def setAll(self, suffix, expression):
        for parameter in self.des.userParameters:
            if parameter.name.endswith(suffix):
                parameter.expression = expression
        adsk.doEvents()

    def healthy(self, name):
        bad = [(self.des.timeline.item(i).name, self.des.timeline.item(i).errorOrWarningMessage[:80]) for i in range(self.des.timeline.count) if self.des.timeline.item(i).healthState not in (0, 5)]
        self.check(f'{name}: nothing in the timeline unhealthy', len(bad) == 0, str(bad))


def centeredGrid(run, name, body, prefix, step):
    """The joint origins of the body's component make a grid of the base unit, centered on the body"""
    component = body.parentComponent
    origins = [origin for origin in component.jointOrigins if origin.name.startswith(prefix)]
    if not origins:
        run.check(f'{name}: joint origins found', False)
        return
    points = [origin.geometry.origin for origin in origins]
    xs = sorted({round(point.x, 4) for point in points})
    ys = sorted({round(point.y, 4) for point in points})
    box = body.boundingBox
    stepsOk = all(abs(b - a - step) < TOLERANCE for (a, b) in zip(xs, xs[1:])) and all(abs(b - a - step) < TOLERANCE for (a, b) in zip(ys, ys[1:]))
    centerX = (xs[0] + xs[-1]) / 2 - (box.minPoint.x + box.maxPoint.x) / 2
    centerY = (ys[0] + ys[-1]) / 2 - (box.minPoint.y + box.maxPoint.y) / 2
    run.check(f'{name}: {len(origins)} joint origins one base unit apart, centered on the body', stepsOk and abs(centerX) < TOLERANCE and abs(centerY) < TOLERANCE,
              f'x {[round(x * 10, 2) for x in xs]} y {[round(y * 10, 2) for y in ys]} off center {round(centerX * 10, 4)}, {round(centerY * 10, 4)} mm')
    loose = [sketch.name for sketch in component.sketches if sketch.name.startswith(prefix) and not sketch.isFullyConstrained]
    run.check(f'{name}: joint origin sketches fully constrained', len(loose) == 0, str(loose))


def groupA(run):
    """p170: feet and sockets follow a changed base unit, also on a bin placed beside another"""
    first = run.bin('bin_1x1x3_plain', binWidth=4, binLength=2, hasJointOrigins=True)
    second = run.bin('bin_1x1x3_plain', binWidth=2, binLength=1, hasJointOrigins=True)
    plate = run.plate('baseplate_3x2_full', plateWidth=3, plateLength=3, hasJointOrigins=True)
    run.setAll('_baseWidth', '50 mm')
    run.setAll('_baseLength', '50 mm')
    centeredGrid(run, 'Bin 4x2', first, 'Foot joint origin', 5.0)
    centeredGrid(run, 'Second bin 2x1', second, 'Foot joint origin', 5.0)
    centeredGrid(run, 'Baseplate 3x3', plate, 'Socket joint origin', 5.0)
    run.healthy('group a')


def sameAsFresh(run, name, caseName='bin_3x1x3_cullenect_compartments', **changes):
    """Built at 42 mm and set to 40 mm by its parameter, the same volume as one built at 40 mm"""
    (case, _) = run.load(caseName)
    changed = run.bin(caseName, **changes)
    prefix = [p.name for p in run.des.userParameters if p.name.endswith('_baseWidth')][-1].rsplit('_', 1)[0]
    run.des.userParameters.itemByName(f'{prefix}_baseWidth').expression = '40 mm'
    adsk.doEvents()
    fresh = run.bin(caseName, baseWidth=case.state.baseWidth * 40 / 42, **changes)
    difference = changed.volume - fresh.volume
    run.check(f'{name}: 42 -> 40 mm by parameter has the volume of a bin built at 40 mm', abs(difference) < 0.001, f'{round(difference * 1000, 4)} mm3')


def groupB(run):
    """p60: sockets of compartments beside the grid follow a changed base width, the bin of the list (round 5)"""
    sameAsFresh(run, 'Cullenect, 4x2, 3 compartments', binWidth=4, binLength=2)
    run.healthy('group b')


def groupC(run):
    """p60, its sister path: text labels of compartments beside the grid"""
    sameAsFresh(run, 'Text labels, 4x2, 3 compartments', binWidth=4, binLength=2, labelStyle='Engraved', labelText='AB')
    run.healthy('group c')


def groupE(run):
    """p60: sockets of 4, 2 and 1 units side by side and behind"""
    sameAsFresh(run, 'Cullenect mixed 4x2', caseName='bin_4x2x3_cullenect_mixed')
    run.healthy('group e')


def groupD(run):
    """p35: Cullenect from 1.2 mm walls, thicker ones build with their sockets"""
    for wallMm in (1.2, 2.0, 3.0):
        body = run.bin('bin_1x1x3_cullenect', wallThickness=wallMm / 10)
        pockets = [origin for origin in body.parentComponent.jointOrigins if origin.attributes.itemByName(run.tagUtils.TAG_GROUP, run.tagUtils.TAG_POCKET) is not None]
        run.check(f'Cullenect, wall {wallMm} mm: built with its socket', len(pockets) == 1, f'{len(pockets)} pockets')
    cullenect = module('lib.gridfinityUtils.cullenect')
    run.check('Cullenect, wall 1.19 mm: the dialog check tells why', cullenect.wallProblem(0.119) is not None, str(cullenect.wallProblem(0.119)))
    run.healthy('group d')


def groupF(run):
    """p101: dividers up to the top with walls of 2 and 3 mm, every corner swept up to the top in one rounding per run,
    none filleted with a smaller radius (the step), and no small level face left at a corner"""
    for wallMm in (2.0, 3.0):
        body = run.bin('bin_3x2x3_dividers_to_top_3_columns', wallThickness=wallMm / 10, labelStyle='Outline', labelText='')
        features = body.parentComponent.features
        # the corners' own fillets, not the one of the foot cutter ('Raised divider corners foot cutout corner fillet')
        fillets = [f.name for f in features.filletFeatures if re.fullmatch(r'Raised divider corner \d+ fillet', f.name)]
        sweeps = [f.name for f in features.sweepFeatures if f.name.startswith('Raised divider corner')]
        run.check(f'Wall {wallMm} mm: no corner filleted instead of swept', len(fillets) == 0 and len(sweeps) > 0, f'{len(sweeps)} sweeps, fillets {fillets}')
        box = body.boundingBox
        small = []
        for face in body.faces:
            plane = adsk.core.Plane.cast(face.geometry)
            if plane is None or abs(abs(plane.normal.z) - 1) > 1e-6:
                continue
            z = face.boundingBox.minPoint.z
            # level faces between the floor and the top no larger than a corner's section (r^2 - pi r^2 / 4, 0.7 mm2 at
            # 1.8 mm): the steps of a corner. The ledge a thick wall leaves under the lip runs along the wall, 3.9 mm2
            # at 2 mm, and isn't one (Fusion 15.11.2026)
            if box.minPoint.z + 0.5 < z < box.maxPoint.z - 0.01 and face.area < 0.01:
                small.append((round(z * 10, 3), round(face.area * 100, 3)))
        run.check(f'Wall {wallMm} mm: no small level face at the corners', len(small) == 0, f'{small[:8]} (z mm, mm2)')
    run.healthy('group f')


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
        doc.name = f'Runde 15 end-to-end {key}'
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
