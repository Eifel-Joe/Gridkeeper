# Auftrag Runde 29: Griff (Preds `Handle`)

Gemeinsame Regeln: `dev-notes/r29/README.md`.


## Pflicht: jede Skizze vollständig bestimmt

Vorgabe 17.11.2026: Alle Zeichnungen müssen vollständig bestimmt sein.
- Jede Skizze dieses Teils ist `isFullyConstrained`. Das gilt auch dort, wo Preds Vorlage es nicht ist. Die JSON aus
  `r29_parts_walk` nennt je Skizze `fullyConstrained`, `freeCurves` und `freePoints`.
- Der pytest prüft den Plan (`sketchChain`/`predSketch`): jede Kurve und jeder Punkt bestimmt, keine losen Punkte.
- Die Fusion-Prüfung meldet je Skizze `isFullyConstrained`; ein einziges False heißt nicht bestanden.

## Ziel

`lib/gridfinityUtils/predHandle.py` mit
`createHandle(component: adsk.fusion.Component, halfWidth: str) -> list[adsk.fusion.BRepBody]`.

- `halfWidth` ist der Ausdruck der halben Griffbreite. Die Integration übergibt
  `predBoxSeats.handleHalfWidth(dims).expression`, in Tests reicht z. B. `'49.5 mm'`.
- Die Skizze bekommt ihn als Bemaßung. So folgt der Griff der Schildbreite, ohne Benutzerparameter.
- Ein Körper, er heißt `Handle`.

## Vorlage

`fusion-auftraege/r28_handle_build.py` zeichnet den Griff schon. Übertragen in das Modul.

- Profil auf XZ, Arm bei −H, Bögen r8 und r15 um (−H+15 | −11,5).
- Steg bis x = 0, gehalten von einer senkrechten Hilfslinie vom Ursprung.
- Maße: H, r8, r15, 3,5, 15.
- Extrude 7 mm symmetrisch, Fillet r3,5 an 2 Kanten, Fase 1 mm an 14 Kanten.
- Bohrung d3,5 über `addWithoutEdges`, Profil nach der Fläche π · 1,75² gewählt, durch alles symmetrisch.
- Spiegelung des Körpers an YZ, combine. Das ist eine Körper-, keine Fasen-Spiegelung und ging in Runde 28.

Preds Griff ist in Preds Datei an der Box modelliert, mit Skizze in der Box-Komponente.
`r29_walk/Handle.json` enthält sie unter `referencedSketches`, zum Gegenprüfen der Maße.

## Joint origin

*Handle joint origin* am Teil-Ursprung, Achsen wie die Komponente, wie in `r28_handle_build`.

## Prüfung

- Volumen 6136,8299 mm³ bei H 49,5 und 6818,3299 mm³ bei H 56,75. Das prüfte `r28_handle_build` schon so.
- Gegen Preds `Handle:1` an Ort und Stelle: In `r28_compare` l3 war der Teil-Rahmen an Preds Stelle, die Verschiebung
  0.
- Breite bei 4 / 5 / ab 6 Einheiten: 57 / 99 / 113,5 mm. Die Tests dafür gibt es in `predBoxSeats`, hier über den
  Ausdruck prüfen.

## Schätzung

0,5 Tag.
