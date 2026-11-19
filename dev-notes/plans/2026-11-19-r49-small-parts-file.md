# Plan round 49: the box's small parts on disk (p610)

Spec: `dev-notes/specs/2026-11-19-r49-small-parts-file.md`. TDD, pytest in `tests/` (Fusion stubs).

1. **`lib/gridfinityUtils/predPartFile.py`, Fusion-free part** (tests `tests/test_pred_part_file.py` first):
   `codeStamp(folder)`, `fileStem(version, stamp, key)`, `PartFile(folder, version, stamp, io, log)` with
   `load(key)` / `save(key, kept)` / `cleanUp()`. The Fusion calls (`exportToFile`, `createFromFile`) come in through
   `io` (two functions), so every broken-file case runs in pytest with fakes. Atomic write: `.tmp` + `os.replace`,
   smt first, json last.
2. **`predPartCache.PartCache` gets an optional store** (tests in `tests/test_pred_part_cache.py` first): memory →
   `store.load` → `draw` + `store.save`; store errors are logged, never raised. `SESSION` gets the store of the running
   add-in lazily (folder from the add-in folder, version from the manifest, stamp of `lib/gridfinityUtils`), so a
   failing set-up of the store leaves the round-47 behaviour.
3. **Fusion `io`** in `predPartFile`: export via `TemporaryBRepManager.exportToFile(list, path)`, import via
   `createFromFile(path)` → list of bodies. Source test (as `test_box_builder_bodies.py` does) that `predBoxInsert`
   still goes through `predPartCache.SESSION.bodies` unchanged.
4. **Add-in folder bits**: `.gitignore` `partCache`, `updateInstall.CARRY_OVER_SKIPPED_FOLDERS` + `partCache` (test in
   the carry-over tests first).
5. **Fusion run** (own slot, one script `fusion-auftraege/r49_snap.py`, one case per call with a state file, code from
   wt-r49, `partCache` of the worktree): `box_5x4x6`, `box_4x3x6_magnets_custom` drawn → files → session cleared → read;
   timing of the parts in `insertParts` both ways and a second box. Log `r49_snap.log`.
6. CHANGELOG `## Unreleased` / `### Small parts kept on disk (round 49)`, `dev-notes/klicktest-r49.md`, docstrings
   (round 47 headers mention the file way).
7. Opus review subagent, findings fixed; push, PR (text to the main session first), CI green; "Klicktest R49 bereit".
