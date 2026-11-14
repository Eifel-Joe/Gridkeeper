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

`screws/` holds one file per valid combination, named
`screw_<head>_<shaft>_<threads>_<driver>_<flange|noflange>_<sec|nosec>.svg`,
`hardware/` one file per hardware symbol. The add-in reads what is in these folders, so another symbol
is another svg file. The hardware symbols are copied to `../labelIcons/<type>/cullenect-*.svg` as well.

## License

The symbols are derived from Cullenect-Labels, MIT License, Copyright (c) 2024 Cullen J Webb. The full
license text is in `LICENSE-Cullenect` in this folder (it ships with the add-in).
