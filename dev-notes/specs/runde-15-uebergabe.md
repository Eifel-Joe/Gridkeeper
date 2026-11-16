# Runde 15 – Übergabe

Stand 2026-11-15. Branch `runde-15` (von `runde-14-18`), nicht gepusht, nicht gemergt. Spec
`dev-notes/specs/2026-11-15-runde-15-design.md` (von Jörg freigegeben), Plan `dev-notes/plans/2026-11-15-runde-15.md`
(121d8eb, von der Hauptsitzung freigegeben).
Punkte: p170 „Joint Origins an Bin-Füßen und Grundplatten-Aufnahmen folgen geänderten Rastermaßen nicht“, p60
„Cullenect-Taschen folgen einer geänderten Rasterbreite nicht ganz, wenn Fächer neben dem Raster liegen“, p101
„Rundung der hochgezogenen Trennwände bei Wänden ab 2 mm nicht ganz nahtlos“, p35 „Cullenect-Tasche bei sehr dünnen
Wänden im Druck prüfen“.

## Stand je Punkt

| Punkt | Stand | Beleg |
|---|---|---|
| p35 | umgesetzt (8918029): Cullenect erst ab 1,2 mm Wand, der Bin-Dialog sperrt OK und nennt den Grund in der Cullenect-Zeile der Maßtabelle; Konfiguration laden und Neubau per Rechtsklick öffnen denselben Dialog | pytest; E2E d ALL OK (1,2 / 2 / 3 mm bauen mit Tasche). Dialog nur von Hand prüfbar → Jörgs Testliste |
| p170 | umgesetzt (a0d2189): jeder Joint Origin eine Skizze mit treibenden Maßen, eine Ebene je Höhe, Namen unverändert | E2E a vorher 6 FAILED (20,75/62,75 mm bei 50 mm, Skizzen unbestimmt), nachher ALL OK |
| p60 | umgesetzt laut Spec (0351fc1): Spanne aus Lasche und Fach als `max()`/`min()`, auch Laschen-Hohlraum, seine Öffnungen und Label der geschalten Bin (Schwester-Pfade) | pytest; E2E b, c, e ALL OK; Symptom auf dem Ausgangsstand nicht nachstellbar (unten) |
| p101 | umgesetzt (452a47e Versuch A, a73e76c Versuch B, c4ace6a Review-Korrekturen): bei 2 und 3 mm Wand jede Ecke in zwei Abschnitten gesweept, kein Fillet-Ausweg, keine Reststufe, eine aufgesetzte Bin stößt nirgends an | E2E f (2 mm) vorher 4 FAILED (nur Fillets, Stufenflächen 0,18–0,70 mm² bei z 15,5), nach B ALL OK; nach dem Review f und g (3 mm) ALL OK mit Stapelprüfung |

## Belege

- **pytest:** `python -m pytest -q` → `726 passed` (Stand c4ace6a, nach den Review-Korrekturen).
- **Nach dem Review** (reload4 = c4ace6a): E2E f und g ALL OK (je 16 Sweeps, keine kleine waagerechte Fläche, eine
  aufgesetzte Bin ohne Durchdringung); die 7 Trennwand-Snapshot-Fälle wiederholt (`r15_snap_div1`–`4`): alle grün.
- **Ende-zu-Ende** `tests/e2e/runde15_grid.py`, Gruppen unter 50 s: a, b, c, d, e ALL OK (Stand reload1/reload2, die
  p101-Änderung betrifft sie nicht), f ALL OK (Stand reload3 = a73e76c). Vorher-Läufe auf dem Ausgangsstand: a 6 FAILED,
  b 0,0 mm³ (OK), f 4 FAILED. Ausgaben in `D:\Entwicklung\Gridfinity\fusion-auftraege\r15_*.out`.
- **Snapshot-Lauf** (`r15_snap`, 18 Häppchen, Stand a73e76c): 79 von 83 grün, rot nur die vier p30-Fälle
  (`bin_2x1x3_label_icon_text_embossed`, `bin_2x1x3_label_text_engraved`, `bin_2x3x5_features`,
  `bin_2x3x5_features_params_all`). Kein Snapshot neu abgelegt.

## Messungen

- **Bauzeit p170** (`r15_timing` / `r15_timing_after`, je Mittel aus 2 Läufen): Bin 4x2 5,01 s → 4,39 s; Grundplatte
  6x6 7,02 s → 9,69 s (+38 %, unter der 50-%-Grenze der Spec).
- **Taschenstufen p60** (`r15_span`, 4x2, 3 Fächer, frisch gebaut): bei 38/40/42/44/46 mm je Fach eine Einheit
  (32,3 / 34,3 / 36,3 / 38,3 / 40,3 mm breit), kein Stufensprung → Paar 42→40 wie in der Spec.
