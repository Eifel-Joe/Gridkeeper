# Runde 11 – Beschriftung druckbar mit 0,4-mm-Düse

Stand 2026-11-15. Ergänzt `2026-11-14-cullenect-labels-design.md`. Punkt p130 „Einleger: Schrift und Symbole zu dünn
für eine 0,4-mm-Düse“. Jörgs Entscheidungen in der Sitzung (15.11.): Weg B (Arial Black) mit Hinweis; die Schrift soll „anständig mit
0,4er Nozzle druckbar sein und eine Dicke von 0,4 mm, also 2 Layer à 0,2 mm haben“.

## Problem

Jörgs Slicer (0,4-mm-Düse, Einleger bündig, mehrfarbig) lässt Teile der Beschriftung leer, vor allem die zweizeilige
Schrift („5mm“ über „Hex key“). Die Einleger setzen den Text in Arial normal, 5 mm Schrifthöhe einzeilig, 3,5 mm
zweizeilig, verkleinert, wenn er nicht in die Breite passt (`fittedLineHeight`, 5 % Reserve).

## Warum 0,9 mm

Eine 0,4-mm-Düse legt Wände mit ~0,42–0,45 mm Linienbreite. Ein Strich ab ~0,9 mm bekommt zwei volle Bahnen und druckt
unabhängig vom Wandgenerator des Slicers. Zwischen 0,42 und 0,9 mm hängt es vom Slicer ab (Arachne legt eine
breitere Einzelbahn, der klassische Generator eine oder keine). Unter ~0,6 mm mittlerer Strichbreite fallen auch bei
einer Bahn sichtbar Teile weg: Arial normal zweizeilig (0,39 mm) verliert bei 0,42 mm Bahnbreite 35 % der Fläche –
das ist Jörgs Slicer-Bild. Ziel: einzeilig ≥ 0,9 mm, zweizeilig so breit, wie der Platz zulässt, nie unter 0,6 mm
ohne Hinweis. Zweizeilig erreicht Heavy 0,76 mm: eine breite Bahn, 99 % der Fläche – zwei volle Wände gibt die
Höhe von 11 mm für zwei Zeilen nicht her (siehe D).

## Messung (Fusion, 15.11.)

Text wie der Generator ihn setzt (Grundlinie, `createInput2`), extrudiert, Kontur der Oberseite, ausgewertet mit
shapely. „mittel“ = 2·Fläche/Umfang; „0,42“/„0,9“ = Anteil der Fläche, den eine Bahn dieser Breite erreicht
(morphologische Öffnung). Höhe = Schrifthöhe an `createInput2`, mm.

| Variante | Text | Höhe | mittel | 0,42 | 0,9 |
|---|---|---|---|---|---|
| Arial normal (bisher) | M4x5 / Welle 6mm | 5,0 | 0,56 | 99 % | 0–2 % |
| Arial fett | M4x5 / Welle 6mm | 5,0 | 0,83–0,85 | 99 % | 74 % |
| Arial Black | M4x5 / Welle 6mm | 5,0 | 1,07–1,12 | 99–100 % | 95–97 % |
| Arial normal (bisher) | 5mm + Hex key | 3,5 | 0,39 | 65 % | 0 % |
| Arial fett | 5mm + Hex key | 3,5 | 0,57 | 96 % | 2 % |
| Arial Black | 5mm + Hex key | 3,5 | 0,76 | 99 % | 70 % |
| fett + Kontur +0,15 | 5mm + Hex key | 3,5 | 0,50 | 94 % | 40 % |
| Bin-Label fett (Standard) | Schrauben M4 / Kleinteile | 7,6–7,8 | 1,23–1,27 | 100 % | 98 % |

Die mittlere Strichbreite ist ein fester Anteil der Schrifthöhe, ein- wie zweizeilig: normal 0,11, fett 0,165,
Arial Black 0,215. Symbole (Madenschraube, Gewindeeinsatz) haben > 1,1 mm, unkritisch.

