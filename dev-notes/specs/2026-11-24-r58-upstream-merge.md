# Round 58: merge GridfinityGenerator up to fadbd128 (Gridkeeper 1.4.0)

Branch `claude/r58-upstream-merge-907dac` from `master` (6d4a15b3, release 1.3.2).
`git log master..upstream/master` = 21 commits (15 by Lev Mishin, 6 by Eifel-Joe merged upstream), 232 files.
Last merge: round 38, up to ee027a9 (v2.5.0.0), see `2026-11-18-r38-upstream-2-5.md`.

## Problem

GridfinityGenerator (Le0Michine) moved on since 19.11.2026: names kept on rebuild, bins built the same in documents in
inches, every snapshot case built in inches too, the lip's sharp top at 4.4 mm, scripts can import the add-in, export
from scripts, multi-plate 3MF. Gridkeeper takes them by `git merge upstream/master` (no rebase, no squash, authors
kept) and resolves the conflicts so every Gridkeeper function stays. Part of it: check whether Gridkeeper's own code
has the inch errors upstream fixed.

## Trial merge (24.11.2026)

82 conflicting files: 60 snapshot binaries / fingerprints, 3 deleted-by-us (`GridfinityGenerator.manifest`,
`documentation/wiki/*.md`), 19 source/test/doc files. Conflict hunks per source file: `commandExport/entry.py` 24,
`commandSnapshotTests/entry.py` 6, `printBeds.py` 5, `binBuilder.py` 4, `commandCreateBin/entry.py` 4,
`labelGenerator.py` 3, `rebuildUtils.py` 3, 1–2 each in `baseGenerator.py`, `binBodyCutoutGenerator.py`,
`binBodyGenerator.py`, `binBodyLipGenerator.py`, `sketchUtils.py`, `baseplateBuilder.py`, `threeMf.py`, `README.md`,
`release.yml`, `tests/e2e/README.md`, `tests/test_dim.py`, `tests/test_print_beds.py`.

## The 21 commits and what is taken

| Commit | Content | Decision |
|---|---|---|
| 9552f792 | joint origins follow a base width change (submitted from Gridkeeper) | Gridkeeper has it since round 46 (`jointOriginLayout.createOffsetJointOrigins`): keep ours, offsets given with `lengthInput` (D6) |
| ae70993a | trim sketch frames fully constrained (submitted from Gridkeeper) | already in Gridkeeper; keep ours where it conflicts |
| 6e89bc44 | every snapshot case also built in inches; underdefined sketch fails a case | **taken**, merged with Gridkeeper's snapshot harness (D7) |
| 9fff0153 | lengths Fusion keeps as parameters given in mm (`lengthInput`), case `bin_1x4x2_plain` | **taken**; same fix applied to Gridkeeper's own code (D6) |
| c5a4bfe3 | label text sketches fully constrained, `createRectangle` → `constrainRectangle` | **taken** in `sketchUtils` beside Gridkeeper's `createCenteredRectangle`; Gridkeeper's own label layout stays (D8) |
| 7a551eb4 | close the document of a case whose build fails (submitted from Gridkeeper) | taken |
| 1d7c65da, 5d30bfa3 | keep the names of a rebuilt bin/baseplate: generated names in the tag, user-given names restored | **taken**, combined with Gridkeeper's rebuild (D4) |
| 25509a2a, 77aaecf4 (wiki part) | contribution guide wiki | not taken, the wiki stays deleted in the fork (as in rounds 22/38) |
| 77aaecf4 | rebuild a bin every time, the parameters-only path scrapped | **taken** (D3) |
| 9797d4fc | rebuild/clone from an older tag with the settings it was built with (`ADDED_FIELDS`) | **taken**, merged with Gridkeeper's `OLDER_VALUES` (round 32) |
| 54522054 | actual dimensions also in inches in an inch document | **taken**, Gridkeeper's Cullenect sockets row stays below |
| 73e35fce | bin one unit high with a scoop (submitted from Gridkeeper) | Gridkeeper's cutout already limits the floor fillet beside a scoop (`scoopSides.scoopFloorRadius`): keep ours; the new case `bin_1x1x1_scoop` is taken and recorded with Gridkeeper |
| a45c6b4e | activate the component active before a build (submitted from Gridkeeper) | **taken** for bin and baseplate, and the same for box, box label and label insert (D9) |
| 1ac1579c | multi-plate 3MF (`bedPacking`, plates palette) | **not taken** again: Gridkeeper 1.3.0 rebuilt it with its own layout and the Bambu Studio project, credits stand in 1.3.0 (D1) |
| 15ce40a4 | scripts import the add-in (`api.py`, `lib/scriptModule.py`) | **taken**, see D2 for the module name |
| b83b694b | export from scripts without dialogs (`exportBodies`) | **not taken** in this round, built on upstream's export (D1) |
| faf27457, a621eae8 | lip's sharp top on a round height, 4.4 mm at the default clearance; upstream snapshots | **taken** (code); snapshots recorded with Gridkeeper (D5) |
| 357d3053 | version bump of GridfinityGenerator's manifest | not taken, Gridkeeper counts its own versions (1.4.0) |
| fadbd128 | first case needing a look shown at the end; label sketches pass when only their text is "not constrained" | **taken** |

