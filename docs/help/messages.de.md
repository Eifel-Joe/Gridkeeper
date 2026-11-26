# Meldungen und gesperrtes OK { #messages-and-locked-ok }

Gridkeeper zeigt auf vier Wegen, dass etwas nicht funktioniert: **OK** bleibt ausgegraut (der Dialog nennt den Grund,
wo er kann), eine Meldung nach dem Erstellen, das Fenster **Gridkeeper Fehler**, wenn ein Erstellen fehlschlägt, und
Hinweise nach einem Neuerstellen. Diese Seite führt alle auf, mit dem, was Sie tun können.

## OK bleibt gesperrt { #ok-stays-locked }

| Dialog | Meldung oder Grund | Was zu tun ist |
|---|---|---|
| Behälter | **Cullenect: Cullenect-Steckplätze brauchen Wände von mindestens 1,2 mm** (in der Tabelle Tatsächliche Maße) | Stellen Sie **Wandstärke** auf 1,2 mm oder mehr, oder wählen Sie einen anderen Beschriftungsstil |
| Behälter | **Wählen Sie mindestens eine Zelle aus** (Zeichnung der eigenen Form) | Klicken Sie mindestens eine Zelle an, oder schalten Sie **Eigene Form** ab |
| Behälter | **Alle Zellen müssen ein zusammenhängendes Teil bilden, verbunden entlang ihrer Seiten** | Zellen, die sich nur an einer Ecke berühren, zählen nicht; verbinden Sie sie |
| Behälter | Eine **Eigene Farbe**, die nicht `#rrggbb` ist | Geben Sie eine Farbe wie `#D02020` ein |
| Behälter | Ein Wert außerhalb seines Bereichs: Rastereinheit über 10 mm, Höheneinheit über 5 mm, Spiel XY 0,1 bis 0,5 mm, Breite und Länge in halben Einheiten, Höhe mindestens 1, Wand 0,4 bis 2 mm, Überhangwinkel Lasche 30° bis 65°, Laschenwinkel oben 0° bis 45°, Spiel des Steckplatzes 0 bis 1 mm, eine Schraubenbohrung über 1 mm und kleiner als die Magnetaussparung | Korrigieren Sie den Wert; Fusion zeigt ihn rot an |
| Grundplatte | **Die Rastereinheiten müssen größer als 0 sein**, **Die Plattengröße muss mindestens 1 x 1 u betragen** (unter Ergebnis) | Korrigieren Sie die Größe |
| Grundplatte | **Die Fläche ist zu klein für eine einzelne Zelle** | Machen Sie die Fläche größer als eine Zelle plus Spiel |
| Grundplatte | **Das Druckbett ist zu klein für eine einzelne Zelle mit der Seitliche Auffüllung** | Wählen Sie ein größeres Druckbett, einen kleineren Rand des Druckbetts oder weniger Auffüllung |
| Grundplatte | Spiel außerhalb des Bereichs, Magnet über 10 mm, Schraubenbohrung über 10 mm, Schraubenkopf nicht größer als die Schraubenbohrung oder über 15 mm, Verbindungsloch über 5 mm | Korrigieren Sie den Wert |
| Einleger | **Ein Einleger ist 10 bis 300 mm breit** | Ändern Sie die Breite oder die Korrektur |
| Einleger | **Ein Einleger ist mindestens 5 mm hoch** | Wählen Sie die Höhenkorrektur kleiner |
| Einleger | **Korrekturen betragen höchstens 1 mm in jede Richtung** | Halten Sie beide Korrekturen zwischen −1 und 1 mm |
| Einleger | **Die Rastereinheit Breite beträgt mindestens 10 mm** | Korrigieren Sie **Rastereinheit X (mm)** |
| Einleger | **Kein Platz für das Symbol, machen Sie den Einleger breiter** | Breiterer Einleger oder kein Symbol |
| Einleger | **Kein Platz für Text neben dem Symbol, machen Sie den Einleger breiter** | Breiterer Einleger oder kein Symbol |
| Einleger | **Zwei Zeilen passen nicht in diese Höhe: Ihre Unterlängen würden über den Rand reichen, und die Buchstaben können nicht kleiner werden, ohne zu dünn zum Drucken zu sein. Verkleinern Sie die Höhenkorrektur, verwenden Sie eine Zeile oder den Stil Extrafett** | Wie in der Meldung beschrieben |
| Einleger | **Keine SVG-Datei für dieses Symbol** | Die gewählte Kombination hat keine Symboldatei; wählen Sie eine andere (tritt nur bei von Hand geänderten Symbolordnern auf) |
| Einleger | **Diese Aufnahme ist zu klein für den Einleger, wählen Sie eine passende aus** | Wählen Sie eine größere Aufnahme oder machen Sie den Einleger schmaler |
| Einleger | Eine **Eigene Farbe**, die nicht `#rrggbb` ist | Geben Sie eine Farbe wie `#D02020` ein |

