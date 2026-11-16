# End-to-end check of round 17 (dev-notes/specs/2026-11-15-runde-17-design.md, "Ende-zu-Ende-Kriterium"), run in Fusion with
# the add-in loaded from this checkout. The groups run each under a minute for the Fusion MCP's time limit: set GROUP
# to 'a' to 'g' before running (all without). Each group builds into a document of its own, closes it when everything
# passes and prints OK or FAIL per point, ALL OK or N FAILED last.
import adsk.core, adsk.fusion, sys, os, dataclasses, time

ADDIN = '__main__D%3A%2FEntwicklung%2FGridfinity%2FGridkeeper%2FGridkeeper_py'
CASES = r'D:\Entwicklung\Gridfinity\Gridkeeper\tests\e2e\cases'
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
        self.labelBuilder = module('commands.commandCreateLabel.labelBuilder')
        self.binBuilder = module('commands.commandCreateBin.binBuilder')

    def check(self, point: str, ok: bool, detail: str = ''):
        self.results.append(ok)
        print(f'{"OK  " if ok else "FAIL"} {point}{": " + detail if detail else ""}')

    def state(self, caseName, **changes):
        case = self.tc.loadCase(os.path.join(CASES, caseName + '.json'), self.stateClasses)
        return (dataclasses.replace(case.state, **changes), self.tc.caseSettings(case))

    def label(self, caseName, **changes):
        (state, settings) = self.state(caseName, **changes)
        return self.labelBuilder.buildLabel(self.des, state, settings)

    def healthy(self, name):
        bad = [(self.des.timeline.item(i).name, self.des.timeline.item(i).errorOrWarningMessage[:80]) for i in range(self.des.timeline.count) if self.des.timeline.item(i).healthState not in (0, 5)]
        self.check(f'{name}: nothing in the timeline unhealthy', len(bad) == 0, str(bad))


def parts(bodies, kind):
    """The text or symbol bodies of an insert built by labelBuilder, by their names"""
    insert = bodies[0]
    return [body for body in bodies[1:] if body.name.startswith(f'{insert.name} {kind} ')]


def byName(component_bodies, names):
    return [body for body in component_bodies if body.name in names]


def groupA(run):
    # p110: two lines with descenders, height correction -1 mm: the lowest point of the letters on the insert. Heavy
    # only, Regular and Bold would need letters below their floor there, see group b
    for (style, surface) in (('Heavy', 'Flush'), ('Heavy', 'Embossed'), ('Heavy', 'Debossed')):
        bodies = run.label('label_1u_two_lines_heavy', line1='gjpy', line2='Agjp', offsetY=-0.1, textStyle=style, surface=surface)
        insert = bodies[0]
        letters = parts(bodies, 'text')
        lowest = min(body.boundingBox.minPoint.y for body in letters)
        bottom = insert.boundingBox.minPoint.y
        run.check(f'p110 {style} {surface}: lowest letter point at or above the insert bottom', lowest >= bottom - TOLERANCE,
                  f'letters from {lowest * 10:.3f} mm, insert from {bottom * 10:.3f} mm, {len(letters)} letter bodies')
    run.healthy('p110')


def groupB(run):
    # the floor: Regular can't shrink below 4.43 mm, its descenders at -1 mm would need it, the check tells
    (regular, _) = run.state('label_1u_two_lines_heavy', line1='gjpy', line2='Agjp', offsetY=-0.1, textStyle='Regular')
    problem = run.labelBuilder.labelProblem(regular)
    run.check('floor: Regular two lines at -1 mm are reported', problem is not None and 'Two lines' in problem, str(problem))
    (heavy, _) = run.state('label_1u_two_lines_heavy', line1='gjpy', line2='Agjp', offsetY=-0.1, textStyle='Heavy')
    run.check('floor: Heavy two lines at -1 mm build', run.labelBuilder.labelProblem(heavy) is None, str(run.labelBuilder.labelProblem(heavy)))
    try:
        run.labelBuilder.buildLabel(run.des, regular, [])
        run.check('floor: building it is refused', False, 'it was built')
    except ValueError as err:
        run.check('floor: building it is refused', 'Two lines' in str(err), str(err))


