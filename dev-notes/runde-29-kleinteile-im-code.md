# Übergabe: neue Runde „Kleinteile im Code zeichnen“ (Release-Blocker 1.1.0)

Stand 17.11.2026, aus Runde 28 und dem Blocker. Nutzer hält diesen Weg für den richtigen: Die Teile entstehen im
selben Befehl wie Box und Deckel und landen damit von selbst in der Zeitleisten-Gruppe der Box.

## Warum

- `importManager.importToTarget` scheitert im execute jedes Befehls mit Eingaben, also mit Dialog
  (`fusion-auftraege/r28_cmdvariants.log`); ohne Eingaben geht es. Der Box-Dialog braucht seine Eingaben.
- Die Teile nach dem Befehl einzufügen (Branch `box-teile-nach-befehl`, Versuche 1–4) scheiterte an der Zeitleiste:
  - Neue Gruppen sind zugeklappt; dann scheitern index und rollTo (`r28_groupindex.log`).
  - Aufgeklappt scheiterte danach `TimelineGroup.deleteMe(False)` (Klicktest Versuch 4, 17:12:49).
- Vereinbarung mit Nutzer: kein Versuch 5 auf diesem Weg.

## Welche Teile

Maße und Zählungen aus `fusion-auftraege/r28_tmp/pred_parts.json` (Preds Datei bei 5 × 4 × 6), Volumen in mm³.

| Teil | Anzahl | Pred | Skizzen (Kurven) | Features | Volumen |
|---|---|---|---|---|---|
| Riegel | 4 | `Latch_Experimental` | Sketch1 (34), Sketch2 (33, auf einer Fläche, 4 Bezugskurven) | 19: Extrude ×7, Fillet ×4, Chamfer ×6, Mirror1, R-Pattern2 | 3232,0691 |
| Griff | 1 | `Handle` | in Preds Datei keine | 5: Extrude1, Fillet1, Chamfer1, Extrude2 (Bohrung), Mirror1 | 6136,8299 (Breite 99) |
| Haltestift | 2 | `HandlePin` | Sketch1 (18), Sketch2 (15) | 7: Extrude ×6, Chamfer1 | 138,1225 |
| Scharnier M3x30 | 2 | `Hinge_M3x30` | HingeBaseTopology (40), HingeTabDetails (11), Sketch3 (13), Sketch4 (9), Sketch5 (10) | 23: Extrude ×16, Chamfer ×5, Mirror ×2 | 1040,9566 + 1376,3412 |
| Scharnier Pinned | 2 | `Hinge_Pined` | wie M3x30, dazu Sketch6/7 | 28, 3 Körper (Stift „Hinge pin“) | 1019,3530 + 1335,3042 + 379,1602 |
| Scharnier Plain | 2 | `Hinge` | HingeBaseTopology, HingeTabDetails | 18 | 896,2301 + 1601,6758 |

Die drei Scharniere teilen sich die Laschen. Diese hängen an den vier Schlitzmaßen der Box: Länge 32, Tiefe 9,
Breite 2, Abstand von hinten 3 mm; Spiel 0,15 mm. Sie unterscheiden sich im Loch- und Außendurchmesser
(Plain 4/7, M3x30 und Pinned 3,5 + 4 × 0,15 / 8 + 2 × 0,15) und in der Laschenstärke (Breite −0,2 bzw. −0,4,
Tiefe −0,5 bzw. −0,2). Die Ausdrücke stehen in `fusion-auftraege/r28_hinge_variants.log`.

## Was es schon gibt

- **Griff:** `fusion-auftraege/r28_handle_build.py` zeichnet ihn bereits im Code.
  - Profil auf XZ, Bögen r8/r15, Extrude 7 symmetrisch, Fillet r3,5, Fase 1 mm an 14 Kanten, Bohrung d3,5 über
    `addWithoutEdges`, Spiegelung.
  - Volumen gleich Preds bei beiden Halbbreiten; nach `lib/gridfinityUtils` übertragen.
