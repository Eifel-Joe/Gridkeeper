# Runde 14: Beschriftung nach Textänderung

Stand 15.11.2026, mit Jörg in der Hauptsitzung abgestimmt. Teil des Sammelbetriebs R14–R18 (siehe CLAUDE.md im
Ordner `D:\Entwicklung\Gridfinity`, „Ergänzung Sammelbetrieb“): Branch von `runde-14-18`, Merge zurück nach
`runde-14-18`, kein Handtest durch Jörg vor dem Merge.

## Punkte

- p72 „Bin-Labels: Text mit mehr Buchstaben kann beim Ändern verrutschen“
- p120 „Eingefärbte Beschriftung: nach Textänderung sind neue Buchstaben nicht eingefärbt“
- p71 „Einleger: nach Textänderung neue Buchstaben ohne Namen und Kennung“
- p53 „Mehrfarbdruck: Text und Symbol sind mehrere Körper“

## Problem

Wird ein Beschriftungstext nachträglich über seinen Parameter länger, legt Fusion für die neuen Buchstaben neue
Körper an. Alles, was der Generator an einzelne Körper gehängt hat, erfasst diese neuen Körper nicht:

- Bin-Labels (`labelGenerator.py`): Text wird extrudiert, dann per Verschieben gekippt (`… tilt`) und platziert
  (`… placement`), dann mit der Bin vereint bzw. aus ihr geschnitten. Alle drei Schritte hängen an der Körperliste vom
  Bauzeitpunkt. Neue Buchstaben bleiben am Nullpunkt bzw. ungekippt und gehen bei graviert/erhaben nicht in die Bin.
- Farbe (`appearanceUtils.colorBodies`): Körper für Körper, neue Buchstaben bleiben in der Standarddarstellung.
- Name und Gridfinity-Kennung: Körper für Körper, neue Buchstaben heißen „Körper7“ und tragen keine Kennung.

Der Cullenect-Einleger ist seit Runde 9 schon so gebaut, dass neue Buchstaben richtig liegen (Skizze an der fertigen
Stelle, keine Verschiebung). Seit Runde 13 liegen eigenfarbige Körper in der Unterkomponente „Text“.

## Entscheidungen

1. **p72 – Bin-Labels ohne nachträgliches Verschieben.** Die Textskizze (und die Icon-Skizze) liegt gleich auf einer
   Konstruktionsebene an der fertigen, gekippten Stelle. Es gibt keine Verschieben-Schritte für Text und Icons mehr.
   Schneiden in die Bin (graviert) bzw. Vereinen (erhaben, einfarbig) geschieht in der Extrusion selbst
   (Operation Schnitt/Vereinen mit `participantBodies` = Bin-Körper als Proxy, wie in Runde 13 belegt), nicht in einem
   eigenen Kombinieren mit einer Körperliste. Eigenfarbige Beschriftung bleibt als eigene Körper in „Text“.
   Gilt für alle Label-Stile der Bin (Outline, Engraved, Embossed) und die Fach-Labels.
2. **p120 – Farbe an der Komponente „Text“.** Die gewählte Farbe kommt an die Text-Komponente bzw. ihre Occurrence,
   sodass neue Körper darin sie ebenfalls zeigen. Die Runde prüft, ob die Farbe im 3MF-Export ankommt. Kommt sie dort
   nicht an, bleibt die Farbe zusätzlich an den Körpern, und das Neubauen per Rechtsklick färbt neue Körper nach;
   das ist dann im Übergabeprotokoll zu nennen.
3. **p71 – Erkennung über die Komponente.** „Gridfinity settings“ und „Gridfinity rebuild“ per Rechtsklick finden das
   Teil auch von einem Körper in „Text“ aus, der keine eigene Kennung trägt (über die Text-Komponente bzw. deren
   Eltern-Teil). Neue Buchstaben behalten Fusions Namen („Körper7“) – Jörg 15.11.2026: „Körper7 ist in Ordnung“.
4. **p53 – durch Runde 13 erledigt**, sofern der Export „Text“ als ein Teil zeigt. Die Runde prüft das im 3MF-Export
   (Teil „Text“ je Bin/Einleger mit allen Buchstaben und Symbolen). Ob es im Slicer reicht, zeigt Jörgs Probedruck.
5. **Bestand:** Bins und Einleger, die vor dieser Runde gebaut wurden, werden nicht umgebaut. Erst ein Neubau per
   Rechtsklick baut sie nach dem neuen Weg.

## Nicht dabei

- Text kürzer machen bzw. schmalere Einleger (p52, Runde 17).
- Schriftart- oder Größenwechsel per Parameter.
- Umbenennen neuer Buchstaben-Körper.

## Erster Schritt: Hinweisfenster-Skript prüfen

Vor der Umsetzung, in einem neuen Fusion-Dokument: Ein Testskript öffnet per `ui.messageBox` einen reinen Hinweis
(nur „OK“). Parallel läuft `bash D:/Entwicklung/Gridfinity/fusion-hinweis-schliessen.sh` (im Hintergrund, mit
Wartezeit). Erwartet: Fenster geschlossen, Skriptaufruf kehrt zurück, Zeile „GESCHLOSSEN …“ in
`D:\Entwicklung\Gridfinity\fusion-hinweise.log`. Ergebnis ins Übergabeprotokoll. Schlägt es fehl: Skript nicht
umbauen ohne Rücksprache mit der Hauptsitzung.

## Ende-zu-Ende-Kriterium

Ein Skript (wie `tests/e2e/runde13_assembly.py`) baut in einem neuen Dokument je Fall, verlängert danach den
Text-Parameter um drei Buchstaben und prüft:

| Fall | Erwartung nach Verlängern |
|---|---|
| Bin, Label Outline | alle Buchstaben an der Label-Stelle, keiner am Nullpunkt |
| Bin, Engraved | Bin-Volumen kleiner als vorher um die neuen Buchstaben, kein Buchstabenkörper außerhalb der Bin |
| Bin, Embossed einfarbig | Buchstaben mit der Bin vereint (keine losen Körper) |
| Bin, Embossed farbig | neue Körper in „Text“, zeigen die gewählte Farbe |
| Fach-Labels (2 Fächer) | wie Outline |
| Einleger farbig | neue Körper in „Text“, gewählte Farbe; Rechtsklick „Gridfinity settings“ auf einem neuen Körper öffnet die Einstellungen des Einlegers |

Dazu: alle Skizzen vollständig bestimmt, Timeline ohne Fehler, pytest grün, Snapshot-Tests grün (bekannte p30-Fälle
ausgenommen; geänderte Snapshots der Bin-Labels sind zu erwarten und werden mit Begründung neu abgelegt, wenn Form und
Volumen gleich bleiben).
