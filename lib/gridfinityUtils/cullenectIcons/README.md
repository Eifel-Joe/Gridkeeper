# Cullenect symbols

The svg files in `screws/` and `hardware/` are the symbols of the Cullenect labels, rendered to 2D
from the original OpenSCAD code:

- Source: [Cullenect-Labels](https://github.com/CullenJWebb/Cullenect-Labels) by CullenJWebb,
  `OpenSCAD/Cullenect.scad`, commit `d6dc0bb2a6491f53c27e5f9db2dfc38ebb07f8db`, MIT License
  (copy with license in `tools/cullenect/`).
- Tool: `tools/cullenectIcons.py` renders them with OpenSCAD (`projection()` of the head without the
  driver, the shaft and the security pin, or of the hardware symbol).
- Generator: the add-in itself is based on FusionGridfinityGenerator by Le0Michine (CC BY-NC-SA 4.0).
  Gridfinity is by Zack Freedman.

`setscrews/` is not Cullenect's: set screws drawn for this fork, with a license of their own, see its README.

`screws/` holds one file per valid combination, named
`screw_<head>_<shaft>_<threads>_<driver>_<flange|noflange>_<sec|nosec>.svg`,
`hardware/` one file per hardware symbol. The add-in reads what is in these folders, so another symbol
is another svg file. The hardware symbols are copied to `../labelIcons/<type>/cullenect-*.svg` as well.

The label command puts a symbol on the insert at the size its svg says, like Cullenect does: give
`width` and `height` with a unit (`mm`, `cm`, `in`, `pt`, `pc`, `px`). A number without a unit counts as
CSS pixels (1/96 in) as in the svg standard, an svg with only a `viewBox` as mm, the way OpenSCAD writes
it. A symbol taller than the insert is scaled down to fit.

## License

The symbols are derived from Cullenect-Labels, MIT License, Copyright (c) 2024 Cullen J Webb. The full
license text is in `LICENSE-Cullenect` in this folder (it ships with the add-in).
