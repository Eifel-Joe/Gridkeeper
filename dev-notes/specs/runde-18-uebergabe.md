# Runde 18 – Übergabe

Stand 2026-11-16. Branch `runde-18` (von `runde-14-18` 96815d7), nicht gepusht, nicht gemergt.
- Spec: `dev-notes/specs/2026-11-15-runde-18-design.md`, freigegeben.
- Plan: `dev-notes/plans/2026-11-15-runde-18.md` (626c893), von der Hauptsitzung freigegeben, mit diesen Antworten:
  - Einleger werden immer neu gebaut.
  - Die Tasche ist vorbelegt.
  - Die neue Komponente sitzt an der alten Stelle.

Punkte:
- p150 „Einleger per Rechtsklick neu bauen und Einstellungen speichern wie Bins“
- p151 „Alte gespeicherte Bin-Einstellungen setzen die Label-Farbe im Dialog auf None“

## Stand je Punkt

**p151 (eca3549): umgesetzt.**
- Ursache: `configJson.readConfig` behält fehlende Felder schon, die Bin übergab als aktuellen Wert aber ihre
  abgeleitete Label-Farbe. Die ist `''`, solange der Dialog gerade keine Lasche mit Label beschreibt.
- Jetzt geht die Farbwahl des Dialogs ein (`labelColors.configCurrentColor`).
- Andere abgeleitete Felder gibt es nicht: Einleger und Grundplatte nehmen die Werte direkt aus dem Dialog.
- Beleg: pytest `test_old_bin_config_keeps_the_dialog_color` und `test_derived_empty_color_would_reset_it` (der alte Weg
  ergibt „None“).

**p150 (8a5ce68): umgesetzt** über den Upstream-Mechanismus aus v2.4, nicht nachgebaut:
- Config im Tag;
- `rebuildUtils.findTarget`/`rebuild`/`configWithParameters`;
- Save, Load und Copy im Dialog;
- Rebuild und Clone in „Gridfinity settings“.
- Neu ist nur, was Einleger zusätzlich brauchen:
  - `labelBuilder.rebuildLabel` und `insertPocket`;
  - in `buildLabel` die Ecke, das Parameter-Präfix, die Transformation und die alte Stelle;
  - `labelConfig` für die Anzeigenamen;
  - im Dialog `applyInputsState`, `startRebuild` und `startWithConfig`.
- Beleg:
  - pytest `tests/test_label_config.py` (Config- und Dialog-Rundlauf über alle Schraubenteile und Hardware);
  - E2E a: Einleger in der Tasche neu gebaut – gleiche Stelle, ein Joint, ein Einleger, alte Gruppe weg;
  - E2E b: frei, 36 → 78 mm, gleiche linke untere Ecke;
  - E2E c: Config aus dem Tag, Dialog-Zustand wie beim Klonen.

## Belege

- pytest: `796 passed`.
- Fusion auf 4996e26 (nach `r18_reload2`): E2E a, b und c sind ALL OK; `r18_snap2` DONE, 83 Fälle, nicht grün `[]`.
- Fusion vorher (nach `r18_reload1`):
  - `r18_e2e_a` und `r18_e2e_b` sind ALL OK.
  - Snapshot-Lauf `r18_snap`: DONE, 83 Fälle, nicht grün `[]`.
- **Dialoge per Skript (Probe `r18_dialog_probe`):** Ein Skript kann keinen Dialog öffnen.
  - Ausgabe: „before: SelectCommand / opened: SelectCommand / after: SelectCommand“.
  - `execute()` kommt erst nach dem Skript dran, danach war auch kein Dialog offen.
  - Gruppe c füllt den Dialog-Zustand deshalb ohne Dialog, wie es beim Klonen geschieht: `readConfig` und
    `applyInputsState`, danach `getInputsState`, anschließend wird der Zustand zurückgesetzt.
  - Das Ende-zu-Ende-Kriterium „Alle drei Dialoge öffnen sich nach Add-in-Neustart“ steht deshalb auf der
    Handtest-Liste (Entscheidung der Hauptsitzung).

## Review (Opus)

