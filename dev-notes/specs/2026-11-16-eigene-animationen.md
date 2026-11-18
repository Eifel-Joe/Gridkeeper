# Eigene Animationen für die Doku (Runde 26)

Stand 16.11.2026, Wunsch: die Animationen selbst erstellen.

## Problem

Alle 25 GIFs in `docs/assets/gif/` sind Byte für Byte die Dateien aus Le0Michines Original. Gridkeeper soll eigene
Animationen haben, die den eigenen Stand zeigen. Außerdem haben fünf Dialogbilder in `docs/assets/images/` einen
rötlichen Rand rechts: Das ist der Leuchtrand, den die Claude-App während der Computer-Nutzung an den Bildschirmrand
legt; der Dialog lag am rechten Bildschirmrand.

## Entscheidungen (16.11.2026)

- Aufbau wie im Original: Modell links, Ausschnitt aus dem Dialog rechts, Beschriftung unter dem Modell, Zustand für
  Zustand.
- Nur dunkles Fusion. Die Dialoge sind in beiden Fassungen dunkel; die `-light`- und `-dark`-GIFs unterscheiden sich nur
  im Seitenhintergrund und in der Schriftfarbe der Beschriftung.
- Mauszeiger wird an der geänderten Stelle eingezeichnet.
- Die drei Bildschirmvideos werden durch Animationen im gleichen Aufbau ersetzt.
- Neue Animationen für Cullenect kommen dazu.

## Aufnahmeweg

1. **Modell:** Ein Fusion-Skript (Auftrag über gf-fusion) baut jeden Zustand in einem eigenen Testdokument, setzt eine
   feste isometrische Kamera und speichert das Viewport-Bild mit durchsichtigem Hintergrund
   (`saveAsImageFileWithOptions`, `isBackgroundTransparent`). Einheitliche blaue Darstellung über ein Erscheinungsbild im
   Testdokument. Nutzerdokumente bleiben unberührt.
2. **Dialog:** Per Computer-Nutzung wird im Testdokument der echte Dialog geöffnet und Zustand für Zustand eingestellt;
   aufgenommen wird der betroffene Abschnitt. Der Leuchtrand der Computer-Nutzung bleibt laut Beobachtung, solange die
   Steuerung läuft; deshalb wird der Dialog vor den Aufnahmen mit mindestens 150 px Abstand zu jedem Bildschirmrand
   verschoben und danach auf Wunsch zurückgeschoben. `compose.py` misst jede Dialog-Aufnahme und bricht bei einem
   rötlichen Rand mit dem Dateinamen ab.
3. **Zusammensetzen:** `dev-notes/tools/anim/compose.py` (Pillow) setzt Modell, Dialogausschnitt mit gezacktem Rand,
   Mauszeiger und Beschriftung zusammen; je Zustand 1,5 s Standbild, 0,4 s Überblendung des Modells. Ausgabe je
   Animation `<name>-light.gif` und `<name>-dark.gif`. Die Rohbilder liegen unter `dev-notes/tools/anim/raw/`, damit
   jede Animation ohne Fusion neu zusammengesetzt werden kann.

## Animationen

Ersatz der Original-Animationen, gleiche Dateinamen (die Doku-Seiten bleiben unverändert):

| Datei | Zustände |
|---|---|
| baseplate-types | Light → Skeletonized → Full → Light |
| baseplate-fill-area | 2x3 grid → 450x200 mm area, Prusa MK4 → 450x300 mm area → Prusa MINI → Prusa XL → 2x3 grid |
| baseplate-connection-holes | No connection holes → 3.2 mm → 5 mm → No connection holes |
| bin-bottom-options | Solid bottom → With screw holes → With magnet cutouts → Combined → Solid bottom |
| bin-compartments | 3x2 compartments → Merged → Labeled |
| bin-creases | Flat walls → Folded in → Panels of 2 units → Flat walls |
| bin-features | 2 wide → 3 wide → Shelled → 0.8 mm walls |
| bin-half-grid | Whole bases → Half grid → 2.5 wide, a row of half bases → Whole bases |
| bin-custom-shape | Every cell → Cells left out → Every cell |
| bin-label-options | Blank → Engraved text → Engraved text and icon → Embossed text and icon (Outline erzeugt keinen Körper) |
| bin-label-tab-options | Full length → Single slot → With offset → Full length |

Ersatz der Bildschirmvideos:

| Alt | Neu | Zustände |
|---|---|---|
| specialized-bin-nozzle-creation.gif (in `bins/body.md`) | bin-solid-tool | Hollow → Solid → Solid with a tool cut into it |
| bin-with-cutout-creation.gif, specialized-bin-creation.gif | – | werden auf keiner Seite benutzt, fallen weg |

Neu für Cullenect:

| Datei | Seite | Zustände |
|---|---|---|
| cullenect-pocket | `cullenect/pockets.md` | Plain label tab → Cullenect pocket → Pocket over 2 units |
| cullenect-insert-text | `cullenect/inserts.md` | One line → Two lines → Set in → Raised |
| cullenect-insert-symbol | `cullenect/symbols.md` | No symbol → Socket head screw → Nut → Washer |

Neu aufgenommen ohne Rand: `dialog-baseplate.png`, `dialog-bin.png`, `dialog-bin-cullenect.png`, `dialog-label.png`,
`dialog-settings-buttons.png`.

## Nicht dabei

- Helle Fusion-Dialoge.
- Echte Videos.
- Änderungen am Add-in-Code.

## Fertig heißt

- Kein GIF in `docs/assets/gif/` ist mehr gleich einer Datei aus `upstream/master` (Hash-Vergleich).
- Kein Bild und kein GIF-Einzelbild hat rechts einen rötlichen Rand (Pixelprüfung: Mittel der rechten 40 Spalten nicht
  r > g + 12).
- Jede Animation zeigt die Zustände aus der Tabelle in dieser Reihenfolge; jedes GIF unter 2,5 MB.
- `python -m mkdocs build --strict` ohne Fehler, pytest grün, Credits-Seite nennt die Animationen nicht mehr als fremd.
- Die Seiten werden gesichtet und freigegeben.
