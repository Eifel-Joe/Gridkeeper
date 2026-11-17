# Runde 28 – Kleinteile der Pred-Box (p261)

Branch `runde-28` (Worktree `wt-r28`), Ziel `master` des Forks. Plan: `dev-notes/plans/2026-11-17-runde-28.md`.
Spec mit den Nachträgen dieser Runde: `dev-notes/specs/2026-11-16-pred-box-design.md`.

## Stand (belegt)

- **Kleinteile im Satz:** 4 Riegel (Preds Latch_Experimental), Griff, 2 Haltestifte, 2 Scharniere (Hinge_M3x30).
  - Riegel, Griff und Stifte sind starr an Joint origins der Box gejointet. Die Gelenke heißen „<Satz> <Sitz>“.
  - Die Scharniere liegen in Druckposition neben der Box: das erste an Preds Stelle, das zweite 5 mm daneben in y
    (Jörg: „Das passt so für das Scharnier“).
  - Die Teile sind `.f3d` in `resources/predBox`, aus Preds Datei übernommen. Herkunft und Änderungen stehen in der
    README dort.
  - Die Griffbreite folgt der Schildbreite: Schildbreite + 28,5 mm, höchstens 113,5 mm (Jörg).
- **Fusion-Prüfung** `r28_insert_check` l5 und l6 (17.11.), beide OK:
  - 5×4×6 → 7×5×10 und 5×4×6 → 4×3×6.
  - Alle Teile da, 8 Gelenke gesund.
  - Lagen gleich Preds Datei auf 0,01 mm, Griff bei 4×3×6 57 mm breit.
  - Teile eingebettet (nicht verknüpft), kein `_XRef_`.
  - Der Bau dauert rund 90 s, der Parameterwechsel 37 s.
- **Griff** `handle.f3d` neu gebaut (`r28_handle_build` l5). Volumen gleich Preds bei beiden Halbbreiten.
- **Klicktest-Funde:**
  - F1: Rechtsklick auf den Satz zeigt Einstellungen, Rebuild und Clone.
  - F3: Export-Dateinamen tragen den Satznamen.
  - Bilder aus dem Klicktest sind in der Doku.
  - F4 ist Verhalten des Originals, steht als p291 auf der Liste.
- **p292:** Der Import schrieb `_XRef_` neben die Teildateien. Jetzt wird aus einer Temp-Kopie importiert
  (`tempCopy`). In Fusion geprüft.
- `python -m pytest -q`: 1253 grün. `mkdocs build --strict` sauber.

## Offen

- **Scharnier-Auswahl** (Jörg: alle drei Varianten zur Wahl):
  - `hingePlain.f3d` (Hinge) und `hingePinned.f3d` (Hinge_Pined) sind übernommen.
  - Die Box ist bei allen drei Varianten gleich: Ihre Features nutzen nur die vier Schlitz-Parameter, und die
    nehmen alle drei Varianten.
  - Offen ist Jörgs Antwort zur Lage von „Hinge“: An Preds Stelle läge es rund 67 mm weiter außen. Vorschlag: an die
    Stelle von M3x30.
  - Danach bauen: Auswahl in Dialog, InputState, configJson, Rebuild und Clone.
- **Task 7:**
  - Vorbereitet in `fusion-auftraege`: `r28_compare` (Form gegen Preds Teile), `r28_cmd` (zwei Sätze, Stapeln,
    Rebuild), `r28_snap` (zehn Box-Snapshots neu).
  - Die Snapshots erst nach der Scharnier-Auswahl ablegen, weil sie die Einstellungen ändert.
  - Ungeprüft:
    - ob der Rebuild die alten Teile mit der alten Zeitleisten-Gruppe entfernt (die Teile werden innerhalb der Gruppe
      eingefügt);
    - Clone;
    - Export eines Satzes mit Teilen;
    - eine Box in einem Bauteil-Design: dort fügt `buildBox` keine Teile ein, weil es keine Box-Occurrence gibt.
- Bild der Box mit Kleinteilen für die Doku (`docs/assets/images/NEEDED.md`).

## Fallen

- Fusion setzt eine Lage nur auf der Proxy-Occurrence aus der Wurzel. Dort ist sie im Wurzel-Rahmen
  (`predBoxSeats.placeInSet`).
- Eine Kopie, die per `addExistingComponent` mit Lage angelegt wird, landete bei „erste Lage + eigene Lage“.
  - Deshalb erst ohne Lage anlegen, dann absolut setzen (`placeAllInSet`).
  - Die Ursache ist nicht geklärt.
- `importToTarget` einer `.f3d` legt `_XRef_` neben die Quelldatei.
- Zeitleisten-Gruppen melden `healthState` 5 (Unknown). Nur ihre Einträge zählen.
- `sketches.add(face)` projiziert die Kanten der Fläche. Für eigene Skizzen auf Flächen `addWithoutEdges` nehmen.

## Nicht löschen ohne Jörg

`wt-r27merge` und der Branch `runde-27-merge` aus Runde 27 können weg. Das entscheidet Jörg über die Hauptsitzung.
