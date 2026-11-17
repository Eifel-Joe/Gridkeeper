# Runde 29, Box-Schild (p262): Spec-Ergänzung und Plan

Auftrag: Schild für die Box nach Pred als **eigener Menübefehl** (Nutzer: „Letzteres wäre mir gut recht, weil man es so
besser auch mal austauschen könnte.“), kommt in Release 1.1.0 („Sonst ist die Box ja nicht komplett.“). Grundlagen:
Spec `dev-notes/specs/2026-11-16-pred-box-design.md` (Abschnitt Schild, Bauweise 3), Regeln `dev-notes/r29/README.md`.
Pflicht: jede Skizze vollständig bestimmt (Nutzer: „Denk nur dran, dass alle Zeichnungen vollständig bestimmt sein müssen.“).

Freigabe: Hauptsitzung 17.11.2026, alle Vorschläge 1–6.

Markierung: **[V]** = Vorschlag dieser Untersitzung zu einer offenen Gestaltungsfrage, Freigabe durch die Hauptsitzung
(oder auf des Nutzers Testliste).

## 1. Befund Preds Schild (gelesen, 5 × 4 × 6)

Aus `fusion-auftraege/pred_read*.out`, `pred_sketches.out`; Bauschritte genau aus `r29_walk/Label.json` und
`Label_M_Screws.json` (Lese-Job `r29_label_walk`, Abschnitt 6).

| | `Label` (leer) | `Label_M_Screws` |
|---|---|---|
| Zeitleiste | Sketch1, Extrude1, Chamfer1 | dazu Sketch3 (Text, 84 Kurven, nicht voll bestimmt), Extrude2 |
| Körper | `EmptyLabel` x 81,25 … 148,75, y 6,45 … 7,3, z 12,45 … 36,95 | y 6,05 … 7,3 (0,4 mm erhabene Schrift nach vorn) |
| Maße | 67,5 × 24,5 × 0,85 mm | 1,25 mm dick |

- Breite = `_LabelWidth` − 3 mm (Schildbreite der Box 70,5 mm bei X = 5, Platte 1,5 mm je Seite innen), Höhe 24,5 mm
  mittig auf der Box-Mittelhöhe (24,7 mm bei Höhe 6), Rückseite 0,2 mm vor der Schlitzwand (y 7,3 statt 7,5 mm).
- Halter (`predBoxGenerator.holders`): Lippen links/rechts decken die Platte 1,0 mm, die untere 1,0 mm, Ecken mit
  2,5-mm-Schräge; oben offen (das Schild wird von oben eingeschoben). Schlitz 1,25 mm tief (y 6,25 … 7,5).
- Erhabene Schrift liegt im offenen Fenster vor der Platte, gleitet zwischen den Lippen durch.

## 2. Spec-Ergänzung (Aufbau des Schilds)

Platte nach Preds Profil (Breite `labelWidth − 3 mm`, 24,5 mm hoch, 0,85 mm dick, Preds Fase), darauf:

```
┌──────────────────────────────────────────┐   Rand 2,5 mm rundum frei  [V]
│  ┌────────┐  ┌──────────────────────────┐ │
│  │        │  │ Zeile 1         (4 mm)   │ │   Zeilen: Versalhöhe 4 mm, schrumpfen auf Breite  [V]
│  │  M2    │  │ Zeile 2                  │ │
│  │ (≤12mm)│  ├──────────────────────────┤ │
│  │        │  │ ⚙ ⚙ ⚙ ⚙ ⚙   (6 mm hoch)  │ │   bis 5 Symbole, 1,5 mm Abstand, links bündig  [V]
│  └────────┘  └──────────────────────────┘ │
└──────────────────────────────────────────┘
   Feld links 35 % der Nutzbreite [V], 2 mm Spalt
```

- **Großes Feld links:** freier Text, eine Zeile, Versalhöhe bis 12 mm, schrumpft auf die Feldbreite (Messung wie bei
  den Einlegern, `_measureText`/`fittedLineHeight`). Leer ⇒ das rechte Feld nimmt die ganze Breite. **[V]**
- **Rechts zwei Zeilen**, darunter **bis zu fünf Cullenect-Symbole** in einer Reihe; je Symbol so hoch wie die Reihe
  (Seitenverhältnis bleibt). Passt die Breite nicht, entfallen Symbole von rechts, verkleinert wird nichts (Festlegung
  der Hauptsitzung); der Dialog zeigt, wie viele entfallen. Keine Zeilen ⇒ Symbole mittig in der Höhe; keine Symbole
  ⇒ die Zeilen mittig. **[V]**
- **Oberfläche** wie bei den Einlegern: erhaben (0,4 mm, wie Preds `Label_M_Screws`), vertieft (0,4 mm in die 0,85-mm-
  Platte) oder bündig; Text und Symbole als eigene Körper in einer Komponente `Text`, eigene Farbe (`labelColors`),
  Schriftstil (`textStyles`, Vorgabe Heavy wie die Einleger).
