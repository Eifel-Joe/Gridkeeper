# Plan: Upstream-Runde 17.11. – Export (p13, p300)

Spec: `dev-notes/specs/2026-11-17-upstream-export.md`. Worktree `upstream-2026-11-17-e953b0`. Je Task: Test → RED →
Code → GREEN → volle Suite → Commit. Testbefehl `python -m pytest`, Doku `mkdocs build --strict`.

## Task 1 – Merge nach Einteilung (ein Merge-Commit)
- [ ] `git merge --no-ff --no-commit upstream/master`.
- [ ] Nicht übernehmen entfernen: alle `documentation/assets/**` aus dem Merge (DU → `git rm`, neue A → `git rm`),
      `documentation/wiki`, `tools/wiki`, `.github/workflows/wiki.yml`, `tests/test_wiki_pages.py`; `README.md` = HEAD.
      `tools/screenshots`-Teile aus 45d280a/568f7af auf HEAD zurück (`dialogRecorder.py`, `fakeAdsk/adsk/core.py`,
      `page/*`, `README.md`-Zeile aus 45d280a, `shots.json` = HEAD, `models/baseplate-*.json` neu → raus); behalten:
      `models/bin-label-tab-hollow.json`, `models/bin-lip-notches.json`, `commandModelScreenshots/*`, README-Zeile aus
      873db19; `models/_baseplate.json` mit `plateEdgeClearance`.
- [ ] Konflikte nach Tabelle: `binBuilder.py` (beide Importe; Einfärben-Block bleibt **vorerst wie Upstream**, Task 3
      ändert ihn testgetrieben), `entry.py` Import, `configJson.py`.
- [ ] `release.yml`: nur die Action-Versionen aus 2588dd7, sonst unser Stand (Diff lesen).
- [ ] pytest: erwartet grün außer evtl. Feldnamen in eigenen Snapshot-Settings (dann Task 2). Commit
      „Merge upstream/master (5627083): Export, 3MF, Plattenabstand je Kante (p13)“.

## Task 2 – Migration `plateClearance` auf allen Lesewegen
- Test `tests/test_config_json.py`: `renamedSettings(GENERATOR_LABEL, {...})` gibt unverändert zurück; unbekannter
  Generator (`'box'`) bricht nicht; ein alter Bin-/Baseplate-Tag mit `plateClearance` liest über den Rebuild-Weg
  (`configJson.stateFromJson`/unser Lade-Pfad mit `OLDER_VALUES`) `plateEdgeClearance` = halber Wert. RED erwartet
  für LABEL/`box` (`KeyError`) und ggf. den Rebuild-Weg.
- Code: `RENAMED_FIELDS[GENERATOR_LABEL] = {}`, `.get(generator, {})`, Aufruf dort ergänzen, wo unser Pfad ihn
  umgeht. Eigene Snapshot-`settings.json` mit `plateClearance` umschreiben (falls vorhanden). GREEN, Commit.

## Task 3 – Fusion-Einfärben nur bei Umriss ohne Farbe
- Test: reine Funktion `labelFaces.paintsLetterFaces(generateBody, labelStyle, labelColor) -> bool` (neu, ohne
  Fusion): Umriss+'' → True; Umriss+'#D02020' → False; Gravur/erhaben/Cullenect → False; ohne Body → False. RED.
- Code: Funktion + Aufruf in `binBuilder`. GREEN, Commit.

## Task 4 – `lib/exportParts.py`: Teile erkennen (p300)
- Tests `tests/test_export_parts.py` (ohne Fusion, Stub-Objekte mit `name`/Tag):
  `EXPORT_TAGS == ('bin','baseplate','label','box')`; `isExportTag('label')` True, `'pocket'`/`'container'` False;
  `isTextComponent('Text')`, `('Text (1)')` True, `('Textile')` False (gleiche Regel wie `partTag`: hier
  `name == 'Text' or name.startswith('Text (')` – prüfen, ob `partTag`s `startswith('Text')` dasselbe will, sonst
  angleichen); `groupParts(bodies)`: getaggte Körper außerhalb Text = Teile, Text-Körper (auch getaggte) → Marking
  ihres Teils, Text-Körper ohne Teil fallen weg. RED.
- Code: `exportParts.py` mit diesen Funktionen, Teil-Zuordnung über eine übergebene Funktion `partOf(body)` (in Fusion
  `tagUtils.partTag`). GREEN, Commit.

## Task 5 – Meshes zusammenführen und färben
- Test `tests/test_export_parts.py`: `mergeMarkings(part: MeshObject, markings: list[MeshObject]) -> MeshObject`:
  Vertices/Dreiecke angehängt mit Index-Versatz, `painted` = Teil-`painted` ∪ alle Marking-Dreiecke; ohne Markings
  unverändert; Name bleibt der des Teils. STL: `stlFile`-Ausgabe eines zusammengeführten Teils hat Dreieckszahl Summe. RED.
- Code: Funktion in `exportParts.py` (nutzt `threeMf.MeshObject`). GREEN, Commit.

## Task 6 – `commandExport` an unsere Teile und unser Menü anpassen
- `ExportItem` bekommt `markings: list[BRepBody]` (sichtbare Körper der Text-Occurrence(s) des Teils, an ihrem Platz).
- `isTagged`/`isGridfinityBody`/`gridfinityBodies`: über `exportParts.EXPORT_TAGS` und `tagUtils.partTag`; Text-Körper
  sind kein Teil; Klick auf Buchstaben → sein Teil.
- `meshOf`: Teil-Mesh + Marking-Meshes über `mergeMarkings`, gefärbt nur mit „Color label text“. STL je Teil
  zusammengeführt; STEP: Teil + Markings in einer Datei (`exportStep` erweitern).
- Tests: was ohne Fusion geht, steht in Task 4/5; hier Fusion-Auftrag (Task 8). Volle Suite grün, Commit.

## Task 7 – Doku und CHANGELOG
- `docs/working/export.md` + Navigation in `mkdocs.yml`, `docs/baseplates.md`, `docs/bins/size.md`,
  `docs/working/colors.md`, `docs/getting-started/whats-new.md`, `docs/assets/images/NEEDED.md`,
  `CHANGELOG-CULLENECT.md` mit Credits. `mkdocs build --strict` grün, Commit.

## Task 8 – Fusion-Auftrag `ug2_export.py`
- Job in `D:\Entwicklung\Gridfinity\fusion-auftraege`, Muster `ug_snap.py` (Paket aus diesem Worktree, eigener Name,
  Schritt-Zustand, je Schritt < 50 s). Schritte: `build` (neues Dokument, 4 Teile laut Spec), `export` (Sammlung, 3MF,
  STL in Temp-Ordner, Ergebnis-JSON), `checks` Snapshots: `baseplate_2x2_light`, `baseplate_3x2_full`,
  `baseplate_fill_area_pieces`, eine Bin mit Umriss-Label ohne Farbe, eine mit Farbe. Auswertung des 3MF/JSON per
  Python im Worktree. Jobname an die Hauptsitzung.

## Task 9 – Review, merge-tree gegen runde-28, PR
- Opus-Review (Diff + Spec + Plan), Funde über receiving-code-review.
- `git merge-tree --write-tree --name-only HEAD runde-28`: Konflikte mit a8233fb/3452e56 notieren, Vorschlag im PR-Text.
- PR-Text der Hauptsitzung zeigen; Push + PR gegen `claude/upstream-2026-11-16-e588a3` laut Dauerfreigabe erst bei
  grünen Tests und Review ohne offene Funde. Neue Funde (z. B. Mehrfarben-Export) in die Liste, p301–p309.
