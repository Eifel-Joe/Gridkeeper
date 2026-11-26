# Farben und mehrfarbiger Druck { #colors-and-multicolor-printing }

Beschriftungen von Behältern und Texte von Einlegern lassen sich in einem zweiten Filament drucken. Gridkeeper macht
die Buchstaben und Symbole zu eigenen Körpern mit einer Farbe, sodass der Slicer sie als getrennte Teile sieht.

## Beschriftungen von Behältern { #bin-labels }

**Beschriftungsfarbe** im Abschnitt der Beschriftungslasche: *Ohne*, *Schwarz*, *Weiß*, *Rot*, *Orange*, *Gelb*,
*Grün*, *Blau*, *Grau* oder *Benutzerdefiniert* mit einem `#rrggbb`-Wert in **Benutzerdefinierte Farbe**.

- **Ohne** funktioniert wie in GridfinityGenerator: Erhabene Buchstaben werden mit dem Behälter verbunden,
  eingravierte und Umriss-Buchstaben werden ausgeschnitten. Die Buchstaben einer Umriss-Beschriftung erscheinen in
  Fusion in einer eigenen dunklen Darstellung, `Gridfinity label`; ändern Sie deren Farbe in den Darstellungen der
  Konstruktion, um alle zu ändern.
- **Eine Farbe** behält die Beschriftung als eigene Körper: Erhabene Buchstaben werden nicht mit dem Behälter
  verbunden, eingravierte und Umriss-Buchstaben füllen ihren Ausschnitt bündig.

## Einleger { #inserts }

**Textfarbe** im Dialog des Einlegers, mit denselben Auswahlmöglichkeiten. Text und Symbol eines Einlegers sind immer
eigene Körper, *Erhaben*, *Vertieft* oder *Bündig*; die Farbe bestimmt nur ihr Aussehen.

## In der Konstruktion { #in-the-design }

Die farbigen Körper liegen in einer Komponente **Text** innerhalb des Behälters oder Einlegers, sodass sie zusammen
und getrennt vom Behälter exportiert werden. Ihre Darstellung ist ein umgefärbter Kunststoff aus der Bibliothek mit
dem Namen `Gridfinity label RRGGBB`. Sie wird an der Komponente Text gesetzt, sodass auch Buchstaben, die ein
längerer Text später hinzufügt, die Farbe erhalten. Unfarbige Beschriftungen von Behältern haben keine eigenen Körper
und erhalten keine Komponente Text.

![Ein Behälter mit einer roten erhabenen Beschriftung aus einem Mutternsymbol und dem Text Bolts](../assets/images/colored-label.png)

## Exportieren { #exporting }

Am einfachsten geht es mit **Gridkeeper Export**: eine 3MF-Datei mit jedem Teil, der Beschriftungstext mit einem
Filamentindex bemalt, den der Slicer übernimmt, siehe [Für den Druck exportieren](export.md). Er gibt dem gesamten
Beschriftungstext dasselbe Filament.

Um jeder Farbe ein eigenes Filament zu geben, exportieren Sie von Hand: Klicken Sie mit der rechten Maustaste im
Browser auf die **Komponente** des Behälters oder Einlegers und wählen Sie **Als Netz speichern**, Format **3MF**,
oder verwenden Sie **Datei › Exportieren** mit 3MF. Beim Export der Komponente wird das Modell mit seiner Komponente
Text übernommen; jeder Körper ist ein eigenes Objekt in seiner Farbe.

!!! note "Bekannte Einschränkung"
    Ein 3MF-Export führt jeden Buchstaben als eigenes Objekt auf, nicht die Komponente Text als ein Teil. Wählen Sie
    sie im Slicer gemeinsam aus.

## Bambu Studio { #bambu-studio }

1. Öffnen Sie die 3MF-Datei oder ziehen Sie sie auf die Druckplatte. Wenn Bambu Studio fragt, ob die Datei als ein
   einzelnes Objekt mit mehreren Teilen geladen werden soll, antworten Sie mit **Ja**: Der Behälter und seine
   Buchstaben bleiben als ein Objekt zusammen, die Buchstaben als dessen Teile.
2. Öffnen Sie in der Liste **Objekte** das Objekt: Der Körper des Behälters und die Buchstabenkörper sind als seine
   Teile aufgeführt.
3. Wählen Sie die Buchstabenteile aus (das erste anklicken, das letzte mit Umschalttaste anklicken) und stellen Sie
   ihr Filament auf Ihre Beschriftungsfarbe, in der Filamentspalte der Liste oder per Rechtsklick › **Filament
   ändern** („Change Filament“). Der Körper des Behälters behält das Basisfilament.
4. Slicen Sie und prüfen Sie in der Vorschau, dass jeder Buchstabe die Beschriftungsfarbe hat.

Erhabene Buchstaben werden auf den Behälter oder Einleger gedruckt. Eingravierte, Umriss-, vertiefte und bündige
Buchstaben füllen ihren Ausschnitt bündig, sodass der Farbwechsel innerhalb der obersten Schichten stattfindet.

Andere Slicer funktionieren genauso: Laden Sie die 3MF-Datei als ein Objekt mit Teilen und geben Sie den
Buchstabenteilen ein eigenes Filament. Wenn ein Slicer die Teile als getrennte Objekte lädt, behalten sie ihre
Positionen; gruppieren oder fügen Sie sie zusammen, bevor Sie Filamente zuweisen.

## Druckbarer Text { #printable-text }

Eine 0,4-mm-Düse legt Linien von etwa 0,42 bis 0,45 mm Breite. Unterhalb der Höhe, bei der der dünnste Strich eines
Textes eine solche Linie ist, lässt ein Slicer Teile der Buchstaben weg: Normal 4,43 mm, Fett 3,42 mm, Extrafett
3,05 mm, an den Buchstaben in Fusion gemessen. Beschriftungen von Behältern werden nie darunter angepasst; Einleger
können es, und eine Meldung nach dem Bauen weist darauf hin. Verwenden Sie für kleine Einleger **Extrafett**, seine
Striche sind etwa 1,5-mal so breit wie die von Normal.
