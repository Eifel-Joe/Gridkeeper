# Cullenect-Wechsel-Labels im Fusion Gridfinity Generator — Design

Stand: 2026-11-14 · Branch `feature/cullenect-labels` im Fork `Eifel-Joe/FusionGridfinityGenerator`
(Basis: upstream `master` 15c4b4d, 12 Commits nach v2.2.0.0)

## Zweck und Warum

Nutzer will Gridfinity-Teile nicht mehr aus der unübersichtlichen Flut fertiger Online-Dateien
zusammensuchen, sondern alles aus **einem** Werkzeug erzeugen: dem Fusion-Add-in
*GridfinityGenerator* (Le0Michine). Diesem fehlt genau eine Sache: **austauschbare Labels**.
Seit v2.0 kann der Generator Text/Icons nur direkt in die Lasche drucken (Outline / Engraved /
Embossed). Nutzer nutzt aber das Klick-System **Cullenect** (CullenJWebb): Einleger werden einmal
gedruckt und in eine Tasche der Bin-Lasche eingeklickt, umsteckbar zwischen Bins.

Erfolg heißt: Im Generator eine Bin mit Cullenect-Aufnahme erzeugen, im Generator den passenden
Einleger erzeugen, beides drucken — der Einleger klickt ein, sitzt fest, lässt sich wieder lösen,
und passt auch in Bins/Einleger aus dem originalen Cullenect-Ökosystem.

## Ziele

1. **Bin-Dialog:** Label-Stil-Auswahl um den Eintrag **„Cullenect“** erweitern. Die Lasche bekommt
   dann statt Text/Icon die Cullenect-v2-Tasche mit Rastrippen.
2. **Neuer Befehl „Gridfinity Label“** im Erstellen-Menü, gleichrangig zu Bin und Baseplate, der
   Cullenect-v2-Einleger erzeugt.
3. Symbolumfang = aktueller Cullenect-Umfang (siehe unten), Struktur so, dass später weitere
   Symbole (Dübel, Elektro, …) nur als zusätzliche SVG-Dateien dazukommen.

## Nicht-Ziele (jetzt)

- Zusätzliche, nicht-Cullenect-Symbole (kommen später, nur die Erweiterbarkeit ist Ziel).
- Vertikale Cullenect-Aufnahme (an der Wand statt auf der Lasche), Cullenect v1/legacy.
- Andere Label-Systeme (gflabel, Pred).
- Upstream-Pull-Request — wird später entschieden (siehe Randbedingungen).

## Anti-Ziele (wäre ein Fehlschlag, auch wenn es „funktioniert“)

- **Nicht vollständig bestimmte Skizzen.** des Nutzers harte Anforderung: jede Skizze, die der neue Code
  anlegt, ist *fully constrained*, sonst brechen Modelle beim Ändern der Parameter.
- Einleger, die nicht in Original-Cullenect-Bins passen, bzw. Taschen, die keine Original-Einleger
  aufnehmen (eigenes Inselmaß).
- Bestehendes Verhalten des Generators verändert (Outline/Engraved/Embossed, Default-Werte,
  bestehende Snapshot-Tests müssen unverändert grün bleiben).

## Randbedingungen

- **Lizenzen:** Generator CC BY-NC-SA 4.0 (Fork bleibt unter dieser Lizenz). Cullenect MIT —
  Symbole/Geometrie dürfen mit Namensnennung übernommen werden; Attribution in README/Lizenzhinweis
  des Icon-Ordners.
- **Upstream-tauglich bauen:** Code-Stil, Struktur, Testart und Namensgebung des Projekts
  übernehmen, damit ein späterer PR an Le0Michine möglich bleibt. Diese Spec liegt in `docs/specs/`
  als eigener Commit, der bei einem PR weggelassen werden kann.
