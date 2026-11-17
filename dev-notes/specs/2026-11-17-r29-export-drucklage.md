# r29-export: Drucklage, Druckbett, Verteilen, Abstand, Purgetower (Gridkeeper 1.1.0)

Stand: 17.11.2026, Entscheidungen D1–D4 von Jörg, Spec und Plan von Jörg freigegeben (17.11.2026).

## Problem
Der 3MF-Export (`lib/threeMf.py`, `placeOnPlate`) setzt jedes Teil auf z=0 und lässt die x/y-Lage wie in der
Konstruktion. Box-Sätze landen übereinander in Einbaulage (Deckel nicht umgedreht, Riegel hochkant). Mehrere Bins oder
Baseplates liegen, wie sie im Design stehen, auch über das Bett hinaus.

Jörg, 17.11.2026: „Noch in 1.1.0, mit Druckbett-Auswahl. Auch für die 3MF bei Bins und Baseplates wichtig. Ebenso
Labels. Natürlich nur wenn es mehrere Druckteile sind. Auch wichtig ist ein Abstand der Teile zueinander, gerne
einstellbar. Und bei zweifarbigem Export auch eine freie Fläche für den Purgetower.“

## Anforderungen
1. **Drucklage je Rolle.** Die Regel gilt im Rahmen des Teils, also in seiner eigenen Komponente. Sie gilt damit für alle
   Sitze gleich, auch für die vier Riegel.

   | Rolle | Drehung im Teil-Rahmen | Beleg |
   |---|---|---|
   | Bin, Baseplate | keine, sie bleiben stehend wie im Design | Auftrag |
   | Cullenect-Label, Stil `Flush` | 180° um X, Schrift aufs Bett | Jörg 17.11.: „Flush kommt auf die Schrift alle anderen auf die Unterseite, wie sie auch eingebaut werden.“ |
   | Cullenect-Label, `Embossed`/`Debossed` | keine, Unterseite aufs Bett (Einbaulage) | ebenda |
   | Box-Schild | wie Cullenect-Label nach seinem Stil (`predBoxLabel.SURFACES`) | Annahme, Jörg bestätigt beim Testtermin |
   | Box (`Base`) | keine | Boden unten |
   | Deckel (`Lid`) | keine, Einbaulage (D1, Jörg 17.11.) | Jörg |
   | Latch | keine: der Teil-Rahmen liegt flach, z 0…7 | Preds Datei, `dev-notes/r29/latch.md` |
   | Handle | +90° um X, flach, 7 mm hoch | hergeleitet: Preds Griff ist 7 mm dick |
   | Handle pin | keine, liegt auf der Abflachung | hergeleitet |
   | Hinge, alle drei Varianten: Hälften | keine, stehend; beide Hälften behalten ihre Lage zueinander | Jörg 16.11.: „Scharniere in Druckposition belassen“ |
   | Hinge Pinned: `Hinge pin` | −90° um X, Abflachung aufs Bett, eigenes Teil | hergeleitet |

   Die Rolle kommt aus der Teil-Rolle der Komponente (`partRoleOf`). Bei Box und Deckel ohne Satz kommt sie aus den
   Körpernamen `Base` und `Lid`.
2. **Druckbett-Auswahl** im Export-Dialog. Die Vorgaben stammen aus `commandCreateBaseplate/printBeds.py` (dieselbe
   Liste wie im Baseplate-Dialog), dazu „Custom“ mit Breite und Tiefe. Vorgabe ist Bambu Lab A1, P1, X1 (256 × 256 mm).
3. **Verteilen.** Die Teile werden zeilenweise nach ihrer Grundfläche auf das Bett gelegt, die größten zuerst. Passt
   ein Teil nur quer, wird es um 90° um Z gedreht. Was nicht mehr auf die Platte passt, kommt auf die nächste. Ein Teil,
   das größer ist als das Bett, kommt allein auf eine Platte, und die Zusammenfassung im Dialog nennt es.
   Gruppen wie die Scharnierhälften werden als ein Block verteilt.
