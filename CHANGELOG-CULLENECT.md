# Changelog — Cullenect labels

Fork of GridfinityGenerator (Le0Michine) with Cullenect label support.

## Unreleased

### Added
- Cullenect symbols as svg files: 480 screw combinations (head, shaft, threads, driver, flange,
  security pin) and 18 hardware symbols in `lib/gridfinityUtils/cullenectIcons/`, rendered once from
  Cullenect's own OpenSCAD code by `tools/cullenectIcons.py` (the plan counted 19 hardware symbols,
  `Cullenect.scad` has 18). The add-in reads the folders, so a new symbol is a new svg file.
- Symbol catalog `lib/gridfinityUtils/cullenectCatalog.py` (building blocks, file names, lookup from
  the folders, svg size).
- The hardware symbols are also in the label icon dropdown (`Cullenect washer`, ...), with the new
  icon types inserts, magnets and crimps.

## Credits

- Le0Michine — FusionGridfinityGenerator (CC BY-NC-SA 4.0)
- CullenJWebb — Cullenect-Labels, `Cullenect.scad`, symbols (MIT)
- ostat / Chris Heazlewood — gridfinity_extended_openscad (reference)
- Zack Freedman — Gridfinity
