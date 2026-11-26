# Größe und Form { #size-and-shape }

## Informationen { #info }

**Informationen** enthält einen Link zu diesem Teil der Dokumentation und die Version des Zusatzmoduls; wurde der
Dialog über **Gridkeeper neu erstellen** geöffnet, steht dort, welcher Behälter an Ort und Stelle neu erstellt wird.

## Grundmaße { #basic-sizes }

| Eingabe | Vorgabe | Wirkung |
|---|---|---|
| **Rastereinheit X (mm)** | 42 mm | Größe einer Rasterzelle entlang X, mindestens 10 mm |
| **Rastereinheit Y (mm)** | 42 mm | Größe einer Rasterzelle entlang Y, mindestens 10 mm |
| **Höheneinheit (mm)** | 7 mm | Eine Höheneinheit, mindestens 5 mm |
| **Spiel XY (mm)** | 0,25 mm | Spalt auf jeder Seite zwischen dem Behälter und seiner Zelle, 0,1 bis 0,5 mm. Wählen Sie denselben Wert wie bei der Grundplatte |

Jeder Behälter hat seine Einheiten als eigene [Benutzerparameter](../working/parameters.md), eine Änderung an einem
Behälter ändert also keinen anderen.

## Hauptmaße { #main-dimensions }

| Eingabe | Vorgabe | Wirkung |
|---|---|---|
| **Breite, X (u)** | 2 | In ganzen oder halben Rastereinheiten, 0,5 bis 100 |
| **Länge, Y (u)** | 3 | In ganzen oder halben Rastereinheiten, 0,5 bis 100 |
| **Halbraster** | aus | Setzt den Behälter auf Füße in halber Größe, für eine Grundplatte im Halbraster; der Behälter behält seine Größe in Rastereinheiten |
| **Höhe, Z (u)** | 5 | Gesamthöhe in Höheneinheiten, Füße eingerechnet, mindestens 1; der Stapelrand addiert oben 3,8 mm, bei ausgeschaltetem **Stapelrand oben kürzen** 4,4 mm |
| **Eigene Form** | aus | Zeigt eine Zeichnung der Behälterzellen, in der Sie Zellen weglassen können |

### Tatsächliche Maße { #actual-dimensions }

Am Ende des Abschnitts zeigt die Tabelle **Tatsächliche Maße** die äußere Breite, Länge und Höhe, die der Behälter
haben wird, auf den Mikrometer genau: Breite und Länge folgen dem **Spiel XY des Behälters**, die Höhe dem Stapelrand
mit ein- oder ausgeschaltetem **Stapelrand oben kürzen**, wobei seine scharfe Oberkante um das Spiel
abgesenkt ist. Beim Beschriftungsstil Cullenect nennt eine zweite Zeile die Größen der Aufnahmen und die Breite des
jeweils passenden Einlegers, z. B. `Cullenect: 2U: Aufnahme 78,3 mm, Einleger 78 mm`, siehe
[Aufnahmen in Behältern](../cullenect/pockets.md).

### Halbe Größen und Halbraster { #half-sizes-and-half-grid }

Eine Größe, die auf eine Hälfte endet, bekommt ohne **Halbraster** ganze Füße und eine Reihe halber Füße an der
Rückseite oder rechten Seite, nur quer zur Reihe halbiert. Mit **Halbraster** ist jeder Fuß ein halber, sodass der
Behälter auf einer Grundplatte im Halbraster um eine halbe Zelle versetzt stehen kann. Halbe Füße haben keine Magnet-
oder Schraubenbohrungen, dafür ist kein Platz.

<picture><source media="(prefers-color-scheme: dark)" srcset="../../../assets/gif/bin-half-grid-dark.gif"><img src="../../../assets/gif/bin-half-grid-light.gif" alt="Halbraster einschalten, dann eine Größe, die auf eine Hälfte endet, mit Behältern auf ganzen, halben und einer Reihe halber Füße"></picture>

### Eigene Form { #custom-shape }

Schalten Sie **Eigene Form** ein und klicken Sie in der Zeichnung auf Zellen, um sie wegzulassen, für einen Behälter in
Form eines L, eines T oder eines anderen Tetris-Steins. **Alle füllen** setzt jede Zelle wieder ein; schalten Sie
**Eigene Form** aus, werden ebenfalls alle Zellen wieder gefüllt.

<picture><source media="(prefers-color-scheme: dark)" srcset="../../../assets/gif/bin-custom-shape-dark.gif"><img src="../../../assets/gif/bin-custom-shape-light.gif" alt="Eine Behälterform zeichnen, mit dem Behälter auf allen Zellen, dann mit weggelassenen Zellen"></picture>

Fächer, Griffmulde und Beschriftungslasche werden für eigene Formen noch nicht erzeugt, ein Behälter mit eigener Form
hat daher ein einziges Fach und keine Beschriftungslasche und keine Cullenect-Aufnahme.
