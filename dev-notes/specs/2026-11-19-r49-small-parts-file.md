# Round 49: the box's small parts kept on disk as well

Point: p610 (keep the box's small parts on disk as well). Box and small parts after Pred's parametric Gridfinity Storage
Box v1.1 (https://www.printables.com/model/543553, CC BY-NC, by Pred), drawn in code (rounds 27–29, 40), kept per Fusion
session since round 47 (`predPartCache`, `predPartCopies`, spec `2026-11-19-r47-box-small-parts.md`).

## Starting point

- Round 47: latch, handle pin and hinge (per variant) are drawn once per Fusion session into a scratch component of the
  first box's set and kept as temporary bodies; every set gets copies as one base feature. The first box after Fusion
  starts still draws them (measured in round 47: about 25–30 s of that box's build).
- Probe of round 47 (`fusion-auftraege/r47_cmdprobe.log`, way C): the latch exported as .smt
  (`TemporaryBRepManager.exportToFile`) and read back (`createFromFile`) in a box command's execute: 0.07 s there and
  back, same area.

## Decided before the spec

- Build it (19.11.2026). The parts are still drawn in code; the file is only a store the add-in writes and reads
  itself, so the rule "parts never by import of a part file, drawn in code" holds: no part file ships with the add-in.

## Requirement

1. **Where.** In the add-in's settings place, the one the dialog defaults (`commands/*/commandConfig`) and the update
   settings (`updateConfig`) use: a folder `partCache` in the add-in folder, beside `updateConfig`. Ignored by git like
   `updateConfig`. An update does not carry it over to the new version (`updateInstall.CARRY_OVER_SKIPPED_FOLDERS`): it
   is no setting of the user, the new version's key differs anyway. Nothing is written anywhere else (no %TEMP%, no
   other folder on C:).
2. **Key.** One pair of files per kept part and key of `predPartCache.cacheKey`:
   `<version>-<code>-<role>[-<hinge>].smt` with the bodies and `….json` with their names in order (an .smt keeps no
   body names; snapshots and export go by body names). `<version>` is the manifest version (`updateCheck.manifestVersion`),
   `<code>` the first 12 hex digits of a SHA-256 over every `.py` and `.json` file in `lib/gridfinityUtils` (relative
   path and content, sorted by path). So a code change without a version step, as in a git checkout, reads no stale
   file. The whole folder rather than the three generators' imports: it cannot miss a module the drawing uses (dim,
   predSketch, sketchUtils, predBoxEdges, …); the price is one redraw after any change there. Taken when
   `predPartCache` is loaded, together with the generators, so code checked out while Fusion runs is not keyed with
   the code that is loaded (review). Line endings are made LF before hashing (CRLF checkout vs. LF zip).
3. **Order of looking.** Memory of the session (as round 47) → file → drawing. A part drawn is written to the file
   right after it was drawn; a part read from the file is kept in memory as if drawn.
4. **Never fails the box.** A missing, unreadable or broken file (no json, json not a list of names, smt missing or not
   readable, a body count other than the names) is read as missing: the part is drawn and the file written anew. A
   failed write or clean-up is only logged (`commonUtils.fileLog`); the box is built either way. Writing goes to a
   temporary name and is renamed into place, the json last, so a half-written pair is never read as whole.
5. **Clean-up.** After a pair is written, every file right in `partCache` whose name does not start with the current
   `<version>-<code>-` is deleted (only files of the add-in's own kinds .smt, .json, .tmp; other files, subfolders and
   anything outside `partCache` stay). Temporaries of the current key stay: a second Fusion on the same add-in folder
   may be writing them. Two Fusions with different versions on one add-in folder delete each other's pairs; that only
   costs a redraw. Failures only logged.
6. **Same geometry.** A box from read parts gives the same snapshots as from drawn ones: the box snapshot cases pass
   both ways (see Checks).
7. Unchanged: everything round 47 keeps unchanged (components, base feature, names, joint origins, joints, rebuild,
   export, colour, handle drawn in the set, the fallback of round 47 requirement 4 when the copy fails).

## Checks

- pytest: key and file names, code stamp (changes with a file's content, not with the order of listing), the order of
  looking, every broken-file case of requirement 4 drawn anew and rewritten, write and clean-up failures do not fail,
  clean-up deletes only old files of the own kinds, carry-over skips `partCache`, `.gitignore` has it.
- Fusion (betroffene Fälle only): box snapshot cases `box_5x4x6` and `box_4x3x6_magnets_custom` once with an empty
  `partCache` (parts drawn, files written) and once with the session cache cleared and the files present (parts read):
  pass both ways; sketches fully constrained. Measured: first box after a fresh load of the add-in code with empty
  `partCache` vs. with files (the three parts' time in `insertParts`), and a second box in the same session.
- Click test in the dialog (`dev-notes/klicktest-r49.md`): first box after Fusion start fast, `partCache` holds the
  files, a broken file is redrawn.

## Expected

- First box of a Fusion session with files present: the three parts about 0.1–1 s each (read + copy) instead of
  25–30 s together; every later box as in round 47.
- First box ever (or after a code change): as today plus writing (< 0.1 s).

## Not part of this

The handle (drawn in each set with its width), bins, baseplates, labels.
