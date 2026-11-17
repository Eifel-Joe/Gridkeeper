# Plan Runde 29: Haltestift im Code (`predHandlePin`)

Auftrag `handlePin.md`, Regeln `README.md`. Branch `r29-pin` ab `runde-29` (c46e91e).

## Preds Stift, aus `r29_walk/HandlePin.json` gelesen

Achse entlang x, Mitte (y 3,75 | z 24,7) mm, im Teil-Rahmen von x 58,05 bis 77,75:

| Abschnitt x (mm) | Form |
|---|---|
| 58,05–60,05 | Spitze ⌀3,5, vorn Fase 1 mm |
| 60,05–74,45 | Schaft ⌀2,6 |
| 74,45–77,75 | Kopf ⌀5,1 |

Dazu drei Schnitte, alle von der Spitze aus:
- unten ab z < 23,4 über die ganze Länge (y 1,2–6,3);
- oben ab z > 26,0 nur über die Spitze (2 mm);
- Schlitz 0,6 mm breit (y 3,45–4,05, z 23,4–26,0), 4 mm tief.

Preds Features enden fast alle „bis Fläche“ seines Griffs (Ebenen x 60,25 / 74,25 mit Versatz 0,2). Im eigenen Teil
gibt es diese Flächen nicht; ich ersetze sie durch Abstände mit denselben Endlagen (17,7 / 3,3 / 2 / 4 / 19,7 mm).

## Bau

Beide Skizzen auf einer Ebene x = 58,05 mm (Versatz der YZ-Ebene, wie `predBoxGenerator.offsetPlane`), gezeichnet mit
`predSketch.WorldSketch`. Damit hängt keine Skizze an einer Körperfläche, und alles wird nur in +x extrudiert.
1. **Sketch1 „Pin profile“:** drei konzentrische Kreise ⌀2,6 / 3,5 / 5,1. Der gemeinsame Mittelpunkt wird vom Ursprung
   aus bemaßt, dazu drei Durchmesser. Voll bestimmt durch `sketchChain`.
2. **Extrude1:** Scheibe ⌀2,6, neuer Körper, 19,7 mm. Der Körper heißt `Handle pin`.
3. **Extrude2:** Ring 2,6–3,5, Join, 2 mm (Spitze).
4. **Extrude3:** Ringe 2,6–5,1, Join, Start-Versatz 16,4 mm, 3,3 mm (Kopf).
5. **Chamfer1:** 1 mm an der Kreiskante r 1,75 bei x 58,05. Die Kante wird über ihre Geometrie gewählt (Mitte, Radius);
   gespiegelt wird nichts.
6. **Sketch2 „Pin cuts“:** ein geschlossenes I-Profil (unteres Rechteck, Schlitz, oberes Rechteck; 12 Punkte, nur
   waagrecht/senkrecht), dazu zwei Trennlinien. Das ergibt genau drei Profile, voll bestimmt durch `sketchChain`.
7. **Extrude4/5/6:** Cut unten 19,7 mm, Schlitz 4 mm, oben 2 mm. Die Profile werden über ihre Welt-Boxen gewählt
   (`WorldSketch.profiles`). Unten und oben haben dieselbe Fläche, deshalb geht `profilesByArea` hier nicht.
8. **Joint origin** `Handle pin joint origin` bei (77,75 | 3,75 | 24,7) mm über `baseGenerator.createPointJointOrigins`.
   Das ist ein bemaßter Skizzenpunkt auf einer Ebene z = 24,7 mm, Z nach oben, X entlang X, wie in `handlePin.f3d`.

Keine Benutzerparameter, nur feste mm-Werte, intern in cm.

## Tests (pytest, zuerst rot)

`tests/test_pred_handle_pin.py`, Fusion-frei über die Plandaten des Moduls:
- Beide Skizzen-Ketten sind exakt bestimmt (`sketchChain.rank` == Variablenzahl, wie `test_sketch_chain.check`).
- Profilflächen 5,3093 / 4,3118 / 10,8071 mm² wie Preds `Sketch1`-Profile.
- **Volumen des geplanten Körpers** analytisch je x-Abschnitt integriert (Kreis ∩ Band ∖ Schlitz, Fase als linearer
  Radius): 138,1225 mm³ auf 0,001. Außerdem Körper-Box (58,05 | 1,2 | 23,4)–(77,75 | 6,3 | 27,25).
- Joint origin: Name und Lage.
- Quelltext per `ast`: `createHandlePin(component)` gibt eine Liste mit einem Körper zurück, er heißt `Handle pin`, keine
  Spiegelung (`mirrorFeatures`), keine Benutzerparameter (`userParameters`).

## Fusion-Prüfung (Job über die Hauptsitzung)

`fusion-auftraege/r29_pin_check.py`, ein Lauf (Ziel < 20 s), Code aus diesem Worktree:
- Ein neues Dokument (Hybrid) mit einer neuen Komponente; darin `createHandlePin`.
- `resources/predBox/handlePin.f3d` per `importToTarget` als Gegenprobe in dasselbe Dokument. Das ist Preds Stift im
  Teil-Rahmen, laut r28_extract l2 V 138,1225, mit Joint origin.
- Boole-Differenz in beide Richtungen nach `r28_compare`: Rest ≤ 0,05 mm, Volumen auf 0,001 mm³.
- Alle Skizzen `isFullyConstrained`, Zeitleiste gesund.
- Joint origin: Ort und Achsen gleich dem der .f3d.
- Körpername `Handle pin`.
- Ausgabe `r29_pin_check.log`. Der Job schließt sein Dokument am Ende wieder (wie `r29_handle_check`); des Nutzers
  Dokumente werden nicht angefasst.

## Grenzen

Nur `lib/gridfinityUtils/predHandlePin.py`, `tests/test_pred_handle_pin.py` und dieser Plan.
`fusion-auftraege/r29_pin_*.py` liegt außerhalb des Repos. Gemeinsame Werkzeuge bleiben unverändert. Nicht pushen,
kein PR.
