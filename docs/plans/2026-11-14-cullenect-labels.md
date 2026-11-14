# Cullenect-Labels — Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bin-Laschen bekommen den Label-Stil „Cullenect“ (Klick-Tasche), ein neuer Befehl „Gridfinity Label“ erzeugt die passenden Einleger mit Text und Cullenect-Symbolen.

**Architecture:** Reine Rechenlogik (Maße, Katalog, Layout) in Fusion-freien Modulen mit pytest-Tests; Fusion-Geometrie in Generator-Modulen nach dem Muster von `labelGenerator.createLabel` (Skizzen auf einer Ebene in aktueller Höhe, Parameteränderungen nur über ein Verschieben-Feature bzw. Ausdrücke auf `gfBaseWidth`). Symbole werden einmalig mit OpenSCAD aus Cullenects eigenem Code als SVG gerendert und eingecheckt.

**Tech Stack:** Python 3.14 in Fusion, Tests auf 3.13 und 3.14 (Fusion-API `adsk`), pytest mit Stubs in `tests/stubs`, Fusion-Snapshot-Tests (`tests/e2e`), OpenSCAD (`C:\Program Files\OpenSCAD`) nur für das Symbol-Werkzeug.

**Spec:** `docs/specs/2026-11-14-cullenect-labels-design.md` (freigegeben). Bei Widerspruch gilt die Spec; Maße aus `Cullenect.scad` (CullenJWebb/Cullenect-Labels, Commit `d6dc0bb2a6491f53c27e5f9db2dfc38ebb07f8db`, MIT).

## Global Constraints

- Längen im Code intern in cm, Testfälle (JSON) in mm, Winkel intern in rad.
- Jede neu angelegte Skizze ist `isFullyConstrained` (Anti-Ziel der Spec).
- Bestehendes Verhalten unverändert: Outline/Engraved/Embossed, Defaults, alle vorhandenen Snapshot-Fälle bleiben grün.
- Neues Feld in `commands/commandCreateBin/inputState.py` ⇒ alle `tests/e2e/cases/bin_*.json` ergänzen (`stateFromJson` ist strikt) und `tests/e2e/README.md` mit `tests/e2e/write_readme.py` neu schreiben.
- Code-Stil, Namen (camelCase, englische Bezeichner/Kommentare) und Teststil (Module per `importlib` laden) wie im Bestand — upstream-tauglich.
- Cullenect-Maße (`Cullenect.scad`, verifiziert 2026-11-14): Einleger Breite `42·n − 6` mm (+ `offset_xy`), Höhe 11 mm, Dicke 1,2 mm, Ecken r 0,5 mm; Schichten 0–0,2 voll, 0,2–0,8 um 0,2 eingezogen, 0,8–1,2 voll. Tasche `socket_offset` 0,3 mm größer in X und Y, Ecken r 0,5, Tiefe 1,2 mm; zwei Rippen über die volle Taschenlänge, 0,2 mm (Y) × 0,4 mm (Z), Unterkante 0,2 mm über Taschenboden, an beiden Längsseiten. Text/Symbol eine Schicht 0,2 mm.
- Credits bei übernommenem Code/Daten: Le0Michine (CC BY-NC-SA 4.0), CullenJWebb (MIT), ostat / Chris Heazlewood (Referenz), Zack Freedman.
- Commits: einer pro grünem Task, Message nennt Was und Warum, Attribution-Zeile `Co-Authored-By: Claude …`.

## Festlegungen dieses Plans (Builder-Calls der Spec)

