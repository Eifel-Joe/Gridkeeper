# Plan r29-export (Spec: dev-notes/specs/2026-11-17-r29-export-drucklage.md)

Einheit in `lib/printLayout.py` ist mm, wie in `threeMf.MeshObject`. Erst kommt der RED-Test, dann der Code, danach
die volle Suite (`python -m pytest`). Commits auf Englisch, einer pro grünem Task.

- [x] **T1 Drehregeln** – `tests/test_print_layout.py`
  - RED: `printRotation(role, bodyName, surface)` liefert 'none' für Bin, Baseplate, Box, Lid, Latch, Handle pin und
    die Hinge-Hälften. 'x+90' für Handle, 'x-90' für den Pinned-`Hinge pin`, 'x180' für ein Label oder Box-Schild mit
    `Flush`, 'none' für Embossed/Debossed. `rotated(vertices, rotation)` dreht richtig: ein Quader 10×20×30 hat nach
    'x+90' die Maße 10×30×20.
  - GREEN: `lib/printLayout.py`.
- [x] **T2 Verteilen** – `arrange(footprints, bed, spacing, purge)` liefert je Teil (Platte, x, y, gedreht).
  - RED, je Fall ein Test:
    - Alles passt auf eine Platte, mit Abstand zueinander und zum Rand.
    - Was nicht passt, kommt auf Platte 2.
    - Ein Teil passt nur gedreht: 90° um Z.
    - Ein Teil ist größer als das Bett: eigene Platte, Hinweis.
    - Die Purgetower-Ecke hinten rechts bleibt auf jeder Platte frei, ohne Bemalung nicht.
    - Ein einzelnes Teil liegt in der Bettmitte.
  - GREEN: Regalverfahren, die größten Teile zuerst.
- [x] **T3 Gruppen und Platzieren** – `layOut(groups, bed, spacing, purge)` auf `MeshObject`-Gruppen.
  - RED:
    - Jede Gruppe steht auf z=0.
    - Die Scharnierhälften einer Gruppe behalten ihre Lage zueinander.
    - Platte i liegt im Bambu-Gitter: x + (i % cols)·W·1,2, y − (i // cols)·D·1,2, cols = ⌈√n⌉.
  - GREEN.
- [x] **T4 Plattendaten in der 3MF** – erst nach dem Ergebnis der Plattenprobe (`notizen/r29-export-probe`).
  - RED: `threeMf.write` schreibt die Platten nach dem Format, das die Probe belegt. Bei einer Platte bleibt die Datei
    wie heute.
  - GREEN. Geht die Probe nicht auf: Nutzer fragen, Ausweg wäre eine Datei je Platte.
  - **Umgesetzt anders:** Die Probe ging nicht auf, Nutzer hat „eine 3MF je Platte“ gewählt (siehe Spec). Das
    Bambu-Plattengitter aus T3 ist entfallen. Stattdessen wird der Inhalt jeder Platte zentriert, und
    `threeMf.write(..., isLaidOut=True)` schreibt eine Datei je Platte.
- [x] **T5 Export-Befehl** (`commands/commandExport/entry.py`). Fusion-Teile werden mit Stub-Tests geprüft, soweit
  `tests/stubs` reicht.
  - Rolle eines Teils:
    - Satzteile über `partRoleOf`.
    - Box und Lid ohne Satz über die Körpernamen.
    - Label und Box-Schild: der Stil kommt aus der Tag-Konfiguration (`surface`).
  - Satzteile werden im Teil-Rahmen vernetzt, also mit dem nativen Körper ohne `transform2`, und dann gedreht.
  - Gruppe = Körper derselben Scharnier-Occurrence.
  - Dialog:
    - „Print bed“ mit der Vorgabenliste aus `printBeds` und Custom.
    - Breite und Tiefe.
    - „Spacing“, Vorgabe 5 mm.
    - „Purge tower area“, Vorgabe 50 mm, nur sichtbar bei 3MF mit Bemalung.
    - Das Bett nur bei 3MF.
  - `readChoices`/`saveChoices` werden um diese Werte erweitert.
  - STL: jedes Teil in Drucklage, `atOrigin` wie bisher.
  - STEP bleibt unverändert.
- [x] **T6 Doku und Changelog**
  - `docs/` (Export-Seite) und `CHANGELOG-CULLENECT.md` 1.1.0.
  - Credit: Pred, Drucklage nach Printables 543553 (CC BY-NC).
  - Prüfung: `mkdocs build --strict`.
- [ ] **T7 Fusion-Job, trocken geprüft, unter 50 s**
  - Box-Satz (M3x30) und ein Mix aus 3 Bins und 2 Baseplates exportieren.
  - Lage und Platten aus der 3MF ausgeben.
  - Bambu-Klicktest durch die Hauptsitzung.
- [ ] **T8 Abschluss**
  - Review durch Opus-Subagent, `master` mergen (Merge-Commit, kein Rebase), pytest grün, Hash an die Hauptsitzung.
