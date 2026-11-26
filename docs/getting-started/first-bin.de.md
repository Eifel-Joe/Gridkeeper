# Erster Behälter { #first-bin }

Ein kurzer Rundgang: eine Grundplatte, ein Behälter darauf mit einer Cullenect-Aufnahme und ein Einleger in der Aufnahme.

1. **Neue Konstruktion.** Beginnen Sie in Fusion eine neue Konstruktion. Gridkeeper arbeitet in Bauteilkonstruktionen und hybriden Konstruktionen; eine Bauteilkonstruktion
   wird in eine hybride Konstruktion umgeschaltet, sobald das erste Modell erzeugt wird, Gridkeeper weist in einer kurzen Meldung darauf hin.
2. **Grundplatte.** Öffnen Sie **Volumenkörper › Erstellen › Gridkeeper Grundplatte**. Setzen Sie *Größenmodus* auf *Rastereinheiten*, *Breite der Platte, X (u)* auf 3
   und *Länge der Platte, Y (u)* auf 2, klicken Sie auf **OK**. Die Platte landet in der Komponente *Grid*.
3. **Behälter.** Öffnen Sie **Volumenkörper › Erstellen › Gridkeeper Behälter**. Setzen Sie *Breite des Behälters, X (u)* auf 2, *Länge des Behälters, Y (u)* auf 1 und *Höhe des Behälters, Z (u)* auf 4. Aktivieren Sie unter
   *Fächer des Behälters › Beschriftungslasche* die Option *Beschriftungslasche hinzufügen (entlang der Behälterbreite)*, setzen Sie *Länge der Lasche (u)* auf 2 u und wählen Sie als *Beschriftungsstil* **Cullenect**. Die zweite Zeile der
   Tabelle *Tatsächliche Maße* zeigt die Größe der Aufnahme, „Cullenect: 2U: Aufnahme 78,3 mm, Einleger 78 mm“. Klicken Sie auf **OK**. Der Behälter landet in
   *Bins*.
4. **Einleger.** Öffnen Sie **Volumenkörper › Erstellen › Gridkeeper Einleger**. Lassen Sie *Breite* auf *Rastereinheiten*, setzen Sie *Breite (u)* auf 2, tippen Sie `M3x10` in *Zeile 1* und behalten Sie die
   Zylinderkopfschraube bei. Klicken Sie unter *Aufnahme* auf den Gelenkursprung in der Mitte der Aufnahme des Behälters. Klicken Sie auf **OK**: Der Einleger
   sitzt in der Aufnahme, in der Komponente *Label*.
5. **Drucken.** Exportieren Sie den Behälter und den Einleger, zum Beispiel als 3MF. Der Text des Einlegers ist ein eigener Körper, weisen Sie ihm im Slicer ein
   zweites Filament zu, siehe [Farben und Mehrfarbdruck](../working/colors.md).

![Die Grundplatte, der 2x1-Behälter mit seiner Cullenect-Aufnahme und ein M3x10-Einleger in der Aufnahme](../assets/images/first-bin-result.png)

Später können Sie mit der rechten Maustaste auf jedes davon klicken, um **Gridkeeper Einstellungen**, **Gridkeeper neu erstellen** und **Gridkeeper klonen** zu nutzen,
siehe [Einstellungen, Neu erstellen und Klonen](../working/settings-rebuild-clone.md).
