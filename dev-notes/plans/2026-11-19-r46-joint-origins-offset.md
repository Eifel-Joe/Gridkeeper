# Plan round 46: joint origins of bins, baseplates and inserts without a sketch each

Spec: `dev-notes/specs/2026-11-19-r46-joint-origins-offset.md`. Branch `r46-joint-origins-offset` from master fa10e31,
worktree `D:\Entwicklung\Gridfinity\wt-r46`. One commit per green task, messages in English.

## Task 1: tests first (red)
`tests/test_offset_joint_origins.py`:
- `test_cell_joint_origins_are_offset_ones`: `baseGenerator.createCellJointOrigins` with the round-45 stand-in component
  (no sketches, no planes) and two cells, one with a parameter-bound x: names `Foot joint origin 1-1`, `… 2-1`, offsets
  the centers, z `-BIN_BASE_HEIGHT`, the x an expression. (baseGenerator imported through the stubs as other tests do;
  if its imports are too heavy, a source check that its body is a `createOffsetJointOrigins(` call instead.)
- Replace `test_bins_baseplates_and_labels_keep_the_sketch_way` by `test_bins_baseplates_and_inserts_use_it`:
  `binBuilder._buildBin` and the label builder's build function call `createOffsetJointOrigins(`, none of the three
  builders calls `createPointJointOrigins(`.
- `test_the_sketch_way_is_gone`: no `def createPointJointOrigins` / `createPointJointOrigins(` in `lib` and `commands`.
- Module docstring updated (bins, baseplates and inserts now too).
Run `python -m pytest tests/test_offset_joint_origins.py` → the new ones red, the rest green.

## Task 2: switch over (green)
- `baseGenerator.createCellJointOrigins` → `jointOriginLayout.createOffsetJointOrigins(...)`, docstring.
- `binBuilder._buildBin`: pocket and cell placement joint origins → `createOffsetJointOrigins` (import from
  `jointOriginLayout`), comments "sketches which don't follow body moves" → offsets.
- `baseplateBuilder`: comment only.
- `labelBuilder`: insert joint origin → `createOffsetJointOrigins`.
- Remove `createPointJointOrigins`; one sentence of its history into `createOffsetJointOrigins`' docstring; fix docstring
  references in `jointOriginLayout` (header), `predBoxSeats` (two docstrings) that name it.
- `python -m pytest` whole suite green.

## Task 3: e2e helpers
`tests/e2e/runde13_assembly.py` (pocket floor, two places), `runde15_grid.py` (grid of joint origins), `runde31_cells.py`
(`world`) read `transform.translation` instead of `geometry.origin`. Not run as a whole (they are Fusion scripts); the
measurement in task 4 covers the same checks.

## Task 4: measurement in Fusion (slot from the main session)
- Base: `git archive fa10e31` into `D:\Entwicklung\Gridfinity\_scratch\r46\base`.
- `fusion-auftraege/r46_mess.py` after `r45_mess.py`: loads the add-in package from the run's repo under its own name,
  one step per call (< 50 s), state file `r46_mess.state`, log `r46_mess.log`, new hybrid document per run, closed
  without saving at the end. Runs `branch`, `base`, `migrate` (base builds, branch rebuilds).
  Steps: `plate` (baseplate 6×6 with joint origins), `bin` (2×1×3 Cullenect with pocket, into socket 2-2),
  `insert` (into the bin's pocket), `replate` (rebuild baseplate 6×6), `rebin` (rebuild bin, height 4),
  `reinsert` (rebuild insert), `param` (`gfBaseplate1_baseWidth` 42 → 50 mm), `close`.
  Per step: seconds, model parameter count of the design, sketches and construction planes in the generated component,
  joint origins and their places (socket 2-2, pocket, insert), joints healthy, bin still at socket 2-2 and insert on the
  pocket floor (by `jointOriginPlace` and bounding boxes), every sketch of the set fully constrained.
  Dry-checked against the code before the slot; the baseplate build of the base run may need its own call (~36 × 0.85 s).
- Evaluation into `_scratch/r46/messung.md` (a Sonnet subagent may tabulate), numbers into the spec and the PR.

## Task 5: snapshot cases (same slot or next)
`baseplate_2x2_light_params_base_40x50`, `bin_2x1x3_cullenect_params_base_40`,
`bin_1x1x3_cullenect_params_length_50_height_10`, `label_1u_screw_text` via the snapshot runner from the worktree.

## Task 6: CHANGELOG, click test, review, PR
- `CHANGELOG-CULLENECT.md` under `## Unreleased`: `### Faster joint origins for bins, baseplates and inserts` with the
  measured numbers.
- `dev-notes/klicktest-r46.md` (steps as in the spec), "Klicktest R46 bereit, Head …" to the main session.
- Review by an Opus subagent on `git diff master`, findings fixed.
- Privacy check `git diff master | grep -iE 'j(ö|oe)rg'` empty; push, PR text to the main session, PR into the fork's
  `master`, CI (`tests.yml`) green. No merge.
