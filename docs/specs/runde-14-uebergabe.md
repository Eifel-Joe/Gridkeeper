# Runde 14 – Übergabe (Zwischenstand)

Stand 2026-11-15. Branch `runde-14` (von `runde-14-18` 6321253), nicht gepusht. Spec
`docs/specs/2026-11-15-runde-14-design.md` (von Nutzer freigegeben), Plan `docs/plans/2026-11-15-runde-14.md` (5f3e381,
von der Hauptsitzung freigegeben).
Punkte: p72 „Bin-Labels: Text mit mehr Buchstaben kann beim Ändern verrutschen“, p120 „Eingefärbte Beschriftung: nach
Textänderung sind neue Buchstaben nicht eingefärbt“, p71 „Einleger: nach Textänderung neue Buchstaben ohne Namen und
Kennung“, p53 „Mehrfarbdruck: Text und Symbol sind mehrere Körper“.

## Blocker: kein Fusion-MCP in dieser Sitzung

- `ToolSearch "select:mcp__Autodesk_Fusion__fusion_mcp_execute,mcp__Autodesk_Fusion__fusion_mcp_read"` →
  „No matching deferred tools found“.
- `session_connectors_status`: keine Zeile „Autodesk Fusion“, auch nicht als failed oder disabled. Der Server ist für
  diese Sitzung nicht vorhanden. Fusion360.exe läuft (tasklist, PID 25884).
- Der Hauptsitzung gemeldet am 15.11.

## Erledigt (belegt)

| Task | Commit | Beleg |
|---|---|---|
| 3 Lage-Rechnung der Bin-Labels (`lib/gridfinityUtils/binLabelLayout.py`) | daff9fa | `tests/test_bin_label_layout.py` 6 Tests, RED (Modul fehlt) → GREEN |
| 5 `tagUtils.partTag`, `selectedTag` nutzt sie (p71) | 622f323 | `tests/test_tag_utils.py` 6 neue Tests, RED (`no attribute 'partTag'`) → GREEN |
| 7 `appearanceUtils.colorPart`, an Bin-Label und Einleger angeschlossen (p120), `colorBodies` entfernt | cffd9da | `tests/test_appearance_utils.py` 5 Tests, RED (`no attribute 'colorPart'`) → GREEN |

`python -m pytest -q` nach cffd9da: `709 passed in 5.05s`. `pyflakes` auf die geänderten Dateien: nur zwei Meldungen,
die schon vor der Runde im Code standen (`labelGenerator.py:254` `textWidth` ungenutzt, `labelBuilder.py:8`
`commonUtils` ungenutzt).

Noch nicht in Fusion geprüft: Task 5 (Rechtsklick auf einen neuen Buchstaben) und Task 7 (zeigt ein neuer Buchstabe die
Farbe, wenn sie an der Occurrence als Proxy mit vollem Pfad steht? Kommt sie im 3MF an?). `COLOR_BODIES_TOO = True`
bleibt, bis Probe Q5 belegt, dass der 3MF-Export die Occurrence-Farbe übernimmt.

## Offen, braucht Fusion

- Task 1 Hinweisfenster-Test. Vorbefund: `fusion-hinweis-schliessen.sh -NurAnzeigen` → keine Ausgabe, Rückgabe 0.
- Task 2 Probe Q1–Q5 mit den Entscheidungsregeln im Plan. Kernfrage Q1: Commit 073efbe meldet, dass eine Label-Skizze
  auf einer mitlaufenden Ebene ihre Textkurven neu bekam und die Extrusion sie verlor.
- Task 4 `createLabel` ohne Verschieben (ruht bis zur Probe).
- Task 6 Ende-zu-Ende-Skript `tests/e2e/runde14_labels.py`, Task 8 Snapshot-Lauf, Changelog, Review, Abschluss.

## Gesammelte Abweichungen

Keine bisher.

## Nächster Schritt

Eine neu gestartete Sitzung mit Fusion-MCP macht ab Task 1 weiter (Plan, Abschnitt Task 1/2). Zuerst Add-in neu laden
per `D:\Entwicklung\Gridfinity\fusion-addin-reload.py`, weil Fusion den Stand von `runde-14` sonst nicht hat.
