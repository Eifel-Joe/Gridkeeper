# Plan round 58: merge GridfinityGenerator up to fadbd128

Spec: `dev-notes/specs/2026-11-24-r58-upstream-merge.md`. Tests: `python -m pytest` (stubs in `tests/stubs`).
Scratch: `D:\Entwicklung\Gridfinity\_scratch\r58`. Fusion jobs: `D:\Entwicklung\Gridfinity\fusion-auftraege`, each
under ~50 s, through the main session.

## Task 1 — Merge commit

- [ ] `git merge --no-ff upstream/master`; resolve by the spec's table:
  - Ours: `commandExport/entry.py`, `threeMf.py`, `printBeds.py` (+ upstream's `presetLabelOf`), `test_print_beds.py`
    (+ its `presetLabelOf` test), `binBuilder.py` parameter path (D3), `baseGenerator.py` joint origins,
    `binBodyCutoutGenerator.py` scoop fillet, label layout in `labelGenerator.py`, all snapshot binaries.
  - Union: imports (`lengthInput`, `lipSharpTop` + Gridkeeper's), `sketchUtils` (both rectangle helpers),
    `commandCreateBin/entry.py` (inch row + Cullenect row; `keepActiveComponent` + `cell=`; `isFromTag` + label color),
    `rebuildUtils.rebuild` (namePrefix + jointsByName/hideByLightBulb), `baseplateBuilder` call, snapshot harness,
    `tests/e2e/README.md`, `tests/test_dim.py`.
  - Removed: `GridfinityGenerator.manifest`, `documentation/wiki/*`, `lib/bedPacking.py`, `tests/test_bed_packing.py`,
    `commands/commandExport/html/plates.html`.
  - `api.py`: without `bedPacking` and the export names. `release.yml`: Gridkeeper's line + `api.py`.
- [ ] RED expectation before resolving the rest: pytest collects; failures only in tests touching the merged points.
- [ ] GREEN: `python -m pytest` all green. Commit the merge (message names the upstream range and the decisions).

## Task 2 — Script module name (D2)

- [ ] RED: `tests/test_script_module.py` expects `MODULE_NAME == 'gridkeeper'`, marker `IS_GRIDKEEPER`, and that a
  module named `gridfinity` (upstream's) is never touched.
- [ ] GREEN: `lib/scriptModule.py`, `api.py` marker, register/unregister in `Gridkeeper.py`; `api.py` exposes box,
  box label and label insert builders. Commit.

## Task 3 — Names on rebuild for every generator (D4)

- [ ] RED: `tests/test_rebuild_names.py` cases for a box, box label and label insert prefix (user-given component,
  group, body names kept; generated names follow the new settings); a case for `retag` writing the generated names
  after a parameters-only rebuild; existing round-44 counter tests stay green.
- [ ] GREEN: `rebuildUtils` (one name mechanism, see D4), callers in box, box label, label builders, `binBuilder.retag`.
  Commit.

## Task 4 — Active component kept for box, box label, label insert (D9)

- [ ] RED: unit test that each of the three command entries builds inside `commonUtils.keepActiveComponent`
  (stub design records activations; the active component after the build is the one before).
- [ ] GREEN: wrap the builds. Commit.

## Task 5 — Lengths in mm in Gridkeeper's own code (D6)

- [ ] RED: `tests/test_length_inputs.py` scans `lib/gridfinityUtils/*.py` and the builders for `setByOffset`,
  fillet/chamfer inputs, shell thickness, joint origin offsets given `valueInput(`/`createByReal(`; lists every site.
- [ ] GREEN: convert the sites to `lengthInput`; label text heights via `lengthExpression(round(height, 4))`. Commit.

## Task 6 — Label text sketches (D8)

- [ ] RED (unit, stubs): Gridkeeper's text creation sets the height by expression and constrains the text box.
- [ ] GREEN. Commit. Fusion check in Task 8.

## Task 7 — Version, changelog, docs

- [ ] `Gridkeeper.manifest` 1.4.0; CHANGELOG 1.4.0 with "Merged from GridfinityGenerator by Le0Michine (Lev Mishin),
  up to fadbd128" and credits; header line 4 (merged up to fadbd128, round 58); `docs/getting-started/whats-new.md`;
  README "Scripting". pytest green. Commit.

## Task 8 — Fusion (through the main session)

- [ ] Job A: reload add-in from the worktree, run the two new cases and 3 bin, 1 baseplate, 1 box, 1 box label,
  1 label case (mm + inches) as a smoke test.
- [ ] Jobs B…: all 135 cases in batches under 50 s (case lists in the job files), mm + inches.
- [ ] Re-record cases changed by the lip move or a listed decision; list them with reason. Failures in inches of
  another pattern → new list points (p720–p729).
- [ ] Hand checks by script: rename + rebuild keeps names (bin, baseplate, box, label insert), active component kept,
  `import gridkeeper` works.

## Task 9 — Review and PR

- [ ] Opus review of the diff against spec and plan; findings through `receiving-code-review`.
- [ ] PR text to the main session; after release: push, PR to `master` of `Eifel-Joe/Gridkeeper`, CI green.
