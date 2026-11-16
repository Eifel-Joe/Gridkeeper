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

**Everything of GridfinityGenerator**, merged up to its current state: bins with compartments, custom shapes, half grid
and creased walls; baseplates that fill an area and are cut for your printer's bed; the settings window with rebuild
and clone; settings files; the snapshot tests. All of that is Le0Michine's work.

**New in Gridkeeper:**

- **Cullenect pockets in label tabs:** label style „Cullenect“ for bin and compartment tabs, with socket play and the
  socket sizes in the dialog.
- **Gridkeeper label**, a command for the Cullenect inserts that click into those pockets: text in one or two lines,
  raised, set in or flush, text colour, 480 screw symbols plus set screws and hardware (nuts, washers, inserts, crimp
  terminals).
- **Inserts placed in their pockets:** bins, baseplates and inserts become components, an insert is jointed into the
  pocket it was made for; inserts can be rebuilt, cloned and opened in the settings window like bins.
- **Dividers up to the top** on grid lines, and a label colour for bin labels.
- **More shape tests**, also checking that every sketch is fully constrained.
- **Own documentation** with every dialog and option explained, in English.

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
