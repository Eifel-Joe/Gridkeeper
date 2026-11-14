# Runde 9 – Einleger-Text einzeilig

Stand 2026-11-14. Ergänzt `2026-11-14-cullenect-labels-design.md` (Abschnitt Text, Befund Spike, p50).
Punkte p84 „Einleger: Text bricht schon beim Erzeugen um und ragt über den Rand“ und p70 „Einleger: deutlich längerer
Text ragt über den Einleger hinaus“ (Jörgs Wahl: „Text einzeilig ohne Umbruch“).

## Befund (Fusion, 14.11.2026)
- Jörgs Einleger 1U „Welle 6mm“, bündig, ohne Symbol: Text in Arial, 4,961 mm, im mehrzeiligen Rahmen x 1–35 mm.
  Die Anpassung misst die **Umrisse** der Buchstaben (34,27 mm bei 5 mm Höhe) und passte die Zeile auf genau 34,0 mm
  ein. Fusion bricht im Rahmen nach der **Laufweite** um (Umrisse plus Seitenabstände der Buchstaben): Im selben
  Rahmen wird „Welle 6mm“ zweizeilig, y −0,94 bis 11,85 mm (in Jörgs Dokument und im Nachbau gleich).
- Text entlang einer Linie (`setAsAlongPath`, links ausgerichtet, über der Linie) bricht nie um: Mit Text-Parameter
  auf 170 mm verlängert bleibt er ein Band gleicher Höhe, die Extrusion nimmt neue Buchstaben mit, gesund.
  Er beginnt mit dem Seitenabstand des ersten Buchstabens (0–0,5 mm rechts der Linie) und reicht um den
  Seitenabstand des letzten über das Linienende (0,2 mm bei „Welle 6mm“).
- Wird die Linie **nach** dem Text fixiert, lehnt Fusion jede Extrusion des Textes ab („Ein Eingabeargument ist
  ungültig“). Vor dem Text fixiert, Punkte danach fixiert: Extrusion gelingt, Skizze `isFullyConstrained`.

## Entscheidung
- Jede Textzeile steht auf einer eigenen fixierten Konstruktionslinie von linkem Rand bis vor das Symbol (bzw. bis
  zum rechten Rand), Grundlinie um die halbe Versalhöhe unter der Zeilenmitte (wie vorher die Mitte des Rahmens).
  Live-Text am Text-Parameter (p50) bleibt.
- Beim Erzeugen bleiben 5 % der Breite frei (`TEXT_WIDTH_RESERVE`), für die Seitenabstände, die die Messung nicht
  sieht.
- Ein später längerer Text wird nicht neu eingepasst: er bleibt einzeilig und läuft nach rechts weiter, Richtung
  Symbol und darüber hinaus über den Einleger. Kürzen oder neu erzeugen liegt beim Benutzer.
- Verworfen: breiterer Rahmen nach rechts (reichte über das Symbol). Rahmen nur eine Zeile hoch nicht ausprobiert:
  er hätte den Umbruch nicht verhindert, nur verschoben.

## Nicht dazu
- Bin-Labels (`labelGenerator.createLabel`) nutzen weiter den mehrzeiligen Rahmen; ob sie bei knapper Breite ebenso
  umbrechen, ist eigener Punkt.

## Prüfung
- pytest: Reserve in `fittedLineHeight`, Prüfung `insertTextProblems` (Jörgs gemessener Fall rot), Testfälle mit
  `texts` (Text-Parameter nach dem Erzeugen).
- Snapshot-Lauf: jeder Einleger-Fall prüft, dass die Buchstabenkörper so viele y-Bänder bilden wie Zeilen und auf dem
  Einleger liegen (verlängerter Text: rechts darf er weiterlaufen). Neue Fälle `label_1u_welle_6mm` (vorher rot:
  2 Zeilen, Text außerhalb) und `label_1u_welle_6mm_text_edited` (vorher rot: 2 Zeilen).
- Label-Snapshots erneuert: Buchstaben bis 0,5 mm weiter rechts (Seitenabstand), bei knapper Breite 5 % kleiner;
  Einleger und Symbole sonst unverändert.
