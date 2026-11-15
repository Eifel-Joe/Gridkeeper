# Runde 13 – Übergabe

Stand 2026-11-15. Branch `runde-13` (von `master` b4577a1), nicht gepusht. Spec
`docs/specs/2026-11-15-runde-13-design.md` (von Jörg freigegeben), Plan `docs/plans/2026-11-15-runde-13.md`.
Punkte: p90 „Bin und Baseplate in einer Baugruppe als Komponente anlegen“, p160 „Einleger per Joint in seine
Cullenect-Tasche setzen“, p100 „Label-Befehl legt den Einleger am Nullpunkt mitten in die Bin“.

## Stand (belegt)

- pytest: 692 passed.
- Snapshot-Lauf in Fusion (alle 83 Fälle): 79 grün. Rot sind die 4 bekannten p30-Fälle, alle mit „built with other
  settings than the snapshot“: `bin_2x1x3_label_icon_text_embossed`, `bin_2x1x3_label_text_engraved`,
  `bin_2x3x5_features`, `bin_2x3x5_features_params_all`. Keine Snapshots neu abgelegt, die neue Strukturprüfung meldet
  nirgends etwas.
- `tests/e2e/runde13_assembly.py` in Fusion: ALL OK (18 Punkte), auch nach dem Review-Fix-Durchgang.
- Review (Opus): kein kritischer Fund. Wichtig 1 und 2 sowie das hochgestufte Minor 4 sind behoben (Commit bc5f853).
  Die übrigen Minors sind zurückgestellt, siehe unten.

## Offen

- Dialoge: Jörg hat Fusion am 15.11. neu gestartet und gemeldet: „Ja, alle drei öffnen“ (Bin, Baseplate, Label).
- **Nicht per API prüfbar:** Wandert ein eingesetzter Einleger mit, wenn Jörg die Bin von Hand verschiebt? Das gehört in
  den Handtest.
- Neuer Punkt in der Liste: p170 „Joint Origins an Bin-Füßen und Grundplatten-Aufnahmen folgen geänderten Rastermaßen
  nicht“ (Upstream-Fehler, Referenzmaße statt steuernder Maße).

## Zurückgestellte Review-Minors

- Rebuild liest `target.occurrence.transform2`, nicht das der nativen Occurrence. Das zählt nur, wenn Jörg eine
  Sammelkomponente löst und verschiebt.
- Gelöschte Tasche oder Joint Origin ohne Taschen-Markierung im Feld „Pocket“: Die Meldung lautet trotzdem
  „too small“.
- Die Text-Komponente eines Einlegers entsteht vorab. Ergeben Text und Symbol keine Profile, bleibt sie leer.
- Die Größe der Tasche im Attribut stammt aus dem Bau. Eine spätere Änderung der Basisbreite nur per Parameter lässt
  sie veraltet.
- Eine kopierte Sammelkomponente: Die erste mit der Markierung gewinnt.
- Ein fehlgeschlagener Bau per Skript in einem Hybrid-Dokument lässt eine leere Sammelkomponente zurück. Die Befehle
  nehmen das zurück.
- Ein eigener Joint auf einem Fuß-Joint-Origin verschwindet beim Rebuild der Bin, wie vor dieser Runde.

## Fallen

- Fusion bindet die erste Occurrence einer Komponente an ihre Eltern (`isGroundToParent`). Ohne festgesetzte
  Sammelkomponente und gelöste Teile verschiebt ein Joint die ganze Sammelkomponente.
- `addDistanceDimension(..., False)` erzeugt Referenzmaße, das letzte Argument heißt `isDriving`. Mehrere Punkte mit
  steuernden Maßen in einer Skizze melden Überbestimmung, deshalb eine Skizze je Punkt.
- Eine Timeline-Gruppe als Ganzes zu löschen nimmt einen umgehängten Joint mit. Einzeln löschen.
- Joints in zugeklappten Gruppen lassen sich nicht per `rollTo` ansteuern, die Gruppe vorher aufklappen.
- pytest importiert die Fusion-Module nicht: `python -m pyflakes` auf geänderte Dateien fand einen fehlenden Import.

## Nächste Schritte (Hauptsitzung)

- Jörg: Fusion neu starten (lädt den Fork-Ordner, Branch `runde-13`), Handtest wie unten, dann Merge nach `master`.

## Handtest für Jörg (nach Fusion-Neustart)

1. Neues Dokument. Baseplate 3x2, Bin 2x1x6 mit Cullenect und 2 Fächern, Bin 1x1 mit farbiger Beschriftung. Im Browser
   prüfen: Grid, Bins, Label, die farbige Bin mit Unterkomponente „Text“. Dass das Dokument hybrid wird, meldet
   jetzt auch der Bin- und Baseplate-Befehl.
2. Label-Befehl: im Feld „Pocket“ den Joint Origin „Compartment 2 pocket joint origin“ der Cullenect-Bin anklicken (der
   Fuß-Origin lässt sich nicht wählen), OK. Der Einleger sitzt in der Tasche. Ein 2U-Einleger auf diese Tasche wird
   abgelehnt.
3. Einen zweiten Einleger ohne Tasche: Er liegt neben allem.
4. Die Bin per Hand verschieben: Der eingesetzte Einleger wandert mit.
5. Rechtsklick „Gridfinity rebuild“ auf die Cullenect-Bin, Höhe ändern: Der Einleger sitzt danach auf dem neuen
   Taschenboden.
6. Komponente „Text“ eines Einlegers als 3MF exportieren bzw. im Slicer getrennt zuweisen.
