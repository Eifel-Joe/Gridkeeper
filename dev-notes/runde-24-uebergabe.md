# Runde 24 – README und Doku für Gridkeeper (p231, p230, p237)

Branch `runde-24` im Worktree `wt-doku`, von master fce1f12. Kein Push, kein Merge, keine Tags.

## Plan

1. Interne Notizen aus `docs/` holen: `docs/specs` → `dev-notes/specs`, `docs/plans` → `dev-notes/plans` (git mv),
   Verweise in Tests und e2e-Skripten angepasst. `docs/` gehört danach allein der Website.
2. MkDocs-Material-Gerüst: `mkdocs.yml` (wie SpoolmanScale-Docs, ohne i18n), `.github/workflows/pages.yml` mit
   `mkdocs build --strict` (wirkt erst nach des Nutzers Freigabe, Pages muss im Repo eingeschaltet werden).
3. Bilder: die Original-Bilder `documentation/assets` nach `docs/assets` verschoben (MkDocs liest nur `docs/`), noch
   passende davon eingebunden. Neue Bilder als Platzhalter `docs/assets/images/<name>.png` (graue Platzhalter-PNG, damit
   `--strict` baut), Liste in `docs/assets/images/NEEDED.md`.
4. Seiten (nur Englisch), Befehlsnamen schon „Gridkeeper …“ (Runde 23), Dialogfelder wie im Code:
   Home, Installation, What's new, Baseplates, Bins (Größe, Körper, Fächer, Scoop, Label-Tab, Basis), Labels und
   Farben/Mehrfarbdruck, Cullenect-Taschen und Einleger mit Symbolen, Settings/Rebuild/Clone, Speichern/Laden,
   Parameter, Known deviations (p237), Snapshot-Tests für Entwickler, Credits und Lizenz.
5. README neu: Gridkeeper, „our further development of GridfinityGenerator“, vibe-coded, nur ZIP aus den
   GitHub-Releases, Credits, Lizenz, Link auf die Doku (Platzhalter-Adresse).
6. `mkdocs build --strict` und `python -m pytest -q` grün, Review per Opus-Subagent (Inhalt gegen Code), Funde einarbeiten.

Commits je Teil.

## Offen / für die Hauptsitzung

- Die Projekt-`CLAUDE.md` (außerhalb des Forks) nennt die Spec noch unter `FusionGridfinityGenerator/docs/specs/…`,
  nach dem Merge heißt der Pfad `dev-notes/specs/…`.
- Doku-Adresse ist ein Platzhalter (`https://eifel-joe.github.io/Gridkeeper/`), Repo wird noch umbenannt.

## Ergebnis (16.11.2026)

- `mkdocs build --strict` fehlerfrei, alle 59 Bildpfade der gebauten Seiten (auch die `<picture>`-Pfade, die MkDocs
  nicht prüft) zeigen auf vorhandene Dateien. `python -m pytest -q`: 930 passed.
- Review per Opus-Subagent, Inhalt gegen Code: 12 Abweichungen gefunden und eingearbeitet (u. a. Einleger-Text hat
  keine Untergrenze, nur einen Hinweis nach OK; Bin-Text, der nicht passt, lässt den Bau scheitern statt OK zu sperren;
  Bin-Höhe ohne Zusatz-Einheit, Lippe +3,8 mm; jede Label-Textänderung baut beim Rebuild neu; Cullenect schaltet auch
  Label color ab; Heavy ~1,5-fache Strichstärke).
- Bilder: 20 Platzhalter, Liste in `docs/assets/images/NEEDED.md`.

## Offen / Folgepunkte (nicht in dieser Runde, Code)

- Projekt-`CLAUDE.md` (außerhalb des Forks) nennt noch `FusionGridfinityGenerator/docs/specs/…`, jetzt `dev-notes/specs/…`.
- „Läuft neben dem Original“ stimmt erst, wenn Runde 23 auch `config.ADDIN_NAME`/`COMPANY_NAME` (Befehls-IDs
  `LevMishin_GridfinityGenerator_cmd*`) und die Manifest-`id` ändert; heute sind sie gleich wie beim Original.
