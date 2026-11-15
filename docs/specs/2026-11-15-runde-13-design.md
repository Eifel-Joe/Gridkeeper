# Runde 13 – Baugruppe aus Komponenten, Einleger per Joint in die Tasche

Stand 2026-11-15, von Jörg freigegeben am 15.11. Ergänzt `2026-11-14-cullenect-labels-design.md` und `2026-11-15-upstream-2-4-merge.md`.
Punkte: p90 „Bin und Baseplate in einer Baugruppe als Komponente anlegen“, p160 „Einleger per Joint in seine
Cullenect-Tasche setzen“, p100 „Label-Befehl legt den Einleger am Nullpunkt mitten in die Bin“.
Jörgs Entscheidungen in der Sitzung (15.11.): siehe „Entscheidungen“.

## Warum

Jörg baut mehrteilige Grids mit vielen Bins und Einlegern in einem Dokument. Heute liegen Bins und Baseplates in einem
Bauteil-Dokument als Körper in der Wurzel. Will er ein Teil neu bauen oder zum Drucken exportieren, sucht er es
in einem Haufen Körper. Seine Notiz zu p90, wörtlich: „Eine Oberkomponente Grid für die Grid-Teile, eine Bins für die
Bins und eine Label für die Labels. Und Beschriftungen, egal ob im Bin oder im Label bekommen auch eine eigene
Bauteilkomonente Text innerhalb der Komponente. So lässt es sich am einfachsten exportieren um es zu drucken.“

Einleger legt der Label-Befehl heute in den Nullpunkt. Die Platzsuche (`placementUtils.findPlacement`) umgeht nur andere
Einleger. So steckt der neue Einleger in der ersten Bin. Ob ein Einleger in seine Tasche passt, prüft Jörg von Hand.

## Ziel

```
Wurzel
├─ Grid                         Sammelkomponente der Baseplates
│   └─ Gridfinity baseplate 4x3      eine Komponente je Baseplate (Fill: eine Komponente mit allen Stücken)
├─ Bins                         Sammelkomponente der Bins
│   └─ Gridfinity bin 2x1x6          eine Komponente je Bin: Bin-Körper, Joint Origins der Füße und Taschen
│       └─ Text                      nur wenn es eigenfarbige Körper gibt: Buchstaben und Symbole
└─ Label                        Sammelkomponente der Einleger
    └─ Gridfinity label 1U M4x5      eine Komponente je Einleger: Einleger-Körper, Joint Origin unten mittig
        └─ Text                      Buchstaben und Symbole des Einlegers
```

1. **p90:** Bin, Baseplate und Einleger sind immer eine eigene Komponente in ihrer Sammelkomponente. Ein Bauteil-Dokument
   wird dafür auf hybrid umgestellt, so wie heute beim Einleger (`designIntent.componentPlan`). Eigenfarbige
   Beschriftungskörper liegen in der Unterkomponente „Text“ ihrer Bin oder ihres Einlegers.
2. **p160:** Jede Cullenect-Tasche einer Bin hat einen Joint Origin mittig auf dem Taschenboden. Jeder Einleger hat einen
   Joint Origin unten mittig. Ein Joint zwischen beiden setzt den Einleger bündig und mittig in die Tasche.
3. **p100:** Im Label-Dialog lässt sich optional eine Tasche wählen. Der Einleger wird dann per Joint hineingesetzt.
   Ohne Wahl liegt er neben allen vorhandenen Bins, Baseplates und Einlegern, nie im Nullpunkt.

Der Druck ändert sich nicht: Geometrie und Maße aller Körper bleiben gleich.

## Entscheidungen (Jörg, 15.11.)

| Frage | Antwort |
|---|---|
| Was kommt in „Text“? | Alle eigenfarbigen Körper: Buchstaben **und** Cullenect-Symbole bzw. Bin-Icons. Ohne eigenfarbigen Körper gibt es keine Text-Komponente, z. B. bei gravierter Beschriftung, die nur in die Bin geschnitten ist, oder bei einfarbiger, die mit der Bin vereint ist. |
| Bestehende Dokumente | Bleiben, wo sie sind. Der Rebuild ersetzt ein altes Teil an seinem bisherigen Ort: Körper in der Wurzel bleiben Körper in der Wurzel, eine Komponente direkt in der Wurzel bleibt dort. Nur neu erzeugte Teile kommen in die neue Struktur. |
| Einleger einsetzen | Optionales Auswahlfeld „Pocket“ im Label-Dialog. Mit Auswahl setzt der Befehl den Einleger per Joint in die Tasche. Ohne Auswahl landet er neben den vorhandenen Teilen. |
| Einleger passt nicht in die gewählte Tasche | Nichts bauen, Hinweis „Tasche passt nicht, passende wählen“. |
| Joint Origins der Taschen | Immer, unabhängig von der Option „Add joint origins“, die weiter nur die Füße bzw. Aufnahmen steuert. |

