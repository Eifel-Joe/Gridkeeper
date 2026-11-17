# Erzeugt lib/gridfinityUtils/predHingeEdges.json aus fusion-auftraege/r29_walk (Preds Kantenlisten der Laschen-Fasen,
# Teil-Rahmen, mm)
import json, sys
WALK = 'D:/Entwicklung/Gridfinity/fusion-auftraege/r29_walk'
SETS = {'M3x30': ('Hinge_M3x30.json', ['Chamfer3', 'Chamfer4', 'Chamfer5']), 'Plain': ('Hinge.json', ['Chamfer3', 'Chamfer5', 'Chamfer6'])}
out = {}
for variant, (name, chamfers) in SETS.items():
    d = json.load(open(WALK + '/' + name, encoding='utf-8'))
    o = d['occurrences'][0]['origin']
    loc = lambda p: [round(p[i] - o[i], 4) + 0.0 for i in range(3)]
    steps = []
    for it in d['items']:
        if it['name'] not in chamfers:
            continue
        (es,) = it['edgeSets']
        assert es['type'] == 'EqualDistanceChamferEdgeSet' and es['isTangentChain']
        edges = []
        for e in es['edges']:
            if e['type'] == 'Line3D':
                edges.append({'line': [loc(e['start']), loc(e['end'])]})
            elif e['type'] == 'Arc3D':
                edges.append({'arc': [loc(e['center']), e['radius'], loc(e['start']), loc(e['end'])]})
            elif e['type'] == 'Circle3D':
                edges.append({'circle': [loc(e['center']), e['radius']]})
            else:
                raise ValueError(e['type'])
        steps.append({'pred': it['name'], 'distance': es['distance']['value'], 'edges': edges})
    out[variant] = steps
# Pinned has none of these chamfers (Pred's Hinge_Pined): listed empty, so predHinge.predChamfers can insist on the key
out['Pinned'] = []
text = json.dumps(out, indent=1)
open(sys.argv[1], 'w', encoding='utf-8').write(text + '\n')
print({v: [(s['pred'], s['distance'], len(s['edges'])) for s in st] for v, st in out.items()})