- Info-Links der Bin- und Baseplate-Dialoge zeigen auf das Wiki des Originals, nicht auf die neue Doku.
- Info-Zeile im Bin-Rebuild-Dialog (`commandCreateBin/entry.py` ~834) sagt „like its height or label“, ein Label-Text
  baut aber neu (binBuilder.parameterEdits).
- Release-ZIP heißt noch `GridfinityGenerator-<tag>.zip` (`release.yml`); Doku nennt keinen Dateinamen.
- „Gridkeeper tests: update snapshots“ in der Doku angenommen (Runde 23 nannte nur „tests: run“).

## Vollständigkeits-Prüfliste (Nutzer 16.11.2026: „wirklich alles erklären“)

Erzeugt aus `commands/*/entry.py` (jedes `add…Input`-Label und die Feld-Tupel der Schleifen) gegen die Doku: ein Feld
gilt als erklärt, wenn eine Seite es fett (`**Label**`) oder als Überschrift nennt. Ergebnis: 0 fehlend. Bedeutung,
Einheit, Standard, Bereich und Sperren stehen in den Tabellen der jeweiligen Seite.

| Dialog | Feld | Seite(n) |
|---|---|---|
| Bin | Actual dimensions (mm) | bins/size.md |
| Bin | Basic sizes | bins/index.md, bins/size.md |
| Bin | Base width unit (mm) | bins/size.md, cullenect/inserts.md, help/messages.md |
| Bin | Base length unit (mm) | bins/size.md |
| Bin | Bin height unit (mm) | bins/size.md |
| Bin | Bin xy clearance (mm) | baseplates.md, bins/size.md |
| Bin | Main dimensions | baseplates.md, bins/index.md, bins/size.md |
| Bin | Bin width, X (u) | bins/size.md |
| Bin | Bin length, Y (u) | bins/size.md |
| Bin | Half grid | bins/base.md, bins/size.md, help/faq.md |
| Bin | Bin height, Z (u) | bins/size.md |
| Bin | Custom shape | bins/size.md, help/messages.md |
| Bin | Bin features | bins/body.md, bins/index.md |
| Bin | Generate body | bins/body.md |
| Bin | Bin type | bins/body.md |
| Bin | Bin wall thickness | bins/body.md, help/messages.md |
| Bin | Generate lip for stackability | bins/body.md |
| Bin | Generate lip notches | bins/body.md |
| Bin | Fold long walls for stiffness | bins/body.md |
| Bin | Bin compartments | bins/compartments.md, bins/index.md, bins/labels.md |
| Bin | Edit compartment layout | bins/body.md, bins/compartments.md |
| Bin | Dividers up to the top on grid lines | bins/compartments.md |
| Bin | Scoop | bins/compartments.md, bins/index.md |
| Bin | Add scoop (along bin width) | bins/compartments.md |
| Bin | Scoop max radius (mm) | bins/compartments.md |
| Bin | Label tab | bins/labels.md |
| Bin | Add label tab (along bin width) | bins/labels.md, cullenect/pockets.md |
| Bin | Tab length (u) | bins/labels.md |
| Bin | Tab width (mm) | bins/labels.md |
| Bin | Tab offset (u) | bins/labels.md |
| Bin | Tab overhang angle | bins/labels.md |
| Bin | Tab top angle | bins/labels.md, cullenect/pockets.md |
| Bin | Hollow tab | bins/body.md, bins/labels.md |
| Bin | Open through side walls | bins/labels.md |
| Bin | Label text | bins/labels.md, cullenect/pockets.md |
| Bin | Label icon | bins/labels.md, cullenect/pockets.md, cullenect/symbols.md |
| Bin | Label style | bins/labels.md, cullenect/pockets.md |
| Bin | Bold label text | bins/labels.md, cullenect/pockets.md |
| Bin | Label color | bins/labels.md, cullenect/pockets.md, getting-started/whats-new.md, working/colors.md |
| Bin | Custom label color | bins/labels.md, help/messages.md, working/colors.md |
| Bin | Socket play (mm) | bins/labels.md, cullenect/pockets.md, help/faq.md |
| Bin | Base interface features | bins/base.md, bins/index.md |
| Bin | Generate base | bins/base.md, bins/body.md, help/faq.md |
| Bin | Add joint origins | baseplates.md, bins/base.md, working/components.md |
| Bin | Add screw holes | baseplates.md, bins/base.md |
| Bin | Screw hole diameter | baseplates.md, bins/base.md |
| Bin | Add magnet sockets | bins/base.md |
| Bin | Add tabs to magnet sockets | bins/base.md |
| Bin | Magnet cutout diameter | baseplates.md, bins/base.md |
| Bin | Magnet cutout depth | baseplates.md, bins/base.md |
| Bin | Changes | bins/index.md, working/save-load.md |
| Bin | Preview | baseplates.md, bins/index.md |
| Bin | Show auto update preview (slow) | bins/index.md, help/faq.md |
| Bin | Update preview once | bins/index.md |
| Bin | Last preview | baseplates.md, bins/index.md, cullenect/inserts.md, help/messages.md |
| Bin | Crease depth | bins/body.md |
| Bin | Creased wall min length (u) | bins/body.md |
| Bin | Crease panel max length (u) | bins/body.md |
| Bin | Creased bin min height (u) | bins/body.md |
| Bin | Save as defaults | working/save-load.md |
| Bin | Reset to defaults | working/save-load.md |
| Bin | Clear defaults | working/save-load.md |
| Bin | Save to file | working/save-load.md, working/settings-rebuild-clone.md |
| Bin | Load from file | working/save-load.md |
| Bin | Copy | working/save-load.md, working/settings-rebuild-clone.md |
| Baseplate | Basic size | baseplates.md |
| Baseplate | Base width unit, X (mm) | baseplates.md |
| Baseplate | Base length unit, Y (mm) | baseplates.md |
| Baseplate | Bin xy clearance (mm) | baseplates.md, bins/size.md |
| Baseplate | Clearance between plates (mm) | baseplates.md |
| Baseplate | Main dimensions | baseplates.md, bins/index.md, bins/size.md |
| Baseplate | Sizing mode | baseplates.md |
| Baseplate | Plate width, X (u) | baseplates.md |
| Baseplate | Plate length, Y (u) | baseplates.md |
| Baseplate | Area width, X | baseplates.md |
| Baseplate | Area length, Y | baseplates.md |
| Baseplate | Fill gaps with half cells | baseplates.md |
| Baseplate | Print bed | baseplates.md |
| Baseplate | Printer | baseplates.md |
| Baseplate | Bed width, X | baseplates.md |
| Baseplate | Bed length, Y | baseplates.md |
| Baseplate | Bed margin | baseplates.md |
| Baseplate | Result | baseplates.md |
| Baseplate | Features | baseplates.md |
| Baseplate | Baseplate type | baseplates.md |
| Baseplate | Add joint origins | baseplates.md, bins/base.md, working/components.md |
| Baseplate | Magnet cutouts | baseplates.md |
| Baseplate | Add magnet cutouts | baseplates.md |
| Baseplate | Magnet cutout diameter | baseplates.md, bins/base.md |
| Baseplate | Magnet cutout depth | baseplates.md, bins/base.md |
| Baseplate | Screw holes | baseplates.md |
| Baseplate | Add screw holes | baseplates.md, bins/base.md |
| Baseplate | Screw hole diameter | baseplates.md, bins/base.md |
| Baseplate | Screw head cutout diameter | baseplates.md |
| Baseplate | Side padding | baseplates.md |
| Baseplate | Add side padding | baseplates.md |
| Baseplate | Padding left | baseplates.md |
| Baseplate | Padding top | baseplates.md |
| Baseplate | Padding right | baseplates.md |
| Baseplate | Padding bottom | baseplates.md |
| Baseplate | Advanced plate size options | baseplates.md |
| Baseplate | Extra bottom thickness | baseplates.md |
| Baseplate | Vertical clearance under bins | baseplates.md, help/faq.md |
| Baseplate | Add connection holes | baseplates.md |
| Baseplate | Connection hole diameter | baseplates.md |
| Baseplate | Inputs | baseplates.md, cullenect/inserts.md, working/save-load.md |
| Baseplate | Preview | baseplates.md, bins/index.md |
| Baseplate | Show preview (slow) | baseplates.md, cullenect/inserts.md, help/faq.md |
| Baseplate | Last preview | baseplates.md, bins/index.md, cullenect/inserts.md, help/messages.md |
| Baseplate | Grid position, X | baseplates.md |
| Baseplate | Grid position, Y | baseplates.md |
| Baseplate | Save as defaults | working/save-load.md |
| Baseplate | Reset to defaults | working/save-load.md |
| Baseplate | Clear defaults | working/save-load.md |
| Baseplate | Save to file | working/save-load.md, working/settings-rebuild-clone.md |
| Baseplate | Load from file | working/save-load.md |
| Baseplate | Copy | working/save-load.md, working/settings-rebuild-clone.md |
| Label | Size | cullenect/inserts.md |
| Label | Width (u) | cullenect/inserts.md |
| Label | Insert | cullenect/inserts.md |
| Label | Text | cullenect/inserts.md, working/colors.md, working/components.md |
| Label | Custom color | cullenect/inserts.md, help/messages.md |
| Label | Symbol | cullenect/inserts.md |
| Label | Pocket | cullenect/inserts.md, cullenect/pockets.md, help/messages.md |
| Label | Inputs | baseplates.md, cullenect/inserts.md, working/save-load.md |
| Label | Preview | baseplates.md, bins/index.md |
| Label | Last preview | baseplates.md, bins/index.md, cullenect/inserts.md, help/messages.md |
| Label | Correction width | cullenect/inserts.md, help/faq.md |
| Label | Correction height | cullenect/inserts.md, help/faq.md |
| Label | Head | cullenect/inserts.md, cullenect/symbols.md |
| Label | Shaft | cullenect/inserts.md, cullenect/symbols.md |
| Label | Threads | cullenect/inserts.md, cullenect/symbols.md |
| Label | Driver | cullenect/inserts.md, cullenect/symbols.md |
| Label | None | working/colors.md |
| Label | Save as defaults | working/save-load.md |
| Label | Reset to defaults | working/save-load.md |
| Label | Clear defaults | working/save-load.md |
| Label | Save to file | working/save-load.md, working/settings-rebuild-clone.md |
| Label | Load from file | working/save-load.md |
| Label | Copy | working/save-load.md, working/settings-rebuild-clone.md |

