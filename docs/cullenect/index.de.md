# Cullenect-Beschriftungen { #cullenect-labels }

[Cullenect](https://github.com/CullenJWebb/Cullenect-Labels) von CullenJWebb ist ein System austauschbarer
Beschriftungen: Ein dünner Einleger mit Text und Symbol rastet in eine Aufnahme in der Beschriftungslasche des Behälters
ein und wird getauscht, wenn sich der Inhalt ändert. Gridkeeper baut beide Hälften:

- **die Aufnahmen**, als Beschriftungsstil *Cullenect* der Beschriftungslasche eines Behälters, siehe
  [Aufnahmen in Behältern](pockets.md);
- **die Einleger**, mit dem Befehl **Gridkeeper Einleger**, siehe [Einleger](inserts.md), mit Schrauben- und
  Befestigungsmaterial-[Symbolen](symbols.md).

Die Maße folgen Cullenects eigenem OpenSCAD-Code, sodass Gridkeeper-Einleger in Cullenect-Aufnahmen passen und
umgekehrt:

| | Maß |
|---|---|
| Breite des Einlegers | Rastereinheit × Einheiten − 6 mm, z. B. 36 mm für 1U, 78 mm für 2U bei 42-mm-Einheiten |
| Höhe des Einlegers | 11 mm |
| Dicke des Einlegers | 1,2 mm |
| Aufnahme | 1,2 mm tief, in Breite und Höhe um das Spiel des Steckplatzes (0,3 mm) größer als der Einleger, mit Rastrippen entlang beider Längsseiten |

![Ein Behälter mit drei Fächern, jedes mit einer Cullenect-Aufnahme und einem Einleger in Rot, Blau und Schwarz, der schwarze aus seiner Aufnahme herausgehoben](../assets/images/cullenect-overview.png)

Um einen Behälter neu zu beschriften, drucken Sie einen neuen Einleger und drücken ihn in die Aufnahme, die Rastung hält
ihn. Text und Symbol sind eigene Körper, bereit für ein zweites Filament, siehe
[Farben und Mehrfarbdruck](../working/colors.md).
