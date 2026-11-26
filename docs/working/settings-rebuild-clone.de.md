# Einstellungen, Neuerstellung und Klonen { #settings-rebuild-and-clone }

Jede Grundplatte, jeder Behälter, Einleger, jede Box und jedes Box-Etikett merkt sich die Einstellungen, mit denen
sie gebaut wurden. Klicken Sie mit der rechten Maustaste darauf, in der Zeichenfläche oder im Browser, für drei
Befehle:

<picture><source media="(prefers-color-scheme: dark)" srcset="../../../assets/images/context-menu-dark.png"><img src="../../../assets/images/context-menu-light.png" alt="Das Kontextmenü von Fusion auf einer Fläche eines Behälters, mit Gridkeeper Einstellungen, Gridkeeper neu erstellen und Gridkeeper klonen an seinem Ende"></picture>

Ein Buchstabe einer Beschriftung oder eine Fläche des Modells funktioniert genauso wie der Körper: Gridkeeper findet
den Behälter oder Einleger, zu dem es gehört. Klicken Sie im Browser mit der rechten Maustaste auf den **Körper**,
nicht auf die Komponente.

## Gridkeeper Einstellungen { #gridkeeper-settings }

Öffnet ein Fenster mit der Version, die das Modell gebaut hat, und allem, womit es gebaut wurde, gruppiert wie sein
Dialog, sowie den Benutzerparametern, die es steuern, mit ihren aktuellen Werten. Bei einem Behälter mit
Cullenect-Aufnahmen listet es die gebaute Laschenbreite und jede Aufnahmegröße auf, mit der Anzahl der Aufnahmen
dieser Größe im Behälter.

![Das Fenster Gridkeeper Einstellungen eines Behälters: die Schaltflächen, die Version, mit der er gebaut wurde, seine Parameter und Einstellungen](../assets/images/settings-window.png)

Seine Schaltflächen:

| Schaltfläche | Was sie bewirkt |
|---|---|
| **In Datei speichern** | Speichert die Einstellungen in einer JSON-Datei, siehe [Einstellungen speichern und laden](save-load.md) |
| **Kopieren** | Kopiert sie als JSON in die Zwischenablage |
| **Klonen als Behälter** (bei Grundplatte und Einleger *Klonen als Grundplatte*, *Klonen als Einleger*) | Dasselbe wie **Gridkeeper klonen** |
| **Neu erstellen** | Dasselbe wie **Gridkeeper neu erstellen** |

Modelle, die von älteren Versionen ohne gespeicherte Einstellungen gebaut wurden, zeigen, was sie haben, ohne
Schaltflächen; sie lassen sich nicht neu erstellen oder klonen.

## Gridkeeper neu erstellen { #gridkeeper-rebuild }

Öffnet den Dialog des Modells mit seinen Einstellungen. Ändern Sie, was Sie möchten, und klicken Sie auf **OK**: Das
Modell wird **an seiner Stelle in der Zeitachse** erneut gebaut, und die nachfolgenden Features arbeiten weiter am
neuen Körper. Der Abschnitt Informationen des Dialogs nennt, welches Modell neu erstellt wird.

- Features, die eine Fläche oder eine Kante des alten Körpers verwendet haben, müssen möglicherweise neu ausgewählt
  werden; Gridkeeper listet sie nach der Neuerstellung in einer Meldung auf.
- Ein Behälter oder eine Grundplatte bleibt in der Komponente, in der er oder sie war.
- Einleger in den Aufnahmen eines neu erstellten Behälters werden wieder mit den gleichnamigen Aufnahmen per Gelenk
  verbunden. Ein Behälter, den der Behälter-Dialog in eine Zelle gesetzt hat, kommt wieder in diese Zelle.
- Eine neu erstellte Grundplatte überträgt Gelenke an ihren Steckplatz-Gelenkursprüngen auf die gleichnamigen; mit ihr
  verbundene Behälter bleiben drin.
- Eine neu erstellte Box ersetzt Box und Deckel gemeinsam, dort, wo der alte Satz stand; Ihre Gelenke an ihren
  Gelenkursprüngen wandern auf die gleichnamigen Gelenkursprünge, siehe [Aufbewahrungsboxen](../boxes.md).
- Ein neu erstellter Einleger wird von der unteren linken Ecke des alten aus gezeichnet; war er in einer Aufnahme,
  hat der Dialog diese Aufnahme schon gewählt, und der neue Einleger wird mit ihr verbunden.
- Ein neu erstelltes Box-Etikett kommt wieder in den Halter seiner Box, der Dialog hat die Box schon gewählt; ein
  Etikett ohne Box bleibt, wo es war, siehe [Aufbewahrungsboxen](../boxes.md#label).
- Ein Behälter wird immer neu gebaut, auch wenn Sie nur geändert haben, was seine [Parameter](parameters.md)
  enthalten, die Höhe und die Einheiten (seit 1.4.0); sein Beschriftungstext wird wieder an seine Beschriftung
  angepasst. Um diese Werte zu ändern, ohne den Behälter neu zu bauen, ändern Sie seine Parameter unter
  **Ändern › Parameter ändern**.
- Namen, die Sie der Komponente des Modells, seiner Zeitachsengruppe oder seinen Körpern gegeben haben, bleiben
  erhalten; ein von Gridkeeper vergebener Name folgt der neuen Größe. Ein Boxteil, das Sie umbenannt haben, sein
  Deckel oder ein Verschluss, behält seinen Namen ebenfalls.
- Die zuvor aktive Komponente ist danach wieder aktiv.

## Gridkeeper klonen { #gridkeeper-clone }

Öffnet den Dialog des Modells mit seinen Einstellungen für ein **neues** Modell, das Original bleibt unverändert.
Praktisch für einen zweiten Behälter wie den ersten, nur höher. Bei einem geklonten Einleger oder Box-Etikett ist
keine Aufnahme und keine Box gewählt; wählen Sie eine für das neue.
