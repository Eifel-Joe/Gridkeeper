# Runde 8 – Verrundung der hochgezogenen Trennwände bis oben

Stand 2026-11-14. Ergänzt `2026-11-14-trennwaende-bis-oben-design.md` (p17) und `2026-11-14-runde-7-design.md`.
Punkt p83 „Hochgezogene Trennwände bis an den Rand und mit Verrundung bis oben“.

## des Nutzers Wunsch (nach dem Handtest von Runde 7)
„Wäre halt schön, wenn die Top-Divider auch bis zum Rand gehen würden und nicht so. Außerdem auch die Verrundung bis
oben so wie es in den Ecken auch ist.“ Später: „Bedenke, dass die Fase der Außenwand zur Trennwand hin mit laufen muss
und zum Ende der Verrundung ausläuft.“

## Befund
- **„Bis zum Rand“:** Die hochgezogene Wand läuft schon bündig bis zur Außenkante des Stapelrands (gemessen an
  `bin_3x2x3_dividers_to_top_3_columns_part` und des Nutzers Nachbau mit Scoop und Cullenect-Tab: Wand massiv bis zur
  Außenfläche, volle 1,18 mm bis 19,8 mm; die Fuß-Schnitte nehmen dort nichts weg, die Wand liegt 0,28 mm neben der
  Rasterlinie und die Lücke zwischen den Füßen ist breiter). Die „Kerbe“ auf des Nutzers Bild ist der Cullenect-Einleger,
  der im selben Dokument am Ursprung liegt und 461 mm³ in der Bin-Ecke steckt (nur lesend gemessen). Ohne Einleger
  keine Kerbe, wie Nutzer selbst gesehen hat. Keine Änderung nötig.
- **Verrundung:** Die Fach-Verrundungen (2,55 mm) kommen nur von den Fach-Ausschnitten und enden 0,5 mm unter der alten
  Trennwandoberkante. Darüber stößt die hochgezogene Wand scharfkantig an Wand, Fase unter dem Stapelrand und Rand.

## Entscheidung
Jede Ecke, deren beide Seiten bis oben gehen (hochgezogene Trennwand oder Außenwand, nicht zwei Außenwände), wird nach
dem Zusammenfügen der Bin von der Oberseite der Fach-Rundung bis zur Oberkante gerundet: Der Querschnitt der Fach-Ecke
(Quadrat minus Viertelkreis, gleicher Radius, gleiche Lage) wird ohne Drehung entlang der Kantenkette Wand → Fase →
Rand nach oben geschoben (Sweep, parallele Ausrichtung) und mit den Füßen einer aufgesetzten Bin beschnitten. So geht
die untere Rundung ohne Absatz in die obere über, die Fase läuft um die Ecke mit und endet an der Trennwand.
Ist die Kantenkette nicht durchgehend (Wand dicker als der Rand: waagerechter Absatz dazwischen) oder scheitert der
Sweep, bekommt die Ecke eine Fusion-Verrundung (Radius 0,05 mm unter der Fach-Ecke, bei ASM_BL_CAP_COMPLEX 80 / 60 /
40 %); gelingt keine, bleibt sie scharf und es wird geloggt, die Bin bleibt gültig.

Verworfen (Nutzer gezeigt bzw. von ihm gefunden): Eckstücke beschnitten vom Rand (Ecke im Rand bleibt scharf) bzw. von
den Füßen (Hinterschnitte oben); Fusion-Verrundung als Hauptweg (des Nutzers Handtest: Sichel von 0,36 mm² auf der Fach-Ecke,
weil die Kugel dem 0,5 mm kurzen Wandstück unter der Fase nicht folgen kann).

## Prüfung
- Unit-Tests: Auswahl der Ecken (`filletCorners`), Kanten einer Ecke (`isCornerChainEdge`) mit in Fusion gemessenen
  Koordinaten.
- Fusion: alle Trennwand-bis-oben-Fälle gesund, alle Ecken verrundet (8/8/8/12/4), Parameterfall (`gfBaseWidth` 40 mm)
  gesund. Stapeltest 4×2 und 2×2 auf jeder Lage: 0 mm³, Gegenprobe 0,3 mm tiefer > 0.
- Ohne Fall, einmal in Fusion (des Nutzers Bin mit Tab abgewandelt): Wand 0,4 mm und Notches ohne Absatz, alle Ecken per
  Sweep. Wand 2,0 / 3,0 mm: Kantenkette unterbrochen, alle Ecken per Verrundung (1,8 / 1,44 bzw. 1,8 / 0,72 mm), dabei
  Absätze von 0,2–0,7 mm² – bekannte Grenze, Punkt p101. Stapeltest überall 0 mm³, Gegenprobe 0,3 mm tiefer > 0.
- Snapshot-Lauf meldet bei Trennwand-bis-oben-Fällen jeden Absatz (nach oben zeigende Fläche ≥ 0,01 mm², ≤ 3 mm) im
  oberen Bereich als Fehler (vorher rot: 8 bzw. 4 Sicheln von 0,36 mm²).
- Neue Fälle `bin_3x2x3_dividers_to_top_3_columns_tab_scoop_part` und `…_tab_part` (des Nutzers Bin aus dem Handtest). Snapshots der Trennwand-bis-oben-Fälle
  ändern sich (Volumen +), sonst keine.

## Nicht-Ziele
Keine Änderung der Trennwandform selbst, kein Hochziehen neben dem Raster, Einleger-Platzierung des Label-Befehls
bleibt (eigener Punkt, falls gewünscht).
