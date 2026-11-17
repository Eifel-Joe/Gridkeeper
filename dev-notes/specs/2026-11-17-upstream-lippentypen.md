# Upstream-Runde 17.11. – Lippentypen und Entwicklerwerkzeuge einmergen (p13)

Stand 2026-11-17. Punkt p13. Branch `claude/upstream-2026-11-16-e588a3` von `master` (3091fc6), eigener Worktree.
`git merge --no-ff upstream/master`: Upstream `Le0Michine/FusionGridfinityGenerator` `master`, Merge-Basis fba170e,
neuer Stand 513e6ab, 13 Commits von Lev Mishin (Le0Michine), CC BY-NC-SA 4.0. Version bleibt 1.0.0.
Einteilung von Nutzer freigegeben („Passt so“), Vorgehen wie Runde 12 (`2026-11-15-upstream-2-4-merge.md`) und Runde 22.

## Probelauf

`git merge --no-commit` zeigt 6 Code-/Textdateien, 4 kleine Daten-Konflikte, 74 Bilder (bei uns gelöscht, bei
Upstream geändert), das alte Manifest und 46 Snapshot-Dateien im Konflikt. Dazu übernimmt Git ohne Konflikt
die neuen Body-Dateien vieler bestehender Snapshots (409b961), weil wir sie seit fba170e nicht angefasst haben.

## Konflikttabelle

| Stelle | Upstream | Lösung |
|---|---|---|
| `commandCreateBin/inputState.py`, `lib/defaultSettings.py`, `binBodyGeneratorInput.py`, `tools/screenshots/models/_bin.json` | Felder `lipType`, `isLipTopTrimmed` (`lipTopTrimHeight`) | beides: unser `hasDividersToTop`/`raisedDividers` und Upstreams Felder. Vorgaben `Light`, `True` = bisheriges Verhalten |
| `binBodyGenerator.py` Importe | `LIP_TYPE_FULL`, `createLipSupport`, `lipInnerInset` | beides (unsere Cullenect-, Layout- und Trenner-Importe bleiben, `applyTo` bleibt) |
| `commandCreateBin/entry.py` (5 Hunks) | Eingabe-IDs, Zustandstabelle, Vorgaben, Dropdown „Lip type“ mit Symbolen, Haken „Trim lip top“, Freigabe mit der Lippe | beides; Freigabe: Lippentyp und Trim mit `generateLip` wie die Kerben, unser `raisedDividers.optionEnabled` bleibt |
| `commandModelScreenshots/entry.py`, `presets.py` | Dialog-Aufnahmen aus der Bilder-Palette (`SHOT_OUTPUT`), Schnittebenen | Upstreams Funktionen übernehmen, alle Ausgaben bleiben unter `tools/screenshots/out/` (`gif`, `models`, `ui`) |
| `commandShowSettings/entry.py` (4ed1476, ohne Konflikt) | Kontextmenü auch, wenn die Komponente (Occurrence) gewählt ist: `componentTag` = der eine getaggte Körper der Komponente | unsere Fassung (`partTag`, Text-Buchstaben p71) bleibt; Upstreams Komponenten-Zweig kommt dazu, denn den Fall „Komponente im Browser gewählt“ konnte unsere Fassung nicht. Unsere Container Bins/Grids/Labels haben keine Körper und bleiben ohne Menü; eine Bin-Komponente mit farbigen Label-Körpern hat genau einen getaggten Körper |
| `commandSnapshotTests` (12d5ce3, ohne Konflikt) | Status-Filter, „Update snapshot“ aus dem Testfenster, „Add new“ | übernehmen; prüfen, dass es unser `saveSnapshot`/`snapshotSettings` nutzt |
| `README.md` | Text und Upstream-GIFs zu Lippentypen | unsere Fassung |
| 74 Bilder `documentation/assets/{gif,models,ui}`, neu `bin-lip-*` | aktualisiert/neu | nicht übernehmen, bleiben gelöscht (Runde 26, „Own pictures only“) |
| `commandCreateBin/resources/lipTypes/*` | Dialog-Symbole der Lippentypen | übernehmen (Code-Ressource, kein Doku-Bild) |
| `tools/lipTypeIcons.py`, `tools/screenshots/*` (Presets, shots, timelines der Lippe) | Werkzeuge | übernehmen, Ausgabe nach `tools/screenshots/out/` |
| `GridfinityGenerator.manifest` (4d3a4fd) | 2.4.x | bleibt gelöscht, `Gridkeeper.manifest` 1.0.0 unverändert |
| `tests/e2e/README.md` | 7 neue Fälle | beides |
| bestehende Snapshots (body*.smt, preview.png, fingerprint.json, settings.json) | neu abgelegt mit Upstreams Code | **alle auf unseren Stand** (`HEAD`). Formänderung ist nicht gewollt; die fehlenden Felder `lipType`/`isLipTopTrimmed` in unseren settings.json gelten als „neuer, auf Vorgabe“ (`settingChanges`, R16 p30) |
| 7 neue Fälle `bin_*lip_full*`, `bin_2x1x3_lip_untrimmed` mit Snapshots | neu | übernehmen; die Snapshots stammen aus Upstreams Code und müssen in Fusion gegen unseren Code geprüft werden (Liste unten) |