| Punkt | Festlegung | Begründung |
|---|---|---|
| Randmaß Tasche | `CULLENECT_POCKET_MARGIN = 0.1` (1,0 mm) je Seite, in X und Y | 1U-Lasche hat 39,1 mm nutzbar (42 − 2·0,25 Spiel − 2·1,2 Wand) ⇒ Rand max. 1,4 mm; 2,65 mm (Gridfinity Extended) passt nicht. 1,0 mm lässt Luft für dickere Wände bis 1,4 mm. |
| Taschenbreite | Größtes Cullenect-Standardmaß `gfBaseWidth·n − 6 mm + 0,3 mm` in Schritten n = 0,5, das mit Rand in die verfügbare Laschenlänge passt | Auch Fach-Laschen bekommen Standardbreiten ⇒ Original-Einleger passen überall. 4x2-Bin, 1x1-Fach (40,375 mm): 1U = 36,3 + 2,0 ≤ 40,375 ✓; Fach über 2 Zellen (81,95 mm): 2U ✓; über 4 Zellen (165,1 mm): 4U ✓ (jeweils mit `tabLength` ≥ Fachbreite). **Entschieden, siehe unten.** |
| Laschenbreite | `max(Nutzerwert, 14 mm, 11,3 + 2·Vorderrand)`; der Nutzerwert im Dialog wird nicht überschrieben | Spec-Vorgabe 14 mm; Formel deckt steile Unterschneidungen ab. |
| Lage in Y | mittig auf der Laschen-Oberseite, aber Vorderrand ≥ `socketFrontInset` | Unter der Tasche bleibt bei 45°-Unterschneidung genug Material (Taschenboden + 0,4 mm Haut, `BIN_TAB_HOLLOW_MIN_SKIN`). |
| Geneigte Laschen-Oberseite | bei Cullenect gesperrt (Winkel 0, Eingabe deaktiviert) | Tasche braucht ebene Auflage. |
| Hohle Lasche | Deckenstärke `max(Wand, 1,2 + 0,4 mm)` | wie Engraved, nur mit Taschentiefe. |
| Breite des Einlegers nachträglich | User-Parameter in mm | eine Zahl, die der Nutzer direkt mit der Taschenanzeige vergleicht. |
| Korrekturwert `offset_xy` | zwei Felder `offsetX`, `offsetY` (Default 0), wirken wie in Cullenect auf Breite und Höhe des Einlegers | Cullenect hat ein Paar `[x, y]` (`labelY = 11 + offset_xy.y`). |
| Laschenlänge bei Fächern | unverändert `tabLength` des Nutzers; Fach-Laschen werden nicht automatisch aufs Fach verlängert | Bestandsverhalten; wer eine 2U-/4U-Tasche im Fach will, setzt `tabLength` entsprechend. Default `tabLength` = 1 ⇒ jedes Fach bekommt 1U. |
| Schaft „keiner“, Gewinde „keins“ | nicht angeboten | Spec listet nur Maschine/Holz und voll/teil; Cullenect kennt zusätzlich `none`. |
| Lage des Symbols | aus den SVG-Abmessungen: senkrecht mittig; Schraube mit rechter Kante bündig am Einleger-Rand (wie Cullenect, Kopf bei `labelX − driverX/2` ± 3 mm), Hardware mit rechter Kante bei `Breite − max(0, (Höhe − Symbolhöhe)/2)` (Cullenect `marginRight`) | neue SVGs brauchen so keine Katalog-Einträge. Abweichung: Schraube ohne Kopf liegt mit dem Schaft am Rand, bei Cullenect bliebe dort der Platz des Kopfes leer. |
| `offsetX`/`offsetY` bei freier mm-Breite | wirkt auch dort | Korrekturwert für Druckerabweichung (Spec), soll unabhängig von der Breitenangabe gelten; Cullenect ignoriert ihn bei `labelXmm`. |
| Schraube und Hardware zugleich (Runde 4) | nein: Schraube an ⇒ Hardware gesperrt | Cullenect zeichnet beide an dieselbe Stelle rechts, sie würden sich überlagern. |
| Text bei nachträglich kleinerer Breite (Runde 4) | Text bleibt, wie er gebaut wurde; das Symbol wandert mit | Text ist explodiert (Spike Task 8) und kann nicht neu umbrechen; wer die Breite deutlich verkleinert, erzeugt den Einleger neu. |
| Text-/Symbol-Körper (Runde 4) | ein Körper je Buchstabe bzw. Symbolteil (`… text N`, `… symbol N`) | Fusion vereint sich nicht berührende Körper nicht (Kombinieren und Extrusion „Verbinden“ geprüft). |
| Korrekturwerte (Runde 4) | höchstens ±1 mm | darüber ist es kein Druckerausgleich mehr; −10 mm Höhe würde die Ecken-Verrundung brechen. |

## Review Focus

1. **Dicke Wände oder kurze Laschen-Länge:** Bei 3 mm Wand hat eine 1x1-Bin nur 35,5 mm ⇒ Tasche fällt auf 0,5U (15,3 mm). Erwartet: Dialog zeigt das an; passt nicht einmal 0,5U, wird keine Tasche gebaut und der Dialog sagt es (Test in Task 1 und 4).
2. **`gfBaseWidth` nach dem Bauen geändert:** Tasche muss mit der Lasche schrumpfen/wachsen und mittig bleiben (e2e-Fall mit `parameters` in Task 5).
3. **Zurückschalten von Cullenect auf Outline:** Text, Symbol, Neigung und Laschenbreite des Nutzers sind wieder da, nichts wurde überschrieben (Test in Task 4).
4. **Alte gespeicherte Dialog-Defaults ohne das neue Feld:** Dialog öffnet mit Default 0,3 mm statt abzustürzen (Test in Task 4).
5. **Einleger extrem schmal/breit oder ohne Text und Symbol:** Label-Befehl verweigert < 10 mm und > 300 mm, ein leerer Einleger ist erlaubt (nur Grundkörper, kein Text/Symbol-Körper) (Tests in Task 9 und 10).

---

# Runde 2 — Bin: Tasche, Breitenanzeige, Constraint-Check

### Task 1: Cullenect-Maße als reine Logik

**Files:**
- Modify: `lib/gridfinityUtils/const.py` (Konstanten anhängen)
- Create: `lib/gridfinityUtils/cullenect.py` (nur `math` und `const`, kein `adsk`)
- Test: `tests/test_cullenect.py`

