# Trennwände bis oben (auf Rasterlinien) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Haken im Bin-Dialog, mit dem Trennwände, die genau auf einer Rasterlinie liegen, bis zur Oberkante gehen und dort im Profil des Stapelrands auslaufen (p17).

**Architecture:** Eine reine Funktion bestimmt aus dem Fach-Layout die Trennwand-Abschnitte auf Rasterlinien
(`lib/gridfinityUtils/raisedDividers.py`, ohne `adsk`, per pytest getestet). Der Bin-Builder reicht sie an den
Körper-Generator; der baut je Abschnitt einen Quader über der Trennwand von unter der „Compartments top clearance“
bis zur Stapelrand-Oberkante, schneidet ihn mit denselben Fuß-Körpern, mit denen „lip notches“ in den Stapelrand
geschnitten werden (Fußgitter + Spiel), und vereint ihn mit dem Bin. Das Profil passt so per Konstruktion zu den
Füßen einer darauf gestapelten Bin, auch wenn die Trennwand leicht neben der Rasterlinie liegt (Teilung über mehrere
Einheiten ist um bis zu (Wand/2 + Spiel) versetzt).

**Tech Stack:** Python, Fusion 360 API, pytest mit `tests/stubs`.

**Spec:** `docs/specs/2026-11-14-trennwaende-bis-oben-design.md`

## Global Constraints

- Standard **aus**; ohne Haken ändert sich nichts (alle bestehenden Snapshot-Fälle unverändert; 4 Text-Label-Fälle sind vorher schon rot, p30).
- Trennwände neben dem Raster bleiben auch mit Haken unten.
- Rasterlinie = Vielfaches einer **ganzen** Rastereinheit (gfBaseWidth/gfBaseLength), auch bei Half-Grid-Bins.
- Jede neue Skizze vollständig bestimmt; Maße als `Dim`, damit Parameteränderungen (`gfBaseWidth` …) mitgehen.
- Längen intern in cm, Testfälle in mm.
- Wirkt nur bei Hollow-Bins mit Stapelrand, ohne eigene Form (sonst gibt es keine Trennwände bzw. keinen Rand).

## Review Focus

- Zusammengefasste Zellen über eine Rasterlinie: dort ist keine Trennwand, also auch kein Hochziehen (Test `test_merged_cells_have_no_divider_on_their_inner_line`).
- Ungleiche Teilung (3 Fächer auf 4 Einheiten) und Half-Grid-Fächer: nur echte Rasterlinien (Tests `test_three_on_four_units_has_none`, `test_half_cells_rise_only_on_whole_lines`).
- Bins mit halber Einheit (2,5 Einheiten, 5 Fächer): Linien bei 1 und 2 Einheiten (Test `test_half_unit_bin_width`).
- Haken an, aber kein Stapelrand / Solid / Shelled / eigene Form: keine Wirkung, kein Fehler (Test `test_disabled_without_lip_or_hollow_body`).
- Trennwand-Abschnitte an Kreuzungen und Außenwänden: Quader um eine Wandstärke verlängert, damit keine Lücke bleibt; geprüft im Snapshot-Fall und Stapeltest.

---

### Task 1: Abschnitte auf Rasterlinien bestimmen

**Files:**
- Create: `lib/gridfinityUtils/raisedDividers.py`
- Test: `tests/test_raised_dividers.py`

**Interfaces:**
- Produces:
  - `DividerSegment` (frozen dataclass): `axis: str` (`'x'` = Wand quer zu X, also an einer X-Teilungslinie; `'y'` = an einer Y-Linie), `line: int` (Teilungslinie im Fach-Raster, 1 … count-1), `start: int`, `end: int` (Fach-Raster-Zellen entlang der Wand, end exklusiv).
  - `gridLineSegments(pockets: list[dict], columns: int, rows: int, binWidth: float, binLength: float) -> list[DividerSegment]` — pockets wie `compartmentLayout.normalizePockets` (dicts mit x, y, width, length), binWidth/binLength in ganzen Rastereinheiten (darf auf .5 enden). Linie k ist Rasterlinie, wenn `k * binWidth / columns` ganzzahlig ist (Toleranz 1e-6). Abschnitt = maximaler Lauf von Zellen, an denen links/rechts (bzw. vorn/hinten) verschiedene Pockets liegen. Sortiert: erst `'x'`, dann `'y'`, dann line, start.
  - `segmentsForBin(isEnabled: bool, hasLip: bool, isHollow: bool, isShaped: bool, pockets, columns, rows, binWidth, binLength) -> list[DividerSegment]` — leere Liste, wenn eine Bedingung fehlt.

- [x] Step 1: Tests schreiben: `test_uniform_4x2_rises_everywhere` (pockets 4×2 Einzelzellen, binWidth 4, binLength 2 → x-Linien 1,2,3 je 0–2, y-Linie 1 von 0–4), `test_three_on_four_units_has_none`, `test_half_cells_rise_only_on_whole_lines` (8×2 Fächer auf 4×2 → x-Linien 2,4,6), `test_merged_cells_have_no_divider_on_their_inner_line` (des Nutzers 4x2: vorn 4×1, hinten 2×1 + 1×1 + 1×1 → `x` Linie 2 [1,2), Linie 3 [1,2), `y` Linie 1 [0,4)), `test_half_unit_bin_width` (5 Fächer, binWidth 2.5 → x-Linien 2, 4), `test_single_compartment_has_none`, `test_disabled_without_lip_or_hollow_body`.
- [x] Step 2: `python -m pytest tests/test_raised_dividers.py -q` → FAIL (Modul fehlt).
- [x] Step 3: Implementieren.
- [x] Step 4: Test → PASS; volle Suite grün.
- [x] Step 5: Commit.

