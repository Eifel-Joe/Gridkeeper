# Klicktest Runde 31 – neuer Bin direkt in eine Zelle (p312)

Add-in aus `D:\Entwicklung\Gridfinity\wt-r31` laden. Spec: `dev-notes/specs/2026-11-18-runde-31-design.md`.

## A – Dokument ohne Baseplate und Box
1. Neues Dokument, Bin-Dialog öffnen.
   - Erwartet: **keine** Gruppe „Placement“. OK baut den Bin wie bisher am Ursprung bzw. neben anderen Bins.

## B – Baseplate-Zelle
1. Baseplate 3×3 mit **Add joint origins** bauen. Zweite Baseplate 2×2 **ohne** Joint Origins bauen.
2. Bin-Dialog öffnen.
   - Erwartet: Gruppe „Placement“ mit Feld „Cell“ steht oben unter Info. Tooltip nennt Baseplates mit Add joint origins
     und Boxen.
3. In „Cell“ klicken, mit der Maus über Joint Origins fahren.
   - Erwartet: `Socket joint origin …` der 3×3-Platte leuchtet und ist wählbar. Fuß-Joint-Origins eines vorhandenen
     Bins (falls mit Add joint origins gebaut) und Taschen-Joint-Origins sind **nicht** wählbar.
4. `Socket joint origin 2-2` wählen, Größe 1×1, OK.
   - Erwartet: Bin steht in der mittleren Zelle. Browser › Relationships › Joints: `Bin … in cell`.
     `Socket joint origin 2-2` bleibt sichtbar.
5. Neuen Bin 2×1, Zelle `Socket joint origin 1-1`, OK.
   - Erwartet: Bin belegt Zellen 1-1 und 2-1 (vorn links, nach rechts).

## C – Box-Bodenzelle
1. Box 3×2 bauen. Im Box-Dialog gibt es **kein** Kästchen „Add joint origins“ mehr.
2. Bin-Dialog, in „Cell“ klicken.
   - Erwartet: `Cell joint origin …` der Box (Komponente *Box*) wählbar; *Stack top joint origin*, *Lid joint
     origin*, Sitz-Joint-Origins, *Label joint origin* **nicht** wählbar.
3. `Cell joint origin 1-1`, Größe 2×1, OK.
   - Erwartet: Bin steht vorn links im Boxboden, reicht nach rechts, Füße sitzen im Boden.

## D – Neubau
1. Bin aus B4 per Rechtsklick „Gridkeeper rebuild“ öffnen.
   - Erwartet: **keine** Gruppe „Placement“.
2. Bin type ändern (z. B. Solid → Hollow, damit es ein echter Neubau ist), OK.
   - Erwartet: Bin steht wieder in Zelle 2-2, Gelenk `… in cell` vorhanden, keine Warnmeldung zum Gelenk.
3. Die 3×3-Baseplate neu bauen (Rechtsklick „Gridkeeper rebuild“, z. B. Typ ändern), OK.
   - Erwartet: Bins aus B bleiben in ihren Zellen.
4. Die Box aus C neu bauen (z. B. Höhe ändern), OK.
   - Erwartet: Bin aus C bleibt in Zelle 1-1.

## E – Klon
1. Bin aus B4 per Rechtsklick „Gridkeeper clone“.
   - Erwartet: Gruppe „Placement“ ist da (Klon = neuer Bin), leer. Ohne Wahl baut OK den Bin daneben, ohne Gelenk.
