# Runde 40 – Symbole aus Linien und Bögen, ein Import: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Symbole bauen messbar schneller: Symboldateien aus Linien, Kreisbögen (und Splines) statt Polygonen, und je
Symbol ein einziger `importSVG`.

**Architecture:** Ein reines Python-Modul `svgSymbol` liest Symboldateien (Umriss, Punktzahl) und berechnet die
Import-Argumente aus der in Fusion gemessenen Abbildung. Ein Werkzeug in `dev-notes/tools` zerlegt die Polygone der
Dateien einmalig (und nach jedem neuen Rendern) und prüft die Kontur. `labelGenerator._importIcon`/`_iconMeasure`
nutzen `svgSymbol` statt Probe-Importen.

**Tech Stack:** Python 3 (nur Standardbibliothek), Fusion API, pytest mit `tests/stubs`.

**Spec:** `dev-notes/specs/2026-11-18-runde-40-symbol-speed.md`

## Global Constraints

- Längen im Add-in-Code in cm, Testfälle in mm; svg-Koordinaten in svg-Einheiten.
- Abbildung von `importSVG` (gemessen): Skizze = (x, −y) · `SVG_UNIT_CM` · scale + (posX, posY), `SVG_UNIT_CM = 2.54 / 96`.
- Toleranz der Zerlegung 0,01 mm (= 0,01 svg-Einheiten bei den OpenSCAD-Dateien, deren Einheit mm ist).
- Keine Versionsänderung; CHANGELOG-CULLENECT.md unter `## Unreleased`, eigene Gruppe `### Faster symbols (p371)`.
- Commit-Messages englisch, keine Personennamen außer Credits (CullenJWebb, Le0Michine …), keine lokalen Pfade.
- Jede Skizze wie bisher (Symbol-Skizzen fixiert bzw. bemaßt), Text-Skizzen bleiben Ausnahme.

## Review Focus

- Datei mit schon vorhandenen `A`-Befehlen (16 eigene Icons, `fill-rule="evenodd"`, Zahlen ohne Leerzeichen
  `M95.00,50.00`, `Z` groß): Werkzeug lässt den Zug unverändert, `svgSymbol` liest sie richtig → Test in Task 1 und 2.
- Ganzer Kreis als Zug (Schraubenschaft-Querschnitt, Magnet): wird zu zwei Halbbögen, nicht zu einem entarteten
  Bogen mit Start = Ende → Test in Task 2.
- Gewinde-Zickzack (kurze gerade Stücke mit Knick): bleibt Linien, kein Bogen über Ecken hinweg → Test in Task 2.
- Kleine Bögen am Polygon-Anfang (Zug beginnt mitten in einem Bogen): Start an der schärfsten Ecke, sonst wird der
  Bogen zerteilt → Test in Task 2 (gedrehter Startpunkt ergibt dieselbe Segmentzahl).
- Symbol auf gekippter Bin-Label-Ebene / Skizze mit gespiegelter x-Achse: ein Import platziert richtig → Fusion-Prüfung
  in Task 5 (vorhandener Log „placed at … expected …“, Abweichung ≤ 0,001 mm).

---

### Task 1: `svgSymbol` – Symboldatei lesen, Umriss, Punktzahl, Import-Argumente

**Files:**
- Create: `lib/gridfinityUtils/svgSymbol.py`
- Test: `tests/test_svg_symbol.py`

**Interfaces:**
- Produces:
  - `SVG_UNIT_CM: float = 2.54 / 96`
  - `Segment = tuple` – `('line', p0, p1)`, `('arc', p0, p1, rx, ry, rotation, largeArc: bool, sweep: bool)`,
    `('cubic', p0, c1, c2, p1)`; Punkte als `(x, y)` in svg-Einheiten
  - `parsePath(d: str) -> list[list[Segment]]` – je geschlossenem Zug seine Segmente; versteht `M L A C Z z`
    (absolut), Zahlen mit Komma oder Leerzeichen, Exponenten
  - `readSymbol(path: str) -> Symbol`; `@dataclass Symbol: loops: list[list[Segment]]; bounds: tuple[float, float, float, float]` (svg-Einheiten, minX, minY, maxX, maxY), Property `pointCount: int` (= Segmente + Bögen über alle Züge), Property `aspect: float` (Breite/Höhe)
  - `segmentBounds(segment) -> tuple` – Bogen über Mittelpunkt-Parametrisierung (SVG 1.1 F.6.5) inkl. Extrema bei 0°/90°/180°/270° im überstrichenen Winkel; Bézier über Nullstellen der Ableitung
  - `importArguments(bounds, minX: float, minY: float, height: float) -> tuple[float, float, float]` – `(x, y, scale)` für `Sketch.importSVG`, damit die gezeichnete Unterkante links bei `(minX, minY)` cm liegt und die Höhe `height` cm ist

