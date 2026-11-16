# End-to-end check of round 13 (dev-notes/specs/2026-11-15-runde-13-design.md, "Ende-zu-Ende-Kriterium"), run in Fusion
# with the add-in loaded from this checkout: Utilities > Scripts, or the content via the Fusion MCP as a script. It builds
# into new documents of its own, closes them when everything passes and prints OK or FAIL per point.
import adsk.core, adsk.fusion, sys, os, dataclasses

ADDIN = '__main__D%3A%2FEntwicklung%2FGridfinity%2FGridkeeper%2FGridkeeper_py'
CASES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cases') if '__file__' in globals() else r'D:\Entwicklung\Gridfinity\Gridkeeper\tests\e2e\cases'
TOLERANCE_MM = 0.001


def module(name):
    return sys.modules[f'{ADDIN}.{name}']


def run(_context: str):
    app = adsk.core.Application.get()
    snap = module('commands.commandSnapshotTests.entry')
    tc = module('commands.commandSnapshotTests.testCases')
    binBuilder = module('commands.commandCreateBin.binBuilder')
    plateBuilder = module('commands.commandCreateBaseplate.baseplateBuilder')
    labelBuilder = module('commands.commandCreateLabel.labelBuilder')
    tagUtils = module('lib.tagUtils')
    load = lambda name: tc.loadCase(os.path.join(CASES, name + '.json'), snap.STATE_CLASSES)
    original = app.activeDocument
    results = []

    def check(point: str, ok: bool, detail: str = ''):
        results.append(ok)
        print(f'{"OK  " if ok else "FAIL"} {point}{": " + detail if detail else ""}')

    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = 'Runde 13 end-to-end'
    des = adsk.fusion.Design.cast(app.activeProduct)
    des.designIntent = adsk.fusion.DesignIntentTypes.PartDesignIntentType
    root = des.rootComponent
    occurrenceOf = lambda body: root.allOccurrencesByComponent(body.parentComponent).item(0)
    world = lambda body: body.createForAssemblyContext(occurrenceOf(body)).boundingBox

    plate = load('baseplate_3x2_full')
    plateBuilder.buildBaseplate(des, plate.state, tc.caseSettings(plate))
    binCase = load('bin_3x1x3_cullenect_compartments')
    cullenectState = dataclasses.replace(binCase.state, binWidth=2, binLength=1, binHeight=6, compartmentsX=2)
    cullenectBin = binBuilder.buildBin(des, cullenectState, tc.caseSettings(binCase))
    coloredCase = load('bin_2x1x3_label_text_engraved_colored')
    coloredState = dataclasses.replace(coloredCase.state, binWidth=1, binLength=1)
    coloredBin = binBuilder.buildBin(des, coloredState, tc.caseSettings(coloredCase))
    binOccurrence = occurrenceOf(cullenectBin[0])
    pocket = binOccurrence.component.jointOrigins.itemByName('Compartment 2 pocket joint origin').createForAssemblyContext(binOccurrence)
    labelCase = load('label_1u_screw_text_colored')
    labelState = dataclasses.replace(labelCase.state, useUnits=True, widthUnits=1)
    jointed = labelBuilder.buildLabel(des, labelState, tc.caseSettings(labelCase), True, pocket)
    free = labelBuilder.buildLabel(des, labelState, tc.caseSettings(labelCase))

    # 1. the browser
    containers = {occurrence.component.name: [child.component.name for child in occurrence.childOccurrences] for occurrence in root.occurrences}
    check('1 containers Grid, Bins, Label in the root', sorted(containers) == ['Bins', 'Grid', 'Label'], str(containers))
    check('1 a baseplate in Grid, two bins in Bins, two inserts in Label', (len(containers.get('Grid', [])), len(containers.get('Bins', [])), len(containers.get('Label', []))) == (1, 2, 2))
    for (name, bodies) in (('colored bin', coloredBin), ('jointed insert', jointed), ('free insert', free)):
        marking = bodies[1:]
        inText = all(body.parentComponent.name.startswith('Text') for body in marking)
        textComponents = []
        for body in marking:
            if not any(component == body.parentComponent for component in textComponents):
                textComponents.append(body.parentComponent)
        onlyMarking = all(any(body == part for part in marking) for component in textComponents for body in component.bRepBodies)
        check(f'1 {name}: its text and symbol in Text and nothing else', len(marking) > 0 and inText and onlyMarking)
    check('1 the Cullenect bin has no Text component', all(not child.component.name.startswith('Text') for child in binOccurrence.childOccurrences))

    # 2. jointed into its pocket, the other beside everything
    insertBox = world(jointed[0])
    floor = pocket.geometry.origin
    offsets = ((insertBox.minPoint.x + insertBox.maxPoint.x) / 2 - floor.x, (insertBox.minPoint.y + insertBox.maxPoint.y) / 2 - floor.y, insertBox.minPoint.z - floor.z)
    check('2 the insert sits mid floor of its pocket', all(abs(value) * 10 < TOLERANCE_MM for value in offsets), str([round(value * 10, 4) for value in offsets]))
    check('2 its joint is healthy', all(joint.healthState == adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState for joint in root.allJoints) and len(root.allJoints) == 1)
    collection = adsk.core.ObjectCollection.create()
    collection.add(cullenectBin[0].createForAssemblyContext(binOccurrence))
    collection.add(jointed[0].createForAssemblyContext(occurrenceOf(jointed[0])))
    interference = [result.interferenceBody.volume * 1000 for result in des.analyzeInterference(des.createInterferenceInput(collection))]
    check('2 no interference of insert and bin', len(interference) == 0, f'{interference} mm3')
    freeBox = world(free[0])
    others = [world(body) for (body, _) in tagUtils.findTaggedBodies(des, tagUtils.TAG_BIN) + tagUtils.findTaggedBodies(des, tagUtils.TAG_BASEPLATE)]
    overlaps = [box for box in others if freeBox.minPoint.x < box.maxPoint.x and box.minPoint.x < freeBox.maxPoint.x and freeBox.minPoint.y < box.maxPoint.y and box.minPoint.y < freeBox.maxPoint.y]
    check('2 the insert without a pocket lies beside everything', len(overlaps) == 0)

    # 3. + 7. rebuild of the Cullenect bin with another height, the insert stays in its pocket
    rebuilt = binBuilder.rebuildBin(des, cullenectBin[0], dataclasses.replace(cullenectState, binHeight=4, hasLip=not cullenectState.hasLip), tc.caseSettings(binCase), False)[0]
    newOccurrence = occurrenceOf(rebuilt[0])
    check('3 the rebuilt bin is in Bins', newOccurrence.assemblyContext is not None and newOccurrence.assemblyContext.component.name == 'Bins')
    check('3 the root is active afterwards', des.activeComponent == root)
    newFloor = newOccurrence.component.jointOrigins.itemByName('Compartment 2 pocket joint origin').createForAssemblyContext(newOccurrence).geometry.origin
    insertBox = world(jointed[0])
    check('7 the insert sits on the floor of the new pocket', abs(insertBox.minPoint.z - newFloor.z) * 10 < TOLERANCE_MM and abs(newFloor.z - floor.z) > 0.1, f'{round(floor.z * 10, 2)} -> {round(newFloor.z * 10, 2)} mm')
    check('7 its joint is healthy', all(joint.healthState == adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState for joint in root.allJoints) and len(root.allJoints) == 1)

    # 4. a longer live text adds its letters in Text
    textParameter = [parameter for parameter in des.userParameters if parameter.name.startswith('gfLabel2_text1')][0]
    textComponent = [body.parentComponent for body in free[1:]][0]
    before = textComponent.bRepBodies.count
    textParameter.expression = module('lib.gridfinityUtils.parameterUtils').textExpression('M3x10 longer')
    adsk.doEvents()
    check('4 the letters of a longer text are in Text', textComponent.bRepBodies.count > before and free[0].parentComponent.bRepBodies.count == 1, f'{before} -> {textComponent.bRepBodies.count}')

    # 5. sketches and timeline
    loose = [sketch.name for component in des.allComponents for sketch in component.sketches if 'joint origin' in sketch.name.lower() and not sketch.isFullyConstrained]
    check('5 the joint origin sketches are fully constrained', len(loose) == 0, str(loose))
    unhealthy = [des.timeline.item(index).name for index in range(des.timeline.count) if des.timeline.item(index).healthState not in (0, 5)]
    check('5 nothing in the timeline is unhealthy', len(unhealthy) == 0, str(unhealthy))
    passed = all(results)
    if passed:
        doc.close(False)

    # 6. an old part design with a bin as bodies in the root, built the way a preview builds: rebuilt in the root
    old = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    old.name = 'Runde 13 old document'
    oldDesign = adsk.fusion.Design.cast(app.activeProduct)
    oldDesign.designIntent = adsk.fusion.DesignIntentTypes.PartDesignIntentType
    plain = load('bin_1x1x3_plain')
    oldBin = binBuilder.buildBin(oldDesign, plain.state, tc.caseSettings(plain), mayChangeDocument=False)
    oldRebuilt = binBuilder.rebuildBin(oldDesign, oldBin[0], dataclasses.replace(plain.state, compartmentsX=2), tc.caseSettings(plain), False)[0]
    ok = oldRebuilt[0].parentComponent == oldDesign.rootComponent and oldDesign.designIntent == adsk.fusion.DesignIntentTypes.PartDesignIntentType and oldDesign.rootComponent.occurrences.count == 0
    check('6 an old bin of root bodies is rebuilt as root bodies, the part design stays', ok)
    if ok:
        old.close(False)
    if original is not None and original.isValid:
        original.activate()
    print('ALL OK' if all(results) else f'{results.count(False)} FAILED')
