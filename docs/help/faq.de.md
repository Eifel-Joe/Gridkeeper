# Fehlersuche und FAQ { #troubleshooting-and-faq }

Siehe auch [Meldungen und gesperrtes OK](messages.md) für alle Meldungen, die Gridkeeper zeigt.

## Installation

**Die Befehle erscheinen nicht unter Volumenkörper › Erstellen.**
Öffnen Sie **Dienstprogramme › Zusatzmodule › Skripte und Zusatzmodule**, prüfen Sie, dass Gridkeeper in der Liste
steht und ausgeführt wird (grüner Punkt oder *Wird ausgeführt*). Wenn nicht, wählen Sie es aus und klicken Sie auf
**Ausführen**. Aktivieren Sie **Beim Start ausführen**, damit es mit Fusion startet. Achten Sie darauf, den Ordner
gewählt zu haben, der die Dateien `.manifest` und `.py` enthält, nicht einen Ordner darüber.

**Nach einem Update hat sich nichts geändert.**
Fusion lädt das Zusatzmodul einmal beim Start. Öffnen Sie **Dienstprogramme › Zusatzmodule › Gridkeeper Updates** und
klicken Sie auf **Gridkeeper neu laden** (wird angezeigt, wenn die Version auf dem Datenträger nicht die laufende ist),
starten Sie Fusion neu, oder **Beenden** und **Ausführen** Sie das Zusatzmodul in **Skripte und Zusatzmodule**.