**Interfaces:**
- Produces (const, cm): `CULLENECT_LABEL_HEIGHT = 1.1`, `CULLENECT_LABEL_THICKNESS = 0.12`, `CULLENECT_WIDTH_REDUCTION = 0.6`, `CULLENECT_SOCKET_OFFSET = 0.03`, `CULLENECT_LATCH_INSET = 0.02`, `CULLENECT_LATCH_BOTTOM = 0.02`, `CULLENECT_LATCH_HEIGHT = 0.06`, `CULLENECT_RIB_WIDTH = 0.02`, `CULLENECT_RIB_HEIGHT = 0.04`, `CULLENECT_RIB_BOTTOM = 0.02`, `CULLENECT_CORNER_RADIUS = 0.05`, `CULLENECT_LAYER = 0.02`, `CULLENECT_POCKET_MARGIN = 0.1`, `CULLENECT_MIN_TAB_WIDTH = 1.4`, `CULLENECT_UNIT_STEP = 0.5`.
- Produces (`cullenect.py`):
  - `labelWidth(units: float, baseWidth: float = 4.2, offsetX: float = 0) -> float`
  - `socketWidth(units: float, baseWidth: float, socketOffset: float) -> float`
  - `socketHeight(socketOffset: float) -> float`
  - `socketUnits(availableLength: float, baseWidth: float, socketOffset: float, margin: float = const.CULLENECT_POCKET_MARGIN) -> float | None`
  - `socketFrontInset(overhangAngle: float, filletAllowance: float) -> float` — `max(margin, (CULLENECT_LABEL_THICKNESS + BIN_TAB_HOLLOW_MIN_SKIN)·tan(a) − filletAllowance)`; Aufrufer übergibt `binBodyTabGenerator.tabFilletAllowance(a, 0)`.
  - `effectiveTabWidth(userTabWidth: float, overhangAngle: float, filletAllowance: float, socketOffset: float) -> float`
  - `tabSpanInCompartment(compartmentWidth: float, tabStart: float, tabLength: float) -> float` — Länge der Lasche innerhalb des Fachs (Lasche wird aufs Fach getrimmt).
  - `describeSocket(units: float | None, baseWidth: float, socketOffset: float) -> str` — z. B. `"1U: pocket 36.3 mm, insert 36 mm"`, bei `None` `"too short for a Cullenect pocket"`; Zahlen auf 0,01 mm gerundet und mit `:g` formatiert (kein `36.300000000000004`).

- [ ] **Step 1: Failing tests schreiben** (`tests/test_cullenect.py`, Modul per `importlib` laden wie `tests/test_compartment_layout.py`)

```python
def test_label_width_follows_cullenect():
    assert cullenect.labelWidth(1) == approx(3.6)
    assert cullenect.labelWidth(2) == approx(7.8)
    assert cullenect.labelWidth(1, 4.0, 0.01) == approx(3.41)

def test_socket_is_label_plus_offset():
    assert cullenect.socketWidth(1, 4.2, 0.03) == approx(3.63)
    assert cullenect.socketHeight(0.03) == approx(1.13)

@pytest.mark.parametrize("available, units", [
    (3.91, 1.0),     # 1x1 bin, 1.2 mm walls
    (4.0375, 1.0),   # 1x1 compartment of a 4x2 bin
    (8.195, 2.0),    # compartment over 2 cells of a 4x2 bin
    (16.51, 4.0),    # compartment over 4 cells
    (3.55, 0.5),     # 1x1 bin with 3 mm walls
    (1.5, None),     # not even half a unit
])
def test_socket_units_take_the_widest_standard_label_that_fits(available, units):
    assert cullenect.socketUnits(available, 4.2, 0.03) == units

def test_front_inset_keeps_the_margin_at_45_degrees():
    allowance = 0.06 / math.tan(math.radians(45) / 2)
    assert cullenect.socketFrontInset(math.radians(45), allowance) == approx(0.1)

def test_steep_overhang_pushes_the_socket_back_and_widens_the_tab():
    allowance = 0.06 / math.tan(math.radians(10) / 2)
    inset = cullenect.socketFrontInset(math.radians(80), allowance)
    assert inset == approx(0.16 * math.tan(math.radians(80)) - allowance)
    assert cullenect.effectiveTabWidth(1.3, math.radians(80), allowance, 0.03) == approx(1.13 + 2 * inset)

def test_tab_width_is_raised_to_14_mm_but_wider_user_tabs_stay():
    a = math.radians(45); allowance = 0.06 / math.tan(a / 2)
    assert cullenect.effectiveTabWidth(1.3, a, allowance, 0.03) == approx(1.4)
    assert cullenect.effectiveTabWidth(1.8, a, allowance, 0.03) == approx(1.8)

def test_tab_span_is_trimmed_to_the_compartment():
    assert cullenect.tabSpanInCompartment(4.0375, 0, 16.8) == approx(4.0375)
    assert cullenect.tabSpanInCompartment(8.195, 4.2, 4.2) == approx(3.995)

def test_describe_socket():
    assert cullenect.describeSocket(1.0, 4.2, 0.03) == "1U: pocket 36.3 mm, insert 36 mm"
    assert cullenect.describeSocket(None, 4.2, 0.03) == "too short for a Cullenect pocket"
```

- [ ] **Step 2:** `python -m pytest tests/test_cullenect.py -v` → FAIL (Modul fehlt).
- [ ] **Step 3:** Konstanten und Funktionen implementieren; `socketUnits` zählt n in `CULLENECT_UNIT_STEP`-Schritten ab 0,5 hoch, solange `socketWidth(n) + 2·margin ≤ available + 1e-9`.
- [ ] **Step 4:** `python -m pytest -q` → alles grün.
- [ ] **Step 5:** Commit „Add Cullenect label and socket dimensions“.

### Task 2: Label-Stil „Cullenect“ und Eingabefeld Taschen-Toleranz

