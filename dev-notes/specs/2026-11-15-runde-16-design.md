# Runde 16: Tests und Einstellungsanzeige

Stand 15.11.2026, in der Hauptsitzung freigegeben. Sammelbetrieb R14–R18, Branch von `runde-14-18`.

## Punkte
- p30 „Snapshot-Tests der Text-Labels passen auf diesem Rechner nicht“
- p31 „Vorschaubilder der Snapshot-Tests fehlen“
- p34 „Skizzen-Prüfung im Testlauf robuster machen“
- p32 „Gridfinity settings zeigen bei Cullenect die echte Laschenbreite“
- p33 „Taschenliste in den Einstellungen anders beschriften“

## Entscheidungen
1. **p30:** Für Testfälle mit Text-Labels vergleicht der Snapshot-Test die Form (Körperanzahl, Volumen, Ausmaße der
   Gesamtform) wie bisher, die Lage der einzelnen Buchstabenkörper aber nicht (hängt von Schrift und Fusion-Version
   ab). Die vier bekannten Fälle müssen danach grün sein, ohne dass Snapshots neu abgelegt werden.
2. **p31:** Die Darstellung für Vorschaubilder wird wie bei den Label-Farben gesucht (`labelColors.baseCandidates`,
   sprachunabhängig über die Bibliotheks-ID). Fehlt sie trotzdem, entsteht das Bild in der Standarddarstellung.
3. **p34:** Die Prüfung auf vollständig bestimmte Skizzen läuft auch nach der Parameteränderung eines Testfalls. Ein
   Fehler in der Prüfung selbst wird als Prüffehler gemeldet, nicht als Baufehler.
4. **p32:** Im Abschnitt Cullenect von „Gridfinity settings“ steht die tatsächlich gebaute Laschenbreite.
5. **p33:** Die Taschenliste zeigt je Größe eine Zeile mit Anzahl, z. B. „1U: 8 sockets“. Oberfläche bleibt Englisch.

## Nicht dabei
- Neue Testfälle über die genannten hinaus, Umbau des Test-Rahmens.

## Ende-zu-Ende-Kriterium
- Snapshot-Lauf in Fusion: alle Fälle grün, auch die vier Text-Fälle; neue Snapshots haben Vorschaubilder.
- Ein absichtlich kaputter Prüfschritt (Unit-Test) erscheint als Prüffehler.
- Rechtsklick „Gridfinity settings“ auf einer Cullenect-Bin mit 8 gleichen Fächern: Laschenbreite = gebaute Breite,
  Taschenliste „1U: 8 sockets“ (bzw. die gebaute Größe).
- pytest grün.
