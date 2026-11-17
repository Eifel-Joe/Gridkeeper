# Plan Runde 29, Riegel (`Latch_Experimental`)

Branch `r29-latch` (ab `runde-29`, c46e91e). Auftrag `latch.md`, Regeln `README.md`.
Quelle: `fusion-auftraege/r29_walk/Latch_Experimental.json`. Maße in mm, im Code in cm.

## Was Pred baut

- Pred baut die **linke Hälfte** (x ≤ 0):
  - Sketch1 auf XY, Extrude1/2/5, Fillet1–3, Chamfer1.
  - Sketch2 auf der Seitenfläche x = −9,8: T-Nut, Nocken und Rastnase.
  - Danach Extrude6/7/3, Chamfer5/7 und R-Pattern2, also eine zweite Nut 10 mm weiter in −y.
  - Zuletzt Extrude4, Chamfer6, Fillet4, Chamfer2, Chamfer3.
- **Mirror1** spiegelt dann den ganzen Körper (mit allen Fasen und Rundungen) an der Fläche x = 0 und vereinigt.
- Halbes Volumen 1616,0345, ganzes 3232,0691 mm³.

## Bauweise

Nach Auftrag/README gilt: Fasen und Rundungen werden nicht gespiegelt, Gegenstücke werden direkt gebaut.

1. **Ganzer Körper von Anfang an, symmetrisch.** Es gibt weder Mirror1 noch R-Pattern2.
   - **Sketch1** (XY) ist Preds Skizze plus ihr Spiegelbild an x = 0.
     - Die Linien auf x = 0 (Preds Kurven 12 und 21) fallen weg, weil sie im ganzen Körper innen liegen.
     - Linien, die an x = 0 enden, laufen durch: Verbinder y −4,9 / −30,1 und die Linien y −2,5 / 0.
   - **Sketch2** auf der linken Seitenfläche (x = −9,8), **Sketch2 right** auf der rechten (x = +9,8).
     - Beide mit `addWithoutEdges` angelegt.
     - Die 4 Bezugslinien (Flächenrand 36,5 × 7) sind als eigene Linien gezeichnet, nicht projiziert.
     - Jede Seitenskizze enthält beide Nuten, die zweite 10 mm weiter in −y. Damit ersetzt sie R-Pattern2.
       Die Richtung −y ist belegt: Die Körper-Box bleibt nach R-Pattern2 bei y ≤ 0. Das Volumen ändert sich durch das
       Muster um −13,1584 mm³, genau Extrude6+7+3+Chamfer5+7.
2. **Features in Preds Reihenfolge**, jeweils für beide Seiten (Volumen jeweils 2 × Preds Halbkörper an derselben Stelle):
   - Extrude1 (neu, 7 mm), Extrude2 (2,5 mm), Extrude5 (2 mm).
   - Fillet1 r4, Fillet2 r2, Chamfer1 1,5, Fillet3 r1.
   - Extrude6 Schnitt 1,45 mm. Pred schneidet „bis Fläche x = −7,15 mit Versatz −1,2“, das endet bei x = −8,35
     (Chamfer7-Kanten). Ich schneide mit Abstand 1,45 = 2,65 − 1,2, die Form ist dieselbe.
   - Extrude7 (+1 mm nach innen), Extrude3 (0,75 nach außen).
   - Chamfer5 0,375, Chamfer7 0,2 (beide Nuten).
   - Extrude4 2 mm, Chamfer6 0,5, Fillet4 r3,5, Chamfer2 1 / 0,25, Chamfer3 0,2.
   - Die Extrusionen aus Sketch2 sind je Seite ein eigenes Feature, also z. B. „Extrude6“ und „Extrude6 right“. Profile
     verschiedener Ebenen gehen nicht in ein Feature.
   - Fasen und Rundungen sind je ein Feature mit den Kanten beider Seiten.
3. **Kanten:** Preds Kantenlisten aus der JSON stehen als Daten im Modul (mm → cm).
   - Das Gegenstück entsteht als Spiegelung an x = 0. Linien, die an x = 0 enden und dort mit ihrem Spiegelbild fluchten,
     werden zu einer Kante zusammengelegt.
   - Die Kanten werden mit einer Toleranz gesucht (0,002 mm, bei Nurbs über die Box), genau ein Treffer je Kante:
     - Preds Werte sind auf 4 Stellen gerundet (z. B. −5,7365).
     - `predBoxEdges.matchItems` rastert ohne Toleranz.
   - Tangentenketten wie bei Pred (`isTangentChain` überall true).