def topRim(run, name, insert):
    """The top face of the insert keeps its outline whole: a rounded rectangle of 4 lines and 4 arcs as large as the
    insert. A cut through the rim adds edges to it"""
    thickness = module('lib.gridfinityUtils.const').CULLENECT_LABEL_THICKNESS
    tops = [face for face in insert.faces if abs(face.boundingBox.minPoint.z - thickness) < TOLERANCE and abs(face.boundingBox.maxPoint.z - thickness) < TOLERANCE]
    top = max(tops, key=lambda face: face.area) if tops else None
    if top is None:
        run.check(f'{name}: top face found', False)
        return
    outer = next(loop for loop in top.loops if loop.isOuter)
    (box, faceBox) = (insert.boundingBox, top.boundingBox)
    sameSize = abs(box.minPoint.x - faceBox.minPoint.x) < TOLERANCE and abs(box.maxPoint.x - faceBox.maxPoint.x) < TOLERANCE \
        and abs(box.minPoint.y - faceBox.minPoint.y) < TOLERANCE and abs(box.maxPoint.y - faceBox.maxPoint.y) < TOLERANCE
    run.check(f'{name}: top rim whole', outer.edges.count == 8 and sameSize, f'{outer.edges.count} edges in its outline, as large as the insert {sameSize}')


def symbolOffRim(run, name, bodies):
    """The symbol stays 0.4 mm off the right, top and bottom edge: an overhang of 0.2 mm cut through below that would
    leave the outline of the top face whole, topRim alone wouldn't tell"""
    rim = module('lib.gridfinityUtils.cullenectLabelLayout').DEBOSS_RIM
    (insert, symbols) = (bodies[0].boundingBox, parts(bodies, 'symbol'))
    gaps = {
        'right': insert.maxPoint.x - max(body.boundingBox.maxPoint.x for body in symbols),
        'top': insert.maxPoint.y - max(body.boundingBox.maxPoint.y for body in symbols),
        'bottom': min(body.boundingBox.minPoint.y for body in symbols) - insert.minPoint.y,
    }
    run.check(f'{name}: symbol 0.4 mm off right, top and bottom', all(gap >= rim - TOLERANCE for gap in gaps.values()),
              ', '.join(f'{side} {gap * 10:.3f} mm' for (side, gap) in gaps.items()))


def groupC(run):
    # p140: 25 mm with a screw, debossed: the top layer stays whole all around, the symbol keeps 0.4 mm off the edge
    bodies = run.label('label_25mm_free', surface='Debossed', line1='gjpy')
    topRim(run, 'p140 debossed screw', bodies[0])
    symbolOffRim(run, 'p140 debossed screw', bodies)
    # the nylon nut debossed, label_2u_hardware as it is
    bodies = run.label('label_2u_hardware')
    topRim(run, 'p140 debossed nylon nut', bodies[0])
    symbolOffRim(run, 'p140 debossed nylon nut', bodies)
    run.healthy('p140')


def groupD(run):
    # p52: a text fitted to its room, the insert made 1 mm narrower afterwards: text and symbol stay apart
    bodies = run.label('label_1u_screw_text', line1='Schrauben M3x10 lang')
    (textNames, symbolNames) = ([body.name for body in parts(bodies, 'text')], [body.name for body in parts(bodies, 'symbol')])
    component = parts(bodies, 'text')[0].parentComponent
    width = next(parameter for parameter in run.des.userParameters if parameter.name.endswith('_width'))
    before = width.value
    width.expression = f'{width.expression} - 1 mm'
    adsk.doEvents()
    run.check('p52: width 1 mm smaller', abs(before - width.value - 0.1) < TOLERANCE, f'{before * 10:.2f} -> {width.value * 10:.2f} mm')
    letters = byName(component.bRepBodies, textNames)
    symbols = byName(component.bRepBodies, symbolNames)
    gap = min(body.boundingBox.minPoint.x for body in symbols) - max(body.boundingBox.maxPoint.x for body in letters)
    # without the 1 mm of p52 the gap would still be above 0 by the fitting reserve, it has to keep the icon gap
    iconGap = module('lib.gridfinityUtils.const').CULLENECT_ICON_GAP
    run.check('p52: text and symbol keep the icon gap', gap >= iconGap - TOLERANCE, f'{gap * 10:.3f} mm, {len(letters)} letters, {len(symbols)} symbol bodies')
    run.healthy('p52')


