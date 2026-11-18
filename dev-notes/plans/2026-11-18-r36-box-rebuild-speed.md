# Plan round 36 (p293, p295; p296 after measuring)

Spec: dev-notes/specs/2026-11-18-r36-box-rebuild-speed.md. Tests: `python -m pytest`.

## Task 1: seat from a joint origin name (p293)
- [ ] Test `tests/test_pred_box_parts.py`: `seatOfJointOriginName('Latch front left joint origin') == 'Latch front left'`,
  every seat of `SEAT_NAMES` round-trips, `'Lid joint origin'`, `'Label joint origin'`, `'Latch joint origin'` give `None`.
  RED: no such function.
- [ ] `predBoxParts.seatOfJointOriginName`. GREEN.

## Task 2: seat per part occurrence from the set's joints (p293)
- [ ] Test `tests/test_box_rebuild_seats.py` (stand-ins, function loaded from rebuildUtils source like
  test_bin_cell_rebuild): `seatsByOccurrence(joints)` maps the occurrence on the other side of a seat joint origin to the
  seat, either side order, falls back to the other joint origin's assemblyContext when the joint has no occurrence,
  ignores joints without a seat joint origin. RED: missing.
- [ ] `rebuildUtils.seatsByOccurrence`. GREEN.

## Task 3: keys with the seat (p293)
- [ ] Tests in the same file: `newJointOriginKeys(newPart, seats)` gives four distinct latch keys
  `('Latch', '<seat>', 'Latch joint origin')` for four occurrences of one component, box/lid keep seat `''`;
  `oldJointOriginKey(jointOrigin, oldComponents..., seats)` gives the same key for the old latch at the same seat; the
  joint on old "Latch front left" picks the new occurrence at "Latch front left", not the last one.
  RED: missing.
- [ ] Extract the key building of `repointJointsByName` into these two functions, keyed (place, seat, name). GREEN.
- [ ] Source test: `repointJointsByName` uses `seatsByOccurrence`, `newJointOriginKeys`, `oldJointOriginKey`.

## Task 4: preview without small parts (p295)
- [ ] Test `tests/test_box_builder_bodies.py`: `_buildBox` takes `withParts`, `insertParts` only under
  `withParts`; `buildBox` passes `mayChangeDocument` as `withParts`; the seat joint origins stay unconditional
  (besides the component guard). RED.
- [ ] Implement; the preview checkbox tooltip says the preview shows box and lid without the small parts. GREEN.

## Task 5: CHANGELOG, click-test checklist
- [ ] `CHANGELOG-CULLENECT.md` under `## Unreleased`, group `### Box rebuild and preview (round 36)`.
- [ ] `dev-notes/klicktest-r36.md`.

## Task 6: Fusion evidence (slot from the main session)
- [ ] p293 end-to-end script: build box, user joint onto "Latch front left" and "Handle pin right", rebuild 6x4x6,
  joints on the occurrences at those seats, healthy.
- [ ] Measurement r36_mess.py before (master code) and after; p296 plan section with the numbers.

## p296: measured (Fusion run round 36, base 446df79)

Seconds; a 5×4×6 box with all parts, the document's size grows from row to row.

| Run | Total | Box+lid (createPredBox) | Parts (insertParts) | Joint origins (6 calls) | Old group removed |
|---|---|---|---|---|---|
| Box 1, empty document | 150 | 75 | 52 | 20 | – |
| Box 2 beside it | 279 | 142 | 87 | 47 | – |
| Rebuild 6×4×6, no joint moved over | 570 | 250 | 137 | 100 | 41 |
| Rebuild 6×4×6, 2 joints moved over | 591 | 202 | 116 | 64 | 186 (one by one) |
| Preview, 2 sets in the document | 328 | 248 | 0 | 75 | – |

Where it goes (cProfile, Fusion calls): `Parameter.expression` 236 calls at 0.05 / 0.2 / 0.5 s each (it grows with the
document), `Sketches.add`, `ExtrudeFeatures.add`, `addDistanceDimension` (~900 calls), `isComputeDeferred`. A constant
~22 s per build: ~49 000 `BRepEdges.item`/`len` calls, the hinge's `_edges` walks every edge of the bodies once per
listed edge (127 items).

## Task 7: hinge edges walked once per call (p296)

- Test in `tests/test_pred_hinge.py`: stand-in bodies counting how often their `edges` is walked; `_edges` with
  many items walks each body once. RED: walked once per item.
- `predHinge._edges`: the bodies' edges into one list before the loop. GREEN, full suite.
- Sister paths: `predLatch.edges` and `predBoxGenerator._pick` already take `list(body.edges)` once per call.

## Task 8: preview without the set's joint origins (p296, deviates from the spec)

The spec kept the seat joint origins in the preview as cheap; measured, the six joint origin calls take 20–100 s and
75 s in the preview. The preview is thrown away, nothing joints to it. Only with the main session's yes: `_buildBox`
creates the cell, stack, seat and lid joint origins only `withParts` (rename to `forOk`), a test like Task 4's.
RED/GREEN as there. Checked first: nothing in the preview reads them (label placement, rebuild preview).

## Task 9: why the old group goes one by one (p296, look only)

With a joint moved over the old group is deleted item by item (186 s against 41 s). Read `removeOldGroup` and
`timelineRemoval.deleteOneByOne`, find whether the one-by-one path is still needed now that the joints are moved
before the removal; a change only with a test and the main session's yes, else a note in the list.

## Task 10: measure again

One Fusion job like `r36_mess` mode p293 (box 1, rebuild with the two probe joints, close) plus a preview, compare
with the table above; p293 must stay green. `Parameter.expression` stays as it is (Fusion recomputes the design on
each change; no cheap way found) – noted as an open point.

## Outcome (round 36)

- p293: green in Fusion at 5568bad and again at 5b34670 (two probe joints, front left latch and right handle pin,
  stay on the part at the same seat after a rebuild to 6×4×6, healthy).
- Task 9: no change. Deleting the group as a whole takes a moved joint along (Fusion 15.11.2026), item by item keeps
  it; deleteOneByOne already rolls back first.
- Task 10 (5b34670, an R37 document open alongside): box 1 200 s (before 192), rebuild 598 s (591), preview 191 s
  with no joint origins (before 328 s with 75 s of joint origins, in a document holding two sets). BRepEdges calls
  ~49 000 → ~34 000 a build; the remaining ~29 000 come from createPredBox itself, noted at p480. Build and rebuild
  aren't measurably faster; Fusion's recompute of a growing design dominates (p480).
