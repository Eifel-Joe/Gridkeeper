# Runde 31: Neuen Bin direkt in eine Zelle setzen (p312)

Stand 18.11.2026. Branch `r31-bin-in-cell` von `master` (1d7ab99). Freigabe durch die Hauptsitzung.

## Punkt
- p312 „Neuen Bin direkt in eine Zelle von Box oder Baseplate setzen“

## Festlegungen
- 17.11.: Bei Bins größer 1×1 ist die gewählte Zelle die **vordere linke Ecke** des Bins. Gibt es im
  Dokument weder Baseplate noch Box, erscheint die Auswahl nicht, der Bin wird wie bisher gebaut.
- 18.11.: Angeboten werden die Zellen jeder Baseplate und die **Bodenzellen im Inneren der Box**, nicht das Raster oben
  auf dem Deckel. Nur für neue Bins; vorhandene Bins behalten beim Neubau ihr Gelenk. Fehlen der Box Zell-Joint-Origins,
  legt die Runde sie an (Box-Rebuild darf bestehende Gelenke nicht verlieren).

## Was es heute gibt
- Baseplate: `Socket joint origin <Spalte>-<Reihe>` je Zelle, nur mit „Add joint origins“ (Standard aus), Z = Sockel-Boden.
- Box: `Cell joint origin <Spalte>-<Reihe>` je Bodenzelle in der Komponente `Box`, nur mit „Add joint origins“
  (Standard an), Z = Boden innen − Fußhöhe. Der Deckel hat keine Zell-Joint-Origins.
- Bin: `Foot joint origin <Spalte>-<Reihe>` je **Fuß** (im Halbraster je Halbfuß), nur mit „Add joint origins“.
- Muster Einleger → Tasche (p160): Auswahlfeld im Label-Dialog, starres Gelenk `<Name> in pocket` in der Zeitleisten-
  gruppe des Einlegers, beim Neubau wird die Tasche aus dem alten Gelenk gelesen und das neue Teil wieder hineingesetzt.

## Entscheidungen dieser Runde

### 1. Dialog
- Neue Gruppe **„Placement“** mit einem Auswahlfeld **„Cell“** (Joint Origins, 0 bis 1 Auswahl), Tooltip:
  „Optional: pick a cell joint origin of a baseplate or of the floor of a box, the bin is jointed there with its front
  left cell. Without, it goes beside the other bins.“
- Sichtbar nur, wenn (a) ein **neuer** Bin entsteht (neu oder geklont aus Config/Kopie, nicht beim Neubau) und (b) das
  Dokument mindestens einen Körper mit Baseplate- oder Box-Tag hat. Sonst fehlt die Gruppe ganz.
- Wählbar (`command_select`) sind nur
  - `Socket joint origin <c>-<r>` einer Komponente mit Baseplate-Körper,
  - `Cell joint origin <c>-<r>` der Box-Komponente (Rolle `Box`, nicht `Lid`).
  Alles andere (Fuß-, Taschen-, Sitz-, Stapel-, Deckel-Joint-Origins) ist nicht wählbar.

### 2. Der Bin bekommt einen eigenen Joint Origin für die Platzierung
`Foot joint origin 1-1` taugt nicht: im Halbraster sitzt er in der Mitte eines Halbfußes, nicht in der Mitte der
vorderen linken **Raster**zelle, und bei geformten Bins fehlt er, wenn die Ecke ausgespart ist. Darum:
- Neuer Joint Origin **`Cell placement joint origin`** am Bin, Mitte der vorderen linken Rasterzelle
  (x = Basisbreite/2 − XY-Spiel, y = Basislänge/2 − XY-Spiel), Z = Fußunterseite (wie die anderen Fuß-Joint-Origins),
  Z nach oben, X entlang X, über `createPointJointOrigins` mit treibenden Maßen (Skizze voll bestimmt).
- Er entsteht nur, wenn der Bin in eine Zelle gesetzt wird (neu oder beim Neubau eines gesetzten Bins), unabhängig von
  „Add joint origins“.
- „Vorn links“ = kleinstes X und kleinstes Y (Fusion-Vorderansicht), so wie Spalte 1 / Reihe 1 der Zellen.

### 3. Gelenk
- Starres Gelenk `<Binname> in cell` vom `Cell placement joint origin` (Bin) auf die gewählte Zelle, in der
  Zeitleistengruppe des Bins, wie beim Einleger. Bin baut an Platzierung (0, 0) ohne Verschiebung, das Gelenk setzt ihn.
- Die Zelle bleibt sichtbar (`assembly.keepShown`, wie Tasche und Box-Label-Halter).
- Ein Bin aus Körpern im Root (Teile-Konstruktion in der Vorschau) bekommt kein Gelenk (wie der Einleger).

