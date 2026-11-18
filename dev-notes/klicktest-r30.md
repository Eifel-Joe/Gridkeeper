# Klicktest Runde 30: Box-Deckel oben geschlossen (p311)

Spec: `dev-notes/specs/2026-11-18-r30-lid-closed.md`. Add-in aus `D:\Entwicklung\Gridfinity\wt-r30` geladen. Je Test
ein neues Dokument, ohne Speichern schließen. Ein Box-Bau dauert 60–75 s.

| # | Schritte | Erwartet |
|---|---|---|
| K1 | Solid › Create › **Gridkeeper box** öffnen | Gruppe **Lid** zwischen *Joint origins* und *Small parts*, Dropdown **Lid top** mit *Grid* (gewählt) und *Closed*; Tooltip erklärt beides |
| K2 | **Lid top** = *Closed*, 5 × 4 × 6 bauen | Box 5×4×6 mit Deckel: oben eben von Rand zu Rand, vier Rastnasen (Viertelringe) in den Ecken, kein Raster; Zeitleiste ohne gelbe/rote Elemente; Kleinteile wie immer |
| K3 | Rechtsklick Box › **Gridkeeper settings** | Einstellungen zeigen `lidTop: Closed` |
| K4 | Rechtsklick Box › **Gridkeeper rebuild**: Dialog zeigt *Closed*; auf *Grid* stellen, ausführen | Deckel neu mit Raster; nochmal rebuild auf *Closed*: wieder geschlossen |
| K5 | Rechtsklick › **Gridkeeper clone** der geschlossenen Box | Klon mit geschlossenem Deckel |
| K6 | Dialog mit *Closed* offen lassen; über **Load** eine Box-Einstellungsdatei ohne `lidTop` laden `dev-notes/klicktest-r30-alt.json` (Box 5×4×6 wie aus 1.1.0, ohne `lidTop`) | Dropdown springt auf *Grid* |
| K7 | Modify › Change Parameters: `gfBox1_baseWidth` = 4, `gfBox1_heightU` = 8 an der geschlossenen Box | Box und Deckel folgen, Deckel bleibt oben eben, Zeitleiste gesund |
| K8 | Rechtsklick geschlossene Box › **Gridkeeper export**, 3MF | Deckel liegt wie gebaut (Oberseite oben), Box und Kleinteile wie bisher, je auf eigener Platte |
| K9 | Solid › Create › **Gridkeeper box label** für die geschlossene Box | Schild sitzt im Halter vorn wie bei der Raster-Box |
| K10 | Zweite Box 5 × 4 × 6 (*Grid*) bauen, ihr *Stack bottom joint origin* auf *Stack top joint origin* der geschlossenen jointen | Box steht auf dem Deckel, Rastnasen in den Rillen ihres Bodens (Schnitt oder Interference: keine Überschneidung) |

Bilder (docs/assets/images/NEEDED.md): `box-lid-closed.png` aus K2 in der Ansicht von `box-5x4x6.png`, `dialog-box.png`
neu aus K1 (mit Gruppe *Lid*).
