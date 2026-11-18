# Plan Runde 37: Label-Farben auf eigene Filamente (p301)

Spec: `dev-notes/specs/2026-11-18-r37-export-filaments.md`. TDD, `python -m pytest` nach jedem Task, ein Commit je
grünem Task.

- [ ] **T1 threeMf je Dreieck ein Filament.** `tests/test_three_mf.py`: `painted={1: 2, 4: 3}` → Dreieck 1 Code `8`,
  Dreieck 4 `0C`, facets-JSON ebenso; leeres `painted` → kein Paint, kein `MmPaintingVersion`, kein facets-JSON.
  RED: `write` erwartet `filament`. GREEN: `painted: dict[int,int]`, `filament`-Parameter raus, Aufrufer anpassen.
- [ ] **T2 labelColors.colorOfAppearanceName.** `tests/test_label_colors.py`: `Gridfinity label D02020` → `#D02020`,
  Rückweg von `appearanceName`; fremde Namen → `''`. RED: Funktion fehlt.
- [ ] **T3 exportParts.assignFilaments / Zuordnung lesen und schreiben.** `tests/test_export_parts.py`: Auto 2, 3 …
  in Reihenfolge; gemerkte gewinnt, Auto überspringt deren Nummer; > 18 → 18; `parseLabelFilaments`/
  `formatLabelFilaments` inkl. kaputter Einträge, `none`, altes `colorIndex`; Merge behält fremde Farben;
  Anzeigenamen „Red text“, „#123456 text“, „Text without color“. RED: Funktionen fehlen.
- [ ] **T4 withMarkings mit Filament je Markierung.** `tests/test_export_parts.py`: Teil mit eigenen Buchstaben
  (Filament 4) + rote (2) + blaue (3) Markierung → `painted` passend; Markierung ohne Filament → unbemalt.
- [ ] **T5 Export-Befehl.** `entry.py`: `markingColor(item)` (Occurrence- dann Körper-Darstellung),
  `colorKeysOf(items)`, Gruppe „Label filaments“ mit Spinnern je Farbe, Neuaufbau in `updateInputs`, Werte im offenen
  Dialog behalten, `readChoices`/`saveChoices` mit `labelFilaments`, `partMesh`/`meshOf` mit Filament-Map,
  `paintNote` je Farbe. Quelltext-Tests wie bisher in `test_export_parts.py` (z. B. Turm nur bei Bemalung) anpassen.
  `test_modules_compile.py` grün.
- [ ] **T6 Fusion-Prüfung.** Auftrag `fusion-auftraege/r37_filaments.py`: neues Dokument, zwei Bins mit rotem und
  blauem Label über die Erzeuger, `export3mf` aus `wt-r37` in Temp-Ordner, 3MF lesen → zwei Codes, Körper unbemalt;
  `isFullyConstrained` der Skizzen; Dokument ohne Speichern schließen. Slot bei der Hauptsitzung.
- [ ] **T7 Doku/CHANGELOG/Klicktest.** Export-Seite der Doku, `CHANGELOG-CULLENECT.md` unter `## Unreleased`,
  `dev-notes/klicktest-r37.md`; Bildwünsche an die Hauptsitzung.
- [ ] **T8 Review** (Opus-Subagent), Funde prüfen, Push, PR-Text an die Hauptsitzung, PR, CI.
