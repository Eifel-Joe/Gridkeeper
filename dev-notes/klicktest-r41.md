# Klicktest Runde 41 – Längenfelder formatiert (p291)

Add-in aus dem Worktree `wt-r41` laden. Spec: `dev-notes/specs/2026-11-18-r41-dialog-inputs.md`.
Tippweise: Feld anklicken, Inhalt markieren, tippen, dann **Tab** (nicht direkt OK). Nach Tab etwa 1 s warten und
den Feldtext ablesen.

## A – Bin
1. Bin-Dialog öffnen, **Bin wall thickness** auf `2.9` → Tab.
   - Erwartet: Feld zeigt `2.90 mm`.
2. Dasselbe Feld `2.9 mm` → Tab. Erwartet: `2.90 mm`.
3. Dasselbe Feld `1 + 1.5` → Tab. Erwartet: bleibt `1 + 1.5` (Formel nicht umgeschrieben).
4. Dasselbe Feld `0.1 in` → Tab. Erwartet: bleibt `0.1 in`.
5. **Tab overhang angle** `40` → Tab. Erwartet: unverändert wie getippt (Winkel werden nicht umformatiert).
6. **Bin height, Z (u)** `3.5` → Tab. Erwartet: unverändert wie getippt (Feld ohne Einheit).
7. Wandstärke wieder `2.9` → Tab, dann OK.
   - Erwartet: Bin entsteht ohne Fehler, Wand 2.9 mm (Messen oder Parameter). Kein Hängen, kein Flackern im Feld
     (keine Endlosschleife).

## B – Baseplate
1. Baseplate-Dialog, **Bin xy clearance (mm)** `0.3` → Tab. Erwartet: `0.30 mm`.
2. **Magnet cutout diameter** `6.5` → Tab. Erwartet: `6.50 mm`. Cancel.

## C – Box
1. Box-Dialog, **Magnet cutout depth** `1.2` → Tab. Erwartet: `1.20 mm`. Cancel.

## D – Label
1. Label-Dialog, **Base width unit (mm)** `42.5` → Tab. Erwartet: `42.50 mm`. Wieder `42` → Tab, Cancel.

## E – Export
1. Ein Teil wählen, Export, Format 3MF. **Spacing** `3` → Tab. Erwartet: `3.00 mm`.
2. **Bed width, X** `250` → Tab. Erwartet: `250.00 mm`, Auswahl **Printer** springt wie bisher auf „Custom“
   (bzw. bleibt, wenn der Wert zum Drucker passt). Cancel.

## F – Wiederöffnen
1. Bin-Dialog erneut öffnen. Erwartet: Wandstärke zeigt den zuletzt benutzten Wert formatiert (`2.90 mm`).
