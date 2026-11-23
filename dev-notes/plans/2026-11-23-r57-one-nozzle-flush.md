# Plan Runde 57 (Version 1.3.2): Spülmengen für alle Bambu-Drucker

Spec: `dev-notes/specs/2026-11-23-r57-one-nozzle-flush.md`. Test: `python -m pytest`. Ein Commit je grünem Task.

## Task 1 – Spülmengen auch für einen Extruder (`lib/threeMf.py`)
- [ ] Test `tests/test_three_mf.py`: `test_one_extruder_gets_no_purging_volumes` ersetzen durch
  - `test_one_extruder_gets_a_block_of_purging_volumes`: P1S (107, Datensatz 0), Grau+Rot →
    Matrix `["0", grau→rot, rot→grau, "0"]` (Werte aus `flushVolume(…, 107, 0)`, als Zahlen festgeschrieben),
    `flush_volumes_vector` 4 × 140, `flush_multiplier` `["1"]`, `flush_multiplier_fast` `["1.2"]`,
    `filament_map` `["1","1"]`, `filament_map_mode` „Auto For Flush“, `not flushingMatrixError`.
  - `test_the_h3c_gets_one_block_with_its_data_set`: H3C (125.9, Datensatz 1), 4 Farben → 16 Werte, Grau→Schwarz
    = int(60·1,3)+125 = 203, `flush_multiplier` `["1"]`.
  - Schlüsselmenge bei einem und zwei Extrudern gleich.
- RED: Schlüssel fehlen (KeyError/assert).
- [ ] Umsetzung: Guard `extruders < 2` entfernen, Docstrings `flushSettings`/`projectSettings`/Kopfkommentar anpassen
  (Beleg `auto_pa_line_single.3mf`, `update_multi_material_filament_presets`).
- GREEN: Suite grün; betroffene Alt-Tests (`test_bambu_project_samples.py` „not in r55-p1s…“) gehen in Task 3 mit.

## Task 2 – Hinweisfenster (`lib/exportParts.py`)
- [ ] Test `tests/test_export_parts.py`: Satz zu Spülmengen/Re-calculate steht für jeden Bambu-Drucker
  (parametrisiert über `printBeds.BAMBU_PROFILES`); Düsen-Verteilungssatz nur bei `extruders > 1`;
  `test_the_notice_of_one_nozzle_has_no_purging_volumes` entfällt.
- RED: Satz fehlt bei P1S.
- [ ] Umsetzung: Text wie Spec Punkt 2.
- GREEN: Suite.

## Task 3 – E2E-Probenskript (`tests/e2e/bambu_project_samples.py`)
- [ ] Test `tests/test_bambu_project_samples.py`: P1S- und A1-mini-Probe haben einen Block, `flush_multiplier` `["1"]`,
  keine 0 außerhalb der Diagonale; Zusatzproben `r57-p1s-4colours.3mf`, `r57-a1mini-4colours.3mf`,
  `r57-h3c-4colours.3mf` (Grau, Rot, Blau, Schwarz, 2 Platten) in der Dateiliste.
- RED: Dateien fehlen.
- [ ] Umsetzung im Skript, Docstring.
- GREEN: Suite. Danach Proben nach `D:\Entwicklung\Gridfinity\_scratch\r57` schreiben und Matrizen notieren.

## Task 4 – Version und Doku
- [ ] `tests/test_gridkeeper_names.py` auf 1.3.2 (RED), `Gridkeeper.manifest` 1.3.2 (GREEN).
- [ ] CHANGELOG 1.3.2 (mit Credits), `docs/working/export.md` (Abschnitt „Purging volumes“), `whats-new.md`.
  Kein Klarname, keine Listennummern.

## Task 5 – Fusion-Auftrag
- [ ] `D:\Entwicklung\Gridfinity\fusion-auftraege\r57_export.py` nach `r56_export.py`: Export P1S als Projekt,
  prüft n² Werte, `flush_multiplier` 1 Eintrag, keine 0 außerhalb der Diagonale; unter ~50 s.

## Task 6 – Review, PR
- [ ] Review per Opus-Subagent (Diff + Spec/Plan), Funde prüfen.
- [ ] PR-Text der Hauptsitzung zeigen, nach Freigabe push + PR gegen `master`, CI.
