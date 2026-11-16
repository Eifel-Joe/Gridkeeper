# Runde 22 – Übergabe: Commits des Originals übernehmen (p13)

Stand 2026-11-16. Branch `runde-22` von `master` (4da7731). Nutzer: „Auch die neuen Commits von Upstream übernehmen.“
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
   Fach-Labels. Upstreams Zweig im Loop entfällt; unser Docstring bleibt, er nennt den Grund schon.
3. **`labelGenerator.createLabel` (4 Konflikte): Rückfrage, siehe unten.** Upstream ändert die Regel des Bin-Labels: Das
   Icon behält seine volle Größe (so hoch, wie die Buchstaben höchstens sein dürfen), nur der Text schrumpft auf die
   Restbreite. Bei uns schrumpfen Icon und Text gemeinsam. Unser Code ist seit R14 ein anderer: Er zeichnet am fertigen
   Ort statt zu verschieben, setzt Text auf eine Grundlinie und hält das Icon über Maße. Die Hunks lassen sich deshalb
   nicht übernehmen, nur die Regel ließe sich in unserem Code nachbauen.
4. **Neue Icons (27264a7): übernehmen.** Das sind neue Dateien ohne Konflikt. Die Vorschauen kommen von Upstream.
5. **Manifest: unsere Version bleibt** (2.4.0.0, die Gridkeeper-Zählung kommt später). Upstreams 2.4.2.0 steht nur als
   Notiz hier.
6. **README und Screenshots von 4ae7afb übernehmen, wie sie sind.** README-Änderungen ohne Konflikt.

## Rückfrage (Hauptsitzung / Nutzer)

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
- Fusion, nur betroffene Fälle (des Nutzers Wunsch): Reload; Snapshots der Bin-Fälle mit Label-Icon
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
  steht aus (Hauptsitzung fragt Nutzer).
- **4 (Icons):** übernommen.
- **5 (Manifest):** Git hatte es ohne Konflikt auf 2.4.2.0 gemergt, zurück auf 2.4.0.0.
- **6 (README, Screenshots, `tools/labelIcons.py`):** übernommen.
- pytest: `920 passed`.

## Punkt 3 entschieden: Variante A (Nutzer: „Wie das Original“)

- Upstreams Regel ist in unserem Code nachgebaut, die Hunks selbst passten nicht.
  - `binLabelLayout.fitBinLabel`: Das Icon behält seine volle Größe (so hoch, wie die Buchstaben höchstens sein dürfen),
    begrenzt nur durch die Label-Breite. Der Text schrumpft auf die Restbreite nach Icon und Abstand.
  - Untergrenze und Ablehnung aus R19 bleiben.
  - `binLabelPlacement`: Ist das Icon höher als die Buchstaben, sitzt es in der Mitte, und die Buchstaben stehen auf
    seiner Unterkante. Upstream richtet die Unterkante der Buchstaben am Icon aus, wir die Grundlinie, wie seit R14;
    Unterlängen reichen damit unter die Icon-Unterkante.
- Tests in `tests/test_bin_label_layout.py`, alle mit Unit-Tests. Die OPEN-Markierung ist entfernt.
- Erwartet ändern sich die Snapshots der Bins mit Icon und Text (`bin_2x1x3_label_icon_text_embossed`, `…_colored`).

## Review (Opus) des Merges

Kein kritischer Fund. Umgang:
- **(I1) erledigt:** Der Arbeitsstand war beim Review noch nicht committet und rot. Er ist in bff0966 fertig und grün.
- **(M1) behoben:** Neu ist `tests/test_context_menu_commands.py`. Er prüft im Quelltext:
  - Clone und Rebuild kennen Bin, Grundplatte und Einleger;
  - `stop()` löscht alle drei Befehle;
  - Clone braucht die Config im Tag;
  - ein Clone-Eintrag im Menü.
- **(M2) behoben:** Das CHANGELOG nennt alle elf neuen Icons.
- **(M3) Notiz für Handtest 3:** „Hex locknut“ (Upstream) und „Cullenect nut nylon“ (unser) zeigen dasselbe Teil.
  Beide bleiben in der Liste.
- **(M4) behoben:** Satz zu `parameterEdits` korrigiert. Die README des Originals nennt beim Kontextmenü nur Bin und
  Grundplatte; sie bleibt wie übernommen.

## Belege

- pytest: `930 passed`.
- Fusion auf 1f9e0b4 (`r22_reload1`):
  - `r22_snap_t`: alle vier Bin-Label-Fälle pass, auch die zwei mit Icon. Bei ihrem kurzen Text („Bolts“) ist das Icon
    schon voll groß, nichts neu abgelegt.
  - `r22_icons`: alle vier neuen Icons gebaut, Timeline gesund. Bauzeiten der Bin mit Label: Hex locknut 5,8 s, Button
    head phillips 8,3 s, Button head phillips self tapping 12,2 s, Button head self tapping 19,2 s.
    - Die selbstschneidenden Schrauben sind langsam, wie die Cullenect-Hardware vor p51: Ihre SVGs haben viele Punkte.
    - Neuer Punkt für die Liste: die Upstream-Icons ebenfalls gröber machen (nicht in dieser Runde).
  - E2E R14 d: ALL OK.
  - E2E R14 e: Fehler an den Testdaten, nicht am Code. „Cullenect tnut 2“ hat seit den gröberen Symbolen (R17) 26
    Punkte und wird über Maße gehalten statt verschoben. Gruppe e und g nehmen jetzt „Cullenect magnet“ (50 Punkte,
    verschoben).
  - E2E R19 a, e und f: ALL OK.
  - E2E R14 e und g mit „Cullenect magnet“: ALL OK.

## p250 „Neue Schrauben-Icons des Originals bauen langsam (bis 19 s)“: erledigt ohne Codeänderung

- Messung `r22_icon_dims` (alle 12 neuen Icons, je eine Bin 2x1x3 mit Label, Grenze für das Halten über Maße
  unverändert):

| Icons | Punkte | Weg | Bin gebaut |
|---|---|---|---|
| hex-locknut, countersunk-slotted, grub-screw | 18 | über Maße | 4,7–5,4 s |
| countersunk-self-tapping, countersunk-screw | 19–20 | über Maße | 4,8–4,9 s |
| countersunk-phillips(-self-tapping) | 25–26 | über Maße | 5,1–5,3 s |
| button-head-slotted, button-head-self-tapping | 39–40 | über Maße | 6,1–6,5 s |
| button-head, button-head-phillips(-self-tapping) | 41–47 | verschoben (0,72–0,78 s) | 4,6 s |

- Eine Bin ohne Label braucht rund 4,5 s. Das Icon kostet also höchstens etwa 2 s, bei 39–40 Punkten über Maße;
  das ist die Grenze aus p180.
- Die 12,2 s und 19,2 s aus `r22_icons` ließen sich nicht wiederholen. Sie stammen aus dem ersten Lauf nach dem
  Reload. Vermutlich hat Fusion die SVGs und Schriften dort zum ersten Mal geladen.
- Die Zeichnungen sind schon schlank (18–47 Punkte, 2 Bögen). Gröber zeichnen brächte nichts, eine Codeänderung ist
  nicht nötig.
- Nebenbei: Der Zeitstempel für den Weg „über Maße“ blieb in diesem Auftrag leer, die Bin-Zeiten zeigen den Aufwand.
