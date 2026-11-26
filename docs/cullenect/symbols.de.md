# Symbole { #symbols }

Die Symbole der Einleger sind SVG-Dateien, die aus Cullenects eigenem OpenSCAD-Code gezeichnet wurden, in
`lib/gridfinityUtils/cullenectIcons/` des Add-ins. Die Namen und ihre Reihenfolge stammen von Cullenect. Ihre
Rundungen sind Kreisbögen statt der Tausenden kurzer Linien, die OpenSCAD schreibt, mit höchstens 0,01 mm Abweichung.

![Einleger mit einem Gewindeeinsatz, einer Gewindestift-Schraube, Senkkopf-, Flachkopf- und Zylinderkopfschrauben, einem Ringkabelschuh, einer Unterlegscheibe und einer Mutter](../assets/images/insert-symbols.png)

<picture><source media="(prefers-color-scheme: dark)" srcset="../../assets/gif/cullenect-insert-symbol-dark.gif"><img src="../../assets/gif/cullenect-insert-symbol-light.gif" alt="Ein Einleger ohne Symbol, dann mit einer Zylinderkopfschraube, einer Sicherungsmutter (Nylon) und einer Unterlegscheibe"></picture>

## Schrauben { #screws }

Bei eingeschaltetem **Schraube** wird das Symbol zusammengesetzt aus:

| Teil | Auswahl |
|---|---|
| **Kopf** | Keine, Zylinderkopf, Senkkopf, Rundkopf, Flachkopf |
| **Schaft** | Metrisch, Blechschraube |
| **Gewinde** | Vollgewinde, Teilgewinde |
| **Antrieb** | Keine, Schlitz, Kreuzschlitz (Phillips), Phillips-Schlitz, Phillips-Vierkant, Torx/Stern, Innensechskant, Robertson/Vierkant, Dreieck |
| **Flansch** | ein oder aus |
| **Sicherheitsstift** | ein oder aus |

Jede Dropdown-Liste bietet nur an, was zusammen mit den Auswahlen darüber ein Symbol ergibt; eine Auswahl, die das nicht
tut, springt auf die erste, die es tut. **Flansch** und **Sicherheitsstift** sind gesperrt, wo kein Symbol sie hat.

**Gewindestifte:** Kopf *Keine* mit dem Antrieb *Schlitz*, *Innensechskant* oder *Torx/Stern* ergibt einen Gewindestift,
gezeichnet als sein Gewinde und daneben sein Ende mit dem Antrieb; *Metrisch* ergibt ein flaches Ende, *Blechschraube*
eine Spitze. Gewindestifte sind 1 mm breiter als die anderen Schrauben.

## Befestigungsmaterial { #hardware }

Wählen Sie **Befestigungsmaterial** statt einer Schraube: Unterlegscheibe, Sicherungsscheibe, Gewindeeinsatz, Mutter,
Vierkantmutter, Sicherungsmutter (Nylon), T-Nut seitlich, T-Nut oben, Magnet, Ringkabelschuh (offen, geschlossen),
Gabelkabelschuh (offen, geschlossen), Flachstecker (offen, geschlossen), Flachsteckhülse (offen, geschlossen) und
Stoßverbinder.

Die Symbole für Befestigungsmaterial werden auch als **Beschriftungssymbol** normaler Behälterbeschriftungen angeboten,
siehe [Beschriftungslasche und Beschriftungen](../bins/labels.md#icons).

## Eigene Symbole { #your-own-symbols }

Eine neue SVG-Datei in `cullenectIcons/hardware/` erscheint nach einem Neustart des Add-ins in der Liste
**Befestigungsmaterial**, benannt nach der Datei. `width` und `height` der SVG-Datei legen ihre Größe fest; eine Zahl
ohne Einheit zählt als CSS-Pixel, wie im SVG-Standard.
