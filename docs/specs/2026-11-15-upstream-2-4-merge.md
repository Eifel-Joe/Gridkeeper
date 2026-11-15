# Runde 12 – Upstream v2.4.0.0 einmergen (p13)

Stand 2026-11-15. Punkt p13 „Eigene Kopie mit dem Original-Generator aktuell halten“. Ergänzt
`2026-11-14-cullenect-labels-design.md`. Branch `upstream-2.4` (Worktree `wt-upstream-2.4`), Basis `master` 83e7d3c,
`git merge --no-ff upstream/master` (65ad83a, v2.4.0.0, 23 Commits von Le0Michine, Basis 15c4b4d). 58 Konflikte.

## Was Upstream geändert hat (das, was uns berührt)

- **Parameter je Bin statt geteilter Rastermaße.** `lib/gridfinityUtils/sharedParameters.py` ist gelöscht
  (`gfBaseWidth`, `gfBaseLength`, `gfHeightUnit` gibt es für neue Bins nicht mehr). Jede Bin bekommt eigene Parameter
  `gfBinN_baseWidth`, `_baseLength`, `_heightUnit`, `_heightU`, `_label`, jeder mit Tag „welches Config-Feld, welche
  Bin“ (`tagUtils.tagParameterField`). Die Grenzen `BASE_UNIT_MIN`/`HEIGHT_UNIT_MIN` stehen jetzt in `const.py`.
- **Ganzer Zustand im Body-Tag.** `binBuilder.buildBin` schreibt `configJson.stateToJson(InputState)` in den Tag.
  „Rebuild“ (Kontextmenü, Settings-Fenster) liest ihn zurück (`readConfig` mit dem aktuellen Dialog als Grundlage für
  fehlende Felder), öffnet den Dialog damit und baut die Bin an ihrer Stelle in der Zeitachse neu. Ändern sich nur
  Felder, die einen eigenen Parameter haben (Höhe, Rastermaße, Label-Text), setzt Upstream nur die Parameter
  (`parameterEdits`), sonst echter Neubau mit Zuordnung alter → neuer Körper (`rebuildUtils.bodyMap`).
- **Configs speichern/laden/klonen** im Dialog (`configButtons`), Format `lib/configJson.py`, Standardwerte
  `lib/defaultSettings.py` (jedes `InputState`-Feld muss dort stehen, `stateFromJson` verlangt alle Felder).
- **Dialog-Zustand per Tabelle** `STATE_INPUT_IDS`/`STATE_ANGLE_INPUT_IDS`, `getInputsState`/`applyInputsState`.
- **Lippe:** Lippen-Kerben neu (eine Kerbe je Wandstoß, `createLipNotch`), der Fuß-Gitter-Schnitt ist weg. Lippensockel
  sitzt um `xyClearance·(√2−1)` tiefer (`lipSocketTop`), damit das Spiel rechtwinklig zur 45°-Fläche stimmt. Massive
  Bins ohne Unterschnitt-Fase (`hasLipBottomChamfer`).
- Shell mit runden Offsets (`isShellRounded`, Standard an), Fehlerfenster, Baseplate je Parameter, Spiel zwischen
  Baseplates, Snapshot-Fälle nur noch mit den **Abweichungen von den Standardwerten**, Snapshots mit `settings.json`.

## Je Konfliktdatei

