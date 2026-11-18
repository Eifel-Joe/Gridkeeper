# Plan round 47: the box's small parts faster (p591), stale latch snapshots (p592)

Spec: `dev-notes/specs/2026-11-19-r47-box-small-parts.md`. Branch `r47-box-small-parts` from master fa10e31,
worktree `wt-r47`. TDD (pytest with the Fusion stand-ins in `tests/stubs`), each task its own commit.

## Task 1: the session cache, Fusion-free (`lib/gridfinityUtils/predPartCache.py`)
- `COPIED_ROLES = ('Latch', 'Handle pin', 'Hinge')`; `cacheKey(role, hinge)`: the hinge variant only for the hinge.
- `PartCache.bodies(key, draw)`: on the first call per key `draw()` gives `[(name, temporaryBody)]`, kept; every call
  returns the kept list. A failing `draw()` keeps nothing (next box tries again). `clear()`.
- One module-level instance; an add-in reload makes a new one.
- Tests first (`tests/test_pred_part_cache.py`): drawn once per key, the hinge variants apart, the other roles one key
  whatever the hinge, a failure keeps nothing, the handle is not a copied role.

## Task 2: joint origins apart from the drawing
- `predLatch.addJointOrigin(component)` (from `_Builder.jointOrigin`), `predHandlePin.addJointOrigin(component)` (the
  offset joint origin at `JOINT_ORIGIN`), the hinge keeps `predBoxInsert.addOriginJointOrigin`. `createLatch` and
  `createHandlePin` call them as before (behaviour unchanged).
- Tests first: source tests that both generators call the new function and that it makes the same joint origin as
  before (names, axis entities, angle / offsets), adapted from `test_pred_latch.py`, `test_pred_handle_pin.py`.

## Task 3: the parts as copies in `predBoxInsert.insertParts`
- Copied roles: `bodies = partCache.bodies(cacheKey(role, hinge), draw)` with `draw` = a scratch occurrence in the set
  component, `drawPart` into it, `[(body.name, TemporaryBRepManager.copy(body))]`, scratch occurrence deleted (also when
  drawing fails). Into the part's component: one base feature (`startEdit`, `bRepBodies.add(copy, base)` per body,
  `finishEdit`), the bodies named as kept; then the part's joint origin (Task 2).
- The handle: `drawPart` as today.
- Any failure on the copy way: what the scratch left is removed, the part drawn in its component as today,
  `commonUtils.fileLog` with the reason.
- Colour, single-body name, occurrences, joints as today (unchanged code after the bodies are there).
- Tests first: source tests in `test_box_builder_bodies.py` (copied roles go through the cache and a base feature,
  the handle through `drawPart`, the fallback draws in place and logs, the scratch occurrence is deleted in a
  `finally`), and a test with fakes for the base-feature insertion helper (names kept, one base feature).

## Task 4: measured in Fusion (`fusion-auftraege/r47_nach.py`, one step per call, state file, as `r45_mess.py`)
Steps, branch code in a new hybrid document: box 1, box 2 (part times as `r47_mess.py`), rebuild of box 1 as 6×4×6
with two user probe joints on a latch and a handle pin (p293: moved to the new set's parts), width of box 2 by
parameter 5 → 6 (handle follows, timeline healthy), every sketch of the sets fully constrained, part components hold
one base feature and their joint origin, area/volume of every part as before, close. Base numbers: `r47_mess.log`
(box 1, box 2) and round 45 (rebuild). Box in a second document of the same session: copies still valid.

## Task 5: snapshot cases (`fusion-auftraege/r47_snap.py`, one case per call)
The 12 box cases once with the branch. Expected: the six of p592 review on the latch's area only (3085.723822 against
3085.727768), the others pass. For the six: the latch's fingerprint entry and its `.smt` replaced by the built latch,
nothing else; then those six once more → pass.

## Task 6: CHANGELOG, click test, review, PR
- `CHANGELOG-CULLENECT.md` under `## Unreleased`, group `### Box small parts (round 47)`, numbers from Task 4.
- `dev-notes/klicktest-r47.md`: a box from the dialog (all parts present, coloured, jointed at their seats, part
  components with one base feature), a second box faster, a rebuild with a user joint on a latch, export of the parts.
- Opus review of the diff; findings fixed. PR text to the main session first, PR against master of the fork, CI green.
