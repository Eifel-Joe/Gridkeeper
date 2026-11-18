# Round 45: box build faster, the next levers

Points: p296 (box build and rebuild with the small parts are slow), p480 (box build gets slower with every box in the
document). Box after Pred's parametric Gridfinity Storage Box v1.1 (https://www.printables.com/model/543553, CC BY-NC,
by Pred), drawn in code.

## What was measured (Fusion 2706.1.17, master 794253f, 18.11.2026)

Scripts `fusion-auftraege/r45_profil.py` (full cProfile of box 1 and box 2 5×4×6 with the small parts in one new hybrid
document) and `r45_probe.py` (three levers). Times attributed from each Fusion call to the repo function that made it.

| | Box 1 | Box 2 |
|---|---|---|
| Whole build | 114 s, 965 parameters after | 248 s, 1930 after |
| predSketch sketches (`WorldSketch.close`) | 33 s | 87 s |
| – of it `Parameter.expression` of the dimensions (`_apply` → `applyTo`) | 8 s | 41 s (235 calls, 195 ms each) |
| Joint origins (`createPointJointOrigins`, 35 points, each its own sketch, plane, point, two dimensions) | 21 s | 43 s |
| Small parts (`insertParts`) | 42 s | 63 s |
| Edge and face lookups of chamfers and fillets (`_pick`, `floorGrid`) | 11 s | 16 s |
| `Sketch.isComputeDeferred` (174 toggles, 70 of them on joint-origin sketches) | 6 s | 15 s |

Model parameters of one box by what made them: sketches 487, extrudes 157, joint origins 152, construction planes 48,
joints 40, chamfers 34, fillets 24, sweeps 16, patterns 4, user parameters 3. Every parameter makes every later call of
the document dearer (round 39), box 2 pays for box 1's.

Probes (`r45_probe.log`):
1. A joint origin without a sketch: `JointGeometry.createByPoint(component.originConstructionPoint)` with
   `JointOriginInput.offsetX/Y/Z` as expressions: 160 ms against 846 ms the sketch way, 4 model parameters against 8, no
   sketch, no plane. Same place and axes as the sketch way; `gfBox1_baseWidth` 5 → 6 moves both alike (200 → 242 mm,
   read through a rigid probe joint on each).
2. Of the 215 expressions `predSketch._apply` sets, 129 cancel to a constant, e.g.
   `abs((((gfBox1_baseWidth * 42 mm) + 20 mm) - 21 mm) - (((gfBox1_baseWidth * 42 mm) + 20 mm) - 41 mm))`: two points
   that hang on the same measure, the dimension between them never changes (LabelSlot, LabelRail, catch tabs, sweep
   cuts, handle holders …). Today each of them still gets the expression.
3. `Component.findBRepUsingPoint(point, BRepEdgeEntityType, 1e-5)` at a point on an edge returns exactly that edge,
   0.25 ms per call; reading all 5702 edges of the finished box body by index takes 5.7 s. Each `_pick` today reads
   every edge (and face) of the body and turns it into its item form: 34 294 `edges.item` per build.

## Requirement
Build and rebuild measurably faster, box 2 more than box 1 (p480). Geometry unchanged (box snapshot cases), every
sketch of the set fully constrained, parameter changes act as before, joints made on the box's joint origins (bins in
cells, stacking, lid, small parts, user joints, rebuild by name) work as before.

## Decision

