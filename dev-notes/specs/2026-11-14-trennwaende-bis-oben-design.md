# Trennwände auf Rasterlinien bis zur Oberkante — Kurz-Spec

Stand 2026-11-14, von Jörg freigegeben („Ja, freigegeben“). Listenpunkt p17
„Trennwände auf Rasterlinien bis zur Oberkante hochziehen“. Liegt vorerst außerhalb des Forks,
weil Runde 2 im Fork-Ordner arbeitet; die umsetzende Runde übernimmt die Datei nach
`dev-notes/specs/` im Fork.

## Warum
Jörg (zur 4x2-Bin mit Fächern): „Ich kann einen 4x2 auch auf zwei 2x2 draufstellen. Wo gehen
denn da die Wände rein.“ Die Füße einer Bin haben auf jeder Rasterlinie eine V-förmige Rille.
Trennwände genau auf einer Rasterlinie können deshalb bis zur Oberkante gehen, wenn sie oben im
Profil des Stapelrands auslaufen – heute enden alle Trennwände unter dem Stapelrand (wie bei
Gridfinity Rebuilt), der Platz darüber ist verschenkt.

## Entscheidungen
- Option im Bin-Dialog: Haken „Trennwände bis oben (auf Rasterlinien)“, Standard **aus**
  (Jörg: „optional mittels anhaken“). Ohne Haken ändert sich nichts.
- Mit Haken: Trennwände, die genau auf einer Rasterlinie liegen, gehen bis zur Oberkante und
  laufen oben im Profil des Stapelrands spitz aus, sodass die Füße einer gestapelten Bin darüber
  passen.
- Trennwände neben dem Raster (z. B. 3 Fächer auf 4 Einheiten, halbe Zellen) bleiben auch mit
  Haken unten.
- Alle neuen Skizzen vollständig bestimmt; Parameteränderungen (`gfBaseWidth` …) führen die
  erhöhten Trennwände mit.

## Prüfung
- Unit-Tests für die Auswahl „Trennwand auf Rasterlinie ja/nein“ (inkl. Half-Grid, ungleiche
  Fächer, zusammengefasste Zellen).
- Snapshot-Fall: Jörgs 4x2 (hinten 1x2 + 2×1x1, vorne 1x4) mit Haken; bestehende Fälle unverändert.
- Constraint-Check aller Skizzen.
- Stapeltest in Fusion: eine 4x2-Bin auf der neuen Bin platziert – keine Überschneidung mit den Füßen.

## Nicht-Ziele
- Kein Hochziehen der Trennwände neben dem Raster, keine Änderung des Standardverhaltens.