- **Keine Trennlinien** auf dem Schild (die Linien in der Skizze der Spec sind nur Aufteilung). **[V]**
- **Symbolauswahl je Platz:** eine Liste aus „None“, allen Hardware-Symbolen und den Schrauben (Maschinenschraube,
  Vollgewinde, ohne Flansch, ohne Sicherung; alle Kopf × Antrieb, die als svg vorliegen). Die volle Schrauben-Auswahl
  mit sechs Feldern wie im Einleger-Dialog wäre × 5 = 30 Felder. **[V]**
- **Skizzen:** Platte, Fase, Joint origin ohne lose Elemente; Text-Skizze wie beim Einleger: fixierte Grundlinien, Live-
  Text an Text-Parametern; Fusion meldet sie mit fixierten Grundlinien als voll bestimmt (Befund Runde 6); die
  Ausnahme p50 im Snapshot-Check bleibt nur Absicherung. Symbolskizzen: alle Kurven/Punkte fixiert (wie Einleger).

## 3. Befehl und Einbau

- Neuer Menübefehl **„Gridkeeper box label“** (`commands/commandCreateBoxLabel/`), Symbol und Dialog nach dem Vorbild
  „Gridkeeper label“: Gruppen *Box*, *Text* (Großes Feld, Zeile 1, Zeile 2, Stil, Oberfläche, Farbe), *Symbols*
  (5 Listen), *Preview*. Vorgaben merkt der Dialog wie die anderen (uiState).
- **Box:** Auswahl der Box (ein Körper der Box oder ihr *Label joint origin*). Mit Box: Breite aus deren Außenbreite
  (Vorbelegung der Auswahl), das Schild wird starr an den *Label joint origin* der Box gejointet. Ohne Box: Auswahl
  *Label width*, das Schild liegt frei neben den anderen Teilen (`placementUtils.findPlacement`).
- **Schildbreite als Auswahl** (Nachtrag 17.11.2026, Nutzer über die Hauptsitzung): „Die Schildbreite muss ich angeben
  können, da sonst ein Nachdruck nur möglich ist, wenn es auch eine Box im Dokument gibt. Aber es kann natürlich auch eine
  Breite übernommen werden, wenn man einen Joint auswählt zum positionieren.“ und „Da das Schild ja feste Breiten hat,
  sollte es nur ein Auswahlmenü dafür geben. Nicht frei einstellbar.“ ⇒ Dropdown **Label width** mit Preds festen
  Breiten: *Box 4 cells (28.5 mm)*, *Box 5 cells (70.5 mm)*, *Box 6+ cells (85 mm)* (Platte jeweils 3 mm schmaler),
  geht ohne Box im Dokument. Ein gewählter *Label joint origin* belegt den passenden Eintrag vor; passt die Auswahl
  danach nicht zur gewählten Box, sperrt der Dialog OK mit Hinweis. Ersetzt das Feld *Box width (cells)* unten.
- **Breite fest beim Bau** (Wert, kein Ausdruck auf die Box-Parameter): Text und Symbole werden beim Bau eingepasst,
  ein mitwanderndes Schild bekäme sie nicht neu gesetzt. Ändert sich die Boxbreite, wird das Schild neu erzeugt. **[V]**
- **Teil-Rahmen:** das Schild liegt in seiner Komponente **flach in Druckrichtung** (XY, Text nach +z), Mitte der
  Rückseite im Ursprung: Platte x −B/2 … B/2, y −12,25 … 12,25 mm, z 0 … 0,85 mm. *Label joint origin* am
  Komponenten-Ursprung (`originConstructionPoint`, keine Null-Bemaßung), Z = +y, X = +x. Damit steht es eingebaut
  richtig: +y → Box +z, +z (Text) → Box −y. Abweichung von Pred (dort stehend im Box-Rahmen); Grund: Druckrichtung
  für den Export, und die Breite wechselt mit der Box. **[V]**
- **Sitz an der Box** (gemeinsame Stelle, wird gemeldet): `predBoxSeats` bekommt den Sitz `Label` bei
  (Boxmitte x, 7,3 mm, Mittelhöhe), aufrecht, X entlang X; `seatJointOriginPoints` liefert ihn mit, die Box legt so
  *Label joint origin* an. Folge für die Integration: ein Joint origin mehr an jeder Box (Snapshots).
- **Komponente** `Gridkeeper box label …` im Container wie die Einleger (`assembly.partPlace`, Art „Labels“ oder eigene
  Art „Box labels“ – nach dem Bau des Befehls zu entscheiden, gemeldet), Text/Symbole in Unterkomponente `Text`.
  Körpername `Box label`, Text `Box label text N`, Symbole `Box label symbol N`.
