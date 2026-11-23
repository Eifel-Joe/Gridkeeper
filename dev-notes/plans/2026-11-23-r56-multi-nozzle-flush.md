# Plan Runde 56 (p690): Spülmengen für Bambu-Drucker mit zwei Düsen

Spec: `dev-notes/specs/2026-11-23-r56-multi-nozzle-flush.md`. Tests: `python -m pytest`.

## Task 1: Profildaten der Düsen
- Fixture `tests/fixtures/bambu_system_profiles.json`: neuer Schlüssel `machine_extruders` je 0.4-Druckerprofil mit
  `nozzle_diameter` (Anzahl), `extruder_max_nozzle_count`, `handle_hotend_as_extruder`, `nozzle_volume` (Standard je
  Extruder); Quelle im `source`-Text (Bambu Studio 8e524a39, BBL 02.09.00.74).
- RED `tests/test_print_beds.py`: `BambuProfiles.nozzleVolumes`, `.hotends`, `.hotendAsExtruder` je Drucker gleich der
  Fixture; `len(nozzleVolumes)` gleich `machine_nozzles`.
- GREEN `lib/printBeds.py`: Felder mit Vorgaben (1 Extruder, 1 Hotend), Werte für alle Bambu-Drucker eintragen.

## Task 2: Farbformel
- RED `tests/test_three_mf.py`: `flushVolume(von, nach)` für Paare mit von Hand aus Bambus Formel gerechneten Werten
  (grau→rot 165, rot→grau 277, gleiche Farbe 60 Minimum, schwarz→weiß, weiß→schwarz).
- GREEN `lib/threeMf.py`: `flushVolume` nach `calc_flush_vol_rgb` mit Quellenangabe.

## Task 3: Spülmengen im Projekt
- RED: `projectSettings(profiles, colours)` hat für zwei Extruder `flush_volumes_matrix` (2·n² Texte, Diagonale 0,
  Block 2 mit `nozzle_volume` 145, höchstens 900), `flush_volumes_vector`, `flush_multiplier(_fast)`, `filament_map`,
  `filament_map_mode`; für einen Extruder keine dieser Schlüssel (wie 1.3.0). Prüfregel wie
  `is_flushing_matrix_error` im Test nachgebaut: keine Warnung.
- GREEN: `flushSettings(profiles, colours)`, in `projectSettings` eingefügt.

## Task 4: Ausnahme TWO_NOZZLES weg
- RED `tests/test_print_beds.py`: `isBambu` für alle Bambu-Drucker wahr; `TWO_NOZZLES` gibt es nicht mehr.
- GREEN: `TWO_NOZZLES` streichen, `isBambu` vereinfachen; Tests in `test_bambu_project_samples.py` anpassen.

## Task 5: Hinweisfenster
- RED `tests/test_export_parts.py`: `bambuNotice` nennt bei mehr als einem Extruder den Satz zu Spülmengen und
  Düsenverteilung, bei einem nicht.
- GREEN `lib/exportParts.py`.

## Task 6: H3C nach Bambu-Test
- Je nach Ergebnis: nichts, Spülmengen auch bei `hotendAsExtruder` (Test + Bedingung), oder Datei je Platte.

## Task 7: E2E-Proben
- `tests/e2e/bambu_project_samples.py`: H2D-Projekt mit 4 Farben dazu; `tests/test_bambu_project_samples.py` prüft
  Spülmengen darin.

## Task 8: Version und Doku
- Manifest 1.3.1, `CHANGELOG.md` (Credits wie Steckbrief, Bambu Studio AGPL als Quelle der Formel),
  `docs/working/export.md`, `docs/getting-started/whats-new.md`; Spec-Nachtrag mit Testergebnis.

## Task 9: Review (Opus), Funde, PR-Text an Hauptsitzung, push, PR, CI.
