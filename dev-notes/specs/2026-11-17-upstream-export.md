# Upstream-Runde 17.11. – Export, 3MF, Plattenabstand (p13) und Export für alle Teile (p300)

Stand 2026-11-17. Rundenname „Upstream-Runde 17.11.“. Punkte p13 „Eigene Kopie mit dem Original-Generator aktuell
halten“ und p300 „Export und 3MF auch für Box, Kleinteile und Cullenect-Einleger“. Branch
`claude/upstream-2026-11-17-e953b0`, abgezweigt von PR #1 (`claude/upstream-2026-11-16-e588a3`, 6bff877).
`git merge --no-ff upstream/master`: Upstream `Le0Michine/FusionGridfinityGenerator`, 513e6ab..5627083, 20 Commits von
Lev Mishin (Le0Michine), CC BY-NC-SA 4.0. Version bleibt 1.0.0. Einteilung freigegeben, Muster `2026-11-17-upstream-lippentypen.md`.

## Einteilung

| Commit | Inhalt | Umgang |
|---|---|---|
| d0ad89c | `lib/labelFaces.py`: Buchstaben der Umriss-Labels bekommen in Fusion eine eigene Darstellung | übernehmen, siehe „Zusammenspiel“ |
| e4c885f | `lib/threeMf.py`: 3MF, Buchstaben-Dreiecke für Bambu/Orca/Prusa eingefärbt | übernehmen |
| 4b2f167 | `commands/commandExport`, `lib/stlFile.py`: Export per Rechtsklick und „Alle“ (3MF/STL/STEP) | übernehmen, an unser Kontextmenü und unsere Teile angepasst (p300) |
| a8233fb | exakte Bin-Größe im Dialog (`lipHeight`) | übernehmen, Import neben unserem `lipTopTrimHeight` |
| 3452e56 | Baseplate: `plateClearance` → `plateEdgeClearance` (Abstand je Kante = halber Spalt), Migration `RENAMED_FIELDS` | übernehmen, Migration auch für Label (und vorbereitet für Box) |
| 2588dd7 | Node-24-Actions | nur `release.yml`; `wiki.yml` entfällt |
| 873db19, b287cf3 | Entwicklerwerkzeuge `commandModelScreenshots`, `tools/screenshots/models/bin-*.json` | übernehmen, ohne Bilder und ohne `tools/wiki` |
| 4cfe1de, 465241b, a82c5e6 | Wiki, `wiki.yml`, `tools/wiki`, `tests/test_wiki_pages.py`, `documentation/wiki` | nicht übernehmen |
| 9281fc4, 81d91b9 | Contribution Guide | nicht übernehmen |
| 45d280a, 5627083, 568f7af, 6b15239 | README, Upstream-Bilder, Diagramme, Bild-Vorlagen dieser Commits | nicht übernehmen (alle Upstream-Bilder bleiben gelöscht, README = unsere) |

**Entschieden (Hauptsitzung, 17.11.):** die `tools/screenshots`-Teile aus 45d280a und 568f7af werden übernommen
(Entwicklerwerkzeuge, Vorgabe: Werkzeuge ja, Doku/Bilder nein), ohne Bilder; `shots.json` = unsere Fassung plus die neuen
Einträge. Die ursprüngliche Frage: 45d280a und 568f7af ändern außer Doku auch
`tools/screenshots` (Dialog-Aufnahme des Export-Dialogs: `dialogRecorder.py`, `fakeAdsk`, `page/*`; Baseplate-Vorlagen
`models/baseplate-*.json`, `_baseplate.json` mit `plateEdgeClearance`). Vorgabe: nicht übernehmen, unser Stand bleibt.
Ausnahme ohne Rückfrage: `tools/screenshots/models/_baseplate.json` bekommt den neuen Feldnamen, sonst lädt die
Vorlage ein umbenanntes Feld (wird ohnehin migriert, aber die Vorlage soll den gültigen Namen tragen).

## Probelauf (`git merge --no-commit`)

Konflikte: `README.md`, `binBuilder.py` (Import, Einfärben nach dem Taggen), `commandCreateBin/entry.py` (Import
`lipHeight`/`lipTopTrimHeight`), `lib/configJson.py` (`plateEdgeClearance` neben unserem `GENERATOR_LABEL`),
`tools/screenshots/shots.json`, 74 Upstream-Bilder (bei uns gelöscht). Ohne Konflikt dazu: `commandExport`,
`labelFaces`, `threeMf`, `stlFile`, Baseplate-Umbenennung, 5 Baseplate-Snapshot-`settings.json`, Wiki-Dateien.