## Bestand (gelesen 15.11.)

- `binBuilder._buildBin` und `baseplateBuilder._buildBaseplate` legen nur in einem Hybrid-Dokument eine Komponente in der
  Wurzel an, sonst bauen sie in die Wurzel. `labelBuilder.buildLabel` stellt ein Bauteil per
  `designIntent.componentPlan` auf hybrid um und nimmt das bei einem Fehler zurück (`_undoHybridSwitch`).
- Alle drei aktivieren nach dem Bau die Wurzel (`des.activateRootComponent()` im `finally`, Commit 6c2743c).
- Der Rebuild (`rebuildUtils.findTarget`/`rebuild`) findet die Bin über die Timeline-Gruppe, aus der der Körper stammt.
  Die erste Occurrence in der Gruppe ist die Komponente der Bin, `transform2` davon geht an den Neubau. Der Neubau
  entsteht direkt nach der alten Gruppe, spätere Features bekommen die neuen Körper (`replaceBodies`), die alte Gruppe
  wird gelöscht (`removeOldGroup`). Die Position steckt in der Verschiebung „Bin placement“ bzw. „Baseplate placement“.
- Farbige Bin-Beschriftung (`labelGenerator.createLabel`) entsteht in der Bin-Komponente, wird gekippt und verschoben
  und mit „keep tools“ aus der Bin geschnitten. Ohne Farbe wird sie mit der Bin vereint oder hineingeschnitten, dann
  gibt es keinen eigenen Körper. `binBuilder` verschiebt Bin und Beschriftung gemeinsam mit „Bin placement“.
- Einleger (`cullenectLabelGenerator.createCullenectLabel`) entstehen gleich an ihrem Platz (`origin`), nicht verschoben:
  Eine Verschiebung würde Buchstaben, die ein späterer Live-Text hinzufügt, im Nullpunkt zurücklassen.
- Taschen (`cullenectSocketGenerator.createCullenectSocket`): Mitte `(centerX, centerY)` als Dim, Oberkante
  `tabTopZ`, Tiefe `CULLENECT_LABEL_THICKNESS`. Bei Cullenect setzt `binBuilder` den Laschenwinkel oben auf 0, die Tasche
  liegt also immer waagerecht, ihre lange Seite entlang X. Das gilt für hohle Bins (eine Tasche je Fach,
  `binBodyGenerator`) und für geschalte Bins (eine Tasche, `binBuilder`).
- Joint Origins der Füße: `baseGenerator.createCellJointOrigins`, auf Skizzenpunkten, die vom Ursprung aus bemaßt sind,
  angelegt nach der Platzierung, weil Skizzen den Körper-Verschiebungen nicht folgen (Le0Michine, Upstream v2.4).

## In Fusion geprüft (15.11., eigenes Testdokument)

- Verschachtelte Komponenten Wurzel › Bins › Bin › Text lassen sich per API anlegen (`occurrences.addNewComponent` auf
  der Komponente der Bin). Die zurückgegebene Occurrence ist nativ, also ohne Pfad von der Wurzel aus. Erst
  `createForAssemblyContext` mit der Eltern-Occurrence ergibt den Pfad `Bins:1+Bin A:1+Text:1`.
- Eine Extrusion in „Text“ mit einer Skizze in „Text“ erzeugt Körper in „Text“.
- Ein „Kombinieren/Ausschneiden“ in der Bin mit einem Werkzeugkörper aus „Text“ ist gesund, **wenn Ziel- und
  Werkzeugkörper als Proxys mit vollem Pfad von der Wurzel übergeben werden**. Mit nativem Ziel meldet Fusion einen
  Referenzfehler („Fehler beim Abrufen der Zielexemplartransformation“).
- Ein Extrusions-Schnitt aus einer Skizze in „Text“ mit `participantBodies` = Bin-Körper (Proxy) ist gesund.
- `BRepBody.moveToComponent` geht auch, legt aber einen Timeline-Eintrag „Körper ausschneiden/einfügen“ an, der genau
  die vorhandenen Körper nimmt.
