# Auftrag Runde 29: Scharniere (Preds `Hinge_M3x30`, `Hinge_Pined`, `Hinge`)

Gemeinsame Regeln: `dev-notes/r29/README.md`. Die drei Varianten teilen sich viel. Sie können in einer Untersitzung
laufen oder M3x30 zuerst und Pinned/Plain danach; das entscheidet die Hauptsitzung.


## Pflicht: jede Skizze vollständig bestimmt

Jörg 17.11.2026: „Denk nur dran, dass alle Zeichnungen vollständig bestimmt sein müssen.“
- Jede Skizze dieses Teils ist `isFullyConstrained`. Das gilt auch dort, wo Preds Vorlage es nicht ist. Die JSON aus
  `r29_parts_walk` nennt je Skizze `fullyConstrained`, `freeCurves` und `freePoints`.
- Der pytest prüft den Plan (`sketchChain`/`predSketch`): jede Kurve und jeder Punkt bestimmt, keine losen Punkte.
- Die Fusion-Prüfung meldet je Skizze `isFullyConstrained`; ein einziges False heißt nicht bestanden.

## Ziel

`lib/gridfinityUtils/predHinge.py` mit
`createHinge(component: adsk.fusion.Component, hinge: str) -> list[adsk.fusion.BRepBody]`.
`hinge` ist ein Schlüssel von `predBoxParts.HINGES`.

| `hinge` | Pred | Körper (Namen wie bei Pred) | Volumen mm³ | Körper-Box im Teil-Rahmen, mm |
|---|---|---|---|---|
| `M3x30` | `Hinge_M3x30` | BottomHingePart_M3x30, TopHingePart_M3x30 | 1040,9566 + 1376,3412 | (−9,2516 \| −4 \| 0) … (9,2516 \| 8,8 \| 31,6) |
| `Pinned` | `Hinge_Pined` | BottomHingePart_M3x30, TopHingePart_M3x30, `Hinge pin` (Pred: Body21) | 1019,3530 + 1335,3042 + 379,1602 | wie M3x30 |
| `Plain` | `Hinge` | BottomHingePart, TopHingePart | 896,2301 + 1601,6758 | (−76,2325 \| −3,5 \| 0) … (−58,7 \| 8,5 \| 31,6) |

- Teil-Rahmen: wie die `.f3d` (`hinge.f3d`, `hingePinned.f3d`, `hingePlain.f3d`), also Preds Komponenten-Rahmen.
- Die Ecken je Variante in `predBoxSeats.HINGE_BODY_BOX` setzen diesen Rahmen voraus. Die Untersitzung muss ihn
  halten, sonst sind die Ecken neu zu bestimmen und zu melden.

## Preds Scharniere

- Quellen: `fusion-auftraege/r29_walk/Hinge_M3x30.json`, `Hinge_Pined.json`, `Hinge.json`. Dazu
  `r28_hinge_variants.log` mit den Parameter-Ausdrücken.
- M3x30: Skizzen HingeBaseTopology (40), HingeTabDetails (11), Sketch3 (13), Sketch4 (9), Sketch5 (10); 23 Features
  (Extrude ×16, Chamfer ×5, Mirror2/3).
- Pinned: dieselbe Grundform, dazu Sketch6/7 und der Stift; 28 Features.
- Plain: HingeBaseTopology und HingeTabDetails; 18 Features.
- Gemeinsam: Laschen aus Preds Schlitzmaßen, gesetzt als Werte. Länge 32 mm (Lasche 31,6), Breite 2 mm, Tiefe 9 mm,
  3 mm von hinten, Spiel 0,15 mm.
- Unterschiede:
  - Loch und außen: Plain 4 + 2 × 0,15 / 7 + 3 × 0,15; M3x30 und Pinned 3,5 + 4 × 0,15 / 8 + 2 × 0,15.
  - Laschenbreite −0,2 (Plain) bzw. −0,4; Laschentiefe −0,5 bzw. −0,2.

## Joint origin

Keiner in den Dateien. Die Integration legt *Hinge joint origin* am Komponenten-Ursprung an
(`predBoxInsert.addOriginJointOrigin`); das Teil braucht keinen eigenen.

## Zu beachten

- **Mirror2/3:** Die Eingaben stehen in der JSON. Bei Fasen oder Rundungen wird das Gegenstück direkt gebaut (README).
- **HingeTabDetails und Sketch3** waren bei Pred nicht voll bestimmt. `hinge.f3d` hat sie mit Maßen zum jetzigen Wert
  bestimmt (`resources/predBox/README.md`). Gezeichnet wird von vornherein voll bestimmt.
- **Prüfung je Variante:** gegen Preds Komponente im Teil-Rahmen. Zusätzlich die Laschen gegen die Schlitze der Box:
  31,6 in 32, 1,8 bzw. 1,6 in 2,1, 8,8 bzw. 8,5 in 9.

## Schätzung

1,5–2 Tage für alle drei.