**Files:**
- Modify: `lib/gridfinityUtils/labelGenerator.py` (`LABEL_STYLE_CULLENECT = 'Cullenect'`, an `LABEL_STYLES` anhängen)
- Modify: `lib/gridfinityUtils/binBodyGenerator.py:332-340` (`tabTopClearance`, `hollowTabWallThickness`)
- Modify: `lib/gridfinityUtils/binBodyGeneratorInput.py` (`cullenectSocketOffset: float`, Default `const.CULLENECT_SOCKET_OFFSET`)
- Modify: `commands/commandCreateBin/inputState.py` (Feld `cullenectSocketOffset: float` direkt nach `isLabelBold`)
- Modify: `commands/commandSnapshotTests/testCases.py` (`'cullenectSocketOffset'` in `MM_FIELDS[GENERATOR_BIN]`)
- Modify: alle `tests/e2e/cases/bin_*.json` (`"cullenectSocketOffset": 0.3` nach `isLabelBold`), `tests/e2e/README.md` per `python tests/e2e/write_readme.py`
- Test: `tests/test_cullenect.py`, `tests/test_test_cases.py`

**Interfaces:**
- Produces: `labelGenerator.LABEL_STYLE_CULLENECT`; `hollowTabWallThickness(wall, LABEL_STYLE_CULLENECT) == max(wall, CULLENECT_LABEL_THICKNESS + BIN_TAB_HOLLOW_MIN_SKIN)`; `tabTopClearance(LABEL_STYLE_CULLENECT) == BIN_TAB_TOP_CLEARANCE`; `InputState.cullenectSocketOffset` (cm).

- [ ] **Step 1: Failing tests:** `test_cullenect_is_a_label_style` (`'Cullenect' in LABEL_STYLES`, Reihenfolge der drei alten unverändert); `test_hollow_cullenect_tab_keeps_a_skin_under_the_socket` (`hollowTabWallThickness(0.12, 'Cullenect') == approx(0.16)`); `test_lengths_come_in_mm_and_angles_in_degrees` um `case.state.cullenectSocketOffset == approx(0.03)` erweitern. `binBodyGenerator` lässt sich nur mit Stubs laden — reicht das nicht, die beiden Funktionen samt Test über `cullenect.py` testen und in `binBodyGenerator` nur aufrufen.
- [ ] **Step 2:** pytest → FAIL.
- [ ] **Step 3:** Umsetzen; JSON-Fälle mit einem Wegwerf-Skript im Scratchpad ergänzen (Schlüsselreihenfolge erhalten), README neu schreiben.
- [ ] **Step 4:** `python -m pytest -q` grün; `git diff --stat tests/e2e/cases` zeigt nur die neue Zeile je Datei.
- [ ] **Step 5:** Commit.

### Task 3: Tasche als Fusion-Geometrie

**Files:**
- Create: `lib/gridfinityUtils/cullenectSocketGenerator.py`
- Modify: `lib/gridfinityUtils/binBodyGenerator.py` (Label-Schleife ab Zeile 303, `createTabLabel`)
- Modify: `commands/commandCreateBin/binBuilder.py` (Fach-Labels Zeile 305–320 **und** Schwester-Pfad „shelled“ ab Zeile 433: bei Cullenect keine Text-Parameter per `createLabelDefinition`; im shelled-Pfad zusätzlich Laschenbreite, Neigung, Tasche statt `createTabLabel`)

**Interfaces:**
- Consumes: Task 1 (`socketUnits`, `socketFrontInset`, `effectiveTabWidth`), Task 2.
- Produces: `createCullenectSocket(minX: Dim, maxX: Dim, tabOriginY: Dim, tabWidth: float, tabOriginZ: Dim, baseWidth: Dim, socketOffset: float, overhangAngle: float, targetBody, targetComponent, *, name: str) -> float | None` — schneidet die Tasche und gibt die gebauten Einheiten zurück (`None` = keine Tasche).

Geometrie (Muster `labelGenerator.createLabel`): Ebene in aktueller Laschen-Oberkante; Skizze „`{name} socket sketch`“ mit abgerundetem Rechteck `socketWidth × socketHeight`, r 0,5 mm, voll bemaßt, Mittelpunkt per Bemaßung zum Skizzen-Ursprung; Breitenbemaßung als Ausdruck `baseWidth·n − 6 mm + offset` (über `dim.applyTo`). Extrusion 1,2 mm nach unten als neuer Körper. Zweite Skizze auf Ebene 0,2 mm über Taschenboden: zwei Rippen-Rechtecke volle Taschenlänge × 0,2 mm an den Längsseiten, 0,4 mm hoch extrudiert, vom Taschenkörper abgezogen. Lage: X mittig zwischen `minX` und `maxX`, Y mittig auf der Oberseite mit Vorderrand ≥ `socketFrontInset`. Verschieben-Feature um (parametrische Mitte − aktuelle Mitte), nur wenn ein Ausdruck drin steckt. Dann Cut vom Bin-Körper.

Bei Cullenect im Bin: `tabWidth = effectiveTabWidth(...)`, `tabTopAngle = 0`, keine Text-/Icon-Labels, Tasche für **jedes** Fach mit Lasche (nicht nur nicht-leere Labels).