- unbestätigt: Ein per API neu angelegtes Dokument war bereits hybrid (`designIntent` 2).
- **Joint bei Rebuild der Bin:** Ein starrer Joint Einleger → Taschen-Origin. Löscht man die Timeline-Gruppe der Bin
  mit `deleteMe(True)`, wie `removeOldGroup` es tut, ist der Joint ebenfalls weg und der Einleger springt still in den
  Nullpunkt zurück. Das passiert auch dann, wenn der Joint vorher umgehängt wurde.
  Was funktioniert:
  1. Neue Bin direkt nach der alten Gruppe bauen.
  2. Marker vor den Joint setzen (`rollTo(True)`).
  3. `joint.geometryOrOriginTwo` auf den neuen Taschen-Origin (Proxy) setzen. Der Einleger wandert mit.
  4. Die alten Gruppeneinträge **einzeln** löschen (`deleteMe(False)`, dann `deleteObject` vom letzten zum ersten).

  Danach ist der Joint gesund und der Einleger sitzt in der neuen Tasche. Umhängen bei Marker am Ende, also mit der neuen
  Bin hinter dem Joint, scheitert (`InternalValidationError`).

## Wege für „Text“

| Weg | Wie | Für | Gegen |
|---|---|---|---|
| **A: gleich in „Text“ bauen** (gewählt) | Skizzen und Extrusionen der Beschriftung entstehen in der Text-Komponente. Schnitte in Bin bzw. Einleger mit vollen Proxys. | Live-Text bleibt richtig: Buchstaben, die ein geänderter Text-Parameter hinzufügt, entstehen ebenfalls in „Text“. Kein Zusatzeintrag in der Timeline. | Generatoren bekommen eine zweite Zielkomponente und die Occurrence-Pfade mitgegeben. |
| B: am Ende verschieben | Wie heute bauen, dann `moveToComponent` in „Text“. | Kaum Änderungen an den Generatoren. | Buchstaben, die ein späterer Live-Text hinzufügt, bleiben in der falschen Komponente. Das widerspricht dem Live-Text des Einlegers (Runde 9). |
| C: nur Sammelkomponenten, kein „Text“ | | Am einfachsten. | Erfüllt Jörgs Notiz nicht. |

## Anforderungen

### Struktur (p90)

1. **Sammelkomponenten** „Grid“, „Bins“, „Label“ direkt in der Wurzel. Sie werden beim ersten Teil ihrer Art angelegt und
   danach wiederverwendet. Erkannt werden sie an einem Attribut (`tagUtils.TAG_GROUP`, eigener Tag-Name je Art) an der
   Komponente, nicht am Namen, damit Jörg sie umbenennen kann. Die Occurrence der Sammelkomponente liegt in der
   Timeline **vor** der Gruppe des Teils, nie darin, sonst würde ein Rebuild sie mit der alten Gruppe löschen.
2. **Teil-Komponente:** Jede neue Bin, Baseplate und jeder neue Einleger bekommt eine eigene Komponente in seiner
   Sammelkomponente, benannt wie heute (`binDisplayName`, `baseplateName`, `labelName`). Eine Fill-Baseplate bleibt
   eine Komponente mit allen Stücken als Körpern. Die Stücke gehören zusammen und werden gemeinsam neu gebaut.
3. **Bauteil → hybrid:** Ein Bauteil-Dokument wird für Bin und Baseplate auf hybrid umgestellt, wie heute beim Einleger.
   Schlägt der Bau fehl, wird das zurückgenommen (`_undoHybridSwitch` wird allgemein, für alle drei Befehle). Eine
   Vorschau ändert die Art des Dokuments nicht: In einem Bauteil baut sie wie heute in die Wurzel (`mayChangeDocument`).
4. **Text-Komponente:** Hat eine Bin oder ein Einleger eigenfarbige Körper, liegen sie in der Unterkomponente „Text“ der
   Teil-Komponente (Weg A). Für den Einleger heißt das: Buchstaben, Symbol-Körper und, bei vertiefter oder bündiger
   Schrift, ihre Füllung. Für die Bin: die farbigen Beschriftungskörper je Fach samt Icon. Die Schnitte in Bin bzw.
   Einleger bleiben in deren Komponente. Gibt es keinen eigenfarbigen Körper, wird „Text“ nicht angelegt.
