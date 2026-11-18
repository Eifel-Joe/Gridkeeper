# Runde 32 – Ältere Bins mit ihren alten Einstellungen füllen (p280)

Punkt: p280 „Ältere Bins beim Neubau mit ihren alten Einstellungen füllen“ (Fehler).

Jörgs Notiz (maßgeblich): „Ältere Bins werden erstellt, wie sie gespeichert wurden. Es werden keine Einstellungen
aktiviert, welche die Config nicht her gibt. So bleiben die Bins identisch mit dem wie sie gespeichert wurden.“

## Problem

Neubau (Rechtsklick „Gridfinity rebuild“), Klonen und „Load from file“ lesen eine gespeicherte Config über den
Dialogzustand (`configJson.readConfig`, `rebuildUtils.configWithParameters`). Fehlt der Config ein Feld, weil es beim
Speichern noch nicht existierte, nimmt der Dialog seinen aktuellen Wert. Eine alte Bin kann so beim Neubau Trennwände
bis oben, eine Label-Farbe oder eine gerundete Schale bekommen, die sie nie hatte.

Für die Lippen ist das seit der Upstream-Runde gelöst: `configJson.OLDER_VALUES` setzt für fehlende Felder den Wert,
der das alte Modell ergibt (`lipType: Light`, `isLipTopTrimmed: True`), für die Box ebenso `hinge: M3x30`. Alle Wege
(Load, Neubau, Klonen, die Parameter-Bearbeitung `binBuilder.parameterEdits`, das Rebuild-Log) laufen schon durch
`withOlderValues`. Es fehlen die übrigen Felder.

## Inventur: Felder, die nach dem ältesten Config-Stand dazukamen

Ältester Config-Stand je Generator: Bin und Baseplate 2fea2a1 (13.11., „Save, load, copy and clone bin and baseplate
configs“), Einleger 8a5ce68 (16.11., Runde 18 p150), Box c5a24e8 (16.11.), Box-Schild bd75733 (17.11.). Ermittelt
per Felder-Vergleich der `InputState`-Klassen über die Git-Historie (Skript im Plan, Task 1).

| Generator | Feld | eingeführt | Wert für ältere Configs | Begründung |
|---|---|---|---|---|
| Bin | `lipType` | b6b417a | `Light` | schon da (Upstream-Runde) |
| Bin | `isLipTopTrimmed` | ec64b22 | `True` | schon da (Upstream-Runde) |
| Bin | `isShellRounded` | 1b44398 (Upstream) | `False` | vorher scharfe Schale; Upstream setzt in allen alten Testfällen `false` |
| Bin | `hasDividersToTop` | 5558f87 | `False` | vorher enden Trennwände unter der Lippe |
| Bin | `labelColor` | cf30d39 (p86) | `''` | vorher keine Farbe |
| Bin | `cullenectSocketOffset` | 2e4cf3a | `0.3` mm | Vorgabe bei Einführung; ältere Configs können kein Cullenect-Label haben, der Wert baut nichts |
| Baseplate | `plateEdgeClearance` (früher `plateClearance`) | 8cc5089 | **das `xyClearance` derselben Config** (Entscheidung 3) | vorher nahm jede Plattenkante, wo Platten sich treffen, das xy-Spiel (8cc5089: „Fill pieces and grid units plates used the bin xy clearance where they meet“). `plateClearance` aus 8cc5089–3452e56 wird wie bisher halbiert umbenannt und hat Vorrang |
| Box | `hinge` | 6c5350d | `M3x30` | schon da (Runde 28) |
| Einleger | – | – | – | seit dem ersten Config-Stand kein Feld dazu |
| Box-Schild | – | – | – | seit dem ersten Config-Stand kein Feld dazu |

Unterfelder: `compartmentPockets` (Fächer) – `compartmentLayout._sanitized` ergänzt fehlende Schlüssel, die Datei ist
seit fbd3146 (vor dem ersten Config-Stand) unverändert. Nichts zu tun.

## Entscheidungen

1. `OLDER_VALUES` bekommt die Bin-Felder der Tabelle. Mechanismus bleibt `withOlderValues`, gilt damit auf allen Wegen.
2. Abgeleiteter Altwert: `OLDER_VALUES` darf statt eines Werts eine Funktion der Config tragen (für
   `plateEdgeClearance` = `xyClearance`). Fehlt der Config auch `xyClearance`, bleibt das Feld fehlend (Dialogwert,
   wie jedes andere fehlende Feld einer handgeschriebenen Teil-Config).
