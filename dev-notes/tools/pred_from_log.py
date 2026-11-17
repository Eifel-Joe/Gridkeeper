"""Round 27: turns fusion-auftraege/r27_pred_walk.log (Pred's box at 5 x 4 x 6, read step by step) into
- lib/gridfinityUtils/predBoxEdges.json: per chamfer/fillet step the value and its edges/faces (mm)
- tests/e2e/pred_box/steps_5x4x6.json: per step the body volumes (mm3) and face counts after the step.
Run: python dev-notes/tools/pred_from_log.py <path to r27_pred_walk.log>"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NUM = r'(-?[\d.]+)'
P = r'\(' + NUM + ',' + NUM + ',' + NUM + r'\)'


def parseEdge(text):
    m = re.match(r'Kante L' + P + '-' + P, text)
    if m:
        v = [float(x) for x in m.groups()]
        return {'kind': 'line', 'start': v[0:3], 'end': v[3:6]}
    m = re.match(r'Kante A c' + P + ' r' + NUM + ' n' + P + ' ' + P + '-' + P, text)
    if m:
        v = [float(x) for x in m.groups()]
        return {'kind': 'arc', 'center': v[0:3], 'radius': v[3], 'normal': v[4:7], 'start': v[7:10], 'end': v[10:13]}
    m = re.match(r'Kante C c' + P + ' r' + NUM + ' n' + P, text)
    if m:
        v = [float(x) for x in m.groups()]
        return {'kind': 'circle', 'center': v[0:3], 'radius': v[3], 'normal': v[4:7]}
    m = re.match(r'Fläche (\w+) bb' + P + '-' + P + '(?: n' + P + ')?', text)
    if m:
        g = m.groups()
        f = {'kind': 'face', 'surface': g[0], 'min': [float(x) for x in g[1:4]], 'max': [float(x) for x in g[4:7]]}
        if g[7] is not None:
            f['normal'] = [float(x) for x in g[7:10]]
        return f
    m = re.match(r'Kante (\w+) bb' + P + '-' + P, text)
    if m:
        g = m.groups()
        return {'kind': g[0], 'min': [float(x) for x in g[1:4]], 'max': [float(x) for x in g[4:7]]}
    raise ValueError(text)


def main(log):
    edges, steps = {}, []
    step = None
    current = None
    for line in open(log, encoding='utf-8'):
        line = line.rstrip('\n')
        m = re.match(r'=== #(\d+) (?:\[[^\]]*\] )?(\S+) (\w+)', line)
        if m:
            step = '#%s %s' % (m.group(1), m.group(2))
            current = None
            continue
        m = re.match(r'   (\w+EdgeSet) (\w+)=.*?\[([-\d.]+)\], \d+ Kanten:', line)
        if m:
            current = {'set': m.group(1), m.group(2): float(m.group(3)), 'items': []}
            edges.setdefault(step, []).append(current)
            continue
        if line.startswith('       ') and current is not None:
            current['items'].append(parseEdge(line.strip()))
            continue
        m = re.match(r'   danach: (.*)', line)
        if m:
            current = None
            entry = {'step': step}
            for part in m.group(1).split(' | '):
                b = re.match(r'(\w+) V=([-\d.]+) F=(\d+)', part.strip())
                if b:
                    entry[b.group(1).lower()] = float(b.group(2))
                    entry[b.group(1).lower() + 'Faces'] = int(b.group(3))
            steps.append(entry)
    os.makedirs(os.path.join(ROOT, 'tests', 'e2e', 'pred_box'), exist_ok=True)
    json.dump(edges, open(os.path.join(ROOT, 'lib', 'gridfinityUtils', 'predBoxEdges.json'), 'w'), indent=1)
    json.dump(steps, open(os.path.join(ROOT, 'tests', 'e2e', 'pred_box', 'steps_5x4x6.json'), 'w'), indent=1)
    print(len(edges), 'edge steps,', len(steps), 'steps')


if __name__ == '__main__':
    main(sys.argv[1])
