# Plan round 55 – one Bambu Studio project with all plates (p680)

Spec: `dev-notes/specs/2026-11-23-r55-bambu-project-3mf.md`. Branch `claude/r55-multi-plate-3mf-94ad04` from master
`1dcb49a`. Test command: `python -m pytest`. Credits: upstream `1ac1579` (Le0Michine).

## Task 1 – printer list to `lib/printBeds.py`, Bambu entries apart
- [ ] Tests `tests/test_print_beds.py` load `lib/printBeds.py`: each Bambu printer of the spec's table is its own entry
  with its bed; purge anchors and excluded areas per printer (P1P, P1S, X1, X1 Carbon, X1E keep `(0, 0, 18, 28)`);
  `PURGE_ANCHORS` (upstream name). `tests/test_export_parts.py`: the old grouped labels open as X1 Carbon, P2S,
  H2D; `DEFAULT_BED` is X1 Carbon. RED: file missing, old names.
- [ ] `git mv commands/commandCreateBaseplate/printBeds.py lib/printBeds.py`, split the entries, rename
  `BAMBU_PURGE_ANCHORS` → `PURGE_ANCHORS`, imports in both dialogs and `printLayout` comment, `OLD_BED_NAMES`,
  `DEFAULT_BED`. GREEN, full suite.

## Task 1a – last chosen printer
- [ ] Tests `tests/test_print_beds.py`: `writeLastPrinter`/`readLastPrinter` round trip in `tmp_path`, missing or
  unreadable file → None, an old grouped label → its printer, an unknown label → None. `tests/test_export_parts.py`:
  `layoutChoices` with a last printer takes it over the saved `bed`, Custom keeps the saved size, none → saved bed →
  X1 Carbon. RED.
- [ ] Implement in `lib/printBeds.py` and `lib/exportParts.layoutChoices(section, bedNames, lastPrinter=None)`.
- [ ] Source tests: export `saveChoices` and baseplate `command_execute` call `writeLastPrinter`; the baseplate's
  `command_created` applies the last printer before a pending config. RED, then implement. GREEN, full suite.

## Task 2 – Bambu profile names
- [ ] Fixture `tests/fixtures/bambu_system_profiles.json`: the machine, process and filament profile names of Bambu
  Studio 02.09.01.70 (names only, from `%APPDATA%\BambuStudio\system\BBL`, plus the subfolders like `filament/P1P`).
- [ ] Tests: every Bambu entry of `PRINT_BED_SIZES` has `bambuProfiles(label)` with printer, process, filament
  names, each in the fixture; none for other printers and Custom; `isBambu(label)`. RED.
- [ ] `BAMBU_PROFILES` table and `bambuProfiles`, `isBambu` in `lib/printBeds.py`. GREEN, full suite.

## Task 3 – plate grid and plate list (upstream names)
- [ ] Tests in `tests/test_three_mf.py` from upstream `1ac1579`: `plateColumns` 1..10, `plateOrigin` for three
  plates of 256 mm (0,0 / 307.2,0 / 0,−307.2), `modelSettings` names, extruder 1, part with unit matrix, the
  objects of each plate. RED.
- [ ] `PLATE_GAP`, `MODEL_SETTINGS_PATH`, `plateColumns`, `plateOrigin`, `modelSettings` in `lib/threeMf.py`. GREEN.

## Task 4 – Bambu project file
- [ ] Tests: `projectSettings(profiles, colours)` has exactly the spec's keys, `filament_settings_id` one per colour,
  `curr_bed_type` `Textured PEI Plate`, version `02.09.01.70`; `bambuModelXml` has the Bambu `Application` and
  `3mfVersion`, each object around its middle with the shift in the build item's `transform`, `paint_color` kept;
  `writeBambuProject(path, objects, plates, bed, profiles, colours, title)` writes the model, model settings and
  project settings, each object on its plate's grid cell (laid out at 10, 20 on plate 1 of 2 → x ≥ 307.2). RED.
- [ ] Implement in `lib/threeMf.py`. GREEN, full suite.

## Task 5 – filament colours, files choice, notice text
- [ ] Tests `tests/test_export_parts.py`: `filamentColours({'#D02020': 2, '': 4})` → `['#808080', '#D02020',
  '#808080', '#000000']`; none → `['#808080']`; `layoutChoices` keeps `files` (`FILES_ONE` default, unknown →
  default); `bambuNotice(profiles, plates)` text for 3 plates and for 1 plate as in the spec. RED.
- [ ] Implement in `lib/exportParts.py`. GREEN, full suite.

## Task 6 – export dialog and export
- [ ] Source tests (style of the existing export tests, `ast`/text): `Files` dropdown `FILES_INPUT_ID` with
  `FILES_ONE`, `FILES_PER_PLATE`, visible only for 3MF and a Bambu printer; saved in `saveChoices`; `export3mf`
  writes `writeBambuProject` for a Bambu printer with `FILES_ONE`, the notice (`OKCancelButtonType`) after
  `mayReplace` and before writing, Cancel returns before any write or removal; plate files otherwise as today. RED.
- [ ] Implement in `commands/commandExport/entry.py`; message names the project and its plates. GREEN, full suite.

## Task 7 – sample files for the Bambu test
- [ ] `tests/e2e/bambu_project_samples.py` (run by hand, path argument): from unit-test style meshes, 3 plates P1S
  with bins and labels (text in two colours and one without), one plate A1 mini, one plate H2D. Write to
  `D:\Entwicklung\Gridfinity\_scratch\r55`. A test runs it into `tmp_path` and checks plates and settings.

## Task 8 – Fusion job (for the main session)
- [ ] `D:\Entwicklung\Gridfinity\fusion-auftraege\r55_export.py`, under 50 s: new document, a 2×1 bin with a colored
  label and a 1×1 bin, export via `export3mf` for X1 Carbon as project and as files per plate into
  `_scratch\r55\fusion`; checks zip contents; document closed without saving. The notice is in `command_execute`,
  checked in the click test.

## Task 9 – version, changelog, docs
- [ ] `Gridkeeper.manifest` 1.3.0, `CHANGELOG.md` entry 1.3.0 with credits (Le0Michine, `1ac1579`), 
  `docs/working/export.md` (project file, the notice, printers apart), `docs/getting-started/whats-new.md`.
  `mkdocs build --strict` if available.

## Task 10 – review
- [ ] Opus subagent review of the diff against spec and plan; findings checked, fixed, suite green.