## Eigene Ergänzung (Zusammenspiel mit unserem Code)

**Erhöhte Trenner (`hasDividersToTop`) mit voller Lippe.** Unsere Fuß-Ausschnitte für die erhöhten Trenner
(`createStackedFootCutters`) bilden den Fuß einer aufgestellten Bin ohne Bodenfase nach – passend zur leichten Lippe.
Die volle Lippe schneidet ihre Fassung mit Bodenfase (Upstream: `hasBottomChamfer = lipType == Full`). Damit der Grat
der Trenner zur Lippe drumherum passt, bekommen die Fuß-Ausschnitte dieselbe Regel, über eine gemeinsame Funktion
`lipSocketHasBottomChamfer(lipType)` (pytest). Neuer E2E-Fall `bin_3x2x3_dividers_to_top_3_columns_lip_full` (wie
`bin_3x2x3_dividers_to_top_3_columns`, mit voller Lippe), im Snapshot-Ordner nur `settings.json` (pytest verlangt sie
je Fall), die Körper legt Fusion per „Add new“ ab. Mit leichter Lippe ändert sich nichts.

## Nicht dabei

- Upstreams README-Text und alle Upstream-Bilder; Versionssprung.
- Eigene Bilder zu den Lippentypen: in `docs/assets/images/NEEDED.md` vorgemerkt, kommen mit den nächsten Doku-Bildern.
- Magnetgrößen (Runde 27).

## Doku

`docs/bins/…`: Lippentypen Light/Full und „Trim lip top“ als Text. CHANGELOG-CULLENECT.md „Merged from upstream“ mit
Credits (Le0Michine, fba170e..513e6ab, übernommen/nicht übernommen). `mkdocs build --strict`.

## Ende-zu-Ende

pytest grün. In Fusion (über die Hauptsitzung, später): Snapshot-Tests der Fälle unten grün, bestehende Bin-Fälle
unverändert grün (Vorgaben = bisheriges Verhalten).

## Snapshot-Fälle für die Fusion-Prüfung

- neu von Upstream: `bin_2x1x3_lip_full`, `bin_2x1x3_lip_untrimmed`, `bin_2x1x3_lip_full_untrimmed_shelled_notches`,
  `bin_2x1x1_lip_full_lowest`, `bin_2x2x4_lip_full_scoop_tab`, `bin_3x3x4_l_shape_lip_full`,
  `bin_1_5x2x6_shape_half_grid_shelled_lip_full`
- neu von uns: `bin_3x2x3_dividers_to_top_3_columns_lip_full` (Add new)
- Stichprobe Vorgabe unverändert: `bin_1x1x3_plain`, `bin_3x3x4_l_shape_lip_notches`, `bin_2x1x3_shelled_notches`,
  `bin_3x2x3_dividers_to_top_3_columns`