## Lösungswege

| Weg | Ergebnis | Aufwand, Risiko |
|---|---|---|
| A Fett als Standard | einzeilig knapp (0,84), zweizeilig 0,57 | nur Vorgabe ändern; löst den Fall aus dem Bild nicht |
| **B Arial Black als dritte Schrift, Standard bei Einlegern** | einzeilig ≥ 1,07, zweizeilig 0,76 (99 % mit einer Bahn) | eine Text-Eigenschaft; ~20 % breiter, lange Texte schrumpfen stärker; Innenraum „e“ zweizeilig 0,54 statt 0,74 mm |
| C Konturen verdicken (Dünnwand-Extrusion um den Text, vereinigt) | zweizeilig höchstens 0,50 / 40 % | Wandseite 1/2 folgt der Kurvenrichtung (teils nach innen), „Mitte“ hinterlässt in der Messung 12–30 Spalten; doppelte Texte für bündig/graviert – verworfen |
| D Zweite Zeile 4,0 statt 3,5 mm | mit B 0,87 / 85 % | Unterlängen („y“) rücken auf 11 mm Einlegerhöhe an die nächste Zeile bzw. den Rand – verworfen |
| E Hinweis bei zu dünner Schrift | macht Schrumpfen durch lange Texte sichtbar | kleine reine Rechnung, ergänzt B |

**Entscheidung (Jörg, 15.11.): B mit Hinweis E.**

## Umsetzung

### Schriftstil statt „Bold“
- Neuer Stil-Begriff mit drei Werten: `Regular` (Arial), `Bold` (Arial fett), `Heavy` (Arial Black, nicht fett).
  Reine Abbildung Stil → (Schriftname oder keiner, fett ja/nein) in `lib/gridfinityUtils/textStyles.py` (ohne Fusion,
  testbar), dazu der Strichfaktor je Stil (0,11 / 0,165 / 0,215).
- Einleger-Dialog: Der Haken „Bold“ wird zur Auswahl „Text style“ mit Regular / Bold / Heavy, **Vorgabe Heavy**.
  `InputState.isBold` wird zu `textStyle` (einer der drei Werte). Gespeicherte Dialog-Vorgaben mit dem alten Haken
  stören nicht (unbekannte Einträge bleiben liegen), die neue Auswahl startet auf Heavy.
- `CullenectLabelInput.isBold` wird zu `textStyle`; Messtext (`_measureText`) und Zeilentext (`_addLineText`) bekommen
  dieselbe Schrift, damit `fittedLineHeight` die breitere Schrift richtig einpasst. Doppeltexte (Zwillinge für
  bündig/graviert) gleich.
- Live-Text bleibt: Schriftname und Stil gehören zum Sketch-Text, eine spätere Änderung am Textparameter behält sie.
  Farbe (p86) wirkt auf die Körper, unberührt.
- Bin-Labels: Schrift bleibt wie bisher (Haken „Bold label text“, Vorgabe fett) – bei voller Höhe 1,23–1,27 mm.
  `labelGenerator._addText`/`_measureText` lernen den Stil intern (fett ↔ `Bold`, sonst `Regular`), damit der Einleger
  dieselben Funktionen nutzt; am Bin-Dialog ändert sich nichts.

### Dicke 0,4 mm (zwei Schichten)
- Text und Symbol der Einleger sind 0,4 mm dick statt einer Schicht (0,2 mm): `const.CULLENECT_LAYER` wird zu
  `CULLENECT_MARKING_DEPTH = 0.04`, für alle Oberflächen. Erhaben steht die Beschriftung 0,4 mm über dem Einleger,
  bündig und vertieft reicht sie 0,4 mm hinein – bis auf die Oberkante der Rastschicht (0,8 mm), der Einleger bleibt
  darunter ganz. Gleiche Tiefe für Symbole, damit ein Farbwechsel für Text und Symbol auf derselben Schicht liegt.
