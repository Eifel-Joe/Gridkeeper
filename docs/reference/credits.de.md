# Danksagung und Lizenz { #credits-and-license }

Gridkeeper ist unsere Weiterentwicklung des GridfinityGenerator. Es baut auf der Arbeit von folgenden Personen auf:

| Wer | Was | Lizenz |
|---|---|---|
| **Le0Michine** (Lev Mishin) | [FusionGridfinityGenerator](https://github.com/Le0Michine/FusionGridfinityGenerator), das Zusatzmodul, auf dem Gridkeeper aufbaut; seine Historie und Urheberschaft bleiben im Repository erhalten | CC BY-NC-SA 4.0 |
| **CullenJWebb** | [Cullenect-Labels](https://github.com/CullenJWebb/Cullenect-Labels): Maße von Einlegern und Aufnahmen, Geometrie und Layout der Einleger, die Schrauben- und Befestigungssymbole | MIT |
| **ostat / Chris Heazlewood** | [gridfinity_extended_openscad](https://github.com/ostat/gridfinity_extended_openscad), Referenz für die Cullenect-Lasche | als Referenz verwendet |
| **Pred** | [Gridfinity Storage Box v1.1 (parametric)](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric): Größe und Form der Aufbewahrungsbox und ihres Deckels, im Code nachgebaut, mit Änderungen, die auf [Aufbewahrungsboxen](../boxes.md) vermerkt sind; ihre Verschlüsse, Griff, Griffstifte und Scharniere, nach Preds Datei im Code gezeichnet | CC BY-NC |
| **Zack Freedman** | [Gridfinity](https://www.youtube.com/watch?v=ra_9zU-mnl8), das System selbst | |

Alle Bilder und Animationen dieser Dokumentation stammen von Gridkeeper selbst und sind mit Gridkeeper in Fusion
entstanden; die Animationen folgen dem Aufbau der README-Animationen des GridfinityGenerator (Modell, Dialog,
Bildunterschrift).

Die Symbole für Madenschrauben sind eine eigene Arbeit von Gridkeeper unter MIT, die Gewinde- und Antriebsformen von
Cullenect verwendet.

## Lizenz { #license }

Gridkeeper steht unter einer
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/),
wie der GridfinityGenerator, auf dem es aufbaut. Die Cullenect-Symbole behalten ihre MIT-Lizenz, siehe
`LICENSE-Cullenect` in `lib/gridfinityUtils/cullenectIcons/`.
Die Aufbewahrungsbox folgt [Preds parametrischer Gridfinity Storage Box v1.1](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric) (CC BY-NC): Gridkeeper baut ihre Form im Code nach, mit den Änderungen, die auf [Aufbewahrungsboxen](../boxes.md) vermerkt sind, und nennt Pred dafür als Urheber; der Nachbau ist Teil von Gridkeeper unter CC BY-NC-SA, Preds eigene Dateien bleiben unter Preds Lizenz.

## Wie es entsteht { #how-it-is-made }

Gridkeeper ist vibe-codiert: Sein Code wird von einer KI, Claude, unter der Leitung von Eifel-Joe geschrieben, der die
Funktionen entwirft, sie in Fusion testet und die Ergebnisse druckt. Jede Änderung wird durch automatisierte Tests,
durch Formtests in Fusion und durch Durchklicken der Dialoge geprüft; Drucke folgen. Dennoch sind Ecken und Kanten zu
erwarten, und bitte
[melden Sie, was Ihnen auffällt](https://github.com/Eifel-Joe/Gridkeeper/issues).
