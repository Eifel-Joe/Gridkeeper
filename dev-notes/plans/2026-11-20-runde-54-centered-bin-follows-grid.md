# Plan round 54 – centered bin follows its base units (p670)

Spec: `dev-notes/specs/2026-11-20-runde-54-centered-bin-follows-grid.md`. Branch `r54-centered-bin-follows-grid`.
Test command: `python -m pytest` (full suite, 2254 passed on master 26814d2).

## Task 1 – `centeredPlacement` as Dims
- [ ] Test `tests/test_bin_centered_placement.py`: load `centeredPlacement` from `binBuilder.py` by `ast` (as
  `test_bin_cell_rebuild.py` does) with the real `Dim`. Cases: 2×1 at 42 mm, clearance 0.25 mm → values
  −4.175/−2.075 cm as today's numbers, expressions contain `gfBin1_baseWidth`/`gfBin1_baseLength`, kind EXPRESSION,
  `dependsOnParameters`; half grid 1.5×2.5; 40×50 mm units.
  RED: today's function takes `state` only and returns floats.
- [ ] Implement: `centeredPlacement(state, baseWidth: Dim, baseLength: Dim) -> tuple[Dim, Dim]`,
  `(Dim.length(2 * clearance) − baseWidth * binWidth) / 2`. GREEN, full suite.

## Task 2 – `moveBodies` takes Dims
- [ ] Test in `tests/test_placement_utils.py` (or new file if it can't load `moveBodies`): a `Dim` expression goes
  to `ValueInput.createByString`, a float to `createByReal` (stub records the calls). RED.
- [ ] Implement via `dim.valueInput`. GREEN, full suite.

## Task 3 – `_buildBin` uses one placement pair of Dims
- [ ] Source test (`tests/test_bin_in_cell_source.py` style): `_buildBin` computes the centered placement after the
  base unit parameters exist, passes the Dims to `moveBodies`, `footCenters`, the pocket joint origins and the label
  (`binBodyInput.binPlacement`); snapped/kept/cell stay `Dim.length` numbers; the `!= (0, 0)` checks look at values.
  Update the existing assertion `centeredPlacement(state) if source == 'center'`. RED.
- [ ] Implement: pick the source before generating as now (snap needs the free spot first), turn it into
  `placementDims` after the parameters are made; numeric `binPlacement` kept for comparisons and `findPlacement`.
  GREEN, full suite.

## Task 4 – colored label follows
- [ ] Test (source or stub): `labelGenerator.createLabel` takes Dims in `binPlacement`, `facePlacement` adds them as
  they are, the one-face check uses their values. RED.
- [ ] Implement in `labelGenerator.py` / `binBodyGenerator.py` type hints. GREEN, full suite.

## Task 5 – snapshot case and Fusion check
- [ ] Case `tests/e2e/cases/bin_2x1x3_centered_params_base_50x46.json` (centered, joint origins, `gfBin1_baseWidth`
  50, `gfBin1_baseLength` 46), README regenerated (`python3 tests/e2e/write_readme.py`).
- [ ] Fusion script `fusion-auftraege/r54_centered.py` (from the worktree, new document, closed without saving):
  centered 2×1×3 Cullenect + colored label, base 42→50 / 42→46 in the parameter table; bbox symmetric, foot joint
  origins ±25 mm, pocket and letters moved with the tab, sketches fully constrained. Snapshot run of the new case
  (recorded), `bin_2x1x3_centered_joint_origins`, `bin_1x1x3_params_base_40x50`. Fusion slot via main session.

## Task 6 – version 1.2.1, CHANGELOG, click test list
- [ ] `tests/test_gridkeeper_names.py` expects 1.2.1 (RED), manifest 1.2.1 (GREEN).
- [ ] `CHANGELOG.md`: `## 1.2.1 (2026-11-20)` with `### Centered bin follows its base units (round 54)`, old bins
  note, credits.
- [ ] `dev-notes/klicktest-r54.md`.

## Task 7 – review, PR
- [ ] Opus subagent review of the diff against spec and plan, findings handled.
- [ ] Name check (`git diff master | grep -iE 'j(ö|oe)rg'` empty), PR text to main session, push, PR, CI green.
