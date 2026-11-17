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
- Bilder der Box und der Magnetgrößen-Auswahl erst nach Runde 28 (Nutzer), Liste in `docs/assets/images/NEEDED.md`.

## Abweichungen von der Spec (Nutzer freigegeben, Wortlaut im Plan)

- Mindesthöhe 6 statt 5 („Mindesthöhe 6. vorerst.“). Höhe 5 ist p264, die Fälle dafür liegen in `dev-notes/box-height5-cases/`.
- Box-Magnete nur 6×2 plus Custom bis 2,6 mm („Box nur 6×2“).
- Bodenpolster und Stapelrand aus Kreisen statt Bögen („Ja, Formen-Weg“, „Versuche b“).

## Offen: Box-Bau scheitert an #42 Mirror6 seit dem langen Rebuild (Nacht 16./17.11.)

Seit etwa 00:53 bricht jeder Box-Bau über `boxBuilder.buildBox` nach #41 an „#42 Mirror6“ ab, mit „Mirror1 / Compute
Failed // FILLET_NO_EDGE_FOUND“. Betroffen waren `r27_render`, alle Box-Schritte von `r27_snap` und `r27_diag` V1. Bis
00:45 baute derselbe Weg zwei Boxen und einen Rebuild (`r27_cmd`). Eingrenzung mit `fusion-auftraege\r27_diag.py`,
Protokoll `r27_diag.log`:

| Lauf | Weg | Ergebnis |
|---|---|---|
| r27_steps | Generator direkt (wie bisher), jetziger Code | baut, alle Schritte gleich Pred |
| V1 | buildBox wie der Befehl | Fehler #42 |
| V2 | buildBox, Magnet-Optionen wie vor 0de77ce | Fehler #42 |
| V3 | Generator direkt, Hybrid | baut |
| V4 | Generator direkt, Container (activate griff nicht) | baut |
| V5/V6 | Zustand vor dem Generator: Parameter, Dims, Einheit, Lage gleich; nur bei buildBox ist die Satz-Komponente aktiv | – |
| V7 | Generator direkt, Komponente wirklich aktiv | baut |
| V8 | buildBox, Wurzel vor dem Generator aktiviert | Fehler #42 |
| V9 | buildBox aus dem Stand a1f99e7 (baute um 00:45) | Fehler #42 |
| V10 | buildBox, Satz-Occurrence wieder am Elternteil fest | Fehler #42 |

**Schluss (vorläufig):** Der Code ist nicht die Ursache. V9 scheitert mit genau dem Code, der um 00:45 baute.
Fusion war seit dem Rebuild-Lauf (`r27_cmd` Lauf 2, 7 min) in einem Zustand, der nur den buildBox-Weg trifft.
Kandidaten: Parameter mit Kommentar und Tags, Attribute, Container über `assembly`, Ereignis-Handler des laufenden
Add-ins. Fusion wurde neu gestartet, der Beleg steht aus: `r27_diag` mit State 1, also V1, als erster Lauf. Baut V1,
bleibt das als Beobachtung offen; tritt es nach einem langen Rebuild wieder auf, kommt es auf des Nutzers Testliste. Bricht
V1 wieder ab, geht die Eingrenzung im buildBox-Pfad weiter.

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
