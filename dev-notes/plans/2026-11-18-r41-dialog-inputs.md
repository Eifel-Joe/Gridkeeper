# Plan Runde 41: Längenfelder formatieren (p291); p490 nach Entscheidung

Spec: `dev-notes/specs/2026-11-18-r41-dialog-inputs.md`. TDD, `python -m pytest` nach jedem Task, ein Commit je
grünem Task. p490: nach Empfehlung F keine Code-Tasks (ggf. nur Doku-Satz in T5).

- [ ] **T1 normalizedExpression.** `tests/test_expression_format.py`: (`'2.9 mm'`, `'mm'`, `'2.90 mm'`) → `'2.90 mm'`;
  `'2.9'` → `'2.90 mm'`; `',5 mm'`/`'-1 mm'`/`'+3mm'` → formatiert; schon formatiert (`'2.90 mm'`) → `None`;
  Formel `'10 + 2'`, `'a*2'`, andere Einheit `'1 in'` bei `mm`, leer → `None`; `unitType` `''` oder `'deg'` → `None`.
  RED: Modul `lib/ui/expressionFormat.py` fehlt. GREEN: Regex + Vergleich.
- [ ] **T2 Custom Event: start/stop/request.** Stub `Application` um `registerCustomEvent`/`unregisterCustomEvent`/
  `fireCustomEvent` ergänzen (nur protokollieren). Tests: `request(input)` merkt vor und feuert einmal; Handler
  setzt `expression` auf `formatInternalValue(...)` nur bei Abweichung, überspringt ungültige (`isValid False`) und
  wirft nicht bei Fehlern (Log); `stop()` entfernt das Event und leert die Vormerkung. RED: Funktionen fehlen.
- [ ] **T3 Aufruf aus CommandUiState.** `tests/test_command_ui_state.py`: `onInputUpdate` mit Längen-`ValueCommandInput`
  ruft `expressionFormat.request`, mit `deg` und `''` nicht; Zustand unverändert (`value`). `commands/__init__.py`
  startet/stoppt `expressionFormat` (Quelltext-Test wie in `test_dialog_state_calls.py`).
- [ ] **T4 Export.** `command_input_changed` des Exports ruft `request` für Bett-Breite/-Länge, Abstand, Turmfläche
  (Quelltext-Test in `test_export_parts.py`). `test_modules_compile.py` grün.
- [ ] **T5 Doku/CHANGELOG/Klicktest.** `CHANGELOG-CULLENECT.md` unter `## Unreleased` → `### Dialog inputs (round 41)`;
  `dev-notes/klicktest-r41.md` (Spec-Kriterium, je Dialog ein Längenfeld). p490 je nach Entscheidung (Doku-Satz).
- [ ] **T6 Review** (Opus-Subagent), Funde prüfen; Klicktest-Meldung an die Hauptsitzung; PR-Text an die
  Hauptsitzung, Push, PR gegen `master`, CI.

Keine Fusion-Skriptprüfung nötig: es entsteht keine Geometrie, das Verhalten ist nur im echten Dialog sichtbar
(Klicktest). Snapshot-Fälle unberührt (Werte ändern sich nicht).
