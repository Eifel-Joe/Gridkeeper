# Auftrag Runde 29: Haltestift (Preds `HandlePin`)

Gemeinsame Regeln: `dev-notes/r29/README.md`.

## Ziel

`lib/gridfinityUtils/predHandlePin.py` mit
`createHandlePin(component: adsk.fusion.Component) -> list[adsk.fusion.BRepBody]`.
Ein Körper, er heißt `Handle pin`.

## Preds Stift

- Quelle: `fusion-auftraege/r29_walk/HandlePin.json`.
- Zwei Skizzen: `Sketch1` mit 18 Kurven, `Sketch2` mit 15 Kurven.
- 7 Features: Extrude1–6, Chamfer1.
- 138,1225 mm³.
- In Preds Datei liegt `HandlePin:1` mit Teil-Rahmen gleich der Welt bei 5 × 4 × 6. Die Körper-Box ist
  (58,05 | 1,2 | 23,4) … (77,75 | 6,3 | 27,25) mm.
- Teil-Rahmen: wie `resources/predBox/handlePin.f3d`, also Preds Komponenten-Rahmen.

## Joint origin

*Handle pin joint origin* bei (77,75 | 3,75 | 24,7) mm im Teil-Rahmen, auf der Bolzenachse an der Bolzen-Ebene.
Z-Achse = Teil +z, X-Achse = Teil +x (`r28_extract`, Ursprung (7,775 | 0,375 | 2,47) cm). In `handlePin.f3d` hält eine
voll bestimmte Skizze *Seat* den Punkt. Beim Zeichnen genügt ein bemaßter Skizzenpunkt.

## Prüfung

Gegen Preds `HandlePin` im Teil-Rahmen (`r28_compare` l3: an Ort und Stelle gleich). Der rechte Stift ist dasselbe
Teil, um z um 180° gedreht (`predBoxSeats.turnAboutZ`); daran ändert sich nichts.

## Schätzung

0,5 Tag.
