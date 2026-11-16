# Runde 20 – Übergabe (Fix-Runde)

Stand 2026-11-16. Branch `runde-20` von `runde-14-18` (bd6098b), nicht gepusht, nicht gemergt. Auftrag der
Hauptsitzung nach dem Handtest per Desktop-Steuerung (Nutzer: „Ja, beheben“). Keine eigene Spec, der Plan steht hier.

Punkte:
- p220 „Einleger per Rechtsklick neu bauen: Dialog stürzt ab, wenn der Einleger in einer Tasche sitzt“
- p221 „Meldung nach „Load from file“ zeigt die Wandstärke zehnmal zu groß“

## Plan

1. **p220, Absicherung (TDD):** `lib/ui/selectionPrefill.prefillSelection(input, entity)`. Lehnt Fusion die Tasche ab,
   bleibt die Auswahl leer, der Dialog baut sich fertig auf und zeigt einen Hinweis.
   - Unit-Test `tests/test_selection_prefill.py`.
   - Schwester-Pfade: `addSelection` gibt es nur an dieser Stelle. Bin-Rebuild und Clone setzen keine Entities in
     Auswahlfelder.
2. **p220, Ursache:** Probe-Auftrag `r20_pocket_probe`. Er zeigt, welche Entity `insertPocket` liefert (Typ,
   assemblyContext, nativeObject, Sichtbarkeit) und ob Fusion sie auswählen lässt (`ui.activeSelections.add`), auch in
   Varianten (native, Proxy über die Bin-Occurrence). Danach wird die Ursache gezielt behoben, mit Test, soweit es ohne
   Fusion geht.
3. **p221:** Der reine Lesepfad (`configJson.readConfig` und `notesText`) zeigt eine fehlende Wandstärke von 0,12 cm
   richtig als „1.2 mm“ (lokal nachgestellt). Die „12 mm“ entstehen also mit einem anderen aktuellen Wert oder einer
   anderen Datei. Ursache klären, dann Test (rot) und Fix; alle Längenfelder und den Label-Dialog mitprüfen.
4. Review (Opus), pytest, Snapshot-Lauf über die Hauptsitzung, Übergabe.

## Befunde

**p220: Ursache belegt** (`r20_pocket_probe`).
- Die Seiten des gespeicherten Joints und damit `insertPocket` liefern den Joint Origin der Tasche ohne
  Baugruppen-Bezug (`assemblyContext` None). `ui.activeSelections.add` lehnt ihn ab: „3 : invalid argument entity“.
- Der Proxy über die Bin-Occurrence (`createForAssemblyContext`) lässt sich auswählen.
- Fix: `labelBuilder._inRoot` gibt die Tasche als Proxy über die Occurrence ihrer Komponente zurück.
- Nebenwirkung, gewollt: `_isAfter` (Tasche einer später gebauten Bin, Review Runde 18) las `assemblyContext` und war
  mit dem Joint Origin ohne Bezug immer falsch. Jetzt greift die Prüfung.
- Die Absicherung `selectionPrefill` bleibt als Netz.

**p221: Nicht nachgestellt.**
- Der Weg „Wand 1,2 mm im Dialog (0,12 cm im Zustand), dann die Datei aus Handtest 10 laden“ ergibt „wallThickness
  (1.2 mm)“. Das gilt in pytest (`test_hand_test_10_file_keeps_lengths_in_mm_in_the_note`, alle Längenfelder in mm) und
  in Fusion (`r20_wall_probe`: Rohzustand 0,12, Meldung 1.2 mm).
- Im Code schreibt nichts einen mm-Wert in den Zustand der Wandstärke.
- Mögliche Erklärung: Im Dialog stand vor dem Laden tatsächlich 12 mm, etwa nach dem Laden einer anderen Datei oder
  einer Eingabe in einem Dokument mit cm als Einheit. Die Meldung zeigt dann richtig den behaltenen Wert.
- Die Testsitzung wiederholt Handtest 10 mit Bildschirmfoto. Bis dahin bleibt p221 offen, der Test bleibt als
  Absicherung.

## Review (Opus)

Kein kritischer Fund. Umgang:
- **(I1) behoben:** `insertPocket` nimmt die Occurrence aus dem Joint selbst (`occurrenceOne`/`occurrenceTwo`). Sonst
  bekäme bei einer in Fusion kopierten Bin, also einer zweiten Occurrence derselben Komponente, die erste Bin den
  Einleger. `_inRoot` bleibt nur der Rückfall. E2E c prüft das.
- **(I2) offen bis Dialogtest:** Belegt ist das Auswählen per `ui.activeSelections.add`, nicht `addSelection` im
  Dialog. Den echten Pfad prüft die Sitzung gf-dialogtests (Handtest 16): Tasche vorgewählt, kein Hinweis.
- **(I3) Fusion-Lauf:** `_isAfter` greift erst jetzt. E2E a prüft den normalen Neubau, E2E b die Ablehnung der Tasche
  einer später gebauten Bin. Dazu läuft `r20_e2e_r18a`, das ist E2E a aus Runde 18.
- Klein:
  - (M1) Der Hinweis verschwindet, sobald eine Tasche gewählt ist.
  - (M2) `_inRoot` ähnelt `lib/ui/selection._inRootContext` für Körper; das Zusammenlegen bleibt für später.
  - (M3) `prefillSelection` fängt alle Ausnahmen ab und schreibt sie ins Log. So gewollt als Netz.
