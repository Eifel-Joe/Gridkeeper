# Runde 29: Preds Kleinteile im Code zeichnen. Gemeinsame Regeln für alle Teile

Entscheidung 17.11.2026: Die Teile werden im Code gezeichnet. Warum, und was es schon gibt, steht in
`dev-notes/runde-29-kleinteile-im-code.md`. Spec: `dev-notes/specs/2026-11-16-pred-box-design.md`. Für die Bauweise
gelten auch die Nachträge von Runde 28.

Je Teil eine Untersitzung mit eigenem Auftrag: `latch.md`, `handle.md`, `handlePin.md`, `hinge.md`. Die Integration
übernimmt danach die Integrations-Sitzung: `predBoxInsert` auf die Generatoren umstellen, den `.f3d`-Import und
`resources/predBox/*.f3d` entfernen, Snapshots ablegen.

## Was jedes Teil liefert

- **Ein Modul** `lib/gridfinityUtils/pred<Teil>.py` mit einer Funktion, die das Teil in eine übergebene, leere
  Komponente zeichnet und deren Körper zurückgibt. Die Signatur steht im Auftrag des Teils. Sonst ändert die
  Untersitzung keine Datei außer ihren eigenen Tests. Gemeinsame Werkzeuge werden nur ergänzt, nicht umgebaut, und das
  wird gemeldet.
- **Teil-Rahmen:** derselbe wie die bisherige `.f3d` in `resources/predBox`. Das ist Preds Komponenten-Rahmen; beim
  Griff ist es der Rahmen von `r28_handle_build`. So bleiben die Sitze in `predBoxSeats` und die Gelenke in
  `predBoxInsert` unverändert gültig.
- **Joint origin** mit demselben Namen, Ort und denselben Achsen wie in der `.f3d`. Die Werte stehen im Auftrag.
- **Körpernamen** wie bisher: ein einzelner Körper heißt wie die Rolle (`Latch`, `Handle`, `Handle pin`). Die
  Scharniere behalten Preds Namen, der gedruckte Stift heißt `Hinge pin` (benennt der Generator selbst).
- **Pflicht: jede Skizze vollständig bestimmt** (`Sketch.isFullyConstrained`; Vorgabe: Alle Zeichnungen müssen vollständig bestimmt sein.). Geprüft per pytest des Plans und in Fusion; die freien Kurven/Punkte von Preds Skizzen stehen in der Walk-JSON (`freeCurves`, `freePoints`).
  - Keine Benutzerparameter. Nur der Griff hat eine Breite, die als Ausdruck an den Box-Parametern hängt.
  - Längen intern in cm, Tests in mm (Projekt-`CLAUDE.md`).
  - Werkzeuge: `predSketch.py`, `sketchChain.py`, `arcDrawing`.
  - Skizzen auf Flächen mit `sketches.addWithoutEdges`.
- **Keine Feature-Spiegelung von Fasen oder Rundungen** (Runde 27, Mirror6, `FILLET_NO_EDGE_FOUND`):
  - Gegenstücke direkt bauen, Kanten mit gespiegelten Koordinaten wählen (`predBoxEdges.mirrorItem`).
  - Eine Körper-Spiegelung (Mirror mit Körper als Eingabe, combine) wie in `r28_handle_build` ging in Runde 28.
    Bevor eine Fase oder Rundung gespiegelt wird, das mit der Hauptsitzung klären.

## Grundlagen

- `fusion-auftraege/r29_walk/<Pred-Komponente>.json` aus `r29_parts_walk.py`: jedes Element des Teils in Preds
  Zeitleisten-Reihenfolge. Das sind Skizzen mit Kurven, Bedingungen und Bemaßungen samt Ausdrücken, dazu die Features
  mit Eingaben und Kanten als Geometrie, sowie Körper nach jedem Schritt. Die Länge ist in mm.
- `fusion-auftraege/r28_tmp/pred_parts.json`: Lagen, Volumen und Skizzenzahlen der Teile in Preds Datei.
- `fusion-auftraege/r28_tmp/raw_*.f3d`: Preds Teile roh. `resources/predBox/*.f3d` sind die nachbearbeiteten
  Fassungen, mit Joint origin und voll bestimmt.
- `fusion-auftraege/r28_extract.l1–l7.out`: Volumen und Körper-Boxen je Teil im Teil-Rahmen.

## Prüfung

- **pytest:**
  - Reine Geometrie (Punkte, Maße als `Dim`) Fusion-frei testen, wie `tests/test_pred_box_*.py`.
  - Was Fusion braucht, über den Quelltext (`ast`) wie `tests/test_box_builder_bodies.py`.
  - Erst ein fehlschlagender Test, dann der Code.
- **Fusion,** über die Hauptsitzung: Skript in `fusion-auftraege`, je Lauf unter 50 s, vorher trocken geprüft und
  während eines Batches nicht mehr geändert.
  - Das Teil in eine neue Komponente eines NEUEN Dokuments zeichnen (Hybrid).
  - Vergleich gegen Preds Teil nach dem Muster `r28_compare.py`: Preds Körper mit dem Kehrwert ihrer Occurrence-Lage in
    den Teil-Rahmen holen, dann Boole-Differenz in beide Richtungen. Bestanden heißt: kein Restkörper mit kleinster
    Ausdehnung über 0,05 mm, Volumen gleich auf 0,001 mm³.
  - Dazu: alle Skizzen voll bestimmt, Zeitleiste gesund, Joint origin an Ort und mit Achsen wie in der `.f3d`
    (diese als Gegenprobe ins selbe Dokument importieren).
- **Review** ohne offene Funde vor der Übergabe an die Integration.

## Ablauf

- Branch je Teil von `runde-29` (z. B. `runde-29-latch`), eigener Worktree. Commits nur der eigenen Dateien.
- Die Untersitzung meldet der Hauptsitzung den fertigen Branch, die Ergebnisse (pytest, Fusion-Vergleich) und
  Abweichungen.
- Merge nach `runde-29` macht die Hauptsitzung.
- Abweichungen von Preds Form oder von diesen Regeln werden nicht gebaut, sondern gemeldet.