| Datei | Upstream | Wir (Runde 1–10) | Zusammenführung |
|---|---|---|---|
| `lib/tagUtils.py` | Shared-Parameter-Tags raus, `TAG_PARAMETER_FIELD` + Body-Ids | `TAG_LABEL` | Upstream + `TAG_LABEL`; alte Shared-Tags entfallen (nur noch für Label-Befehl genutzt, s. u.) |
| `binBodyGeneratorInput.py` | `hasLipBottomChamfer` | `raisedDividers` | beide Felder |
| `commandShowSettings/entry.py` | Rebuild-Menüpunkt, Beschreibung | Label in Beschreibung | Upstream-Text + „or label“; Rebuild bleibt nur für Bin/Baseplate (Label hat kein Rebuild) |
| `binBuilder.py` (5) | Parameter je Bin, Tag mit Config, `BIN_PLACEMENT_FEATURE` | Cullenect-Sockel statt Label, Farb-Label-Körper (`labelBodies`, `movedBodies`) | Upstreams Parameter/Tag/Placement-Name; unsere Zweige bleiben: Cullenect ohne Label-Parameter, Sockel wie bisher, verschoben/getaggt werden Bin- **und** Label-Körper |
| `commandCreateBin/entry.py` (3) | `DEFAULT_STATE` statt Literale, `STATE_INPUT_IDS` | neue Eingaben Trennwände-bis-oben, Label-Farbe (Dropdown + Hex-Feld), Sockelspiel | Upstreams Form; unsere Eingaben in `STATE_INPUT_IDS` (`hasDividersToTop`, `cullenectSocketOffset`), Farbe gesondert (s. u.) |
| `binBodyLipGenerator.py` (2) | neue Kerben, `lipSocketTop` | `createStackedFootCutters` (alte Kerbenform herausgezogen, nutzen die hochgezogenen Trennwände) | Upstreams Kerben für die Lippe; `createStackedFootCutters` bleibt **nur** für die Trennwände und bekommt Upstreams `lipSocketTop` als Oberkante, damit der Trennwand-Grat zum neuen Sockel passt |
| `commandSnapshotTests/testCases.py` | Format/Defaults aus `configJson`/`defaultSettings`, `settings.json`, Fälle nur mit Abweichungen | Generator `label`, `texts` nach dem Bau, `designIntent(After)`, Prüf-Helfer (Kanten-Sichel, Einleger-Text, Farben) | Upstreams Grundlage; `label` kommt in `configJson`/`defaultSettings` (eigene Tabellen), unsere Felder und Helfer bleiben; Parameter-Namen `gfBin1_…`, `gfPlate1_…`, `gfLabel1_baseWidth` |
| `tests/test_command_ui_state.py`, `tests/test_test_cases.py` | neue Tests zu Defaults/Config | Tests zu unseren Eingaben/Fällen | beide Seiten, an neue Formate angepasst |
| `tests/e2e/README.md` | generiert | generiert | neu erzeugen mit `tests/e2e/write_readme.py` |
| 48 `tests/e2e/cases/*.json` | auf Abweichungen gekürzt | nur unsere neuen Felder mit Standardwerten ergänzt | Upstream-Seite nehmen (per Skript geprüft: unsere Seite weicht nur in Feldern mit Standardwert ab). Unsere 28 eigenen Fälle ebenfalls auf Abweichungen kürzen (`caseJson`) |

## Unsere Bin-Eingaben im Parameter-/Config-Mechanismus

- `defaultSettings.BIN` bekommt `hasDividersToTop: false`, `labelColor: ""`, `cullenectSocketOffset: 0.3` (mm).
- `configJson.MM_FIELDS[bin]` bekommt `cullenectSocketOffset` (intern cm, in Config/Tag mm wie alle Längen).
- `STATE_INPUT_IDS` bekommt `hasDividersToTop` und `cullenectSocketOffset`. `labelColor` wird aus Dropdown +
  Hex-Feld gebildet (`binLabelColor()`); `applyInputsState` setzt beides aus dem Farbwert zurück (Hex einer der
  8 Farben → Dropdown-Eintrag, sonst „Custom“ + Hex, leer → „None“). Neue reine Funktion dafür in `labelColors`.
- `configChoices`: `labelStyle` enthält `Cullenect`. Laden einer Config mit unbekannter Farbe: `labelColor` bleibt
  Text, ungültiger Wert → Dialog zeigt den bestehenden Farbfehler (kein stiller Ersatz).
- Damit stehen alle drei im Tag jeder Bin und kommen beim Rebuild/Klonen/Laden zurück. Alte Bins (vor Runde 12) haben
  keinen Config-Tag; Upstream baut sie nicht per Rebuild neu (bleibt so).
