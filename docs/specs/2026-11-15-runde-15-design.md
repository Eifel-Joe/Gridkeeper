# Runde 15: Raster und Bin-Geometrie

Stand 15.11.2026, von Nutzer in der Hauptsitzung freigegeben. Sammelbetrieb R14–R18 (CLAUDE.md in
`D:\Entwicklung\Gridfinity`, „Ergänzung Sammelbetrieb“): Branch von `runde-14-18`, Merge zurück dorthin.

## Punkte
- p170 „Joint Origins an Bin-Füßen und Grundplatten-Aufnahmen folgen geänderten Rastermaßen nicht“
- p60 „Cullenect-Taschen folgen einer geänderten Rasterbreite nicht ganz, wenn Fächer neben dem Raster liegen“
- p101 „Rundung der hochgezogenen Trennwände bei Wänden ab 2 mm nicht ganz nahtlos“
- p35 „Cullenect-Tasche bei sehr dünnen Wänden im Druck prüfen“ (Entscheidung Nutzer 15.11.2026, siehe unten)

## Befund (Code, 15.11.)
- p170: `createCellJointOrigins` (`baseGenerator.py:520`) legt alle Punkte in eine Skizze mit Referenzmaßen
  (`addDistanceDimension(..., False)`), die Punkte folgen den Parametern nicht. Treibende Maße in einer Skizze
  scheitern an Überbestimmung, sobald zwei Punkte x oder y teilen. `createPointJointOrigins` (Runde 13,
  `baseGenerator.py:566`) löst das mit einer Ebene und Skizze je Punkt und treibenden Maßen. Ein Punkt je Zelle.
- p60: In `binBodyGenerator.py:352-377` wird zur Bauzeit per `.value` entschieden, ob Laschenende oder Fachende die
  Taschenmitte bestimmt (`labelMinX`/`labelMaxX`), ebenso `units` und `socketFitsDepth`. Kippt das Verhältnis nach
  einer gfBaseWidth-Änderung, stimmt die Mitte nicht mehr.
- p101: Ab Wand dicker als die Lippenwand liefert `chainPath` keine Kette, die Ecke fällt in den Fillet-Fallback
  (`filletRaisedDividerCorner`) mit kleinerem Radius; das ergibt die Stufe.

## Entscheidungen
1. **p170:** Fuß- und Grundplatten-Joint-Origins über `createPointJointOrigins` (eine Skizze je Punkt, treibende
   Maße). Bauzeit vorher/nachher messen (4x2-Bin, 6x6-Grundplatte) und ins Übergabeprotokoll. Wird die 6x6-Grundplatte
   um mehr als 50 % langsamer, im Protokoll für Nutzer vermerken, nicht eigenmächtig anders lösen.
2. **p60:** Die Min/Max-Wahl wird als Ausdruck (`min()`/`max()` in Fusion-Parameterausdrücken) gebaut, nicht per
   `.value` zur Bauzeit. Größenstufe (`units`) und `socketFitsDepth` bleiben Bauzeit-Entscheidungen; springt eine
   Stufe nach einer Änderung, ist ein Neubau nötig – das kommt in CHANGELOG und Protokoll.
3. **p101:** Nahtlose Rundung auch über die Stufe bei Wänden ab 2 mm (z. B. bis zur Stufe sweepen, den Rest getrennt).
   Gelingt es nach drei Versuchen nicht: bisheriger Stand bleibt, Punkt bleibt offen, ein Satz ins Protokoll.

4. **p35 – Mindestwand für Cullenect 1,2 mm.** Nutzer 15.11.2026: „Standard für Cullenect ist 1,2mm. Dicker geht,
   dünner nicht.“ Der Label-Stil Cullenect ist nur mit Wandstärke ≥ 1,2 mm zulässig. Bei dünnerer Wand meldet der
   Bin-Dialog das Problem und sperrt OK (wie die übrigen Dialogprüfungen); dasselbe beim Laden einer Konfiguration und
   beim Neubau per Rechtsklick. Dickere Wände (z. B. 2 und 3 mm) mit Cullenect müssen bauen – das Ende-zu-Ende-Skript
   prüft das. Bereits gebaute Bins werden nicht angefasst.

## Nicht dabei
- Taschen-Größenstufe, die einer Parameteränderung folgt.
- Joint Origins standardmäßig einschalten (Default bleibt aus).

## Ende-zu-Ende-Kriterium
Skript in neuem Dokument:
- 4x2-Bin und 3x3-Grundplatte mit Joint Origins, gfBaseWidth 42 → 50 mm: jeder Joint Origin in der Mitte seiner Zelle
  (±0,01 mm), Skizzen vollständig bestimmt, Timeline ohne Fehler.
- 4x2-Bin, 3 Fächer nebeneinander, Cullenect: Volumen nach Änderung auf 40 mm gleich dem einer frisch mit 40 mm gebauten
  Bin (±0,001 cm³).
- Trennwände bis oben mit Wand 2 mm und 3 mm: keine waagerechte Stufe an den Trennwand-Ecken (Flächenprüfung) – oder,
  falls p101 offen bleibt, Stand dokumentiert.
- Cullenect mit Wand 1,19 mm: Prüffunktion meldet das Problem (Unit-Test); mit 1,2 / 2 / 3 mm baut die Bin mit Taschen,
  Timeline ohne Fehler.
- pytest grün, Snapshot-Tests grün (bekannte p30-Fälle ausgenommen).
