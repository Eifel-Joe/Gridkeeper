# Neuerungen gegenüber dem GridfinityGenerator { #whats-new-compared-to-gridfinitygenerator }

Gridkeeper geht vom GridfinityGenerator v2.4.2.0 von Le0Michine aus, übernimmt dessen spätere Änderungen (etwa die Stapelrandtypen und, bis v2.6.0.0, Behälter, die in Dokumenten in Zoll gleich herauskommen, sowie beim Neuerstellen beibehaltene Namen) und behält
alles davon: Grundplatten, die eine Fläche füllen und für das Druckbett teilen, Behälter in Eigenen Formen mit
Fächern, Griffmulden und Beschriftungslaschen, gefalzte Wände, Neuerstellen und Klonen aus dem Rechtsklick-Menü, Einstellungen, die in
JSON-Dateien gespeichert werden. Darüber hinaus kommt Folgendes hinzu.
Die vollständige Liste der Änderungen, Runde für Runde, steht in
[CHANGELOG.md](https://github.com/Eifel-Joe/Gridkeeper/blob/master/CHANGELOG.md).

## Aufbewahrungsboxen { #storage-boxes }

- **Gridkeeper Box:** eine Aufbewahrungsbox mit Deckel nach [Preds parametrischer Gridfinity Storage Box v1.1](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric)
  (CC BY-NC), im Code nachgebaut
  mit vollständig bestimmten Skizzen: jede Größe ab 4 × 3 Zellen und 6 Einheiten, Stapeln und Verriegeln mit Preds gedruckten
  Boxen, Größenparameter `gfBox1_…`, Gelenkursprünge im Boden, zum Stapeln und für den Deckel. Siehe
  [Aufbewahrungsboxen](../boxes.md).
- **Magnetgröße** zur Auswahl in den Dialogen für Behälter und Grundplatte: Magnete von 6 × 2 oder 6 × 3 mm legen die Tiefe fest. Die Box nimmt
  nur Magnete von 6 × 2 mm auf, solche von 6 × 3 mm würden ihren Boden durchbrechen.

## Cullenect-Beschriftungen { #cullenect-labels }

- **Cullenect-Beschriftungsstil für Behälter:** Die Beschriftungslasche oder jede Fachlasche erhält eine Aufnahme für einen austauschbaren
  [Cullenect](https://github.com/CullenJWebb/Cullenect-Labels)-Einleger statt einer gedruckten Beschriftung, bemessen nach der
  größten passenden Standard-Cullenect-Breite, sodass auch originale Cullenect-Einleger passen. Siehe
  [Aufnahmen in Behältern](../cullenect/pockets.md).
- **Gridkeeper Einleger**, ein eigener Befehl für die Einleger: eine oder zwei Textzeilen und ein Schrauben- oder Hardwaresymbol,
  erhaben, eingelassen oder bündig, als eigene Körper für eine zweite Farbe. Siehe [Einleger](../cullenect/inserts.md).
- **Symbole:** 480 Schraubenkombinationen aus Kopf, Schaft, Gewinde, Antrieb, Flansch und Sicherungsstift, Gewindestifte und 18
  Hardwaresymbole (Unterlegscheiben, Muttern, T-Nuten-Muttern, Gewindeeinsatz, Magnet, Quetschkabelschuhe), gezeichnet nach Cullenects eigenem
  Code. Neue SVG-Dateien in den Symbolordnern erscheinen im Dialog. Siehe [Symbole](../cullenect/symbols.md).
- **Einleger per Gelenk in ihren Aufnahmen:** Jede Aufnahme hat einen Gelenkursprung; wählen Sie ihn im Einleger-Dialog, und der Einleger
  sitzt in der Aufnahme. Ein neu erstellter Behälter behält seine Einleger in ihren Aufnahmen.
- **Einleger wie Behälter:** Einleger werden auf dieselbe Weise neu erstellt, geklont, gespeichert und geladen wie Behälter und Grundplatten.

## Beschriftungen und Farben { #labels-and-colors }

- **Beschriftungsfarbe** für Behälterbeschriftungen und **Textfarbe** für Einleger: Die Buchstaben und Symbole werden eigene Körper
  in einer Farbe, bereit für einen Mehrfarbdruck; eine exportierte 3MF-Datei hat jeden in seiner Farbe. Siehe
  [Farben und Mehrfarbdruck](../working/colors.md).
- **Textstile für Einleger:** Normal, Fett und Extrafett (Arial Black). Extrafett druckt sauber mit einer 0,4-mm-Düse und ist
  die Vorgabe.
- **Druckbare Texthöhen:** Der Text einer Behälterbeschriftung wird nie unter die Höhe verkleinert, bei der sein dünnster Strich noch
  eine Linie der 0,4-mm-Düse ist (Normal 4,43 mm, Fett 3,42 mm, gemessen); Einleger melden nach dem Erstellen, wenn ihr Text
  darunter liegt (Extrafett 3,05 mm).
- **Hardwaresymbole auf Behälterbeschriftungen:** Die Cullenect-Hardwaresymbole können auch bei normalen Behältern als Beschriftungssymbole gewählt werden.
- **Beschriftungen folgen ihrem Text:** Ein Behälterbeschriftungstext, der über seinen Benutzerparameter geändert wird, folgt der Lasche, neue Buchstaben erhalten
  die Beschriftungsfarbe, und **Gridkeeper neu erstellen** passt einen längeren Text wieder an die Lasche an.

## Behälter { #bins }

- **Trennwände bis oben:** Fachtrennwände auf einer Rasterlinie reichen bis zur Oberkante des Stapelrands; die Füße eines
  darauf gestapelten Behälters haben dort eine Nut, sodass Behälter jeder Größe weiterhin stapelbar sind.
- **Gelenkursprünge folgen dem Raster:** Die Gelenkursprünge der Behälterfüße und der Steckplätze der Grundplatte bewegen sich mit den Parametern der
  Rastereinheit.
- **Cullenect-Wände:** Ein Behälter mit Cullenect-Aufnahmen braucht Wände von mindestens 1,2 mm; der Dialog weist darauf hin, statt
  eine schwache Lasche zu erzeugen.

## Export

- **Gridkeeper Export** im Rechtsklick-Menü, aus dem GridfinityGenerator (Le0Michine): eine 3MF-Datei aller Teile mit dem
  Beschriftungstext, bemalt für Bambu Studio, OrcaSlicer und PrusaSlicer, oder je eine STL- oder STEP-Datei. Gridkeeper exportiert
  auch Cullenect-Einleger und legt die farbigen Text- und Symbolkörper von Behältern und Einlegern in ihr Teil, bemalt. Siehe
  [Für den Druck exportieren](../working/export.md).
- **Druckausrichtung:** Die 3MF-Datei legt jedes Teil so, wie es gedruckt wird, Griff und Verschlüsse der Box flach,
  und verteilt sie mit Abstand über das gewählte Druckbett, eine 3MF-Datei je Platte, wenn eine nicht reicht, wobei die Ecke für den Reinigungs-
  turm frei bleibt.
- **Ein Bambu-Studio-Projekt mit allen Druckplatten** für einen Bambu-Lab-Drucker, mit den Beschriftungsfarben auf ihren Filamenten und
  den Standardprofilen des Druckers von Bambu Studio, mit aus den Beschriftungsfarben berechneten Spülmengen. Nach
  der Mehrplatten-3MF-Datei des Originals (Le0Michine), siehe
  [Ein Bambu-Studio-Projekt mit allen Druckplatten](../working/export.md#a-bambu-studio-project-with-all-plates).
- Ebenfalls aus dem GridfinityGenerator: Die Buchstaben von Umrissbeschriftungen werden in Fusion in einer eigenen Farbe angezeigt, der Behälterdialog
  zeigt die Größe des Behälters auf den Mikrometer genau, und Grundplatten legen das **Spiel am Plattenrand** je Kante fest (ältere Einstellungen
  werden als die Hälfte des alten Spalts gelesen).

## Deutsch { #german }

- **Das Zusatzmodul auf Deutsch**, wenn Fusion auf Deutsch eingestellt ist: Menüeinträge, Dialoge, Tooltips, Meldungen,
  das Einstellungsfenster, der Export und die Update-Dialoge, in den Worten der deutschen Fusion-Oberfläche. Jede andere
  Sprache bleibt Englisch. Was gespeichert wird, bleibt englisch, eine Konstruktion wandert also unverändert zwischen
  deutschem und englischem Fusion.
- **Diese Dokumentation auf Deutsch**, mit dem Sprachumschalter in der Kopfzeile.

## Updates

- **Update-Suche:** Einmal am Tag beim Start fragt Gridkeeper bei GitHub nach einer neuen Version und zeigt sie mit einem Link zu ihren
  Versionshinweisen; **Jetzt aktualisieren** ersetzt den Zusatzmodul-Ordner und behält Ihre Dialogvorgaben. Git-Checkouts werden nie
  ersetzt, und die Suche lässt sich ausschalten. Siehe [Aktualisieren](installation.md#update).

## Die Konstruktion { #the-design }

- **Eine Baugruppe aus Komponenten:** Jede Grundplatte, jeder Behälter und jeder Einleger ist eine eigene Komponente, in den Containern
  *Grid*, *Bins* und *Label*. Farbige Buchstaben liegen in einer Komponente *Text* darin, sodass sie getrennt exportiert werden. Eine Bauteilkonstruktion wird dafür
  in eine hybride Konstruktion umgeschaltet. Siehe [Komponenten und Gelenke](../working/components.md).
- **Die zuvor aktive Komponente bleibt aktiv** nach einem Erstellen, Fusion zeigt nicht alles andere halbtransparent.
- **Skripte**, die in Fusion laufen, etwa die eines MCP-Servers, können `import gridkeeper` verwenden, solange das Zusatzmodul läuft, um
  Behälter, Grundplatten, Boxen und Einleger ohne die Dialoge zu erzeugen (der Skriptzugriff des GridfinityGenerator unter einem eigenen Namen),
  und sie mit `gridkeeper.exportBodies(bodies, folder, options)` zu exportieren: 3MF mit den Beschriftungsfarben, ein Bambu-Studio-
  Projekt, STL oder STEP, wobei für alles, was das Skript offenlässt, die letzten Auswahlen des Export-Dialogs gelten, ohne Dialog oder Meldung.

## Danksagung und Benennung { #credits-and-naming }

- Die Befehle heißen **Gridkeeper Behälter**, **Gridkeeper Grundplatte**, **Gridkeeper Einleger**, **Gridkeeper
  Einstellungen**, **Gridkeeper neu erstellen**, **Gridkeeper klonen** und **Gridkeeper Export**, damit sie sich nicht mit dem ursprünglichen Zusatzmodul vermischen. Körper heißen
  weiterhin *Gridfinity bin …*, wie bisher.
- Installiert aus der ZIP-Datei eines GitHub-Releases, nicht aus dem Autodesk App Store, siehe
  [Installation](installation.md).