- **Fusion-Dokumenttyp:** Ab Generator 2.x funktioniert auch eine Bauteil-Konstruktion (Nutzer, 14.11.:
  „Mit der aktuellen Version des Generator muss man nichts mehr umstellen auf Hybrid. Es geht jetzt
  auch in Bauteilkonstruktion.“); nur die alte App-Store-Version 1.2.7 brauchte Hybrid. Der
  Label-Befehl verhält sich wie Bin/Baseplate.
- **Installation zum Testen:** Fusion lädt den Fork per Shift+S → „+“ direkt aus
  `D:\Entwicklung\Gridfinity\FusionGridfinityGenerator`; die bisher geladene Kopie
  (`D:\Entwicklung\Gridfinity\GridfinityGenerator`, v2.2-Release) wird dafür deaktiviert, sonst
  kollidieren die Befehls-IDs.

## Referenz: Cullenect v2 (Quelle: github.com/CullenJWebb/Cullenect-Labels, README + `OpenSCAD/Cullenect.scad`, MakerWorld 446624, v2.0.2)

| Maß | Wert |
|---|---|
| Einleger Breite | 42 mm × Einheiten − 6 mm (1U = 36 mm, 2U = 78 mm) |
| Einleger Höhe (Y) | 11 mm |
| Einleger Dicke (Z) | 1,2 mm |
| Einleger-Rast (Latch) | umlaufend, XY-Einzug 0,2 mm, Z-Höhe 0,6 mm, Unterkante 0,2 mm über Einleger-Unterseite |
| Tasche | Einleger + 0,3 mm in X und Y (1U: 36,3 × 11,3 mm), Tiefe 1,2 mm |
| Taschen-Rippen | entlang X auf beiden Längsseiten, 0,2 mm XY, 0,4 mm Z, Unterkante 0,2 mm über Taschenboden |
| Text/Symbol | 0,2 mm (eine Schicht) erhaben, vertieft oder bündig |

Maßgeblich bei Widerspruch: `Cullenect.scad` (Module `cullenect_base_v2`, `cullenect_socket`)
und die Zeichnungen `Documentation/Dimensions_Cullenect_v2_*`. Nutzer stellt zusätzlich eine STEP
seiner gedruckten Einleger bereit — Passungs-Referenz zum Gegenprüfen.

## Ansätze (betrachtet)

1. **Separater parametrischer Taschen-Körper** (eigene .f3d, manuell einsetzen + kombinieren) —
   billig, aber Handarbeit pro Bin, fehleranfällig. Verworfen.
2. **Eigenes Fusion-Skript „Tasche auf gewählte Fläche“** — unabhängig vom Generator, ein Klick
   pro Bin; aber zweites Werkzeug, kein Einleger-Generator. Verworfen.
3. **Generator selbst erweitern** (Label-Stil „Cullenect“ + Befehl „Gridfinity Label“) —
   **gewählt** von Nutzer: alles aus einem Werkzeug, nutzt die vorhandene Label-/Icon-/Parameter-
   Infrastruktur von v2.x. Preis: Fork pflegen (upstream-Updates nachziehen), solange kein PR.

## Entscheidungen

### Bin: Label-Stil „Cullenect“

- Neuer Wert in der vorhandenen Label-Stil-Auswahl (`LABEL_STYLES` in
  `lib/gridfinityUtils/labelGenerator.py`), neben Outline/Engraved/Embossed.
- Ist er gewählt, werden Text- und Icon-Felder der Lasche im Dialog ausgeblendet/deaktiviert
  *(Claudes Vorschlag, von Nutzer bestätigt)*.
- Die Tasche wird in die Oberseite der Label-Lasche geschnitten, in X mittig auf der Lasche, in Y
  so, dass die Tasche vollständig auf der Laschen-Oberseite liegt *(Builder-Call: genaue Y-Lage;
  Vorgabe: mittig auf der Oberseite)*.
