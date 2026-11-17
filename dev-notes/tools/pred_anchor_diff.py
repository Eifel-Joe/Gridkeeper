"""Round 27: which of Pred's sketch coordinates follow what? Compares the world coordinates of every sketch curve
at 5 x 4 x 6 (r27_pred_walk.log) with another size (r27_pred_size_<size>.txt) and prints per sketch and axis the
distinct (value at 5x4x6 -> change) pairs. Run: python dev-notes/tools/pred_anchor_diff.py <walk log> <size file>"""
import re, sys
from collections import defaultdict

NUM = r'(-?[\d.]+)'
P = r'\(' + NUM + ',' + NUM + ',' + NUM + r'\)'


def sketches(path):
    out = {}
    name = None
    for line in open(path, encoding='utf-8'):
        m = re.match(r'## Skizze (\S+)', line)
        if m:
            name = m.group(1)
            out[name] = {}
            continue
        m = re.match(r'   k(\d+)\s+(\S+).*welt (?:c)?' + P + '(?:-' + P + ')?', line)
        if m and name:
            g = m.groups()
            pts = [tuple(float(v) for v in g[2:5])]
            if g[5] is not None:
                pts.append(tuple(float(v) for v in g[5:8]))
            out[name][int(g[0])] = (g[1], pts)
    return out


def main(base, other):
    a, b = sketches(base), sketches(other)
    for name in a:
        if name not in b:
            print(name, 'fehlt'); continue
        pairs = [defaultdict(set) for _ in range(3)]
        for k, (kind, pts) in a[name].items():
            if k not in b[name]:
                continue
            for p, q in zip(pts, b[name][k][1]):
                for axis in range(3):
                    pairs[axis][round(p[axis], 3)].add(round(q[axis] - p[axis], 3))
        print('##', name)
        for axis, label in enumerate('xyz'):
            items = sorted(pairs[axis].items())
            print('  %s: %s' % (label, '  '.join('%g:%s' % (v, '/'.join('%+g' % d for d in sorted(ds))) for v, ds in items)))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