- Bin-Labels sind schon 0,5 mm tief/hoch (`BIN_LABEL_DEPTH`), unverändert.

### Hinweis bei dünner Schrift
- Geschätzte Strichbreite = Strichfaktor des Stils × tatsächliche Schrifthöhe (nach dem Einpassen).
- Liegt sie unter **0,6 mm**, sammelt der Generator einen Hinweis je Zeile bzw. Label: Text, Schrifthöhe,
  geschätzte Strichbreite. Sammelstelle ist ein kleines Modul (`textStrokes`), das der Befehl vor dem Bau leert und
  danach liest; reine Rechnung und Textbau ohne Fusion testbar.
- Einleger-Befehl: Bei OK einmal eine Meldung („Text … ist ca. 0,52 mm breit, unter 0,6 mm druckt eine 0,4-mm-Düse
  Teile nicht: Text kürzen, Einleger breiter oder Stil Heavy“). Bei der Vorschau steht derselbe Kurztext neben der
  Vorschauzeit, keine Meldung.
- Bin-Befehl: gleiche Meldung bei OK, wenn ein Label-Text unter 0,6 mm schrumpft (z. B. „Schrauben M4“ fett auf 1U).
- Die Schwelle 0,6 statt 0,9: Mit 0,9 meldete jeder zweizeilige Einleger (Heavy 0,76 mm), obwohl er mit einer Bahn
  vollständig druckt (99 %). Die Meldung soll nur kommen, wo wirklich Teile fehlen werden. (Eigene Wahl, Jörg prüft.)

### Testfälle und Snapshots
- Fall-JSONs der Einleger: `isBold` → `textStyle` (`false` → `Regular`, `true` → `Bold`). Die Schrift der alten Fälle
  bleibt gleich; ihre Snapshots ändern sich nur durch die Dicke 0,4 mm (Volumen der Beschriftungskörper doppelt, Höhe
  bzw. Tiefe +0,2 mm). Bin-Snapshots ändern sich nicht.
- Neuer Fall: zweizeilig „5mm“ / „Hex key“, bündig, Heavy – Snapshot neu.
- Bekannt rot bleiben die 4 Text-Label-Bin-Fälle (p30).

## Nicht dazu
- Andere Schriften als Arial/Arial Black, freie Schriftwahl.
- Konturen verdicken, größere zweite Zeile (C, D verworfen).
- Prüfung nach späterer Textänderung über den Parameter (der Hinweis kommt nur beim Bau).
- Stilauswahl für Bin-Labels (bleibt der Fett-Haken).
- Exakte Strichmessung im Generator (geschätzt über den Faktor; die Messung oben belegt ihn).

## Ende-zu-Ende-Kriterium
1. In Fusion gebaut: Einleger „M4x5“ und „Welle 6mm“ einzeilig, „5mm“/„Hex key“ zweizeilig, bündig, Vorgabe Heavy –
   dieselbe Messung wie oben: einzeilig in voller Höhe (M4x5) mittel ≥ 0,9 mm und ≥ 90 % bei 0,9; zweizeilig
   ≥ 95 % bei 0,42. Ein eingepasster Text (Welle 6mm auf Jörgs Einleger, ~20 % breiter als bisher) wird mit seiner
   Höhe und Strichbreite berichtet; er liegt erwartbar bei ~0,85 mm, über der Hinweisschwelle.
2. Textparameter ändern: Text bleibt Arial Black, Breite eingepasst wie bisher.
3. Langer Text, der unter 0,6 mm schrumpft, zeigt den Hinweis.
4. `python -m pytest` grün; Snapshot-Lauf: Einleger-Fälle nur um die Dicke geändert (begründet neu abgelegt), Bin-Fälle
   unverändert, neuer Fall grün, nur die 4 bekannten roten.
5. Die Beschriftungskörper eines gebauten Einlegers sind 0,4 mm dick (Bounding Box in z).
6. Jörg: Slicer mit 0,4-mm-Düse zeigt die zweizeilige Schrift vollständig; Probedruck.