4. **Skizzen voll bestimmt:**
   - Gezeichnet wird mit `WorldSketch`/`sketchChain` als planarer Graph: Linien sind an jedem T-Punkt geteilt, es gibt
     keine überlappenden Doppel-Linien (Pred hat in beiden Skizzen deckungsgleiche Kurven).
   - **Sehne der Rastnase:** Ihre Enden liegen auf dem Kreis d 3,8. Die Kette kann „Punkt auf Kreis“ nicht. Die Sehne wird
     nach `close()` wie bei Pred angehängt: waagrecht, beide Enden koinzident auf dem Kreis, Abstand 1,4 zur Kreismitte.
     Das sind 4 Freiheitsgrade und 4 Bedingungen.
   - Hilfslinien:
     - Preds Konstruktionslinien zur Höhenmitte und zur Kreismitte übernehme ich.
     - Die Hilfslinie 8 hängt an einem projizierten Bezugspunkt und fällt weg (sie trägt keine Form).
5. **Joint origin** *Latch joint origin* wie in `r28_extract`:
   - am `originConstructionPoint`;
   - Z = `yConstructionAxis`, X = `xConstructionAxis`, Winkel 180°.
6. **Gemeinsame Werkzeuge:** keine Änderung.
   - Die Flächenskizze nutzt `WorldSketch` über einen kleinen Adapter im eigenen Modul, der `addWithoutEdges` statt
     `add` aufruft.

## Dateien

- `lib/gridfinityUtils/predLatch.py`:
  - Fusion-freie Daten und Geometrie: Kurven, Profil-Boxen, Kanten mit Spiegeln/Zusammenlegen, Toleranz-Abgleich.
  - `createLatch(component) -> [body]`.
- `tests/test_pred_latch.py`:
  - beide Skizzen voll bestimmt (`sketchChain.rank` = Variablenzahl), planarer Graph (kein Punkt im Inneren einer
    anderen Linie);
  - Sehne mit 4 unabhängigen Bedingungen;
  - Profilflächen × Höhen = 2 × Preds Volumenzuwachs je Extrude;
  - Kantenzahlen je Feature, Spiegeln/Zusammenlegen, Abgleich;
  - per `ast`: keine Mirror-/Pattern-Features, kein `userParameters`, `addWithoutEdges`, Körpername `Latch`, Joint
    origin.
- `fusion-auftraege/r29_latch_build.py`, ein Lauf in einem neuen Dokument (Hybrid):
  - Lädt den Code aus diesem Worktree und baut den Riegel in eine neue Komponente.
  - Importiert `resources/predBox/latch.f3d` (Preds Teil, Teil-Rahmen = Welt) als Gegenprobe.
  - Prüft:
    - Boole-Differenz in beide Richtungen (Rest ≤ 0,05 mm);
    - Volumen 3232,0691 auf 0,001;
    - jede Skizze `isFullyConstrained`;
    - Zeitleiste ohne Fehler/Warnung;
    - Joint origin gegen den der `.f3d` (Ort, Z- und X-Richtung).
  - Dazu Volumen je Schritt gegen 2 × Pred. Log `r29_latch_build.log`, Ziel < 50 s.

## Abweichungen (nur Aufbau, Form gleich)

- Keine Mirror1/R-Pattern2-Features: Gegenstücke und zweite Nut sind direkt gebaut, deshalb zwei Seitenskizzen.
- Extrude6 mit Abstand statt „bis Fläche + Versatz“.
- Hilfslinie 8 entfällt.
- Doppelte Kurven entfallen, und es gibt keine Mittellinie x = 0.

Falls die direkte Bauweise in Fusion scheitert, wäre die Alternative Preds Körper-Spiegelung wie beim Griff in R28. Die
spiegelt aber Fasen und Rundungen mit und braucht deshalb eure Freigabe.

## Ergebnis (17.11.2026)

- pytest: 1389 grün, davon 26 in `tests/test_pred_latch.py`. Mutationsprobe: alle sieben Mutationen gefunden.
- Review per Opus-Subagent:
  - Am Modul keine Funde. Die Kantenlisten sind per Skript gegen die Walk-JSON abgeglichen.
  - Zwei Funde am Fusion-Job (Volumen-Genauigkeit, Körper nach dem Zurückrollen) sind vor dem Lauf behoben.
- Fusion `r29_latch_build.py` Lauf 1 (`r29_latch_build.l1.out`): **BESTANDEN** in 14,9 s.
  - Volumen 3232,0691. Kein Restkörper gegen `latch.f3d`. Flächen und Kanten 323/820 wie bei Pred.
  - Sketch1, Sketch2 und Sketch2 right sind voll bestimmt. Die Zeitleiste mit 26 Schritten ist gesund.
  - Das Volumen nach jedem Feature ist gleich 2 × Preds Halbkörper (größte Abweichung 0,0001).
  - Der Joint origin stimmt in Ort, Achsen und Winkel 180° mit dem aus `latch.f3d` überein.