### Meldungen, Befehle, Knöpfe, Parameter → Seite

| Thema | Seite |
|---|---|
| Alle OK-Sperren (Cullenect-Wand 1,2 mm, Form, Farbe, Bereiche, Fill-Area-Fehler, Einleger-Größe/Korrektur/Symbol/Text, „Two lines don't fit …“, Tasche zu klein) | `help/messages.md` › OK stays locked |
| Meldungen nach dem Bau (Hybrid-Umstellung, dünne Schrift Einleger/Bin, Laden mit Änderungen), Preview-Notiz | `help/messages.md` › Messages after building |
| Fehlerfenster „Gridfinity error“ (Copy report, Copy and open an issue), „… doesn't fit the label even at …“, Timeline aus | `help/messages.md` › Build failed |
| Rebuild-Meldungen (Features neu wählen, Einleger passt nicht mehr, Tasche nicht wählbar, Bin nach Einleger, Timeline-Gruppe, Auswahl) | `help/messages.md` › Rebuild |
| Settings-Datei-Meldungen | `help/messages.md` › Settings files, `working/save-load.md` |
| Rechtsklick: Gridkeeper settings / rebuild / clone | `working/settings-rebuild-clone.md` |
| Knöpfe Settings-Fenster (Save to file, Copy, Clone into new …, Rebuild) | `working/settings-rebuild-clone.md` |
| Knöpfe Changes/Inputs (Save as defaults, Reset to defaults, Clear defaults, Save to file, Load from file, Copy) | `working/save-load.md` |
| Parameter gfBinN_baseWidth/baseLength/heightUnit/heightU/label(K), gfPlateN_baseWidth/baseLength/padding*, gfLabelN_baseWidth/width/text1/text2 und was beim Ändern passiert | `working/parameters.md`, `bins/labels.md`, `cullenect/inserts.md` |
| Mehrfarbdruck, Export 3MF, Bambu Studio (Teile, Filament je Teil) | `working/colors.md` |
| Installation, Update, Deinstallation, Parallelbetrieb mit dem Original | `getting-started/installation.md` |
| Fehlerbehebung / FAQ | `help/faq.md` |
| Testbefehle (tests: run, tests: update snapshots) | `developers/snapshot-tests.md` |