- [ ] **Step 1:** Akzeptanzkriterium vorab festhalten (nicht per pytest testbar): In Fusion eine 1x1x3-Bin „Cullenect“ erzeugen; Messung ergibt Tasche 36,30 × 11,30 × 1,20 mm (±0,01), Rippen 0,20 × 0,40 mm ab 0,20 über Boden; alle Skizzen `isFullyConstrained`; Timeline ohne Fehler; danach `gfBaseWidth` = 40 mm ⇒ Tasche 34,30 mm und mittig.
- [ ] **Step 2:** Umsetzen.
- [ ] **Step 3:** Prüfung nach Step 1 in Fusion (Fusion-MCP `fusion_mcp_execute` oder Jörg), Messwerte und Constraint-Liste ins Protokoll; `python -m pytest -q` grün.
- [ ] **Step 4:** Commit.

### Task 4: Bin-Dialog — Sichtbarkeit, Taschen-Toleranz, Breitenanzeige

**Files:**
- Modify: `commands/commandCreateBin/entry.py` (neue ID `BIN_TAB_CULLENECT_OFFSET_INPUT_ID`, neue Zeile `BIN_REAL_DIMENSIONS_TABLE_CULLENECT` in der Maß-Tabelle `render_actual_bin_dimensions_table`/`update_actual_bin_dimensions`; `initDefaultUiState`, `command_created`, `onChangeValidate`, `getInputsState`, `snapshotSettings`)
- Modify: `lib/gridfinityUtils/cullenect.py` (`socketSummary(...)`)
- Test: `tests/test_cullenect.py`, `tests/test_command_ui_state.py`

**Interfaces:**
- Produces: `socketSummary(compartmentWidths: list[float], tabStart: float, tabLength: float, baseWidth: float, socketOffset: float) -> list[str]` — je verschiedener Breite eine Zeile `describeSocket`, sortiert, ohne Dubletten.

Verhalten: Bei Stil Cullenect sind Text, Icon, Fett und Neigung deaktiviert (Werte bleiben im Zustand), Toleranz-Eingabe (mm, Default 0,3, 0–1 mm) sichtbar. Die Maß-Tabelle bekommt bei Cullenect eine zweite Zeile mit `socketSummary` (Spec: „in der Maß-Tabelle“); „Gridfinity settings“ bekommt einen eigenen Abschnitt „Cullenect“ in `snapshotSettings`, weil die Maß-Tabelle dort ausgeschlossen ist. Fachbreiten aus `compartmentCellSize()` und den Fach-Pockets.

- [ ] **Step 1: Failing tests:** `test_socket_summary_lists_each_width_once` (4x2-Bin gemischt mit `tabLength` 4, also Laschenlänge 16,8 cm: Zellen 40,375 mm, Fächer 1/1/2/4 Zellen ⇒ `["1U: …", "2U: …", "4U: …"]`; dieselbe Bin mit `tabLength` 1 ⇒ nur `["1U: …"]`); `test_missing_saved_value_falls_back_to_default` (UI-Zustand ohne Toleranz-Schlüssel lädt Default — gegen `CommandUiState`, wie bestehende Tests); `test_switching_back_from_cullenect_keeps_user_values` (Zustand mit `tabWidth` 13 mm, Stil hin und zurück ⇒ 13 mm, Text unverändert — prüft, dass `onChangeValidate` keine Werte schreibt; falls `entry.py` ohne Fusion nicht ladbar, die Logik als reine Funktion `cullenectDisabledInputs(style) -> set[str]` in `cullenect.py` testen).
- [ ] **Step 2:** FAIL.
- [ ] **Step 3:** Umsetzen.
- [ ] **Step 4:** pytest grün; in Fusion: Maß-Tabelle zeigt bei 4x2 gemischt (`tabLength` 4) die drei Breiten, Umschalten auf Outline stellt Text/Icon wieder her (Screenshot).
- [ ] **Step 5:** Commit.

### Task 5: Snapshot-Fälle und Constraint-Check

**Files:**
- Create: `commands/commandSnapshotTests/constraints.py` (Fusion-frei)
- Modify: `commands/commandSnapshotTests/entry.py` (`runCase`: nach dem Bauen Skizzen aller Komponenten prüfen)
- Create: `tests/e2e/cases/bin_1x1x3_cullenect.json`, `bin_2x1x3_cullenect_params_base_40.json` (`parameters: {"gfBaseWidth": 40}`), `bin_1x1x3_cullenect_params_length_50_height_10.json` (`parameters: {"gfBaseLength": 50, "gfHeightUnit": 10}`), `bin_3x1x3_cullenect_compartments.json`, `bin_4x2x3_cullenect_mixed.json` (`tabLength` 4; vorn ein Fach über 4 Zellen, hinten ein Fach über 2 Zellen + zwei Einzelfächer), `bin_2x1x4_cullenect_hollow_tab.json`, `bin_2x1x3_cullenect_shelled.json` (`binType` `Shelled`, Schwester-Pfad in `binBuilder.py`), `bin_1x4x10_cullenect_creases.json` (gefaltete Wände, feste Lasche), `bin_1x1x2_cullenect.json`, `bin_6x4x12_cullenect.json`
- Test: `tests/test_snapshot_constraints.py`

**Interfaces:**
- Produces: `unconstrainedSketches(sketches) -> list[str]` (Duck-Typing: `.name`, `.isFullyConstrained`); `constraintFailure(generator: str, caseName: str, names: list[str]) -> str | None` — Fehler bei Generator `label` (ab Task 11) oder Fallname mit `cullenect`; sonst werden Namen nur gemeldet (Spec: Bestand nicht ungefragt beheben).

