# Runde 40: Symbole aus Linien, Bögen und Kreisen statt tausender Linienstücke (p371)

Stand 18.11.2026, Entwurf. Punkt p371 „Torx-Symbole machen den Bau sehr langsam“.

## Warum

Ein Box-Schild mit dem Symbol der Senkkopfschraube mit Torx brauchte im Test fast eine Minute, ohne Symbol rund 10 s.
Einleger (Cullenect-Labels) und Bin-Labels bauen ihre Symbole auf demselben Weg (`labelGenerator._importIcon`).

Vorgabe: Die Symbole werden mit echten Bögen, Kreisen, Splines und Linien nachgebaut, statt mit tausenden kurzen
Linienstücken. Die Zahl der Punkte und Segmente sinkt radikal. Dazu nur noch ein Import je Symbol statt 4 bis 5.

## Befund (ohne Fusion, gelesen und gezählt)

1. **Die Dateien bestehen nur aus Linienstücken.** OpenSCAD schreibt jede Rundung als Polygon (`M … L … z`).
   `screw_countersunk_machine_full_torx_noflange_nosec.svg` hat 1700 Punkte, davon 1670 im Torx-Antrieb: ein Bogenzug
   mit Schritten von 0,01 mm (Cullenect.scad zeichnet die Schrauben mit `$fa = 1, $fs = 0.01`). 158 der 508
   Cullenect-Symbole haben über 500 Punkte, 60 über 1000. Die Hardware-Symbole wurden in Runde 17 gröber gerendert
   (`HARDWARE_RESOLUTION`), sind aber weiter Polygone.
2. **Jedes Symbol wird mehrfach importiert.** `_importIcon` importiert die Datei viermal (Maßstab 1 messen, skaliert
   messen, um 1 verschoben messen, endgültig), das Bin-Label zusätzlich einmal in `_iconMeasure` (Seitenverhältnis und
   Punktzahl). Jeder Import legt jede Linie als Skizzenkurve an.
3. Danach kommen je Kurve bzw. Punkt: `_fixSketch` (jede Kurve und jeder Punkt `isFixed`), `_iconProfiles` und die
   Extrusion. Bin-Label-Symbole bis 40 Punkte werden je Punkt bemaßt (`ICON_POINTS_HELD_BY_DIMS`).
4. Bin-Label-Symbole (`labelIcons`) haben höchstens 122 Punkte, Torx-Schrauben sind dort nicht wählbar. Das Bin-Label
   ist vor allem über die Zahl der Importe betroffen.

**Prototyp der Zerlegung** (Probe außerhalb des Repos, Toleranz 0,01 mm, Kreis-Fit nach Kåsa, gierig je geschlossenem Zug, Start an
der schärfsten Ecke):

| | vorher | nachher |
|---|---|---|
| Torx-Senkkopf | 1700 Punkte | 36 Linien, 19 Bögen; Fläche des Antriebs 13,747 → 13,750 mm² |
| Linsenkopf Torx mit Bund und Sicherungsstift (größte Datei) | 2246 Punkte | 42 Linien, 21 Bögen, 1 Kreis |
| alle 542 Symboldateien | 243 959 Punkte | 18 113 Linien, 2 012 Bögen, 176 Kreise; höchstens 83 Segmente je Datei |

Splines brauchte der Prototyp für keine Datei (OpenSCAD erzeugt nur Geraden und Kreisbögen); das Werkzeug sieht sie
trotzdem für Freiformen vor.

## Messung in Fusion (vorher, 18.11.2026, Code `master` 5f42fb4)

Jobs `r40_m_imp/box/box0/ins/ins0/bin` (Fusion-Auftragsordner), je neues Dokument, cProfile.

| Bau | mit Symbol | ohne Symbol |
|---|---|---|
| Box-Schild 5 Felder, Torx-Senkkopf | **40,9 s** | 0,7 s |
| Einleger 1U, Senkkopf Torx | **40,4 s** | 0,9 s |
| Bin 2×1×3, Label-Symbol Hex nut (10 Punkte, bemaßt) | 7,9 s | 4,3 s |
| Bin 2×1×3, Label-Symbol Crimp butt splice (122 Punkte, bewegt) | 12,1 s | 4,3 s |

Aufteilung beim Box-Schild (Einleger gleich): 4 × `importSVG` 9,5 s; `SketchCurves.item`/`__len__` 20,7 s und
`SketchPoints.item`/`__len__` 4,1 s (jedes Element kostet ~1 ms: Bounds nach jedem Probe-Import über 1692 Kurven,
`_fixSketch`); 3 Wegwerf-Skizzen löschen 1,3 s; Extrusion 4,4 s. Beim Bin entfallen 1,4 s auf die 4 Importe und 0,4 s
auf `_iconMeasure`; die Bin-Zeilen bauen im selben Dokument nacheinander, der Rest der Differenz ist nicht dem Symbol
zuzuordnen.

Einzelimport auf XY (Torx-Senkkopf):

