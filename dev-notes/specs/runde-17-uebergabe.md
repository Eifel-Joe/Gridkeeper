# Runde 17 – Übergabe

Stand 2026-11-15. Branch `runde-17`, abgezweigt von `runde-14-18` (82f15f8), mit `runde-14-18` (38af627) gemergt. Der
Branch ist nicht gepusht und nicht gemergt.
- Spec: `dev-notes/specs/2026-11-15-runde-17-design.md`, mit der Ergänzung zu p180.
- Plan: `dev-notes/plans/2026-11-15-runde-17.md`, von der Hauptsitzung freigegeben.

Punkte:
- p110 „Einleger mit zwei Zeilen und negativer Höhenkorrektur: Unterlängen ragen unten über den Rand“
- p140 „Vertiefter Einleger: Symbol in voller Höhe kerbt den Rand ein“
- p52 „Einleger-Text passt sich einer nachträglich kleineren Breite nicht an“
- p51 „Hardware-Symbole schneller machen (Einleger mit Mutter braucht gut 20 Sekunden)“
- p180 „Große Cullenect-Symbole in Bin-Labels werden noch verschoben“

## Stand je Punkt

| Punkt | Stand | Beleg |
|---|---|---|
| Untergrenze der Schrift | gemessen, siehe unten (947c1e0) | `tools/fontStroke.py` mit Tests; Messung in Fusion (`r17_font`) |
| p110 | umgesetzt (fd2c663): Zwei Zeilen werden auf die Unterlängen begrenzt, aber nicht unter die Untergrenze des Stils. Reicht das nicht, meldet die Prüfung das Problem und der Dialog sperrt OK. | pytest `TestDescenders`; E2E a (Heavy bündig/erhaben/vertieft), E2E b ALL OK |
| p140 | umgesetzt (08b3b88, e0d3bd8): Das Symbol hält bei „vertieft“ 0,4 mm Abstand vom Rand. | pytest `TestDebossedRim`; E2E c ALL OK |
| p52 | umgesetzt (f6dca88): 1 mm mehr Luft vor dem Symbol beim Einpassen. | pytest `TestTextFitWidth`; E2E d ALL OK (Lücke 1,816 mm nach −1 mm) |
| p51 | umgesetzt (4efb729): Die Hardware-Symbole sind gröber neu erzeugt, die Schrauben unverändert. | `--compare`: höchstens 0,041 mm; E2E e: Nylonmutter 2,83 s, Crimp-Ring 4,17 s |
| p180 | gemessen (fa3f9f4): Die Grenze bleibt bei 40 Punkten. | Messung `r17_dims`, siehe unten; pytest-Tabelle in `tests/test_bin_label_layout.py` |

**Untergrenze der Schrift:**
- Gemessen wurde an den Umrissen von A–Z, a–z und 0–9 bei 10 mm Texthöhe. Je Punkt der Kontur wird quer zum Strich
  gemessen, Ecken bleiben außen vor; der Wert ist das 1-%-Quantil.
- Dünnster Strich bei 10 mm Texthöhe:

| Stil | Strich | 0,4 mm ab |
|---|---|---|
| Regular | 0,903 mm | 4,43 mm |
| Bold | 1,170 mm | 3,42 mm |
| Heavy | 1,313 mm | 3,05 mm |

- Die Unterlänge ist bei allen drei Stilen 0,294 der Versalhöhe. Fusions Texthöhe ist die Versalhöhe.
- Das Review hat das Quantil hinterfragt. Die tieferen Quantile liegen deutlich darunter:
  - 0,5 %: 0,854, 1,055 und 1,121 mm;
  - 0,1 %: 0,75, 0,816 und 0,794 mm (Regular, Bold, Heavy).
  - Ob das echte dünne Stellen sind (Ansätze, Bogenenden), zeigt erst der Slicer, siehe Handtest 4.

**p51:**
- Die alte Auflösungszeile im Werkzeug hat nie gewirkt, weil `Cullenect.scad` in seinen Modulen `$fa = 1` setzt.
- Die neue Auflösung geht deshalb als Argument an `cullenect_hardware`: `$fa = 12, $fs = 0.2`. `$fs = 0.5` und `0.3`
  wichen bis 0,073 mm ab.
- Segmente vorher und nachher: Nylonmutter 1086 → 96, geschlossener Crimp-Ring 1372 → 120.
- Bauzeit vorher (`r17_time_*`): Nylonmutter 23,69 s, davon 14,56 s Import; Crimp-Ring 33,39 s.