- [ ] **Step 1: Failing tests:** zwei Fake-Skizzen, eine unbestimmt ⇒ Liste mit ihrem Namen; `constraintFailure('bin', 'bin_1x1x3_cullenect', ['x'])` ist Text, `constraintFailure('label', 'label_1u_screw_text', ['x'])` ist Text, `constraintFailure('bin', 'bin_1x1x3_plain', ['x'])` ist `None`; `test_every_case_in_the_repo_loads` lädt die neuen Fälle.
- [ ] **Step 2:** FAIL. **Step 3:** Umsetzen.
- [ ] **Step 4:** pytest grün. In Fusion „Gridfinity tests: update snapshots“ nur für die neuen Fälle, dann „run“ für alle: alle grün, Constraint-Meldungen der Bestandsfälle an Jörg (Liste im PR-Text).
- [ ] **Step 5:** Commit. **Live-Test (Jörg):** Probedruck 1x1-Bin + Original-Cullenect-Einleger klickt, hält, löst sich.

---

# Runde 3 — Symbole (OpenSCAD → SVG)

### Task 6: Symbol-Katalog

**Files:**
- Create: `lib/gridfinityUtils/cullenectCatalog.py` (Fusion-frei)
- Test: `tests/test_cullenect_catalog.py`

**Interfaces:**
- Produces: Baukasten-Listen für das Render-Werkzeug `HEADS = ['none','socket','countersunk','roundh','pan']`, `SHAFTS = ['machine','tapping']`, `THREADS = ['full','partial']`, `DRIVERS = ['none','slot','phillips','phillips_slot','phillips_square','torx','hex','square','triangle']`, `CULLENECT_HARDWARE` (19 Cullenect-Schlüssel aus `Select_Hardware`, nur für das Werkzeug); `displayName(key) -> str`; `isValidScrew(head, shaft, threads, driver, flange, security) -> bool`; `screwIconFileName(...) -> str` (`screw_<head>_<shaft>_<threads>_<driver>_<flange|noflange>_<sec|nosec>.svg`); `allScrewCombinations() -> list[tuple]`; `HARDWARE_LABEL_ICON_TYPE: dict[str, str]` (washer*→`washers`, nut*/tnut*→`nuts`, `threaded_insert`→`inserts`, `magnet`→`magnets`, crimp*→`crimps`).
- Produces (zur Laufzeit, **aus den Ordnern abgeleitet** — Spec: neues Symbol = neue SVG, keine Code-Änderung): `listHardwareIcons(folder) -> list[tuple[str, str]]` (Anzeigename, Pfad; jede SVG in `cullenectIcons/hardware/`); `screwOptions(folder) -> dict[str, list[str]]` (Werte je Baukasten-Feld, gelesen aus den Dateinamen in `cullenectIcons/screws/`); `screwIconPath(folder, head, shaft, threads, driver, flange, security) -> str | None` (`None` = Kombination nicht vorhanden ⇒ im Dialog gesperrt).
- Modify: `lib/gridfinityUtils/labelGenerator.py` `LABEL_ICON_TYPE_ORDER` um `inserts`, `magnets`, `crimps` erweitern.

Ungültig: Flansch bei `countersunk` oder `none`; Antrieb ≠ `none` bei Kopf `none`; Sicherheits-Pin bei Antrieb `none`.

- [ ] **Step 1: Failing tests:** `len(allScrewCombinations()) == 480`; `isValidScrew('countersunk', …, flange=True, …) is False`; Dateiname-Beispiel `screw_socket_machine_full_hex_noflange_nosec.svg`; `len(CULLENECT_HARDWARE) == 19`; jeder Hardware-Schlüssel hat einen Icon-Typ; mit `tmp_path`: eine zusätzliche `dowel.svg` im Hardware-Ordner erscheint in `listHardwareIcons` als „Dowel“; zwei Schrauben-Dateien ⇒ `screwOptions` liefert genau deren Werte, `screwIconPath` für eine fehlende Kombination `None`.
- [ ] **Step 2:** FAIL. **Step 3:** Umsetzen. **Step 4:** grün. **Step 5:** Commit.

### Task 7: Konvertierungswerkzeug und gerenderte Symbole

**Files:**
- Create: `tools/cullenect/Cullenect.scad` (Kopie Commit `d6dc0bb`, unverändert), `tools/cullenect/LICENSE` (MIT von CullenJWebb), `tools/cullenectIcons.py`
- Create (generiert): `lib/gridfinityUtils/cullenectIcons/screws/*.svg`, `…/hardware/*.svg`, `…/README.md` (Quelle, MIT, Credits); Hardware-Kopien in `lib/gridfinityUtils/labelIcons/<typ>/` samt Vorschaubildern per `tools/labelIcons.py`
- Test: `tests/test_cullenect_icons_tool.py`