## Konflikttabelle

| Stelle | Lösung |
|---|---|
| `README.md` | unsere Fassung |
| `binBuilder.py` Import | beides (`assembly`, `labelFaces`) |
| `binBuilder.py` nach dem Taggen | beides: `generatedBodies = movedBodies` bleibt; Einfärben nur bei Umriss **ohne** Farbe (siehe unten) |
| `commandCreateBin/entry.py` Import | `LIP_TYPES, lipTopTrimHeight, lipHeight` + unsere Importe |
| `lib/configJson.py` | `plateEdgeClearance` in `MM_FIELDS`, unser `GENERATOR_LABEL` bleibt; `RENAMED_FIELDS` bekommt `GENERATOR_LABEL: {}`, `renamedSettings` liest mit `.get(generator, {})`, damit ein neuer Generator (Box, R27) ohne Eintrag nicht bricht |
| `tools/screenshots/shots.json` | unsere Fassung (Ausgabe `tools/screenshots/out`) |
| Upstream-Bilder, neue Bilder, `documentation/wiki`, `tools/wiki`, `wiki.yml`, `test_wiki_pages.py` | nicht übernehmen |
| 5 Baseplate-Snapshots `settings.json` | übernehmen (nur Feldname + halber Wert, Upstream-begründet), im PR-Text nennen; Fingerprints/Körper unverändert |
| eigene Baseplate-Snapshots mit `plateClearance` | pytest zeigt, ob es welche gibt; dann gleich umschreiben wie Upstream |

