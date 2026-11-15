# Runde 17: Einleger-Geometrie

Stand 15.11.2026, von Nutzer in der Hauptsitzung freigegeben. Sammelbetrieb R14–R18, Branch von `runde-14-18`
nach dem Merge von R14 (beide ändern den Einleger-Generator).

## Punkte
- p110 „Einleger mit zwei Zeilen und negativer Höhenkorrektur: Unterlängen ragen unten über den Rand“
- p140 „Vertiefter Einleger: Symbol in voller Höhe kerbt den Rand ein“
- p52 „Einleger-Text passt sich einer nachträglich kleineren Breite nicht an“
- p51 „Hardware-Symbole schneller machen (Einleger mit Mutter braucht gut 20 Sekunden)“

## Druckbarkeit (Nutzer 15.11.2026)
Maßstab: 0,4-mm-Düse, Bambu-Standard-Druckprofil (0,2 mm Schicht), bestenfalls Arachne-Wandgenerator.

**Schriftgrößen-Untergrenze:** Keine Verkleinerung unter die Größe, bei der der dünnste Strich der verwendeten Schrift
schmaler als 0,4 mm wird. Die Runde bestimmt diese Größe aus der Schrift (Messung an Fusion-Text, Beleg ins
Protokoll) und legt sie als Konstante ab. Reicht die Untergrenze nicht für den Einleger, wird nicht weiter verkleinert:
Die Prüfung meldet das Problem und der Dialog sperrt OK, wie die übrigen Einleger-Prüfungen in
`cullenectLabelLayout.py`.

## Entscheidungen
1. **p110:** Bei zwei Zeilen und negativer Höhenkorrektur wird die Schrift so weit verkleinert (nicht unter die
   Untergrenze), dass Unterlängen (g, j, p, y) innerhalb des Einlegers bleiben.
2. **p140:** Bei „vertieft“ wird das Symbol so begrenzt, dass die oberste Randschicht (Überstand über die Rastschicht)
   ganz bleibt. „Bündig“ und „erhaben“ bleiben, wie sie sind.
3. **p52:** Vor dem Symbol bleibt beim Bauen 1 mm Luft, damit der Text bei leicht schmalerem Einleger das Symbol nicht
   berührt. Deutlich schmaler: weiter neu erzeugen.
4. **p51:** Symbol-Dateien mit gröberen Kreisen neu erzeugen (Werkzeuge in `tools/cullenect`). Ziel: Einleger mit
   Nylonmutter unter 5 s. Sichtbar gleich bei 0,4-mm-Düse: Abweichung der Kontur höchstens 0,05 mm. Herkunft und
   Erzeugung bleiben dokumentiert, die MIT-Hinweise von CullenJWebb bleiben.

## Nicht dabei
- Text kürzer machen über p52 hinaus, Schriftartwahl.

## Ende-zu-Ende-Kriterium
- Einleger mit zwei Zeilen „gjpy“/„Agjp“, Höhenkorrektur −1 mm: tiefster Punkt der Schrift ≥ Unterkante Einleger.
- Höhenkorrektur so stark, dass die Untergrenze greift: Prüffunktion meldet das Problem.
- Einleger 25 mm mit Schraube, vertieft: oberste Randschicht durchgehend (Volumen-/Querschnittsprüfung).
- Einleger mit Text, danach Breite −1 mm: Abstand Text–Symbol > 0.
- Bauzeit Einleger mit Nylonmutter < 5 s; Crimp-Ring gemessen und protokolliert.
- pytest grün, Snapshot-Tests grün (bekannte p30-Fälle ausgenommen).