**Interfaces:**
- Produces: `wrapperScad(kind: str, combination) -> str` (Text einer `.scad`, die `use <Cullenect.scad>` lädt und `projection()` von Kopf−Antrieb ∪ Schaft ∪ Pin bzw. `cullenect_hardware(key)` rendert — Zusammensetzung wie `fastener()` in `cullenect_label_generate`); `openscadCommand(exe, scadPath, svgPath) -> list[str]`; `svgSize(path) -> tuple[float, float]` (mm aus `width`/`height`/`viewBox`, liegt in `cullenectCatalog.py`, weil der Label-Befehl es zur Laufzeit braucht). Kein Katalog-JSON: Größe und Lage ergeben sich aus der SVG selbst (siehe Festlegung „Lage des Symbols“). Die Schraube ist breit: Kopf 6 mm + Schaft 8,56 mm (`shaftX = headY·0,856`) ≈ 14,6 mm.

- [ ] **Step 1: Failing tests** für `wrapperScad` (enthält `use <Cullenect.scad>`, `cullenect_head(head="socket"`), `openscadCommand` (`[exe, '-o', svg, scad]`), `svgSize` an einer kleinen Beispiel-SVG in `tmp_path`.
- [ ] **Step 2:** FAIL. **Step 3:** Umsetzen.
- [ ] **Step 4:** pytest grün; Werkzeug lokal laufen lassen (`python tools/cullenectIcons.py --openscad "C:\Program Files\OpenSCAD\openscad.exe"`, im Hintergrund, Dauer messen): 480 + 19 SVGs; Stichprobe von 5 SVGs gegen OpenSCAD-Vorschau.
- [ ] **Step 5:** Commit (Werkzeug und generierte Dateien getrennt).

---

# Runde 4 — Befehl „Gridfinity Label“

### Task 8: Spike — Text- und SVG-Skizzen vollständig bestimmt

Klärt vor dem Generator, wie `SketchText` und importierte SVG-Kurven in Fusion `isFullyConstrained` werden (Spec: SVG `isFixed`, Text an bemaßte Konstruktion). Ergebnis: kurze Notiz in `docs/specs/2026-11-14-cullenect-labels-design.md` (Abschnitt „Vollständig bestimmte Skizzen“, Befund mit Datum) und ein Wegwerf-Skript im Scratchpad. Kein Produktionscode. Gleichzeitig Befund zu den bestehenden Text/Icon-Labels (Outline/Engraved/Embossed) für Jörg.

- [ ] **Step 1:** In Fusion: Skizze mit Mehrzeilen-Text, Eckpunkte des Textrahmens bemaßen/fixieren ⇒ `isFullyConstrained`? SVG importieren, alle Kurven `isFixed = True` ⇒ `isFullyConstrained`? Außerdem messen: welche Fusion-Texthöhe ergibt Großbuchstaben so hoch wie Cullenects `text(size = 5)` in Open Sans (OpenSCAD-`size` ist nicht die Fusion-Texthöhe) — Ergebnis legt `CULLENECT_TEXT_HEIGHT` in Task 9 fest.
- [ ] **Step 2:** Befund notieren, Commit (nur Spec-Notiz).

### Task 9: Einleger-Layout als reine Logik

**Files:**
- Create: `lib/gridfinityUtils/cullenectLabelLayout.py` (Fusion-frei); Test: `tests/test_cullenect_label_layout.py`

**Interfaces:**
- Produces: `LabelLayout` (dataclass, cm): `width, height, textMinX, textMaxX, iconMaxX, iconCenterY, lineHeights: list[float]`; `labelLayout(width: float, height: float, iconSize: tuple[float, float] | None, isScrew: bool, lineCount: int) -> LabelLayout`; `labelSize(units: float | None, widthMm: float | None, baseWidth: float, offsetX: float, offsetY: float) -> tuple[float, float]`; `validWidth(width: float) -> bool` (1,0–30,0 cm). Symbol: rechte Kante `iconMaxX = width` bei Schrauben, sonst `width − max(0, (height − iconHeight)/2)`; senkrecht mittig. Text links ab `CULLENECT_TEXT_MARGIN = 0.1`, endet `CULLENECT_ICON_GAP = 0.1` vor der linken Symbolkante; Zeilenhöhen nach Task 8.

- [ ] **Step 1: Failing tests:** 1U mit Schraube der Größe (1,46 × 1,0): `width == 3.6`, `iconMaxX == approx(3.6)`, `textMaxX == approx(3.6 - 1.46 - 0.1)` (≈ 2,04 cm); Hardware 0,8 × 0,8: `iconMaxX == approx(3.45)`; ohne Symbol: `textMaxX == approx(3.5)`; `labelSize(1, None, 4.2, 0, 0) == (3.6, 1.1)`, `labelSize(None, 25, 4.2, 0, 0) == (2.5, 1.1)`, `labelSize(1, None, 4.2, -0.01, 0.01) == approx((3.59, 1.11))`, `labelSize(None, 25, 4.2, -0.01, 0) == approx((2.49, 1.1))`; `validWidth(0.9) is False`, `validWidth(30.1) is False`; leerer Einleger (`lineCount` 0, kein Symbol) ist gültig.
- [ ] **Step 2:** FAIL. **Step 3:** Umsetzen. **Step 4:** grün. **Step 5:** Commit.

### Task 10: Einleger-Generator

**Files:**
- Create: `lib/gridfinityUtils/cullenectLabelGenerator.py`