**p180, Zeit zum Halten über Maße je Symbol auf einem Bin-Label:**
- unter 2 s: tnut-2 (26 Punkte, 1,30 s), tnut-1 (32, 1,77 s), nut-square (34, 1,75 s), nut (36, 1,92 s).
- darüber: magnet (50, 3,04 s), crimp-spade-open (57, 3,75 s), washer-locking (58, 4,33 s), washer (60, 4,45 s),
  crimp-fork-open (69, 6,18 s), crimp-receptacle-open (76, 6,29 s), threaded-insert (76, 5,55 s), crimp-ring-open
  (85, 7,5 s), crimp-spade-closed (96, 9,79 s), nut-nylon (96, 9,11 s), crimp-fork-closed (108, 12,84 s),
  crimp-receptacle-closed (115, 14,11 s), crimp-ring-closed (120, 15,19 s), crimp-butt-splice (122, 15,08 s).
- Weg: Bis 36 Punkte wird über Maße gehalten, ab 50 verschoben.
- Die Bin-Labels nutzen die Kopien `labelIcons/*/cullenect-*.svg`. Sie sind beim Neuerzeugen mitgeschrieben worden und
  byteweise gleich den Hardware-Symbolen, die Messung lief also schon auf den gröberen Symbolen.

## Snapshots neu abgelegt (Bedingung der Hauptsitzung: Ursache gewollt und belegt, Einleger-Grundkörper mit gleicher Bounding-Box)

Lauf `r17_snap` (83 Fälle): rot waren nur diese fünf Einleger-Fälle, alle mit Symbol.

| Fall | Ursache | Beleg |
|---|---|---|
| `label_2u_hardware` | p51 (gröbere Nylonmutter, 1340 → 350 Flächen) und p140 (Symbol 0,4 mm vom Rand) | Volumen 974,48 → 974,54 mm³ |
| `label_1u_screw_text`, `_colored`, `_part` | p52: Der Text ist auf die Breite eingepasst und bekommt 1 mm weniger | Raum 19,44 mm → 18,44 mm, Faktor 0,949; text 1 bis x 13,07 → 12,45 mm (0,953) |
| `label_25mm_free` | p52: „M3“ in Bold ist ebenfalls eingepasst, eine Schraube steht rechts daneben | Text 1,44–9,36 mm = 0,95 · 8,32 mm Raum; nachher 7,32 mm Raum, Faktor 0,88; Volumen text 1 5,43 → 4,21 mm³ (0,88² = 0,77). Der Grundkörper weicht um 2,5 mm³ ab, weil „bündig“ den kleineren Text aus ihm herausschneidet |

Die Fälle sind mit `r17_refresh` neu abgelegt. Die vorhandenen Vorschaubilder bleiben dabei erhalten. Dass die Bounding-
Box der Grundkörper gleich bleibt, ist im `git diff` der `fingerprint.json` geprüft:
- `label_1u_screw_text` (alle drei Varianten): 0..36 × 0..11 × 0..1,2 mm, gleich.
- `label_25mm_free`: 0..24,9 × 0..11 × 0..1,2 mm, gleich.
- `label_2u_hardware`: 0..78 × 0..11 × 0..1,2 mm, gleich.

Vorschaubilder gab es für die fünf Fälle keine, und die Test-Palette war zu. Danach war `r17_snap_t` für alle fünf Fälle
„pass“, der übrige Lauf (78 Fälle) bleibt grün aus `r17_snap`.

## Belege, Abschluss

- pytest: `779 passed`.
- Ende-zu-Ende (Stand `r17_reload2`): a, b, c, d, e, f und g sind alle ALL OK.
  - c: Abstand rechts, oben und unten je 0,400 mm bei der Schraube und 1,170 mm bei der Nylonmutter.
  - d: Abstand 1,816 mm.
  - f: Die Mutter wird über Maße gehalten, die Nylonmutter verschoben; beide bleiben an ihrer Stelle.
  - g: Der Crimp-Ring bleibt an seiner Stelle.
- Bauzeiten nachher: Nylonmutter 2,93 s (vorher 23,69 s), Crimp-Ring 3,04 s (vorher 33,39 s).

## Fragen an Jörg (Testtermin)

