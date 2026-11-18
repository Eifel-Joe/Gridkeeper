# Plan Runde 32 – p280 ältere Bins mit alten Einstellungen

Spec: `dev-notes/specs/2026-11-18-r32-old-bin-defaults.md`. Tests: `python -m pytest` im Worktree.

- [ ] **Task 1 – Bin-Altwerte.** Test in `tests/test_config_json.py`: `withOlderValues(BIN, {"binWidth": 4})` enthält
  `isShellRounded False`, `hasDividersToTop False`, `labelColor ''`, `cullenectSocketOffset 0.3` (plus die Lippe);
  `read()` einer Config ohne die sechs Felder über einen Gegenteil-Dialogzustand ergibt die Altwerte, keins davon in
  `notes.missing`. Dazu ein Inventur-Test: jedes Feld der heutigen Bin-`InputState`, das in einer festen Feldliste des
  Stands 2fea2a1 fehlt, steht in `OLDER_VALUES` (fängt künftige Felder ab). Gleiches für Baseplate/Box/Einleger/Box-Schild
  mit ihrem ersten Stand. RED: fehlende Schlüssel. Umsetzung: Einträge in `configJson.OLDER_VALUES`. GREEN.
- [ ] **Task 2 – p151-Tests umstellen.** `test_old_bin_config_keeps_the_dialog_color` → alte Config mit Label ergibt
  Farbe `''` und Dialogwahl „None“, auch wenn der Dialog Rot hat. `test_derived_empty_color_would_reset_it` entfällt
  (deckt sich dann). Handtest-10-Test bleibt (seine Felder sind alte Felder).
- [ ] **Task 3 – abgeleiteter Baseplate-Wert.** Tests: `withOlderValues(BASEPLATE, {"xyClearance": 0.2})` →
  `plateEdgeClearance 0.2`; `xyClearance 0.5` → `0.25`; ohne `xyClearance` kein `plateEdgeClearance`; mit
  `plateClearance 0.6` (renamed) → `0.3`. RED. Umsetzung: Werte in `OLDER_VALUES` dürfen Funktionen der Settings sein,
  `withOlderValues` wertet sie aus; Grenzen 0,025/0,25 mm als Konstanten in `configJson` (Kommentar: Dialogbereich in
  `commandCreateBaseplate/entry.py`). GREEN.
- [ ] **Task 4 – Rebuild-Weg.** Bestehender Quelltest `test_rebuild_fills_the_older_values_into_a_tagged_config` deckt
  `configWithParameters`; ergänzen um `configChanges` (Rebuild-Log), falls es `withOlderValues` noch nicht nutzt
  (prüfen, sonst nachziehen – Schwester-Pfad).
- [ ] **Task 5 – CHANGELOG** unter `## Unreleased` / `### Round 32`, des Nutzers Satz zitiert. Klicktest-Checkliste
  `dev-notes/klicktest-r32.md` mit alter Testdatei `dev-notes/specs/testdateien/r32-alte-bin.json`.
- [ ] **Task 6 – Review** per Opus-Subagent, Funde erledigen, volle Suite.
- [ ] **Task 7 – PR-Text** an die Hauptsitzung, Klicktest melden, nach Grün push + PR, CI.
