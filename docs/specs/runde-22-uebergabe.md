# Runde 22 – Übergabe: Commits des Originals übernehmen (p13)

Stand 2026-11-16. Branch `runde-22` von `master` (4da7731). Jörg: „Auch die neuen Commits von Upstream übernehmen.“
Upstream `Le0Michine/FusionGridfinityGenerator` `master` (fba170e), 6 Commits von Lev Mishin (Le0Michine):

| Commit | Inhalt | Überschneidung mit uns |
|---|---|---|
| f1cb49b | Label-Icon behält volle Größe, Text passt sich der Restbreite an; Rebuild mit neuem Label-Text baut neu | p181 (R19), Label-Layout (R14, R19) |
| 27264a7 | neue Label-Icons: Schrauben (Button head Phillips, self-tapping …), Hex-Kontermutter | keine (neue Dateien) |
| 4ae7afb | „Gridfinity clone“ im Kontextmenü | Clone im Settings-Fenster (R18), Texte „bin, baseplate or label“ |
| 09fd6b6, 74e7751, fba170e | Versions-Bumps im Manifest (bis 2.4.2.0) | unsere Version 2.4.0.0 |

## Plan (zur Freigabe)

Ein Merge-Commit `git merge upstream/master`, kein Rebase, kein Cherry-Pick. Die Urheberschaft der sechs Commits bleibt
so erhalten. Ein Probelauf mit `--no-commit` hat genau drei Konfliktdateien gezeigt; der Merge ist danach wieder
abgebrochen. Vorgehen je Stelle:

1. **`commandShowSettings/entry.py` (1 Konflikt): beides übernehmen.**
   - Upstreams Kontextmenü-Eintrag „Gridfinity clone“ kommt dazu, neben unserem Clone-Knopf im Settings-Fenster.
     Doppelt ist das nicht: Das eine ist ein Menüeintrag, das andere ein Knopf in einem Fenster, beide rufen dasselbe
     `startWithConfig` auf.
   - Weil unser `CLONE_COMMANDS` seit R18 auch Labels kennt, gilt der Menüeintrag dann auch für Einleger. Die Texte
     werden auf „bin, baseplate or label“ angeglichen, wie bei Rebuild.
2. **`binBuilder.parameterEdits` (2 Konflikte): unsere Fassung behalten.** Die beiden Lösungen sind doppelt: Upstream
   baut bei jeder Änderung von `labelText` neu, wir seit R19 bei einem Text, der vom gebauten abweicht
   (`textChangedSinceBuild`, auch für Fach-Labels, mit `sharedText`). Unsere Fassung deckt Upstreams Fall ab
   (geänderter Text → Neubau) und zusätzlich den Text, der vorher über den Parameter geändert wurde, sowie die
   Fach-Labels. Upstreams Zweig im Loop würde damit nie erreicht; er entfällt, der Docstring wird zusammengeführt.
3. **`labelGenerator.createLabel` (4 Konflikte): Rückfrage, siehe unten.** Upstream ändert die Regel des Bin-Labels: Das
   Icon behält seine volle Größe (so hoch, wie die Buchstaben höchstens sein dürfen), nur der Text schrumpft auf die
   Restbreite. Bei uns schrumpfen Icon und Text gemeinsam. Unser Code ist seit R14 ein anderer: Er zeichnet am fertigen
   Ort statt zu verschieben, setzt Text auf eine Grundlinie und hält das Icon über Maße. Die Hunks lassen sich deshalb
   nicht übernehmen, nur die Regel ließe sich in unserem Code nachbauen.
4. **Neue Icons (27264a7): übernehmen.** Das sind neue Dateien ohne Konflikt. Die Vorschauen kommen von Upstream.
5. **Manifest: unsere Version bleibt** (2.4.0.0, die Gridkeeper-Zählung kommt später). Upstreams 2.4.2.0 steht nur als
   Notiz hier.
6. **README und Screenshots von 4ae7afb übernehmen, wie sie sind.** README-Änderungen ohne Konflikt.

## Rückfrage (Hauptsitzung / Jörg)