- [ ] **Step 1: Write the failing tests**

```python
def test_parse_polygon_and_arcs():
    loops = svgSymbol.parsePath('M 2,1 L 12,1 L 2,4 z M14,-3 A 2,2 0 0 1 18,-3 L 14,-3 Z')
    assert [len(loop) for loop in loops] == [3, 2]
    assert loops[1][0][0] == 'arc'

def test_point_count_matches_fusion():          # gemessen: Probe 6, Hex nut 10
    assert readSymbol(TRI_WITH_ARC).pointCount == 6
    assert readSymbol(LABEL_ICONS + '/nuts/hex-nut.svg').pointCount == 10

def test_arc_bounds_include_bulge():
    assert segmentBounds(('arc', (14, -3), (18, -3), 2, 2, 0, False, True)) == approx((14, -5, 18, -3))

def test_hex_nut_bounds():                       # Kreis-Loch liegt innen, Umriss = Sechseck
    assert readSymbol(HEX).bounds == approx((5, 11.03, 95, 88.97))

def test_import_arguments_place_bottom_left():
    (x, y, s) = importArguments((-11.56, -5, 3, 5), 2.0, 1.0, 0.8)
    k = SVG_UNIT_CM * s
    assert -11.56 * k + x == approx(2.0) and -5 * -k + y == approx(1.8)   # oben = minY + height
    assert 10 * k == approx(0.8)

def test_reads_every_symbol_file():              # alle 542 Dateien lesbar, Züge geschlossen
```

- [ ] **Step 2:** `python -m pytest tests/test_svg_symbol.py -v` → FAIL (`ModuleNotFoundError`)
- [ ] **Step 3:** `svgSymbol.py` implementieren (keine adsk-Imports).
- [ ] **Step 4:** Tests → PASS; volle Suite `python -m pytest` grün.
- [ ] **Step 5:** Commit `Add svgSymbol: read symbol svgs, bounds, point count and importSVG arguments`

### Task 2: Werkzeug `dev-notes/tools/arcSymbols.py` – Zerlegung und Prüfung

**Files:**
- Create: `dev-notes/tools/arcSymbols.py`, `tests/fixtures/symbols/torx_countersunk_original.svg` (Kopie des heutigen Originals)
- Test: `tests/test_arc_symbols_tool.py` (lädt das Werkzeug per `importlib` wie `test_cullenect_icons_tool.py`)

**Interfaces:**
- Consumes: `svgSymbol.parsePath`, `svgSymbol.segmentBounds`
- Produces:
  - `decomposeLoop(points: list[tuple[float, float]], tolerance: float) -> list[Segment]`
  - `pathData(loops: list[list[Segment]]) -> str` (Ausgabe `M … L … A … C … z`, Zahlen mit `:g`)
  - `contourDeviation(original: list[list[tuple]], loops: list[list[Segment]]) -> float` (beide Richtungen, Abtastung ≤ 0,002)
  - `loopArea(segments) -> float`
  - `convertFile(path: str, tolerance: float, write: bool) -> Report` mit `pointsBefore, lines, arcs, cubics, deviation, areaChange, changed`; wirft `SymbolCheckError` bei Abweichung > Toleranz, Flächenänderung > max(0,5 %, 0,01 mm²), geänderter Zugzahl
  - CLI `python dev-notes/tools/arcSymbols.py [--tolerance 0.01] [--check] <Ordner…>`; schreibt/aktualisiert je Ordner `symbol-check.json` (`{datei: {"areas": [...], "bounds": [...]}}` des Originals)

