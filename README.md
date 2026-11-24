[![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

# Gridkeeper

Gridkeeper is an add-in for Autodesk Fusion that builds [Gridfinity](https://www.youtube.com/watch?v=ra_9zU-mnl8)
baseplates, bins and exchangeable [Cullenect](https://github.com/CullenJWebb/Cullenect-Labels) label inserts. It is our
further development of [GridfinityGenerator](https://github.com/Le0Michine/FusionGridfinityGenerator) by
Le0Michine: everything GridfinityGenerator does is still there, extended by Cullenect label pockets and inserts,
colored labels for multicolor printing, an assembly of components with joints, and more.

**Documentation: [eifel-joe.github.io/Gridkeeper](https://eifel-joe.github.io/Gridkeeper/)**

![Three Gridkeeper bins on a baseplate, with labels and symbols in red and blue](docs/assets/images/home-hero.png)

## Features

- **Baseplates**: light, full or skeletonized, with magnets, screws and connection holes, or a whole drawer filled and
  split into pieces that fit your print bed
- **Bins**: hollow, shelled or solid, in whole or half base units, custom shapes, compartments with their own labels
  and depths, dividers up to the top, a scoop, a label tab, creased walls, magnet and screw holes
- **Labels** on the tab with text and an icon, outlined, engraved or embossed, in a color of their own for multicolor
  printing
- **Cullenect pockets** in the label tabs and the **Gridkeeper label** command for the inserts: text and a screw or
  hardware symbol, jointed into their pocket
- **Storage boxes** with lid after Pred's parametric Gridfinity Storage Box v1.1, the **Gridkeeper box** command:
  any size from 4 × 3 cells and 6 units high, stacking and latching with boxes printed from Pred's file
- **Settings, rebuild and clone** from the right-click menu of every model, settings saved to and loaded from JSON
  files, user parameters to change a model without building it again

See [What's new compared to GridfinityGenerator](https://eifel-joe.github.io/Gridkeeper/getting-started/whats-new/).

## Vibe-coded

Gridkeeper is vibe-coded: its code is written by an AI, Claude, under the lead of Eifel-Joe, who designs the features,
tests them in Fusion and prints the results. Every change is checked by automated tests, by shape tests in Fusion and
by clicking through the dialogs; prints follow. Still,
expect rough edges, and please [open an issue](https://github.com/Eifel-Joe/Gridkeeper/issues) when you
find one.

### Scripting
While the add-in runs, scripts run in Fusion, such as those of an MCP server, can `import gridfinity` to reach its builders, settings and export, see [api.py](api.py).

## Installation

Gridkeeper is installed from a GitHub release, **not** from the Autodesk App Store.

1. Download the ZIP file of the latest release from the
   [releases page](https://github.com/Eifel-Joe/Gridkeeper/releases).
2. Unpack it to a place that stays where it is. It holds a folder `Gridkeeper`; keep that name, Fusion loads the
   add-in only from a folder named like its manifest.
3. In Fusion open **Utilities › Add-Ins › Scripts and Add-Ins**, click **+** on the **Add-Ins** tab and pick the
   `Gridkeeper` folder.
4. Select Gridkeeper, tick **Run on Startup** and click **Run**.

**Gridkeeper bin**, **Gridkeeper baseplate**, **Gridkeeper label** and **Gridkeeper box** now show in **Solid › Create**.

**Update:** Gridkeeper updates offers new releases, installs them and can reload itself. By hand: unpack the ZIP of
the new release over the old folder and click **Reload Gridkeeper** in **Utilities › Add-Ins › Gridkeeper updates**
(or restart Fusion). Gridkeeper runs beside the
original GridfinityGenerator.

Details in the [installation guide](https://eifel-joe.github.io/Gridkeeper/getting-started/installation/).

## Versions

Gridkeeper counts its own versions, starting with 1.0.0. Releases are tagged `gridkeeper-vX.Y.Z` and their ZIP is
`Gridkeeper-vX.Y.Z.zip`; the four-part versions such as v2.4.0.0 are GridfinityGenerator's.

## Development

- Unit tests: `python -m pytest -q`, with a stand-in for the Fusion API in `tests/stubs`
- Shape snapshot tests: in Fusion, **Gridkeeper tests: run**, when the add-in runs from a git checkout, see
  [Snapshot tests](https://eifel-joe.github.io/Gridkeeper/developers/snapshot-tests/)
- Documentation: `docs/`, built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/), preview with
  `pip install mkdocs-material` and then `python -m mkdocs serve`
- Changes of this project: [CHANGELOG.md](CHANGELOG.md)

## Credits

- **Le0Michine** (Lev Mishin): [FusionGridfinityGenerator](https://github.com/Le0Michine/FusionGridfinityGenerator),
  the add-in Gridkeeper is built on, CC BY-NC-SA 4.0. If you like it, you can
  [buy him a coffee](https://www.buymeacoffee.com/levmishin).
- **CullenJWebb**: [Cullenect-Labels](https://github.com/CullenJWebb/Cullenect-Labels), the label inserts, their
  pockets and symbols, MIT
- **ostat / Chris Heazlewood**: [gridfinity_extended_openscad](https://github.com/ostat/gridfinity_extended_openscad),
  used as a reference
- **Pred**: [Gridfinity Storage Box v1.1](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric),
  size and shape of the storage box and its lid, rebuilt in code with changes, CC BY-NC
- **Zack Freedman**: [Gridfinity](https://www.youtube.com/watch?v=ra_9zU-mnl8)

## License

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa], like
GridfinityGenerator. The Cullenect symbols in `lib/gridfinityUtils/cullenectIcons/` keep their MIT license.
The storage box follows [Pred's parametric Gridfinity Storage Box v1.1](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric) (CC BY-NC): Gridkeeper rebuilds its shape in code, with the changes noted on [Storage boxes](https://eifel-joe.github.io/Gridkeeper/boxes/), and credits Pred for it; the rebuild is part of Gridkeeper under CC BY-NC-SA, Pred's own files stay under Pred's license.

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