| Datei | Import | Kurven | Skizzenpunkte | Bounds über alle Kurven |
|---|---|---|---|---|
| Original | 1,74 s | 1692 Linien | 1693 | 4,02 s |
| Prototyp Linien/Bögen | **0,06 s** | 35 Linien, 19 Bögen | 74 | 0,01 s |
| Prototyp Linsenkopf (mit Kreis) | 0,07 s | 41 Linien, 23 Bögen | 88 | 0,01 s |

Belegt außerdem:
- `importSVG` legt `A`-Befehle als echte `SketchArc` an; ein ganzer Kreis aus zwei Halbbögen bleibt zwei Bögen.
  Gefüllte Profile wie beim Original (2 bzw. 3).
- **Abbildung**: Skizzenpunkt = (x, −y) · 2,54/96 cm · scale + (posX, posY), unabhängig von `viewBox`, `width`-Einheit
  und Skizzenebene (XY, XZ, YZ gleich; Dreieck mit Bogen als Probe). Damit lassen sich Maßstab und Lage aus der Datei
  berechnen, ein Import genügt.
- Skizzenpunkte eines Imports = Segmente + Bögen (je Bogen sein Mittelpunkt) – Hex nut 10, Prototyp Torx 73, Probe 6.
- `Sketch.move` nimmt nur gleichmäßige Skalierung (auch in z); Verschieben geht.

## Optionen

- **A, Symbole in Linien, Bögen, Kreise (und Splines) zerlegen (Vorgabe):** Werkzeug `dev-notes/tools/arcSymbols.py`,
  Toleranz 0,01 mm. Schreibt die Dateien im bisherigen svg-Format, `d` mit `M`, `L`, `A` (Kreisbogen), `C` (kubischer
  Bézier für Freiformen) und `z`; ein ganzer Kreis als zwei Halbbögen. Der Importweg bleibt `Sketch.importSVG`
  (echte Bögen belegt), kein eigenes Format. Züge, die schon Bögen enthalten (16 eigene Icons in `labelIcons`),
  bleiben unverändert.
- A', erweitertes eigenes Format (z. B. JSON) und eigenes Zeichnen per API: unnötig, `importSVG` legt Bögen an.
  Verworfen.
- B, Douglas-Peucker (Punkte ausdünnen, weiter nur Linien): Torx 1700 → 186 Punkte bei 0,005 mm. Weniger Gewinn als A
  und nicht die Vorgabe. Verworfen.
- C, Schrauben mit OpenSCAD gröber neu rendern: bleibt ein Polygon; Cullenect.scad setzt `$fa/$fs` auf Modulebene,
  von außen nicht erreichbar (Runde 17). Verworfen.
- D, Cache importierter Symbole über Bauten hinweg: hilft nur beim zweiten Bau. Verworfen.

**Ein Import je Symbol:** Das Werkzeug kennt die Geometrie jeder Datei, also auch ihren Umriss (Bounds aus Linien,
Bögen, Kreisen, Splines). Ein reines Python-Modul `lib/gridfinityUtils/svgSymbol.py` liest eine Symboldatei
(`M/L/A/C/z`) und liefert Umriss, Seitenverhältnis und Zahl der Skizzenpunkte. Aus dem Umriss und der einmal in Fusion
gemessenen Abbildung von `importSVG` (Maßstab, Lage, Richtung je Skizzenebene) berechnet `_importIcon` Maßstab und
Position und importiert **einmal** in die Zielskizze. Danach misst es die Bounds des Imports (bei ≤ 100 Kurven
billig) und protokolliert die Abweichung wie bisher; weicht die Lage um mehr als 0,001 mm ab, verschiebt es die Kurven
per `Sketch.move` (reine Verschiebung, kein zweiter Import). Das Bin-Label nimmt Seitenverhältnis und Punktzahl aus
`svgSymbol` statt aus einem Messimport.

**Entscheidung (Vorschlag an die Hauptsitzung): A mit einem Import, Toleranz 0,01 mm.**

## Anforderungen

1. Werkzeug `dev-notes/tools/arcSymbols.py`, reines Python: liest jeden geschlossenen Zug einer OpenSCAD-svg, zerlegt
   ihn in Linien, Kreisbögen und ganze Kreise (Bogen-Erkennung mit Toleranz, Standard 0,01 mm; ein Bogen braucht
   mindestens 4 Punkte, monotonen Drehsinn und einen Radius unter einer Obergrenze), Freiform-Läufe als kubische
   Bézier-Splines innerhalb der Toleranz, sonst als Linien. Aufruf
   `python dev-notes/tools/arcSymbols.py [--tolerance 0.01] [--check] <Ordner…>`; `--check` schreibt nichts.
   Ausgabe je Datei: Punkte vorher, Linien/Bögen/Kreise/Splines nachher, größte Abweichung, Flächenänderung.