Algorithmus `decomposeLoop` (Prototyp in der Spec gemessen):
Punkte entdoppeln; ganzer Zug passt auf einen Kreis (≥ 8 Punkte, Radialfehler ≤ tol) → zwei Halbbögen. Sonst Start an der
Ecke mit dem größten Knickwinkel, dann gierig: vom aktuellen Punkt aus so weit wie möglich verlängern, solange der Lauf
eine Linie (Punktabstand zur Sehne ≤ tol) oder ein Bogen ist (Kåsa-Kreisfit, Radialfehler der Punkte **und** der
Sehnenmitten ≤ tol, ≥ 4 Punkte, monotoner Drehsinn, Überstreichung < 360°, Radius ≤ 50); abbrechen, wenn 8 Punkte
lang keine Form mehr passte; die längere Form gewinnt, bei Gleichstand die Linie. Läufe von ≥ 6 Punkten, die weder
Linie noch Bogen sind, versucht es als eine kubische Bézier (Endpunkte fest, Tangenten aus den Nachbarpunkten,
Längen per kleinster Quadrate) innerhalb tol; sonst Linien. Züge, die schon `A`/`C` enthalten, bleiben unverändert.

- [ ] **Step 1: Write the failing tests**

```python
def test_circle_polygon_becomes_two_half_arcs():      # 360 Punkte r 0.75
def test_rounded_rectangle_is_4_lines_4_arcs():
def test_thread_zigzag_stays_lines():                 # Zickzack 0.7 mm, Knick 90°
def test_start_point_does_not_matter():               # gedrehter Polygonstart → gleiche Segmentzahl
def test_torx_original_within_tolerance():            # Fixture: ≤ 60 Segmente, deviation ≤ 0.01, Flächen ±0.5 %
def test_existing_arcs_are_kept():                    # hex-nut.svg: pathData unverändert
def test_check_error_when_tolerance_exceeded():       # künstlich verfälschte Zerlegung → SymbolCheckError
def test_free_form_uses_cubic():                      # Parabelstück → ein 'cubic'
```

- [ ] **Step 2:** `python -m pytest tests/test_arc_symbols_tool.py -v` → FAIL
- [ ] **Step 3:** Werkzeug implementieren; Docstring nennt Herkunft der Daten (Cullenect, MIT) nicht – das steht in den READMEs (Task 3).
- [ ] **Step 4:** → PASS, volle Suite grün.
- [ ] **Step 5:** Commit `Add arcSymbols tool: rebuild symbol polygons as lines, arcs and splines within 0.01 mm`

### Task 3: Alle Symboldateien zerlegen, Prüfdateien, Herkunftsvermerke, Render-Werkzeuge

**Files:**
- Modify: alle `lib/gridfinityUtils/cullenectIcons/{screws,hardware,setscrews}/*.svg`, `lib/gridfinityUtils/labelIcons/**/*.svg` (nur Züge ohne Bögen)
- Create: `symbol-check.json` in jedem dieser Ordner
- Modify: `lib/gridfinityUtils/cullenectIcons/README.md`, `.../setscrews/README.md`, `lib/gridfinityUtils/labelIcons/cullenect-LICENSE.txt`, `tools/cullenectIcons.py`, `tools/setScrewIcons.py`, `tools/labelIcons.py` (nach dem Rendern `arcSymbols.convertFile(..., write=True)` aufrufen)
- Test: `tests/test_symbol_files.py`

- [ ] **Step 1: Write the failing test** `test_every_symbol_file_is_arcs_and_matches_check`: für jede Datei aller
  Symbolordner: `readSymbol` ok, ≤ 150 Segmente, Flächen je Zug und Umriss gegen `symbol-check.json` innerhalb
  Toleranz (Flächen ±max(0,5 %, 0,01 mm²), Umriss ±0,01). Plus `test_render_tools_call_arc_symbols` (Quelltext der
  drei Render-Werkzeuge ruft `convertFile`).
- [ ] **Step 2:** → FAIL (noch Polygone, keine check-Dateien)
- [ ] **Step 3:** `python dev-notes/tools/arcSymbols.py lib/gridfinityUtils/cullenectIcons/screws lib/gridfinityUtils/cullenectIcons/hardware lib/gridfinityUtils/cullenectIcons/setscrews lib/gridfinityUtils/labelIcons` (rekursiv), Ausgabe-Summe ins Commit-Body.
  READMEs: Satz „Rebuilt from the rendered polygons as lines, circular arcs and splines with `dev-notes/tools/arcSymbols.py`, tolerance 0.01 mm (round 40); `symbol-check.json` holds the area and outline of the polygons for the tests.“ Herkunft/Lizenz/Commit unverändert.
