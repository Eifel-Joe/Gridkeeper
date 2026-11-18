# Runde 37: Label-Farben auf eigene Filamente verteilen (p301)

Stand 18.11.2026. Punkt p301 „Export: verschiedene Label-Farben auf verschiedene Filamente verteilen“.
Festgelegte Variante „Automatisch + änderbar“: Körper bekommen Filament 1, jede Label-Farbe automatisch eine eigene
Nummer 2, 3 …; im Export-Dialog lässt sich die Zuordnung ändern, und sie wird gemerkt.

## Problem

`threeMf.write(path, objects, filament)` kennt eine Filament-Nummer für alle bemalten Dreiecke
(`MeshObject.painted: set[int]`). Der Export-Dialog hat einen Spinner „Label color index“. Rote und blaue Texte landen
auf demselben Filament.

## Woher die Farbe kommt

Alle farbigen Texte und Symbole (Bin, Cullenect-Einleger, Box-Label) färbt `appearanceUtils.colorPart` mit der
Darstellung `Gridfinity label RRGGBB` (`labelColors.appearanceName`): auf der Text-Occurrence, bei Körpern im Root
auf dem Körper. Die Farbe einer Markierung wird daraus zurückgelesen:
1. Darstellung der Text-Occurrence, sonst die des Körpers.
2. Heißt sie `Gridfinity label RRGGBB` → Farbe `#RRGGBB`.
3. Sonst (keine eigene Farbe, z. B. Text ohne Farbe; ebenso die Buchstabenflächen der Outline-Labels ohne Farbe,
   `hasOutlineLabels`) → Schlüssel „ohne Farbe“ (`''`).

Verworfen: Farbe aus der Bin-/Label-Konfiguration im Tag lesen. Drei Konfig-Formate (Bin `labelColor`, Einleger und
Box-Label `textColor`), und die Darstellung ist das, was der User in Fusion sieht. Verworfen: beliebige Darstellungen
über ihren Farbwert erkennen. Dann würde Text ohne Farbe die Standardfarbe des Bins als „Farbe“ zeigen.
Nicht dabei: Texte, die der User von Hand umgefärbt hat; sie zählen als „ohne Farbe“.

## Zuordnung (Fusion-frei, `lib/exportParts.py`)

- Schlüssel: `'#RRGGBB'` oder `''` (ohne Farbe). Reihenfolge = erstes Auftreten in der Export-Reihenfolge.
- `assignFilaments(keys, saved)`: gemerkte Nummer, wenn vorhanden (1 … 18); sonst die kleinste Nummer ≥ 2, die keine
  andere Farbe hat, weder dieses Exports noch gemerkt (Review: rot allein → 2, blau allein → 2, zusammen dann still auf
  einem Filament). Sind alle gemerkt vergeben, die kleinste freie dieses Exports; sind 2 … 18 belegt, bekommt jede
  weitere 18. Gespeichert wird die Zuordnung, mit der exportiert wurde.
- Zwei Farben dürfen dieselbe Nummer bekommen, wenn der User sie so einstellt (gleiches Filament gewollt).
- Gemerkt in `commandConfig`, Abschnitt `Export`, Schlüssel `labelFilaments`, Format `D02020=2,2060D0=3,none=4`.
  Beim Export werden die Nummern der gezeigten Farben übernommen, gemerkte andere Farben bleiben stehen.
- Altes `colorIndex` (ein Spinner bisher): wird als gemerkte Nummer für „ohne Farbe“ übernommen, wenn
  `labelFilaments` dafür nichts hat. Damit druckt ein bisheriges Outline-Label auf demselben Filament wie vorher.
- Körper: unbemalte Dreiecke, also das Filament des Objekts im Slicer, Nummer 1. Nicht änderbar.

## 3MF (`lib/threeMf.py`)

- `MeshObject.painted` wird `dict[int, int]`: Dreieck → Filament. Jede Nummer bekommt ihren eigenen Paint-Code
  (`paint_color` / `slic3rpe:mmu_segmentation`, `Slic3r_facets_annotation.json` je Dreieck).
- `write`/`modelXml`/`facetsAnnotation` verlieren den Parameter `filament`; „nicht bemalen“ = leere `painted`.
- `exportParts.withMarkings(part, markings)`: Markierungen als Paare (Mesh, Filament oder None).

## Export-Dialog (`commands/commandExport/entry.py`)

- Der Spinner „Label color index“ entfällt. Neu unter „Color label text“: eine Gruppe „Label filaments“ mit einer
  Auswahlliste 1 … 18 je Farbe der aktuellen Auswahl, Name „Red text“, „#123456 text“ (`labelColors.choiceOf`) bzw.
  „Text without color“; Tooltip nennt, dass 1 das Filament der Körper ist. Entscheidung: Liste statt Spinner, weil
  Fusion eine in einen Spinner getippte Zahl verwirft, wenn direkt aus dem Feld auf OK geklickt wird (Klicktest D,
  kein inputChanged, Wert unverändert).
- Die Listen werden bei jeder Auswahländerung neu aufgebaut. Werte, die der User im offenen Dialog geändert hat,
  bleiben bei einer Auswahländerung erhalten. Ohne farbigen Text in der Auswahl: Gruppe unsichtbar.
- Sichtbar nur bei 3MF und „Color label text“ an.
- Meldung nach dem Export: „Label text of 2 parts: Red text on filament 2, Blue text on filament 3.“ statt „assigned color N“.
- Turm-Fläche: unverändert, sobald etwas bemalt ist.

## Nicht dabei

- Körper auf ein anderes Filament als 1 legen, Filamentfarben/-namen in die 3MF schreiben (Slicer-Projekteinstellung).
- STL/STEP (keine Farben).
- Von Hand umgefärbte Texte erkennen.

## Ende-zu-Ende

- pytest: zwei Markierungen mit `#D02020` und `#2060D0` → im 3MF Paint-Codes `8` und `0C`; gemerkte Zuordnung
  `D02020=3` → rot `0C`, blau `8`; Speichern/Lesen der Zuordnung; Auswahl zwei Farben + ohne Farbe.
- Fusion (ein Slot-Job): zwei Bins mit rotem und blauem Label, `export3mf` aus dem Worktree, 3MF lesen: zwei
  verschiedene Paint-Codes, Körper unbemalt.
- Klicktest `dev-notes/klicktest-r37.md`: Liste je Farbe, Nummer ändern, exportieren, Dialog neu öffnen → Nummer
  gemerkt.
