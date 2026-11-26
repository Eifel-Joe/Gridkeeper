# Parameter ändern { #changing-parameters }

Jedes Modell erhält eigene Benutzerparameter, pro Modell nummeriert: Der erste Behälter hat `gfBin1_…`, der nächste
`gfBin2_…`, ebenso `gfPlate1_…`, `gfLabel1_…` und `gfBox1_…`. Ändern Sie sie unter **Ändern › Parameter ändern**, und das
Modell folgt, ohne neu erstellt zu werden; die Parameter eines Modells zu ändern, ändert kein anderes Modell.

![Fusions Fenster Parameter mit den Benutzerparametern gfBin1_baseWidth, gfBin1_baseLength, gfBin1_heightU und gfBin1_heightUnit eines Behälters](../assets/images/change-parameters.png)

## Behälter { #bins }

| Parameter | Was er enthält |
|---|---|
| `gfBin1_baseWidth` | Rastereinheit Breite |
| `gfBin1_baseLength` | Rastereinheit Länge |
| `gfBin1_heightUnit` | Höheneinheit |
| `gfBin1_heightU` | Höhe des Behälters in Höheneinheiten |
| `gfBin1_label` | Beschriftungstext, bei mehreren Fächern `gfBin1_label1`, `gfBin1_label2` … für die mit Text |

Die Wände, Fächer, Beschriftungslasche, Cullenect-Aufnahmen, Gelenkursprünge und erhöhten Trennwände folgen den
Einheiten. Ein länger gemachter Beschriftungstext behält die Höhe seiner Buchstaben und kann über die Lasche
hinauslaufen: **Gridkeeper neu erstellen** passt ihn erneut an. Die Größe einer Cullenect-Aufnahme (1U, 2U …) wird beim
Erstellen des Behälters festgelegt; würde eine Änderung eine andere Größe erfordern, erstellen Sie den Behälter neu.

## Grundplatten { #baseplates }

| Parameter | Was er enthält |
|---|---|
| `gfPlate1_baseWidth` | Rastereinheit Breite |
| `gfPlate1_baseLength` | Rastereinheit Länge |
| `gfPlate1_paddingLeft`, `…Top`, `…Right`, `…Bottom` | Rand an den Seiten |

Die Gelenkursprünge der Steckplätze folgen den Rastereinheiten.

## Einleger { #inserts }

| Parameter | Was er enthält |
|---|---|
| `gfLabel1_baseWidth` | Rastereinheit Breite, nur bei einer Breite in Rastereinheiten |
| `gfLabel1_width` | Breite des Einlegers, ein Ausdruck aus Rastereinheit Breite, den Einheiten und der Korrektur |
| `gfLabel1_text1`, `gfLabel1_text2` | Die Textzeilen |

Das Symbol bleibt am rechten Rand, wenn sich die Breite ändert. Ein länger gemachter Text wird nicht erneut angepasst,
er läuft nach rechts weiter; kürzen Sie ihn oder erstellen Sie den Einleger neu.

!!! tip "Stattdessen neu erstellen"
    Alles, was kein Parameter ist, etwa die Größe des Behälters in Einheiten oder die Fächer, ändern Sie mit
    [Gridkeeper neu erstellen](settings-rebuild-clone.md#gridkeeper-rebuild).

## Boxen { #boxes }

| Parameter | Was er ist |
|---|---|
| `gfBox1_baseWidth` | Breite in Rasterzellen zu 42 mm, mindestens 4 |
| `gfBox1_baseLength` | Länge in Rasterzellen, mindestens 3 |
| `gfBox1_heightU` | Höhe in Einheiten zu 7 mm, mindestens 6 |

Die Zellen-Gelenkursprünge einer Box behalten die Zellen, mit denen sie erstellt wurde, siehe
[Aufbewahrungsboxen](../boxes.md).
