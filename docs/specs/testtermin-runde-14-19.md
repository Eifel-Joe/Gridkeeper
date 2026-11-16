# Testtermin Runde 14–19

Stand 16.11.2026. Sammelbranch `runde-14-18` (Merge-Commit 79e559c), `master` unverändert auf b367997.
Jede Runde: pytest grün (zuletzt 910), Ende-zu-Ende in Fusion grün, Snapshot-Tests 83/83 grün, Opus-Review ohne
offene Funde. Details je Runde: `docs/specs/runde-NN-uebergabe.md`.

**Vor dem Test:** Fusion neu starten (das Add-in lädt den ausgecheckten Stand des Fork-Ordners). Zum Testen den
Sammelbranch im Fork-Ordner auschecken lassen – das macht die Hauptsitzung auf dein Wort.

## Was drin ist

| Runde | Punkte |
|---|---|
| 14 | p72, p120, p71: Beschriftung nach Textänderung (Buchstaben bleiben auf der Lasche, eingefärbt, mit Namen) |
| 15 | p35 Cullenect erst ab 1,2 mm Wand; p170 Joint Origins folgen dem Raster; p60 Taschen bei Fächern neben dem Raster; p101 Trennwand-Ecken nahtlos bei 2–3 mm Wand |
| 16 | p30, p34 Snapshot-Tests; p32, p33 Einstellungen zeigen gebaute Laschenbreite und Sockel; p31 Vorschaubilder |
| 17 | p110 Unterlängen; p140 Rand bei „vertieft“; p52 Luft vor dem Symbol; p51 Symbole schneller (Nylonmutter 23,7 s → 2,9 s); p180 Symbole in Bin-Labels |
| 18 | p150 Einleger per Rechtsklick neu bauen, Einstellungen speichern/laden/klonen; p151 Label-Farbe bei alten Configs |
| 19 | p181 Bin-Label-Text beim Verlängern; p210 Umlaute (gemessen, passt, nichts gebaut) |

Offen geblieben: p53 „Mehrfarbdruck: Text und Symbol sind mehrere Körper“ (Slicer-Prüfung, Handtest 4).

## Fragen an dich

1. **Zweizeilig vertieft (R17):** verbieten oder die kleine Kerbe durch Unterlängen hinnehmen? Mit Randabstand ginge
   zweizeilig vertieft in Regular und Bold gar nicht mehr. Gebaut ist: nur das Symbol hält Abstand.
2. **Hinweis bei langen Texten (R17):** Der alte p130-Hinweis greift bei Heavy erst unter 2,79 mm, die Untergrenze
   liegt bei 3,05 mm. Soll er der Untergrenze folgen?
3. **Einleger ohne Symbol, schmaler gestellt (R17):** Text reicht bei −1 mm Breite an den rechten Rand. Auch 1 mm Luft?
4. **Zwei Zeilen Regular/Bold (R17):** werden ab etwa −0,45 / −0,57 mm Höhenkorrektur gesperrt (vorher mit
   überstehenden Unterlängen gebaut). Recht so?
5. **Zu langer Bin-Label-Text (R19):** wird beim Bauen abgelehnt, die Meldung nennt ihn. Reicht das, oder soll der
   Dialog OK vorher sperren (nur über geschätzte Textbreite möglich)?
6. **Schrift beim Parameter-Ändern nachführen (R19):** Fusion-Ausdrücke können die Textlänge nicht lesen. Möglich wäre
   ein Add-in-Ereignis nach „Parameter ändern“ (eigener Undo-Schritt, nur mit geladenem Add-in). Gewünscht?
7. **Alte Bins mit sehr kleiner Schrift (R19):** werden beim Neubau abgelehnt, reine Parameteränderungen gehen weiter.
   Recht so?
8. **Joint beim Einleger-Neubau (R18):** entsteht neu; eigene Verweise auf den alten Joint gehen verloren. Recht so?
9. **Parameternamen (R18):** `gfLabel2_text1` – von dir schon mit „Passt so“ beantwortet.

