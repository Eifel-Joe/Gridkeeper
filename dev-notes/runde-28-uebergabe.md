# Runde 28 – Kleinteile der Pred-Box (p261)

Branch `runde-28` (Worktree `wt-r28`), Ziel `master` des Forks. Plan: `dev-notes/plans/2026-11-17-runde-28.md`.
Spec mit den Nachträgen dieser Runde: `dev-notes/specs/2026-11-16-pred-box-design.md`.

## Stand (belegt)

- **Kleinteile im Satz:** 4 Riegel (Preds Latch_Experimental), Griff, 2 Haltestifte, 2 Scharniere (Hinge_M3x30).
  - Riegel, Griff und Stifte sind starr an Joint origins der Box gejointet. Die Gelenke heißen „<Satz> <Sitz>“.
  - Die Scharniere liegen in Druckposition neben der Box: das erste an Preds Stelle, das zweite 5 mm daneben in y
    (Nutzer: „Das passt so für das Scharnier“).
  - Die Teile sind `.f3d` in `resources/predBox`, aus Preds Datei übernommen. Herkunft und Änderungen stehen in der
    README dort.
  - Die Griffbreite folgt der Schildbreite: Schildbreite + 28,5 mm, höchstens 113,5 mm (Nutzer).
- **Fusion-Prüfung** `r28_insert_check` l5 und l6 (17.11.), beide OK:
  - 5×4×6 → 7×5×10 und 5×4×6 → 4×3×6.
  - Alle Teile da, 8 Gelenke gesund.
  - Lagen gleich Preds Datei auf 0,01 mm, Griff bei 4×3×6 57 mm breit.
  - Teile eingebettet (nicht verknüpft), kein `_XRef_`.
  - Der Bau dauert rund 90 s, der Parameterwechsel 37 s.
- **Formvergleich** `r28_compare` l3 (17.11.) BESTANDEN, Restkörper 0,0000 mm:
  - Riegel, Griff, Stift und Scharnier sind exakt Preds Teile.
  - Bericht gegen Preds eingebauten Latch:1 (ältere Form): Reste 2 × 4,41 und 2 × 17,57 mm³. Das ergibt genau den
    Volumenunterschied der beiden Riegel (26,32 mm³). Die Ausrichtung des Riegel-Gelenks stimmt also.
- **Griff** `handle.f3d` neu gebaut (`r28_handle_build` l5). Volumen gleich Preds bei beiden Halbbreiten.
- **Klicktest-Funde:**
  - F1: Rechtsklick auf den Satz zeigt Einstellungen, Rebuild und Clone.
  - F3: Export-Dateinamen tragen den Satznamen.
  - Bilder aus dem Klicktest sind in der Doku.
  - F4 ist Verhalten des Originals, steht als p291 auf der Liste.
- **p292:** Der Import schrieb `_XRef_` neben die Teildateien. Jetzt wird aus einer Temp-Kopie importiert
  (`tempCopy`). In Fusion geprüft.
- **Review** über den ganzen Branch (17.11.). Behoben:
  - Snapshot-Strukturprüfung (4c02915).
  - Export der Kleinteile mit Satznamen (0a0f9f8).
  - Namen nach dem Rebuild (Commit „Rebuild gibt auch den Kleinteilen ihre Namen zurück“).
  - Sitze nur mit Teilen, Körpername des Stifts (6fdc3ed).
  - Auf der Liste: p293 bis p295.
- **Scharniere festgejointet** (Vorschlag J, Nutzer: „Ja, beides“) und **Auswahl Hinge** (M3x30, Pinned, Plain):
  - `r28_cmd` l3/l4: zwei Sätze mit je eigenen Teilen, 20 Gelenke gesund.
  - Die Scharniere wandern beim Stapeln mit.
  - Rebuild 6×4×7 in 695 s, danach nichts ungesund und nichts übrig.
- **Box-Snapshots** neu abgelegt, alle zehn pass (`r28_snap`, 671f9e9).
- `origin/master` (PR #4) gemergt (da801b7).
- `r28_insert_check` Plain und Pinned (l11/l12): beide OK, Scharnier-Quader an der M3x30-Ecke, das zweite 5 mm daneben.
- Zweites Review über Scharniere und Auswahl: unbekanntes Scharnier wird vor dem Bau gemeldet, Preds gedruckter Stift
  heißt „Hinge pin“ (e22a70c); die Verwechslung beim Umhängen (p293) gilt jetzt auch für Scharniere.
- `python -m pytest -q`: 1362 grün. `mkdocs build --strict` sauber.

## Offen

- Bild der Box mit Kleinteilen und neues Dialogbild (`docs/assets/images/NEEDED.md`).
- Ungeprüft in Fusion: Clone; Export eines Satzes mit Teilen (Code angepasst).
- Liste: p293 (eigenes Gelenk an einem Riegel springt beim Rebuild), p295 (Vorschau fügt die Teile jedes Mal ein),
  p296 (Bau rund 95 s, Rebuild mit Stapel rund 11,5 min).

## Fallen

- Fusion setzt eine Lage nur auf der Proxy-Occurrence aus der Wurzel. Dort ist sie im Wurzel-Rahmen
  (`predBoxSeats.placeInSet`).
- Eine Kopie, die per `addExistingComponent` mit Lage angelegt wird, landete bei „erste Lage + eigene Lage“.
  - Deshalb erst ohne Lage anlegen, dann absolut setzen (`placeAllInSet`).
  - Die Ursache ist nicht geklärt.
- `importToTarget` einer `.f3d` legt `_XRef_` neben die Quelldatei.
- Zeitleisten-Gruppen melden `healthState` 5 (Unknown). Nur ihre Einträge zählen.
- `sketches.add(face)` projiziert die Kanten der Fläche. Für eigene Skizzen auf Flächen `addWithoutEdges` nehmen.

## Nicht löschen ohne Nutzer

`wt-r27merge` und der Branch `runde-27-merge` aus Runde 27 können weg. Das entscheidet Nutzer über die Hauptsitzung.