**Interfaces:**
- Consumes: Task 1 (Maße), 6 (Katalog), 8 (Befund), 9 (Layout), `labelGenerator._addText`/`_importIcon`.
- Produces: `CullenectLabelInput` (width: Dim, height: float, lines: list[UserParameter], iconPath: str | None, surface: `'Embossed'|'Debossed'|'Flush'`, isBold: bool); `createCullenectLabel(input, targetComponent, *, name) -> tuple[BRepBody, BRepBody | None]` (Grundkörper, Text/Symbol-Körper).

Geometrie: Grundkörper aus drei Extrusionen (0–0,2 voll, 0,2–0,8 Einzug 0,2, 0,8–1,2 voll), Ecken r 0,5, Breiten-Bemaßung als Ausdruck auf den Breiten-Parameter. Text/Symbol 0,2 mm: erhaben auf 1,2–1,4; vertieft/bündig 1,0–1,2 aus dem Grundkörper geschnitten, Körper bleibt erhalten. Symbol-Kurven `isFixed`, Lage per Verschieben-Feature abhängig von der Breite (Spec).

- [ ] **Step 1:** Akzeptanzkriterium vorab: 1U-Einleger mit Text „M3x10“ + Schraube: Außenmaß 36,00 × 11,00 × 1,20 mm, Einzug 0,20 mm zwischen 0,2 und 0,8 mm Höhe (±0,01); zwei Körper; alle Skizzen bestimmt; Breiten-Parameter auf 78 mm ⇒ Symbol bleibt rechts, keine Timeline-Fehler. Vergleich mit Jörgs gedruckten Einlegern (f3z, in Fusion geöffnet).
- [ ] **Step 2:** Umsetzen. **Step 3:** Prüfung in Fusion, Messwerte protokollieren. **Step 4:** Commit.

### Task 11: Befehl, Dialog, Snapshot-Fälle

**Files:**
- Create: `commands/commandCreateLabel/{__init__.py, entry.py, inputState.py, labelBuilder.py, resources/}` (Aufbau wie `commandCreateBaseplate`)
- Modify: `commands/__init__.py` (Befehl registrieren), `commands/commandSnapshotTests/testCases.py` (`GENERATOR_LABEL = 'label'`, `MM_FIELDS`/`DEGREE_FIELDS`/`CELL_LIST_FIELDS`/`PARAMETER_FIELDS` ergänzen), `commands/commandSnapshotTests/entry.py` (`STATE_CLASSES`, `buildBodies`)
- Create: `tests/e2e/cases/label_1u_screw_text.json`, `label_2u_hardware.json`, `label_25mm_free.json`, `label_6u_text.json`
- Test: `tests/test_test_cases.py`

**Interfaces:**
- Produces: `InputState` (Label): `baseWidth, widthUnits, widthMm, useUnits, line1, line2, showScrew, head, shaft, threads, driver, flange, security, hardware, surface, offsetX, offsetY, isBold`; `buildLabel(state) -> list[BRepBody]`.

Dialog: Auswahllisten aus `cullenectCatalog.screwOptions`/`listHardwareIcons`, Kombinationen ohne Datei gesperrt (`screwIconPath` gibt `None`; `isValidScrew` dient nur dem Render-Werkzeug), Rasterbreite aus `gfBaseWidth` des Designs falls vorhanden; Defaults speicherbar; „Gridfinity settings“ per Tag wie Bin/Baseplate; Platzierung nahe Ursprung mit `placementUtils`; Dokumenttyp wie Bin (Bauteil- oder Hybrid-Konstruktion).

- [ ] **Step 1: Failing tests:** neuer Generator lädt (`test_every_case_in_the_repo_loads` mit `STATE_CLASSES` inkl. Label), `offsetX`/`offsetY`/`widthMm` werden mm→cm umgerechnet; der Constraint-Check ist für Generator `label` streng (Task 5).
- [ ] **Step 2:** FAIL. **Step 3:** Umsetzen.
- [ ] **Step 4:** pytest grün; in Fusion Snapshots der vier Label-Fälle anlegen, alle Fälle „run“ grün, Constraint-Check grün.
- [ ] **Step 5:** Commit. **Live-Test (Jörg):** Einleger 1U zweifarbig drucken, klickt in die neue Tasche und in eine Original-Cullenect-Bin.

---

## Entschieden und offen

**Entschieden (Runde 1, nach Plan, Dauerfreigabe):** Taschenbreite (A) — Standardbreiten in 0,5U-Schritten mit 1,0 mm Mindestrand; Original-Einleger passen in jede Tasche, auch in Fach-Laschen. Verworfen (B): freie Breite = Laschenlänge − 2 × 1,4 mm — 1U-Bin exakt 36,3 mm, ein 1x1-Fach der 4x2-Bin aber 37,6 mm (Original-Einleger hätte 1,3 mm Spiel).

**Offen für Jörg, vor Runde 4 klären** (Auslegung der Spec, keine Abweichung):
1. **Oberfläche „vertieft“ vs. „bündig“:** Laut Spec bleibt bei „vertieft“ der Füllkörper erhalten — dann sind beide gleich. Vorschlag: bei „vertieft“ Füllkörper ausgeblendet (wird nicht exportiert, kann eingeblendet werden), bei „bündig“ sichtbar.
2. **Zwei Textzeilen:** Vorschlag übereinander, statt Cullenects zweitem Text auf derselben Zeile rechts.
3. **Fach-Laschen automatisch aufs Fach verlängern** (statt `tabLength` von Hand)? Plan: nein, Bestandsverhalten.
