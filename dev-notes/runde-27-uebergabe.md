# Runde 27 – Aufbewahrungsbox nach Pred (p260) und Magnetgröße (p263)

Branch `runde-27` von `pred-box` (Spec 7523862) im Fork-Ordner, Ziel `master` des Forks. Plan mit allen Entscheidungen
und Abweichungen: `dev-notes/plans/2026-11-16-runde-27.md`. Spec: `dev-notes/specs/2026-11-16-pred-box-design.md`.

## Stand (belegt)

- **Gridkeeper box** baut Box und Deckel nach Preds parametrischer Storage Box v1.1 (Printables 543553, CC BY-NC).
  - Schrittvergleich 5×4×6 (`r27_steps`): alle 86 Schritte gleich Pred, nichts ungesund, alle Skizzen voll bestimmt.
    Der Bau dauert 56 s.
  - Maßvergleich 5×4×6 gegen Preds unberührten Export (`r27_pred6`, `r27_compare`): BESTANDEN. Die größte kleinste
    Ausdehnung eines Restkörpers ist 0,0000 mm.
    - Base 276676,62 mm³, Pred 276676,35. Der Unterschied sind Preds 0,0001 mm tiefe Magnetlöcher.
    - Lid gleich.
  - Parameterwechsel 5×4×6 → 7×5×10 folgt genau (`r27_params`/`r27_diff`).
  - Befehl ohne Dialog (`r27_cmd`):
    - Struktur Boxes › Satz › Box/Lid, Parameter `gfBoxN_*`, Tags und Joint origins stimmen.
    - Das Gelenk „Lid on box“ ist gesund.
    - Stapeln per Joint origins funktioniert: Satz 2 steht 55 mm höher, der Stapelrand übergreift 1,5 mm.
- **Magnetgröße (p263)** ist in Bin, Baseplate und Box wählbar. Nur die Tiefe wird gespeichert, alte Einstellungen laden
  unverändert.
- **Rebuild** löscht die alte Gruppe einzeln mit dem Marker dahinter (5137df6).
  - Vorher rechnete Fusion nach jedem gelöschten Element alles Spätere neu. Der Rebuild einer Box mit einer gestapelten
    zweiten dahinter dauerte damit 23 min statt etwa 2.
  - Gegenprobe Bin mit eingejointetem Einleger (`r27_regress13` = `tests/e2e/runde13_assembly.py`): ALL OK.
- **Opus-Review** über den ganzen Branch, alle Funde behoben (0de77ce):
  - Der Bin-Dialog öffnete nach p263 nicht mehr (verdeckter Modulname).
  - Das Baseplate-Tiefenfeld folgte der Magnetgröße erst nach einer Änderung.
  - Die Box-Bodenpolster hingen ohne Magnete am Durchmesser.
  - Box-Rebuild mit Parametern außerhalb der Drehfeld-Grenzen.
  - Marker im Fehlerfall nicht wieder am Ende.
- `python -m pytest -q`: 1093 grün, 1 rot (`test_every_snapshot_has_its_settings`, die Box-Snapshots fehlen noch). `mkdocs build --strict` sauber.
- Bilder der Box und der Magnetgrößen-Auswahl erst nach Runde 28 (Jörg), Liste in `docs/assets/images/NEEDED.md`.

## Abweichungen von der Spec (Jörg freigegeben, Wortlaut im Plan)

- Mindesthöhe 6 statt 5 („Mindesthöhe 6. vorerst.“). Höhe 5 ist p264, die Fälle dafür liegen in `dev-notes/box-height5-cases/`.
- Box-Magnete nur 6×2 plus Custom bis 2,6 mm („Box nur 6×2“).
- Bodenpolster und Stapelrand aus Kreisen statt Bögen („Ja, Formen-Weg“, „Versuche b“).

## Gelöst: Box-Bau scheiterte an #42 Mirror6 (16./17.11.)

Jeder Box-Bau über `boxBuilder.buildBox` brach nach #41 an „#42 Mirror6“ ab (`FILLET_NO_EDGE_FOUND`), auch nach
Fusion-Neustart; der Generator direkt baute. Eingrenzung in `fusion-auftraege27_diag.log` und `r27_diag2.log`:

- Maße, Parameter, Lage und Optionen sind in beiden Wegen gleich. Ohne Erdung des Containers oder ohne Parameter-Tags
  baute buildBox, mit beiden nicht (V3, V4, V5, V6). Kanten und Fasen-Zweige sind in beiden Fällen gleich (V7, V8).
- Mirror6 kippt auf Kleinigkeiten: Ohne irgendeins von sechs der zehn gespiegelten Features baut er (V7). Fusions
  Standard-Compute-Typ Adjust scheitert, Identical und Optimized bauen (V9 bis V11).
- Fix 1, Identical (824dad7): `r27_compare` bestanden, `r27_cmd` mit einem Design-Attribut scheiterte wieder.
- Fix 2, Weg A (Jörg: „Ja, A bauen“, 69c0e59): rechte Griff- und Schildhalter als Gegenstück mit gespiegelten
  x-Koordinaten und Kantenauswahlen, kein Mirror6 mehr. Spec-Nachtrag „Bauweise“.
- Dabei gefunden (`r27_diag3.log`, ca5173e): Fusion legt einen Bogen mit negativem Sweep mit vertauschten Enden an,
  die gespiegelte Schiene war überbestimmt. Bögen werden jetzt immer gegen den Uhrzeigersinn gezeichnet.
- Ergebnis mit ca5173e: `r27_compare` bestanden (Restkörper 0,0000 mm, Volumen wie zuvor), `r27_cmd` beide Läufe OK
  mit Design-Attribut, Rebuild 6×4×7 in 413 s. Preds Mirror1 bis 4 bleiben Spiegelungen (Identical) und hielten mit.

## Offen

- Zweite Box im selben Dokument baut etwa doppelt so lange wie die erste (77 s / 165 s). Ursache nicht untersucht.
- **Rebuild mit einer gestapelten Box dahinter dauert 430 s** (`r27_cmd` Lauf 2, Box 1 5×4×6 → 6×4×7).
  - Belegt ist nur die Summe. Die Aufteilung ist aus dem Code abgeleitet, nicht gemessen:
    - Neubau des Satzes etwa 75 s.
    - `replaceBodies` rollt den Marker zu jedem späteren Feature mit Körper-Eingaben, auch wenn es keinen alten Körper
      nutzt. Das ist ein voller Durchlauf durch Box 2.
    - Löschen der alten Gruppe, dann einmal `moveToEnd`: ein zweiter Durchlauf.
  - Möglicher Gewinn um einen Durchlauf: Erst die Eingaben lesen, nur bei einem Treffer `rollTo`. Das betrifft den
    gemeinsamen Rebuild-Code von Bin, Baseplate und Einleger, also eigene Runde mit Test.
- Kleinteile (Verschlüsse, Scharniere, Griff) Runde 28 (p261), Schild Runde 29 (p262).

## Fallen

- Preds Datei findet nach dem Rückweg Höhe 6 → 5 → 6 nicht ganz zu ihrem Stand zurück (Base 276676,02 statt ,35): Für
  den Vergleich immer einen unberührten Export nehmen (`r27_pred6`).
- Fusion-Läufe, die zwei Boxen bauen, brauchen 4 min und mehr, weit über die ~60 s des MCP. Sie laufen trotzdem durch,
  das Ergebnis steht dann im `.out`.
- Bash-Heredocs verstümmeln `\b` und `'''`; Skripte mit dem Write-Werkzeug schreiben.

## Nächste Schritte (morgen früh, mit Fusion)

1. `fusion-auftraege\r27_diag.py` einmal (State 1 = V1, buildBox wie der Befehl). Muss bauen.
2. `fusion-auftraege\r27_snap.py` 15-mal, je ein Job (State 0): 10 Box-Fälle und 2 Fälle 6×3 ablegen und prüfen, 3 alte
   Magnet-Fälle nur prüfen. Die Fälle bin_2x1x3_magnets_3mm und baseplate_2x2_light_magnets_3mm haben Restläufe der
   Nacht schon abgelegt (nicht committet), Schritt 11/12 legt sie neu ab.
3. Snapshots per `git diff` sichten und committen, pytest grün.
4. PR-Text (Entwurf bei der Hauptsitzung) mit den Ergebnissen füllen, Push `runde-27`, PR gegen `master`, CI prüfen.