4. **Abstand** zwischen den Teilen und zum Bettrand ist einstellbar. Vorgabe 5 mm (D2, Jörg 17.11.).
5. **Purgetower.** Ist „Color label text“ an, bleibt hinten rechts ein Quadrat frei. Größe 50 × 50 mm, einstellbar (D2, Jörg 17.11.). Gilt auf jeder Platte.
6. **Merken.** Bett, Breite, Tiefe, Abstand und Purgetower-Größe werden wie die übrigen Wahlen in der
   Export-Konfiguration gespeichert (`readChoices`/`saveChoices`).
7. **Nur bei mehreren Teilen.** Ein einzelnes Teil wird nur in Drucklage gedreht und in die Bettmitte gesetzt.

## Umsetzung
- Neues Fusion-freies Modul `lib/printLayout.py` mit Drehregeln, Verteilen und Plattenaufteilung, Einheit mm wie
  `threeMf.MeshObject`. Unit-Tests in `tests/test_print_layout.py`.
- `threeMf.write` schreibt die schon gelegten Objekte. `placeOnPlate` bleibt nur für den alten Aufruf.
- `commandExport/entry.py`:
  - Für Teile eines Satzes vernetzt `meshOf` den Körper im Teil-Rahmen und dreht ihn nach seiner Rolle.
  - Alle anderen Teile laufen wie bisher über `transform2`.
  - Neu sind die Dialog-Eingaben und das Speichern.
- Mehrere Platten: **eine 3MF je Platte**, „<Name>, plate N.3mf“, bei einer Platte nur „<Name>.3mf“. Jörg 17.11.2026
  nach der Plattenprobe: „Eine Sortierung kann ja nur bei eine 3MF je Platte anständig durchgeführt werden. Wenn alles
  in eine 3MF kommt und Bambu/Orca dann selber verteilt kommt alles durcheinander.“ Erste Wahl (D3, „Eine Datei.
  Plattengröße gemäß Eingabe.“) ist damit überholt.
  - Plattenprobe 17.11. (`notizen/r29-export-probe/LIESMICH.md`): Bambu übernimmt Platten nur aus einer Datei mit
    Bambu-Kennung **und** Projekt-Einstellungen. Diese ersetzen Drucker, Filament und Prozess.
  - Bambu und PrusaSlicer verschieben die Teile einer fremden 3MF als Gruppe in die Bettmitte (Plater.cpp
    `center_instances_around_point`). Deshalb wird der Inhalt jeder Platte schon zentriert geschrieben. Die
    Purge-Ecke wird nach dem Zentrieren geprüft. Liegt ein Teil darin, wird die Ecke größer angesetzt. Geht auch das
    nicht, nennt die Meldung die Platte.
- STL in Drucklage (je Teil gedreht, ohne Verteilen), STEP unverändert in Konstruktionslage (D4, Jörg 17.11.).

## Nicht dabei
- Kein Slicer-Projekt mit Druckereinstellungen und keine Filamentzuordnung über das hinaus, was es heute gibt.
- Keine Drehung von Bins, Baseplates und Labels. Kein Verschachteln: Teile werden nach ihren Grundflächen gelegt, es
  wird nichts ineinander gepackt.
- Keine Purgetower-Lage pro Drucker, immer hinten rechts.

## Ende-zu-Ende
1. Die Hauptsitzung lässt in Fusion den Job `fusion-auftraege/r29_export.py` laufen. Er exportiert:
   - einen Box-Satz mit Pinned-Scharnier, der den Stift mit abdeckt (die Hälften von M3x30 folgen derselben Regel);
   - einen Mix aus 2 Bins, 2 Baseplates und 2 Cullenect-Labels, eines davon Flush. Den Mix einmal auf 256 mm mit
     Bemalung und einmal auf 180 mm ohne Bemalung.
2. Bambu Studio öffnet beide fehlerfrei.
3. Alle Teile liegen in Drucklage innerhalb des 256er-Betts, mit Abstand und mit freier Purgetower-Ecke.
4. Was nicht passt, liegt in einer weiteren Datei „…, plate 2.3mf“.
