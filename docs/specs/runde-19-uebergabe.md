# Runde 19 – Übergabe

Stand 2026-11-16. Branch `runde-19`, abgezweigt von `runde-14-18` (976fd0f) und mit `runde-14-18` (6c1a32f, Ergänzung
p210) gemergt. Nicht gepusht, nicht gemergt.
- Spec: `docs/specs/2026-11-15-runde-19-design.md`. Die Hauptsitzung hat sie auf Jörgs Auftrag geschrieben, Jörg sieht
  sie beim Testtermin.
- Plan: `docs/plans/2026-11-16-runde-19.md`, von der Hauptsitzung freigegeben, mit diesen Antworten:
  1. Die Untergrenze bremst nur das Verkleinern für die Breite.
  2. Kein Nachführen über ein Ereignis in dieser Runde.
  3. Ein Text, der auch auf der Untergrenze nicht passt, wird nicht gebaut, die Meldung nennt ihn.

Punkte:
- p181 „Bin-Label-Text läuft beim Verlängern über den Bin-Rand“
- p210 „Einleger mit zwei Zeilen: Umlaut-Punkte der oberen Zeile ragen oben über den Rand“

## Option A geht nicht (Probe in Fusion, 16.11.2026)

- `r19_textheight` und `r19_textheight2`:
  - Ein Skizzentext hat einen eigenen Höhen-Parameter (`heightParameter`, „d3 5.00 mm“).
  - Gebunden an `probeH` = 7 mm wird der Text 7,0 mm hoch, mit `min(probeH; 6 mm)` 6,0 mm.
- `strlen`, `len`, `length` und `size`, angewandt auf einen Text-Parameter oder ein Literal, sind alle ungültig. Die
  Höhe kann der Textlänge deshalb nicht von selbst folgen, es gilt Option B.

## Stand je Punkt

**p181 (497317d, 6b0bd5f, Review-Funde):**
- Der Neubau per Rechtsklick passt einen seit dem Bau geänderten Label-Text neu ein, für Bin-Label und Fach-Labels.
  Bisher setzte er nur den Text-Parameter, oder er tat gar nichts, wenn der Parameter schon geändert war.
- Die Schrift wird für die Breite nicht unter die Untergrenze verkleinert. Passt der Text auch dort nicht, wird nichts
  gebaut, bei OK, Vorschau und Neubau. Die Meldung erscheint in der Fehleranzeige des Dialogs, zum Beispiel:
  „"Bolzen …" doesn't fit the label even at 3.4 mm, the least height a 0.4 mm nozzle prints. Shorten it or make the bin
  wider.“
- Beleg:
  - pytest (`fittedHeight`, `overflowProblem`, `textChangedSinceBuild`, `sharedText`);
  - E2E b: Höhe unverändert bei 7,736 mm;
  - E2E c: langer Text abgelehnt;
  - E2E a, e und f siehe Belege.

**p210: Nichts ragt über, es wurde nichts gebaut.** Messung `r19_umlauts` auf 4996e26:
- Oberkante von „ÄÖÜÅÉ“ je Texthöhe: Regular 1,2524, Bold 1,2613, Heavy 1,2647.
- Bei 0 mm reichen die Buchstaben bis 10,454 (Regular), 10,526 (Bold) und 10,569 mm (Heavy). Der Einleger ist 11 mm
  hoch.
- Heavy bei −1 mm: bis 9,811 mm, der Einleger ist 10 mm hoch.
- Regular und Bold bei −1 mm lehnt p110 ab.
- E2E d hält das fest: Umlaute mit 0,189 mm Luft, Unterlängen mit 0,000 mm.

## Review (Opus)

Kein kritischer Fund. Umgang:
- **Wichtig, behoben:**
  - (I1) Zwei Fächer zeigen das Bin-Label über je einen eigenen Parameter. Wird nur einer verlängert, ging die Änderung
    verloren. Jetzt gibt der geänderte Parameter den Text (`binLabelLayout.sharedText`, E2E f).
  - (I2) Bins aus Skripten oder alten Versionen haben im Tag keine Fächer. Der Dialog füllt leere ein, das galt als
    Textänderung und erzwang immer einen Neubau. Jetzt zählen nur gesetzte Fach-Labels je Zelle (Unit-Tests).
  - Klein (M1): Die Meldung bei einer Lasche, die niedriger ist als die Untergrenze, nennt jetzt die Lasche.
  - Klein (M3): Kommentare angepasst.
  - E2E e: Text im Dialog geändert, Bin ohne Farbe (der alte Parameter-Weg).
