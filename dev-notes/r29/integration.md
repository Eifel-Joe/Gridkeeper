# Integration der gezeichneten Kleinteile (Runde 29), Zweig `r29-int`

Jörg 17.11.2026: „So wie eine Sitzung fertig ist, kann ja sofort ein Testlauf mit Klicktest durchgeführt werden.“
Die Teile kommen deshalb einzeln auf `r29-int` (ab `runde-29`), je Teil ein Klicktest im echten Dialog.

## Gerüst (Stand dieses Zweigs)

- **`predBoxParts.DRAWN_ROLES`:** Rollen, deren Teil gezeichnet wird. Anfangs leer. `partsToDraw(hinge)` liefert
  nur diese Teile, in der Reihenfolge von `PARTS`.
- **`predBoxInsert.insertParts`:** zeichnet jedes Teil aus `partsToDraw` in eine neue Komponente des Satzes
  (`addNewComponent`). Name und Rollen-Tag wie bisher; das Zeichnen übernimmt `drawPart(component, part, dims,
  hinge)`. Weitere Exemplare sind dieselbe Komponente. Gejointet wird wie in Runde 28. Kein Import,
  `importToTarget` und `tempCopy` sind entfernt.
- **`boxBuilder`:** unverändert. `insertParts` läuft im Befehl, die Teile landen in der Gruppe des Satzes.
- **Teile, die noch nicht gezeichnet werden,** fehlen im Satz ganz. Ihre Joint origins an der Box sind schon da.

## Ein Teil aufnehmen, sobald seine Untersitzung fertig ist

1. Den Teil-Branch nach `r29-int` mergen (Merge-Commit): Griff `claude/r29-handle-049385`, Riegel
   `claude/r29-latch-3b0e5c`, Haltestift `claude/r29-pin-251c13`, Scharniere `claude/r29-hinge-a89d58`.
2. Den Test zuerst: `tests/test_pred_box_parts.py` und `tests/test_box_builder_bodies.py` erwarten die Rolle in
   `DRAWN_ROLES` und einen Zweig für sie in `drawPart`. `test_every_drawn_role_has_its_generator` prüft das.
3. In `drawPart` den Zweig ergänzen:
   - Griff: `predHandle.createHandle(component, predBoxSeats.handleHalfWidth(dims).expression)`.
   - Riegel und Stift: `createLatch(component)` bzw. `createHandlePin(component)`.
   - Scharnier: `predHinge.createHinge(component, hinge)`; den Joint origin legt `insertParts` mit
     `addOriginJointOrigin` an.
4. Die Rolle in `DRAWN_ROLES` aufnehmen; pytest grün.
5. Commit, Hash an die Hauptsitzung. Sie schaltet den Gridkeeper-Ordner, startet Fusion neu und lässt im Dialog
   prüfen: Erzeugen in Part- und Hybrid-Dokument, Gruppe, Rückgängig, Rebuild, Clone.

## Zum Schluss, wenn alle Teile da sind

- `resources/predBox/*.f3d` und deren README entfernen; die Credits für Pred bleiben in Doku und Changelog.
- Das Feld `file` in `predBoxParts.Part` und `HINGES`-Dateinamen durch Varianten-Schlüssel ersetzen.
- Snapshots der Box-Fälle neu ablegen (r28_snap-Muster), Doku `docs/boxes.md` (Teile werden gezeichnet).
- Während der Zwischenstände passen die Box-Snapshots nicht (weniger Körper); das ist erwartet, sie werden am Ende neu
  abgelegt.
