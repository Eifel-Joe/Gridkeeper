# Runde 19: Bin-Label-Text beim Verlängern

Stand 15.11.2026. Von der Hauptsitzung geschrieben auf Jörgs Auftrag („Setz die offenen neuen Punkte auch mit in die
Bearbeitung. Je mehr erledigt ist bis ich wieder da bin desto besser.“). Die Entscheidung unten legt Jörg beim
Testtermin noch einmal vor. Branch von `runde-14-18` nach dem Merge von R18.

## Punkt
- p181 „Bin-Label-Text läuft beim Verlängern über den Bin-Rand“

## Problem
Ein Bin-Label-Text, der das Label schon füllt, behält beim Verlängern über seinen Text-Parameter die Buchstabenhöhe
und wächst nach rechts. In Runde 14 reichte er bis 105 mm bei einer 99,5 mm breiten Bin.

## Anforderungen
1. Nach dem Ändern des Text-Parameters liegt kein Buchstabe außerhalb der Label-Fläche seines Fachs.
2. Die Schrift wird dabei nicht kleiner als die Untergrenze aus Runde 17.
3. Kurzer Text bleibt so groß wie gebaut (keine Vergrößerung über die gebaute Höhe).
4. Skizzen bleiben vollständig bestimmt; Einfärbung und Text-Komponente (Runde 14) bleiben erhalten.

## Optionen
- **A: Schrifthöhe folgt der Textlänge** über die Parameter (Ausdruck mit `min()` aus gebauter Höhe und verfügbarer
  Breite), so wie die Laschen-Spanne in Runde 15. Nur möglich, wenn Fusion die Höhe eines Skizzentexts an einen
  Parameter bindet – das prüft die Runde zuerst in Fusion (Beleg ins Protokoll).
- **B: Neubau per Rechtsklick** passt die Schrift wieder ein; beim Ändern per Parameter wächst der Text weiter.

## Entscheidung
A, wenn Fusion es trägt; sonst B, und die Prüfung beim Neubau meldet, wenn der Text auch mit der Untergrenze nicht
passt. Passt der Text in A auch mit Untergrenze nicht, bleibt er auf der Untergrenze und der Neubau per Rechtsklick
meldet es.

## Nicht dabei
- Zeilenumbruch, Text kürzen, Einleger (dort regelt das Runde 17).

## Ende-zu-Ende-Kriterium
- Bin 2x1 mit zwei Fächern, Label-Text füllt das Label, Text per Parameter um 5 Zeichen verlängert: alle Buchstaben in
  x innerhalb der Label-Fläche ihres Fachs (A) bzw. nach Rechtsklick-Neubau (B).
- Kurzer Text verlängert, der noch passt: Höhe unverändert.
- Label-Skizzen vollständig bestimmt, Timeline ohne Fehler; pytest und Snapshot-Tests grün.