1. **Zweizeilig vertieft:** verbieten oder die Kerbe durch die Unterlängen hinnehmen?
   - Die Hauptsitzung hatte für die Unterlängen denselben Randabstand freigegeben und die Freigabe wieder
     zurückgezogen. Gebaut ist der Stand der Spec: Nur das Symbol hält Abstand.
   - Bei 11 mm Höhe enden die Unterlängen der unteren Zeile heute 0,22 mm über der Unterkante, also im Überstand von
     0,2 mm plus 0,2 mm.
   - Mit 0,4 mm Abstand müssten zwei Zeilen auf 3,27 mm schrumpfen. Regular hat 3,5 mm und eine Untergrenze von
     4,43 mm, Bold eine Untergrenze von 3,42 mm: Zweizeilig vertieft ginge dann in Regular und Bold gar nicht mehr, und
     Heavy scheitert bei −1 mm.
2. **Untergrenze bei langen Texten** (Rückfrage 1 der Planung): Die Breitenanpassung langer Texte behält den alten
   Hinweis aus p130 und sperrt nicht.
   - Das Review fand eine Lücke bei Heavy: Der Hinweis greift erst unter 2,79 mm, die neue Untergrenze liegt bei
     3,05 mm.
   - Soll der Hinweis der Untergrenze folgen?
3. **p52 ohne Symbol:** Ein Einleger ohne Symbol hat dasselbe Muster, bei −1 mm Breite reicht der Text an den rechten
   Rand. Nach der Spec nicht gebaut, gesammelt.
4. **Zwei Zeilen in Regular und Bold** werden ab etwa −0,45 mm bzw. −0,57 mm Höhenkorrektur gesperrt (Spec: „der Dialog
   sperrt OK“). Bisher wurden sie mit überstehenden Unterlängen gebaut.

## Review (Opus)

Kein kritischer Fund. Umgang:
- **Wichtig, behoben (53860a9):**
  - (1) Der Planhinweis zur Untergrenze war falsch; er ist berichtigt, und die Meldung nennt jetzt Unterlängen und
    Heavy.
  - (4) E2E c prüft den Symbolabstand oben, unten und rechts in beiden Fällen.
  - (5) E2E d verlangt den Symbolabstand statt nur > 0; der alte Stand hätte ihn mit etwa 0,97 mm nicht erfüllt.
  - (7) `--compare` scheitert, wenn es nichts verglichen hat.
  - Klein (1): Kommentar zu `DEBOSS_RIM` berichtigt.
  - Klein (6): Bold bei −1 mm hat einen Test.
- **Wichtig, nicht gebaut:**
  - (2) Siehe Frage 2.
  - (3) Siehe die Untergrenze oben und Handtest 4.
  - (6) Die Umlaute der oberen Zeile sind als neuer Punkt p210 auf der Liste. Geschätzt nach Arial-Maßen, nicht
    gemessen.
- **Klein, bleibt:**
  - (2) Siehe Frage 1.
  - (3) Kein Sicherheitsabstand unter den Unterlängen: Die Spec verlangt „≥ Unterkante“.
  - (4) Bei sehr schmalem Textraum prüft `MIN_TEXT_SPACE` den Raum vor Abzug der 1 mm Luft.
  - (5) Bin-Labels vergrößern Symbole mitunter, dann kann die Abweichung über 0,05 mm liegen.
  - (7) E2E f/g vergleicht die Lage des Symbols über Feature-Flächen.

## Handtest für Jörg (Testtermin)

1. Einleger 1U, zwei Zeilen „gjpy“/„Agjp“, Heavy, Höhenkorrektur −1 mm: Die Unterlängen bleiben im Einleger.
2. Dasselbe in Regular: Der Dialog meldet „Two lines don't fit this height …“ und sperrt OK.
3. Einleger 25 mm, Schraube, vertieft, drucken: Der Rand ist ringsum ganz, und der Einleger rastet ein.
4. Text in Heavy bei 3,05 mm und in Regular bei 4,43 mm Höhe in Bambu Studio (0,4-mm-Düse, Standardprofil, Arachne)
   ansehen: Bleiben Teile der Buchstaben leer? Das prüft die Untergrenze.
5. Einleger mit Nylonmutter bauen: in wenigen Sekunden. Das Symbol sieht gedruckt aus wie vorher.
6. Bin mit Label „Cullenect nut nylon“ und langem Text, danach den Text verlängern: Das Symbol bleibt an seiner Stelle.