## Decisions (proposals for the main session)

**D1 Export.** `commandExport/entry.py`, `lib/threeMf.py`, `lib/printBeds.py` and `tests/test_print_beds.py` keep
Gridkeeper's side in every hunk; upstream-only additions that don't hang on its export are kept if harmless
(`printBeds.presetLabelOf` is taken with its test, it's pure). `lib/bedPacking.py`, `tests/test_bed_packing.py` and
`commands/commandExport/html/plates.html` are removed in the merge commit (nothing in Gridkeeper uses them, decided in
1.3.0). Export from scripts on top of Gridkeeper's export (Bambu project, label filaments, the notice before saving)
is its own piece of work: a new list point, not this round.

**D2 Script module.** `api.py` and `lib/scriptModule.py` are taken, registered in `Gridkeeper.py`'s `run`/`stop`,
`api.py` added to the release ZIP. `api.py` drops `bedPacking` and the `exportBodies…` names (D1) and adds the
Gridkeeper builders (box, box label, label insert). **Module name: `gridkeeper`** (marker `IS_GRIDKEEPER`), not
`gridfinity`: both add-ins may be installed, a script then knows which one it gets, and neither replaces the other's
module. Alternative: keep `gridfinity` (smaller diff to upstream, but Gridkeeper would take over upstream's name
whenever both run).

**D3 Bins are always rebuilt (approved change).** Decision: as in GridfinityGenerator, a bin changed in the bin
dialog is always built again in its place, also when only settings that are its parameters changed. One way to build
a bin is simpler to keep right than two; the parameters-only path had grown special cases (label refit, cells,
Cullenect sockets, creases, colored text). Removed with it: `binBuilder.parameterEdits`, `isSameSetting`, `retag`,
`binCell.parameterEditKeepsPlacement`, `cullenect.parameterEditKeepsSockets`, `labelColors.textEditByParameter`,
`binLabelLayout.textChangedSinceBuild` and their tests (none is used elsewhere; `configWithParameters` stays, the
settings window and the other rebuilds use it). What the full rebuild already does stays covered by tests: label
fitted anew, bin kept in its cell and its joint, Cullenect sockets fitted. Changing the bin's parameters directly in
Fusion (*Change Parameters*) is unchanged. Consequence: features made after the bin may lose their references when it
is rebuilt from the dialog, as with any rebuild.

**D4 Names on rebuild.** Upstream's `generatedNames`/`keepName` (component, timeline group, bodies) is taken and
combined with Gridkeeper's rebuild (joints by name, light-bulb hiding, joint and component counters of round 44).
Where upstream's name restore and Gridkeeper's `dropComponentCounters` do the same, one of them stays (whichever the
unit tests show covers both cases). Box, box label and label insert rebuild through `rebuildUtils.rebuild` too: they
pass their own name prefix and keep user-given names the same way (sister paths). (The parameters-only path is gone,
D3, so no retag is needed.)

**D5 Lip 4.4 mm.** Taken as is. Every bin with a lip moves 0.0036 mm at the default clearance; snapshots that change
are recorded again with Gridkeeper's code (not upstream's binaries, our bins differ). Gridkeeper code using the lip
height goes through `lipHeight` (raised dividers, label tab), no own constant to change; `binBodyGenerator.py:613`
uses `BIN_LIP_EXTRA_HEIGHT` for the trimmed top (3.8 mm), unchanged by upstream.