def groupE(run):
    # p51: build time of the insert with a nylon lock nut under 5 s, the crimp ring measured
    for (hardware, limit) in (('nut_nylon', 5.0), ('crimp_ring_closed', None)):
        started = time.perf_counter()
        run.label('label_2u_hardware', hardware=hardware, textStyle='Heavy')
        seconds = time.perf_counter() - started
        run.check(f'p51: {hardware} built in {seconds:.2f} s', limit is None or seconds < limit, f'limit {limit} s' if limit else 'measured')
    run.healthy('p51')


def binLabel(run, iconName, isHeld):
    """p180: a bin label with a Cullenect symbol takes the path the measurement says (dims up to 40 points, moved
    above), its icon and text sketches are fully constrained, and a longer text leaves the symbol where it is"""
    (case, settings) = (lambda c: (c, run.tc.caseSettings(c)))(run.tc.loadCase(os.path.join(CASES, 'bin_2x1x3_label_icon_text_embossed_colored.json'), run.stateClasses))
    body = run.binBuilder.buildBin(run.des, dataclasses.replace(case.state, labelIcon=iconName, labelText='M4'), settings)[0]
    occurrence = next(o for o in run.des.rootComponent.allOccurrences if o.component == body.parentComponent) if body.parentComponent != run.des.rootComponent else None
    components = [body.parentComponent] + ([child.component for child in occurrence.childOccurrences] if occurrence is not None else [])
    sketches = [sketch for component in components for sketch in component.sketches]
    iconSketches = [sketch for sketch in sketches if sketch.name.endswith('icon sketch')]
    held = any(sketch.sketchDimensions.count > 10 for sketch in iconSketches)
    run.check(f'p180 {iconName}: {"held by dims" if isHeld else "moved"}', len(iconSketches) > 0 and held == isHeld,
              f'{[(sketch.name, sketch.sketchDimensions.count) for sketch in iconSketches]}')
    constraints = module('commands.commandSnapshotTests.constraints')
    loose = constraints.unconstrainedSketches([sketch for sketch in sketches if 'icon' in sketch.name or 'text' in sketch.name])
    run.check(f'p180 {iconName}: label sketches fully constrained', len(loose) == 0, str(loose))

    # The colored case keeps the label bodies apart from the bin, so the symbol is a body of its own; embossed into the
    # bin it is joined and has none (the first try looked for its extrude feature's faces and found nothing). A longer
    # text adds letters to the right, every body there was keeps its place, the symbol with them
    def boxes():
        return sorted(tuple(round(v, 4) for v in (b.boundingBox.minPoint.x, b.boundingBox.minPoint.y, b.boundingBox.minPoint.z, b.boundingBox.maxPoint.x, b.boundingBox.maxPoint.y, b.boundingBox.maxPoint.z))
                      for component in run.des.allComponents for b in component.bRepBodies)
    before = boxes()
    names = []
    for sketch in sketches:
        for text in sketch.sketchTexts:
            if text.textParameter is not None and text.textParameter.expression not in names:
                names.append(text.textParameter.expression)
    parameters = [run.des.userParameters.itemByName(name) for name in names]
    textUtils = module('lib.gridfinityUtils.parameterUtils')
    for parameter in parameters:
        parameter.expression = textUtils.textExpression(parameter.textValue + ' Mutter')
    adsk.doEvents()
    after = boxes()
    moved = [box for box in before if box not in after]
    run.check(f'p180 {iconName}: symbol and letters stay where they are after a longer text', len(moved) == 0 and len(after) > len(before) and len(parameters) > 0,
              f'{len(before)} -> {len(after)} bodies, moved {moved[:3]}, {len(parameters)} text parameters')


def groupF(run):
    binLabel(run, 'Cullenect nut', True)
    binLabel(run, 'Cullenect nut nylon', False)
    run.healthy('p180')


def groupG(run):
    binLabel(run, 'Cullenect crimp ring closed', False)
    run.healthy('p180')


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
        doc.name = f'Runde 17 end-to-end {key}'
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
