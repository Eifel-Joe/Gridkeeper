# Gridkeeper

Gridkeeper ist ein Zusatzmodul für Autodesk Fusion, das [Gridfinity](https://www.youtube.com/watch?v=ra_9zU-mnl8)-Grundplatten,
-Behälter, austauschbare [Cullenect](https://github.com/CullenJWebb/Cullenect-Labels)-Einleger und Aufbewahrungsboxen
mit Deckel erzeugt. Es ist unsere Weiterentwicklung des
[GridfinityGenerator](https://github.com/Le0Michine/FusionGridfinityGenerator) von Le0Michine (Lev Mishin): Alles, was
der GridfinityGenerator kann, ist weiterhin vorhanden, erweitert um Cullenect-Aufnahmen und -Einleger, Aufbewahrungsboxen
nach Pred, farbige Beschriftungen für den Mehrfarbdruck, eine Baugruppe aus Komponenten mit Gelenken, einen Export für den
Slicer sowie eine Reihe von Korrekturen und kleineren Funktionen, siehe [Neuerungen](getting-started/whats-new.md).

![Drei Gridkeeper-Behälter auf einer Grundplatte, mit Beschriftungen und Symbolen in Rot und Blau](assets/images/home-hero.png)

## Was es erzeugt { #what-it-builds }

| Modell | Was es ist |
|---|---|
| **[Grundplatten](baseplates.md)** | Platten aus Steckplätzen für die Behälter, leicht, voll oder skelettiert, mit Magneten und Schrauben, oder eine ganze Schublade, gefüllt und in Stücke geteilt, die auf Ihr Druckbett passen. |
| **[Behälter](bins/index.md)** | Behälter vom Typ Hohl, Schale oder Voll in beliebiger Größe in ganzen oder halben Rastereinheiten, Eigene Formen, Fächer, eine Griffmulde, eine Beschriftungslasche mit Text und Symbol, Magnet- und Schraubenlöcher im Boden. |
| **[Cullenect-Beschriftungen](cullenect/index.md)** | Aufnahmen in der Beschriftungslasche eines Behälters und die Einleger, die dort einrasten, mit Text und einem Schrauben- oder Hardwaresymbol, zweifarbig gedruckt und ausgetauscht, wenn sich der Inhalt ändert. |
| **[Aufbewahrungsboxen](boxes.md)** | Eine Box mit Deckel nach Preds parametrischer Gridfinity Storage Box: Behälter sitzen in ihrem Boden, ihr Deckel trägt ein Raster oder eine geschlossene Oberseite, mit Verschlüssen, Griff und Scharnieren sowie einem Etikett für den Halter an der Vorderseite. Stapelbar und verriegelbar mit Boxen, die nach Preds eigener Datei gedruckt wurden. |

Jedes Modell ist parametrisch und merkt sich, wie es erzeugt wurde: Klicken Sie mit der rechten Maustaste darauf, um seine
[Einstellungen zu sehen, es neu zu erstellen oder zu klonen](working/settings-rebuild-clone.md), oder ändern Sie seine
[Benutzerparameter](working/parameters.md), ohne es neu zu erzeugen. Der [Export](working/export.md) schreibt alle Teile
in eine 3MF-Datei für den Slicer, einschließlich der Beschriftungsfarben.

## Befehle { #commands }

Nach der [Installation](getting-started/installation.md) fügt Gridkeeper diese Befehle zum Arbeitsbereich „Konstruktion“ von Fusion hinzu:

| Befehl | Wo | Was er tut |
|---|---|---|
| **Gridkeeper Grundplatte** | Volumenkörper › Erstellen | Erzeugt eine Grundplatte, siehe [Grundplatten](baseplates.md) |
| **Gridkeeper Behälter** | Volumenkörper › Erstellen | Erzeugt einen Behälter, siehe [Behälter](bins/index.md) |
| **Gridkeeper Einleger** | Volumenkörper › Erstellen | Erzeugt einen Cullenect-Einleger, siehe [Einleger](cullenect/inserts.md) |
| **Gridkeeper Box** | Volumenkörper › Erstellen | Erzeugt eine Aufbewahrungsbox mit Deckel, siehe [Aufbewahrungsboxen](boxes.md) |
| **Gridkeeper Box-Etikett** | Volumenkörper › Erstellen | Erzeugt das Etikett für den Halter an der Vorderseite einer Box, siehe [Etikett](boxes.md#label) |
| **Gridkeeper Einstellungen** | Rechtsklick auf einen erzeugten Körper | Zeigt, womit er erzeugt wurde, speichert, kopiert oder klont ihn |
| **Gridkeeper neu erstellen** | Rechtsklick auf einen erzeugten Körper | Öffnet seinen Dialog, um ihn an seiner Stelle neu zu erstellen |
| **Gridkeeper klonen** | Rechtsklick auf einen erzeugten Körper | Öffnet seinen Dialog mit seinen Einstellungen für einen neuen |
| **Gridkeeper Export** | Rechtsklick auf einen erzeugten Körper | Schreibt die Teile in eine 3MF-, STL- oder STEP-Datei, siehe [Export](working/export.md) |
| **Gridkeeper Updates** | Dienstprogramme › Zusatzmodule | Zeigt die laufende und die neueste Version und aktualisiert Gridkeeper, siehe [Installation](getting-started/installation.md) |
| **Gridkeeper tests: run** | Dienstprogramme › Zusatzmodule, nur Git-Checkouts mit einem Ordner `.git` | Formtests (Snapshot-Tests) für Entwickler, siehe [Snapshot-Tests](developers/snapshot-tests.md) |

## Vibe-codiert, durch Drucken getestet { #vibe-coded-tested-by-printing }

Gridkeeper ist vibe-codiert: Sein Code wird von einer KI, Claude, geschrieben, unter der Leitung von Eifel-Joe, der die
Funktionen entwirft, in Fusion testet und die Ergebnisse druckt. Jede Änderung wird durch automatisierte Tests, durch
Formtests in Fusion und durch Durchklicken der Dialoge geprüft; der Druck folgt. Dennoch
sind Ecken und Kanten zu erwarten, und bitte [melden Sie, was Ihnen auffällt](https://github.com/Eifel-Joe/Gridkeeper/issues).

## Danksagung { #credits }

- **GridfinityGenerator** von [Le0Michine](https://github.com/Le0Michine/FusionGridfinityGenerator), CC BY-NC-SA 4.0,
  das Zusatzmodul, auf dem Gridkeeper aufbaut
- **Cullenect-Labels** von [CullenJWebb](https://github.com/CullenJWebb/Cullenect-Labels), MIT, die Einleger,
  ihre Aufnahmen und Symbole
- **Gridfinity Storage Box v1.1 (parametric)** von
  [Pred](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric), CC BY-NC, die Form
  der Aufbewahrungsbox, ihres Deckels und der Kleinteile, im Code nachgebaut
- **gridfinity_extended_openscad** von [ostat (Chris Heazlewood)](https://github.com/ostat/gridfinity_extended_openscad),
  als Referenz verwendet
- **Gridfinity** von [Zack Freedman](https://www.youtube.com/c/ZackFreedman/about)

Gridkeeper steht unter der Lizenz [CC BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/), siehe
[Danksagung und Lizenz](reference/credits.md).