### Task 2: Option durchreichen (InputState, Fälle, Dialog)

**Files:**
- Modify: `commands/commandCreateBin/inputState.py` (Feld `hasDividersToTop: bool` nach `hasLipNotches`)
- Modify: alle `tests/e2e/cases/bin_*.json` und `tools/screenshots/models/_bin.json` (`"hasDividersToTop": false`)
- Modify: `commands/commandCreateBin/entry.py` (ID `BIN_DIVIDERS_TO_TOP_INPUT_ID = 'dividers_to_top'`, `initValue` False, Checkbox „Dividers up to the top on grid lines“ nach „Generate lip notches“ mit Tooltip, aktiv nur mit Body + Lip + Hollow + ohne eigene Form, `getInputsState`)
- Modify: `lib/gridfinityUtils/binBodyGeneratorInput.py` (`raisedDividers: list = []`)
- Modify: `commands/commandCreateBin/binBuilder.py` (`binBodyInput.raisedDividers = raisedDividers.segmentsForBin(...)` mit den normalisierten pockets, `compartmentsX/Y`, `state.binWidth/binLength`)
- Test: `tests/test_test_cases.py`

- [x] Step 1: Test `test_dividers_to_top_defaults_off_in_every_bin_case` (jeder Bin-Fall außer `*_dividers_to_top*` hat `hasDividersToTop == False`).
- [x] Step 2: → FAIL (Feld unbekannt).
- [x] Step 3: Feld, Fälle, Dialog, Builder.
- [x] Step 4: volle Suite grün.
- [x] Step 5: Commit.

### Task 3: Geometrie der hochgezogenen Trennwände

**Files:**
- Modify: `lib/gridfinityUtils/binBodyGenerator.py` (neue Funktion `createRaisedDividers(input, compartmentPlacementDims, binBodyTotalHeight, targetComponent) -> adsk.fusion.BRepBody | None`, Aufruf im `not input.isSolid`-Zweig, Ergebnis in `bodiesToMerge`)
- Modify: `lib/gridfinityUtils/binBodyLipGenerator.py` (Fuß-Schnittkörper der lip notches als Funktion `createStackedFootCutters(input: BinBodyLipGeneratorInput, targetComponent, name) -> list[BRepBody]` herauslösen, Notches nutzen sie unverändert)

Geometrie je Abschnitt (Dims aus `compartmentWidthUnit`, `compartmentLengthUnit`, `wall`):
- quer: Wand zwischen Fach-Spalte line-1 und line: `x0 = compartmentsMinX + (unitX + wall) * line - wall`, Breite `wall`.
- längs: von `cavityStart(start) - wall` bis `cavityEnd(end-1) + wall` (deckt Kreuzungen und Außenwand ab).
- z: von `binBodyTotalHeight - BIN_TAB_TOP_CLEARANCE` bis `binBodyTotalHeight + BIN_LIP_EXTRA_HEIGHT - BIN_LIP_TOP_RECESS_HEIGHT`.
- Alle Quader per `extrudeUtils.createBoxAtPoint(..., originX=, originY=, originZ=)` (Skizzen bestimmt), zu einem Körper vereint, mit `createStackedFootCutters` geschnitten.

- [x] Step 1: Prüfkriterium vorab (kein Unit-Test möglich, Fusion-Geometrie): neuer Snapshot-Fall aus Task 4 baut fehlerfrei, Constraint-Check streng ohne Befund, Timeline gesund; Höhe der Trennwand-Spitze = Stapelrand-Oberkante; bestehender Fall `bin_4x2x3_cullenect_mixed` pass.
- [x] Step 2: Implementieren, volle Suite grün, Add-in neu laden, Kriterium prüfen.
- [x] Step 3: Commit.

### Task 4: Snapshot-Fall, Stapeltest

**Files:**
- Create: `tests/e2e/cases/bin_4x2x3_cullenect_mixed_dividers_to_top.json` (Kopie von `bin_4x2x3_cullenect_mixed` mit Haken)
- Create: `tests/e2e/cases/bin_4x2x3_dividers_to_top_3x2_params_base_40.json` (3x2 Fächer ohne Laschen, `gfBaseWidth` → 40 mm; mit Cullenect-Laschen scheitert der Parametervergleich auch ohne Haken, p60)
- Create: `tests/e2e/snapshots/<beide>/` (aufgenommen in Fusion)

- [x] Step 1: Fälle anlegen, `python -m pytest` grün (Fälle laden).
- [x] Step 2: In Fusion (neues Dokument) beide Fälle laufen lassen und aufnehmen; Bestandsfälle laufen: nur p30-Fälle rot.
- [x] Step 3: Stapeltest: 4x2x3-Bin ohne Fächer in dasselbe Dokument, um die Bin-Höhe nach oben versetzt; Interferenz-Analyse → keine Überschneidung. Gegenprobe: Quader ungeschnitten → Interferenz vorhanden.
- [x] Step 4: Commit (Fälle + Snapshots + README).

### Task 5: Abschluss

- [x] `CHANGELOG-CULLENECT.md` unter „Unreleased“, Credits.
- [x] Opus-Review des Branch-Diffs, Funde abarbeiten.
- [x] Add-in neu laden, Übergabe-Notiz, Meldung an die Hauptsitzung.
