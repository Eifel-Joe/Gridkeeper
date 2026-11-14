# Runde 8 – Verrundung der hochgezogenen Trennwände bis oben

Stand 2026-11-14. Ergänzt `2026-11-14-trennwaende-bis-oben-design.md` (p17) und `2026-11-14-runde-7-design.md`.
Punkt p83 „Hochgezogene Trennwände bis an den Rand und mit Verrundung bis oben“.

## Jörgs Wunsch (nach dem Handtest von Runde 7)
„Wäre halt schön, wenn die Top-Divider auch bis zum Rand gehen würden und nicht so. Außerdem auch die Verrundung bis
oben so wie es in den Ecken auch ist.“ Später: „Bedenke, dass die Fase der Außenwand zur Trennwand hin mit laufen muss
und zum Ende der Verrundung ausläuft.“

## Befund
- **„Bis zum Rand“:** Die hochgezogene Wand läuft schon bündig bis zur Außenkante des Stapelrands (gemessen an
  `bin_3x2x3_dividers_to_top_3_columns_part` und Jörgs Nachbau mit Scoop und Cullenect-Tab: Wand massiv bis zur
  Außenfläche, volle 1,18 mm bis 19,8 mm; die Fuß-Schnitte nehmen dort nichts weg, die Wand liegt 0,28 mm neben der
  Rasterlinie und die Lücke zwischen den Füßen ist breiter). Die „Kerbe“ auf Jörgs Bild ist der Cullenect-Einleger,
  der im selben Dokument am Ursprung liegt und 461 mm³ in der Bin-Ecke steckt (nur lesend gemessen). Ohne Einleger
  keine Kerbe, wie Jörg selbst gesehen hat. Keine Änderung nötig.
- **Verrundung:** Die Fach-Verrundungen (2,55 mm) kommen nur von den Fach-Ausschnitten und enden 0,5 mm unter der alten
  Trennwandoberkante. Darüber stößt die hochgezogene Wand scharfkantig an Wand, Fase unter dem Stapelrand und Rand.

## Entscheidung
Jede Ecke, deren beide Seiten bis oben gehen (hochgezogene Trennwand oder Außenwand, nicht zwei Außenwände), bekommt
nach dem Zusammenfügen der Bin eine Fusion-Verrundung entlang der Kantenkette von der Oberseite der Fach-Verrundung bis
zur Oberkante: Wand, Fase, Rand. Die Fase läuft so um die Verrundung herum und endet mit ihr. Radius 0,05 mm unter dem
der Fach-Verrundung (gleich groß lässt Fusion scheitern, ASM_INCONS_FACE). Eine Verrundung, die Fusion nicht schafft,
bleibt scharf und wird geloggt, die Bin bleibt gültig.

Verworfen (Jörg gezeigt): Eckstücke vom Radius, beschnitten vom Rand (Ecke im Rand bleibt scharf) bzw. von den Füßen
(Hinterschnitte oben).

## Prüfung
- Unit-Tests: Auswahl der Ecken (`filletCorners`), Kanten einer Ecke (`isCornerChainEdge`) mit in Fusion gemessenen
  Koordinaten.
- Fusion: alle Trennwand-bis-oben-Fälle gesund, alle Ecken verrundet (8/8/8/12/4), Parameterfall (`gfBaseWidth` 40 mm)
  gesund. Stapeltest 4×2 und 2×2 auf jeder Lage: 0 mm³, Gegenprobe 0,3 mm tiefer > 0.
- Neuer Fall `bin_3x2x3_dividers_to_top_3_columns_tab_scoop_part` (Jörgs Bin). Snapshots der Trennwand-bis-oben-Fälle
  ändern sich (Volumen +), sonst keine.

## Nicht-Ziele
Keine Änderung der Trennwandform selbst, kein Hochziehen neben dem Raster, Einleger-Platzierung des Label-Befehls
bleibt (eigener Punkt, falls gewünscht).
