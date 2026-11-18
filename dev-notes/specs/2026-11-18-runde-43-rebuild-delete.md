# Round 43: faster deletion of the old part on a rebuild, joint names without a counter

Points: p533 (box rebuild: deleting the old box takes over four minutes), p430 (joint name after a rebuild with a
counter "(1)").

## p533: deleting the old group

### Problem
A rebuild with a joint moved over to the new part (a bin in a cell of a rebuilt baseplate or box, an insert in the
pocket of a rebuilt bin, a box label or a user joint on a rebuilt box) deletes the old timeline group item by item
(`rebuildUtils.removeOldGroup(oneByOne=True)` → `timelineRemoval.deleteOneByOne`). A box set has 298 items, about
0.85–0.92 s each: 252–274 s of a 726 s rebuild (round 39 measurement). Deleting the group as a whole
(`TimelineGroup.deleteMe(True)`) took 41 s but took the moved joint along (15.11.2026: the insert fell back to the
origin). Every rebuild (bin, insert, baseplate, box, box label) goes through `rebuildUtils.rebuild` →
`removeOldGroup`, so all sister paths share the one function.

### Measured (Fusion, `fusion-auftraege/r43_probe.py`, 18.11.2026)
Scenarios: baseplate 2×2 with a bin jointed into socket 2-2, rebuilt Full → Light (joint moved by name, 42 old items);
Cullenect bin with an insert in its pocket, rebuilt 1×1 → 1×2 (pocket joint moved, 61 old items).

| Way of deleting the old group | Baseplate + bin | Bin + insert |
|---|---|---|
| Today: item by item, marker after them | 2.72 s, joint kept | 5.41 s, joint kept |
| Group as a whole, marker at the end | 0.44 s, **joint gone**, bin at the origin | 0.48 s, **joint gone** |
| Group as a whole, marker right after the group | 0.36 s, **joint gone** | not run (same result expected) |
| Header off, old occurrence `deleteMe()` (took all 42 items) | 0.46 s, **joint gone** | not run |
| Header off, **the old joint origins the moved joints used, one by one, then the rest as a new group, whole** | **0.67 s, joint kept, bin in the new cell, timeline healthy** | **0.90 s, joint kept, insert in the new pocket, timeline healthy** |

Reading: a moved joint still depends on the old joint origin it used before. Deleting that one on its own frees the
joint; deleting it as part of a whole (group or occurrence) takes the joint along as a dependent.

### Decision
- The repoint functions (`repointJoints`, `repointJointsByName`) note on the target each old joint origin (native) a
  joint was moved away from (`RebuildTarget.movedFrom`).
- `removeOldGroup`: with joints moved over, the group header goes, the items of the noted joint origins are deleted one
  by one (`deleteOneByOne`), the items left (contiguous in the timeline) are grouped anew and that group deleted as a
  whole. Fallback to item by item for what is left when: a noted joint origin couldn't be deleted (the whole delete
  would take its joint), the items left aren't contiguous, the whole delete fails or leaves items behind.
- Without moved joints nothing changes (group as a whole, fallback item by item).
- The flow is Fusion-free in `timelineRemoval` (testable with stand-ins); `rebuildUtils` hands in which items are
  noted.

### Not part of this
- Faster building of the new box, preview, parameter edits (round 39).
- Joints that couldn't be moved over: they go with the old part as before.

## p430: joint name with a counter

### Problem
The bin command names its joint into a cell "<bin> in cell", the label command "<insert> in pocket". On a rebuild the
new joint is made while the old one still exists, Fusion counts up: "… in cell (1)", the next rebuild "(2)"; the same
for inserts "… in pocket (1)" (measured in `r43_probe.py`, step onebyone).

### Decision
After the old group is gone (not on a preview), each joint the build made that ends in a counter " (n)" gets the
lowest free name of base, "base (1)", … below its own, among the other joints of its component; Fusion's name is kept
when none is free. A pure helper `jointNames.freedName(name, taken)` decides; `rebuildUtils.rebuild` notes the joints
there were before the build (entity tokens) and renames the new ones. Applies to every rebuild (bin in cell, insert in
pocket, any other joint a build makes).

### Not part of this
- Joints of the user, and joints moved over (they keep their name).

## End-to-end criterion
Fusion, code of this branch, no patches (`fusion-auftraege/r43_e2e.py`):
1. Baseplate with a bin in a cell, rebuilt: bin in the same cell of the new baseplate, one joint, timeline healthy,
   old group gone, deletion faster than item by item (log of the step).
2. Bin with an insert in its pocket, rebuilt: insert in the new pocket, timeline healthy, old group gone.
3. Bin in a cell rebuilt itself: joint named "… in cell" without counter; insert rebuilt itself: "… in pocket".
4. Box 5×4×6 with the two probe joints of round 39 (`r39_mess.py` scheme), rebuilt 6×4×6: probe joints at the same
   seat of the new set, timeline healthy, time of `removeOldGroup` measured against 252–274 s. Only measured values go
   into the CHANGELOG.
Plus pytest green, every sketch the generator makes still fully constrained (no sketch is touched).