2. **Prüfungen im Werkzeug und in pytest, automatisiert für alle Symboldateien:** Abstand der Kontur in beiden
   Richtungen (abgetastete neue Kontur zu den alten Segmenten, alte Punkte zur neuen Kontur) ≤ Toleranz; Fläche je
   Zug auf 0,5 % bzw. 0,01 mm² gleich; jeder Zug geschlossen (Ende = Anfang), keine Selbstüberschneidung neu
   entstanden; Zahl der Züge gleich. Das Werkzeug bricht bei einem Verstoß ab und schreibt die Datei nicht.
   Die Original-Polygone werden nicht als Ganzes eingecheckt. Das Werkzeug schreibt je Ordner eine kleine
   `symbol-check.json` (je Datei: Fläche je Zug und Umriss des Originals). pytest prüft für **alle** eingecheckten
   Symboldateien: lesbar (`svgSymbol`), jeder Zug geschlossen, Fläche je Zug und Umriss gegen `symbol-check.json`
   innerhalb der Toleranz, höchstens 150 Segmente je Datei. Die Abstandsprüfung selbst testet pytest am Werkzeug mit
   Fixtures (synthetischer Kreis, Rechteck mit Rundungen, Gewinde-Zickzack und das Original des Torx-Senkkopfs als
   Fixture-Datei).
3. Alle Symboldateien (`cullenectIcons/screws`, `hardware`, `setscrews`, `labelIcons/**`) sind zerlegt.
   `tools/cullenectIcons.py` und `tools/setScrewIcons.py` rufen das Werkzeug nach dem Rendern auf, damit ein neues
   Rendern die Dateien nicht wieder zu Polygonen macht.
4. Lizenz und Credits bleiben: `cullenectIcons/README.md`, `setscrews/README.md`, `labelIcons/cullenect-LICENSE.txt`
   nennen weiter CullenJWebb, Cullenect-Labels, MIT, Commit, und vermerken die Ableitung („in Linien, Kreisbögen und
   Kreise zerlegt mit `dev-notes/tools/arcSymbols.py`, Toleranz 0,01 mm“). Die eigenen Symbole von
   `tools/labelIcons.py` ebenso mit ihrem Herkunftsvermerk.
5. `svgSymbol.py` (reines Python, pytest): Umriss inklusive Bögen, Kreise und Splines, Seitenverhältnis, Punktzahl,
   wie Fusion sie nach dem Import zählt (im Fusion-Lauf gegen `sketchPoints.count` geprüft).
6. `_importIcon` importiert je Symbol **einmal**, `_iconMeasure` importiert nicht mehr. Lage und Größe des platzierten
   Symbols wie vorher (≤ 0,001 mm, im Fusion-Lauf geprüft auf XY und der gekippten Bin-Label-Ebene).
7. Skizzen wie bisher: Symbol-Skizzen von Einleger und Box-Schild fixiert (`_fixSketch`), Bin-Label-Symbole bis 40
   Punkte per Bemaßung gehalten (jetzt Bögen: Mittelpunkte zählen mit), größere als bewegte Körper; Text-Skizzen
   bleiben die bekannte Ausnahme. Das Prüfskript prüft `isFullyConstrained` der Symbol-Skizzen.
8. `ICON_POINTS_HELD_BY_DIMS` bleibt 40. Symbole, die durch die Zerlegung darunter fallen, werden künftig bemaßt statt
   bewegt; das ist so gemeint, der Klicktest sieht es an. Dauert das Bemaßen eines Bogens deutlich länger als eines
   Punkts, wird die Grenze nach Messung als Spec-Änderung vorgeschlagen, nicht still geändert.

## Nicht dabei

- Keine Änderung an Text-Skizzen, Extrusion, Layout, Symbolauswahl, Dialog.
- Keine Änderung an Cullenects Quelle, kein Cache.
- Keine Versionsänderung (Manifest bleibt 1.1.0); CHANGELOG unter `## Unreleased`.

## Snapshots

Die Snapshot-Fingerprints vergleichen auf 1e-6. Jeder Fall mit Symbol ändert Flächen (Bögen statt Facetten) und
Volumen minimal und wird bewusst neu abgenommen: `label_1u_screw_text*`, `label_1u_set_screw_hex`,
`label_2u_hardware`, `label_1u_welle_6mm*`, `label_25mm_free`, `label_6u_text`, Box-Fälle mit Schild-Symbol und
Bin-Fälle mit Label-Symbol (`bin_2x1x3_label_icon_text_embossed*`, weitere laut Fall-Einstellungen). Fälle ohne
Symbol bleiben unverändert grün. Je neu abgenommenem Fall: Symbolvolumen < 0,5 % anders, Umriss ≤ 0,02 mm.

## Ende-zu-Ende-Kriterium

- Fusion-Messung mit denselben Jobs vorher/nachher: Box-Schild 5 Felder mit Torx-Senkkopf, Einleger 1U Senkkopf
  Torx, Bin 2×1×3 mit Label-Symbol „Cullenect crimp butt splice“ – jeweils deutlich schneller (Zahlen in PR und
  CHANGELOG, nur Gemessenes); ohne Symbol unverändert.
- Aussehen gleich: Prüfungen aus Anforderung 2 grün für alle Dateien; Snapshot-Abweichungen wie oben.
- Profile geschlossen: jedes Symbol ergibt in Fusion dieselbe Zahl gefüllter Profile wie vorher.
- pytest grün, betroffene Snapshot-Fälle grün, Klicktest (Box-Schild, Einleger, Bin-Label mit Symbol) bestanden.