**Bin-Label-Icon: Upstreams Regel „Icon volle Größe, nur Text schrumpft“ übernehmen?**
- **A, übernehmen (Empfehlung):**
  - In unserem `createLabel` wird `iconSize` nicht mehr an die Buchstaben gekoppelt. Die Breitenskala für den Text
    rechnet mit `contentWidth − Iconbreite − Abstand`. Die Untergrenze und die Ablehnung aus R19 bleiben.
  - Folge: Lange Texte mit Icon werden eher abgelehnt, weil das große Icon Platz nimmt. Die Buchstaben stehen dann an
    der Unterkante des Icons. Die Snapshots der Bins mit Icon und Text ändern sich gewollt und werden mit belegter
    Ursache neu abgelegt.
  - Vorteil: Wir bleiben nah am Original, spätere Merges werden leichter, und das Icon bleibt lesbar.
- **B, unsere Regel behalten:** Icon und Text schrumpfen gemeinsam, wie getestet. Upstreams Teil von f1cb49b entfällt mit
  Begründung, der Rest wird übernommen.

## Danach

- pytest, Review (Opus) mit Blick auf die Konfliktstellen, CHANGELOG-Abschnitt „Merged from upstream“ mit Credits an
  Le0Michine.
- Fusion, nur betroffene Fälle (Jörgs Wunsch): Reload; Snapshots der Bin-Fälle mit Label-Icon
  (`bin_2x1x3_label_icon_text_embossed`, `…_colored`) und eine Probe der neuen Icons (Hex-Kontermutter, eine neue
  Schraube) auf einem Bin-Label; Rebuild mit geändertem Text (E2E R19 a, e, f).
- **Handtests für die Desktop-Steuerung:**
  1. Rechtsklick auf eine Bin › „Gridfinity clone“: Der Bin-Dialog öffnet sich mit ihren Werten. Das Menü hat genau
     einen Clone-Eintrag.
  2. Dasselbe für eine Grundplatte und einen Einleger.
  3. Bin-Dialog › Label icon: „Hex locknut“ und die neuen Schrauben stehen in der Liste und haben Vorschaubilder.
  4. Rechtsklick › „Gridfinity settings“: Der Clone-Knopf im Fenster funktioniert weiter.

## Umsetzung

Merge-Commit 1e5d9e4 (`git merge upstream/master`). Die sechs Commits von Lev Mishin bleiben mit Urheber erhalten.
- **1 (Kontextmenü Clone):** übernommen, Texte auf „bin, baseplate or label“.
- **2 (`parameterEdits`):** unsere Fassung.
- **3 (`createLabel`):** vorerst unsere Fassung, Stelle im Code mit „OPEN (round 22, p13)“ markiert. Entscheidung A/B
  steht aus (Hauptsitzung fragt Jörg).
- **4 (Icons):** übernommen.
- **5 (Manifest):** Git hatte es ohne Konflikt auf 2.4.2.0 gemergt, zurück auf 2.4.0.0.
- **6 (README, Screenshots, `tools/labelIcons.py`):** übernommen.
- pytest: `920 passed`.

## Punkt 3 entschieden: Variante A (Jörg: „Wie das Original“)

- Upstreams Regel ist in unserem Code nachgebaut, die Hunks selbst passten nicht.
  - `binLabelLayout.fitBinLabel`: Das Icon behält seine volle Größe (so hoch, wie die Buchstaben höchstens sein dürfen),
    begrenzt nur durch die Label-Breite. Der Text schrumpft auf die Restbreite nach Icon und Abstand.
  - Untergrenze und Ablehnung aus R19 bleiben.
  - `binLabelPlacement`: Ist das Icon höher als die Buchstaben, sitzt es in der Mitte, und die Buchstaben stehen auf
    seiner Unterkante. Upstream richtet die Unterkante der Buchstaben am Icon aus, wir die Grundlinie, wie seit R14;
    Unterlängen reichen damit unter die Icon-Unterkante.
- Tests in `tests/test_bin_label_layout.py`, alle mit Unit-Tests. Die OPEN-Markierung ist entfernt.
- Erwartet ändern sich die Snapshots der Bins mit Icon und Text (`bin_2x1x3_label_icon_text_embossed`, `…_colored`).
