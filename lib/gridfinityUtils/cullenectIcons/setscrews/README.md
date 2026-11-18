# Set screw symbols

The svg files here are set screws (grub screws) for the Cullenect labels: no head, threaded all along, the
driver in their end. Cullenect has no such symbol, they are **own work of this fork**
(Eifel-Joe/Gridkeeper), not Cullenect code.

- Drawing: the thread as Cullenect draws it, beside it a gap apart a disc for the end of the screw with the driver
  cut out (slot, hex or torx, at 70 % of Cullenect's size), with or without a security pin (hex, torx). Shaft
  `machine` has a flat end, `tapping` a point.
- Source: `tools/setscrew/SetScrew.scad`, rendered by `tools/setScrewIcons.py` with OpenSCAD.
- Lines and arcs: the rendered polygons are rebuilt as lines and circular arcs within 0.01 mm by
  `dev-notes/tools/arcSymbols.py` (round 40), which `tools/setScrewIcons.py` runs after rendering.
- It uses the thread, point and driver shapes of `Cullenect.scad` from
  [Cullenect-Labels](https://github.com/CullenJWebb/Cullenect-Labels) by CullenJWebb, MIT License
  (copy in `tools/cullenect/`, license text in `../LICENSE-Cullenect`).

The files are named like the screws, `screw_none_<shaft>_full_<driver>_noflange_<sec|nosec>.svg`, the label command
offers them with head None.

## License

The set screw symbols and `SetScrew.scad`: MIT License, see `LICENSE` in this folder. The Cullenect shapes they use:
MIT License, Copyright (c) 2024 Cullen J Webb. The add-in itself is based on FusionGridfinityGenerator by Le0Michine
(CC BY-NC-SA 4.0). Gridfinity is by Zack Freedman.