- **Taschenbreite:** Cullenect-Standard, abgeleitet aus der Laschenlänge in Einheiten
  (42 × n − 6 + 0,3). Für Laschen, deren Länge kein ganzzahliges Vielfaches ergibt (Fach-Laschen,
  Half-Grid), wird die Taschenbreite aus der verfügbaren Laschenlänge abzüglich Randmaß bestimmt
  *(Builder-Call: Randmaß; Vorgabe ≥ 2,65 mm wie Gridfinity Extended)*. Der Label-Generator
  muss für jede so entstehende Breite einen Einleger erzeugen können (Breite frei in mm).
- **Laschenbreite:** Bei „Cullenect“ wird die Laschenbreite auf ein Minimum angehoben, das die
  11,3-mm-Tasche plus Rand trägt *(Builder-Call; Vorgabe 14 mm wie Gridfinity Extended; Default
  des Generators ist 13 mm)*. Ist der Nutzer-Wert größer, gilt der Nutzer-Wert.
- **Rastermaß ≠ 42 mm** *(Claudes Call)*: Die Taschenbreite ist ein Ausdruck auf
  `gfBaseWidth` (`gfBaseWidth · n − 6 mm + Toleranz`), genau wie Cullenect selbst
  (`label_width * gridfinityX − 6`). Beim Standardraster 42 mm ergibt das exakt Cullenect-Maß und
  damit Kompatibilität zu Original-Einlegern; bei anderem Raster folgt die Tasche dem Raster
  (Original-Kompatibilität gibt es dann naturgemäß nicht). Die Taschenhöhe 11 mm + Toleranz ist
  rasterunabhängig.
- **Toleranz** *(Claudes Call, nach `Cullenect.scad`)*: Die Passungs-Luft sitzt **nur in der
  Tasche** (`socket_offset`, Default 0,3 mm), als Eingabe im Bin-Dialog. Der Einleger ist exakt
  nominal (36 × 11 mm bei 1U). Der Label-Befehl bekommt nur einen optionalen Korrekturwert
  `offset_xy` (Default 0 mm, wie Cullenect), um Druckerabweichungen auszugleichen — keine zweite
  Passungs-Toleranz.
- **Taschenbreite sichtbar machen** *(Claudes Call)*: Die errechnete Taschenbreite (und die
  passende Einleger-Breite) steht im Bin-Dialog in der Maß-Tabelle und unter „Gridfinity
  settings“ der erzeugten Bin, damit für Fach-Laschen-Taschen der passende Einleger ohne
  Nachmessen erzeugt werden kann.
- Laschen-Varianten, die mit der Tasche kollidieren (z. B. hohle Lasche mit zu dünner Oberseite,
  geneigte Oberseite): Tasche muss vollständig im Material liegen; wo das nicht geht, verhindert der
  Dialog die Kombination oder passt sie an *(Builder-Call, Verhalten im Dialog sichtbar machen)*.
- Gilt für die Haupt-Lasche und für Fach-Laschen (Compartments mit eigener Lasche).
- Nachträgliche Parameter-Änderungen (`gfBaseWidth`, `gfBaseLength`, `gfHeightUnit`, …) müssen die
  Tasche korrekt mitführen — wie die bestehenden Labels (siehe upstream-Commit 073efbe „Keep labels
  intact and centred when the units change“).

### Neuer Befehl „Gridfinity Label“

- Eigener Befehl unter `commands/` analog zu `commandCreateBaseplate`, eigener Eintrag im
  Erstellen-Menü mit Icon/Tooltip wie die anderen.