## Meldungen nach dem Erstellen { #messages-after-building }

| Meldung | Bedeutung |
|---|---|
| **Dieses Dokument war eine Bauteilkonstruktion. Es wurde in eine Hybride Konstruktion umgewandelt, damit das erzeugte Teil (Behälter) eine eigene Komponente ist. Eine Konstruktion mit Komponenten kann nicht mehr in eine Bauteilkonstruktion zurückgestellt werden.** | Wird einmal angezeigt, wenn das erste Modell in einer Bauteilkonstruktion erstellt wird. Siehe [Komponenten und Gelenke](../working/components.md#part-designs). |
| **„M3“: 2,8 mm hoch, unter den 3,05 mm, die eine 0,4-mm-Düse im Stil Extrafett druckt. Kürzen Sie den Text, machen Sie ihn breiter oder verwenden Sie den Stil Extrafett.** (Einleger) | Der Text wurde unter die Druckgrenze seines Stils eingepasst, eine 0,4-mm-Düse lässt Teile der Buchstaben aus. Der Einleger wird trotzdem erstellt. |
| **„…“: … mm hoch, unter den … mm, die eine 0,4-mm-Düse im Stil Normal druckt. Machen Sie die Lasche breiter oder verwenden Sie den Stil Fett.** (Behälter) | Nur bei einer Lasche, die niedriger als die Druckgrenze ist. Der Behälter wird trotzdem erstellt. |
| **Geladen „file.json“ mit Änderungen:** gefolgt von *Nicht erkannt, übersprungen:*, *Nicht in der Datei, aktueller Wert beibehalten:*, *Unbekannte Option, Vorgabe verwendet:* | Eine Einstellungsdatei einer anderen Version, siehe [Einstellungen speichern und laden](../working/save-load.md#loading-older-or-other-files). |

Die Vorschau zeigt den Hinweis auf dünnen Text ebenfalls: **Letzte Vorschau** erhält „, Text unter der Druckgrenze“.

## Erstellen fehlgeschlagen: das Fenster Gridkeeper Fehler { #build-failed-the-gridfinity-error-panel }

Schlägt ein Erstellen fehl, bleibt ein Fenster **Gridkeeper Fehler** offen, mit dem Fehler, dem Stacktrace und den
Einstellungen, mit denen erstellt wurde (bei einem Neuerstellen zusätzlich den Einstellungen davor). **Bericht
kopieren** kopiert alles für einen Fehlerbericht, **Kopieren und Issue öffnen** öffnet zusätzlich die Issue-Seite.

Fehler, die Sie selbst beheben können:

| Fehler | Was zu tun ist |
|---|---|
| **„…“ passt nicht auf die Beschriftung, auch nicht bei 4,4 mm, der geringsten Höhe, die eine 0,4-mm-Düse druckt. Kürzen Sie den Text oder machen Sie den Behälter breiter.** | Der Beschriftungstext eines Behälters ist für seine Lasche zu lang, siehe [Textgröße](../bins/labels.md#text-size). Eine größere **Länge der Lasche (u)** hilft ebenfalls. |
| **„…“ passt nicht auf die Beschriftung, auch nicht bei … mm, so hoch, wie seine Lasche es zulässt. Kürzen Sie den Text oder machen Sie den Behälter breiter.** | Dasselbe bei einer Lasche, die niedriger als die Druckgrenze ist. |
| **Die Zeitachse muss aktiviert sein, damit der Generator funktioniert, Projekte mit deaktiviertem Konstruktionsverlauf werden derzeit nicht unterstützt** | Schalten Sie **Konstruktionsverlauf erfassen** ein (Rechtsklick auf die Dokumentwurzel im Browser). |

## Neu erstellen { #rebuild }

| Meldung | Bedeutung |
|---|---|
| **Der Behälter wurde neu erstellt. Diese Elemente danach müssen geprüft werden, solche, die eine Fläche oder Kante des alten Behälters verwenden, müssen neu ausgewählt werden:** und eine Liste | Öffnen Sie jedes aufgeführte Element in der Zeitachse und wählen Sie ihre Flächen oder Kanten neu aus. Ebenso bei Grundplatten und Einlegern. |
| **…: Der Einleger passt nicht mehr in die neu erstellte Aufnahme …, … x … mm in … x … mm** (in dieser Liste) | Eine Aufnahme des neu erstellten Behälters ist kleiner geworden als der Einleger, der per Gelenk darin sitzt. Erstellen Sie den Einleger schmaler neu. |
| **Die Aufnahme, in der der Einleger saß, …, konnte nicht ausgewählt werden. Wählen Sie sie erneut aus, sonst wird der Einleger ohne Gelenk an der alten Stelle erstellt.** (Dialog Einleger) | Wählen Sie den Gelenkursprung der Aufnahme unter **Aufnahme** erneut aus. |
| **Der Behälter dieser Aufnahme liegt in der Zeitachse hinter dem Einleger, der Einleger kann nicht an Ort und Stelle in dieser Aufnahme neu erstellt werden** | Der Einleger ist älter als der Behälter; erstellen Sie stattdessen einen neuen Einleger in der Aufnahme. |
| **Zum Neuerstellen muss der Konstruktionsverlauf, die Zeitachse, eingeschaltet sein** | Schalten Sie **Konstruktionsverlauf erfassen** ein. |
| **Die Zeitachsengruppe …, in der das Modell erzeugt wurde, wurde nicht gefunden, sie wurde möglicherweise aufgelöst** / **In der Zeitachsengruppe … wurden keine erzeugten Körper gefunden** | Die Zeitachsengruppe des Modells wurde aufgelöst oder geleert; Gridkeeper findet nicht, was ersetzt werden soll. Erstellen Sie mit **Gridkeeper klonen** ein neues Modell. |
| **Der neu zu erstellende Körper ist nicht mehr im Design vorhanden** | Der Körper wurde gelöscht, nachdem das Menü geöffnet wurde. |
| **Wählen Sie einen erzeugten Behälter, eine Grundplatte oder einen Einleger aus, um ihn neu zu erstellen.** / **… um ihn zu klonen.** | Die Auswahl ist kein Gridkeeper-Modell; wählen Sie seinen Körper aus. |

## Einstellungsdateien { #settings-files }

| Meldung | Bedeutung |
|---|---|
| **Die Konfiguration konnte nicht gelesen werden. Es ist keine JSON-Datei, …** | Die Datei ist kein gültiges JSON. |
| **… Es ist die Konfiguration für „Grundplatte“, nicht für „Behälter“** | Eine Datei eines anderen Generators. |
| **… binWidth muss eine Zahl sein, nicht „two“** | Eine Einstellung vom falschen Typ; die Datei wird als Ganzes abgelehnt. |
| **Die Konfiguration konnte nicht in … gespeichert werden** / **… konnte nicht gelesen werden** / **Das Kopieren in die Zwischenablage ist fehlgeschlagen** | Ein Datei- oder Zwischenablagefehler des Systems. |
