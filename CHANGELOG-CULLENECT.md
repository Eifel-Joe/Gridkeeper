# Changelog — Cullenect labels

Changes of this fork (`Eifel-Joe/FusionGridfinityGenerator`) on top of GridfinityGenerator v2.2.0.0.

## Unreleased

### Added

- **Label style „Cullenect“ for bins.** Every label tab, also each compartment tab and the tab of a shelled bin,
  gets a socket for exchangeable Cullenect label inserts instead of a printed label: 1.2 mm deep, 0.3 mm larger than
  the insert, with the latch ribs along both long sides. The socket takes the widest standard Cullenect width
  (`42 mm × n − 6 mm`, in half units) that fits the tab with 1 mm to spare, so original Cullenect inserts fit compartment
  tabs too. Its width is an expression on `gfBaseWidth` and it follows parameter changes like the labels do.
- The tab is widened to at least 14 mm (more under steep overhangs) and kept flat with this style; text, icon, bold and
  tab top angle are switched off in the dialog but keep their values. Hollow tabs keep a 0.4 mm skin under the socket.
- **Socket play** input in the label tab section (default 0.3 mm like Cullenect, 0–1 mm).
- **Socket widths in the dialog:** a second row of the dimensions table lists each socket size of the bin with the
  insert width that fits it, and the bin's „Gridfinity settings“ keep the same list under „Cullenect“.
- **Sketch constraint check** in the shape tests: Cullenect cases fail on a sketch that is not fully constrained,
  other cases log such sketches. Eleven new Cullenect bin cases.

## Credits

- **Le0Michine** — [FusionGridfinityGenerator](https://github.com/Le0Michine/FusionGridfinityGenerator), the add-in
  this fork builds on, CC BY-NC-SA 4.0.
- **CullenJWebb** — [Cullenect Labels](https://github.com/CullenJWebb/Cullenect-Labels), insert and socket dimensions
  from `OpenSCAD/Cullenect.scad` (commit `d6dc0bb`), MIT.
- **ostat / Chris Heazlewood** — [gridfinity_extended_openscad](https://github.com/ostat/gridfinity_extended_openscad),
  reference for the Cullenect tab.
- **Zack Freedman** — [Gridfinity](https://gridfinity.xyz).