- **Lagen und Gelenke:** `predBoxSeats` (Sitze als Formeln auf den Box-Parametern, Scharnier-Ecken je Variante),
  `predBoxParts` (Rollen, Anzahl, Sitze, Varianten), die Joint origins der Box und die Gelenk-Erzeugung in
  `predBoxInsert` (Drehung je Sitz). Das bleibt; nur das Einfügen per Import wird ersetzt.
- **Werkzeuge aus Runde 27** für Bauen und Prüfen:
  - `lib/gridfinityUtils/predSketch.py`, `sketchChain.py` (voll bestimmte Skizzen aus Weltkoordinaten,
    `arcDrawing` für Bögen).
  - `predBoxEdges.py` (Kantenauswahl für Fasen und Rundungen).
  - `fusion-auftraege/r27_pred_walk.py` liest eine Komponente in Preds Datei Schritt für Schritt aus: Skizzen,
    Profile, Kanten, Spiegel-Eingaben. Bisher lief es für `Box`; für die Teile die Komponente umstellen.
  - `r28_compare.py` (Boole-Vergleich je Teil gegen Pred, Toleranz 0,05 mm, Rahmen-genau), `r28_insert_check.py`
    (Lagen gegen Preds Datei), Snapshot-Fälle `box_*`.
- **Preds Teile als Dateien:** `resources/predBox/*.f3d` (voll bestimmt nachbearbeitet) und
  `fusion-auftraege/r28_tmp/raw_*.f3d` (roh) als Lesequelle für die Maße.

## Schätzung

| Schritt | Aufwand |
|---|---|
| Griff aus `r28_handle_build` in einen Generator übertragen, Breite als Ausdruck | 0,5 Tag |
| Haltestift (2 Skizzen, 7 Features) | 0,5 Tag |
| Riegel (2 dichte Skizzen, eine davon auf einer Fläche, 19 Features mit Kantenauswahl, Muster) | 1–1,5 Tage |
| Scharnier: Grundform plus drei Varianten | 1,5–2 Tage |
| Einbau in `boxBuilder` (Teile-Komponenten im Satz, Gelenke wie bisher), Rebuild/Clone, Tests, Snapshots, `r28_compare` je Teil | 1 Tag |
| **Zusammen** | **etwa 4,5–5,5 Arbeitstage**, dazu Fusion-Läufe über die Hauptsitzung |

## Risiken

- **Kantenauswahl** für Fasen und Rundungen, vor allem beim Riegel (6 Fasen, 4 Rundungen):
  - Fusions Mirror und Fasen rechneten in Runde 27 je nach Dokumentzustand anders (Mirror6).
  - Vorbeugen: auf Spiegelungen verzichten und Gegenstücke direkt bauen, wie in Runde 27 bei den Haltern.
- **Voll bestimmte Skizzen** mit vielen Bögen (34/33/40 Kurven).
  - In Runde 27 lösten `arcDrawing` und der Planer das.
  - Bei Skizzen auf Flächen (Riegel Sketch2) projiziert Fusion Kanten mit; `addWithoutEdges` nehmen.
- **Bauzeit:** Ein Satz mit Teilen braucht heute rund 95 s. Gezeichnete Teile werden eher länger rechnen als
  eingefügte; vier Riegel und zwei Stifte sind aber je eine Komponente, die mehrfach vorkommt, und werden nur einmal
  gezeichnet.
- **Maßgleichheit:** Ziel ist Restkörper ≤ 0,05 mm gegen Preds Teile (`r28_compare`). Die Volumina oben dienen als
  schnelle Kontrolle.
- **Scharnier-Druckposition:** Die Teile liegen in Preds Teil-Rahmen. Die Ecken je Variante in `predBoxSeats`
  setzen diesen Rahmen voraus; die gezeichneten Teile müssen denselben Rahmen haben, oder die Ecken werden neu
  bestimmt.

## Bis dahin

- `master` (1.1.0, 0afa26a) fügt die Teile im Dialog per Import ein und scheitert dort.
- Ob 1.1.0 so bleibt oder die Teile im Dialog vorerst ausgelassen werden, entscheidet Nutzer.
- Der Branch `box-teile-nach-befehl` (bis c3df9f5) ist nicht mergefähig. Er enthält aber diese Übergabe und die
  belegten Befunde in `boxPartsLater.py` und im Spec-Nachtrag.