- **Wichtig, bewusst so, auf Jörgs Liste:**
  - (I3) Ein Bin, dessen Text früher unter die Untergrenze verkleinert gebaut wurde, lässt sich bei einem echten Neubau
    nicht mehr bauen, auch wenn der Text gleich bleibt. Ebenso eine Lasche, die niedriger ist als die Untergrenze, mit
    einem Text, der für die Breite kleiner werden müsste.
  - Das folgt aus der Entscheidung „wird nicht gebaut“. Reine Parameteränderungen, etwa die Höhe, sind davon nicht
    betroffen, sie setzen weiter nur Parameter.
- **Klein, bleibt:**
  - (M2) Die Ablehnung erscheint in der Fehleranzeige wie andere Eingabefehler, etwa die der Cullenect-Einleger.
  - (M4) Plan: Statt `noteOverflow` und Hinweis gibt es nach Antwort 3 die Ablehnung mit `overflowProblem`.

## Belege

- pytest: `910 passed`. Nach den Review-Funden ist ein neuer voller Snapshot-Lauf fällig (`r19_snap2`).
- Fusion (nach `r19_reload1`):
  - E2E b, c und d sind ALL OK.
  - `r19_snap` ist DONE, 83 Fälle, nicht grün `[]`.
  - E2E a scheiterte zweimal an den Testdaten, nicht am Code:
    - „Schrauben M4x2“ passt in ein Fach auch auf der Untergrenze nicht und wurde zu Recht abgelehnt.
    - „Bolzen“ war von der Lasche begrenzt, nicht von der Breite. Die Lasche begrenzt die Höhe der Buchstaben selbst:
      „Bolzen“ mit seinen Oberlängen kam auf 7,773 mm, „M3“ auf 7,736 mm. Die Schrift überragt die Lasche also nicht,
      der Vergleichswert aus Gruppe b passte nur nicht zu diesem Text.
    - Jetzt: „Muttern“ gegen „Mu“ (gleiche Buchstabenhöhe) im selben Dokument, verlängert zu „Muttern M4x2“.
    - Der Rest von a war schon grün: Die Buchstaben liegen in ihren Fächern, 7,773 → 4,385 mm, über der Untergrenze
      3,419 mm.
  - Nach den Review-Funden (`r19_reload2`): E2E e ALL OK (7,773 → 4,385 mm, neuer Text in beiden Fächern), E2E f ALL OK.

## Bekannte Grenze

Ändert man den Text nur über den Parameter, ohne neu zu bauen, kann er weiter über den Rand laufen. Eine Nachführung
beim Schließen des Parameter-Dialogs (`ui.commandTerminated`) wäre möglich, ist aber nicht gebaut: Sie liefe bei jeder
Parameteränderung und legte einen eigenen Undo-Schritt an. Das ist eine Frage an Jörg.

## Handtest-Liste und Fragen an Jörg

1. Bin 2x1 mit zwei Fächern, Label „Bolzen“, Bold. Den Text-Parameter in Fusion um „ M4x2“ verlängern, dann
   Rechtsklick und „Gridfinity rebuild“, OK: Die Schrift ist kleiner und liegt in jedem Fach auf dem Label.
2. Sehr langer Text im Bin-Dialog: Die Vorschau zeigt „failed“, OK meldet „… doesn't fit the label even at …“, es wird
   nichts gebaut. Frage: Reicht das, oder soll der Dialog OK schon vorher sperren? Das ginge nur über eine geschätzte
   Textbreite.
3. Frage: Soll die Schrift beim Ändern des Text-Parameters automatisch nachgeführt werden (siehe „Bekannte Grenze“)?
4. Ein alter Bin mit sehr kleiner Schrift (p130-Hinweis) wird nach dieser Version beim Neubau abgelehnt (I3). Ist das
   recht so?
