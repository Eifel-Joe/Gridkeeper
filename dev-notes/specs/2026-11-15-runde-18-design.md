# Runde 18: Einleger neu bauen und Einstellungen

Stand 15.11.2026, in der Hauptsitzung freigegeben. Sammelbetrieb R14–R18, Branch von `runde-14-18`
nach dem Merge von R14 (beide berühren den Label-Befehl).

## Punkte
- p150 „Einleger per Rechtsklick neu bauen und Einstellungen speichern wie Bins“
- p151 „Alte gespeicherte Bin-Einstellungen setzen die Label-Farbe im Dialog auf None“

## Entscheidungen
1. **p150:** Einleger aus „Gridfinity label“ bekommen denselben Weg wie Bins und Grundplatten aus Version 2.4:
   Rechtsklick „Gridfinity rebuild“ baut an derselben Stelle neu (Komponente und Joint in der Tasche bleiben), dazu
   Einstellungen speichern, laden, kopieren und klonen. Den Upstream-Mechanismus wiederverwenden, nicht nachbauen.
2. **p151:** Fehlt in einer gespeicherten Konfiguration ein Feld (ältere Version), bleibt der im Dialog gewählte Wert
   stehen, statt auf None zu springen. Gilt allgemein für fehlende Felder, belegt an der Label-Farbe.

## Nicht dabei
- Neue Einstellungen für Einleger über die bestehenden hinaus.

## Ende-zu-Ende-Kriterium
- Einleger bauen, per Joint in Tasche, Rechtsklick-Neubau mit anderem Text: neuer Einleger an derselben Stelle, Joint
  intakt, nur ein Einleger in seiner Komponente.
- Einleger-Konfiguration speichern, laden, klonen: Werte gleich.
- Alte Bin-Konfiguration ohne Label-Farbe laden: Farbwahl unverändert (Unit-Test).
- Alle drei Dialoge (Bin, Baseplate, Label) öffnen sich nach Add-in-Neustart (per Skript: Befehl ausführen,
  `activeCommand` prüfen, abbrechen).
- pytest grün, Snapshot-Tests grün (bekannte p30-Fälle ausgenommen).