Laden alter Einstellungen: `renamedSettings` muss überall greifen, wo wir Einstellungen lesen (Load-Datei,
Rebuild/Clone aus dem Tag, `OLDER_VALUES` aus PR #1, Snapshot-Tests). Prüfen, dass Upstreams Aufrufstelle unsere Pfade
abdeckt; sonst ergänzen (pytest).

## Zusammenspiel mit unserem Code

**Farbige Texte sind bei uns eigene Körper (p86, p90).** Ein Bin-Label mit Farbe und jeder Cullenect-Einleger mit Text
haben Text- und Symbolkörper in der Komponente `Text` des Teils (Bin-Label: Umriss/Gravur bündig gefüllt oder erhaben;
Einleger: alle Körper mit `TAG_LABEL`, später ergänzte Buchstaben ungetaggt). Upstream kennt nur Umriss-Labels ohne
eigene Körper (geteilte Flächen im Bin-Körper).

- **Fusion (d0ad89c):** `paintLetterFaces` nur bei Umriss-Label **ohne** Farbe. Mit Farbe liegen die Buchstaben als
  eigene Körper in der Ausfräsung; die Flächen darunter einzufärben wäre unsichtbar und falsch.
- **Export-Teil:** ein getaggter Körper (`bin`, `baseplate`, `label`, später `box`) plus die sichtbaren Körper der
  `Text`-Komponente(n) seines Teils (`Text`, `Text (1)` …, wie `tagUtils.partTag`). Körper in einer `Text`-Komponente
  sind nie ein eigener Teil – auch nicht der getaggte Text eines Einlegers.
- **3MF:** die Text-Körper kommen in dasselbe 3MF-Objekt wie ihr Teil (gleiche Lage), alle ihre Dreiecke sind mit dem
  Filament des Dialogs eingefärbt (Upstreams `painted`). Ohne „Color label text“ kommen sie ungefärbt mit. Damit ist der
  Teil im Slicer vollständig und der Text in Farbe, ohne Slicer-spezifische Teil-Zuordnung.
- **STL:** Text-Dreiecke in derselben Datei wie ihr Teil (ein Teil = eine Datei, vollständig). **STEP:** Text-Körper in
  derselben Datei wie ihr Teil.
- Eine Farbe je Export (Filament-Index des Dialogs) für alle Label-Texte, wie Upstream. Verschiedene Label-Farben auf
  verschiedene Filamente zu verteilen ist nicht dabei (neuer Punkt, siehe unten).

**Kontextmenü (4b2f167, „unsere Fassung bleibt maßgeblich“).** Unser `commandShowSettings`-Menü (Settings, Rebuild,
Clone, `partTag`) bleibt unverändert. Der Export-Eintrag erscheint, wenn die Auswahl ein Export-Teil ist oder einen
enthält: Körper über `partTag` (ein Klick auf einen Buchstaben zählt für seinen Teil), Komponente/Occurrence rekursiv –
auch unsere Container Grid/Bins/Label (exportiert dann alles darin). Upstreams Platz im Menü (nach „Save As Mesh“)
bleibt.

## p300: Export für alle Teile

- Eine Liste der exportierbaren Markierungen an **einer** Stelle: `lib/exportParts.py`, `EXPORT_TAGS =
  ('bin', 'baseplate', 'label', 'box')`. Neue Teile (Kleinteile R28, Box-Label p262) = ein Eintrag + ein Test.
  `'box'` steht als Literal drin (Tags sind Literale, `tagUtils`), damit Box und Deckel aus R27 beim Zusammenführen
  ohne Codeänderung mitzählen; ihre Prüfung geschieht erst nach dem Merge von R27 (eigener Fusion-Auftrag dann).
- „All Gridfinity bodies“ und Rechtsklick sammeln über diese Liste; die Auswahl zählt Teile, nicht Text-Körper.
- Cullenect-Einleger: Text und Symbole im 3MF eingefärbt (s. o.).
- Reiner Python-Kern ohne Fusion (pytest): Tag-Erkennung, Zuordnung Text→Teil (über Komponentennamen),
  Zusammenführen der Meshes mit Färbung (`threeMf.MeshObject`).
- Grenze: ein Teil ohne Komponente (Körper im Wurzelbauteil, alte Bins) hat keine `Text`-Komponente; seine farbigen
  Label-Körper gehören dann nicht erkennbar zu ihm und fehlen im Export. Im Doku-Text nennen.

## Nicht dabei

- Upstream-Wiki, Contribution Guide, Upstream-README/-Bilder/-Diagramme, Versionssprung.
- Box-Label (p262), Kleinteile (R28) – nur die Erweiterungsstelle.
- Mehrere Label-Farben auf mehrere Filamente (neuer Punkt aus p301–p309).
- Magnetgrößen (R27/R28): nicht auf diesem Branch. Nach dem Merge per `git merge-tree` gegen `runde-28` die Konflikte
  mit a8233fb/3452e56 (Bin-Dialog, Baseplate-Eingaben) auflisten und im PR-Text mit Lösungsvorschlag nennen; gelöst
  wird beim Zusammenführen durch die Hauptsitzung.

## Doku (mkdocs, `docs/`)

- Neue Seite `docs/working/export.md` (Navigation): Rechtsklick/„All“, 3MF/STL/STEP, „Color label text“ +
  Filament-Index, welche Teile (Bins, Baseplates, Cullenect-Einleger, später Box), farbige Texte im 3MF, Grenze
  Wurzelkörper. Ohne Bilder (in `docs/assets/images/NEEDED.md` vormerken).
- `docs/baseplates.md`: „Plate edge clearance“ je Kante (halber Spalt), alte Einstellungen werden umgerechnet.
- `docs/bins/size.md`: exakte Größe im Dialog.
- `docs/working/colors.md`: Umriss ohne Farbe zeigt die Buchstaben in Fusion farbig (Darstellung „Label“).
- `docs/getting-started/whats-new.md`, `CHANGELOG-CULLENECT.md` „Merged from upstream“ mit Credits (Le0Michine,
  513e6ab..5627083, übernommen/nicht übernommen), p300 als eigene Zeile.
- `mkdocs build --strict` grün.

## Ende-zu-Ende

1. `python -m pytest` grün, `mkdocs build --strict` grün.
2. Fusion-Auftrag `ug2_export.py` (über die Hauptsitzung, Code aus diesem Worktree wie `ug_snap.py`): baut in einem
   neuen Dokument eine Bin mit Umriss-Label ohne Farbe, eine Bin mit rotem Umriss-Label, einen Cullenect-Einleger mit
   blauem Text und Symbol und eine Baseplate; ruft die Export-Funktionen direkt (ohne Dialog): „All“-Sammlung, 3MF,
   STL. Prüft: 4 Teile, kein Text-Körper als eigener Teil, je Label-Teil eingefärbte Dreiecke > 0 (Einleger: genau die
   Text-Dreiecke), STL-Dateien je Teil; Rechtsklick-Erkennung `isTagged` für Buchstabe, Bin, Container. Plus
   Snapshot-Stichprobe Baseplates (Umbenennung) und Umriss-Bins (Einfärben ändert keine Geometrie).
3. 3MF in Bambu Studio/OrcaSlicer öffnen, Farben prüfen (Testplan im PR-Text).

## Neue Funde

`liste: neu`, `gruppe: Neu aufgetaucht`, `herkunft: Upstream-Runde 17.11.`, IDs p301–p309.