Kein kritischer Fund. Umgang:
- **Wichtig, behoben:**
  - (I1) Neubau per Rechtsklick auf die Buchstaben: Die Tasche ging verloren. `insertComponent` geht jetzt vom
    Text-Bauteil zum Einleger.
  - (I2) Die Ecke hing an der Reihenfolge der Körper. Jetzt wird der Einleger-Körper ausgewählt (`_insertBody`).
  - (I3) Die Ecke wird direkt hinter der alten Gruppe gelesen, sonst würde eine spätere Bewegung doppelt wirken.
  - (I4) Ein Text nur in Zeile 2 kam doppelt zurück. Die Parameter heißen jetzt nach ihrer Zeile
    (`labelConfig.textLines`), mit Unit-Test.
  - (I5) Eine Tasche einer Bin, die erst nach dem Einleger in der Timeline steht, wird beim Neubau mit Meldung
    abgelehnt.
  - (I6) Vorbelegt wird nur der eigene Joint „… in pocket“ des Befehls auf eine Cullenect-Tasche.
  - Klein (M1): Der Dialog sagt jetzt „Rebuilding …“.
  - Klein (M3): Schraubenteile und Hardware sind Config-Auswahlen; was fehlt, wird gemeldet.
  - Klein (M4): unbenutzter Import entfernt.
  - Klein (M7): Startet kein Dialog, bleibt nichts für den nächsten liegen.
  - E2E: a startet vom Buchstaben, b prüft Zeile 2 allein. c ruft `labelEntry.readConfig` nur ohne Notizen auf, weil
    sonst eine messageBox das Skript anhalten würde.
- **Klein, bleibt:**
  - (M2) Ein von Hand geänderter Breitenparameter wird beim Neubau aus der Config neu gesetzt. Gewollt, die Breite folgt
    aus Einheiten, Basisbreite und Korrektur.
  - (M5) `labelConfig.settingsOfDialog` spiegelt `getInputsState` für den Test. Der Dialog selbst nutzt
    `applyInputsState`/`getInputsState`, beide sind über E2E c geprüft.
  - (M6) Der p151-Test prüft den Weg über `configJson.readConfig` mit der Dialogfarbe. Die Verdrahtung in
    `binEntry.readConfig` ist eine Zeile, Handtest 4.
  - Ein eigener, späterer Joint des Users auf den Einleger wird nicht übernommen (er bleibt ein späteres Feature und
    kann danach fehlerhaft sein, `newlyUnhealthy` meldet es).

## Parameternamen (Frage aus E2E b)

In `gfLabel2_text1` zählt nichts ab 0:
- `gfLabel2` ist das Präfix des zweiten Einlegers im Dokument. E2E b baut zwei Einleger, der erste ist `gfLabel1`.
- `text1`/`text2` nummerieren die Text-Parameter des Einlegers in Reihenfolge der nicht leeren Zeilen. Das gilt seit
  den Text-Parametern (`LABEL_TEXT_PARAMETERS`), die Namen stehen in Nutzerdokumenten und bleiben deshalb.
- Ein Einleger nur mit Zeile 2 hat also einen Parameter `…_text1` mit dem Label „Text line 2“. Das Label sagt die
  Zeile, und der Neubau richtet sich danach (`labelConfig.textLines`).
- Entscheidung (16.11.2026, über die Hauptsitzung): passt so, die Namen bleiben, wie sie sind.
- Bins benennen ihre Label-Parameter nach eigenem Schema (`gfBinN_…`) und sind davon nicht berührt.

## Testtermin

1. **Joint wird neu angelegt:** Ein Einleger in einer Tasche bekommt beim Neubau einen neuen Joint in dieselbe Tasche.
   Der alte geht mit der alten Timeline-Gruppe. Eigene Verweise auf den alten Joint gehen dabei verloren.
2. **Alte Einleger:** Einleger, die vor dieser Version gebaut wurden, haben keine Config im Tag. „Gridfinity settings“
   zeigt ihre Einstellungen, bietet aber weder Neubau noch Klonen an, wie bei alten Bins.

## Handtest-Liste

1. Fusion neu starten: Die Dialoge Bin, Baseplate und Label öffnen sich (Spec-Kriterium, per Skript nicht prüfbar).
2. Bin mit Cullenect-Lasche, Einleger mit Tasche bauen, Rechtsklick auf den Einleger, „Gridfinity rebuild“:
   - Der Dialog zeigt die Werte des Einlegers und die Tasche.
   - Mit anderem Text OK: Der neue Einleger sitzt in derselben Tasche, und es gibt einen Einleger.
3. Rechtsklick auf den Einleger, „Gridfinity settings“:
   - „Save to file“, dann im Label-Dialog „Load“: Die Werte sind gleich.
   - „Clone“ öffnet den Label-Dialog mit diesen Werten.
4. Bin-Dialog ohne Lasche, Label-Farbe Rot, eine alte Bin-Config ohne Label-Farbe laden: Die Farbwahl bleibt Rot.