- **Menü-Registrierung** in `commands/__init__.py` (gemeinsame Stelle, gemeldet).
- **Nicht in dieser Runde [V]:** Rebuild/Clone/Konfig-Datei per Rechtsklick wie bei den Einlegern (`configJson`,
  `rebuildUtils`); das Schild wird bei Bedarf gelöscht und neu erzeugt. Vorschlag neuer Listenpunkt (p370).

## 4. Dateien

| Datei | Inhalt |
|---|---|
| `lib/gridfinityUtils/predBoxLabelLayout.py` | Fusion-frei: Plattenmaße aus der Rasterzahl, Felder, Zeilen, Symbolreihe, Probleme |
| `lib/gridfinityUtils/predBoxLabel.py` | `createBoxLabel(input, component, *, name, origin, markingComponent, …) -> (plate, marking)` |
| `commands/commandCreateBoxLabel/{entry,inputState,boxLabelBuilder}.py`, `resources/` | Befehl |
| `lib/gridfinityUtils/predBoxSeats.py` | + Sitz `Label` (gemeinsam, gemeldet) |
| `commands/__init__.py` | + Befehl (gemeinsam, gemeldet) |
| `tests/test_pred_box_label_layout.py`, `tests/test_box_label_command.py`, `tests/test_pred_box_seats.py` | Tests |
| `fusion-auftraege/r29_label_walk.py`, `r29_label_check.py` | Lese-Job, Prüfjob |
| `docs/boxes.md`, `CHANGELOG-CULLENECT.md` (1.1.0) | Doku |

Wiederverwendet: `cullenectLabelGenerator` (`_texts`, `_fixSketch`, `_cutExtrude`, `_extrude`, `_offsetPlane`),
`labelGenerator` (`_measureText`, `_importIcon`, `_iconProfiles`), `cullenectLabelLayout.fittedLineHeight`,
`cullenectCatalog`, `labelColors`, `appearanceUtils`, `textStyles`, `assembly`, `placementUtils`.

## 5. Schritte (test-first)

1. `predBoxLabelLayout`: Tests für Plattenmaße (X = 4, 5, 6, 7 → 25,5 / 67,5 / 82 / 82 mm), Nutzfeld, Feldaufteilung,
   Zeilenlagen, Symbolreihe (Anzahl, die passt; entfallene), Probleme; dann Code.
2. `predBoxSeats`: Test Sitz `Label` (Lage bei 5 × 4 × 6 = (115, 7,3, 24,7) mm, wandert mit Breite/Höhe); dann Code.
3. `predBoxLabel` (Fusion): Quelltext-Tests (`ast`) für Pflichtteile: Plattenskizze voll bestimmt (Rechteck mit
   Bemaßungen wie `sketchUtils.createRectangle`), Fase wie Pred, Joint origin am Ursprung mit Achsen, Skizzen auf
   Ebenen/Flächen, kein Mirror; dann Code.
4. Befehl: Quelltext-/Zustandstests nach dem Muster `test_box_dialog.py`; dann Code; Registrierung.
5. Fusion-Prüfjob `r29_label_check.py` (neues Dokument, < 50 s je Lauf): Schild ohne Text gegen Preds `EmptyLabel` in
   unseren Rahmen geholt (Boole beidseitig, Rest ≤ 0,05 mm, Volumen auf 0,001 mm³), alle Skizzen `isFullyConstrained`,
   Schild mit Text + 5 Symbolen in allen drei Oberflächen, Zeitleiste gesund, Sitz im Halter einer gebauten Box 5 × 4 × 6
   (Schild an *Label joint origin* gejointet, Interferenz mit der Box = 0, Körper-Box = Preds `EmptyLabel`-Lage).
6. Review (Opus-Subagent) ohne offene Funde, Doku, Commit auf `r29-boxlabel`.

## 6. Preds Platte (r29_walk/Label.json, gelesen 17.11.2026)

- `Sketch1` (voll bestimmt): Rechteck 67,5 × 24,5 mm mit vier Eckbögen 3,5 mm (10 Kurven: obere und untere Kante in
  der Mitte geteilt). `Extrude1` 0,85 mm. `Chamfer1`: gleicher Abstand 0,2 mm, tangentiale Kette, Umriss vorn und
  hinten (16 Kanten). Volumen 1389,6464 mm³, 26 Flächen, 56 Kanten.
- Nachbau: `predSketch.WorldSketch.roundedRectangle` (createRectangle + vier gleiche Verrundungen, ein Radiusmaß), Fase
  über je eine Kante der Start- und Endfläche als tangentiale Kette.
- Symbolreihe 6 mm hoch (statt 7 mm im ersten Entwurf): bei 82 mm Breite passen so vier Schrauben-Symbole. **[V]**