- **p60 auf dem Ausgangsstand** (`r15_e2e_b_red`): 42→40 mm per Parameter gegen frisch gebaut 0,0 mm³ (Cullenect und
  Text-Label). Das Runde-5-Symptom (0,02 mm³) zeigt sich auf `runde-14-18` nicht mehr. Nachgerechnet: Laschenanfang
  immer ≥ Fachanfang, das Ende kippt bei 3 Fächern in 4 Einheiten nur bei einer Laschenlänge um 1,290 Einheiten
  (Fenster 0,002). Der Ausdruck-Fix ist gebaut (Spec, Entscheidung 2), E2E e prüft zusätzlich den gemischten Fall.
- **Befund p101** (`r15_ledge`): Unter der Lippe ist die Wand bis z = 16,0 mm so dick wie eingestellt, darüber 1,9 mm:
  ein waagerechter Absatz von 0,1 mm (2 mm Wand) bzw. 1,1 mm (3 mm Wand). Die Kettenkanten jeder Ecke zerfallen daran in
  zwei Abschnitte, alle 8 Ecken gingen in den Fillet-Ausweg, bei 3 mm scheiterte der bis 1,08 mm Radius.

## p101 – Versuche

- **Versuch A** (452a47e): `raisedDividers.chainRuns` teilt die Kette, jeder Abschnitt eigener Sweep mit dem
  Eckquerschnitt an seinem unteren Ende, der obere um den Absatz versetzt (feste Abstände zu den parametrischen
  Größen). Ergebnis: 16 Sweeps, kein Fillet; 2 mm grün, bei 3 mm je Ecke eine Fläche von 0,594 mm² bei z 15,896.
- **Befund** (`r15_corner`): die Fläche zeigt nach unten und grenzt an die Fach-Eckrundung, die ungeschnitten bis
  16,0 mm reicht: der Fuß-Schnitt kürzte das untere Stück um 0,104 mm.
- **Versuch B** (a73e76c): nur der oberste Abschnitt einer Ecke bekommt den Fuß-Schnitt; unter dem Absatz kommt kein
  Fuß an der dicken Wand vorbei. Scheitert der Schnitt, bleiben keine losen Stücke. Ergebnis: E2E f ALL OK.
- E2E-Kriterium korrigiert (in a73e76c): gezählt werden nur die eigenen Eck-Fillets („Raised divider corner N fillet“,
  nicht der Fillet des Fuß-Schneidkörpers) und waagerechte Flächen < 1 mm² (Eckquerschnitt ≈ 0,7 mm²); der Wandabsatz
  entlang der Wand (3,9 mm² bei 2 mm) ist keine Stufe.

## Gesammelte Abweichungen

- Der Bin-Dialog lässt höchstens 2 mm Wand zu; 3 mm entstehen nur über Konfiguration bzw. Builder. Nicht geändert
  (Hauptsitzung 15.11.).

## Review (Opus)

Kein kritischer Fund. Umgang:
- **Wichtig, behoben (c4ace6a):** (1) Der untere Abschnitt unter dem Absatz wird nicht vom Fuß-Schnitt gekürzt, das
  Stapeln war ungeprüft → E2E f/g setzen eine schlichte Bin um 3 Höheneinheiten auf, `analyzeInterference` leer.
  (2) `chainRuns` nahm jeden zerfallenen Kantenzug als Absatz → Abschnitte nur, wenn der nächste auf der Endhöhe des
  vorigen und seitlich versetzt beginnt, sonst Fillet wie vorher (Tests: drei Abschnitte, loser Kantenrest,
  Höhenlücke ohne Versatz). (3) Schlug der letzte Fuß-Schnitt fehl, blieben die Schneidkörper in der Bin → entfernt.
  (4) Schlug das Vereinen fehl, wurden Ecken doppelt gefilletet und Stücke blieben lose → nur die vereinten Ecken,
  Stücke entfernt.
- **Klein, behoben:** (5) Skizze und Ebene eines gescheiterten Abschnitts bleiben nicht stehen. (6) Docstring.
  (7) Versatz als reine Funktion `raisedDividers.runOffset` mit Test auf den gemessenen 3-mm-Kanten.
- **Klein, bleibt:** (8) Ebenennamen der Joint Origins geändert, nichts sucht sie; Joint-Origin-Namen gleich.
  (9) Die 1,2-mm-Prüfung sitzt laut Spec nur im Dialog; Skripte, die den Builder direkt rufen, bauen dünnere Wände.

## Handtest für Jörg (Testtermin)

1. Bin-Dialog, Label-Stil Cullenect, Wand 1,1 mm: OK gesperrt, Cullenect-Zeile nennt „at least 1.2 mm“; 1,2 mm: OK frei.
2. Bin 4x2 und Grundplatte 3x3 mit Joint Origins, `gfBinN_baseWidth` bzw. die Grundplatten-Basisbreite auf 50 mm: die
   Joint Origins sitzen in den Zellmitten, ein Joint Bin–Grundplatte sitzt weiter.
3. Bin mit Trennwänden bis oben und 3 mm Wand (über eine Konfiguration): Ecken durchgehend gerundet, der kleine Absatz
   unter der Lippe gehört zur Wand.
