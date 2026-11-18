# Plan round 48: more scoops

Spec: [2026-11-19-runde-48-more-scoops.md](../specs/2026-11-19-runde-48-more-scoops.md). TDD, one commit per green task.

Done before the addendum (bb98659): tasks 1–7. Task 0 dropped, the snapshot run checks the same on the real code.

- [x] **0. Fusion feasibility probe** (slot from the main session, one job ~30 s): a cutter box with two adjacent and
  four bottom edges filleted in one feature, then the vertical corner fillets with today's radii and margin, then the
  bottom fillet. Decides before any production code whether one fillet feature carries the corner blends; fallback
  if not: vertical corner fillets first, then the scoops.
- [x] **1. `scoopSides`** (new pure module `lib/gridfinityUtils/scoopSides.py`, `tests/test_scoop_sides.py`).
  RED: sides from the four flags, back dropped with tab, empty for shelled/solid/shaped. GREEN: implement.
- [x] **2. Settings**: `hasScoopBack/Left/Right` in `InputState`, `defaultSettings.BIN` (False),
  `configJson.OLDER_VALUES` (False). RED: `tests/test_config_json.py` field list and older-values check. GREEN.
- [x] **3. Creases**: `wallCreases.creaseLayout(..., scoopSides)` replaces `skipFront`, `isScoopSide(side, sides)`.
  RED: `tests/test_wall_creases.py` back/left/right left out. GREEN, `binBuilder.creaseLayout` passes the set.
- [x] **4. Generator inputs**: `scoopSides` on `BinBodyGeneratorInput` and `BinBodyCutoutGeneratorInput`
  (`hasScoop` removed), `binBuilder` fills it. RED: source test that no `hasScoop` is read in `lib/gridfinityUtils`
  (style of `test_shelled_tab_origin.py`). GREEN.
- [x] **5. Compartment bounds and lip chamfer** (`binBodyGenerator`): pure helpers `compartmentBounds(...)` and
  `chamferBoxBounds(...)` returning insets per side, unit tested with numbers; chamfer edge pick by position.
  Top clearance uses the bounds.
- [x] **6. Cavity cutter** (`binBodyCutoutGenerator`): side faces picked first, one scoop fillet, bottom fillet seed per
  the spec. Not unit testable (Fusion B-rep), checked by the snapshots.
- [x] **7. Dialog** (`entry.py`): three new checkboxes, label of the old one, enable logic (radius on any side, back
  off with tab). RED: dialog state test (`tests/test_dialog_state_calls.py` style) for the IDs and enable rule. GREEN.
- [ ] **7a. Pocket scoops** (`compartmentLayout`, `tests/test_compartment_layout.py`): RED for `scoops` in
  `pocket`, `_sanitized` (unknown names, wrong types, missing → `None`), `isCustomized`, `isUniform`, `describe`. GREEN.
- [ ] **7b. Per-compartment walls** (`scoopSides.compartmentScoopSides`, `outerScoopWalls`, `scoopRadiusLimits`
  pure; `tests/test_scoop_sides.py`): RED for inherit/own/tab lock, outer walls from compartments touching them,
  radius limit only for an axis with two scoops. GREEN.
- [ ] **7c. Generator per compartment**: `BinBodyCompartmentDefinition.scoopSides`, builder fills from pockets,
  generator uses `outerScoopWalls` for bounds/chamfer/creases and the per-compartment radius limit (`Dim.min`).
  Source tests as in task 4. GREEN.
- [ ] **7d. Editor**: `compartments.html` Scoops row, `binScoops` in the page data, merge/split keep the choice;
  `tests/test_compartment_layout.py`/page source tests for the row and the data key. GREEN.
- [ ] **7e. Opus review** of the whole change before any Fusion run.
- [ ] **8. Snapshot cases**: three new cases from the spec, README via `write_readme.py`. Fusion job (slot): record the
  four new ones (with `bin_3x1x3_scoops_per_compartment`), run the five existing scoop cases unchanged, sketches fully constrained.
- [ ] **9. Docs and CHANGELOG**: `docs/bins/compartments.md` (sides, tab rule), picture wishes to the main session;
  `CHANGELOG-CULLENECT.md` `## Unreleased` / `### More scoops` with the idea credited to teateatea (#140).
- [ ] **10. Review** (Opus subagent, diff + spec), fix findings, `dev-notes/klicktest-r48.md`, report "Klicktest 48
  bereit". After it passes: PR text to the main session, push, PR, CI green.