5. **Platzierung bleibt eine Verschiebung:** Bin und Baseplate werden weiter mit „Bin placement“ bzw.
   „Baseplate placement“ verschoben, nicht über die Lage der Occurrence. Davon hängt der Rebuild ab. Die Körper in
   „Text“ verschiebt eine eigene Verschiebung „Text placement“ in der Text-Komponente um denselben Weg.
   `groupPlacement` liest weiter nur die Verschiebung mit dem Platzierungsnamen.
6. **Hauptkomponente aktiv:** Nach jedem Bau, auch nach einem Fehler, ist die Wurzel aktiv (wie heute).
7. **Rebuild** (Rechtsklick „Gridfinity rebuild“, Parameter je Bin, Configs) funktioniert weiter:
   - Er findet das Teil in seiner Komponente in der Sammelkomponente und baut das neue Teil **in dieselbe Eltern-Komponente**
     wie das alte, mit derselben Lage (`transform2` der nativen Occurrence relativ zu ihrer Eltern-Komponente).
   - Teile alter Dokumente bleiben, wo sie sind (Entscheidung): Körper in der Wurzel werden als Körper in der Wurzel neu
     gebaut, ohne Umstellung auf hybrid. Eine Komponente direkt in der Wurzel bleibt dort. Altes Verhalten also für
     alles, was vor dieser Runde gebaut wurde.
   - Die Text-Occurrence in der Gruppe stört `findTarget` nicht: Die Teil-Occurrence ist die erste in der Gruppe.
   - Parameter-Änderung ohne Neubau (`parameterEdits`) bleibt, wie sie ist.
   - **Joints auf Taschen bleiben erhalten:** Joints, die einen Taschen-Origin der alten Bin nutzen, bekommen den
     Taschen-Origin gleichen Namens der neuen Bin, wie oben in Fusion geprüft. Sobald ein Joint umgehängt wurde, löscht der
     Rebuild die alte Gruppe Eintrag für Eintrag statt als Ganzes. Hat die neue Bin diese Tasche nicht mehr, etwa weil
     es weniger Fächer gibt oder kein Cullenect mehr, meldet der Rebuild den Joint als „needs a look“. Er geht dann mit
     der alten Gruppe verloren, und der Einleger bleibt frei liegen.

### Joint Origins (p160)

8. **Taschen:** Jede Cullenect-Tasche einer Bin, ob in hohlen Bins je Fach oder in geschalten Bins, bekommt einen Joint
   Origin in der Mitte des Taschenbodens, Z nach oben, X entlang der langen Seite der Tasche. Er liegt auf einem
   Skizzenpunkt, der vom Ursprung aus bemaßt ist, und folgt damit den Parametern der Bin (Höhe, Einheiten), so wie
   `createCellJointOrigins`. Angelegt wird er nach der Platzierung, mit der Platzierung in den Koordinaten. Immer, also
   unabhängig von „Add joint origins“. Name: „Pocket joint origin“ bei einem Fach, sonst
   „Compartment N pocket joint origin“. Die Joint Origins tragen ein Attribut, an dem der Label-Befehl eine Tasche
   erkennt, mit ihrer Breite und Höhe in mm. Verglichen wird in mm, weil Einleger und Bin eigene Basisbreiten haben und
   der Einleger auch eine freie Breite haben kann.
9. **Einleger:** Jeder Einleger bekommt einen Joint Origin unten mittig (Mitte seiner Grundfläche, Z = 0 seiner
   Unterseite), Z nach oben, X entlang seiner Breite. Er folgt dem Breiten-Parameter des Einlegers.
10. **Passung:** Ein starrer Joint zwischen Einleger und Tasche setzt den Einleger mittig auf den Taschenboden, seine
    Oberseite bündig mit der Laschenoberseite, wie in Cullenect.scad. Die Interferenzprüfung zeigt keine Überschneidung
    außer, falls vorhanden, der gewollten Rastnase an den Rippen (unbestätigt, wird im Live-Test gemessen und hier
    nachgetragen).

### Einsetzen beim Label-Befehl (p100)

11. **Auswahlfeld „Pocket“** im Label-Dialog, optional, höchstens eine Auswahl, nimmt nur Joint Origins mit dem
    Taschen-Attribut aus Anforderung 8. Mit Auswahl legt der Befehl nach dem Bau einen starren Joint an: Einleger-Origin
    auf Taschen-Origin. Der Einleger bewegt sich, die Bin nicht. Der Joint gehört zur Timeline-Gruppe des Einlegers.