**D6 Inches in Gridkeeper's own code.** Upstream gives fillets, chamfers, plane offsets, shell thicknesses, joint
origin offsets and text heights to Fusion as mm expressions (`dim.lengthInput`, `lengthExpression`). Gridkeeper's own
generators still pass reals at such sites (box, latch, hinge, handle pin, box label, Cullenect socket and label,
wall crease, raised dividers, joint origin layout, label text heights). They are converted the same way, as a sister
fix of the same pattern, guarded by a unit test that finds feature-parameter sites still given a real. The check
itself: every snapshot case built in inches (D7); a case failing there for another reason than this pattern becomes a
new list point.

**D6, result (Fusion run).** Bins, baseplates and label inserts build the same in inches as in mm. Boxes don't:
in inches box and lid have 12 small vertical round faces split in two halves each, at six places near the front and
right edge, bottom and top, with the same shape. Giving the box's extrudes, start offsets, symmetric extents and the
spacing of its cell pattern to Fusion in mm (same pattern as D6) did not change that; it stays, as D6 applied to the
box's own lengths, its build in mm and all its snapshots are unchanged by it. Finding the feature that cuts these
circles is a list point of its own.

**D7 Snapshot harness.** Upstream's inch build, closing failed documents and the "first case that needs a look" are
merged into Gridkeeper's harness (box/label cases, text components, parameter cases); the inch build goes through the
same case build as the mm one. Upstream's underdefined-sketch check is not taken: Gridkeeper's own
(`constraints.unconstrainedSketches`, live text included) checks the same. The run takes about twice as long.

**D8 Label sketches.** Gridkeeper's label layout (`binLabelLayout`, text styles, symbols) stays. From upstream it takes
the text height as a mm expression. `constrainTextBox` isn't needed: Gridkeeper's texts run along a fixed baseline,
the multi-line text boxes are only measuring probes and deleted (it stays in `sketchUtils` as upstream has it).

**D9 Active component.** `commonUtils.keepActiveComponent` wraps the build in the bin and baseplate commands (upstream)
and in box, box label and label insert (same `occurrence.activate()` in their builders).

**Files.** `GridfinityGenerator.manifest` and `documentation/wiki/*` stay deleted. README: Gridkeeper's, plus a short
"Scripting" section. Version 1.4.0 in `Gridkeeper.manifest`.

## Not part of this round

- Export from scripts on Gridkeeper's export (D1) — new list point.
- Upstream's `bedPacking` and plates palette.
- Any change of Gridkeeper's export or label layout beyond the merge points above.
- Upstream wiki, FUNDING, version number.

## End-to-end criterion

- pytest green.
- In Fusion: every snapshot case (133 + 2 new) green in mm and in inches, recorded snapshots changed only where the lip
  move or a listed decision explains it (list in the PR); no underdefined sketch.
- Inch check: result per generator (bin, baseplate, box, box label, label insert) in the PR; open failures as new
  list points.
- A rebuilt bin, baseplate, box and label insert keep a component/group/body name the user gave; a renamed part of a
  box (lid, latch) keeps its name too.
- After building any part, the component active before is active again.
- A Fusion script `import gridkeeper; gridkeeper.version()` returns 1.4.0 while the add-in runs.