- **Eingaben:**
  - Breite: in Einheiten (1, 1.5, 2, …) **oder** frei in mm (für Fach-Laschen-Taschen).
  - Textzeile 1, Textzeile 2 (optional).
  - Schraubensymbol (an/aus) als Baukasten: **Kopf** (keiner, Zylinder/Socket, Senk, Rund, Linse/Pan),
    **Schaft** (Maschine, Holz), **Gewinde** (voll, teil), **Antrieb** (keiner, Schlitz, Kreuz,
    Kreuz+Schlitz, Kreuz+Vierkant, Torx, Innensechskant, Vierkant/Robertson, Dreieck),
    **Flansch** (an/aus), **Sicherheits-Pin** (an/aus).
  - Hardware-Symbol: keins oder einer der 19 Cullenect-Typen (Scheibe, Federscheibe,
    Gewindeeinsatz, Mutter, Vierkantmutter, Sicherungsmutter, T-Mutter seitlich/oben, Magnet,
    Crimp Ring/Gabel/Flachstecker/Buchse je offen/geschlossen, Stoßverbinder).
  - Oberfläche: erhaben / vertieft / bündig (Multi-Color-Druck).
  - Korrekturwert `offset_xy` (Default 0 mm), siehe Toleranz oben.
  - Rasterbreite (Default 42 mm bzw. `gfBaseWidth` des Designs, falls vorhanden), damit
    „Einheiten“ auch bei anderem Raster stimmen.
- **Layout** wie Cullenect (`cullenect_label_generate`): Text links, Schraubensymbol bzw.
  Hardware-Symbol rechts.
- **Ausgabe** *(Claudes Call, für Mehrfarbdruck)*: je Aufruf eine eigene Komponente, platziert
  wie Bins/Baseplates (freier Platz nahe Ursprung), Druckausrichtung flach. Darin **zwei Körper**:
  Einleger-Grundkörper und Text/Symbol-Körper (bei „vertieft“ bleibt der Text/Symbol-Körper als
  Füllung der Vertiefung erhalten). So lässt sich die Komponente als 3MF exportieren und im Slicer
  pro Körper eine Farbe zuweisen. Einfarbig drucken = beide Körper gleiche Farbe.
- Texte als User-Parameter nachträglich änderbar, wie die bestehenden Bin-Labels.
  Breite nachträglich änderbar über einen User-Parameter *(Builder-Call, ob Einheit oder mm)*.
  Symbolwahl ändern = neu generieren.
- Einstellungen sind wie bei Bin/Baseplate als Default speicherbar und per Rechtsklick
  „Gridfinity settings“ einsehbar.

### Symbole

- Quelle: Cullenect `OpenSCAD/Cullenect.scad` (MIT). OpenSCAD ist auf des Nutzers Rechner unter
  `C:\Program Files\OpenSCAD` installiert. Das Konvertierungsskript wird im Repo unter `tools/`
  abgelegt, damit es reproduzierbar ist.
- **Vorab gerendert, nicht zur Laufzeit zusammengesetzt** *(Claudes Call)*: Das Skript lässt
  OpenSCAD **jede Schrauben-Kombination** (Kopf × Schaft × Gewinde × Antrieb × Flansch ×
  Sicherheits-Pin, ≈ 720) und jede Hardware als fertiges SVG rendern (`projection()` →
  SVG-Export). Die Positionierungslogik bleibt damit in Cullenects OpenSCAD und muss nicht in
  Python nachgebaut werden. Der Dialog bietet die Baukasten-Auswahllisten an und wählt daraus den
  Dateinamen (z. B. `screw_socket_machine_full_hex_noflange_nosec.svg`); ungültige Kombinationen
  (Flansch + Senkkopf) sind im Dialog gesperrt.
- Ablage: eigener Ordner `lib/gridfinityUtils/cullenectIcons/` (Schrauben-Kombinationen,
  Hardware). Hardware-SVGs zusätzlich in den vorhandenen Icon-Mechanismus
  (`labelIcons/<typ>/`), damit sie auch auf normalen Bin-Labels wählbar sind; die ≈ 720
  Schrauben-Kombinationen nicht (würde die vorhandene Icon-Liste überfluten).
- Erweiterbarkeit: neues Symbol = neue SVG-Datei in einem Typ-Ordner, keine Code-Änderung.
  Weitere Schrauben-Kombinationen entstehen durch erneuten Lauf des Konvertierungsskripts.
- Attribution: README im Icon-Ordner mit Quelle und MIT-Lizenz von Cullenect.

### Vollständig bestimmte Skizzen

