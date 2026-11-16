# Gridkeeper 1.0.0

The first release of **Gridkeeper**, our further development of
[GridfinityGenerator](https://github.com/Le0Michine/FusionGridfinityGenerator) by Le0Michine, the Fusion add-in for
Gridfinity bins and baseplates. Everything GridfinityGenerator does is still there; Gridkeeper adds Cullenect label
pockets and inserts and more. Gridkeeper is vibe-coded: written with an AI assistant and tested in Fusion.

**Documentation:** https://eifel-joe.github.io/Gridkeeper/

## Install

Gridkeeper is not in the Autodesk App Store. Download `Gridkeeper-v1.0.0.zip` below, unpack it to a folder
that stays where it is, and add the `Gridkeeper` folder in Fusion under **Utilities › Add-Ins › Scripts and Add-Ins**
(green plus). Step by step: [Installation](https://eifel-joe.github.io/Gridkeeper/getting-started/installation/).
Gridkeeper runs beside GridfinityGenerator, and it recognises bins and baseplates made with GridfinityGenerator for
settings, rebuild and clone.

## What's in it

- **Cullenect labels:** label tabs with a Cullenect pocket, and a label command for the inserts that click into them,
  with text in one or two lines, raised, set in or flush, screw and hardware symbols, and joints that put the insert
  into its pocket.
- **Compartments:** merge cells into pockets by dragging, give each a label and a depth; dividers up to the top.
- **Bins:** custom shapes (cells left out), half grid, creased walls for long thin bins, shelled and solid bins.
- **Baseplates:** fill an area, cut into pieces for your printer's bed, half cells, connection holes.
- **Settings in the design:** right-click a bin, baseplate or insert for **Gridkeeper settings**, **rebuild** and
  **clone**; save and load dialog settings as files.
- **Snapshot tests** in Fusion that compare every generator against saved shapes.
- Merged from GridfinityGenerator up to its current state, including clone in the context menu and its new label icons.

The full list is in [CHANGELOG-CULLENECT.md](https://github.com/Eifel-Joe/Gridkeeper/blob/master/CHANGELOG-CULLENECT.md).

## Versions and tags

Gridkeeper counts its own versions from 1.0.0. Its tags are `gridkeeper-vX.Y.Z`; the `vX.Y.Z.W` versions are
GridfinityGenerator's.

## Credits

- **Le0Michine** (Lev Mishin): [FusionGridfinityGenerator](https://github.com/Le0Michine/FusionGridfinityGenerator),
  the add-in Gridkeeper is built on, CC BY-NC-SA 4.0. Gridkeeper is under the same license.
- **CullenJWebb**: [Cullenect-Labels](https://github.com/CullenJWebb/Cullenect-Labels), insert and pocket dimensions,
  insert geometry and layout, screw and hardware symbols, MIT.
- **ostat / Chris Heazlewood**: [gridfinity_extended_openscad](https://github.com/ostat/gridfinity_extended_openscad),
  reference for the Cullenect tab.
- **Zack Freedman**: [Gridfinity](https://gridfinity.xyz), the system itself.
