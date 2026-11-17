# Plan Runde 29, Griff (`predHandle`)

Auftrag `handle.md`, Regeln `README.md`. Vorlage `fusion-auftraege/r28_handle_build.py` (Volumen gleich Preds bei
H 49,5 und 56,75, l5).

## Modul `lib/gridfinityUtils/predHandle.py`

- `profile(halfWidth: Dim)`: reine Geometrie, Fusion-frei. Das halbe Profil wie in der Vorlage als Weltpunkte
  (x, 0, z) in cm, die x-Werte als Dims auf H:
  - Arm −H … −H + 7, z 3,5 … −11,5; Bögen r8 und r15 um (−H + 15 | −11,5); Steg bis x = 0, z −19,5 … −26,5.
  - 8 Kurven: 6 Linien, 2 Bögen.
- `createHandle(component, halfWidth: str) -> [BRepBody]`:
  - H = Dim(Wert aus `unitsManager.evaluateExpression`, Ausdruck `halfWidth`, EXPRESSION).
  - **Profil-Skizze** „Handle profile“ auf XZ über `predSketch.WorldSketch` (Kette aus `sketchChain`). Damit ist sie
    voll bestimmt nach dem Muster aus Runde 27. Alle Maße mit x hängen als Ausdruck an H, auch die Abstände zur Mitte
    (`H - 15 mm`). Die Vorlage nahm Tangenten und eine Hilfslinie; Tangenten verbietet die Kette.
  - **Features wie in der Vorlage:**
    - Extrude 7 mm symmetrisch.
    - Fillet r3,5 an den 2 oberen Armkanten, Fase 1 mm an 14 Kanten. Die Kanten wählt der Code nach Koordinaten mit
      dem Wert von H aus, so wie die Vorlage.
    - Bohrung d3,5: Schnitt durch alles, symmetrisch, nur am Griffkörper.
    - Körper-Spiegelung an YZ mit combine. Das ist eine Körper-, keine Fasen-Spiegelung.
  - **Bohrungsskizze** „Pin hole“, *Abweichung von der Vorlage:* auf der YZ-Ebene statt auf der Armfläche.
    - Der Kreis sitzt deckend auf dem Skizzen-Ursprung, dazu ein Durchmessermaß. Das ist voll bestimmt, ohne
      Flächenwahl und ohne Projektion.
    - Der Schnitt läuft durch alles, symmetrisch, entlang X. Er trifft nur den Arm, den Steg nicht (Bohrung bei
      z = 0, Steg bei z ≤ −19,5). Die Form bleibt dieselbe; der Fusion-Vergleich belegt das.
  - Joint origin „Handle joint origin“ am Komponenten-Ursprung, Achsen wie die Komponente. Ein Körper `Handle`.

## pytest (zuerst, rot)

`tests/test_pred_handle.py`:
- Profil: die Punkte der Vorlage bei H 49,5 und 28,5. Fläche 472,9491 mm² (Pred) aus Linien und Bögen.
- Kette: `sketchChain.chain` plus `rank` gleich der Variablenzahl. Kein Nullmaß, keine Tangente; alles voll bestimmt.
- Jedes Maß mit x-Anteil enthält den Ausdruck von H.
- Quelltext (`ast`):
  - `addWithoutEdges` oder Basis-Ebene, keine Feature-Spiegelung von Fasen oder Rundungen.
  - Mirror nur mit dem Körper; Name `Handle`, Joint origin `Handle joint origin`.
  - Keine `userParameters`.

## Fusion-Job (über die Hauptsitzung)

`fusion-auftraege/r29_handle_check.py`, Code aus diesem Worktree. Je Lauf eine Größe (Zustandsdatei), unter 50 s.
1. Preds Archiv `r27_tmp/r27_pred_kopie.f3d` in ein neues Dokument importieren, Größe setzen (Lauf 1: 5 × 4 × 6,
   Lauf 2: 7 × 5 × 10). `Handle:1` als Temp-Körper in den Teil-Rahmen holen:
   - Verschiebung = Mitte in x und y, z = oberste Kante − 3,5 (Sitz laut `predBoxSeats`, Test
     `test_the_handle_seat_is_the_middle_of_preds_handle_on_the_pin_axis`).
   - Danach das Dokument schließen.
2. Ein neues Dokument (Hybrid) anlegen.
   - Als Box-Ersatz die Benutzerparameter `gfBox1_baseWidth/Length/heightU` anlegen; das sind keine des Teils.
   - Eine neue Komponente, darin `createHandle(comp, handleHalfWidth(dims).expression)`.
3. Prüfen:
   - Boole-Differenz in beide Richtungen, Rest ≤ 0,05 mm, Volumen auf 0,001 mm³.
   - Jede Skizze `isFullyConstrained`, Zeitleiste gesund, keine Benutzerparameter in der Komponente.
4. Die Breite über `gfBox1_baseWidth` = 4/5/6/7 umstellen.
   - Erwartet: Breite der Körperbox 57/99/113,5/113,5 mm, Zeitleiste gesund, Skizzen voll bestimmt.
5. `resources/predBox/handle.f3d` ins selbe Dokument importieren.
   - Gegenprobe: Joint origin dort an Ort, mit Achsen wie unserer.
   - Dazu Boole gegen den importierten Griff, nur als Bericht.
