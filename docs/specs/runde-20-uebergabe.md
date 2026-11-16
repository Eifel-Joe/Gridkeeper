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
