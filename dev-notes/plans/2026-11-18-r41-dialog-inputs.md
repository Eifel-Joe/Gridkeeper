# Plan Runde 41: Längenfelder formatieren (p291, zurückgenommen); p490 dokumentiert

Spec: `dev-notes/specs/2026-11-18-r41-dialog-inputs.md`. TDD, `python -m pytest` nach jedem Task, ein Commit je
grünem Task. p490: entschieden F, keine Code-Tasks, nur Doku-Satz in T5.

- [x] ~~zurückgenommen~~ **T1 normalizedExpression.** `tests/test_expression_format.py`: (`'2.9 mm'`, `'mm'`, `'2.90 mm'`) → `'2.90 mm'`;
  `'2.9'` → `'2.90 mm'`; `'.5'`/`'-1'`/`'+2.9 mm'`/`'2.9mm'` → formatiert (Dezimalpunkt; Komma bleibt, wie getippt); schon formatiert (`'2.90 mm'`) → `None`;
  Formel `'10 + 2'`, `'a*2'`, andere Einheit `'1 in'` bei `mm`, leer → `None`; `unitType` `''` oder `'deg'` → `None`.
  RED: Modul `lib/ui/expressionFormat.py` fehlt. GREEN: Regex + Vergleich.
- [x] ~~zurückgenommen~~ **T2 Custom Event: start/stop/request.** Stub `Application` um `registerCustomEvent`/`unregisterCustomEvent`/
  `fireCustomEvent` ergänzen (nur protokollieren). Tests: `request(input)` merkt vor und feuert einmal; Handler
  setzt `expression` auf `formatInternalValue(...)` nur bei Abweichung, überspringt ungültige (`isValid False`) und
  wirft nicht bei Fehlern (Log); `stop()` entfernt das Event und leert die Vormerkung. RED: Funktionen fehlen.
- [x] ~~zurückgenommen~~ **T3 Aufruf aus CommandUiState.** `tests/test_command_ui_state.py`: `onInputUpdate` mit Längen-`ValueCommandInput`
  ruft `expressionFormat.request`, mit `deg` und `''` nicht; Zustand unverändert (`value`). `commands/__init__.py`
  startet/stoppt `expressionFormat` (Quelltext-Test wie in `test_dialog_state_calls.py`).
- [x] ~~zurückgenommen~~ **T4 Export.** `command_input_changed` des Exports ruft `request` für Bett-Breite/-Länge, Abstand, Turmfläche
  (Quelltext-Test in `test_export_parts.py`). `test_modules_compile.py` grün.
- [x] **T5 Doku/CHANGELOG/Klicktest.** `CHANGELOG-CULLENECT.md` unter `## Unreleased` → `### Typed values in the dialogs (round 41)`;
  Klicktest-Checkliste (mit der Formatierung zurückgenommen). p490: Satz in `docs/help/faq.md` (Building) und CHANGELOG-Zeile.
- [ ] **T6 Review** (Opus-Subagent), Funde prüfen; Klicktest-Meldung an die Hauptsitzung; PR-Text an die
  Hauptsitzung, Push, PR gegen `master`, CI.

**Nach dem Klicktest:** T1–T4 umgesetzt, im Bin-Dialog formatierte die Änderung mitten im Tippen (Fusion feuert
`inputChanged` schon bei einer Tipp-Pause). Entscheidung: Formatierung weglassen; T1–T4, der Klicktest und die
`forceUIRefresh`-Änderung sind zurückgenommen. Im Diff bleiben FAQ-Satz und CHANGELOG zu p490 sowie Spec und Plan.

Keine Fusion-Skriptprüfung nötig: es entsteht keine Geometrie, das Verhalten ist nur im echten Dialog sichtbar
(Klicktest). Snapshot-Fälle unberührt (Werte ändern sich nicht).