**Kann ich den ursprünglichen GridfinityGenerator behalten?**
Ja, siehe [Neben dem Original](../getting-started/installation.md#beside-the-original).

**Ich habe GridfinityGenerator aus dem Autodesk App Store installiert, ist das Gridkeeper?**
Nein. Der App Store enthält das ursprüngliche Zusatzmodul von Le0Michine. Gridkeeper gibt es nur über die
[GitHub-Releases](https://github.com/Eifel-Joe/Gridkeeper/releases).

## Erstellen { #building }

**Der Dialog reagiert langsam.**
Schalten Sie die Vorschau ab (**Vorschau laufend (langsam)**, **Vorschau anzeigen (langsam)**); im
Dialog Behälter zeigt **Vorschau aktualisieren** das Ergebnis jeweils bei Bedarf. Große Grundplatten mit
Gelenkursprüngen und Einleger mit Symbolen aus vielen Punkten brauchen einige Sekunden.

**Ein eingegebener Wert wurde ignoriert.**
Fusion übernimmt einen in ein Eingabefeld getippten Wert erst einen Augenblick nach der letzten Taste. Wird direkt
nach dem Tippen geklickt, erstellt OK mit dem Wert, den das Feld vorher hatte; das gilt für jedes Feld jedes Dialogs.
Drücken Sie nach dem Tippen die **Tabulatortaste** oder warten Sie einen Moment, bevor Sie auf OK klicken.

**OK ist ausgegraut.**
Ein Eingabewert liegt außerhalb seines Bereichs oder eine Prüfung ist fehlgeschlagen; der Dialog nennt den Grund, wo er
kann. Siehe [Meldungen und gesperrtes OK](messages.md#ok-stays-locked).

**Meine Bauteilkonstruktion wurde zu einer hybriden Konstruktion.**
Das ist Absicht: Jedes Modell ist eine eigene Komponente, und eine Bauteilkonstruktion kann keine Komponenten
enthalten. Siehe [Komponenten und Gelenke](../working/components.md#part-designs).

**Fusion zeigt nach dem Erstellen alles halbtransparent.**
Eine andere Komponente ist aktiv. Gridkeeper aktiviert nach jedem Erstellen die Wurzel; wurde ein Erstellen
zwischendurch abgebrochen, aktivieren Sie die Wurzel selbst (Doppelklick im Browser).

**Der Stil Cullenect ist ausgegraut oder erzeugt keine Aufnahme.**
Aufnahmen brauchen eine Beschriftungslasche, Wände von mindestens 1,2 mm, einen hohlen oder als Schale gebauten
Behälter und keine eigene Form. Ein zu schmales oder zu kurzes Fach erhält keine Aufnahme, die Tabelle Tatsächliche
Maße nennt es. Siehe [Aufnahmen in Behältern](../cullenect/pockets.md).

**Beschriftungstext, Symbol und Farbe sind ausgegraut.**
Der Beschriftungsstil ist *Cullenect*: Der Text kommt auf den Einleger. Wählen Sie einen anderen Stil, um sie
zurückzuerhalten; ihre Werte sind erhalten geblieben.

**Löcher im Boden sind ausgegraut.**
Der Behälter steht auf dem **Halbraster**: Halbe Füße haben keinen Platz für Magnet- oder Schraubenlöcher. Oder
**Füße erzeugen** ist abgeschaltet.

## Beschriftungen und Text { #labels-and-text }

**Teile meiner Buchstaben fehlen im Slicer.**
Der Text ist dünner als eine Linie einer 0,4-mm-Düse. Verwenden Sie einen fetten Stil oder **Extrafett**, eine breitere
Lasche oder einen breiteren Einleger oder einen kürzeren Text; Gridkeeper warnt nach dem Erstellen, siehe
[Druckbarer Text](../working/colors.md#printable-text).

**Ich habe einen Beschriftungstext in Parameter ändern verlängert, jetzt ragt er über die Lasche hinaus.**
Die Buchstaben behalten ihre Höhe, wenn der Text über seinen Parameter geändert wird. Rechtsklick auf den Behälter ›
**Gridkeeper neu erstellen** › **OK** passt den Text wieder an.

**Neue Buchstaben eines verlängerten Textes haben die falsche Farbe.**
Erstellen Sie den Behälter oder Einleger neu; die Farbe liegt an der Komponente Text und wird normalerweise
übernommen.

## Neu erstellen und Einstellungen { #rebuild-and-settings }

**Im Rechtsklickmenü gibt es kein Gridkeeper neu erstellen.**
Klicken Sie mit der rechten Maustaste auf den **Körper** des Modells (im Zeichenbereich oder im Browser unter der
Komponente › Bodies), nicht auf die Komponente selbst. Modelle, die von sehr alten Versionen ohne gespeicherte
Einstellungen erstellt wurden, lassen sich nicht neu erstellen.

**Nach dem Neuerstellen sind einige Elemente rot.**
Sie verwendeten eine Fläche oder Kante des alten Körpers. Die Meldung nach dem Neuerstellen führt sie auf; bearbeiten
Sie jede und wählen Sie ihre Flächen oder Kanten neu aus.

**Mein Einleger hat nach dem Neuerstellen des Behälters seine Aufnahme verlassen.**
Die gleichnamige Aufnahme fehlt im neuen Behälter oder ist zu klein geworden; die Hinweise zum Neuerstellen nennen es.
Erstellen Sie den Einleger neu und wählen Sie eine Aufnahme aus.

## Drucken { #printing }

**Der Einleger rastet nicht ein oder fällt heraus.**
Ändern Sie die Passung: **Steckplatzspiel (mm)** am Behälter (größer ist lockerer) oder **Korrektur Breite** /
**Korrektur Höhe** am Einleger (kleiner ist lockerer). Drucken Sie zuerst einen Test-Einleger.

**Die Behälter sitzen nicht plan auf der Grundplatte.**
Verwenden Sie bei Behältern und Grundplatte dasselbe **Spiel XY (mm)**. **Abschnitt oben (mm)** an der
Grundplatte lässt Behälter auf ihren Füßen statt auf den Stegen der Platte sitzen.

**Wie drucke ich die Beschriftung in einer zweiten Farbe?**
Siehe [Farben und mehrfarbiger Druck](../working/colors.md#bambu-studio).