3. Obergrenze des Plattenspalts (Hauptsitzung, 18.11.: „Jörg will identische Bauten“, erst prüfen, ob die Grenze einen
   geometrischen Grund hat). Geprüft: keinen. Die 0,25 mm pro Kante sind Upstreams Halbierung der 0,5 mm Gesamtspalt
   aus 8cc5089 (3452e56, Le0Michine). Vor 8cc5089 nahm dieselbe Kante das xy-Spiel bis 0,5 mm, und die Außenkante
   einer Fill-Area nimmt es bis heute mit derselben Rechnung (`baseplateGenerator`, `outlineMin/Max ± edgeClearance`).
   Deshalb hebt der Baseplate-Dialog die Grenze auf den Höchstwert des xy-Spiels an (0,5 mm, Eingabe, Tooltip und
   OK-Prüfung über eine Konstante `const.BASEPLATE_PLATE_EDGE_CLEARANCE_MAX`). Alte Baseplates bauen damit
   ausnahmslos identisch, keine Begrenzung. Abweichung von Upstream in `commandCreateBaseplate/entry.py`, das keiner
   anderen Runde gehört.
4. **Gegen p151 (Runde 18):** Dort galt „fehlt ein Feld, bleibt der Dialogwert stehen, belegt an der Label-Farbe“.
   Jörgs p280-Notiz kehrt das für Felder um, die es beim Speichern noch nicht gab: eine alte Bin mit Label bekommt beim
   Laden keine Farbe, der Dialog springt auf „None“. Die zwei p151-Tests in `tests/test_config_json.py` werden darauf
   umgestellt. Für Felder, die jede Config seit 2fea2a1 hat, bleibt p151: fehlen sie einer handgeschriebenen
   Teil-Config (Handtest 10), Dialogwert mit Hinweis „Not in the file, kept the current value“. Die Felder der Tabelle
   bekommen auch in einer Teil-Config den Altwert (alt und unvollständig sind nicht zu unterscheiden; Review).
5. Keine Änderung in `commands/commandCreateBin/` (Runde 31 arbeitet dort); alles in `lib/configJson.py`, dazu die
   Grenze in `commandCreateBaseplate/entry.py` und `const.py`.
6. Freigabe Hauptsitzung 18.11.: p151 ändert sich dadurch (alte Bin mit Label = keine Farbe), in CHANGELOG und PR-Text
   ausdrücklich nennen. Ein Inventur-Test hält fest, dass jedes spätere Feld einen Altwert braucht (Runde 30 Box, Runde
   31 Bin ergänzen `OLDER_VALUES`, wer nach dieser Runde gemergt wird).

## Nicht dabei

- `fitTolerance` (Fill-Area-Baseplates bis 3010f3f): die Funktion ist entfernt, eine Config damit wird wie bisher als
  „Not recognised, skipped“ gemeldet und ohne sie gebaut.
- Ein eigener Hinweis im Dialog „mit altem Wert gefüllt“ (die Lippen-Felder melden es auch nicht).
- Gespeicherte Dialog-Vorgaben („Save as default“) – das sind keine Configs einer Bin.
- Versionsnummer (bleibt 1.1.0).

## Ende-zu-Ende-Kriterium

- pytest: eine Bin-Config im Stand 2fea2a1 (ohne die sechs Felder), gelesen über einen Dialogzustand mit allen sechs
  Feldern auf dem Gegenteil (volle Lippe, ungetrimmt, gerundete Schale, Trennwände bis oben, Farbe Rot, Spiel 0,5 mm),
  ergibt `Light`, `True`, `False`, `False`, `''`, `0.3`. Ebenso über `rebuildUtils.configWithParameters`.
- pytest: eine Baseplate-Config ohne Plattenspalt mit `xyClearance` 0,2 mm ergibt `plateEdgeClearance` 0,2 mm; 0,5 mm
  ergibt 0,5 mm und liegt im Dialogbereich; mit `plateClearance` 0,6 mm bleibt es 0,3 mm.
- Klicktest (`dev-notes/klicktest-r32.md`): im Bin-Dialog Gegenteil-Werte einstellen, alte Config-Datei laden, die
  sechs Eingaben stehen auf den Altwerten. Fusion-Lauf nicht nötig: die Builder ändern sich nicht, nur die gelesenen
  Werte, und die Altwerte sind die Vorgaben, mit denen die bestehenden Snapshots schon bauen.