- [ ] **Step 4:** → PASS, volle Suite grün (Tests, die Punktzahlen der Dateien erwarten, z. B. `test_bin_label_layout`, prüfen und – nur wo sie die alte Datei-Punktzahl festschreiben – auf `svgSymbol` umstellen).
- [ ] **Step 5:** Commit `Rebuild all symbol svgs as lines and arcs`

### Task 4: Ein Import je Symbol in `labelGenerator`

**Files:**
- Modify: `lib/gridfinityUtils/labelGenerator.py:151-191` (`_importMeasured`, `_importIcon`, `_iconMeasure`)
- Test: `tests/test_label_icon_import.py` (Stub-Sketch, der `importSVG`-Aufrufe zählt)

**Interfaces:**
- Consumes: `svgSymbol.readSymbol`, `svgSymbol.importArguments`, `Symbol.pointCount`, `Symbol.aspect`
- Produces: unveränderte Signaturen `_importIcon(sketch, path, minX, minY, height)` und `_iconMeasure(sketch, path) -> tuple[float, int] | None` (letzteres ohne Import; bleibt wegen der Aufrufer)

- [ ] **Step 1: Write the failing tests**
  `test_import_icon_imports_once` (Stub zählt genau 1 `importSVG` mit den Argumenten aus `importArguments`, keine
  `sketches.add` für Wegwerf-Skizzen); `test_icon_measure_does_not_import` (0 Importe, liefert `(aspect, pointCount)`
  der Datei); `test_import_icon_moves_when_off` (Stub liefert nach dem Import Bounds um 0,01 cm versetzt → ein
  `sketch.move` mit reiner Verschiebung um −0,01).
- [ ] **Step 2:** → FAIL
- [ ] **Step 3:** `_importIcon`: `symbol = readSymbol(path)`, `importSVG(path, *importArguments(symbol.bounds, minX, minY, height))`, Bounds der neuen Kurven messen (nur der importierten: Kurvenzahl vorher merken), bei > 1e-4 cm Abweichung `sketch.move(curves, translation)`, `debugLog` wie bisher. `_importMeasured` entfällt. Code-Kommentar nach Skill `code-doku` (Wurzel: 4 Importe + Kurven-Iteration je 1 ms; gemessene Abbildung; verworfen: Probe-Importe).
- [ ] **Step 4:** → PASS, volle Suite grün.
- [ ] **Step 5:** Commit `Import each label symbol once, placed from its own outline`

### Task 5: Fusion – nachher messen, Platzierung, Skizzen, Snapshots

**Files:**
- Fusion-Jobs (außerhalb des Repos) `r40_m_*` unverändert wiederholen; neuer Job `r40_check` (Platzierung ≤ 0,001 mm auf
  Box-Schild, Einleger, Bin-Label flach und gekippt `bin_3x2x6_tab_steep_tilted` mit Symbol; `isFullyConstrained`
  der Symbol-Skizzen wie vorher; Profilzahl je Symbol wie vorher)
- Modify: `tests/e2e/snapshots/<betroffene Fälle>` (nur Fälle mit Symbol)

- [ ] **Step 1:** Fusion-Slot anfragen; `r40_m_box/ins/bin` + `r40_check` laufen lassen, Zahlen in die Spec (Tabelle „nachher“).
- [ ] **Step 2:** Snapshot-Fälle mit Symbol laufen lassen (Liste aus Spec), Abweichung je Fall ansehen (Symbolvolumen < 0,5 %, Umriss ≤ 0,02 mm), dann neu abnehmen; Fälle ohne Symbol unverändert grün.
- [ ] **Step 3:** Commit `Update snapshots of symbol cases for arc symbols`

### Task 6: CHANGELOG, Klicktest-Checkliste, Review, PR

**Files:**
- Modify: `CHANGELOG-CULLENECT.md` (`## Unreleased` → `### Faster symbols (p371)`, nur gemessene Zahlen, Credits CullenJWebb)
- Create: `dev-notes/klicktest-r40.md` (Box-Schild, Einleger, Bin-Label mit Torx-/Crimp-Symbol; Dauer, Aussehen, Text ändern, Change Parameters)

- [ ] **Step 1:** CHANGELOG + Checkliste schreiben, `git diff master | grep -iE 'j(ö|oe)rg'` leer.
- [ ] **Step 2:** Opus-Review (Diff + Spec + Plan), Funde abarbeiten.
- [ ] **Step 3:** „Klicktest R40 bereit, Head <hash>“ an die Hauptsitzung; nach bestandenem Klicktest PR-Text vorlegen, Push, PR, CI grün.
