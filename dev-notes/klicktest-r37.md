# Klicktest Runde 37 – Label-Farben auf eigene Filamente (p301)

Add-in aus `D:\Entwicklung\Gridfinity\wt-r37` laden. Spec: `dev-notes/specs/2026-11-18-r37-export-filaments.md`.
Vor dem Test die gemerkten Export-Einstellungen sichern: `wt-r37\commands\commandExport\commandConfig\*` (falls da).

## A – Altes gemerktes colorIndex
1. In `commandConfignfig.ini`, Abschnitt `[Export]`) `colorIndex = 4` eintragen, `labelFilaments`
   entfernen (falls vorhanden). Ein Bin mit **Outline**-Label ohne Farbe bauen.
2. Bin wählen, Rechtsklick › Export (bzw. Utilities › Export), Format 3MF, **Color label text** an.
   - Erwartet: Gruppe **Label filaments** mit genau einem Eintrag *Text without color* = **4**. Kein Feld
     „Label color index“ mehr.

## B – Zwei Farben automatisch
1. Zwei weitere Bins bauen, Label **Embossed**, **Label color** *Red* bzw. *Blue*.
2. Export öffnen, **All Gridkeeper parts** an.
   - Erwartet: *Text without color* = 4, *Red text* = 2, *Blue text* = 3 (Reihenfolge wie gefunden). Tooltip der Gruppe
     nennt Filament 1 als Filament der Teile.
3. **Color label text** aus.
   - Erwartet: Gruppe **Label filaments** und **Purge tower area** verschwinden. Wieder an: beide wieder da.
4. Format STL. Erwartet: Gruppe weg. Zurück auf 3MF.

## C – Ändern, Auswahl wechseln, merken
1. *Blue text* auf **5** stellen.
2. **All Gridkeeper parts** aus, nur den blauen Bin wählen.
   - Erwartet: nur *Blue text* = **5** (geänderter Wert bleibt).
3. Wieder **All Gridkeeper parts** an.
   - Erwartet: *Text without color* 4, *Red text* 2, *Blue text* 5; kein Spinner springt beim Klicken weg.
4. OK, Export in einen Testordner.
   - Erwartet: Meldung nennt „Label text of 3 parts: Text without color on filament 4, Red text on filament 2, Blue
     text on filament 5.“ (Reihenfolge wie im Dialog).
5. Export erneut öffnen.
   - Erwartet: dieselben Nummern (4, 2, 5) – gemerkt. In `commandConfig` steht `labelFilaments = none=4,D02020=2,2060D0=5`
     (Reihenfolge egal).

## D – Gemerkte Farbe nicht in der Auswahl
1. Nur den roten Bin wählen, *Red text* auf **3** stellen, exportieren.
2. Export erneut, alle Teile.
   - Erwartet: *Red text* 3, *Blue text* 5 (blieb gemerkt, obwohl nicht exportiert), *Text without color* 4.

## E – 3MF im Slicer
1. Datei aus C.4 in Bambu Studio oder OrcaSlicer öffnen, Filamentliste auf mindestens 5 Filamente.
   - Erwartet: Bins in Filament 1, Outline-Buchstaben in 4, roter Text in 2, blauer Text in 5.

## F – Aufräumen
- Gesicherte `commandConfig` zurückspielen, Testdokument ohne Speichern schließen.
