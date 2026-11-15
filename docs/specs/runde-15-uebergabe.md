# Runde 15 – Übergabe (Zwischenstand)

Stand 2026-11-15. Branch `runde-15` (von `runde-14-18` 629e85e…fba00ef), nicht gepusht. Spec
`docs/specs/2026-11-15-runde-15-design.md` (von Jörg freigegeben), Plan `docs/plans/2026-11-15-runde-15.md`
(121d8eb, von der Hauptsitzung freigegeben).
Punkte: p170 „Joint Origins an Bin-Füßen und Grundplatten-Aufnahmen folgen geänderten Rastermaßen nicht“, p60
„Cullenect-Taschen folgen einer geänderten Rasterbreite nicht ganz, wenn Fächer neben dem Raster liegen“, p101
„Rundung der hochgezogenen Trennwände bei Wänden ab 2 mm nicht ganz nahtlos“, p35 „Cullenect-Tasche bei sehr dünnen
Wänden im Druck prüfen“.

## Stand je Punkt

| Punkt | Stand | Beleg |
|---|---|---|
| p35 | umgesetzt (8918029): Cullenect erst ab 1,2 mm Wand, der Bin-Dialog sperrt OK und nennt den Grund in der Cullenect-Zeile der Maßtabelle; Konfiguration laden und Neubau per Rechtsklick öffnen denselben Dialog | pytest; E2E d ALL OK (1,2 / 2 / 3 mm bauen mit Tasche). Dialog selbst nur von Hand prüfbar → Jörgs Testliste |
| p170 | umgesetzt (a0d2189): jeder Joint Origin eine Skizze mit treibenden Maßen, eine Ebene je Höhe | E2E a vorher 6 FAILED (20,75/62,75 mm bei 50 mm, Skizzen unbestimmt), nachher ALL OK |
| p60 | umgesetzt laut Spec (0351fc1): Spanne aus Lasche und Fach als `max()`/`min()`, auch Laschen-Hohlraum, seine Öffnungen und das Label der geschalten Bin (Schwester-Pfade) | pytest; E2E b/c/e ausstehend |
| p101 | Versuch A im Code (nicht committet bis E2E f): Kette in Abschnitte, jeder Abschnitt eigener Sweep | E2E f ausstehend |

## Messungen

- **Bauzeit p170** (`r15_timing` / `r15_timing_after`, je Mittel aus 2 Läufen): Bin 4x2 5,01 s → 4,39 s; Grundplatte
  6x6 7,02 s → 9,69 s (+38 %, unter der 50-%-Grenze der Spec).
- **Taschenstufen p60** (`r15_span`, frisch gebaut, 4x2, 3 Fächer): bei 38/40/42/44/46 mm je Fach eine Einheit
  (32,3 / 34,3 / 36,3 / 38,3 / 40,3 mm breit), kein Stufensprung → Paar 42→40 wie in der Spec.
- **p60 auf dem Ausgangsstand** (`r15_e2e_b_red`): 42→40 mm per Parameter gegen frisch gebaut: 0,0 mm³ Unterschied,
  Cullenect und Text-Label. Das Symptom aus Runde 5 (0,02 mm³) zeigt sich auf `runde-14-18` nicht mehr. Nachgerechnet:
  der Laschenanfang ist immer ≥ dem Fachanfang, das Ende kippt bei 3 Fächern in 4 Einheiten nur bei einer
  Laschenlänge um 1,290 Einheiten (Fenster 0,002). Der Ausdruck-Fix ist trotzdem gebaut (Spec, Entscheidung 2).
- **Befund p101** (`r15_ledge`): Unter der Lippe ist die Wand bis z = 16,0 mm so dick wie eingestellt, darüber 1,9 mm
  (Lippe): ein waagerechter Absatz von 0,1 mm (2 mm Wand) bzw. 1,1 mm (3 mm Wand). Die Kettenkanten jeder Ecke zerfallen
  daran in zwei Abschnitte, alle 8 Ecken gingen in den Fillet-Ausweg, bei 3 mm scheitert der bis 1,08 mm Radius
  (ASM_BL_CAP_COMPLEX).

## p101 – Versuche

- **Versuch A** (im Code): `raisedDividers.chainRuns` teilt die Kette in Abschnitte (pytest mit den gemessenen Kanten
  der 3-mm-Wand). Jeder Abschnitt wird mit dem Eckenquerschnitt an seinem unteren Ende gesweept; der obere Querschnitt
  liegt um den Absatz versetzt und um die Absatzhöhe höher, beides als feste Abstände zu den parametrischen Größen.
  Foot-Cut je Abschnitt, eine Ecke kommt nur ganz hinein. Prüfung: E2E f.

## Offene Aufträge (Fusion)

In dieser Reihenfolge, ohne Reload bis zum markierten Schritt: `r15_e2e_b`, `r15_e2e_c`, `r15_e2e_e`, `r15_e2e_f_red`,
dann `r15_reload2`, dann `r15_e2e_f`. Danach der Snapshot-Lauf `r15_snap` (wiederholen bis DONE).

## Gesammelte Abweichungen

- Der Bin-Dialog lässt höchstens 2 mm Wand zu; 3 mm entstehen nur über Konfiguration bzw. Builder. Nicht geändert
  (Hauptsitzung 15.11.).