- **Parameter statt Neubau:** Upstreams Abkürzung (nur Parameter setzen) gilt weiter für Höhe und Rastermaße — Sockel
  und Trennwände hängen bereits an diesen Parametern (Ausdrücke wie bisher an `gfBaseWidth`, jetzt an
  `gfBinN_baseWidth`). Ausnahme neu: Ändert sich `labelText` und die Bin hat eine `labelColor`, wird **neu gebaut**,
  weil Fusion neue Buchstaben aus einer Parameteränderung ungefärbt anlegt (bekannt aus p120). Cullenect-Bins haben
  keinen Label-Parameter, ein Text-Wechsel dort baut ohnehin neu.
- Bekannte Grenze (wie vor dem Merge): Die Anzahl Sockel-Einheiten wird beim Bau aus dem Rastermaß bestimmt; ändert
  man nur `gfBinN_baseWidth`, passt die Breite, die Einheitenzahl nicht. Ein Rebuild über den Dialog rechnet neu.

## Label-Befehl (Einleger)

- Hing an `sharedParameters` (geteilte Basisbreite `gfBaseWidth`). Das gibt es nicht mehr. Neu wie bei Upstreams Bins:
  jeder Einleger bekommt eigenen Parameter `gfLabelN_baseWidth` (nur bei Breite in Einheiten), die Breite ist ein
  Ausdruck darauf wie bisher. Dialog-Startwert der Basisbreite = gemerkter Wert (das Übernehmen aus `gfBaseWidth`
  entfällt). `BASE_UNIT_MIN` aus `const`.
- Config speichern/laden/Rebuild für Einleger baue ich in dieser Runde **nicht** (nicht im Auftrag) → neuer Punkt p150
  „Einleger per Rechtsklick neu bauen und Configs speichern wie Bins“.
- Für die Snapshot-Fälle bekommt `configJson` den Generator `label` (MM-Felder `baseWidth`, `freeWidth`, `offsetX`,
  `offsetY`) und `defaultSettings.LABEL`.

## Tests (TDD, vor dem Code)

- `defaultSettings.BIN` lädt mit `InputState` (alle Felder, inkl. unserer drei) — schlägt heute fehl.
- `stateToJson`/`stateFromJson`: `cullenectSocketOffset` 0,03 cm ↔ 0,3 mm; Rundreise mit Cullenect + Farbe +
  Trennwänden ergibt denselben Zustand.
- `readConfig`: Config ohne unsere Felder (von Upstream gespeichert) → Felder behalten Dialogwert, Hinweis „missing“.
- `labelColors`: Farbe → (Dropdown, Hex) und zurück, für leer, alle 8 Farben, Custom.
- Text-Wechsel mit Farbe erzwingt Neubau (reine Entscheidungsfunktion).
- Testfälle: unsere Fälle laden im neuen Format, `label`-Fälle laden, Parameter-Namen `gfLabel1_baseWidth`.
- Label-Builder importiert ohne `sharedParameters`.
- Ende: `python -m pytest` vollständig grün.

## Fusion (wartet auf Freigabe der Hauptsitzung, Runde 11 belegt Fusion)

- Voller Snapshot-Lauf. Erwartet geändert und neu aufzunehmen: alle Fälle wegen Upstreams Lippe/Shell/Defaults (macht
  Upstream ebenso), unsere Fälle zusätzlich wegen Parameter-Namen und `settings.json`. Prüfen: Constraint-Check,
  Kanten-Sichel-Prüfung der Trennwände, Farbprüfung, Einleger-Text.
- Hand-Prüfung Rebuild: Cullenect-Bin mit Farbe und Trennwänden bauen, per Rechtsklick „Gridfinity rebuild“ öffnen →
  Dialog zeigt Stil Cullenect, Sockelspiel, Farbe, Trennwände; Höhe ändern → OK → gleiche Bin, höher.

## Weitere Punkte

- Manifest `2.4.0.0` (Upstream-Wert, kein Konflikt).
- `CHANGELOG-CULLENECT.md`: Abschnitt „Basis auf Upstream v2.4.0.0 gehoben“ mit Credits; Stellen, die `gfBaseWidth`
  nennen, auf `gfBinN_baseWidth` / `gfLabelN_baseWidth` umschreiben.

## Nicht dazu

- Rebuild/Config für Einleger (→ p150). Push, PR, Tag, Release, Merge nach `master`.
