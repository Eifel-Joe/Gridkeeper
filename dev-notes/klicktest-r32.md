# Klicktest Runde 32 – ältere Bins mit ihren alten Einstellungen (p280)

Add-in aus `D:\Entwicklung\Gridfinity\wt-r32` laden, neues Dokument.
Testdateien: `dev-notes/specs/testdateien/r32-alte-bin.json` (Bin im Config-Stand 13.11., ohne die sechs späteren
Felder, geschalt, mit Tab und Label „R32 old“) und `r32-alte-baseplate.json` (Grid units 2×2, xy-Spiel 0,4 mm, ohne
Plattenspalt, mit dem entfernten `fitTolerance`).

## A – Bin: Load from file über einen „Gegenteil“-Dialog
1. Bin-Dialog öffnen. Einstellen: Lip type **Full**, **Trim lip top** aus, **Dividers up to the top on grid lines**
   an, Label color **Red** (Tab an, damit die Farbe wählbar ist).
2. „Load from file“ → `r32-alte-bin.json`.
   - Erwartet: Lip type **Light**, Trim lip top **an**, Dividers up to the top **aus**, Label color **None**,
     Größe 2×1×4, Shelled, Label „R32 old“.
   - Erwartet: Der Hinweis nach dem Laden nennt **keins** der sechs Felder unter „Not in the file, kept the current
     value“ (dort stehen nur Felder, die es schon gab und die der Datei nicht fehlen – hier keine).
3. OK. Im Fusion-Log (`commonUtils.fileLog`) bzw. „Show settings“ des Körpers: `isShellRounded` **False**,
   `cullenectSocketOffset` **0.3**, `labelColor` leer.

## B – Neubau einer alten Bin
1. Die Bin aus A per Rechtsklick „Gridfinity rebuild“ öffnen, im Dialog vorher nichts ändern; dazu den Dialog-Zustand
   aus A1 (Full, Trim aus, Dividers an, Red) **nicht** übernehmen – der Neubau liest das Tag.
   - Erwartet: dieselben Werte wie A2, OK baut eine gleiche Bin. Rebuild-Log: „no changes to its config“ (die Altwerte
     erscheinen nicht als `None -> …`).
   (Das Tag einer echt alten Bin hat die Felder nicht; die Bin aus A hat sie schon. Der Pfad ist per pytest belegt:
   `test_rebuild_fills_the_older_values_into_a_tagged_config`, `test_rebuild_log_compares_with_the_older_values`.)

## C – Baseplate
1. Baseplate-Dialog öffnen, **Plate edge clearance** auf 0,05 mm.
2. „Load from file“ → `r32-alte-baseplate.json`.
   - Erwartet: Bin xy clearance **0,4 mm**, Plate edge clearance **0,4 mm**. Hinweis: „Not recognised, skipped:
     fitTolerance“.
   - Erwartet: OK ist **frei** (die Grenze liegt jetzt bei 0,5 mm). Tooltip der Plate edge clearance nennt
     „[0.025, 0.5]mm“.
3. Plate edge clearance von Hand auf 0,6 mm: OK gesperrt. Auf 0,5 mm: OK frei.

## D – Gegenprobe p151 (bleibt für Felder, die es damals gab)
1. Bin-Dialog, Wall thickness 1,6 mm. „Load from file“ → `handtest-10-alte-bin-ohne-farbe.json` (nur Größe).
   - Erwartet: Wall thickness bleibt 1,6 mm, der Hinweis listet sie unter „Not in the file, kept the current value“.
