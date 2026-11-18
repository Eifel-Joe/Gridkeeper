# Runde 35: Schneid-Skizzen voll bestimmt (p282, p290)

Stand 18.11.2026. Regel: jede Skizze, die der Generator anlegt, ist voll bestimmt (`Sketch.isFullyConstrained`).
Festlegung: Fehler aus dem Original werden nur im Fork behoben.

## Punkte
- p282 „Geformte Bins: eine Skizze zum Beschneiden des äußeren Freiraums ist nicht vollständig bestimmt“
  (`Outer clearance trim sketch`, `baseGenerator.cutOutsideShape`).
- p290 „Baseplate: Skizze ‚Plate outline trim sketch‘ nicht voll bestimmt“
  (`Plate outline trim sketch` und gleich gebaut `Plate pieces cut sketch`, `baseGenerator.cutOutsideRoundedRectangles`).

## Ursache (belegt)
Beide Funktionen zeichnen um die Umrisse einen Rahmen mit `sketchLines.addTwoPointRectangle(...)`, ohne Lage und Maße.
Fusion setzt dabei nur Waagrecht/Senkrecht, es bleiben 4 Freiheitsgrade (Lage x/y, Breite, Länge).
Beleg: `fusion-auftraege/ug_snap.step13.out`, `bin_3x3x4_l_shape_lip_full`: 12 von 13 Skizzen voll bestimmt, auch die
Lippen-Skizzen aus derselben `createShapeOutlineSketch`; lose ist nur `Outer clearance trim sketch`. Ebenso
`r27_snap.out`, `baseplate_3x2_full`: nur `Plate outline trim sketch` lose. Die Umrisse selbst sind bemaßt
(`createShapeOutlineSketch` bzw. `createRectangle` mit Lage-Dims), nur der Rahmen nicht.
Schwester-Pfad-Check: `addTwoPointRectangle` ohne Bemaßung kommt in `lib/` und `commands/` nur an diesen zwei Stellen vor.

## Optionen
1. **Rahmen mit `sketchUtils.createRectangle` zeichnen** (Ecke vom Ursprung bemaßt, Breite, Länge), über eine gemeinsame
   Hilfsfunktion `sketchUtils.addFrame(sketch, minX, minY, maxX, maxY)` für beide Stellen. Lage und Größe als feste
   Werte (wie bisher berechnet: Abstand = größere Ausdehnung des Umrisses auf jeder Seite).
2. Rahmenlinien `isFixed = True`. Zählt in Fusion zwar als bestimmt, ist aber ein anderes Muster als im übrigen Code
   und lässt sich nicht über Maße nachvollziehen. Verworfen.
3. Rahmen an die Parameter-Ausdrücke binden (wächst mit Rastermaß). Mehr Aufwand ohne Nutzen: der Rahmen ragt um die
   volle Umrissgröße über, eine Parameteränderung bis auf das Doppelte bleibt innerhalb. Verworfen.

**Entscheidung:** Option 1. Eine Hilfsfunktion, beide Aufrufer nutzen sie, keine Zweitfassung der Rahmenrechnung.

## Nicht dabei
Andere lose Skizzen (keine bekannt in den betroffenen Fällen), Änderungen an Umriss-Geometrie, Schnitttiefe oder
Profilauswahl; Strenge der Snapshot-Prüfung für Bins/Baseplates (bleibt „reported only“).

## Ende-zu-Ende
- pytest: `addFrame` bestimmt alle vier Ecken (Waagrecht/Senkrecht + 4 Maße, Fortpflanzung über alle Punkte) und
  liegt um den Abstand außerhalb des Umrisses. Quelltext-Test: `baseGenerator` zeichnet keinen Rahmen mehr per
  `addTwoPointRectangle`.
- Fusion (Code aus `wt-r35`): `bin_3x3x4_l_shape_lip_full` bzw. ein L-Form-Bin mit Kerben,
  `bin_2x2x3_l_shape_half_grid`, `baseplate_3x2_full`, `baseplate_2x2_light_magnets_3mm`, `baseplate_fill_area_pieces`
  (Stückschnitt): alle Skizzen `isFullyConstrained`, Snapshots unverändert grün.

# Plan

Task 1 — `tests/test_sketch_frame.py` (neu): Fake-Skizze, `sketchUtils.addFrame` bestimmt alle Eckpunkte, Rahmen um
den Abstand außen. RED: `addFrame` fehlt. Implementierung: `addFrame` in `sketchUtils.py` über `createRectangle`.
GREEN: Test grün, volle Suite grün. Commit.

Task 2 — Quelltext-Test in derselben Datei: kein `addTwoPointRectangle` in `baseGenerator.py`. RED: zwei Fundstellen.
Implementierung: `cutOutsideShape` und `cutOutsideRoundedRectangles` rufen `sketchUtils.addFrame`. GREEN, volle Suite.
CHANGELOG `## Unreleased`. Commit.

Task 3 — Fusion-Prüfung (ein Slot, ein Skript, die fünf Fälle oben, je Fall Skizzen-Check + Snapshot-Vergleich).

Task 4 — Opus-Review, Funde prüfen. Push, PR (Text vorher an die Hauptsitzung), CI.

Kein Klicktest nötig: der Code läuft beim Erzeugen, nicht im Dialog; die Fusion-Prüfung erzeugt über denselben Pfad.