12. Passt der Einleger nicht in die Tasche (breiter oder höher als die Tasche, in mm), baut der Befehl nichts. Der
    Dialog zeigt den Hinweis, dass diese Tasche nicht passt und eine passende gewählt werden soll, so wie andere
    Eingabeprobleme heute (`labelProblem`). Entscheidung Jörg, 15.11.: „Gar nichts. Hinweis, dass diese Tasche nicht
    passt und eine passende gewählt werden soll.“
13. **Ohne Auswahl** sucht die Platzsuche einen freien Platz neben allen getaggten Bins, Baseplates und Einlegern, auch
    denen in Komponenten, nicht nur neben anderen Einlegern. Bisherige Einleger-Raster (`PLACEMENT_CELL_LENGTH`)
    bleiben.

## Nicht dabei

- Umzug alter Teile in die neue Struktur (Entscheidung „bleiben, wo sie sind“).
- Ein Rebuild-Befehl für Einleger (gibt es heute nicht).
- Joints für Bins auf Baseplates (die Joint Origins dafür gibt es seit Upstream v2.4, setzen tut Jörg sie selbst).
- Änderungen an Geometrie, Maßen oder Druckbild.

## Ende-zu-Ende-Kriterium

In einem neuen Bauteil-Dokument in Fusion: eine Baseplate 3x2, eine hohle Bin 2x1x6 mit Cullenect und zwei Fächern,
eine Bin 1x1 mit farbiger Bin-Beschriftung, dann ein Einleger mit Auswahl einer Tasche der ersten Bin und einer ohne
Auswahl.

1. Browser: Wurzel › Grid › Baseplate, Bins › zwei Bins, Label › zwei Einleger; die farbige Bin und beide Einleger mit
   Unterkomponente „Text“, in der alle Buchstaben und Symbole liegen und sonst nichts.
2. Der erste Einleger sitzt per Joint in der gewählten Tasche, die Interferenzprüfung zeigt nur die Rastnase.
   Der zweite liegt frei neben allem, ohne Überschneidung.
3. Rechtsklick „Gridfinity rebuild“ auf die farbige Bin mit anderer Höhe: Die neue Bin steht in „Bins“ an derselben
   Stelle, mit „Text“. Danach ist die Wurzel aktiv.
4. Einen Text-Parameter des Einlegers um Buchstaben verlängern: Die neuen Buchstaben liegen in „Text“.
5. Alle Skizzen des Generators sind vollständig bestimmt, pytest grün, Snapshot-Tests grün bis auf die bekannten
   p30-Fälle. Die Dialoge Bin, Baseplate und Label öffnen sich wirklich.
6. Ein altes Dokument mit Bins als Körpern in der Wurzel: Rebuild baut sie an derselben Stelle als Körper in der Wurzel
   neu.
7. Rebuild der ersten Bin (andere Höhe): Der eingesetzte Einleger sitzt danach in der neuen Tasche, sein Joint ist gesund.

## Tests

- pytest für alles ohne Fusion: welche Sammelkomponente, wohin ein Rebuild baut (alt/neu), Namen und Zuordnung der
  Taschen-Origins, Passt-Prüfung in mm, Platzsuche über alle Tags.
- Snapshot-Fälle in Fusion: Die Geometrie bleibt gleich, die abgelegten Snapshots gelten weiter. Die vier Fälle mit
  `designIntent: part` bekommen `designIntentAfter: hybrid`, weil Bin und Baseplate ein Bauteil jetzt auch umstellen.
  Der Test-Ablauf sucht die Beschriftungskörper (`labelPartBodies`) auch in der Text-Komponente. Neue Fälle: Struktur
  (Sammel-, Teil- und Text-Komponente), Taschen-Origins einer zweifächrigen Cullenect-Bin, Einleger in Tasche per Joint,
  Rebuild mit eingesetztem Einleger.

## Dem Umsetzer überlassen

- Name und Form der neuen Hilfsfunktionen (z. B. `assembly.py` für Sammelkomponenten, Text-Komponente, Proxys).
- Ob die Vorschau des Label-Befehls den Joint schon zeigt oder erst der Bau.
- Wie die Taschen-Mitten aus `createCullenectSocket` bzw. `binBodyGenerator` an `binBuilder` zurückgegeben werden.

## Credits

Komponenten, Rebuild, Configs und `createCellJointOrigins` von Le0Michine (FusionGridfinityGenerator, Upstream v2.4,
CC BY-NC-SA 4.0). Cullenect-Labels von CullenJWebb (MIT). Referenz gridfinity_extended_openscad von ostat /
Chris Heazlewood. Gridfinity von Zack Freedman.