## Handtest-Liste

Bin und Beschriftung
1. Zwei Bins mit Label (graviert, farbig erhaben, eine gekippt) plus Fach-Label, Text-Parameter um drei Buchstaben
   verlängern: alles bleibt auf der Lasche, farbig in „Text“ und in der Farbe (R14).
2. Bin mit Sechskantmutter und Text, Basisbreite ändern: Icon und Text wandern zusammen (R14).
3. Bin 2x1 mit zwei Fächern, Label „Bolzen“ Bold, Text-Parameter um „ M4x2“ verlängern, Rechtsklick „Gridfinity
   rebuild“, OK: Schrift kleiner, in jedem Fach auf dem Label (R19).
4. 3MF-Export einer farbigen Bin in Bambu Studio: Buchstaben als ein Teil oder einzeln? (p53)
5. Bin mit Label „Cullenect nut nylon“ und langem Text, Text verlängern: Symbol bleibt an seiner Stelle (R17).
6. Bin-Dialog, Cullenect, Wand 1,1 mm: OK gesperrt, Cullenect-Zeile nennt „at least 1.2 mm“; 1,2 mm: OK frei (R15).
7. Bin 4x2 und Grundplatte 3x3 mit Joint Origins, Basisbreite auf 50 mm: Joint Origins in den Zellmitten, ein Joint
   Bin–Grundplatte sitzt weiter (R15).
8. Bin mit Trennwänden bis oben, 3 mm Wand (über Konfiguration): Ecken durchgehend gerundet (R15).
9. Bin mit 8 gleichen Fächern, Cullenect, Rechtsklick „Gridfinity settings“: gebaute Laschenbreite (≥ 14 mm) und
   „1U: 8 sockets, …“ (R16).
10. Bin-Dialog ohne Lasche, Label-Farbe Rot, alte Bin-Config ohne Label-Farbe laden: Farbe bleibt Rot (R18).

Einleger
11. Nach Fusion-Neustart öffnen sich die Dialoge Bin, Baseplate und Label (per Skript nicht prüfbar, R18).
12. Einleger 1U, zwei Zeilen „gjpy“/„Agjp“, Heavy, −1 mm: Unterlängen im Einleger; in Regular meldet der Dialog
    „Two lines don't fit this height …“ und sperrt OK (R17).
13. Einleger 25 mm, Schraube, vertieft, drucken: Rand ringsum ganz, Einleger rastet ein (R17).
14. Einleger mit Nylonmutter: in wenigen Sekunden gebaut, Symbol gedruckt wie vorher (R17).
15. Text in Heavy 3,05 mm und Regular 4,43 mm in Bambu Studio (0,4-mm-Düse, Standardprofil, Arachne): bleiben Teile
    der Buchstaben leer? Prüft die Untergrenze (R17).
16. Einleger mit Tasche, Rechtsklick „Gridfinity rebuild“, anderer Text: neuer Einleger in derselben Tasche, nur einer
    (R18).
17. Rechtsklick „Gridfinity settings“ auf einen Einleger: „Save to file“ → im Label-Dialog „Load“ gleiche Werte;
    „Clone“ öffnet den Label-Dialog mit diesen Werten (R18).
18. Farbiger Einleger, Text verlängern, Rechtsklick auf einen neuen Buchstaben: „Gridfinity settings“ zeigt den
    Einleger (R14).
19. Utilities › Add-Ins › „Gridfinity tests: update snapshots“ für einen Fall (Test-Palette offen): Vorschaubild
    entsteht (R16).

## Danach

Abnahme durch dich → Hauptsitzung mergt `runde-14-18` nach `master` (dein Ja), setzt die Punkte in der Liste auf
erledigt und räumt die Runden-Branches auf (Löschen nur mit deinem Ja).