- **Befund 2026-11-14:** Eine mit dem Fork-Stand erzeugte 4x2-Bin mit gemischten Fächern hatte
  19 Skizzen, alle `isFullyConstrained == True` (Fuß, Körper, Lippe, Kerben, Fach-Hohlräume,
  Fach-Laschen). Der Generator erfüllt die Regel also bereits; sie gilt damit für **alle**
  Skizzen der erzeugten Bins und Einleger, und der neue Code reiht sich ein. Nicht geprüft
  wurden die vorhandenen Text-/Icon-Labels (Outline/Engraved/Embossed) — der Code importiert
  SVGs ohne `isFixed`; das prüft der Constraint-Check mit, ein Befund dort wird Nutzer gemeldet,
  aber nicht ungefragt im Bestandscode behoben.
- Alle vom neuen Code angelegten Skizzen sind fully constrained (Prüfung über
  `Sketch.isFullyConstrained`).
- Importierte SVG-Kurven sind in Fusion lose. Lösung *(Claudes Vorschlag, von Nutzer bestätigt)*:
  SVG-Kurven in ihrer Skizze fixieren (`isFixed`), die Lage des Symbols über ein parametrisches
  Verschieben-Feature steuern, dessen Distanz an der Label-Breite hängt. So bleibt jede Skizze
  bestimmt, und das Symbol wandert bei Breitenänderung mit.
- Text-Skizzen: Textposition an bemaßte Konstruktion gebunden.

## Prüfung (Akzeptanzkriterien)

1. **Unit-Tests (pytest, `tests/`)** für die neue reine Logik zuerst schreiben (fehlschlagend), dann
   implementieren: Taschen-/Einlegermaße aus Einheiten und mm, Mindest-Laschenbreite,
   Symbol-Katalog (Ordner → Auswahllisten), Dialog-Zustand (Text/Icon aus bei Cullenect).
   `python -m pytest` grün, Output wird gezeigt.
2. **E2E-Snapshot-Fälle (`tests/e2e/cases`)** neu: Bin 1x1x3 Cullenect, 2x1x3 Cullenect mit
   geänderten Basis-Parametern (`gfBaseWidth`), Bin mit Fach-Laschen Cullenect, **Bin 4x2 mit
   gemischter Fächeraufteilung** (vorne ein Fach über 4 Zellen, hinten ein Fach über 2 Zellen +
   zwei Einzelfächer; des Nutzers Anwendungsfall, jede Fach-Lasche mit eigener Tasche passender Breite),
   Einleger 1U mit
   Schraube+Text, Einleger 2U mit Hardware, Einleger freie mm-Breite. In Fusion über
   „Gridfinity tests: run“; alle bestehenden Fälle bleiben grün.
3. **Constraint-Check:** Skript prüft nach jedem neuen E2E-Fall, dass alle Skizzen der erzeugten
   Komponenten `isFullyConstrained` sind, und dass Parameter-Extremwerte (1×1×2 bis 6×4×12,
   Einleger 1U bis 6U) ohne Timeline-Fehler durchlaufen.
4. **Passung digital:** Einleger und Tasche gegen `Cullenect.scad`-Geometrie bzw. des Nutzers
   Einleger-STEP vermessen (Maße innerhalb ±0,01 mm der Referenz).
5. **Passung real (Nutzer):** Probedruck 1U-Bin + Einleger, klickt ein, hält, lässt sich lösen;
   zusätzlich ein Original-Cullenect-Einleger in der neuen Tasche.

## Dem Builder überlassen

- Genaue Klassen-/Dateiaufteilung (analog zu bestehenden Generator-Modulen).
- Dialog-Layout im Detail, Icons/Tooltip-Bilder des neuen Befehls.
- Die oben als *Builder-Call* markierten Punkte, jeweils mit der genannten Vorgabe als Start.
- Reihenfolge: Bin-Tasche vor Label-Befehl vor Symbol-Konvertierung ist eine sinnvolle Vorgabe, da
  jede Stufe für sich testbar ist.
