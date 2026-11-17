# Plan Runde 29, Scharniere (Branch `r29-hinge`)

Auftrag `dev-notes/r29/hinge.md`, Regeln `dev-notes/r29/README.md`. Reihenfolge M3x30, Pinned, Plain.

## Was Preds Schritte ergeben (aus `r29_walk/*.json`, Teil-Rahmen, mm)

Alle drei Varianten haben dieselbe Grundform; Achse des Gelenks entlang z bei (cx | 0), cx 0 (M3x30, Pinned) bzw.
−67,4662 (Plain). Länge L 31,6, Drittel s = (32 − 2 × 0,15) / 3 = 10,5667, Spalt t 0,15.

- **Querschnitt** O: U aus zwei Laschen (Stärke 1,6 bzw. 1,8, Höhe 8,8 bzw. 8,5) und Steg y 0,15 … 2,5 mit Fasen-Ecken.
  Dazu Kreise: Auge R_k (4 bzw. 3,5), Freiraum R_c (4,15 bzw. 3,725), Kern R_p (1,75 bzw. 2), bei Plain Loch R_h 2,15.
- **Körper vor der Teilung** = (O ∪ Auge) × [0, L], davon ab:
  - Freiraum-Ring R_k … R_c links der Achse für z ∈ [0, s + t] und [L − s − t, L], rechts für [s, L − s];
  - zwei Spalte (Ring R_p … R_c) für z ∈ [s, s + t] und [L − s − t, L − s];
  - Plain zusätzlich der Lauf-Spalt R_p … R_h für z ∈ [s, L − s] (Mittelauge dreht um den Kern).
  Bottom… = linke Lasche mit Mittelauge, Top… = rechte Lasche mit den beiden Außenaugen.
- **Rastnasen** (HingeTabDetails/Extrude14, Chamfer1 1,2, Chamfer2 1,3, Mirror2/3): vier gleiche Nasen 1,3 hoch auf den
  Laschen-Außenseiten, y 3 … 5,6, z 20,9 … 26,7 und gespiegelt 4,9 … 10,7.
- **M3x30:** Sechskant SW 5,5 z 28,1 … L, Schraubenloch R_p z 0 … 28,1 (teilt die Körper), Senkung d 5,5 bis z 3,9,
  zwei Brückenlagen 0,2 / 0,4 (Sketch5), Fasen 1,5 (Laschen-Enden oben), 1,0 (Laschen unten), 0,5 (Kantenzug).
- **Pinned:** Loch d 4,5 ganz durch (teilt), Senkungen d 5,5 je 3,9 tief an beiden Enden mit Fase 0,5; keine
  Laschenfasen. Stift „Hinge pin“: Köpfe d 5,1 je 3,3, Schaft d 4,1, Fasen innen 0,5, Kopffase 1,5 radial × 2,5 axial,
  Schlitz 1 × 7,5, Abflachung y > 1,5819 ganz, y < −1,5819 nur am Schlitz, Rundung r 0,5 im Schlitzgrund.
- **Plain:** Fasen 1,5 / 1,0 / 0,5 wie M3x30 (Chamfer3/5/6), kein Loch (Kern gehört zum Top).

## Bauweise

- `lib/gridfinityUtils/predHinge.py`: `createHinge(component, hinge)`; eine Tabelle `HingeShape` je Variante (cx, Maße
  oben), **eine** Funktion für die Grundform, die Extras je Variante als eigene kleine Funktionen.
- Jede Skizze mit `WorldSketch` (voll bestimmt durch `sketchChain`), auf den Grundebenen oder deren Versatz-Ebenen
  (keine Skizzen auf Flächen nötig). Jede Form bekommt möglichst eine eigene Skizze mit einem Profil (Ring-Hälfte aus
  zwei Viertelbögen je Radius, Spalt-Ring, Sechskant, Nase als Achteck). Wo eine Skizze mehrere Profile hat, Auswahl
  über Fläche bzw. Schwerpunkt-Regel (Brückenlagen).
- Längen: Preds „bis Fläche“-Grenzen werden feste Abstände (es gibt keine Benutzerparameter).
- **Keine Feature-Spiegelung.** Preds Mirror2/3/4 als Gegenstücke direkt gebaut:
  - Nasen: Chamfer1 (Ecken im Querschnitt der Nase) wird zum Achteck-Profil der Nase, so braucht es dafür keine Fase;
    Chamfer2 (1,3 an der Außenkante oben) als eine Fase über die vier Nasen, Kanten per Koordinaten gewählt.
  - Pinned Mirror4: zweite Senkung + Fase am anderen Ende direkt.
  - Begründung: Mirror6-Lehre (R27), Fasen in Spiegel-Features rechneten je nach Dokumentzustand anders.
- Fasen sonst als Fasen, Kanten über ihre Geometrie aus Preds Kantenlisten (Teil-Rahmen), Fehler bei fehlender Kante.
- Stift (Pinned) als Drehteil: ein voll bestimmtes Halbprofil auf XZ (mit Kopffase 1,5 × 2,5 und den Innenfasen
  0,5), Revolve um die z-Achse; dann Schlitz/Abflachungen als Schnitte, Rundung r 0,5 per Kantenwahl. So gibt es bei
  der Zwei-Abstände-Fase keine Richtungs-Zweideutigkeit.
- Körpernamen wie Pred; Rückgabe in Preds Reihenfolge (Bottom, Top[, Hinge pin]).

## Gemeinsame Werkzeuge

Voraussichtlich keine Änderung. Falls `WorldSketch` einen Helfer braucht (z. B. Profilwahl nach Schwerpunkt und
Fläche zugleich), wird er ergänzt, nicht umgebaut, und gemeldet.

## Prüfung

- pytest (`tests/test_pred_hinge.py`): Querschnitt, Ring-/Spalt-Lagen, Nasen-Achteck, Sechskant, Stift-Halbprofil
  (Volumen nach Pappus = Preds 444,2207 vor den Schnitten), jede Skizze per `sketchChain.rank` voll bestimmt; Quelltext
  per `ast` (Namen, keine `mirrorFeatures`).
- Fusion je Variante `r29_hinge_check.py` (Muster `r29_pin_check`): neues Dokument, `createHinge`, `.f3d` als Gegenprobe
  ins selbe Dokument, Boole beide Richtungen (Rest ≤ 0,05 mm), Volumen je Körper auf 0,001 mm³, Körper-Box, alle
  Skizzen voll bestimmt, Zeitleiste gesund, keine Benutzerparameter, Laschen-Maße gegen die Schlitze.
- Vorab **`r29_hinge_probe.py`** (nur lesen, < 20 s): Preds fertige Körper aus den `.f3d` — Stirnflächen mit Kanten
  und Innen/Außen an Probe-Punkten. Grund: Preds Kantenliste für die 0,5-Fase nennt an z 0, s, L − s, L einen Bogen r 4
  zwischen rechter Lasche und Außenauge, den meine Lesart der Schritte nicht als Kante hätte.
  **Ergebnis (17:45, `r29_hinge_probe.log`):** Stirnflächen sind verschmolzen; der Bogen ist der Rand des Auges,
  als langer Bogen von der Stegoberkante um das Auge herum bis zur Steg-Unterkante. Die Lesart oben gilt.
- Review per Opus-Subagent ohne offene Funde, dann Commit auf `r29-hinge`.