### 4. Neubau eines gesetzten Bins („behalten beim Neubau ihr Gelenk“)
- Nur Parameter geändert (`parameterEdits`): die Zeitleiste bleibt, das Gelenk auch. Nichts zu tun.
- Echter Neubau: Das alte Gelenk `… in cell` liegt in der alten Gruppe und geht mit ihr. `rebuildBin` liest vorher aus
  ihm die Zelle (Gegenseite, aus Root-Sicht wie `labelBuilder._inRoot`) und baut den neuen Bin wieder in diese Zelle.
- Gibt es die Zelle nicht mehr oder liegt ihre Baseplate/Box in der Zeitleiste nach dem Bin: Neubau ohne Gelenk an der
  alten Lage (Transform), Hinweis in den Neubau-Notizen.
- Der Dialog zeigt beim Neubau keine Zellauswahl.

### 5. Box: Zell-Joint-Origins immer
- Die Box legt ihre Boden-Zell-Joint-Origins **immer** an. Das Kästchen „Add joint origins“ im Box-Dialog entfällt;
  das Config-Feld `hasJointOrigins` bleibt lesbar (alte Config-Dateien, Tags), wird aber nicht mehr ausgewertet.
- Eine alte Box ohne Zell-Joint-Origins bekommt sie mit ihrem nächsten Neubau. Der Box-Neubau hängt Gelenke schon heute
  nach Namen um (`jointsByName=True`), Bins in Zellen bleiben also drin – wird in Fusion geprüft.
- Die Bin-Zellauswahl selbst legt **keine** Joint Origins an fremden Teilen an (sie lägen außerhalb deren Gruppe und
  gingen beim nächsten Box-Neubau verloren). Eine Box ohne Zellen zeigt der Dialog im Hinweistext:
  „Rebuild the box to give it cell joint origins.“

### 6. Baseplate-Neubau
- Bisher hängt der Baseplate-Neubau nur Taschen-Gelenke um; ein Gelenk eines Bins auf eine Sockel-Zelle bräche mit dem
  Neubau. Weil die Runde solche Gelenke jetzt selbst anlegt, hängt der Baseplate-Neubau Gelenke nach Namen um
  (`jointsByName=True`, wie die Box). Hat die neue Baseplate die Zelle nicht mehr (kleiner, Joint Origins aus), gibt es
  die vorhandene Notiz „the new part has no …“.
- Baseplates **ohne** Joint Origins werden nicht nachgerüstet (die Festlegung nennt nur die Box); sie bieten keine
  Zellen an. Der Tooltip sagt: „Baseplates offer their cells with Add joint origins.“

## Ausdrücklich nicht dazu
- Kein Prüfen, ob der Bin über den Rand der Baseplate/Box ragt oder andere Bins überlappt.
- Kein Abgleich der Basiseinheit von Bin und Baseplate/Box.
- Kein Umsetzen vorhandener Bins in Zellen, kein Nachrüsten von Baseplate-Joint-Origins.
- Keine Zellen auf dem Deckel (Stapelraster).

## Testbare Logik (pytest, ohne Fusion)
Neues Modul `lib/gridfinityUtils/binCell.py`:
- `cellOf(jointOriginName)` → (Spalte, Reihe) für `Socket joint origin c-r` / `Cell joint origin c-r`, sonst None.
- `isCellJointName(name)`, `cellJointName(binName)` (Suffix ` in cell`, Fusion-Zähler „ (2)“ erlaubt).
- (Umsetzung: die Mitte der vorderen linken Rasterzelle kommt aus `baseGenerator.cellCenters` mit den Einheits-Parametern
  des Bins, nicht aus einer eigenen Funktion, damit die Skizzenmaße den Parametern folgen.)
- `offersCellPick(isNewBin, hasBaseplateOrBox)`.
Dazu Tests: Box-Dialog ohne Kästchen, Box-Builder ruft Zell-Joint-Origins unabhängig von `hasJointOrigins` auf (Stub).

## Ende-zu-Ende-Kriterium (Fusion-Skript, eigenes Dokument)
1. Baseplate 3×3 mit Joint Origins, Box 3×2. Bin 1×1 in `Socket joint origin 2-2`: Bin-`Cell placement joint origin`
   fällt in Weltkoordinaten mit der Zelle zusammen (< 0,01 mm), Gelenk `… in cell` existiert.
2. Bin 2×1 in Box-`Cell joint origin 1-1`: Bin liegt mit der vorderen linken Zelle dort, der Rest in +X.
3. Halbraster-Bin 1×1 in eine Baseplate-Zelle: Lage wie 1.
4. Neubau des Bins aus 1 (Höhe geändert, echter Neubau): Gelenk wieder da, Lage gleich.
5. Neubau der Box aus 2 und der Baseplate aus 1: Bins bleiben in ihren Zellen.
6. Alle neu angelegten Skizzen `isFullyConstrained`.
Dokument ohne Baseplate/Box (Auswahl fehlt) und die Auswahlfilter prüft der Klicktest (`dev-notes/klicktest-31.md`).
