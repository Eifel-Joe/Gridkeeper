# Auftrag Runde 29: Riegel (Preds `Latch_Experimental`)

Gemeinsame Regeln: `dev-notes/r29/README.md`.

## Ziel

`lib/gridfinityUtils/predLatch.py` mit `createLatch(component: adsk.fusion.Component) -> list[adsk.fusion.BRepBody]`.
Die Funktion zeichnet Preds Riegel in die leere Komponente und gibt seinen einen Körper zurück; dieser heißt `Latch`.

## Preds Riegel

- Quelle: `fusion-auftraege/r29_walk/Latch_Experimental.json`.
- Zwei Skizzen:
  - `Sketch1`: 34 Kurven, auf XY.
  - `Sketch2`: 33 Kurven, auf einer Fläche (−9,8 | 0 | 0) mit Normale −X, 4 Bezugskurven.
- 19 Features: Extrude1–7, Fillet1–4, Chamfer1–3/5–7, Mirror1, R-Pattern2.
- Ein Körper, 3232,0691 mm³.
- In Preds Datei liegt die Occurrence `Latch_Experimental:1` flach in Druckposition am Ursprung, mit Teil-Rahmen
  gleich der Welt. Die Körper-Box ist (−11,8 | −36,5 | 0) … (11,8 | 0 | 7) mm.
- Teil-Rahmen: wie `resources/predBox/latch.f3d`, also Preds Komponenten-Rahmen.

## Joint origin

*Latch joint origin* am Teil-Ursprung (0 | 0 | 0). Z-Achse = Teil +y, X-Achse = Teil −x; in `r28_extract` war das
Drehung 180°. Eingebaut ergibt das die Lage von Preds `Latch:1`; geprüft mit `r28_compare` l3.

## Zu beachten

- **Mirror1:** Die Eingaben stehen in der JSON. Spiegelt Pred damit Fasen oder Rundungen, wird das Gegenstück direkt
  gebaut (README).
- **R-Pattern2:** ein Rechteck-Muster. Anzahl und Abstand stehen in der JSON; direkt nachbauen.
- **Sketch2 auf einer Fläche:** Die Skizze mit `addWithoutEdges` anlegen. Die 4 Bezugskurven von Pred als eigene,
  bemaßte Linien zeichnen, nicht projizieren.
- **Prüfung:** gegen Preds `Latch_Experimental` im Teil-Rahmen. Zusätzlich eingebaut gegen `Latch:1`. Das ist eine
  ältere Form mit 3258,3859 mm³, daher nur als Bericht. Die erwarteten Reste sind 2 × 4,41 und 2 × 17,57 mm³
  (`r28_compare.l3.out`).

## Schätzung

1–1,5 Tage.