### A. Box joint origins without sketches
New `baseGenerator.createOffsetJointOrigins(points, component, *, name)`, same points and return as
`createPointJointOrigins`: one joint origin per point on the component's origin point, its offsets X, Y, Z the point's
dims through `valueInput` (an expression where the dim hangs on a parameter, a number otherwise; signed, no `abs` needed).
No construction plane, no sketch, no dimension. The box uses it for every joint origin it makes today with
`createPointJointOrigins`: cells, stack bottom and top, seats, the lid pair (`boxBuilder._buildBox`) and the handle pin's
seat (`predHandlePin.createHandlePin`). Names, order and the `forOk` guard stay.
- Saves per box: 35 sketches, about 9 planes, 70 dimensions, 70 deferral toggles, 140 model parameters.
- Bins, baseplates and labels keep `createPointJointOrigins` this round (they aren't part of the points; new point).
- Boxes already in a document keep their sketch joint origins; a rebuild makes the new kind, joints move over by name as
  today (R36, R43).

### B. No expression for a dimension that cannot change
`Dim` gets a linear form of its expression: the coefficients of the parameters and of every non-linear part (min, max,
abs, a product or quotient of two parameter-bound dims), each such part keyed by its expression text, plus a constant.
`+`/`-` add the forms, `*`/`/` by a plain number scale them; everything else becomes one part of its own. A new
property `Dim.dependsOnParameters` is false when every coefficient cancels (within 1e-9). `Dim.parameter` starts a form
with its name, `Dim.length`/`Dim.number` a constant one. The kind (VALUE/EXPRESSION) and the expression text stay as
today, so every other generator sees no change.
- `WorldSketch._apply` leaves a distance or diameter dimension at the value it was drawn with when its dim does not
  depend on parameters (no `applyTo`, no `Parameter.expression` call). The value it was drawn with is exactly that
  constant (the point coordinates come from the same dims). The dimension stays; the sketch stays fully constrained.
- Saves 129 of 215 expression calls per box (box 2: about 25 s).

### C. Edges and faces looked up where they are
`_Builder._pick` finds each expected item at its place instead of reading the whole body:
- line: `findBRepUsingPoint` at the midpoint of its expected ends; arc: at its expected start point (the edges meeting
  there); face: at the middle of its expected bounding box with `BRepFaceEntityType`.
- Candidates are those of the body (`candidate.body == body`), turned into the item form with today's `_edgeItem` /
  `_faceItem` and matched with today's `predBoxEdges.matchItems`, so the same signature picks the same edge.
- An item not found that way: the step falls back to today's walk over all edges/faces for that step, and the
  fallback is logged (`debugLog`), so no step fails where it passes today.
- `floorGrid`'s blend edges (`_isVerticalAt`, a walk over the base's edges) go the same way: a point midway up each
  expected vertical edge.
- The small parts' own walks (latch, hinge, handle, pin) read bodies of a few hundred edges, under 1 s in all; left as
  they are.

### Kept as is
Order and kind of the features, their parameters, sketches and shapes, the timeline group, the joints.

## Expected
Box 1 about 114 → 80 s, box 2 about 248 → 165 s (A ~15/30 s, B ~5/25 s, C ~11/16 s); the rebuild and the second box
gain through the 140 fewer parameters per box as well. Measured, not promised: the numbers go into the plan and the PR.

## Not part of this round
- The small parts (`insertParts`, 42–63 s): their sketches are plain numbers already (round 39); a further cut would
  need a different way of making them (no history, copies), a decision of its own.
- `Sketches.add` itself (46 predSketch sketches, 17 s in box 2) and the extrudes: the box's shape needs them.
- `isComputeDeferred` on the remaining predSketch sketches: not measured whether it helps or costs; open point.
- Bin, baseplate and label joint origins without sketches (A for the other generators): new point.

## Tests
- pytest: `createOffsetJointOrigins` (offsets from the dims, expression/number, signed, names; stand-ins), boxBuilder
  and predHandlePin call it and no longer `createPointJointOrigins` (source checks as today), `Dim` linear form and
  `dependsOnParameters` (sums, differences that cancel, min/max/abs parts that cancel only when identical, scaling,
  products of two parameters), `WorldSketch._apply` skips `applyTo` for a constant dim (source/flow check), `_pick`
  by point with fallback (stand-ins: found, not found → walk).
- Fusion (`r45_mess.py`, as `r39_mess.py`): base (794253f) and branch back to back in the same Fusion session: box 1,
  box 2, rebuild of box 1 as 6×4×6 with the two probe joints (p293), preview, width of box 2 5 → 6, rebuild preview.
  Each faster on the branch, p293 green, parameter change healthy (+42 mm), every sketch of the set fully constrained,
  no fallback line from C in the log.
- Box snapshot cases green (geometry unchanged): box_5x4x6, box_5x4x6_params_7x5x10, box_6x5x7_params_4x3x6,
  box_5x4x6_lid_closed_params_4x3x8 (the parameter cases check that joint origins and dimensions follow).
- Click test (`dev-notes/klicktest-r45.md`): box from the dialog with parts, a bin from the bin dialog into a box cell,
  box rebuild with a user joint on a latch.
